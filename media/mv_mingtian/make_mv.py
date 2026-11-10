#!/usr/bin/env python3
"""《明天还没来》MV 生成器 —— 纯程序化渲染（numpy + OpenCV + Pillow + ffmpeg）。

用法:
    python3 make_mv.py still  <t秒> <out.png>          # 渲染单帧预览
    python3 make_mv.py part   <起始帧> <结束帧> <out.mp4>  # 渲染一段（无音频）
    python3 make_mv.py all    <out.mp4> [并行数]        # 全片 + 混音

环境变量:
    MV_AUDIO  音频文件（内嵌 mov_text 歌词字幕轨）
    MV_WORK   工作目录（缓存 / 字体 fonts/*.ttf）
"""
import math
import os
import re
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
DUR = 346.8
NF = int(DUR * FPS)
AUDIO = os.environ.get("MV_AUDIO", "audio.m4a")
WORK = os.environ.get("MV_WORK", "./work")
FONTS = os.path.join(WORK, "fonts")
cv2.setNumThreads(1)

f32 = np.float32


# ───────────────────────── 基础工具 ─────────────────────────
def sstep(a, b, x):
    if a == b:
        return 1.0 if x >= a else 0.0
    u = min(1.0, max(0.0, (x - a) / (b - a)))
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def pulse(t, a, b, fi=0.5, fo=0.5):
    """a 淡入、b 淡出的包络。"""
    return sstep(a, a + fi, t) * (1 - sstep(b - fo, b, t))


def col(*c):
    return np.array(c, f32)


def fbm(w, h, seed, octaves=6, base=3, tile_x=False, gain=0.5):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), f32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw = base * 2 ** o
        gh = max(2, int(round(gw * h / w)))
        g = rng.random((gh, gw), dtype=f32)
        if tile_x:
            g = np.concatenate([g[:, -2:], g, g[:, :2]], 1)
            big = cv2.resize(g, (int(round(w * (gw + 4) / gw)), h), interpolation=cv2.INTER_CUBIC)
            off = int(round(2 * w / gw))
            big = big[:, off:off + w]
        else:
            big = cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        out += big * amp
        tot += amp
        amp *= gain
    out /= tot
    lo, hi = np.percentile(out, [0.5, 99.5])
    return np.clip((out - lo) / (hi - lo), 0, 1).astype(f32)


def radial(r, power=2.0, core=0.0):
    """半径 r 的径向辉光精灵 (2r+1)^2, 中心=1。"""
    y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(f32)
    d = np.sqrt(x * x + y * y) / r
    g = np.clip(1 - d, 0, 1) ** power
    if core:
        g = np.maximum(g, (d < core).astype(f32))
    return g


def add_sprite(img, spr, cx, cy, color, gain=1.0):
    """把单通道精灵按颜色叠加到 img (加色)。"""
    if gain <= 0:
        return
    h, w = spr.shape
    x0, y0 = int(round(cx)) - w // 2, int(round(cy)) - h // 2
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa >= xb or ya >= yb:
        return
    s = spr[ya - y0:yb - y0, xa - x0:xb - x0]
    img[ya:yb, xa:xb] += s[..., None] * (np.asarray(color, f32) * gain)


