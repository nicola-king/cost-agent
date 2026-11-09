# 看句成画 Picture Sentence（MVP）

输入一句简单英文，就会生成一段带声效的小动画，同时播放英文发音、逐词高亮，并给出逐词释义和整句中文。

## 文件

| 文件 | 作用 | 迁移到 sayelf.cn / 小程序时 |
|---|---|---|
| `engine.js` | 核心：词库、句子解析、场景 JSON、Canvas 渲染、合成音效。不依赖 DOM | 直接复用 |
| `index.html` | 网页演示界面和语音适配（Web Speech API） | 换成网站组件或小程序页面 |

## 数据流

```
英文句子 ──parse()──▶ 结构化解析 ──buildScene()──▶ 场景 JSON ──Stage──▶ Canvas 动画 + 音效事件
```

- MVP 阶段用本地规则解析器，不调用 AI，零成本。
- 上线后：句子交给大模型输出同样格式的场景 JSON，高频句子提前生成并缓存。
- 渲染层只认场景 JSON，所以替换解析器不影响画面。

## 成本

- 画面：浏览器或手机本地用 Canvas 2D 渲染，不需要服务器。
- 声效：用 Web Audio 实时合成，不需要音频文件。
- 发音：浏览器自带语音合成，免费。

## 迁移到微信小程序要改的地方

1. Canvas：`<canvas type="2d">` 取到 node 后传给 `new Stage(canvas, { width, dpr, raf: canvas.requestAnimationFrame.bind(canvas) })`。
2. 音效：`new Sfx(() => wx.createWebAudioContext())`。
3. 发音：小程序没有 Web Speech API。可以改用微信同声传译插件，或者提前生成高频句子的 mp3。
4. 素材：emoji 在不同手机上画风不一样。正式版用 AI 一次性生成统一画风的素材，人工审核后替换 `emoji` 字段对应的图片。

## MVP 范围

约 70 个名词、40 个动词、20 个介词（含词组），支持一般现在时、一般过去时、现在进行时、过去进行时和 will 将来时。
