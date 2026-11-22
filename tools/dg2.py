# -*- coding: utf-8 -*-
"""DG2 = 머리 없는 RGB555(빅 엔디언, 최상위 비트 1 = 불투명) — 크기로 폭 추정해 PNG 로 → work/dg2/디스크N/
python tools/dg2.py   (폭 표 W 는 실측해서 고칠 것)"""
import os, sys, struct
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from iso import Disc, ROOT
W = {101376: 288, 82944: 288, 124416: 288, 153600: 320, 21632: 104, 10240: 160, 512: 16, 8832: 0, 4320: 0,
     40960: 320, 71680: 320, 3840: 0, 1664: 0, 25600: 160, 4800: 0, 4608: 0, 43008: 0, 50176: 0, 6916: 0}
NAMEW = {'MESBEST.DG2': 224, 'MESBAD.DG2': 224, 'MESGOOD.DG2': 224, 'T_STT1.DG2': 184, 'T_STT2.DG2': 184, 'T_STT3.DG2': 184, 'T_STT4.DG2': 184}   # 실측 2026-11-22


def to_img(d, w):
    a = np.frombuffer(d[:len(d) // 2 * 2], '>u2')
    h = len(a) // w
    a = a[:w * h].reshape(h, w)
    r = (a & 31) << 3; g = ((a >> 5) & 31) << 3; b = ((a >> 10) & 31) << 3
    rgb = np.stack([r, g, b], -1).astype(np.uint8)
    rgb[(a & 0x8000) == 0] = (255, 0, 255) if False else rgb[(a & 0x8000) == 0]
    return Image.fromarray(rgb)


if __name__ == '__main__':
    for n in (1, 2):
        D = Disc(n); out = os.path.join(ROOT, 'work', 'dg2', 'disc%d' % n); os.makedirs(out, exist_ok=True)
        for p, l, s in D.files:
            if not p.upper().split('.')[-1].startswith('DG'):
                continue
            d = D.read(p)
            w = NAMEW.get(p[1:]) or W.get(s) or next((x for x in (320, 288, 256, 240, 192, 160, 144, 128, 120, 112, 104, 96, 80, 72, 64, 56, 48, 40, 32, 24, 16, 8) if (s // 2) % x == 0), s // 2)
            to_img(d, w).save(os.path.join(out, p[1:] + '.png'))
            print(n, p, s, w, (s // 2) // w)
