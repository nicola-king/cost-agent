"""Build ipa.json: American and British IPA (Oxford Learner's Dictionary style) for every
vocabulary word, from misaki's us_gold / gb_gold pronunciation dictionaries."""
import json, re, sys, os, misaki
DATA = os.path.join(os.path.dirname(misaki.__file__), 'data')
words = json.load(open(sys.argv[1]))['words']
out_path = sys.argv[2]
def lex(name):
    d = {}
    for f in (name + '_silver.json', name + '_gold.json'):  # gold wins
        d.update(json.load(open(os.path.join(DATA, f))))
    return d
US, GB = lex('us'), lex('gb')
VOW = 'aæɑɒɔəɛeɜɪiʊuʌAIOQWYᵊᵻ'
ONSETS = {'pl','pr','bl','br','tr','dr','kl','kr','gl','gr','ɡl','ɡr','fl','fr','θr','ʃr','sp','st','sk','sm','sn','sl','sw','tw','kw','dw','spr','str','skr','spl','skw','pj','bj','kj','fj','mj','hj','vj','sj','tj','dj','nj','lj'}
def raw(d, w):
    v = d.get(w) or d.get(w.capitalize())
    if isinstance(v, dict): v = v.get('DEFAULT') or next(iter(v.values()))
    return v
def place_stress(p):
    """misaki marks stress right before the vowel; dictionaries mark it before the syllable."""
    s = list(p); out = []
    i = 0
    res = ''
    for ch in s:
        if ch in 'ˈˌ':
            # move back over the onset consonants already written
            j = len(res)
            cons = ''
            while j > 0 and res[j - 1] not in VOW + 'ːˈˌ' and res[j - 1] != ' ':
                j -= 1
            cluster = res[j:]
            # keep the longest legal onset at the end of the cluster
            k = 0
            for n in range(len(cluster), 0, -1):
                tail = cluster[-n:]
                if n == 1 or tail in ONSETS or tail.replace('ɹ', 'r') in ONSETS:
                    k = n; break
            if j == 0: k = len(cluster)
            res = res[:len(res) - k] + ch + res[len(res) - k:]
        else:
            res += ch
    return res
def nvowels(p):
    return len(re.findall('[AIOQWY]|[aæɑɒɔəɛeɜɪiʊuʌᵊᵻ]+', p))
def common(p):
    for a, b in (('A', 'eɪ'), ('I', 'aɪ'), ('W', 'aʊ'), ('Y', 'ɔɪ'), ('ᵊ', 'ə'), ('ʤ', 'dʒ'), ('ʧ', 'tʃ'), ('ᵻ', 'ɪ'), ('ɡ', 'g')):
        p = p.replace(a, b)
    return p
def us(p):
    p = place_stress(p)
    p = p.replace('O', 'oʊ').replace('ɾ', 't')
    p = re.sub('([ˈˌ][^aæɑɒɔəɛeɜɪiʊuʌAIOQWY]*)i', r'\1iː', p)   # stressed i -> iː
    p = re.sub('([ˈˌ][^aæɑɒɔəɛeɜɪiʊuʌAIOQWY]*)u', r'\1uː', p)
    p = p.replace('ɜɹ', 'ɜːr').replace('ɑɹ', 'ɑːr').replace('ɔɹ', 'ɔːr').replace('ɛɹ', 'er').replace('əɹ', 'ər')
    p = re.sub('ɑ(?!ː)', 'ɑː', p); p = re.sub('ɔ(?![ːɪ])', 'ɔː', p)
    p = p.replace('ɹ', 'r').replace('ɛ', 'e')
    return p
def gb(p):
    p = place_stress(p)
    p = p.replace('Q', 'əʊ').replace('O', 'əʊ').replace('ɛː', 'eə').replace('ɪː', 'ɪə').replace('ʊː', 'ʊə')
    p = re.sub('(?<![ɑɔ])a(?![ɪʊ])', 'æ', p)
    p = re.sub('([ˈˌ][^aæɑɒɔəɛeɜɪiʊuʌAIOQWY]*)i(?!ː)', r'\1iː', p)
    p = re.sub('([ˈˌ][^aæɑɒɔəɛeɜɪiʊuʌAIOQWY]*)u(?!ː)', r'\1uː', p)
    p = p.replace('ɹ', 'r').replace('ɛ', 'e')
    return p
def finish(p, single):
    p = common(p)
    if single: p = p.replace('ˈ', '').replace('ˌ', '')
    if single and p.endswith('i') and not p.endswith('ɪi'): p = p[:-1] + 'iː'   # tea, he
    if single and p.endswith('u'): p = p[:-1] + 'uː'
    return p
SAY = {'i': 'I'}
res, miss = {}, []
for w in words:
    u, g = raw(US, SAY.get(w, w)), raw(GB, SAY.get(w, w))
    if not u or not g: miss.append(w); continue
    res[w] = [finish(us(u), nvowels(u) == 1), finish(gb(g), nvowels(g) == 1)]
# Oxford-style overrides where the source dictionary picks a less common variant
for w in [x for x in res if x.startswith('catch') or x == 'caught']:
    res[w][0] = res[w][0].replace('ketʃ', 'kætʃ')
# weak forms, as heard in a sentence
res.update({'the': ['ðə', 'ðə'], 'a': ['ə', 'ə'], 'an': ['ən', 'ən']})
# regular inflections the dictionary lacks: derive from the base word's last sound
VOICELESS = ('p', 't', 'k', 'f', 'θ')
SIB = ('s', 'z', 'ʃ', 'ʒ', 'tʃ', 'dʒ')
def base_of(w):
    for suf, rep in (('ies', 'y'), ('ied', 'y'), ('es', ''), ('s', ''), ('ed', ''), ('ed', 'e'), ('d', ''), ('ing', ''), ('ing', 'e')):
        if w.endswith(suf):
            b = w[:-len(suf)] + rep
            if b in res: return b, suf
            if len(b) > 2 and b[-1] == b[-2] and b[:-1] in res: return b[:-1], suf
    return None, None
def inflect(ipa, suf):
    end = ipa.rstrip('ː')
    if suf in ('s', 'es', 'ies'):
        return ipa + ('ɪz' if end.endswith(SIB) else 's' if end.endswith(VOICELESS) else 'z')
    if suf in ('ed', 'd', 'ied'):
        return ipa + ('ɪd' if end.endswith(('t', 'd')) else 't' if end.endswith(VOICELESS + ('s', 'ʃ', 'tʃ')) else 'd')
    return ipa + 'ɪŋ'
for w in list(miss):
    b, suf = base_of(w)
    if b:
        res[w] = [inflect(x, suf) for x in res[b]]
        res[w] = [x if 'ˈ' in x or nvowels(x.replace('aɪ', 'A').replace('aʊ', 'W').replace('eɪ', 'A').replace('oʊ', 'O').replace('əʊ', 'Q').replace('ɔɪ', 'Y')) < 2 else 'ˈ' + x for x in res[w]]
        miss.remove(w)
json.dump(res, open(out_path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('ok', len(res), 'missing', miss)
