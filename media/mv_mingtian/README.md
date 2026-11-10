# 《明天还没来》MV

为歌曲《明天还没来》配的 16:9（1920×1080 / 30fps）程序化动画 MV。
画面全部由 `make_mv.py` 用 numpy + OpenCV + Pillow 计算生成，不含任何外部图片或视频素材。

## 分镜

| 时间 | 歌曲段落 | 画面 |
| --- | --- | --- |
| 0:00 | Intro 独白 | 雨夜江边，撑伞的孤独身影，对岸灯火 |
| 0:38 | Verse 1 焦虑 | 城市黎明，万家灯火明灭，车流光轨 |
| 1:21 | Pre-Chorus | 镜头升空，穿过云层 |
| 1:32 | Chorus 1 | 地球晨昏线上的日出 |
| 1:54 | Verse 2 行动 | 太阳系：每颗行星按自己的节奏公转（88 天一圈 … 165 年一圈） |
| 2:37 | Bridge 音乐骤停 | 六十亿公里外回望的“暗淡蓝点”，星云渐亮 |
| 3:14 | Chorus 2 爆发 | 银河系全景，“你在这里” |
| 3:36 | Verse 3 | 庄子、刘邦、刘备、朱元璋、苏轼、赵孟頫、八大山人 —— 逆境中坚持的七个人，逐一点亮成北斗七星 |
| 4:22 | Final Chorus | 滨江路 · 星河演唱会：七位古人剪影登台，烟花、灯柱、观众灯海、江面倒影 |
| 4:59 | Outro | 江上日出，“明天还没来。今天，我在。” |

歌词字幕的时间轴直接读取音频文件内嵌的字幕轨；灯光与亮度跟随音频低频能量律动。

## 重新生成

```bash
pip install numpy opencv-python-headless pillow scipy fonttools
# 字体（OFL 开源）放到 $MV_WORK/fonts/ ：NotoSerifSC.ttf、MaShanZheng.ttf
export MV_AUDIO=/path/to/song.m4a MV_WORK=/path/to/workdir
python3 make_mv.py still 270 preview.png     # 预览第 270 秒
python3 make_mv.py all out.mp4 4             # 4 进程渲染全片并混入音频
```
