# -*- coding: utf-8 -*-
"""두 디스크 FILM(.CPK) 목록 — 크기·해상도·소리·길이 → work/movies.tsv"""
import os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from iso import Disc, ROOT
rows = []
for n in (1, 2):
    D = Disc(n)
    for p, l, s in D.files:
        if not p.endswith('.CPK'):
            continue
        h = D.sec(l, 1)
        hl = struct.unpack_from('>I', h, 4)[0]
        h = D.sec(l, (hl + 2047) // 2048)[:hl]
        fd = h[16:48]
        four = fd[8:12]; H, W = struct.unpack_from('>II', fd, 12); bpp, ch, bits = fd[20], fd[21], fd[22]
        rate = struct.unpack_from('>H', fd, 24)[0]
        so = h.index(b'STAB'); base, cnt = struct.unpack_from('>II', h, so + 8)
        last = 0; nv = na = 0; asz = 0
        for i in range(cnt):
            off, ln, i1, i2 = struct.unpack_from('>IIII', h, so + 16 + 16 * i)
            if i1 == 0xFFFFFFFF:
                na += 1; asz += ln
            else:
                nv += 1; last = max(last, (i1 & 0x7FFFFFFF) + i2)
        dur = last / base if base else 0
        adur = asz / (rate * ch * bits / 8) if rate and bits else 0
        rows.append((n, p[1:], s, four.decode('latin1').strip('\0') or '-', W, H, rate, ch, bits, nv, na, round(dur, 2), round(adur, 2)))
os.makedirs(os.path.join(ROOT, 'work'), exist_ok=True)
with open(os.path.join(ROOT, 'work', 'movies.tsv'), 'w', encoding='utf-8') as f:
    f.write('disc\tfile\tsize\tcodec\tw\th\trate\tch\tbits\tvframes\tachunks\tvsec\tasec\n')
    for r in rows:
        f.write('\t'.join(map(str, r)) + '\n')
for n in (1, 2):
    rs = [r for r in rows if r[0] == n]
    print('disc', n, len(rs), '개  영상', round(sum(r[11] for r in rs) / 60, 1), '분  소리', round(sum(r[12] for r in rs) / 60, 1), '분')
from collections import Counter
print(Counter((r[3], r[4], r[5], r[6], r[7], r[8]) for r in rows))