def make_stars(w, h, n, seed, bright=1.0):
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), f32)
    xs = rng.integers(0, w, n)
    ys = rng.integers(0, h, n)
    b = (rng.random(n) ** 6 * 1.6 + 0.08) * bright
    tint = rng.random(n)
    c = np.stack([0.8 + 0.2 * tint, 0.85 + 0.1 * np.abs(tint - 0.5), 1.0 - 0.25 * tint], 1).astype(f32)
    np.add.at(img, (ys, xs), c * b[:, None])
    glow = cv2.GaussianBlur(img, (0, 0), 1.6) * 3.0
    big = np.zeros_like(img)
    idx = np.argsort(b)[-max(8, n // 60):]
    np.add.at(big, (ys[idx], xs[idx]), c[idx] * b[idx, None])
    big = cv2.GaussianBlur(big, (0, 0), 4.0) * 22
    return img + glow + big


def shift_wrap(tex, dx, dy, w=W, h=H):
    """从可平铺纹理中取 (w,h) 窗口，整像素平移。"""
    th, tw = tex.shape[:2]
    xs = (np.arange(w) + int(dx)) % tw
    ys = (np.arange(h) + int(dy)) % th
    return tex[ys][:, xs]


def affine(tex, scale, ang, cx, cy, sy=1.0, tcx=None, tcy=None, border=cv2.BORDER_CONSTANT, size=(W, H)):
    """纹理中心 -> 屏幕 (cx,cy)，旋转 ang、缩放 scale，y 方向再压扁 sy。"""
    th, tw = tex.shape[:2]
    tcx = tw / 2 if tcx is None else tcx
    tcy = th / 2 if tcy is None else tcy
    c, s = math.cos(ang) * scale, math.sin(ang) * scale
    M = np.array([[c, -s, 0], [s * sy, c * sy, 0]], np.float64)
    M[0, 2] = cx - (M[0, 0] * tcx + M[0, 1] * tcy)
    M[1, 2] = cy - (M[1, 0] * tcx + M[1, 1] * tcy)
    return cv2.warpAffine(tex, M, size, flags=cv2.INTER_LINEAR, borderMode=border), M


# ───────────────────────── 文字 ─────────────────────────
_fonts = {}
_cmaps = {}


def font(name, size, weight=None):
    key = (name, size, weight)
    if key not in _fonts:
        path = os.path.join(FONTS, name + ".ttf")
        if not os.path.exists(path):
            path = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
        f = ImageFont.truetype(path, size)
        if weight:
            try:
                f.set_variation_by_axes([weight])
            except Exception:
                pass
        _fonts[key] = f
    return _fonts[key]


def has_glyphs(name, s):
    if name not in _cmaps:
        try:
            from fontTools.ttLib import TTFont
            _cmaps[name] = set(TTFont(os.path.join(FONTS, name + ".ttf"), lazy=True).getBestCmap().keys())
        except Exception:
            _cmaps[name] = None
    cm = _cmaps[name]
    return cm is None or all(ord(ch) in cm or ch.isspace() for ch in s)


_tcache = {}


def text_sprite(s, fname="NotoSerifSC", size=56, weight=700, spacing=0, shadow=6):
    """返回 (alpha, shadow_alpha) 两张单通道 float 图。"""
    key = (s, fname, size, weight, spacing, shadow)
    if key in _tcache:
        return _tcache[key]
    if not has_glyphs(fname, s):
        fname, weight = "NotoSerifSC", 900
    f = font(fname, size, weight)
    pad = int(size * 0.5) + shadow * 3
    widths = [f.getlength(ch) for ch in s]
    tw = int(sum(widths) + spacing * (len(s) - 1)) + 2 * pad
    th = int(size * 1.5) + 2 * pad
    im = Image.new("L", (tw, th), 0)
    d = ImageDraw.Draw(im)
    x = pad
    for ch, wd in zip(s, widths):
        d.text((x, pad), ch, font=f, fill=255)
        x += wd + spacing
    a = np.asarray(im, f32) / 255
    sh = np.clip(cv2.GaussianBlur(a, (0, 0), shadow) * 1.8, 0, 1) if shadow else np.zeros_like(a)
    _tcache[key] = (a, sh)
    return _tcache[key]


def draw_text(img, s, cx, cy, color=(1, 1, 1), op=1.0, shadow_op=0.75, anchor="c", **kw):
    if op <= 0.003 or not s:
        return
    a, sh = text_sprite(s, **kw)
    h, w = a.shape
    x0 = int(cx - w / 2) if anchor == "c" else (int(cx) if anchor == "l" else int(cx - w))
    y0 = int(cy - h / 2)
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    aa = a[ya - y0:yb - y0, xa - x0:xb - x0, None] * op
    ss = sh[ya - y0:yb - y0, xa - x0:xb - x0, None] * (op * shadow_op)
    reg = img[ya:yb, xa:xb]
    reg *= (1 - ss)
    reg *= (1 - aa)
    reg += aa * np.asarray(color, f32)


# ───────────────────────── 歌词 / 音频 ─────────────────────────
def load_lyrics():
    srt = subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-map", "0:s:0", "-f", "srt", "-"],
                         capture_output=True).stdout.decode("utf8")
    out = []
    for m in re.finditer(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)\n(.*?)\n\n", srt + "\n\n", re.S):
        g = m.groups()
        a = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
        b = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
        txt = g[8].strip()
        if txt.startswith("[") or b - a < 0.05:
            continue
        out.append((a, b, txt))
    return out


def load_env():
    """每帧的低频能量包络 (0..1)，用于随鼓点律动。"""
    path = os.path.join(WORK, "env.npy")
    if os.path.exists(path):
        return np.load(path)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-map", "0:a", "-ac", "1", "-ar", "8000",
                          "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(f32) / 32768
    from scipy.signal import butter, sosfilt
    lo = sosfilt(butter(4, 160, "low", fs=8000, output="sos"), x)
    hop = 8000 / FPS
    env = np.zeros(NF + 2, f32)
    full = np.zeros(NF + 2, f32)
    for i in range(NF + 2):
        a, b = int(i * hop), int((i + 1) * hop)
        if a >= len(x):
            break
        env[i] = np.sqrt(np.mean(lo[a:b] ** 2) + 1e-12)
        full[i] = np.sqrt(np.mean(x[a:b] ** 2) + 1e-12)
    env /= np.percentile(env, 97) + 1e-9
    full /= np.percentile(full, 97) + 1e-9
    env = np.clip(env, 0, 1.3)
    # 快起慢落
    sm = np.zeros_like(env)
    v = 0.0
    for i in range(len(env)):
        v = max(env[i], v * 0.86)
        sm[i] = v
    res = np.stack([sm, np.clip(full, 0, 1.3)], 0)
    np.save(path, res)
    return res


# ───────────────────────── 共享资源 ─────────────────────────
class Assets:
    def __init__(self):
        self._c = {}

    def get(self, name, fn):
        if name not in self._c:
            self._c[name] = fn()
        return self._c[name]

    @property
    def stars(self):
        return self.get("stars", lambda: make_stars(2400, 1500, 5200, 11))

    @property
    def stars2(self):
        return self.get("stars2", lambda: make_stars(2400, 1500, 1500, 12, 1.5))

    @property
    def sunglow(self):
        def mk():
            y, x = np.mgrid[-H:H, -W:W].astype(f32)
            d = np.sqrt(x * x + y * y)
            return (1 / (1 + (d / 90) ** 2) + 0.6 / (1 + (d / 420) ** 2)).astype(f32)
        return self.get("sunglow", mk)

    def sun(self, img, sx, sy, color, gain=1.0):
        sx, sy = int(sx), int(sy)
        if not (-W < sx < 2 * W and -H < sy < 2 * H) or gain <= 0:
            return
        g = self.sunglow
        y0, x0 = H - sy, W - sx
        ya, xa = max(0, y0), max(0, x0)
        yb, xb = min(2 * H, y0 + H), min(2 * W, x0 + W)
        if ya >= yb or xa >= xb:
            return
        img[ya - y0:yb - y0, xa - x0:xb - x0] += g[ya:yb, xa:xb, None] * (np.asarray(color, f32) * gain)

    @property
    def vignette(self):
        def mk():
            y, x = np.mgrid[0:H, 0:W].astype(f32)
            d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
            return (1 - 0.42 * np.clip(d - 0.35, 0, 1.2) ** 1.6)[..., None].astype(f32)
        return self.get("vig", mk)

    @property
    def grain(self):
        return self.get("grain", lambda: (np.random.default_rng(5).normal(0, 1, (H + 256, W + 256, 1)) * 0.012).astype(f32))


A = Assets()
G1 = radial(40, 2.2)
G2 = radial(120, 2.6)
G3 = radial(300, 3.0)
GS = radial(12, 2.0)


def person_mask(cx, base, h, umbrella=False):
    """栏杆边的孤独身影 (单通道 0..1)。"""
    m = np.zeros((H, W), np.uint8)
    s = h / 300.0
    P = lambda pts: np.array([[cx + x * s, base + y * s] for x, y in pts], np.int32)
    cv2.fillPoly(m, [P([(-34, -215), (34, -215), (44, -100), (40, 0), (8, 0), (0, -95), (-8, 0), (-40, 0), (-44, -100)])], 255, cv2.LINE_AA)
    cv2.circle(m, (int(cx), int(base - 250 * s)), int(27 * s), 255, -1, cv2.LINE_AA)
    cv2.fillPoly(m, [P([(-34, -210), (-58, -110), (-46, -105), (-26, -160)])], 255, cv2.LINE_AA)
    if umbrella:
        cv2.fillPoly(m, [P([(34, -210), (62, -235), (66, -222), (40, -180)])], 255, cv2.LINE_AA)
        cv2.line(m, tuple(P([(62, -228)])[0]), tuple(P([(62, -400)])[0]), 255, max(2, int(4 * s)), cv2.LINE_AA)
        cv2.ellipse(m, (int(cx + 62 * s), int(base - 385 * s)), (int(170 * s), int(80 * s)), 0, 180, 360, 255, -1, cv2.LINE_AA)
    else:
        cv2.fillPoly(m, [P([(34, -210), (58, -110), (46, -105), (26, -160)])], 255, cv2.LINE_AA)
    return m


def railing_mask(y, seed=0):
    m = np.zeros((H, W), np.uint8)
    cv2.rectangle(m, (0, y), (W, y + 9), 255, -1)
    cv2.rectangle(m, (0, y + 60), (W, y + 65), 255, -1)
    for x in range(40, W, 150):
        cv2.rectangle(m, (x, y - 14), (x + 12, H), 255, -1)
    for x in range(40, W, 30):
        cv2.rectangle(m, (x, y), (x + 3, H), 255, -1)
    cv2.rectangle(m, (0, y + 150), (W, H), 255, -1)
    return m


def river_reflect(img, hy, depth, t, gain=0.5, tint=(0.8, 0.9, 1.0), amp=5.0):
    """把地平线 hy 以上的画面倒映到 [hy, hy+depth)。"""
    src = img[max(0, hy - depth):hy][::-1]
    n = src.shape[0]
    rows = np.arange(n, dtype=f32)
    dx = (np.sin(rows * 0.31 + t * 2.3) * amp * (0.3 + rows / n) +
          np.sin(rows * 0.117 - t * 1.4) * amp * 1.6 * (rows / n))
    mx = (np.arange(W, dtype=f32)[None, :] + dx[:, None]).astype(f32)
    my = np.repeat(rows[:, None], W, 1).astype(f32)
    ref = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    ref = cv2.blur(ref, (1, 9))
    fall = (gain * (1 - 0.55 * rows / n))[:, None, None]
    band = (0.85 + 0.15 * np.sin(rows * 0.9 + t * 3.0 + np.sin(rows * 0.05) * 6))[:, None, None]
    img[hy:hy + n] = ref * fall * band * np.asarray(tint, f32)


# ───────────────────────── 场景 1：雨夜江边 ─────────────────────────
class Intro:
    def __init__(self):
        rng = np.random.default_rng(21)
        PW = W + 300
        plate = np.zeros((H, PW, 3), f32)
        yy = np.linspace(0, 1, H, dtype=f32)[:, None, None]
        plate += lerp(col(0.006, 0.01, 0.03), col(0.05, 0.06, 0.13), np.clip(yy / 0.6, 0, 1))
        bok = np.zeros((H, PW, 3), np.uint8)
        pal = [(255, 170, 80), (255, 210, 130), (120, 200, 255), (255, 90, 80), (255, 255, 230), (190, 130, 255), (90, 255, 200)]
        for _ in range(230):
            x, y = rng.integers(0, PW), int(rng.normal(560, 40))
            r = int(rng.integers(8, 34))
            c = np.array(pal[rng.integers(len(pal))]) * rng.uniform(0.15, 0.6)
            layer = np.zeros_like(bok)
            cv2.circle(layer, (int(x), y), r, c.tolist(), -1, cv2.LINE_AA)
            cv2.circle(layer, (int(x), y), r, (c * 1.25).clip(0, 255).tolist(), 2, cv2.LINE_AA)
            bok = cv2.max(bok, layer)
        plate += cv2.GaussianBlur(bok.astype(f32) / 255, (0, 0), 3.0) * 0.85
        self.plate = plate
        self.sil = np.maximum(railing_mask(850), person_mask(1420, 1000, 400, umbrella=True)).astype(f32)[..., None] / 255
        n = 420
        self.rx = rng.uniform(0, W + 300, n)
        self.rs = rng.uniform(1100, 1900, n)
        self.rp = rng.uniform(0, H + 200, n)
        self.rl = rng.uniform(22, 60, n)

    def rain(self, img, t, gain):
        if gain <= 0:
            return
        cv = np.zeros((H, W), np.uint8)
        y = (self.rp + t * self.rs) % (H + 200) - 100
        x = self.rx - y * 0.14
        for i in range(len(y)):
            cv2.line(cv, (int(x[i]), int(y[i])), (int(x[i] - self.rl[i] * 0.14), int(y[i] + self.rl[i])), 150, 1, cv2.LINE_AA)
        img += (cv.astype(f32) / 255 * gain)[..., None] * col(0.6, 0.72, 0.9)

    def render(self, t, e):
        pan = 40 + t * 5.0
        x0 = int(pan)
        img = self.plate[:, x0:x0 + W].copy()
        img[:640] *= 1 + 0.06 * math.sin(t * 1.3)
        river_reflect(img, 640, 300, t, gain=0.55, amp=7)
        img *= (1 - self.sil * 0.985)
        self.rain(img, t, 0.5)
        img *= sstep(0, 1.6, t)
        op = pulse(t, 0.5, 4.6, 1.0, 0.8)
        draw_text(img, "明天还没来", W / 2, 215, (1, 0.96, 0.88), op, fname="MaShanZheng", size=190, weight=None, spacing=14, shadow=10)
        draw_text(img, "漫长的岁月 · 等待最后的灿烂", W / 2, 350, (0.9, 0.85, 0.75), op * 0.95, size=40, weight=600, spacing=10)
        return img


# ───────────────────────── 场景 2：城市黎明 → 升空 ─────────────────────────
def skyline(seed, w, hmax, hmin, tone, win_p, bw=(40, 120)):
    rng = np.random.default_rng(seed)
    rgb = np.zeros((hmax + 40, w, 3), f32)
    alpha = np.zeros((hmax + 40, w), f32)
    wa = np.zeros((hmax + 40, w, 3), f32)
    wb = np.zeros_like(wa)
    x = -20
    Ht = hmax + 40
    while x < w:
        b = int(rng.integers(*bw))
        h = int(rng.uniform(hmin, hmax) * (0.6 + 0.4 * rng.random()))
        x1 = min(w, x + b)
        xa = max(0, x)
        alpha[Ht - h:, xa:x1] = 1
        rgb[Ht - h:, xa:x1] = np.asarray(tone, f32) * rng.uniform(0.7, 1.2)
        if rng.random() < 0.25:
            cv2.line(alpha, ((xa + x1) // 2, Ht - h), ((xa + x1) // 2, Ht - h - int(rng.integers(15, 50))), 1.0, 2)
        wc = col(1.0, 0.82, 0.5) if rng.random() < 0.7 else col(0.6, 0.85, 1.0)
        for wy in range(Ht - h + 8, Ht - 6, 13):
            for wx in range(xa + 5, x1 - 6, 10):
                r = rng.random()
                if r < win_p:
                    (wa if rng.random() < 0.5 else wb)[wy:wy + 6, wx:wx + 5] = wc * rng.uniform(0.4, 1.0)
                if r < win_p * 0.35:
                    wa[wy:wy + 6, wx:wx + 5] = wb[wy:wy + 6, wx:wx + 5] = wc * rng.uniform(0.5, 1.0)
        x += b + int(rng.integers(0, 6))
    return rgb, alpha[..., None], wa, wb


class City:
    def __init__(self, intro):
        self.intro = intro
        self.layers = [skyline(31, 2300, 330, 120, (0.045, 0.05, 0.085), 0.30, (30, 80)),
                       skyline(32, 2500, 520, 200, (0.025, 0.028, 0.05), 0.42, (50, 130)),
                       skyline(33, 2700, 700, 260, (0.008, 0.009, 0.018), 0.5, (80, 190))]
        self.cloud = fbm(W, 2400, 41, 6, 3)
        rng = np.random.default_rng(34)
        n = 46
        self.tx = rng.uniform(0, W, n)
        self.tv = rng.uniform(500, 1500, n) * rng.choice([-1, 1], n)
        self.tl = rng.uniform(60, 220, n)

    def render(self, t, e):
        d = sstep(36, 82, t)                 # 天亮程度
        rise = sstep(76, 93, t) ** 1.5       # 升空
        yoff = rise * 2300
        yy = np.linspace(0, 1, H, dtype=f32)[:, None]
        hz = np.clip((yy * H + yoff * 0.55) / H, 0, 1) ** 1.6   # 0 顶 → 1 地平线
        top = lerp(col(0.012, 0.018, 0.06), col(0.07, 0.13, 0.32), d)
        hor = lerp(col(0.07, 0.07, 0.15), col(1.0, 0.52, 0.26), d)
        sky = top[None, :] * (1 - hz) + hor[None, :] * hz
        sky = sky * (1 - 0.9 * rise) + col(0.004, 0.006, 0.016) * rise
        img = np.repeat(sky[:, None, :], W, 1).astype(f32)
        st = max(0.0, 0.25 * (1 - d) + rise * 0.95)
        if st > 0.01:
            img += shift_wrap(A.stars, 200, 300 - yoff * 0.08) * st
        if d > 0.2 and rise < 0.98:
            A.sun(img, 1180, 850 + yoff * 0.6 - 60 * d, col(1.0, 0.55, 0.25), 0.55 * d * (1 - rise))
        pan = (t - 38) * 9
        wmix = 0.5 + 0.5 * math.sin(t * 0.9)
        wg = (1 - 0.6 * d) * (0.85 + 0.25 * e)
        for i, (rgb, al, wa, wb) in enumerate(self.layers):
            par = (0.45, 0.7, 1.0)[i]
            base = H - (160, 60, -40)[i] + yoff * (0.75 + 0.25 * par)
            lh, lw = rgb.shape[:2]
            y0 = int(base - lh)
            if y0 >= H:
                continue
            x0 = int(60 + pan * par) % (lw - W)
            ya, yb = max(0, y0), min(H, y0 + lh)
            sl = (slice(ya - y0, yb - y0), slice(x0, x0 + W))
            a = al[sl]
            haze = lerp(col(0.03, 0.035, 0.07), hor * 0.5, d) * (1 - par) * 0.9
            c = rgb[sl] + haze + (wa[sl] * wmix + wb[sl] * (1 - wmix)) * wg
            img[ya:yb] = img[ya:yb] * (1 - a) + c * a
            if yb < H:
                img[yb:] = rgb[-1, 0] * 0.6
        # 车流光轨
        ry = int(H - 26 + yoff)
        if ry < H + 40:
            cv = np.zeros((H, W, 3), np.uint8)
            x = (self.tx + (t - 38) * self.tv * (0.8 + 0.6 * e)) % (W + 400) - 200
            for i in range(len(x)):
                c = (255, 70, 50) if self.tv[i] > 0 else (255, 240, 210)
                yv = ry + (i % 4) * 9 - 18
                cv2.line(cv, (int(x[i]), yv), (int(x[i] - self.tl[i] * np.sign(self.tv[i])), yv), c, 3, cv2.LINE_AA)
            band = slice(max(0, ry - 60), min(H, ry + 60))
            if band.stop > band.start:
                img[band] += cv2.GaussianBlur(cv[band].astype(f32) / 255, (0, 0), 3) * 1.6
        # 云层
        if rise > 0.02:
            cy = int(-2400 + yoff * 1.75 - 300)
            ya, yb = max(0, cy), min(H, cy + 2400)
            if yb > ya:
                c = self.cloud[ya - cy:yb - cy]
                edge = np.clip(np.minimum(np.arange(ya - cy, yb - cy), 2400 - np.arange(ya - cy, yb - cy)) / 500, 0, 1).astype(f32)[:, None]
                a = (np.clip((c - 0.38) * 2.6, 0, 1) * edge)[..., None]
                lit = lerp(col(0.9, 0.55, 0.5), col(0.35, 0.4, 0.6), c[..., None])
                img[ya:yb] = img[ya:yb] * (1 - a * 0.92) + lit * a * 0.8
        self.intro.rain(img, t, 0.5 * (1 - sstep(38, 58, t)))
        return img


# ───────────────────────── 场景 3：地球 ─────────────────────────
class Earth:
    TW, TH = 2048, 1024

    def __init__(self):
        TW, TH = self.TW, self.TH
        h = fbm(TW, TH, 51, 7, 4, tile_x=True, gain=0.55)
        m = fbm(TW, TH, 52, 6, 6, tile_x=True)
        lat = np.abs(np.linspace(-1, 1, TH, dtype=f32))[:, None]
        land = np.clip((h - 0.53) * 14, 0, 1)[..., None]
        ocean = lerp(col(0.01, 0.045, 0.16), col(0.03, 0.17, 0.36), np.clip((h - 0.25) * 3, 0, 1)[..., None])
        dry = np.clip(m * 1.4 - 0.25 + (0.35 - np.abs(lat - 0.3)) * 0.8, 0, 1)[..., None]
        ground = lerp(col(0.07, 0.22, 0.07), col(0.5, 0.4, 0.22), dry)
        ground = lerp(ground, col(0.35, 0.3, 0.26), np.clip((h - 0.72) * 6, 0, 1)[..., None])
        day = ocean * (1 - land) + ground * land
        ice = np.clip((lat + (m - 0.5) * 0.2 - 0.9) * 14, 0, 1)[..., None]
        self.day = (day * (1 - ice) + col(0.9, 0.93, 0.97) * ice).astype(f32)
        rng = np.random.default_rng(53)
        pop = fbm(TW, TH, 54, 5, 10, tile_x=True)
        lights = (rng.random((TH, TW), dtype=f32) < (np.clip(pop - 0.55, 0, 1) * 0.7)) * land[..., 0] * (1 - ice[..., 0])
        self.night = np.clip(cv2.GaussianBlur(lights.astype(f32), (0, 0), 1.1) * 3.2, 0, 1.5)
        c = fbm(TW, TH, 55, 7, 5, tile_x=True, gain=0.6)
        self.clouds = np.clip((c - 0.56) * 3.0, 0, 1) ** 1.3

    def render(self, t, e):
        u = sstep(90, 116, t)
        R = math.exp(lerp(math.log(2900), math.log(330), u))
        cx = lerp(900, 960, u)
        cy = lerp(1080 + 2900 - 470, 560, u ** 0.8)
        phi = lerp(-0.10, 0.95, sstep(91, 113, t))
        L = np.array([0.38, -math.cos(phi), math.sin(phi)], f32)
        L /= np.linalg.norm(L)
        img = shift_wrap(A.stars, 300 + t * 3, 200) * 0.9
        # 太阳（在晨昏线上方的地平弧处升起）
        sx, sy = cx + L[0] * R * 1.0, cy + L[1] * R * 1.0
        sg = (1 - sstep(96, 110, t)) * sstep(90.5, 94, t)
        if sg > 0:
            A.sun(img, sx, sy, col(1.0, 0.9, 0.75), 0.8 * sg * (1 + 0.15 * e))
            streak = np.zeros((H, W), f32)
            yy = int(sy)
            if 0 <= yy < H:
                xs = np.arange(W, dtype=f32)
                streak[max(0, yy - 2):yy + 3] = 1 / (1 + ((xs - sx) / 500) ** 2)
                img += cv2.GaussianBlur(streak, (0, 0), 3)[..., None] * col(1.0, 0.85, 0.7) * 0.6 * sg
        x0, x1 = int(max(0, cx - R * 1.08)), int(min(W, cx + R * 1.08))
        y0, y1 = int(max(0, cy - R * 1.08)), int(min(H, cy + R * 1.08))
        if x1 > x0 and y1 > y0:
            xs = (np.arange(x0, x1, dtype=f32) - cx) / R
            ys = (np.arange(y0, y1, dtype=f32) - cy) / R
            nx, ny = np.meshgrid(xs, ys)
            r2 = nx * nx + ny * ny
            inside = r2 < 1
            nz = np.sqrt(np.clip(1 - r2, 0, 1))
            rot = t * 0.035 + 1.0
            lon = np.arctan2(nx, nz)
            v = ((np.arcsin(np.clip(ny, -1, 1)) / math.pi + 0.5) * (self.TH - 1)).astype(f32)
            uu = (((lon + rot) / (2 * math.pi)) % 1.0 * self.TW).astype(f32)
            uc = (((lon + rot * 1.35 + 2) / (2 * math.pi)) % 1.0 * self.TW).astype(f32)
            day = cv2.remap(self.day, uu, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            ngt = cv2.remap(self.night, uu, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            cl = cv2.remap(self.clouds, uc, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            ndl = nx * L[0] + ny * L[1] + nz * L[2]
            dif = np.clip(ndl * 1.05 + 0.04, 0, 1)
            term = np.clip(1 - np.abs(ndl) * 5, 0, 1) * np.clip(ndl * 4 + 0.6, 0, 1)
            surf = day * 1.25 * (1 - cl[..., None] * 0.85) + cl[..., None] * 0.8
            lit = surf * (dif[..., None] * col(1.0, 0.97, 0.92) + term[..., None] * col(0.9, 0.35, 0.12) * 0.55)
            nightside = np.clip(-ndl * 6 + 0.3, 0, 1) * (1 - cl * 0.8)
            lit += (ngt * nightside)[..., None] * col(1.0, 0.75, 0.4) * 0.9
            rim = (1 - nz) ** 3.2
            lit += (rim * np.clip(ndl * 2 + 0.5, 0, 1))[..., None] * col(0.3, 0.55, 1.0) * 0.9
            reg = img[y0:y1, x0:x1]
            edge = np.clip((1 - np.sqrt(r2)) * R * 0.8, 0, 1)[..., None]
            m = inside[..., None] * edge
            reg *= (1 - m)
            reg += lit * m
            rr = np.sqrt(r2)
            halo = np.exp(-np.clip(rr - 1, 0, 9) / (0.012 + 6.0 / R)) * (rr >= 1) * np.clip(
                (nx * L[0] + ny * L[1]) / np.maximum(rr, 1e-3) * 1.6 + 0.75 + L[2], 0, 1.3)
            reg += halo[..., None] * col(0.3, 0.58, 1.0) * 0.75
        return img


# ───────────────────────── 场景 4：太阳系 ─────────────────────────
PLANETS = [  # 名称, 轨道 AU, 公转周期文字, 颜色, 大小
    ("水星", 0.39, "88 天一圈", (0.75, 0.7, 0.65), 4),
    ("金星", 0.72, "225 天一圈", (1.0, 0.85, 0.55), 6),
    ("地球", 1.0, "1 年一圈", (0.35, 0.65, 1.0), 6.5),
    ("火星", 1.52, "1.9 年一圈", (1.0, 0.45, 0.3), 5),
    ("木星", 5.2, "12 年一圈", (0.95, 0.75, 0.55), 15),
    ("土星", 9.5, "29 年一圈", (0.95, 0.85, 0.6), 12.5),
    ("天王星", 19.2, "84 年一圈", (0.6, 0.9, 0.95), 9),
    ("海王星", 30.0, "165 年一圈", (0.35, 0.5, 1.0), 9),
]


class Solar:
    TILT = 0.5

    def __init__(self):
        rng = np.random.default_rng(61)
        self.th0 = rng.uniform(0, 2 * math.pi, len(PLANETS))
        self.th0[2] = 2.5
        n = 900
        self.ar = rng.uniform(2.3, 3.4, n)
        self.at = rng.uniform(0, 2 * math.pi, n)

    @staticmethod
    def disp(a):
        return 200 * a ** 0.42

    def zoom(self, t):
        if t < 157.5:
            return math.exp(lerp(math.log(2.7), math.log(0.92), sstep(112, 157.5, t)))
        return math.exp(lerp(math.log(0.92), math.log(0.012), sstep(157.5, 168, t) ** 0.8))

    def render(self, t, e):
        z = self.zoom(t)
        cx, cy = W / 2, H / 2 + 10
        img = affine(A.stars, 1.0 + 0.1 * z, t * 0.004, W / 2, H / 2, border=cv2.BORDER_WRAP)[0] * 0.75
        cv = np.zeros((H, W, 3), np.uint8)
        tt = t - 114
        lab = sstep(140, 146, t) * (1 - sstep(157, 160, t))
        fade = 1 - sstep(160, 166, t)
        pos = []
        for i, (name, a, per, c, sz) in enumerate(PLANETS):
            r = self.disp(a) * z
            if r < 1.2:
                continue
            w = 1.9 * a ** -1.5 + 0.012
            th = self.th0[i] + w * tt
            x, y = cx + r * math.cos(th), cy + r * math.sin(th) * self.TILT
            oc = int(70 * fade)
            cv2.ellipse(cv, (int(cx), int(cy)), (int(r), int(r * self.TILT)), 0, 0, 360, (oc, int(oc * 1.1), int(oc * 1.5)), 1, cv2.LINE_AA)
            arc = min(2.2, w * 2.2 + 0.25)
            for k in range(10):
                a0 = math.degrees(th - arc * (k + 1) / 10)
                a1 = math.degrees(th - arc * k / 10)
                b = (1 - k / 10) ** 1.6 * 0.85 * fade
                cc = tuple(int(255 * v * b) for v in c)
                cv2.ellipse(cv, (int(cx), int(cy)), (int(r), int(r * self.TILT)), 0, a0, a1, cc, 2, cv2.LINE_AA)
            pos.append((i, x, y))
        if z > 0.25:
            ax = cx + self.disp(self.ar) * z * np.cos(self.at + tt * 0.12)
            ay = cy + self.disp(self.ar) * z * np.sin(self.at + tt * 0.12) * self.TILT
            ok = (ax >= 0) & (ax < W) & (ay >= 0) & (ay < H)
            cv[ay[ok].astype(int), ax[ok].astype(int)] = (95, 90, 80)
        img += cv.astype(f32) / 255
        sgain = min(1.0, z ** 0.6) * (1 + 0.12 * e)
        add_sprite(img, G3, cx, cy, (1.0, 0.7, 0.35), 0.75 * sgain)
        add_sprite(img, G2, cx, cy, (1.0, 0.85, 0.55), 0.9 * sgain)
        add_sprite(img, G1, cx, cy, (1, 1, 0.95), 2.5 * sgain)
        for i, x, y in pos:
            name, a, per, c, sz = PLANETS[i]
            s = max(1.2, sz * (0.55 + 0.45 * z) * min(1, z * 2.5))
            add_sprite(img, G1, x, y, c, 0.5 * fade * min(1, z * 2))
            if i == 5:
                ring = np.zeros((80, 160, 3), np.uint8)
                cv2.ellipse(ring, (80, 40), (int(s * 2.3), int(s * 0.8)), -15, 0, 360, (200, 180, 130), max(1, int(s / 4)), cv2.LINE_AA)
                xa, ya = int(x) - 80, int(y) - 40
                if 0 <= xa and xa + 160 < W and 0 <= ya and ya + 80 < H:
                    img[ya:ya + 80, xa:xa + 160] += ring.astype(f32) / 255 * fade
            pc = np.zeros((64, 64, 3), np.uint8)
            cv2.circle(pc, (32, 32), int(round(s)), tuple(int(255 * v) for v in c), -1, cv2.LINE_AA)
            xa, ya = int(x) - 32, int(y) - 32
            if 0 <= xa and xa + 64 < W and 0 <= ya and ya + 64 < H:
                img[ya:ya + 64, xa:xa + 64] += pc.astype(f32) / 255 * fade
            if lab > 0 and 0 < x < W - 150 and i not in (1, 3):
                ly = y - 48 if i % 2 == 0 else y + 34
                draw_text(img, name + " · " + per, x, ly, tuple(0.5 + 0.5 * v for v in c), lab * 0.95, size=22, weight=700, shadow=4)
        return img


# ───────────────────────── 场景 5：暗淡蓝点 / 星海 ─────────────────────────
class Dot:
    def __init__(self):
        y, x = np.mgrid[0:H, 0:W].astype(f32)
        beams = np.zeros((H, W, 3), f32)
        for off, wd, c in [(-260, 90, (0.5, 0.25, 0.12)), (40, 55, (0.28, 0.42, 0.5)), (330, 120, (0.35, 0.2, 0.4))]:
            d = (x - W / 2 - off) * 0.94 + (y - H / 2) * 0.34
            beams += np.exp(-(d / wd) ** 2)[..., None] * col(*c)
        self.beams = beams * (0.75 + 0.25 * fbm(W, H, 71, 4, 4))[..., None]

    def render(self, t, e):
        img = shift_wrap(A.stars, 500 + t * 2, 600 + t * 1.2) * 0.55
        k = sstep(165, 170, t)
        img += self.beams * 0.42 * k
        x, y = 990 + (t - 170) * 1.2, 505 - (t - 170) * 0.6
        tw = 0.8 + 0.2 * math.sin(t * 2.2)
        add_sprite(img, GS, x, y, (0.45, 0.7, 1.0), 1.6 * tw)
        add_sprite(img, G1, x, y, (0.3, 0.5, 1.0), 0.35 * tw)
        op = pulse(t, 168.5, 178.5, 1.5, 1.5)
        draw_text(img, "地球", x + 46, y - 4, (0.75, 0.85, 1.0), op * 0.9, anchor="l", size=26, weight=600, shadow=4)
        draw_text(img, "六十亿公里之外回望，一粒悬浮在阳光里的微尘", W / 2, 150, (0.85, 0.85, 0.9), op * 0.95, size=32, weight=500, spacing=6)
        return img


class Flight:
    def __init__(self):
        a = fbm(1600, 1000, 81, 6, 3)
        b = fbm(1600, 1000, 82, 6, 4)
        neb = (np.clip(a - 0.42, 0, 1) ** 1.5)[..., None] * col(1.0, 0.42, 0.3) * 2.0
        neb += (np.clip(b - 0.45, 0, 1) ** 1.5)[..., None] * col(0.25, 0.45, 1.0) * 2.2
        neb += (np.clip(a * b * 2 - 0.42, 0, 1) ** 2)[..., None] * col(1.0, 0.9, 0.7) * 2.5
        self.neb = neb.astype(f32)

    def render(self, t, e):
        u = (t - 176) / 18.0
        img = np.zeros((H, W, 3), f32)
        for i, (tex, sp, g) in enumerate([(A.stars, 0.10, 0.7), (A.stars2, 0.28, 0.8), (A.stars2, 0.7, 0.55)]):
            s = 1.0 + sp * max(0, u) * (1 + i * 0.6)
            img += affine(tex, s, 0.02 * t * (1 + i), W / 2 + i * 137, H / 2 - i * 91, border=cv2.BORDER_WRAP)[0] * g
        k = sstep(178, 193, t)
        n = affine(self.neb, 1.3 + 0.5 * max(0, u), 0.25 + 0.01 * t, W / 2, H / 2, border=cv2.BORDER_REFLECT)[0]
        img += (1 - np.exp(-n * 0.9)) * (0.12 + 0.8 * k ** 1.5)
        add_sprite(img, G3, W / 2, H / 2, (1.0, 0.85, 0.7), 0.9 * sstep(186, 194, t) ** 2)
        return img


# ───────────────────────── 场景 6：银河 + 逆境七星 ─────────────────────────
FIGURES = [
    ("庄子", "战国 · 约前369—前286", "身居陋巷，织履为生，辞楚相而不就", "以逍遥之笔，写尽天地大美"),
    ("刘邦", "西汉 · 汉高祖", "泗水亭长，年近半百方才起兵", "屡败屡战，终开四百年大汉"),
    ("刘备", "三国 · 汉昭烈帝", "织席贩履，半生颠沛，寄人篱下", "年近五十始遇孔明，终立蜀汉"),
    ("朱元璋", "明 · 明太祖", "放牛娃、小沙弥，托钵乞食三年", "从一无所有，到开创大明"),
    ("苏轼", "北宋 · 东坡居士", "乌台诗案，一贬再贬：黄州、惠州、儋州", "贬谪路上，写出千古绝唱"),
    ("赵孟頫", "元 · 松雪道人", "宋室之后，国亡闲居，十年苦学", "终成一代书画宗师"),
    ("八大山人", "清初 · 朱耷", "国破家亡，隐于僧道数十年", "花甲之后，笔墨登峰造极"),
]
# 北斗七星（归一化坐标）
DIPPER = [(0.00, 0.30), (0.17, 0.12), (0.33, 0.20), (0.49, 0.34), (0.56, 0.62), (0.80, 0.72), (0.86, 0.42)]
DIPPER_LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3)]
V3_T0, V3_T1 = 216.1, 262.0
V3_STEP = (V3_T1 - V3_T0) / 7


def star_flare(img, x, y, color, gain):
    if gain <= 0:
        return
    add_sprite(img, G1, x, y, color, 1.1 * gain)
    add_sprite(img, GS, x, y, (1, 1, 1), 1.6 * gain)
    L = int(46 * min(1.6, gain))
    xi, yi = int(x), int(y)
    if L < 3 or not (L < xi < W - L and L < yi < H - L):
        return
    fall = (1 - np.abs(np.arange(-L, L + 1, dtype=f32)) / L) ** 2 * 0.8 * gain
    img[yi, xi - L:xi + L + 1] += fall[:, None] * np.asarray(color, f32)
    img[yi - L:yi + L + 1, xi] += fall[:, None] * np.asarray(color, f32)


def dipper_draw(img, t, ox, oy, sw, sh, lit, names=True, gain=1.0, label_op=1.0):
    """lit: 每颗星的亮度 0..1 列表。"""
    pts = [(ox + px * sw, oy + py * sh) for px, py in DIPPER]
    cv = np.zeros((H, W), np.uint8)
    for a, b in DIPPER_LINES:
        k = min(lit[a], lit[b])
        if k > 0.02:
            cv2.line(cv, (int(pts[a][0]), int(pts[a][1])), (int(pts[b][0]), int(pts[b][1])), int(110 * k * gain), 1, cv2.LINE_AA)
    img += (cv.astype(f32) / 255)[..., None] * col(0.8, 0.85, 1.0)
    for i, (x, y) in enumerate(pts):
        if lit[i] <= 0.01:
            continue
        tw = 0.85 + 0.15 * math.sin(t * 2.1 + i * 1.7)
        star_flare(img, x, y, (1.0, 0.9, 0.7), lit[i] * tw * gain)
        if names:
            draw_text(img, FIGURES[i][0], x, y + 44, (1.0, 0.88, 0.62), lit[i] * 0.9 * label_op, size=24, weight=600, shadow=4)
    return pts


class Galaxy:
    S = 2200

    def __init__(self):
        path = os.path.join(WORK, "galaxy.npy")
        if os.path.exists(path):
            self.tex = np.load(path)
            return
        S = self.S
        rng = np.random.default_rng(91)
        img = np.zeros((S, S, 3), f32)

        def splat(r, th, c, wgt):
            x = (S / 2 + r * np.cos(th)).astype(int)
            y = (S / 2 + r * np.sin(th)).astype(int)
            ok = (x >= 0) & (x < S) & (y >= 0) & (y < S) & (r < Rm * 1.0)
            np.add.at(img, (y[ok], x[ok]), c[ok] * wgt[ok, None])

        Rm = S * 0.46
        pitch = 0.33
        for arm, (off, strength) in enumerate([(0, 1.0), (math.pi, 1.0), (math.pi / 2, 0.55), (3 * math.pi / 2, 0.55)]):
            n = int(260000 * strength)
            r = Rm * (rng.exponential(0.34, n) + 0.05)
            th = np.log(r / (Rm * 0.06)) / pitch + off + rng.normal(0, 0.16 + 0.1 * rng.random(n), n)
            r = np.abs(r + rng.normal(0, 14, n)) + 1
            hot = rng.random(n)
            c = np.stack([0.38 + 0.35 * hot, 0.6 + 0.15 * hot, 1.25 - 0.35 * hot], 1).astype(f32)
            splat(r, th, c, (rng.random(n) ** 3 * 2 + 0.25).astype(f32))
            m = int(1300 * strength)
            r2 = Rm * np.clip(rng.uniform(0.15, 0.9, m), 0, 1)
            th2 = np.log(r2 / (Rm * 0.06)) / pitch + off + rng.normal(0, 0.07, m) - 0.06
            splat(r2, th2, np.tile(col(1.0, 0.3, 0.5), (m, 1)), np.full(m, 30.0, f32))
        n = 320000
        r = Rm * rng.exponential(0.25, n)
        th = rng.uniform(0, 2 * math.pi, n)
        splat(r, th, np.tile(col(1.0, 0.72, 0.42), (n, 1)), np.full(n, 0.5, f32))
        soft = cv2.GaussianBlur(img, (0, 0), 2.2) * 5 + cv2.GaussianBlur(img, (0, 0), 10) * 14 + cv2.GaussianBlur(img, (0, 0), 40) * 22
        fine = img * 0.9 + cv2.GaussianBlur(img, (0, 0), 0.9) * 1.6
        y, x = np.mgrid[0:S, 0:S].astype(f32)
        rr = np.sqrt((x - S / 2) ** 2 + (y - S / 2) ** 2)
        th = np.arctan2(y - S / 2, x - S / 2)
        ph = (th - np.log(np.maximum(rr, 1) / (Rm * 0.06)) / pitch + 0.42) % math.pi
        lane = np.exp(-((ph - math.pi / 2) / 0.2) ** 2) * np.clip(rr / (Rm * 0.15), 0, 1) * np.clip(1.25 - rr / Rm, 0, 1)
        dust = 1 - np.clip(lane * (0.35 + 0.9 * fbm(S, S, 92, 6, 8)), 0, 0.85)
        tex = (soft * 0.05 + fine * 0.45) * dust[..., None]
        tex += (np.exp(-(rr / (Rm * 0.07)) ** 1.3) * 1.1 + np.exp(-(rr / (Rm * 0.28)) ** 2) * 0.12)[..., None] * col(1.0, 0.8, 0.5)
        tex *= np.clip((1.0 - rr / Rm) * 4, 0, 1)[..., None]
        self.tex = (1 - np.exp(-tex * 0.9)).astype(f32)
        np.save(path, self.tex)

    def render(self, t, e):
        S = self.S
        v3 = sstep(214.5, 219, t)
        z = math.exp(lerp(math.log(3.3), math.log(0.6), sstep(193, 214, t) ** 0.75)) * lerp(1.0, 0.9, sstep(216, 262, t))
        ang = 0.6 + t * 0.016
        # 太阳的位置（纹理坐标）
        sr, sa = S * 0.46 * 0.5, 2.05
        sxT, syT = S / 2 + sr * math.cos(sa), S / 2 + sr * math.sin(sa)
        foc = 1 - sstep(194, 207, t)
        tcx, tcy = lerp(S / 2, sxT, foc), lerp(S / 2, syT, foc)
        gx = lerp(W / 2, 1300, v3)
        gy = lerp(H / 2, 590, v3)
        img = affine(A.stars, 1.0, t * 0.003, W / 2, H / 2, border=cv2.BORDER_WRAP)[0] * 0.6
        g, M = affine(self.tex, z, ang, gx, gy, sy=0.56, tcx=tcx, tcy=tcy)
        bright = (1.0 + 0.25 * e) * lerp(1.0, 0.7, v3)
        img += g * bright
        px, py = M[0, 0] * sxT + M[0, 1] * syT + M[0, 2], M[1, 0] * sxT + M[1, 1] * syT + M[1, 2]
        mk = pulse(t, 196.0, 208.5, 0.8, 1.2)
        if mk > 0:
            cv = np.zeros((H, W), np.uint8)
            rad = int(20 + 5 * math.sin(t * 4))
            cv2.circle(cv, (int(px), int(py)), rad, 255, 2, cv2.LINE_AA)
            cv2.line(cv, (int(px) + rad, int(py) - rad), (int(px) + 80, int(py) - 80), 255, 1, cv2.LINE_AA)
            img += (cv.astype(f32) / 255 * mk)[..., None]
            draw_text(img, "你在这里", px + 92, py - 100, (1, 1, 1), mk, anchor="l", size=34, weight=700)
            draw_text(img, "银河系 · 两千亿颗恒星中的一颗", px + 92, py - 58, (0.8, 0.85, 0.95), mk * 0.85, anchor="l", size=22, weight=400, shadow=4)
        # 开场闪白
        fl = max(0.0, 1 - (t - 194.2) / 1.3) if t >= 194.1 else 0.0
        if fl > 0:
            img += fl ** 2 * 0.95
        # 第三段：七位古人 → 北斗七星
        if v3 > 0:
            lit = [sstep(V3_T0 + i * V3_STEP, V3_T0 + i * V3_STEP + 1.0, t) for i in range(7)]
            dipper_draw(img, t, 1010, 110, 760, 330, lit, names=True)
            draw_text(img, "有人开花晚 —— 他们，都曾在逆境里等了很久", 150, 150, (0.82, 0.8, 0.75), v3 * 0.85 * (1 - sstep(260.5, 262, t)), anchor="l", size=30, weight=500, spacing=4)
            for i, (name, era, l1, l2) in enumerate(FIGURES):
                a = V3_T0 + i * V3_STEP
                op = pulse(t, a, a + V3_STEP, 0.6, 0.5)
                if op <= 0:
                    continue
                dy = (1 - sstep(a, a + 1.2, t)) * 26
                x = 150
                draw_text(img, name, x - 30, 350 + dy, (1.0, 0.95, 0.85), op, anchor="l", fname="MaShanZheng", size=170, weight=None, spacing=10, shadow=10)
                cv2.rectangle(img, (x, int(468 + dy)), (x + 70, int(472 + dy)), (float(0.8 * op), float(0.2 * op), float(0.15 * op)), -1)
                draw_text(img, era, x - 12, 512 + dy, (1.0, 0.8, 0.5), op, anchor="l", size=32, weight=600, spacing=3)
                draw_text(img, l1, x - 14, 590 + dy, (0.95, 0.95, 0.95), op, anchor="l", size=40, weight=600, spacing=2)
                draw_text(img, l2, x - 14, 654 + dy, (1.0, 0.9, 0.7), op, anchor="l", size=40, weight=800, spacing=2)
        return img


# ───────────────────────── 场景 7：滨江路星河演唱会 ─────────────────────────
def draw_figure(m, x, base, h, kind, raise_arm=0):
    """古人剪影。m: uint8 单通道。"""
    P = lambda pts: np.array([[x + px * h, base - py * h] for px, py in pts], np.int32)
    fill = lambda pts: cv2.fillPoly(m, [P(pts)], 255, cv2.LINE_AA)
    fill([(-0.13, 0.80), (0.13, 0.80), (0.17, 0.45), (0.23, 0.0), (-0.23, 0.0), (-0.17, 0.45)])      # 长袍
    if raise_arm >= 0:
        fill([(-0.13, 0.80), (-0.27, 0.52), (-0.25, 0.36), (-0.12, 0.42), (-0.10, 0.6)])           # 垂袖
    if raise_arm <= 0:
        fill([(0.13, 0.80), (0.27, 0.52), (0.25, 0.36), (0.12, 0.42), (0.10, 0.6)])
    if raise_arm > 0:
        fill([(0.11, 0.80), (0.30, 1.02), (0.36, 0.98), (0.30, 0.72), (0.14, 0.62)])               # 举右臂
    if raise_arm < 0:
        fill([(-0.11, 0.80), (-0.30, 1.02), (-0.36, 0.98), (-0.30, 0.72), (-0.14, 0.62)])
    fill([(-0.035, 0.86), (0.035, 0.86), (0.04, 0.79), (-0.04, 0.79)])
    cv2.circle(m, (int(x), int(base - 0.905 * h)), int(0.068 * h), 255, -1, cv2.LINE_AA)
    if kind == "bun":            # 庄子：发髻
        cv2.circle(m, (int(x), int(base - 0.995 * h)), int(0.032 * h), 255, -1, cv2.LINE_AA)
        fill([(-0.005, 1.0), (0.09, 1.03), (0.09, 1.015), (-0.005, 0.985)])
    elif kind == "mian":         # 帝王冕旒
        fill([(-0.055, 0.96), (0.055, 0.96), (0.05, 1.02), (-0.05, 1.02)])
        fill([(-0.15, 1.035), (0.15, 1.005), (0.15, 1.025), (-0.15, 1.055)])
        for k in (-0.14, -0.11, -0.08, 0.08, 0.11, 0.14):
            cv2.line(m, tuple(P([(k, 1.04 - k * 0.1)])[0]), tuple(P([(k, 0.95)])[0]), 255, 1, cv2.LINE_AA)
    elif kind == "ming":         # 翼善冠
        cv2.ellipse(m, (int(x), int(base - 0.955 * h)), (int(0.07 * h), int(0.065 * h)), 0, 180, 360, 255, -1, cv2.LINE_AA)
        fill([(-0.05, 0.99), (0.05, 0.99), (0.045, 1.05), (-0.045, 1.05)])
        fill([(-0.04, 1.03), (-0.075, 1.12), (-0.05, 1.125), (-0.015, 1.04)])
        fill([(0.04, 1.03), (0.075, 1.12), (0.05, 1.125), (0.015, 1.04)])
    elif kind == "dongpo":       # 东坡巾 + 竹杖
        fill([(-0.06, 0.95), (0.06, 0.95), (0.07, 1.09), (-0.07, 1.09)])
        cv2.line(m, tuple(P([(0.3, 0.0)])[0]), tuple(P([(0.26, 0.9)])[0]), 255, max(2, int(0.018 * h)), cv2.LINE_AA)
    elif kind == "li":           # 笠帽 + 毛笔
        cv2.ellipse(m, (int(x), int(base - 0.955 * h)), (int(0.13 * h), int(0.022 * h)), 0, 0, 360, 255, -1, cv2.LINE_AA)
        cv2.ellipse(m, (int(x), int(base - 0.96 * h)), (int(0.065 * h), int(0.07 * h)), 0, 180, 360, 255, -1, cv2.LINE_AA)
        cv2.line(m, tuple(P([(0.33, 1.0)])[0]), tuple(P([(0.40, 1.22)])[0]), 255, max(2, int(0.016 * h)), cv2.LINE_AA)
    elif kind == "douli":        # 八大山人：斗笠
        fill([(-0.2, 0.95), (0.2, 0.95), (0.0, 1.08)])


FIG_KIND = [("bun", -1), ("mian", 0), ("mian", 1), ("ming", 0), ("dongpo", 0), ("li", 1), ("douli", -1)]
FW_COL = [(1.0, 0.75, 0.35), (1.0, 0.4, 0.45), (0.45, 0.75, 1.0), (0.75, 0.5, 1.0), (0.5, 1.0, 0.75), (1.0, 0.92, 0.75), (1.0, 0.55, 0.2)]


class Concert:
    HY = 650           # 地平线
    SX0, SX1 = 520, 1400
    SBASE = 862        # 舞台台面

    def __init__(self, lyrics):
        rng = np.random.default_rng(101)
        HY = self.HY
        sky = np.zeros((H, W, 3), f32)
        yy = np.linspace(0, 1, HY, dtype=f32)[:, None, None]
        sky[:HY] = lerp(col(0.006, 0.01, 0.035), col(0.06, 0.05, 0.12), yy ** 2)
        sky[:HY] += shift_wrap(A.stars, 100, 50, W, HY) * 0.9
        y, x = np.mgrid[0:HY, 0:W].astype(f32)
        d = (y - 200) * 0.92 + (x - W / 2) * 0.36
        n1 = fbm(W, HY, 102, 6, 5)
        n2 = fbm(W, HY, 103, 6, 9)
        band = np.exp(-(d / 150) ** 2) * (0.35 + 0.9 * n1)
        lane = 1 - np.clip(np.exp(-((d + 18) / 34) ** 2) * (n2 * 1.9 - 0.25), 0, 0.85)
        mw = (band * lane)[..., None] * lerp(col(0.5, 0.62, 1.0), col(1.0, 0.8, 0.6), n2[..., None]) * 0.5
        dense = make_stars(W, HY, 9000, 104, 0.9) * np.clip(band * 1.3, 0, 1)[..., None]
        sky[:HY] += mw + dense * 0.8
        sky[:HY] *= np.clip((HY - y) / 150 + 0.25, 0, 1)[..., None]
        # 对岸城市
        rgb, al, wa, wb = skyline(105, W + 40, 230, 60, (0.012, 0.014, 0.028), 0.5, (36, 110))
        lh = rgb.shape[0]
        reg = sky[HY - lh:HY]
        a = al[:, :W]
        reg[:] = reg * (1 - a) + (rgb[:, :W] + (wa[:, :W] + wb[:, :W]) * 0.8) * a
        glowsrc = np.zeros((H, W, 3), f32)
        glowsrc[HY - lh:HY] = (wa[:, :W] + wb[:, :W]) * a
        sky += cv2.GaussianBlur(glowsrc, (0, 0), 14) * 1.3
        sky[HY:] = 0
        self.sky = sky
        self.skyline_alpha = np.zeros((H, W, 1), f32)
        self.skyline_alpha[HY - lh:HY] = a
        # 近岸前景蒙版：舞台 + 人物 + 栏杆 + 观众
        fg = np.zeros((H, W), np.uint8)
        SB, X0, X1 = self.SBASE, self.SX0, self.SX1
        cv2.rectangle(fg, (X0 - 30, SB), (X1 + 30, H), 255, -1)
        self.truss_y = 520
        for xx in (X0, X1):
            cv2.rectangle(fg, (xx - 9, self.truss_y), (xx + 9, SB), 255, -1)
            for k in range(self.truss_y, SB, 28):
                cv2.line(fg, (xx - 9, k), (xx + 9, k + 28), 255, 2, cv2.LINE_AA)
        cv2.rectangle(fg, (X0 - 20, self.truss_y - 12), (X1 + 20, self.truss_y + 8), 255, -1)
        self.lamps = [int(v) for v in np.linspace(X0 + 40, X1 - 40, 9)]
        for lx in self.lamps:
            cv2.rectangle(fg, (lx - 9, self.truss_y + 8), (lx + 9, self.truss_y + 24), 255, -1)
        self.fig_x = [int(v) for v in np.linspace(X0 + 95, X1 - 95, 7)]
        self.fig_h = 172
        for i, fx in enumerate(self.fig_x):
            draw_figure(fg, fx, SB + 1, self.fig_h, FIG_KIND[i][0], FIG_KIND[i][1])
        cv2.line(fg, (self.fig_x[3] + 34, SB), (self.fig_x[3] + 34, SB - 132), 255, 2, cv2.LINE_AA)
        cv2.circle(fg, (self.fig_x[3] + 34, SB - 134), 5, 255, -1, cv2.LINE_AA)
        cv2.rectangle(fg, (0, 968), (W, 973), 255, -1)
        for xx in list(range(10, X0 - 40, 46)) + list(range(X1 + 46, W, 46)):
            cv2.rectangle(fg, (xx, 968), (xx + 3, H), 255, -1)
        cv2.rectangle(fg, (0, 1012), (W, H), 255, -1)
        self.heads = []
        for row, (by, r, n) in enumerate([(1015, 15, 80), (1048, 21, 56), (1092, 30, 38)]):
            for k in range(n):
                hx = int((k + rng.uniform(0.15, 0.85)) * W / n)
                hy = int(by + rng.uniform(-9, 9))
                cv2.circle(fg, (hx, hy), r, 255, -1, cv2.LINE_AA)
                cv2.ellipse(fg, (hx, hy + int(r * 2.3)), (int(r * 1.8), int(r * 1.6)), 0, 180, 360, 255, -1, cv2.LINE_AA)
                if rng.random() < 0.6:
                    side = rng.choice([-1, 1])
                    cv2.line(fg, (hx + side * r, hy + r), (hx + side * int(r * 1.6), hy - int(r * 1.9)), 255, max(3, r // 3), cv2.LINE_AA)
                    self.heads.append((hx + side * int(r * 1.6), hy - int(r * 2.1), rng.uniform(0, 6.28), row, tuple(FW_COL[rng.integers(len(FW_COL))])))
        self.fg = fg.astype(f32)[..., None] / 255
        # 舞台背屏（让剪影显形）
        scr = np.zeros((H, W), f32)
        scr[self.truss_y + 30:SB, X0 + 14:X1 - 14] = 1
        self.screen = cv2.GaussianBlur(scr, (0, 0), 8)[..., None]
        sy, sxg = np.mgrid[0:H, 0:W].astype(f32)
        self.scr_grad = (np.clip((sy - self.truss_y) / (SB - self.truss_y), 0, 1) ** 1.5)[..., None]
        self.scr_noise = fbm(W, H, 106, 5, 12)[..., None]
        # 烟花时刻表
        self.fw = []
        k = 0
        for a, b, txt in lyrics:
            if 261.5 <= a < 298:
                self.fw.append((a + 0.05, rng.uniform(260, W - 260), rng.uniform(110, 330), FW_COL[k % 7], rng.uniform(170, 260), 500 + k))
                self.fw.append((a + 1.25, rng.uniform(200, W - 200), rng.uniform(90, 360), FW_COL[(k + 3) % 7], rng.uniform(120, 200), 700 + k))
                k += 1
        for j, tt in enumerate(np.arange(292.2, 299.4, 0.36)):
            self.fw.append((float(tt), rng.uniform(160, W - 160), rng.uniform(80, 400), FW_COL[j % 7], rng.uniform(170, 300), 900 + j))
        self.rail_lamps = [x for x in range(90, W, 230) if not (self.SX0 - 80 < x < self.SX1 + 80)]

    def fireworks(self, cv, t):
        for (t0, fx, fy, c, rad, seed) in self.fw:
            dt = t - t0
            if dt < -0.7 or dt > 2.6:
                continue
            c255 = np.array(c) * 255
            if dt < 0:                          # 升空尾迹
                u = 1 + dt / 0.7
                yy = lerp(self.HY - 20, fy, 1 - (1 - u) ** 2)
                cv2.line(cv, (int(fx), int(yy)), (int(fx), int(yy + 34)), (255, 220, 170), 2, cv2.LINE_AA)
                continue
            rng = np.random.default_rng(seed)
            n = 150
            ang = rng.uniform(0, 2 * math.pi, n)
            sp = rad * (0.3 + 0.7 * rng.random(n) ** 0.6)
            k = 1 - math.exp(-dt * 2.4)
            k0 = 1 - math.exp(-max(0, dt - 0.09) * 2.4)
            grav = 26 * dt * dt
            life = max(0.0, 1 - dt / 2.5)
            b = life ** 1.3 * (0.75 + 0.25 * np.sin(dt * 30 + ang * 7))
            x1, y1 = fx + np.cos(ang) * sp * k, fy + np.sin(ang) * sp * k + grav
            x0, y0 = fx + np.cos(ang) * sp * k0, fy + np.sin(ang) * sp * k0 + grav * 0.8
            for i in range(n):
                cv2.line(cv, (int(x0[i]), int(y0[i])), (int(x1[i]), int(y1[i])), (c255 * b[i]).tolist(), 2, cv2.LINE_AA)
            if dt < 0.25:
                cv2.circle(cv, (int(fx), int(fy)), int(26 * (1 - dt / 0.25)) + 2, (255, 255, 255), -1, cv2.LINE_AA)

    def render(self, t, e):
        HY = self.HY
        img = self.sky.copy()
        lit = [1.0] * 7
        dipper_draw(img, t, 1290, 150, 500, 215, lit, names=False, gain=0.8)
        # 灯柱光束 + 烟花（半分辨率，加色）
        k_on = sstep(261, 263.5, t) * (1 - sstep(298.5, 301, t))
        hw, hh = W // 2, H // 2
        cvb = np.zeros((hh, hw, 3), np.uint8)
        for i, lx in enumerate(self.lamps):
            a = -math.pi / 2 + 0.75 * math.sin(t * (0.5 + 0.07 * i) + i * 1.3) + (i - 4) * 0.09
            c = np.array(FW_COL[(i + int(t / 2.7)) % 7]) * 255 * (0.16 + 0.12 * e) * k_on
            L = 1250
            p0 = (lx / 2, (self.truss_y + 16) / 2)
            pa = (p0[0] + math.cos(a - 0.035) * L / 2, p0[1] + math.sin(a - 0.035) * L / 2)
            pb = (p0[0] + math.cos(a + 0.035) * L / 2, p0[1] + math.sin(a + 0.035) * L / 2)
            layer = np.zeros_like(cvb)
            cv2.fillPoly(layer, [np.array([p0, pa, pb], np.int32)], c.tolist(), cv2.LINE_AA)
            cvb = cv2.add(cvb, layer)
        beams = cv2.GaussianBlur(cvb.astype(f32) / 255, (0, 0), 3)
        fade = np.clip(np.linspace(0.25, 1.0, hh, dtype=f32) * 1.6, 0, 1)[:, None, None]
        img += cv2.resize(beams * fade, (W, H), interpolation=cv2.INTER_LINEAR)
        cvf = np.zeros((H, W, 3), np.uint8)
        self.fireworks(cvf, t)
        fwf = cvf.astype(f32) / 255
        fws = cv2.resize(fwf, (hw, hh), interpolation=cv2.INTER_AREA)
        img += fwf * 1.3 + cv2.resize(cv2.GaussianBlur(fws, (0, 0), 6), (W, H)) * 2.2
        # 烟花照亮夜空
        amb = float(fws.mean()) * 40
        img[:HY] *= (1 + min(0.6, amb))
        river_reflect(img, HY, 330, t, gain=0.62, amp=6)
        # 舞台背屏
        hue = FW_COL[int(t / 2.7) % 7]
        scr = self.screen * (0.25 + 0.75 * self.scr_grad) * (0.75 + 0.5 * self.scr_noise)
        glow = np.asarray(hue, f32) * (0.5 + 0.45 * e) * k_on + col(0.9, 0.6, 0.35) * 0.28
        img = img * (1 - self.screen * 0.85) + scr * glow
        for lx in self.lamps:
            add_sprite(img, G1, lx, self.truss_y + 20, (1, 0.95, 0.85), (0.8 + 0.6 * e) * k_on)
        # 前景剪影
        img *= (1 - self.fg * 0.985)
        for x in self.rail_lamps:
            add_sprite(img, G2, x, 950, (1.0, 0.7, 0.35), 0.5)
            add_sprite(img, GS, x, 950, (1.0, 0.9, 0.7), 1.6)
        # 舞台边沿光 + 名牌
        img[self.SBASE:self.SBASE + 3, self.SX0 - 30:self.SX1 + 30] += np.asarray(hue, f32) * 0.8 * k_on + 0.15
        nm = sstep(263, 265, t) * (1 - sstep(297, 300, t))
        for i, fx in enumerate(self.fig_x):
            draw_text(img, FIGURES[i][0], fx, self.SBASE + 30, (1.0, 0.86, 0.6), nm * 0.95, size=22, weight=700, shadow=3)
        # 观众的手机灯海
        for (hx, hy, ph, row, c) in self.heads:
            sway = math.sin(t * 2.3 + ph) * (10 + row * 6)
            tw = 0.6 + 0.4 * math.sin(t * 5 + ph * 3)
            add_sprite(img, GS, hx + sway, hy - abs(sway) * 0.3, (1.0, 0.96, 0.85), (1.3 + row * 0.5) * tw * k_on)
            add_sprite(img, G1, hx + sway, hy - abs(sway) * 0.3, c, 0.22 * k_on)
        # 缓慢推近
        z = 1.0 + 0.07 * sstep(262, 300, t)
        if z > 1.001:
            M = np.array([[z, 0, W / 2 * (1 - z)], [0, z, 620 * (1 - z)]], np.float64)
            img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR)
        op = pulse(t, 262.3, 268.5, 0.8, 1.0)
        draw_text(img, "滨江路 · 星河演唱会", W / 2, 84, (1.0, 0.9, 0.7), op, fname="MaShanZheng", size=78, weight=None, spacing=10, shadow=8)
        return img


# ───────────────────────── 场景 8：江上日出 ─────────────────────────
class Outro:
    HY = 650

    def __init__(self, concert):
        self.sa = concert.skyline_alpha
        self.sil = np.maximum(railing_mask(880), person_mask(1500, 1010, 330)).astype(f32)[..., None] / 255
        self.cloud = fbm(W, 650, 111, 6, 4)
        y = np.linspace(0, 1, 650, dtype=f32)[:, None]
        self.cmask = np.clip((self.cloud - 0.5) * 3, 0, 1) * np.clip(y * 2.2 - 0.25, 0, 1) * np.clip((1 - y) * 6, 0, 1)

    def render(self, t, e):
        HY = self.HY
        p = sstep(298, 338, t)
        sunp = sstep(314, 343, t)
        yy = np.linspace(0, 1, HY, dtype=f32)[:, None] ** 1.5
        top = lerp(col(0.012, 0.02, 0.06), col(0.16, 0.3, 0.58), p)
        hor = lerp(col(0.09, 0.07, 0.14), col(1.0, 0.56, 0.26), sstep(0, 0.6, p))
        hor = lerp(hor, col(1.0, 0.8, 0.52), sstep(0.6, 1.0, p))
        img = np.zeros((H, W, 3), f32)
        img[:HY] = (top[None] * (1 - yy) + hor[None] * yy)[:, None, :]
        if p < 0.85:
            img[:HY] += shift_wrap(A.stars, 100, 50, W, HY) * 0.8 * (1 - p / 0.85) ** 2
        dipper_draw(img, t, 1290, 150, 500, 215, [1 - sstep(0.35, 0.8, p)] * 7, names=False, gain=0.8)
        sx, sy = 1240, HY + 70 - 150 * sunp
        A.sun(img, sx, sy, col(1.0, 0.72, 0.4), 0.25 + 1.5 * sunp * (1 - 0.4 * sstep(0.7, 1, sunp)))
        if sunp > 0:
            add_sprite(img, G2, sx, sy, (1, 1, 0.92), 3.0 * sunp)
        cm = self.cmask[..., None]
        ccol = lerp(col(0.12, 0.1, 0.18), col(1.0, 0.6, 0.42), p)
        img[:HY] = img[:HY] * (1 - cm * 0.55) + ccol * cm * 0.6
        img[HY:] = 0
        a = self.sa[:HY]
        img[:HY] = img[:HY] * (1 - a) + lerp(col(0.012, 0.014, 0.03), col(0.1, 0.07, 0.09), p) * a
        river_reflect(img, HY, 330, t, gain=0.78, amp=5, tint=(0.95, 0.92, 0.9))
        img[HY + 330:] = img[HY + 329]
        img *= (1 - self.sil * (0.985 - 0.06 * p))
        op1 = pulse(t, 331.0, 337.0, 1.2, 0.8)
        draw_text(img, "明天还没来。", W / 2 - 200, 300, (1, 0.97, 0.9), op1, fname="MaShanZheng", size=130, weight=None, spacing=12, shadow=10)
        op2 = sstep(337.0, 338.6, t)
        draw_text(img, "今天，我在。", W / 2 - 200, 300, (1, 0.97, 0.9), op2, fname="MaShanZheng", size=200, weight=None, spacing=16, shadow=12)
        draw_text(img, "漫长的岁月，等待最后的灿烂", W / 2 - 200, 452, (1, 1, 1), sstep(339.2, 341, t), shadow_op=1.0, size=40, weight=800, spacing=10, shadow=8)
        img *= 1 - sstep(343.6, 346.5, t)
        return img


# ───────────────────────── 总导演 ─────────────────────────
class Director:
    #         名称      起      止
    CUTS = [("intro", 0.0, 38.0), ("city", 38.0, 92.2), ("earth", 92.2, 114.0), ("solar", 114.0, 166.0),
            ("dot", 166.0, 179.0), ("flight", 179.0, 194.2), ("galaxy", 194.2, 262.0), ("concert", 262.0, 300.0),
            ("outro", 300.0, DUR + 1)]
    XF = {38.0: 2.0, 92.2: 2.4, 114.0: 2.4, 166.0: 2.5, 179.0: 3.0, 194.2: 0.0, 262.0: 1.6, 300.0: 4.0}

    def __init__(self):
        self.lyrics = load_lyrics()
        self.env = load_env()
        self.sc = {}

    def scene(self, name):
        if name not in self.sc:
            if name == "intro":
                s = Intro()
            elif name == "city":
                s = City(self.scene("intro"))
            elif name == "earth":
                s = Earth()
            elif name == "solar":
                s = Solar()
            elif name == "dot":
                s = Dot()
            elif name == "flight":
                s = Flight()
            elif name == "galaxy":
                s = Galaxy()
            elif name == "concert":
                s = Concert(self.lyrics)
            elif name == "outro":
                s = Outro(self.scene("concert"))
            self.sc[name] = s
        return self.sc[name]

    def subtitle(self, img, t):
        for a, b, txt in self.lyrics:
            if a - 0.15 <= t < b + 0.1:
                if a >= 330.5:          # 结尾两句用大字呈现
                    continue
                b2 = min(b, a + max(2.0, len(txt) * 0.5))
                op = sstep(a - 0.15, a + 0.12, t) * (1 - sstep(b2 - 0.2, b2 + 0.1, t))
                big = 194 <= a < 216 or 262 <= a < 299
                draw_text(img, txt, W / 2, H - 112, (1, 1, 1), op, shadow_op=0.85, size=62 if big else 54,
                          weight=800 if big else 700, spacing=3, shadow=7)

    def frame(self, i):
        t = i / FPS
        e = float(self.env[0, min(i, self.env.shape[1] - 1)])
        idx = next(k for k, (n, a, b) in enumerate(self.CUTS) if a <= t < b)
        name, a, b = self.CUTS[idx]
        img = self.scene(name).render(t, e)
        xf = self.XF.get(b, 0) / 2
        if xf and t > b - xf and idx + 1 < len(self.CUTS):
            w = sstep(b - xf, b + xf, t)
            img = img * (1 - w) + self.scene(self.CUTS[idx + 1][0]).render(t, e) * w
        xf = self.XF.get(a, 0) / 2
        if xf and t < a + xf and idx > 0:
            w = sstep(a - xf, a + xf, t)
            img = self.scene(self.CUTS[idx - 1][0]).render(t, e) * (1 - w) + img * w
        img *= A.vignette
        self.subtitle(img, t)
        gx, gy = (i * 37) % 256, (i * 91) % 256
        img += A.grain[gy:gy + H, gx:gx + W]
        np.clip(img, 0, 1, out=img)
        img = np.sqrt(img) * 0.18 + img * 0.82       # 轻微提亮暗部
        return (img * 255 + 0.5).astype(np.uint8)


def render_part(f0, f1, out):
    d = Director()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", "-g", "60", out], stdin=subprocess.PIPE)
    for i in range(f0, f1):
        p.stdin.write(d.frame(i).tobytes())
        if (i - f0) % 150 == 0:
            print(f"[{f0}-{f1}] {i - f0}/{f1 - f0}", flush=True)
    p.stdin.close()
    p.wait()


def main():
    cmd = sys.argv[1]
    os.makedirs(WORK, exist_ok=True)
    if cmd == "still":
        d = Director()
        for k in range(2, len(sys.argv), 2):
            fr = d.frame(int(float(sys.argv[k]) * FPS))
            Image.fromarray(fr).save(sys.argv[k + 1])
    elif cmd == "part":
        render_part(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif cmd == "all":
        out = sys.argv[2]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        load_env()
        Galaxy()
        chunk = 300
        jobs = [(a, min(NF, a + chunk)) for a in range(0, NF, chunk)]
        parts = [os.path.join(WORK, f"part_{a:05d}.mp4") for a, _ in jobs]
        running = []
        todo = [(j, p) for j, p in zip(jobs, parts) if not os.path.exists(p + ".ok")]
        while todo or running:
            while todo and len(running) < n:
                (a, b), p = todo.pop(0)
                pr = subprocess.Popen([sys.executable, __file__, "part", str(a), str(b), p], stdout=subprocess.DEVNULL)
                running.append((pr, p))
            pr, p = running.pop(0)
            if pr.wait() != 0:
                raise SystemExit(f"part failed: {p}")
            open(p + ".ok", "w").close()
            print("done", os.path.basename(p), flush=True)
        lst = os.path.join(WORK, "parts.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", AUDIO,
                               "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                               "-movflags", "+faststart", "-shortest", out])
        print("wrote", out)


if __name__ == "__main__":
    main()
