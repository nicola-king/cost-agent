"""Build dist/picture-sentence.html: one self-contained file (engine, IPA, voice clips inline).
Works opened straight from disk or uploaded anywhere as a single file."""
import base64, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
page = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
engine = open(os.path.join(ROOT, 'engine.js'), encoding='utf-8').read()
man = json.load(open(os.path.join(ROOT, 'audio/manifest.json'), encoding='utf-8'))
paths = [v['f'] for v in man['words'].values()]
for s in man['sentences'].values():
    paths += [s['en']['f'], s['slow']['f'], s['zh']['f']]
audio = {p: base64.b64encode(open(os.path.join(ROOT, 'audio', p), 'rb').read()).decode() for p in paths}
embed = {'manifest': man, 'ipa': json.load(open(os.path.join(ROOT, 'ipa.json'), encoding='utf-8')), 'audio': audio}
data = json.dumps(embed, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
assert '<script src="engine.js"></script>' in page
page = page.replace('<script src="engine.js"></script>',
                    '<script>window.__EMBED=' + data + ';</script>\n<script>\n' + engine.replace('</script', '<\\/script') + '\n</script>')
head = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>body{margin:0}[hidden]{display:none!important}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>\n')
i = page.index('<div class="app">')
out = head + page[:i] + '</head>\n<body>\n' + page[i:] + '\n</body>\n</html>\n'
os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
dst = os.path.join(ROOT, 'dist', 'picture-sentence.html')
open(dst, 'w', encoding='utf-8').write(out)
print(dst, round(os.path.getsize(dst) / 1e6, 2), 'MB', len(audio), 'clips')
