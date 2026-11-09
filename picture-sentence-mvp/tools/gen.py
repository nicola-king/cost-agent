import json, re, os, subprocess, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from misaki import zh
OUT = '/home/user/cost-agent/picture-sentence-mvp/audio'
for d in ('s', 'w', 'z'): os.makedirs(f'{OUT}/{d}', exist_ok=True)
L = json.load(open('lists.json'))
k = Kokoro('model_q8.onnx', 'voices.npz'); g2p = zh.ZHG2P()
EN, ZH = 'af_heart', 'zf_xiaobei'
def trim(a, sr, pad=0.04):
    thr = max(1e-4, np.abs(a).max() * 0.02); idx = np.where(np.abs(a) > thr)[0]
    if not len(idx): return a
    s, e = max(0, idx[0] - int(pad * sr)), min(len(a), idx[-1] + int(pad * sr)); return a[s:e]
def save(a, sr, path):
    sf.write('/tmp/_c.wav' if False else path + '.wav', a, sr)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path + '.wav', '-ac', '1', '-ar', '24000', '-b:a', '48k', path], check=True)
    os.remove(path + '.wav'); return round(len(a) / sr, 3)
key = lambda t: re.sub(r'\s+', ' ', re.sub(r"[^a-z' ]", ' ', t.lower())).strip()
slug = lambda t: key(t).replace(' ', '-').replace("'", '')
SAY = {'i': 'I', 'tom': 'Tom', 'amy': 'Amy'}
man = {'voice': {'en': 'Kokoro af_heart', 'zh': 'Kokoro zf_xiaobei'}, 'words': {}, 'sentences': {}}
wdur = {}
for w in L['words']:
    a, sr = k.create(SAY.get(w, w), voice=EN, speed=1.0, lang='en-us'); a = trim(a, sr)
    wdur[w] = save(a, sr, f'{OUT}/w/{w}.mp3'); man['words'][w] = {'f': f'w/{w}.mp3', 'd': wdur[w]}
for s in L['sentences']:
    sl = slug(s['text']); ent = {}
    toks = re.findall(r"[A-Za-z']+", s['text'])
    for name, sp in (('en', 1.0), ('slow', 0.78)):
        a, sr = k.create(s['text'], voice=EN, speed=sp, lang='en-us'); a = trim(a, sr, 0.06)
        d = save(a, sr, f'{OUT}/s/{sl}{"" if name == "en" else "-slow"}.mp3')
        # word start times: share of each word's solo length, scaled to the sentence
        ws = [wdur.get(t.lower(), 0.35) for t in toks]; tot = sum(ws); acc = 0.06; marks = []
        for x in ws: marks.append(round(acc, 3)); acc += x / tot * (d - 0.12)
        ent[name] = {'f': f's/{sl}{"" if name == "en" else "-slow"}.mp3', 'd': d, 'marks': marks}
    ph = g2p(s['zh']); ph = ph[0] if isinstance(ph, tuple) else ph
    a, sr = k.create(ph, voice=ZH, speed=1.0, is_phonemes=True); a = trim(a, sr, 0.06)
    ent['zh'] = {'f': f'z/{sl}.mp3', 'd': save(a, sr, f'{OUT}/z/{sl}.mp3'), 'text': s['zh']}
    man['sentences'][key(s['text'])] = ent
json.dump(man, open(f'{OUT}/manifest.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('ok', len(man['words']), len(man['sentences']))
