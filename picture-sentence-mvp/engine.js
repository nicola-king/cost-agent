/*
 * 看句成画 engine (MVP)
 * ---------------------------------------------------------------
 * Platform-neutral core. No DOM access here, so the same file can be
 * reused on sayelf.cn (web) or in a WeChat mini-program (Canvas 2D +
 * wx.createWebAudioContext). Layers:
 *   1. Lexicon      nouns / verbs / prepositions / adverbs (+ 中文释义)
 *   2. parse()      English sentence  -> structured parse
 *   3. buildScene() parse             -> Scene JSON (what an LLM would output later)
 *   4. Stage        Scene JSON        -> Canvas 2D animation (+ sound events)
 *   5. Sfx          Web Audio synthesized sound effects (no audio files)
 */
(function (global) {
  'use strict';

  /* ================= helpers ================= */
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const ease = t => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
  const easeOut = t => 1 - Math.pow(1 - t, 3);
  const seg = (p, a, b) => clamp((p - a) / (b - a), 0, 1); // local progress of p inside [a,b]
  const bounceOut = t => {
    const n = 7.5625, d = 2.75;
    if (t < 1 / d) return n * t * t;
    if (t < 2 / d) return n * (t -= 1.5 / d) * t + 0.75;
    if (t < 2.5 / d) return n * (t -= 2.25 / d) * t + 0.9375;
    return n * (t -= 2.625 / d) * t + 0.984375;
  };

  /* ================= 1. Lexicon ================= */
  const NOUNS = {};
  function noun(words, emoji, zh, kind, extra) {
    const list = words.split('|');
    const def = Object.assign({ id: list[0], emoji, zh, kind, scale: 1 }, extra || {});
    list.forEach(w => { NOUNS[w] = def; });
  }
  // animals
  noun('cat', '🐈', '猫', 'animal');
  noun('dog', '🐕', '狗', 'animal');
  noun('bear', '🐻', '熊', 'animal');
  noun('bird', '🐦', '小鸟', 'animal', { flyer: true, scale: 0.8 });
  noun('fish', '🐟', '鱼', 'animal', { scale: 0.8 });
  noun('rabbit|bunny', '🐇', '兔子', 'animal');
  noun('mouse', '🐁', '老鼠', 'animal', { scale: 0.7 });
  noun('duck', '🦆', '鸭子', 'animal');
  noun('frog', '🐸', '青蛙', 'animal', { scale: 0.85 });
  noun('monkey', '🐒', '猴子', 'animal');
  noun('horse', '🐎', '马', 'animal', { scale: 1.3 });
  noun('pig', '🐖', '猪', 'animal');
  noun('panda', '🐼', '熊猫', 'animal');
  noun('tiger', '🐅', '老虎', 'animal', { scale: 1.2 });
  noun('elephant', '🐘', '大象', 'animal', { scale: 1.5 });
  noun('cow', '🐄', '奶牛', 'animal', { scale: 1.3 });
  noun('chicken', '🐔', '鸡', 'animal', { scale: 0.85 });
  noun('butterfly', '🦋', '蝴蝶', 'animal', { flyer: true, scale: 0.7 });
  noun('snake', '🐍', '蛇', 'animal');
  noun('turtle', '🐢', '乌龟', 'animal', { scale: 0.85 });
  // people
  noun('boy', '👦', '男孩', 'person');
  noun('he', '👦', '他', 'person', { pron: true });
  noun('tom', '👦', '汤姆', 'person', { pron: true });
  noun('girl', '👧', '女孩', 'person');
  noun('she', '👧', '她', 'person', { pron: true });
  noun('amy', '👧', '艾米', 'person', { pron: true });
  noun('i', '🙋', '我', 'person', { pron: true });
  noun('man', '👨', '男人', 'person', { scale: 1.15 });
  noun('woman', '👩', '女人', 'person', { scale: 1.15 });
  noun('dad|father', '👨', '爸爸', 'person', { scale: 1.15 });
  noun('mom|mum|mother', '👩', '妈妈', 'person', { scale: 1.15 });
  noun('baby', '👶', '宝宝', 'person', { scale: 0.8 });
  noun('grandma', '👵', '奶奶', 'person', { scale: 1.1 });
  noun('grandpa', '👴', '爷爷', 'person', { scale: 1.1 });
  // things
  noun('ball', '⚽', '球', 'thing', { scale: 0.6 });
  noun('apple', '🍎', '苹果', 'thing', { scale: 0.6 });
  noun('banana', '🍌', '香蕉', 'thing', { scale: 0.6 });
  noun('cake', '🍰', '蛋糕', 'thing', { scale: 0.65 });
  noun('cookie', '🍪', '饼干', 'thing', { scale: 0.55 });
  noun('pizza', '🍕', '披萨', 'thing', { scale: 0.6 });
  noun('carrot', '🥕', '胡萝卜', 'thing', { scale: 0.6 });
  noun('bread', '🍞', '面包', 'thing', { scale: 0.6 });
  noun('egg', '🥚', '鸡蛋', 'thing', { scale: 0.5 });
  noun('milk', '🥛', '牛奶', 'thing', { scale: 0.6 });
  noun('juice', '🧃', '果汁', 'thing', { scale: 0.6 });
  noun('water', '💧', '水', 'thing', { scale: 0.5, place: 'water' });
  noun('book', '📕', '书', 'thing', { scale: 0.6 });
  noun('hat', '🎩', '帽子', 'thing', { scale: 0.6 });
  noun('key', '🔑', '钥匙', 'thing', { scale: 0.5 });
  noun('phone', '📱', '手机', 'thing', { scale: 0.55 });
  noun('toy|teddy', '🧸', '玩具熊', 'thing', { scale: 0.65 });
  noun('pencil', '✏️', '铅笔', 'thing', { scale: 0.5 });
  noun('flower', '🌸', '花', 'thing', { scale: 0.6 });
  noun('kite', '🪁', '风筝', 'thing', { scale: 0.7, flyer: true });
  noun('umbrella', '☂️', '雨伞', 'thing', { scale: 0.7 });
  noun('shoe', '👟', '鞋', 'thing', { scale: 0.6 });
  noun('sock', '🧦', '袜子', 'thing', { scale: 0.55 });
  noun('balloon', '🎈', '气球', 'thing', { scale: 0.7, flyer: true });
  noun('letter', '✉️', '信', 'thing', { scale: 0.55 });
  noun('cup', '☕', '杯子', 'thing', { scale: 0.65, inside: 'container' });
  noun('plane', '✈️', '飞机', 'thing', { flyer: true });
  // places (things you can be on / in / under ...)
  noun('table|desk', '', '桌子', 'place', { draw: 'table', under: 'legs', inside: 'top' });
  noun('box', '📦', '箱子', 'place', { scale: 1.3, under: 'stack', inside: 'container' });
  noun('bed', '🛏️', '床', 'place', { scale: 1.8, under: 'legs', inside: 'top' });
  noun('chair', '🪑', '椅子', 'place', { scale: 1.4, under: 'legs', inside: 'top' });
  noun('sofa|couch', '🛋️', '沙发', 'place', { scale: 1.8, under: 'legs', inside: 'top' });
  noun('tree', '🌳', '树', 'place', { scale: 2.5, under: 'canopy', inside: 'canopy' });
  noun('house|home', '🏠', '房子', 'place', { scale: 2.3, under: 'canopy', inside: 'room' });
  noun('basket', '🧺', '篮子', 'place', { scale: 1.2, under: 'stack', inside: 'container' });
  noun('bag|schoolbag', '🎒', '书包', 'place', { scale: 1.1, under: 'stack', inside: 'container' });
  noun('bowl', '🥣', '碗', 'place', { scale: 1, under: 'stack', inside: 'container' });
  noun('door', '🚪', '门', 'place', { scale: 2, under: 'canopy', inside: 'room' });
  noun('wall', '🧱', '墙', 'place', { scale: 1.5, under: 'canopy', inside: 'room' });
  noun('rock|stone', '🪨', '石头', 'place', { scale: 1.3, under: 'stack', inside: 'top' });
  noun('car', '🚗', '汽车', 'place', { scale: 1.7, under: 'legs', inside: 'room' });
  noun('river', '', '河', 'place', { draw: 'water' });
  noun('lake', '', '湖', 'place', { draw: 'water' });
  noun('pool', '', '水池', 'place', { draw: 'water' });
  noun('sea', '', '大海', 'place', { draw: 'water' });
  noun('mountain|hill', '⛰️', '山', 'place', { scale: 2.8, under: 'canopy', inside: 'room' });
  noun('cloud', '☁️', '云', 'place', { scale: 1.8, sky: true, under: 'sky', inside: 'room' });
  noun('moon', '🌙', '月亮', 'place', { scale: 1.3, sky: true, under: 'sky', inside: 'room' });
  noun('sun', '☀️', '太阳', 'place', { scale: 1.4, sky: true, under: 'sky', inside: 'room' });

  function lookupNoun(w) {
    if (NOUNS[w]) return { n: NOUNS[w], plural: false };
    if (w.length > 3 && w.endsWith('es') && NOUNS[w.slice(0, -2)]) return { n: NOUNS[w.slice(0, -2)], plural: true };
    if (w.length > 2 && w.endsWith('s') && NOUNS[w.slice(0, -1)]) return { n: NOUNS[w.slice(0, -1)], plural: true };
    return null;
  }

  // verbs ------------------------------------------------------------
  // trans: 0 intransitive, 1 needs object, 2 object optional
  // motion: a location preposition means "move to there" (jump on the table = jump onto)
  // zai:    Chinese uses "V在X上" (坐在椅子上 / 躲在床下面)
  const VERBS = {}, VERB_FORMS = {};
  function inflect(b, o) {
    const cy = /[^aeiou]y$/.test(b);
    const dbl = o.dbl ? b + b.slice(-1) : null;
    return {
      base: b,
      s: o.s || (/(s|sh|ch|x|z|o)$/.test(b) ? b + 'es' : cy ? b.slice(0, -1) + 'ies' : b + 's'),
      past: o.past || (b.endsWith('e') ? b + 'd' : cy ? b.slice(0, -1) + 'ied' : dbl ? dbl + 'ed' : b + 'ed'),
      ing: o.ing || (b.endsWith('ie') ? b.slice(0, -2) + 'ying' : b.endsWith('e') && !b.endsWith('ee') ? b.slice(0, -1) + 'ing' : dbl ? dbl + 'ing' : b + 'ing'),
    };
  }
  function verb(base, zh, anim, o) {
    o = o || {};
    const d = Object.assign({ id: base, zh, anim, trans: 0 }, o);
    d.forms = inflect(base, o);
    VERBS[base] = d;
    [['base', d.forms.base], ['s', d.forms.s], ['past', d.forms.past], ['ing', d.forms.ing]].forEach(([f, w]) => {
      if (!VERB_FORMS[w]) VERB_FORMS[w] = { v: d, form: f };
    });
  }
  verb('jump', '跳', 'jump', { motion: true });
  verb('hop', '蹦', 'jump', { motion: true, dbl: true });
  verb('run', '跑', 'run', { motion: true, past: 'ran', dbl: true });
  verb('walk', '走', 'walk', { motion: true });
  verb('fly', '飞', 'fly', { motion: true, past: 'flew' });
  verb('fall', '掉', 'fall', { motion: true, past: 'fell' });
  verb('roll', '滚', 'roll', { motion: true });
  verb('climb', '爬', 'climb', { motion: true });
  verb('swim', '游泳', 'swim', { past: 'swam', dbl: true, zhMove: '游' });
  verb('sit', '坐', 'sit', { zai: true, past: 'sat', dbl: true });
  verb('sleep', '睡觉', 'sleep', { zai: true, past: 'slept', zhZai: '睡' });
  verb('hide', '躲', 'hide', { zai: true, motion: true, past: 'hid' });
  verb('stand', '站', 'stand', { zai: true, past: 'stood' });
  verb('lie', '躺', 'lie', { zai: true, past: 'lay', s: 'lies', ing: 'lying' });
  verb('dance', '跳舞', 'dance', { zhMove: '跳着舞' });
  verb('sing', '唱歌', 'sing', { past: 'sang' });
  verb('laugh', '笑', 'laugh');
  verb('smile', '微笑', 'smile');
  verb('cry', '哭', 'cry');
  verb('sigh', '叹气', 'sigh');
  verb('sneeze', '打喷嚏', 'sneeze');
  verb('shout', '大喊', 'shout');
  verb('wave', '挥手', 'wave');
  verb('look', '看', 'look');
  verb('play', '玩', 'play');
  verb('eat', '吃', 'eat', { trans: 2, past: 'ate' });
  verb('drink', '喝', 'drink', { trans: 2, past: 'drank' });
  verb('read', '读', 'read', { trans: 2, past: 'read' });
  verb('kick', '踢', 'kick', { trans: 1 });
  verb('throw', '扔', 'throw', { trans: 1, past: 'threw' });
  verb('push', '推', 'push', { trans: 1 });
  verb('pull', '拉', 'pull', { trans: 1 });
  verb('put', '放', 'put', { trans: 1, past: 'put', dbl: true });
  verb('carry', '搬', 'carry', { trans: 1 });
  verb('hug', '抱', 'hug', { trans: 1, dbl: true });
  verb('catch', '接住', 'catch', { trans: 1, past: 'caught' });
  verb('chase', '追', 'chase', { trans: 1 });
  verb('drop', '丢', 'drop', { trans: 1, dbl: true });

  // prepositions ---------------------------------------------------------
  // rel: where the mover ends up. kind: how Chinese word order works.
  const PREPS = {
    'on top of': { rel: 'top', kind: 'loc', loc: '上', gloss: '在…上面' },
    'in front of': { rel: 'front', kind: 'loc', loc: '前面', gloss: '在…前面' },
    'next to': { rel: 'next', kind: 'loc', loc: '旁边', gloss: '在…旁边' },
    'out of': { rel: 'outof', kind: 'from', gloss: '从…里出来' },
    'on': { rel: 'top', kind: 'loc', loc: '上', gloss: '在…上面' },
    'onto': { rel: 'top', kind: 'dir', gloss: '到…上面' },
    'in': { rel: 'inside', kind: 'loc', loc: '里', gloss: '在…里面' },
    'inside': { rel: 'inside', kind: 'loc', loc: '里', gloss: '在…里面' },
    'into': { rel: 'inside', kind: 'dir', gloss: '进入…里面' },
    'under': { rel: 'under', kind: 'loc', loc: '下面', gloss: '在…下面' },
    'behind': { rel: 'behind', kind: 'loc', loc: '后面', gloss: '在…后面' },
    'beside': { rel: 'next', kind: 'loc', loc: '旁边', gloss: '在…旁边' },
    'over': { rel: 'over', kind: 'path', loc: '上方', gloss: '越过；在…上方' },
    'off': { rel: 'off', kind: 'from', gloss: '从…上离开' },
    'to': { rel: 'to', kind: 'to', gloss: '向；到' },
    'towards': { rel: 'to', kind: 'to', gloss: '朝着' },
    'toward': { rel: 'to', kind: 'to', gloss: '朝着' },
    'around': { rel: 'around', kind: 'around', gloss: '围绕' },
    'at': { rel: 'at', kind: 'at', gloss: '朝；看着' },
    'with': { rel: 'with', kind: 'with', gloss: '和…一起' },
    'up': { rel: 'top', kind: 'up', gloss: '向上' },
  };

  const ADJS = {
    big: { zh: '大', scale: 1.35 }, large: { zh: '大', scale: 1.35 },
    small: { zh: '小', scale: 0.7 }, little: { zh: '小', scale: 0.7 }, tiny: { zh: '小小的', scale: 0.5 },
    happy: { zh: '开心的', mood: 'happy', pred: '开心' },
    sad: { zh: '伤心的', mood: 'sad', pred: '伤心' },
    angry: { zh: '生气的', mood: 'angry', pred: '生气' },
    sleepy: { zh: '困倦的', mood: 'sleepy', pred: '困' },
    tired: { zh: '累的', mood: 'sleepy', pred: '累' },
    hungry: { zh: '饿的', mood: 'hungry', pred: '饿' },
    scared: { zh: '害怕的', mood: 'scared', pred: '害怕' },
  };
  const ADVS = {
    loudly: { zh: '大声地', volume: 1.8, amp: 1.5 },
    quietly: { zh: '轻轻地', volume: 0.45, speed: 0.8, amp: 0.7 },
    softly: { zh: '轻轻地', volume: 0.45, speed: 0.8, amp: 0.7 },
    slowly: { zh: '慢慢地', speed: 0.5 },
    quickly: { zh: '快快地', speed: 1.8 },
    fast: { zh: '飞快地', speed: 1.9 },
    carefully: { zh: '小心地', speed: 0.7 },
    happily: { zh: '开心地', mood: 'happy' },
    sadly: { zh: '伤心地', mood: 'sad' },
    high: { zh: '高高地', height: 1.7 },
    again: { zh: '又', repeat: 2 },
    very: { zh: '很' },
  };
  const TIMES = {
    yesterday: { zh: '昨天', tense: 'past' }, today: { zh: '今天' }, tomorrow: { zh: '明天', tense: 'future' },
    now: { zh: '现在' }, 'every day': { zh: '每天' },
  };
  const DETS = {
    the: { zh: '（特指）', show: '' }, a: { zh: '一个', show: '' }, an: { zh: '一个', show: '' },
    my: { zh: '我的', show: '我的' }, your: { zh: '你的', show: '你的' }, his: { zh: '他的', show: '他的' },
    her: { zh: '她的', show: '她的' }, our: { zh: '我们的', show: '我们的' }, their: { zh: '他们的', show: '他们的' },
    its: { zh: '它的', show: '它的' }, this: { zh: '这个', show: '这个' }, that: { zh: '那个', show: '那个' },
  };
  const AUX = { am: 'present', is: 'present', are: 'present', was: 'past', were: 'past', will: 'future' };

  const TENSES = {
    present: { label: '一般现在时', en: 'Present simple', hint: '事实 / 习惯' },
    past: { label: '一般过去时', en: 'Past simple', hint: '已经发生' },
    progressive: { label: '现在进行时', en: 'Present continuous', hint: '正在发生（动画循环）' },
    pastProgressive: { label: '过去进行时', en: 'Past continuous', hint: '当时正在发生' },
    future: { label: '一般将来时', en: 'Future simple', hint: '将要发生' },
  };

  /* ================= 2. parse ================= */
  function parse(text) {
    const words = (String(text || '').replace(/[’]/g, "'").match(/[A-Za-z']+/g) || []);
    const toks = words.map(w => ({ text: w, low: w.toLowerCase(), role: null, zh: '' }));
    const r = { tokens: toks, subject: null, verb: null, verbForm: null, object: null, prep: null, target: null,
      advs: [], aux: null, copula: false, adjPred: null, times: [], tense: 'present', unknown: [], error: null };
    let i = 0;
    const tag = (t, role, zh) => { t.role = role; t.zh = zh; };
    const at = k => (toks[k] ? toks[k].low : '');

    function eatAdvs() {
      while (i < toks.length) {
        const two = at(i) + ' ' + at(i + 1);
        if (TIMES[two]) { tag(toks[i], 'time', TIMES[two].zh); tag(toks[i + 1], 'time', ''); r.times.push(two); i += 2; continue; }
        if (ADVS[at(i)]) { tag(toks[i], 'adv', ADVS[at(i)].zh); r.advs.push(at(i)); i++; continue; }
        if (TIMES[at(i)]) { tag(toks[i], 'time', TIMES[at(i)].zh); r.times.push(at(i)); i++; continue; }
        break;
      }
    }
    function np(role) {
      const start = i, det = [], adjs = [];
      while (i < toks.length && DETS[at(i)]) { det.push(at(i)); tag(toks[i], 'det', DETS[at(i)].zh); i++; }
      while (i < toks.length && ADJS[at(i)] && !lookupNoun(at(i))) { adjs.push(at(i)); tag(toks[i], 'adj', ADJS[at(i)].zh); i++; }
      const hit = i < toks.length ? lookupNoun(at(i)) : null;
      if (hit) {
        tag(toks[i], role, hit.n.zh); i++;
        return { n: hit.n, det, adjs, plural: hit.plural };
      }
      for (let k = start; k < i; k++) tag(toks[k], null, '');
      i = start;
      return null;
    }
    function matchPrep() {
      for (const len of [3, 2, 1]) {
        const phrase = toks.slice(i, i + len).map(t => t.low).join(' ');
        if (toks.length - i >= len && PREPS[phrase]) {
          for (let k = 0; k < len; k++) tag(toks[i + k], 'prep', k === 0 ? PREPS[phrase].gloss : '');
          i += len;
          return phrase;
        }
      }
      return null;
    }

    eatAdvs();
    r.subject = np('subject');
    if (!r.subject) {
      r.error = toks.length ? '没找到主语。句子请以 MVP 词库里的名词或代词开头，例如 The cat / The boy / She。' : '请输入一个英文句子。';
      return finish();
    }
    eatAdvs();
    if (AUX[at(i)]) {
      r.aux = at(i); tag(toks[i], 'aux', ''); i++;
      if (r.aux === 'will' && at(i) === 'be') { tag(toks[i], 'aux', ''); i++; r.aux = 'will be'; }
      eatAdvs();
    }
    const vf = VERB_FORMS[at(i)];
    const isBe = r.aux && r.aux !== 'will';
    if (vf) {
      r.verb = vf.v; r.verbForm = vf.form; tag(toks[i], 'verb', vf.v.zh); i++;
      if (r.aux === 'will' || r.aux === 'will be') r.tense = 'future';
      else if (isBe && vf.form === 'ing') r.tense = AUX[r.aux] === 'past' ? 'pastProgressive' : 'progressive';
      else if (vf.form === 'past' && !(vf.form === 'base')) r.tense = 'past';
      else r.tense = 'present';
      if (r.verb.id === 'look' && at(i) === 'at') { /* handled as prep */ }
    } else if (r.aux) {
      r.copula = true;
      r.tense = r.aux === 'will be' ? 'future' : AUX[r.aux];
    } else {
      r.error = '没找到动词。试试 jump / run / eat / sigh 这类 MVP 词库里的动词。';
      return finish();
    }
    eatAdvs();
    if (r.copula && ADJS[at(i)]) { r.adjPred = at(i); tag(toks[i], 'adj', ADJS[at(i)].pred); i++; }
    if (r.verb && r.verb.trans > 0) r.object = np('object');
    eatAdvs();
    const p = matchPrep();
    if (p) {
      r.prep = p;
      r.target = np('target');
      if (!r.target) { r.prep = null; }
    }
    eatAdvs();
    if (r.times.some(t => TIMES[t].tense === 'past') && r.tense === 'present' && r.verbForm !== 's') r.tense = 'past';
    return finish();

    function finish() {
      toks.forEach(t => { if (!t.role) { t.role = 'unknown'; r.unknown.push(t.text); } });
      if (r.subject && r.verb && r.verb.trans === 1 && !r.object && !r.error) {
        r.error = '“' + r.verb.id + '” 后面需要一个宾语，例如 kick the ball。';
      }
      return r;
    }
  }

  /* ================= 3. buildScene ================= */
  function npZh(x) {
    if (!x) return '';
    const pos = x.det.map(d => DETS[d].show).join('');
    const adj = x.adjs.map(a => ADJS[a].zh).join('');
    return pos + adj + x.n.zh + (x.plural && !x.n.pron ? '们'.repeat(x.n.kind === 'person' ? 1 : 0) : '');
  }
  function zhSentence(r) {
    const S = npZh(r.subject), O = npZh(r.object), T = npZh(r.target);
    const adv = r.advs.map(a => ADVS[a].zh).join('');
    const time = r.times.map(t => TIMES[t].zh).join('');
    const P = r.prep ? PREPS[r.prep] : null;
    const v = r.verb;
    let core = '';
    if (r.copula) {
      if (P && T) core = '在' + T + (P.loc || '');
      else if (r.adjPred) core = '很' + ADJS[r.adjPred].pred;
    } else if (v.trans && r.object) {
      if (P && T) core = adv + '把' + O + v.zh.replace('住', '') + transSuffix(P.rel, T);
      else core = adv + v.zh + O;
    } else {
      const V = v.zh, VM = v.zhMove || v.zh;
      if (!P || !T) core = adv + V;
      else switch (P.kind) {
        case 'loc':
          if (v.zai) core = adv + (v.zhZai || V) + '在' + T + P.loc;
          else if (v.motion) core = adv + VM + '到' + T + P.loc;
          else core = '在' + T + P.loc + adv + V;
          break;
        case 'dir': core = adv + VM + (P.rel === 'top' ? '到' + T + '上' : '进' + T + '里'); break;
        case 'path': core = adv + VM + '过' + T; break;
        case 'from': core = '从' + T + (P.rel === 'off' ? '上' : '里') + adv + VM + (P.rel === 'off' ? '下来' : '出来'); break;
        case 'to': core = adv + VM + '向' + T; break;
        case 'around': core = '绕着' + T + adv + VM; break;
        case 'at': core = adv + V + '着' + T; break;
        case 'with': core = '和' + T + '一起' + adv + V; break;
        case 'up': core = adv + VM + '上' + T; break;
        default: core = adv + V;
      }
    }
    let out;
    switch (r.tense) {
      case 'progressive': out = S + time + (v && v.zai && P ? '正' : '正在') + core; break;
      case 'pastProgressive': out = S + (time || '当时') + (v && v.zai && P ? '正' : '正在') + core; break;
      case 'future': out = S + time + '会' + core; break;
      case 'past': out = r.copula ? S + (time || '当时') + core : S + time + core + '了'; break;
      default: out = S + time + core;
    }
    return out + '。';
  }
  function transSuffix(rel, T) {
    return ({ top: '到' + T + '上', inside: '进' + T + '里', under: '到' + T + '下面', behind: '到' + T + '后面',
      front: '到' + T + '前面', next: '到' + T + '旁边', over: '过' + T, to: '给' + T, outof: '出' + T,
      off: '下' + T, around: '绕着' + T, at: '向' + T, with: '和' + T + '一起', })[rel] || '';
  }
  function nounJSON(x, extra) {
    if (!x) return null;
    let scale = 1, mood = null;
    x.adjs.forEach(a => { if (ADJS[a].scale) scale *= ADJS[a].scale; if (ADJS[a].mood) mood = ADJS[a].mood; });
    const o = { id: x.n.id, emoji: x.n.emoji, zh: x.n.zh, kind: x.n.kind };
    if (x.n.draw) o.draw = x.n.draw;
    if (scale !== 1) o.size = +scale.toFixed(2);
    if (mood) o.mood = mood;
    if (x.plural) o.plural = true;
    return Object.assign(o, extra || {});
  }
  function buildScene(text) {
    const r = parse(text);
    if (r.error) return { error: r.error, unknown: r.unknown, tokens: r.tokens.map(t => ({ t: t.text, role: t.role, zh: t.zh })) };
    const mods = { speed: 1, volume: 1, amp: 1, height: 1, repeat: 1, mood: null };
    r.advs.forEach(a => {
      const d = ADVS[a];
      ['speed', 'volume', 'amp', 'height'].forEach(k => { if (d[k]) mods[k] *= d[k]; });
      if (d.repeat) mods.repeat = d.repeat;
      if (d.mood) mods.mood = d.mood;
    });
    if (r.adjPred) mods.mood = ADJS[r.adjPred].mood || mods.mood;
    const scene = {
      text: String(text).trim(),
      tense: r.tense,
      tenseLabel: TENSES[r.tense].label,
      loop: r.tense === 'progressive' || r.tense === 'pastProgressive',
      subject: nounJSON(r.subject),
      action: r.verb ? { verb: r.verb.id, zh: r.verb.zh, anim: r.verb.anim } : { verb: 'be', zh: '在/是', anim: r.adjPred ? 'mood' : 'place' },
      object: nounJSON(r.object),
      relation: r.prep ? { prep: r.prep, rel: PREPS[r.prep].rel, zh: PREPS[r.prep].gloss } : null,
      target: nounJSON(r.target),
      modifiers: mods,
      zh: zhSentence(r),
      tokens: r.tokens.map(t => ({ t: t.text, role: t.role, zh: t.zh })),
      unknown: r.unknown,
    };
    // Implicit props so the picture still makes sense
    if (scene.action.anim === 'swim' && !scene.target) scene.target = { id: 'water', emoji: '', zh: '水', kind: 'place', draw: 'water', implicit: true };
    if (scene.action.anim === 'swim' && scene.relation == null) scene.relation = { prep: '(in)', rel: 'inside', implicit: true };
    if (['eat', 'drink', 'read'].includes(scene.action.anim) && !scene.object) {
      const d = { eat: ['bone', '🦴', '骨头'], drink: ['milk', '🥛', '牛奶'], read: ['book', '📖', '书'] }[scene.action.anim];
      scene.object = { id: d[0], emoji: d[1], zh: d[2], kind: 'thing', implicit: true };
    }
    return scene;
  }

  /* ================= 4. Stage (Canvas 2D) ================= */
  const W = 360, H = 240, HORIZON = 150, G = 202, GB = 190, GF = 218, BASE = 46;
  const EMOJI_FONT = '"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji","Twemoji Mozilla",sans-serif';
  const SCALE_OF = { thing: 0.6 };

  function nounScale(n) {
    const lex = NOUNS[n.id];
    return (lex ? lex.scale : SCALE_OF[n.kind] || 1) * (n.size || 1);
  }
  function mkEnt(role, n) {
    const lex = NOUNS[n.id] || {};
    const drawKind = n.draw || (role === 'target' && lex.place) || null;
    return {
      role, n, lex, emoji: n.emoji, draw: drawKind,
      size: Math.round(BASE * nounScale(n)) * (drawKind === 'water' ? 1 : 1),
      x: 0, y: 0, rot: 0, sx: 1, sy: 1, k: 1, alpha: 1, z: role === 'target' ? 0 : role === 'object' ? 2.5 : 2,
      flip: false, lift: 0, legs: false, pulse: 0, label: '', labelT: 0, mood: n.mood || null,
    };
  }
  const half = e => e.size * e.k * 0.42;
  function box(e) {
    const k = e.size / BASE;
    if (e.draw === 'table') { const w = 118 * k, h = 60 * k; return { x: e.x, y: e.y, top: e.y - h / 2, bottom: e.y + h / 2, w, h, gap: h - 12 * k }; }
    if (e.draw === 'water') return { x: e.x, y: e.y, top: G - 8, bottom: H, w: 170, h: 40, gap: 0 };
    const h = e.size * e.k * 0.84, w = e.size * e.k * 0.95, cy = e.y - e.lift;
    return { x: e.x, y: cy, top: cy - h / 2, bottom: cy + h / 2, w, h, gap: h * 0.6 };
  }
  function restY(e, lane) {
    if (e.draw === 'table') return lane - 30 * e.size / BASE;
    if (e.draw === 'water') return G + 14;
    return lane - half(e);
  }

  // Where does mover m end up for relation rel against target T?
  function relPos(rel, T, m) {
    const b = box(T), s = m.size, lex = T.lex || {};
    const out = (x, lane, z, k, extra) => Object.assign({ x, y: lane - s * (k || 1) * 0.42, z, k: k || 1 }, extra || {});
    const sky = lex.sky;
    switch (rel) {
      case 'top':
        if (T.draw === 'water') return out(b.x - 10, G + 6, 2, 1);
        return { x: b.x, y: b.top - s * 0.42 + s * 0.06, z: 2, k: 1 };
      case 'inside': {
        const mode = T.draw === 'water' ? 'water' : (lex.inside || 'container');
        if (mode === 'water') return out(b.x - 10, G + 20, 1, 1, { wet: true });
        if (mode === 'top') return relPos('top', T, m);
        if (mode === 'canopy') return { x: b.x + b.w * 0.12, y: b.top + b.h * 0.3, z: 2, k: 0.7 };
        if (mode === 'room') return { x: b.x, y: b.y + b.h * 0.12, z: 2, k: 0.5 };
        return { x: b.x, y: b.top + s * 0.85 * 0.42 * 0.35, z: -1, k: 0.85 };
      }
      case 'under': {
        const mode = T.draw === 'table' ? 'table' : T.draw === 'water' ? 'water' : (lex.under || 'stack');
        if (mode === 'water') return out(b.x, G + 26, 1, 0.9, { wet: true });
        if (mode === 'table') { const k = Math.min(1, b.gap / (s * 0.86)); return out(b.x, G, 2, k); }
        if (mode === 'canopy') return out(b.x + b.w * 0.14, G, 2, 1);
        if (mode === 'sky') return out(b.x, G, 2, 1);
        if (mode === 'legs') { const k = Math.min(0.8, (b.h * 0.6) / (s * 0.84)); return out(b.x, G, 2, k, { lift: s * k * 0.84 + 4, legs: true }); }
        return out(b.x, G, 2, 0.9, { lift: s * 0.9 * 0.84 + 1 }); // stack: target sits on the mover
      }
      case 'behind': return sky ? { x: b.x + b.w * 0.4, y: b.y - 6, z: -1, k: 0.85 } : out(b.x + b.w * 0.42, GB - 6, -1, 0.85);
      case 'front': return sky ? { x: b.x - b.w * 0.05, y: b.y + 8, z: 3, k: 1 } : out(b.x - b.w * 0.06, GF, 3, 1.06);
      case 'next': case 'to': case 'with': case 'at':
        return sky ? { x: b.x - b.w / 2 - s * 0.5, y: b.y, z: 2, k: 1 } : out(b.x - b.w / 2 - s * 0.5 - 6, G, 2, 1);
      case 'over': return { x: b.x, y: b.top - s * 0.95, z: 2, k: 1 };
      case 'beyond': return out(Math.min(W - s * 0.6, b.x + b.w / 2 + s * 0.75), G, 2, 1);
      case 'around': return out(b.x - b.w / 2 - s * 0.6, G, 2, 1);
    }
    return out(b.x - b.w / 2 - s * 0.6, G, 2, 1);
  }

  const MOVERS = { jump: 1, run: 1, walk: 1, fly: 1, roll: 1, climb: 1, swim: 1, fall: 1 };
  const POSERS = { hide: 1, sit: 1, stand: 1, lie: 1, sleep: 1 };

  // Moves entity e along a path A->B in the style of `anim`, p in [0,1]
  function travel(anim, e, A, B, p, o) {
    o = o || {};
    const dx = B.x - A.x;
    if (Math.abs(dx) > 1) e.flip = dx > 0;
    e.rot = 0; e.sx = 1; e.sy = 1;
    const rise = A.y - B.y; // >0 if B is higher
    if ((anim === 'run' || anim === 'walk' || anim === 'roll' || anim === 'swim') && rise > 14 && !o.noHop) {
      // go along the ground, then hop up onto B
      const mid = { x: B.x - Math.sign(dx || 1) * (o.hopGap || 34), y: A.y };
      if (p < 0.7) return travel(anim, e, A, mid, p / 0.7, { noHop: true });
      return travel('jump', e, mid, B, (p - 0.7) / 0.3, { h: 22 });
    }
    switch (anim) {
      case 'jump': {
        const h = (o.h != null ? o.h : 26 + Math.max(0, rise) * 0.55) * (o.height || 1);
        e.x = lerp(A.x, B.x, p);
        e.y = lerp(A.y, B.y, p) - h * 4 * p * (1 - p);
        if (p < 0.1) { e.sy = 1 - 0.22 * (1 - p / 0.1) * 0; }
        if (p > 0.92) { const q = (p - 0.92) / 0.08; e.sy = 1 - 0.18 * Math.sin(q * Math.PI); e.sx = 1 + 0.12 * Math.sin(q * Math.PI); }
        else e.sy = 1 + 0.08 * Math.sin(p * Math.PI);
        break;
      }
      case 'run': {
        const q = ease(p);
        e.x = lerp(A.x, B.x, q); e.y = lerp(A.y, B.y, q) - Math.abs(Math.sin(p * Math.PI * 9)) * 6;
        e.rot = (e.flip ? 1 : -1) * 0.1 * Math.sin(p * Math.PI);
        break;
      }
      case 'walk': case 'swim': {
        const q = ease(p);
        e.x = lerp(A.x, B.x, q);
        e.y = lerp(A.y, B.y, q) - (anim === 'swim' ? Math.sin(p * Math.PI * 6) * 3 : Math.abs(Math.sin(p * Math.PI * 6)) * 3.5);
        e.rot = anim === 'swim' ? Math.sin(p * Math.PI * 6) * 0.12 : 0;
        break;
      }
      case 'roll': {
        const q = ease(p);
        e.x = lerp(A.x, B.x, q); e.y = lerp(A.y, B.y, q);
        e.rot = (e.x - A.x) / Math.max(10, half(e));
        break;
      }
      case 'fly': {
        const q = ease(p);
        e.x = lerp(A.x, B.x, q);
        e.y = lerp(A.y, B.y, q) - Math.sin(p * Math.PI) * (o.h != null ? o.h : 50) * (o.height || 1) + Math.sin(p * Math.PI * 7) * 5;
        e.rot = Math.sin(p * Math.PI * 7) * 0.12;
        break;
      }
      case 'fall': {
        e.x = lerp(A.x, B.x, easeOut(p));
        const yp = p * p;
        e.y = A.y + (B.y - A.y) * yp;
        e.rot = (e.flip ? 1 : -1) * p * 1.4;
        if (p > 0.95) { e.sy = 0.85; e.sx = 1.1; }
        break;
      }
      default: { e.x = lerp(A.x, B.x, ease(p)); e.y = lerp(A.y, B.y, ease(p)); }
    }
  }

  // Builds entities + an animation plan for a scene.
  function makePlan(sc) {
    const S = mkEnt('subject', sc.subject);
    const O = sc.object ? mkEnt('object', sc.object) : null;
    const T = sc.target ? mkEnt('target', sc.target) : null;
    const ents = [S, O, T].filter(Boolean);
    const anim = sc.action.anim;
    const rel = sc.relation ? sc.relation.rel : null;
    const m = sc.modifiers || { speed: 1, volume: 1, amp: 1, height: 1, repeat: 1 };
    const plan = { ents, S, O, T, dur: 1.5, events: [], update() {}, fx: null, idle: null, overlay: null, sfxVol: m.volume || 1 };
    const ev = (at, sfx) => plan.events.push({ at, sfx });

    // ---- place target ----
    if (T) {
      T.x = rel === 'off' || rel === 'outof' ? 165 : rel === 'over' ? 188 : (rel === 'at' ? 262 : 236);
      if (T.draw === 'water' && sc.target.implicit) T.x = 190;
      T.y = T.lex.sky ? 62 : restY(T, G);
      T.z = T.draw === 'water' ? -2 : 0;
    }
    const startOf = e => ({ x: 58, y: G - half(e) });
    const centerOf = e => ({ x: T ? 120 : 180, y: G - half(e) });
    const relEnd = (mover) => {
      if (!T || !rel) return null;
      if (rel === 'over') return relPos(sc.action.verb === 'be' ? 'over' : 'beyond', T, mover);
      if (rel === 'off' || rel === 'outof') return relPos('beyond', T, mover);
      if (rel === 'around') return relPos('around', T, mover);
      return relPos(rel, T, mover);
    };
    const applyEnd = (e, P, p, from) => { // scale / z / lift settle near the end of a move
      const q = seg(p, from == null ? 0.75 : from, 1);
      e.k = lerp(1, P.k || 1, q);
      if (p >= (from == null ? 0.85 : from + 0.1)) e.z = P.z != null ? P.z : 2; else e.z = 2.2;
      if (T && P.lift) { T.lift = P.lift * easeOut(q); T.legs = !!P.legs; }
    };
    const idleMood = mood => mood ? (t, dt, emit) => moodFx(mood, S, t, dt, emit) : null;
    plan.idle = idleMood(m.mood || S.mood);

    // ---- movers ----
    if (MOVERS[anim]) {
      let A = startOf(S), B, kind = anim;
      const P = relEnd(S);
      if (anim === 'fly' && !P) { A = { x: 50, y: 110 }; B = { x: 300, y: 84 }; }
      else if (anim === 'fall' && !P) {
        if (S.n.kind === 'thing') { A = { x: 180, y: 40 }; B = { x: 180, y: G - half(S) }; }
        else { A = { x: 160, y: G - half(S) }; B = { x: 200, y: G - half(S) * 0.6 }; }
      } else if (anim === 'swim' && T && T.draw === 'water') {
        A = { x: T.x - 70, y: G + 20 - half(S) * 0.2 }; B = { x: T.x + 60, y: A.y };
      } else if (!P) {
        if (anim === 'jump' || anim === 'climb') { A = B = centerOf(S); kind = 'jumpInPlace'; }
        else B = { x: 300, y: A.y };
      }
      if (P) {
        if (rel === 'off') A = relPos('top', T, S);
        if (rel === 'outof') { const I = relPos('inside', T, S); A = I; }
        B = P;
        if (anim === 'fly' && S.lex.flyer && rel !== 'off' && rel !== 'outof') A = { x: 46, y: 100 };
      }
      if (!B) B = A;
      if (rel === 'outof') { S.k = A.k || 1; S.z = A.z; }
      const dur = { jump: 1.2, run: 1.4, walk: 2, fly: 2, roll: 1.8, climb: 2.2, swim: 2.2, fall: 1.2 }[anim] || 1.5;
      plan.dur = dur;
      plan.update = p => {
        if (rel === 'outof') { S.k = lerp(A.k || 1, 1, seg(p, 0, 0.3)); S.z = p < 0.25 ? -1 : 2; }
        else if (rel === 'off') S.z = 2;
        if (kind === 'jumpInPlace') {
          const q = (p * 2) % 1;
          travel('jump', S, A, B, q, { h: 34, height: m.height });
          if (p >= 1) { S.y = A.y; S.sy = 1; S.sx = 1; }
          return;
        }
        if (rel === 'around') {
          const b = box(T), R = b.w / 2 + S.size * 0.6, th = Math.PI + p * Math.PI * 2 * ease(1);
          S.x = b.x + R * Math.cos(th); S.y = G - half(S) + 14 * Math.sin(th);
          S.z = Math.sin(th) < 0 ? -1 : 2; S.flip = Math.sin(th) < 0;
          S.rot = 0; S.sy = 1 - (anim === 'run' ? Math.abs(Math.sin(p * 40)) * 0.04 : 0);
          return;
        }
        if (anim === 'climb' && P && T) {
          const b = box(T), side = { x: b.x - b.w * 0.42, y: A.y }, up = { x: side.x, y: Math.min(A.y, P.y + 4) };
          if (p < 0.3) travel('walk', S, A, side, p / 0.3);
          else if (p < 0.85) { const q = (p - 0.3) / 0.55; S.x = side.x + Math.sin(q * Math.PI * 8) * 2; S.y = lerp(side.y, up.y, q); S.rot = Math.sin(q * Math.PI * 8) * 0.18; S.flip = true; }
          else travel('jump', S, up, P, (p - 0.85) / 0.15, { h: 12 });
          applyEnd(S, P, p, 0.85);
          return;
        }
        if (P && rel === 'over') {
          const b = box(T), h = Math.max(30, A.y - (b.top - half(S) - 12));
          travel(anim === 'fly' ? 'fly' : 'jump', S, A, B, p, { h, height: m.height });
          S.z = 2.2;
          return;
        }
        let style = anim === 'climb' ? 'jump' : anim;
        if (rel === 'off' && anim === 'roll') { // roll to the edge, then fall
          const edge = { x: box(T).x + box(T).w / 2 + 4, y: A.y };
          if (p < 0.4) travel('roll', S, A, edge, p / 0.4); else { travel('fall', S, edge, B, (p - 0.4) / 0.6); S.rot += (edge.x - A.x) / half(S); }
          return;
        }
        travel(style, S, A, B, p, { height: m.height });
        if (P) applyEnd(S, P, p);
      };
      const land = T && (rel === 'inside') && T.draw === 'water' ? 'splash' : 'thud';
      if (anim === 'jump') { ev(0, 'boing'); if (kind === 'jumpInPlace') { ev(0.5, 'boing'); } else ev(0.96, land); }
      if (anim === 'climb') { ev(0.3, 'scrape'); ev(0.95, 'thud'); }
      if (anim === 'run') ev(0, 'patter');
      if (anim === 'walk') ev(0, 'steps');
      if (anim === 'fly') ev(0, 'flutter');
      if (anim === 'roll') { ev(0, 'rumble'); if (rel === 'off') ev(0.97, 'thud'); }
      if (anim === 'swim') { ev(0, 'splash'); ev(0.5, 'splash'); }
      if (anim === 'fall') { ev(0, 'whistle'); ev(0.95, land); }
      if ((anim === 'run' || anim === 'walk') && P && P.y < A.y - 14) ev(0.72, 'boing');
      if (land === 'splash' && anim !== 'jump' && anim !== 'fall') ev(0.95, 'splash');
      plan.fx = (p, dt, emit) => {
        if (anim === 'swim' || (T && T.draw === 'water' && rel === 'inside' && p > 0.9 && p < 0.97)) {
          if (Math.random() < 0.3) emit({ x: S.x + (Math.random() - 0.5) * 20, y: G - 4, vx: (Math.random() - 0.5) * 40, vy: -60 - Math.random() * 40, g: 160, life: 0.6, shape: 'dot', size: 3, color: '#7cc4f0' });
        }
        if (anim === 'run' && Math.random() < 0.25) emit({ x: S.x, y: G - 2, vx: (S.flip ? -1 : 1) * -20, vy: -10, life: 0.5, shape: 'dot', size: 3, color: 'rgba(120,100,70,.5)', grow: 6 });
      };
      return plan;
    }

    // ---- posers: go somewhere, then take a pose ----
    if (POSERS[anim]) {
      const P = relEnd(S) || centerOf(S);
      const A = (P.x === centerOf(S).x && !rel) ? P : startOf(S);
      const moving = A !== P;
      const lieRot = -Math.PI / 2 * 0.92;
      plan.dur = moving ? 2.2 : 1.2;
      plan.update = p => {
        const split = moving ? 0.62 : 0;
        if (moving && p < split) {
          const style = anim === 'hide' ? 'run' : 'walk';
          travel(style, S, A, P, p / split);
          applyEnd(S, P, p / split, 0.8);
          if (p / split > 0.8) applyEnd(S, P, 1, 0.8);
          return;
        }
        if (moving) { S.x = P.x; S.y = P.y; applyEnd(S, P, 1); }
        const q = seg(p, split, 1);
        S.rot = 0; S.sx = 1; S.sy = 1;
        if (anim === 'sit') { S.sy = 1 - 0.14 * easeOut(q); S.sx = 1 + 0.06 * easeOut(q); S.y = P.y + half(S) * 0.14 * easeOut(q); }
        if (anim === 'stand') { S.sy = 1 + 0.08 * Math.sin(q * Math.PI) + 0.04 * q; }
        if (anim === 'hide') { S.rot = Math.sin(q * 40) * 0.06 * (1 - q * 0.5); S.k = (P.k || 1) * (1 - 0.1 * q); }
        if (anim === 'lie' || anim === 'sleep') { S.rot = lieRot * easeOut(q) * (S.flip ? -1 : 1); S.y = P.y + half(S) * 0.3 * easeOut(q); }
      };
      if (moving) ev(0, anim === 'hide' ? 'patter' : 'steps');
      if (anim === 'sit') ev(moving ? 0.66 : 0.05, 'pop');
      if (anim === 'hide') ev(moving ? 0.62 : 0.05, 'swoosh');
      if (anim === 'sleep') ev(moving ? 0.75 : 0.2, 'snore');
      if (anim === 'stand') ev(moving ? 0.66 : 0.05, 'tap');
      if (anim === 'sleep') plan.idle = (t, dt, emit) => { if (Math.random() < dt * 1.3) emit({ x: S.x + 10, y: S.y - half(S), vx: 14, vy: -22, life: 1.6, shape: 'text', txt: 'z', size: 12 + Math.random() * 6, color: '#5b6fb5' }); };
      return plan;
    }

    // ---- transitive actions ----
    if (O && ['eat', 'drink', 'read', 'kick', 'throw', 'push', 'pull', 'put', 'carry', 'hug', 'catch', 'chase', 'drop'].includes(anim)) {
      const sh = half(S), oh = half(O);
      const P = T ? relPos(rel || 'next', T, O) : null;
      const offRight = { x: W + 40, y: 70 };
      switch (anim) {
        case 'eat': case 'drink': case 'read': {
          const base = (T && rel && !['top', 'inside'].includes(rel)) ? relPos(rel, T, S) : (T && rel ? relPos(rel, T, S) : { x: 140, y: G - sh, z: 2, k: 1 });
          S.x = base.x; S.y = base.y; S.z = base.z; S.k = base.k || 1;
          if (T && base.lift) { T.lift = base.lift; T.legs = !!base.legs; }
          S.flip = true;
          const ox = S.x + half(S) * 1.15 + oh * 0.6, oy = S.y + half(S) * (anim === 'read' ? 0.3 : 0.05);
          O.x = ox; O.y = oy; O.z = 3;
          plan.dur = anim === 'read' ? 2.2 : 1.8;
          plan.update = p => {
            S.sy = 1; S.sx = 1; S.rot = 0; O.alpha = 1; O.rot = 0;
            if (anim === 'eat') {
              const bites = Math.min(3, Math.floor(p * 3.2 + 0.1));
              O.k = 1 - bites / 3;
              const ph = (p * 3) % 1;
              S.rot = 0.12 * Math.sin(ph * Math.PI); S.x = base.x + 4 * Math.sin(ph * Math.PI);
              O.alpha = O.k > 0.01 ? 1 : 0;
            } else if (anim === 'drink') {
              O.rot = -0.9 * easeOut(seg(p, 0, 0.25)); O.x = lerp(ox, S.x + half(S) * 0.9, seg(p, 0, 0.25)); O.y = lerp(oy, S.y - half(S) * 0.3, seg(p, 0, 0.25));
              O.alpha = 1 - seg(p, 0.8, 1); S.rot = 0.1 * Math.sin(p * Math.PI * 4);
            } else {
              S.y = base.y + Math.sin(p * Math.PI * 4) * 1.5; O.rot = Math.sin(p * Math.PI * 2) * 0.05;
            }
          };
          if (anim === 'eat') { ev(0.08, 'crunch'); ev(0.4, 'crunch'); ev(0.72, 'crunch'); }
          if (anim === 'drink') { ev(0.35, 'gulp'); ev(0.65, 'gulp'); }
          if (anim === 'read') { ev(0.05, 'page'); ev(0.6, 'page'); }
          plan.fx = (p, dt, emit) => {
            if (anim === 'eat' && Math.random() < 0.35) emit({ x: O.x, y: O.y, vx: (Math.random() - 0.3) * 60, vy: -40 - Math.random() * 40, g: 220, life: 0.6, shape: 'dot', size: 2.5, color: '#c8873e' });
            if (anim === 'read' && Math.random() < dt * 3) emit({ x: O.x, y: O.y - oh, vx: (Math.random() - 0.5) * 20, vy: -30, life: 1.2, shape: 'text', txt: 'abcABC'[Math.floor(Math.random() * 6)], size: 12, color: '#3b7f6f' });
          };
          return plan;
        }
        case 'kick': case 'throw': {
          S.x = 70; S.y = G - sh; S.flip = true;
          const O0 = anim === 'kick' ? { x: S.x + sh + oh + 2, y: G - oh } : { x: S.x - 4, y: S.y - sh - oh * 0.9 };
          const O1 = P || offRight;
          const k1 = P ? (P.k || 1) : 1;
          const hit = anim === 'kick' ? 0.3 : 0.28;
          plan.dur = 1.6;
          plan.update = p => {
            const a = seg(p, 0, hit);
            S.rot = anim === 'kick' ? -0.25 * Math.sin(a * Math.PI) : -0.25 * Math.sin(a * Math.PI);
            S.x = 70 + (anim === 'kick' ? 10 * Math.sin(a * Math.PI) : 0);
            if (p < hit) { O.x = O0.x - (anim === 'throw' ? 8 * a : 0); O.y = O0.y; O.rot = 0; O.k = 1; O.z = 2.5; return; }
            const q = seg(p, hit, 1);
            const h = 80;
            O.x = lerp(O0.x, O1.x, q); O.y = lerp(O0.y, O1.y, q) - h * 4 * q * (1 - q);
            O.rot = q * 8; O.k = lerp(1, k1, seg(q, 0.8, 1));
            if (P && q > 0.9) { O.z = P.z != null ? P.z : 2.5; if (P.lift) { T.lift = P.lift * seg(q, 0.9, 1); T.legs = !!P.legs; } }
            if (q >= 1) O.rot = 0;
          };
          ev(anim === 'kick' ? hit : hit - 0.02, anim === 'kick' ? 'thump' : 'whoosh');
          if (P) ev(0.98, T.draw === 'water' && rel === 'inside' ? 'splash' : 'thud');
          return plan;
        }
        case 'push': case 'pull': case 'carry': case 'put': case 'chase': {
          const gap = sh + oh + 2;
          let O0, O1, S0, S1, holdOnHead = anim === 'carry' || anim === 'put';
          if (anim === 'push') { S0 = { x: 50, y: G - sh }; O0 = { x: 50 + gap, y: G - oh }; O1 = P || { x: O0.x + 140, y: O0.y }; S1 = { x: O1.x - gap, y: G - sh }; }
          else if (anim === 'pull') { O0 = { x: 70, y: G - oh }; S0 = { x: 70 + gap, y: G - sh }; O1 = P || { x: 200, y: O0.y }; S1 = { x: O1.x + gap, y: G - sh }; }
          else if (anim === 'chase') { S0 = { x: 40, y: G - sh }; O0 = { x: 130, y: G - oh }; S1 = { x: 250, y: G - sh }; O1 = { x: 330, y: G - oh }; }
          else { // carry / put: object rides on head
            S0 = { x: 50, y: G - sh }; O0 = { x: 50, y: S0.y - sh - oh * 0.8 };
            const stand = T ? Math.max(60, box(T).x - box(T).w / 2 - sh - 4) : 260;
            S1 = { x: stand, y: G - sh }; O1 = P || { x: stand + sh + oh, y: G - oh };
          }
          if (anim === 'chase' || anim === 'pull' || anim === 'push') { if (P && anim !== 'push') O1 = P; }
          plan.dur = anim === 'put' ? 2.4 : 2;
          plan.update = p => {
            const walkEnd = anim === 'put' || anim === 'carry' ? (T || anim === 'put' ? 0.62 : 1) : 1;
            const q = seg(p, 0, walkEnd);
            travel(anim === 'chase' ? 'run' : 'walk', S, S0, S1, q);
            if (anim === 'pull') S.flip = S1.x > S0.x;
            if (holdOnHead) {
              if (p < walkEnd) { O.x = S.x; O.y = S.y - sh - oh * 0.8; O.rot = 0; O.k = 1; O.z = 2.5; }
              else {
                const r2 = seg(p, walkEnd, 1);
                const from = { x: S1.x, y: S1.y - sh - oh * 0.8 };
                O.x = lerp(from.x, O1.x, ease(r2)); O.y = lerp(from.y, O1.y, ease(r2)) - 30 * Math.sin(r2 * Math.PI);
                O.k = lerp(1, P ? (P.k || 1) : 1, r2);
                if (r2 > 0.85) { O.z = P && P.z != null ? P.z : 2.5; if (P && P.lift) { T.lift = P.lift * seg(r2, 0.85, 1); T.legs = !!P.legs; } }
              }
            } else {
              const mv = anim === 'chase' ? 'run' : anim === 'push' ? 'walk' : 'walk';
              const st = { x: O.x, y: O.y };
              travel(mv, O, O0, O1, q);
              if (anim === 'push' || anim === 'pull') { O.rot = 0; O.sy = 1; O.flip = false; if (O.n.id === 'ball') O.rot = (O.x - O0.x) / oh; }
              if (P && q > 0.85) { O.k = lerp(1, P.k || 1, seg(q, 0.85, 1)); O.z = P.z != null ? P.z : 2.5; if (P.lift) { T.lift = P.lift * seg(q, 0.85, 1); T.legs = !!P.legs; } }
              void st;
            }
          };
          ev(0, anim === 'chase' ? 'patter' : anim === 'push' || anim === 'pull' ? 'scrape' : 'steps');
          if (anim === 'put') ev(0.97, 'tap');
          return plan;
        }
        case 'drop': {
          const stand = T ? box(T).x - box(T).w / 2 - sh + 6 : 150;
          S.x = stand; S.y = G - sh; S.flip = true;
          const O0 = { x: S.x + sh * 0.9, y: S.y - sh * 0.4 };
          const O1 = P || { x: O0.x + 10, y: G - oh };
          plan.dur = 1.3;
          plan.update = p => {
            const q = seg(p, 0.15, 1);
            O.x = lerp(O0.x, O1.x, q); O.y = O0.y + (O1.y - O0.y) * q * q;
            O.rot = q * 1.5; O.k = lerp(1, P ? P.k || 1 : 1, seg(q, 0.8, 1));
            if (P && q > 0.85) { O.z = P.z != null ? P.z : 2.5; if (P.lift) { T.lift = P.lift * seg(q, 0.85, 1); T.legs = !!P.legs; } }
            if (q >= 1) O.rot = 0;
          };
          ev(0.15, 'whistle'); ev(0.98, T && T.draw === 'water' ? 'splash' : 'thud');
          return plan;
        }
        case 'catch': {
          S.x = 120; S.y = G - sh; S.flip = true;
          const hand = { x: S.x + sh * 0.9, y: S.y - sh * 0.3 };
          plan.dur = 1.4;
          plan.update = p => {
            const q = ease(p);
            O.x = lerp(offRight.x, hand.x, q); O.y = lerp(offRight.y, hand.y, q) - 60 * Math.sin(q * Math.PI);
            O.rot = (1 - q) * 6;
            S.y = G - sh - (p > 0.9 ? 8 * Math.sin(seg(p, 0.9, 1) * Math.PI) : 0);
          };
          ev(0.05, 'whoosh'); ev(0.96, 'pop');
          return plan;
        }
        case 'hug': {
          O.x = 230; O.y = G - oh; O.flip = false;
          const S0 = { x: 60, y: G - sh }, S1 = { x: O.x - (sh + oh) * 0.75, y: G - sh };
          plan.dur = 2;
          plan.update = p => {
            travel('walk', S, S0, S1, seg(p, 0, 0.65));
            const q = seg(p, 0.65, 1), sq = Math.sin(q * Math.PI);
            S.sx = 1 + 0.08 * sq; O.sx = 1 + 0.08 * sq; S.rot = 0.15 * sq; O.rot = -0.15 * sq;
            S.x = lerp(S.x, S1.x + 6, sq);
          };
          ev(0.66, 'aww');
          plan.fx = (p, dt, emit) => { if (p > 0.7 && Math.random() < dt * 6) emit({ x: (S.x + O.x) / 2, y: S.y - sh, vx: (Math.random() - 0.5) * 30, vy: -40, life: 1, shape: 'text', txt: '♥', size: 14, color: '#e0567a' }); };
          return plan;
        }
      }
    }

    // ---- copula: "The cat is under the box" / "The bear is sad" ----
    if (anim === 'place' || anim === 'mood') {
      const P = relEnd(S) || { x: 180, y: G - half(S), z: 2, k: 1 };
      plan.dur = 1.3;
      plan.update = p => {
        const q = seg(p, 0, 0.75);
        S.x = P.x; S.y = lerp(P.y - 60, P.y, bounceOut(q)); S.alpha = seg(p, 0, 0.25);
        S.k = P.k || 1; S.z = P.z != null ? P.z : 2; S.rot = 0; S.sx = 1; S.sy = 1;
        if (P.lift && T) { T.lift = P.lift * easeOut(seg(p, 0.55, 0.9)); T.legs = !!P.legs; }
      };
      if (rel) {
        ev(0.6, 'chime');
        plan.overlay = (ctx, p) => {
          if (p < 0.85) return;
          const a = Math.min(1, (p - 0.85) * 6);
          ctx.save(); ctx.globalAlpha = a * 0.85; ctx.setLineDash([4, 4]); ctx.lineWidth = 2; ctx.strokeStyle = '#e9a21b';
          ctx.beginPath(); ctx.ellipse(S.x, S.y, half(S) + 9, half(S) + 7, 0, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
        };
      } else ev(0.6, { happy: 'sparkle', sad: 'sob', angry: 'shout', sleepy: 'snore', scared: 'whistle', hungry: 'gulp' }[m.mood] || 'chime');
      return plan;
    }

    // ---- actions done in place ----
    const P = (T && rel && rel !== 'at') ? relEnd(S) : (rel === 'at' ? { x: 90, y: G - half(S), z: 2, k: 1 } : { x: 170, y: G - half(S), z: 2, k: 1 });
    S.x = P.x; S.y = P.y; S.z = P.z != null ? P.z : 2; S.k = P.k || 1;
    if (P.lift && T) { T.lift = P.lift; T.legs = !!P.legs; }
    if (T) S.flip = T.x > S.x;
    const amp = m.amp || 1;
    plan.dur = { dance: 2, sing: 2, laugh: 1.6, smile: 1.4, cry: 2, sigh: 2, sneeze: 1.6, shout: 1.3, wave: 1.6, look: 1.6, play: 2 }[anim] || 1.6;
    plan.update = p => {
      S.rot = 0; S.sx = 1; S.sy = 1; S.x = P.x; S.y = P.y;
      switch (anim) {
        case 'dance': S.rot = Math.sin(p * Math.PI * 4) * 0.28; S.y = P.y - Math.abs(Math.sin(p * Math.PI * 4)) * 10; break;
        case 'sing': S.y = P.y - Math.sin(p * Math.PI * 6) * 2; S.sy = 1 + 0.04 * Math.sin(p * Math.PI * 6); break;
        case 'laugh': S.x = P.x + Math.sin(p * Math.PI * 22) * 2.5 * amp; S.sy = 1 - 0.06 * Math.abs(Math.sin(p * Math.PI * 10)); S.rot = -0.08 * Math.sin(p * Math.PI); break;
        case 'smile': S.sy = 1 + 0.05 * Math.sin(p * Math.PI); break;
        case 'cry': S.sy = 1 - 0.05 * Math.abs(Math.sin(p * Math.PI * 6)); S.rot = 0.05 * Math.sin(p * Math.PI * 3); break;
        case 'sigh': {
          const inh = easeOut(seg(p, 0, 0.32)), exh = ease(seg(p, 0.32, 1));
          const big = 0.12 * amp;
          S.sy = 1 + big * inh - (big + 0.12 * amp) * exh; S.sx = 1 - 0.03 * inh + 0.07 * exh * amp;
          S.y = P.y + half(S) * (1 - S.sy); S.rot = (S.flip ? 1 : -1) * -0.1 * exh;
          break;
        }
        case 'sneeze': {
          const a = seg(p, 0, 0.55), b = seg(p, 0.55, 0.7), c = seg(p, 0.7, 1);
          const dir = S.flip ? 1 : -1;
          S.rot = dir * (-0.28 * easeOut(a) + 0.55 * b - 0.27 * c);
          S.sy = 1 + 0.1 * a - 0.18 * b + 0.08 * c;
          break;
        }
        case 'shout': S.k = (P.k || 1) * (1 + 0.15 * amp * Math.sin(seg(p, 0, 0.5) * Math.PI)); break;
        case 'wave': S.rot = Math.sin(p * Math.PI * 6) * 0.25; break;
        case 'look': S.rot = (S.flip ? 1 : -1) * -0.12 * Math.sin(seg(p, 0, 0.3) * Math.PI / 2); if (T) T.pulse = Math.max(T.pulse, 0.6 * Math.sin(p * Math.PI)); break;
        case 'play':
          S.y = P.y - Math.abs(Math.sin(p * Math.PI * 4)) * 10;
          if (T) T.sy = 1 + 0.06 * Math.sin(p * Math.PI * 4 + Math.PI / 2);
          break;
      }
    };
    const SFX = { dance: 'music', sing: 'notes', laugh: 'haha', smile: 'sparkle', cry: 'sob', sigh: 'sigh', sneeze: 'achoo', shout: 'shout', wave: 'swoosh', play: 'boing' };
    if (SFX[anim]) ev(0, SFX[anim]);
    if (anim === 'play') ev(0.5, 'boing');
    const mouth = () => ({ x: S.x + (S.flip ? 1 : -1) * half(S) * 0.85, y: S.y + half(S) * 0.1 });
    plan.fx = (p, dt, emit) => {
      const r = Math.random();
      if (anim === 'sing' && r < dt * 4) emit({ x: mouth().x, y: S.y - half(S) * 0.4, vx: (S.flip ? 1 : -1) * 18, vy: -34, life: 1.3, shape: 'text', txt: Math.random() < 0.5 ? '♪' : '♫', size: 16, color: '#1f7a68', wobble: 1 });
      if (anim === 'dance' && r < dt * 3) emit({ x: S.x + (Math.random() - 0.5) * 40, y: S.y - half(S), vx: 0, vy: -30, life: 1.1, shape: 'text', txt: '♪', size: 15, color: '#c0661b', wobble: 1 });
      if (anim === 'laugh' && r < dt * 5) emit({ x: S.x + (Math.random() - 0.3) * 30, y: S.y - half(S) * 0.8, vx: (Math.random() - 0.5) * 30, vy: -36, life: 0.9, shape: 'text', txt: 'ha', size: 13 * amp, color: '#c0661b' });
      if (anim === 'smile' && r < dt * 4) emit({ x: S.x + (Math.random() - 0.5) * 36, y: S.y - half(S) * 0.6, vx: 0, vy: -16, life: 0.9, shape: 'text', txt: '✦', size: 12, color: '#e9a21b' });
      if (anim === 'cry' && r < dt * 9) { const side = Math.random() < 0.5 ? -1 : 1; emit({ x: S.x + side * half(S) * 0.35, y: S.y - half(S) * 0.05, vx: side * 22, vy: -10, g: 260, life: 0.8, shape: 'drop', size: 3.2, color: '#5aa8e6' }); }
      if (anim === 'sigh' && p > 0.32 && p < 0.9 && r < dt * 16 * amp) {
        const mo = mouth(), dir = S.flip ? 1 : -1;
        emit({ x: mo.x, y: mo.y, vx: dir * (40 + Math.random() * 30) * amp, vy: 6 + Math.random() * 10, life: 1.1, shape: 'puff', size: 3 + Math.random() * 3, grow: 14 * amp, color: 'rgba(150,165,175,.55)' });
      }
      if (anim === 'sneeze' && p > 0.55 && p < 0.68) for (let k = 0; k < 3; k++) {
        const mo = mouth(), dir = S.flip ? 1 : -1;
        emit({ x: mo.x, y: mo.y, vx: dir * (90 + Math.random() * 90), vy: (Math.random() - 0.6) * 60, g: 120, life: 0.6, shape: 'dot', size: 2 + Math.random() * 2, color: 'rgba(120,190,230,.8)' });
      }
      if (anim === 'shout' && p < 0.6 && r < dt * 10) { const dir = S.flip ? 1 : -1; emit({ x: mouth().x, y: S.y - 4, vx: dir * 80, vy: (Math.random() - 0.5) * 50, life: 0.5, shape: 'text', txt: '!', size: 16 * amp, color: '#d0452f' }); }
      if (anim === 'play' && r < dt * 3) emit({ x: (S.x + (T ? T.x : S.x)) / 2, y: S.y - half(S), vx: 0, vy: -30, life: 1, shape: 'text', txt: '♥', size: 13, color: '#e0567a' });
    };
    if (anim === 'look' && T) plan.overlay = (ctx, p) => {
      const a = Math.sin(clamp(p, 0, 1) * Math.PI) || (p >= 1 ? 0.5 : 0);
      ctx.save(); ctx.globalAlpha = 0.8 * Math.max(a, p >= 1 ? 0.5 : 0); ctx.setLineDash([3, 5]); ctx.strokeStyle = '#1f7a68'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(S.x + half(S) * 0.6, S.y - half(S) * 0.2); ctx.lineTo(box(T).x - box(T).w * 0.3, box(T).y); ctx.stroke(); ctx.restore();
    };
    return plan;
  }

  function moodFx(mood, S, t, dt, emit) {
    const r = Math.random(), h = half(S);
    if (mood === 'happy' && r < dt * 3) emit({ x: S.x + (Math.random() - 0.5) * h * 2.4, y: S.y - h * 0.8, vx: 0, vy: -18, life: 1, shape: 'text', txt: '✦', size: 12, color: '#e9a21b' });
    if (mood === 'sad' && r < dt * 4) emit({ x: S.x + (Math.random() < 0.5 ? -1 : 1) * h * 0.35, y: S.y, vx: 0, vy: 10, g: 200, life: 0.7, shape: 'drop', size: 3, color: '#5aa8e6' });
    if (mood === 'angry' && r < dt * 2) emit({ x: S.x + h * 0.7, y: S.y - h * 0.9, vx: 0, vy: -6, life: 0.6, shape: 'text', txt: '💢', size: 16, color: '#d0452f' });
    if (mood === 'sleepy' && r < dt * 1.3) emit({ x: S.x + h * 0.4, y: S.y - h, vx: 14, vy: -22, life: 1.6, shape: 'text', txt: 'z', size: 14, color: '#5b6fb5' });
    if (mood === 'scared' && r < dt * 3) emit({ x: S.x + h * 0.7, y: S.y - h * 0.6, vx: 10, vy: 20, g: 100, life: 0.6, shape: 'drop', size: 3, color: '#6fb7e8' });
    if (mood === 'hungry' && r < dt * 1) emit({ x: S.x + h * 0.9, y: S.y - h * 1.1, vx: 0, vy: -10, life: 1.4, shape: 'text', txt: '🍎', size: 14, color: '#000' });
    if (mood === 'scared') S.rot = Math.sin(t * 50) * 0.04;
    if (mood === 'sad') S.sy = 0.95;
  }

  function Stage(canvas, opts) {
    opts = opts || {};
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.onEvent = opts.onEvent || function () {};
    this.raf = opts.raf || (cb => (global.requestAnimationFrame || (f => setTimeout(() => f(Date.now()), 16)))(cb));
    this.now = opts.now || (() => (global.performance ? global.performance.now() : Date.now()));
    this.reduceMotion = !!opts.reduceMotion;
    this.parts = [];
    this.plan = null; this.scene = null; this.state = 'empty';
    this.running = false;
    this.resize(opts.width, opts.dpr);
  }
  Stage.W = W; Stage.H = H;
  Stage.prototype.resize = function (cssWidth, dpr) {
    dpr = dpr || global.devicePixelRatio || 1;
    const w = cssWidth || this.canvas.clientWidth || W;
    this.canvas.width = Math.round(w * dpr);
    this.canvas.height = Math.round(w * H / W * dpr);
    this.scale = (w * dpr) / W;
    if (this.plan) this.draw();
  };
  // Load a scene. still=true shows the finished picture without animating.
  Stage.prototype.load = function (scene, still) {
    this.scene = scene; this.plan = makePlan(scene); this.parts = [];
    this.cycle = 0; this.fired = new Set();
    if (still) { this.plan.update(1); this.state = 'hold'; this.tHold = this.now(); this.actionP = 1; this.intro = 1; }
    else { this.plan.update(0); this.state = 'intro'; this.tIntro = this.now(); this.actionP = 0; this.intro = 0; }
    this._kick();
  };
  Stage.prototype.startAction = function () {
    if (!this.plan || this.state === 'action') return;
    this.state = 'action'; this.tAction = this.now(); this.fired = new Set(); this._kick();
  };
  Stage.prototype.pulse = function (role, label) {
    if (!this.plan) return;
    const e = this.plan.ents.find(x => x.role === role);
    if (e) { e.pulse = 1; e.label = label || ''; e.labelT = 1.6; this._kick(); }
  };
  Stage.prototype._kick = function () {
    if (this.running) return;
    this.running = true; this.last = this.now();
    const step = () => {
      const t = this.now(), dt = Math.min(0.05, (t - this.last) / 1000); this.last = t;
      const keep = this.tick(t, dt);
      this.draw();
      if (keep) this.raf(step); else this.running = false;
    };
    this.raf(step);
  };
  Stage.prototype.tick = function (t, dt) {
    const pl = this.plan; if (!pl) return false;
    const sc = this.scene, m = sc.modifiers || {};
    const dur = pl.dur / (m.speed || 1) * (this.reduceMotion ? 0.6 : 1);
    const reps = m.repeat || 1;
    const emit = p => this.parts.push(Object.assign({ age: 0, vx: 0, vy: 0, g: 0 }, p));
    if (this.state === 'intro') {
      this.intro = Math.min(1, (t - this.tIntro) / 400);
      if (this.intro >= 1) this.state = 'ready';
    } else if (this.state === 'action') {
      const total = (t - this.tAction) / 1000 / dur;
      const cyc = Math.min(reps - 1, Math.floor(total));
      let p = total - cyc; if (total >= reps) p = 1;
      if (cyc !== this.cycle) { this.cycle = cyc; this.fired = new Set(); }
      pl.update(clamp(p, 0, 1));
      const audible = (this.loopCount || 0) < 2;
      pl.events.forEach((e, idx) => {
        const key = idx + ':' + cyc;
        if (p >= e.at && !this.fired.has(key)) { this.fired.add(key); if (audible) this.onEvent({ type: 'sfx', name: e.sfx, volume: pl.sfxVol }); }
      });
      if (pl.fx) pl.fx(p, dt, emit);
      this.actionP = p;
      if (total >= reps) {
        this.state = 'hold'; this.tHold = t; this.onEvent({ type: 'done' });
      }
    } else if (this.state === 'hold') {
      if (sc.loop && t - this.tHold > 600) {
        this.loopCount = (this.loopCount || 0) + 1;
        if (this.loopCount < 12) { this.plan.update(0); this.startAction(); }
      }
    }
    if (pl.idle && (this.state === 'hold' || this.state === 'ready')) pl.idle(t / 1000, dt, emit);
    // particles
    this.parts.forEach(q => { q.age += dt; q.vy += (q.g || 0) * dt; q.x += q.vx * dt; q.y += q.vy * dt; });
    this.parts = this.parts.filter(q => q.age < q.life);
    let busy = this.parts.length > 0 || this.state === 'intro' || this.state === 'action' || (sc.loop && (this.loopCount || 0) < 12) || !!pl.idle;
    pl.ents.forEach(e => { if (e.pulse > 0) { e.pulse = Math.max(0, e.pulse - dt * 1.4); busy = true; } if (e.labelT > 0) { e.labelT -= dt; busy = true; } });
    return busy;
  };

  // ---- drawing ----
  Stage.prototype.draw = function () {
    const ctx = this.ctx, pl = this.plan;
    ctx.setTransform(this.scale, 0, 0, this.scale, 0, 0);
    drawBackground(ctx, this.scene ? this.scene.tense : 'present', this.now() / 1000);
    if (!pl) return;
    const items = pl.ents.map(e => ({ z: e.z, f: () => drawEnt(ctx, e, this.intro) }));
    const water = pl.ents.find(e => e.draw === 'water');
    if (water) items.push({ z: 1.5, f: () => drawWaterFront(ctx, water, this.now() / 1000, this.intro) });
    items.sort((a, b) => a.z - b.z).forEach(it => it.f());
    if (pl.overlay) pl.overlay(ctx, this.state === 'hold' ? 1 : this.actionP || 0);
    drawParticles(ctx, this.parts);
    pl.ents.forEach(e => { if (e.labelT > 0 && e.label) drawLabel(ctx, e); });
    if (this.scene && (this.scene.tense === 'future')) drawFutureFrame(ctx);
  };

  function drawBackground(ctx, tense, t) {
    const past = tense === 'past' || tense === 'pastProgressive', fut = tense === 'future';
    const sky = ctx.createLinearGradient(0, 0, 0, HORIZON);
    if (past) { sky.addColorStop(0, '#e9d7b4'); sky.addColorStop(1, '#f4e8cf'); }
    else if (fut) { sky.addColorStop(0, '#cfd6f5'); sky.addColorStop(1, '#eceffd'); }
    else { sky.addColorStop(0, '#9fd3f2'); sky.addColorStop(1, '#dff1fb'); }
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, HORIZON + 2);
    // distant hills
    ctx.fillStyle = past ? '#d8c08f' : fut ? '#c3cde9' : '#b9dfa6';
    ctx.beginPath(); ctx.moveTo(0, HORIZON);
    for (let x = 0; x <= W; x += 10) ctx.lineTo(x, HORIZON - 14 - 10 * Math.sin(x / 47) - 6 * Math.sin(x / 19 + 1));
    ctx.lineTo(W, HORIZON); ctx.closePath(); ctx.fill();
    // ground
    const gr = ctx.createLinearGradient(0, HORIZON, 0, H);
    if (past) { gr.addColorStop(0, '#cdb27c'); gr.addColorStop(1, '#b89a63'); }
    else if (fut) { gr.addColorStop(0, '#b6c3e6'); gr.addColorStop(1, '#a2b1dd'); }
    else { gr.addColorStop(0, '#93cd78'); gr.addColorStop(1, '#73b35c'); }
    ctx.fillStyle = gr; ctx.fillRect(0, HORIZON, W, H - HORIZON);
    ctx.strokeStyle = past ? 'rgba(120,90,40,.15)' : fut ? 'rgba(80,90,150,.12)' : 'rgba(40,100,40,.12)';
    ctx.lineWidth = 1;
    for (let y = HORIZON + 12; y < H; y += 14) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    if (fut) { // twinkles: imagined / not yet real
      ctx.fillStyle = 'rgba(255,255,255,.9)';
      for (let i = 0; i < 9; i++) { const x = (i * 71) % W + 12, y = 18 + (i * 37) % 90, a = 0.5 + 0.5 * Math.sin(t * 2 + i); ctx.globalAlpha = a; ctx.fillRect(x, y, 2, 2); }
      ctx.globalAlpha = 1;
    }
  }
  function drawFutureFrame(ctx) {
    ctx.save(); ctx.setLineDash([8, 6]); ctx.strokeStyle = 'rgba(90,100,170,.55)'; ctx.lineWidth = 3;
    ctx.strokeRect(6, 6, W - 12, H - 12); ctx.restore();
  }
  function drawShadow(ctx, e, intro) {
    if (e.draw === 'water' || (e.lex && e.lex.sky) || e.alpha < 0.05) return;
    const h = half(e), feet = e.y + h - e.lift;
    if (e.y < 100) return;
    const lane = e.z < 0 ? GB : e.z >= 3 ? GF : G;
    const above = Math.max(0, lane - feet);
    if (above > 70) return;
    const w = (e.draw === 'table' ? 56 * e.size / BASE : h * 0.95) * (1 - above / 120);
    ctx.save(); ctx.globalAlpha = 0.18 * e.alpha * intro; ctx.fillStyle = '#1b2a1e';
    ctx.beginPath(); ctx.ellipse(e.x, lane + 1, w, w * 0.18, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  function drawEnt(ctx, e, intro) {
    const pop = intro < 1 ? 0.6 + 0.4 * easeOut(intro) : 1;
    if (e.draw === 'water') return drawWaterBack(ctx, e, intro);
    drawShadow(ctx, e, intro);
    const k = e.k * pop * (1 + 0.12 * Math.sin(e.pulse * Math.PI));
    ctx.save();
    ctx.globalAlpha = clamp(e.alpha * intro, 0, 1);
    if (e.legs && e.lift > 2) { // little legs for raised furniture
      const b = box(e); ctx.strokeStyle = '#7a4a2a'; ctx.lineWidth = 3;
      [-0.32, 0.32].forEach(f => { ctx.beginPath(); ctx.moveTo(e.x + b.w * f, b.bottom - 4); ctx.lineTo(e.x + b.w * f, b.bottom + e.lift); ctx.stroke(); });
    }
    if (e.pulse > 0) {
      ctx.save(); ctx.globalAlpha = e.pulse * 0.5; ctx.fillStyle = '#ffd36b';
      const b = box(e); ctx.beginPath(); ctx.ellipse(e.x, b.y, b.w * 0.62, b.h * 0.62, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    }
    ctx.translate(e.x, e.y - e.lift);
    ctx.rotate(e.rot);
    ctx.scale((e.flip ? -1 : 1) * e.sx * k, e.sy * k);
    if (e.draw === 'table') drawTable(ctx, e.size / BASE);
    else {
      ctx.font = e.size + 'px ' + EMOJI_FONT;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(e.emoji, 0, e.size * 0.06);
    }
    ctx.restore();
  }
  function drawTable(ctx, k) {
    const w = 118 * k, h = 60 * k;
    ctx.fillStyle = '#8a5530';
    ctx.fillRect(-w / 2 + 8 * k, -h / 2 + 8 * k, 8 * k, h - 8 * k);
    ctx.fillRect(w / 2 - 16 * k, -h / 2 + 8 * k, 8 * k, h - 8 * k);
    ctx.fillStyle = '#b5773f';
    roundRect(ctx, -w / 2, -h / 2, w, 11 * k, 3 * k); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(-w / 2 + 4 * k, -h / 2 + 2 * k, w - 8 * k, 2 * k);
  }
  function drawWaterBack(ctx, e, intro) {
    const b = box(e);
    ctx.save(); ctx.globalAlpha = intro;
    const g = ctx.createLinearGradient(0, b.top, 0, H);
    g.addColorStop(0, '#5fb3e8'); g.addColorStop(1, '#2d7fc0');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.ellipse(b.x, b.top + 26, b.w / 2, 34, 0, Math.PI, 0); ctx.lineTo(b.x + b.w / 2, H); ctx.lineTo(b.x - b.w / 2, H); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
  function drawWaterFront(ctx, e, t, intro) {
    const b = box(e);
    ctx.save(); ctx.globalAlpha = 0.72 * intro;
    ctx.beginPath();
    ctx.moveTo(b.x - b.w / 2, G + 8);
    for (let x = -b.w / 2; x <= b.w / 2; x += 6) ctx.lineTo(b.x + x, G + 8 + Math.sin(x / 9 + t * 3) * 2);
    ctx.lineTo(b.x + b.w / 2, H); ctx.lineTo(b.x - b.w / 2, H); ctx.closePath();
    const g = ctx.createLinearGradient(0, G, 0, H); g.addColorStop(0, '#6cbcf0'); g.addColorStop(1, '#2a74b4');
    ctx.fillStyle = g; ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,.7)'; ctx.lineWidth = 1.5; ctx.beginPath();
    for (let x = -b.w / 2 + 6; x <= b.w / 2 - 6; x += 6) { const y = G + 8 + Math.sin(x / 9 + t * 3) * 2; x === -b.w / 2 + 6 ? ctx.moveTo(b.x + x, y) : ctx.lineTo(b.x + x, y); }
    ctx.stroke(); ctx.restore();
  }
  function drawParticles(ctx, parts) {
    parts.forEach(q => {
      const a = 1 - q.age / q.life;
      ctx.save(); ctx.globalAlpha = clamp(a, 0, 1); ctx.fillStyle = q.color;
      const x = q.x + (q.wobble ? Math.sin(q.age * 8) * 4 : 0);
      if (q.shape === 'text') {
        ctx.font = '700 ' + q.size + 'px "Baloo 2",' + EMOJI_FONT; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(q.txt, x, q.y);
      } else if (q.shape === 'drop') {
        ctx.beginPath(); ctx.ellipse(x, q.y, q.size * 0.75, q.size * 1.15, 0, 0, Math.PI * 2); ctx.fill();
      } else {
        const r = q.size + (q.grow || 0) * (q.age / q.life);
        ctx.beginPath(); ctx.arc(x, q.y, r, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
    });
  }
  function drawLabel(ctx, e) {
    const b = box(e), txt = e.label;
    ctx.save(); ctx.globalAlpha = clamp(e.labelT / 0.4, 0, 1);
    ctx.font = '700 15px "Baloo 2", system-ui, sans-serif';
    const w = ctx.measureText(txt).width + 16, x = clamp(b.x - w / 2, 4, W - w - 4), y = Math.max(4, b.top - 30);
    ctx.fillStyle = '#1c2a27'; roundRect(ctx, x, y, w, 22, 11); ctx.fill();
    ctx.fillStyle = '#ffd36b'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(txt, x + w / 2, y + 12);
    ctx.restore();
  }
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }

  /* ================= 5. Sfx (Web Audio, synthesized) ================= */
  function Sfx(factory) { this.factory = factory; this.ac = null; this.enabled = true; }
  Sfx.prototype.unlock = function () {
    try {
      if (!this.ac) {
        this.ac = this.factory && this.factory();
        if (!this.ac) return;
        this.master = this.ac.createGain(); this.master.gain.value = 0.8; this.master.connect(this.ac.destination);
        const len = this.ac.sampleRate, buf = this.ac.createBuffer(1, len, this.ac.sampleRate), d = buf.getChannelData(0);
        for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
        this.noiseBuf = buf;
      }
      if (this.ac.state === 'suspended') this.ac.resume();
    } catch (e) { this.ac = null; }
  };
  Sfx.prototype.play = function (name, vol) {
    if (!this.enabled || !this.ac || !SOUNDS[name]) return;
    try { SOUNDS[name](this, this.ac.currentTime + 0.01, clamp(vol || 1, 0.2, 2)); } catch (e) { /* ignore */ }
  };
  function tone(s, t, o, v) {
    const ac = s.ac, osc = ac.createOscillator(), g = ac.createGain();
    const dur = o.dur, gain = Math.max(0.0002, (o.gain || 0.3) * v), f0 = o.f0, f1 = o.f1 || o.f0;
    osc.type = o.type || 'sine';
    osc.frequency.setValueAtTime(f0, t);
    if (f1 !== f0) osc.frequency.exponentialRampToValueAtTime(Math.max(1, f1), t + dur);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(gain, t + (o.attack || 0.005)); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    let node = osc;
    if (o.lp) { const f = ac.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = o.lp; node.connect(f); node = f; }
    if (o.vib) { const l = ac.createOscillator(), lg = ac.createGain(); l.frequency.value = o.vib; lg.gain.value = f0 * 0.05; l.connect(lg); lg.connect(osc.frequency); l.start(t); l.stop(t + dur + 0.05); }
    node.connect(g); g.connect(s.master); osc.start(t); osc.stop(t + dur + 0.05);
  }
  function noise(s, t, o, v) {
    const ac = s.ac, src = ac.createBufferSource(); src.buffer = s.noiseBuf; src.loop = true;
    const f = ac.createBiquadFilter(); f.type = o.type || 'bandpass'; f.Q.value = o.Q || 1;
    const f0 = o.f0 || 1000, f1 = o.f1 || f0, dur = o.dur;
    f.frequency.setValueAtTime(f0, t); if (f1 !== f0) f.frequency.exponentialRampToValueAtTime(f1, t + dur);
    const g = ac.createGain(), gain = Math.max(0.0002, (o.gain || 0.3) * v);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(gain, t + (o.attack || 0.01)); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(f); f.connect(g); g.connect(s.master); src.start(t, Math.random() * 0.5); src.stop(t + dur + 0.05);
  }
  const SOUNDS = {
    boing: (s, t, v) => tone(s, t, { f0: 170, f1: 560, dur: 0.3, gain: 0.3, vib: 16 }, v),
    thud: (s, t, v) => { tone(s, t, { f0: 140, f1: 45, dur: 0.22, gain: 0.6 }, v); noise(s, t, { type: 'lowpass', f0: 400, dur: 0.1, gain: 0.3 }, v); },
    patter: (s, t, v) => { for (let i = 0; i < 7; i++) noise(s, t + i * 0.09, { f0: 1700, Q: 2, dur: 0.05, gain: 0.2 }, v); },
    steps: (s, t, v) => { for (let i = 0; i < 4; i++) { noise(s, t + i * 0.24, { f0: 800, Q: 1.5, dur: 0.08, gain: 0.25 }, v); tone(s, t + i * 0.24, { f0: 95, f1: 70, dur: 0.07, gain: 0.2 }, v); } },
    flutter: (s, t, v) => { for (let i = 0; i < 16; i++) noise(s, t + i * 0.055, { f0: 900, Q: 0.8, dur: 0.04, gain: 0.14 }, v); },
    whistle: (s, t, v) => tone(s, t, { f0: 1500, f1: 350, dur: 0.6, gain: 0.12 }, v),
    pop: (s, t, v) => tone(s, t, { f0: 480, f1: 980, dur: 0.1, gain: 0.35 }, v),
    snore: (s, t, v) => { for (let i = 0; i < 2; i++) tone(s, t + i * 1.3, { type: 'sawtooth', f0: 78, f1: 60, dur: 1.0, gain: 0.14, attack: 0.4, lp: 420 }, v); },
    swoosh: (s, t, v) => noise(s, t, { f0: 400, f1: 2800, Q: 0.9, dur: 0.35, gain: 0.3, attack: 0.12 }, v),
    whoosh: (s, t, v) => noise(s, t, { f0: 300, f1: 2200, Q: 0.9, dur: 0.5, gain: 0.3, attack: 0.2 }, v),
    splash: (s, t, v) => { noise(s, t, { type: 'highpass', f0: 1000, dur: 0.55, gain: 0.4 }, v); for (let i = 0; i < 5; i++) tone(s, t + 0.05 + i * 0.06, { f0: 700 + Math.random() * 900, dur: 0.05, gain: 0.07 }, v); },
    scrape: (s, t, v) => { for (let i = 0; i < 9; i++) noise(s, t + i * 0.07, { f0: 2400, Q: 3, dur: 0.045, gain: 0.12 }, v); },
    rumble: (s, t, v) => noise(s, t, { type: 'lowpass', f0: 180, dur: 1, gain: 0.55, attack: 0.1 }, v),
    music: (s, t, v) => [523, 659, 784, 1047, 784, 659].forEach((f, i) => tone(s, t + i * 0.17, { type: 'triangle', f0: f, dur: 0.18, gain: 0.18 }, v)),
    notes: (s, t, v) => [392, 440, 523, 587, 523].forEach((f, i) => tone(s, t + i * 0.24, { type: 'sine', f0: f, dur: 0.22, gain: 0.2, vib: 6 }, v)),
    haha: (s, t, v) => { for (let i = 0; i < 4; i++) { tone(s, t + i * 0.17, { type: 'triangle', f0: 430 - i * 15, f1: 360 - i * 15, dur: 0.12, gain: 0.25 }, v); noise(s, t + i * 0.17, { f0: 1300, Q: 2, dur: 0.08, gain: 0.05 }, v); } },
    sob: (s, t, v) => { for (let i = 0; i < 2; i++) tone(s, t + i * 0.55, { f0: 620, f1: 420, dur: 0.45, gain: 0.14, vib: 7 }, v); },
    // the bear's sigh: breathy noise that swells then slowly falls, plus a low voice
    sigh: (s, t, v) => { noise(s, t, { f0: 750, f1: 420, Q: 1.4, dur: 1.4, gain: 0.5, attack: 0.35 }, v); noise(s, t, { type: 'lowpass', f0: 900, f1: 500, dur: 1.3, gain: 0.2, attack: 0.35 }, v); tone(s, t + 0.25, { f0: 170, f1: 110, dur: 1.0, gain: 0.06, attack: 0.2 }, v); },
    achoo: (s, t, v) => { noise(s, t, { f0: 500, f1: 1400, dur: 0.5, gain: 0.15, attack: 0.35 }, v); noise(s, t + 0.85, { type: 'highpass', f0: 1800, dur: 0.28, gain: 0.55 }, v); tone(s, t + 0.85, { f0: 320, f1: 190, dur: 0.18, gain: 0.2 }, v); },
    crunch: (s, t, v) => { for (let j = 0; j < 6; j++) noise(s, t + j * 0.028, { type: 'highpass', f0: 2500, dur: 0.025, gain: 0.32 }, v); },
    gulp: (s, t, v) => tone(s, t, { f0: 270, f1: 110, dur: 0.13, gain: 0.35 }, v),
    thump: (s, t, v) => { tone(s, t, { f0: 115, f1: 50, dur: 0.15, gain: 0.6 }, v); noise(s, t, { type: 'lowpass', f0: 900, dur: 0.05, gain: 0.3 }, v); },
    tap: (s, t, v) => { tone(s, t, { f0: 900, f1: 700, dur: 0.06, gain: 0.25 }, v); noise(s, t, { type: 'highpass', f0: 3000, dur: 0.02, gain: 0.15 }, v); },
    chime: (s, t, v) => { tone(s, t, { f0: 880, dur: 0.7, gain: 0.15 }, v); tone(s, t + 0.08, { f0: 1320, dur: 0.7, gain: 0.08 }, v); },
    aww: (s, t, v) => { tone(s, t, { f0: 660, dur: 0.4, gain: 0.12 }, v); tone(s, t + 0.15, { f0: 880, dur: 0.5, gain: 0.12 }, v); },
    page: (s, t, v) => noise(s, t, { type: 'highpass', f0: 3000, dur: 0.14, gain: 0.14, attack: 0.04 }, v),
    shout: (s, t, v) => { tone(s, t, { type: 'sawtooth', f0: 300, f1: 430, dur: 0.45, gain: 0.12, lp: 1600 }, v); noise(s, t, { f0: 1200, Q: 1, dur: 0.4, gain: 0.08 }, v); },
    sparkle: (s, t, v) => [1800, 2200, 2700].forEach((f, i) => tone(s, t + i * 0.07, { f0: f, dur: 0.14, gain: 0.06 }, v)),
  };

  const api = { parse, buildScene, Stage, Sfx, NOUNS, VERBS, PREPS, ADVS, ADJS, TENSES, _makePlan: makePlan };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  global.PictureSentence = api;
})(typeof window !== 'undefined' ? window : globalThis);
