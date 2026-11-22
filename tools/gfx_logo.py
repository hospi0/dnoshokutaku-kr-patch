# -*- coding: utf-8 -*-
r"""제목 로고 «D의 식탁» (2026-11-22, 하스피가 준 그림 data/gfx/title_logo_kr_src.png 2117×743)
  원본 T_LOG*.DG2 11장(1장, 320×112) = 같은 로고의 밝기 단계(페이드). 장마다 «T_LOG300 빨강 값 → 그 장 빨강 값» 대응표를
  원본에서 뽑아(같은 값 칸들의 중앙값, 빈 값은 보간, 단조 증가) 한글 로고(T_LOG300 기준판)에 그대로 적용. 초록·파랑 = 0.
  한글 로고 = 받은 그림의 빨강 잉크 범위를 원본 잉크 범위(x 19‥298, y 3‥108) 안에 가로 폭 맞춰 가운데, LANCZOS 축소, 최대 248.
  → work/gfx/disc1/T_LOG*.DG2 · 미리보기 work/check/그림미리보기/T_LOG_원본_한글.png
  python tools/gfx_logo.py"""
import os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from iso import Disc
from gfx_kr import to_rgb, to_dg2

SRC = os.path.join(ROOT, 'data', 'gfx', 'title_logo_kr_src.png')
W, H = 320, 112
BOX = (19, 3, 298, 108)                                   # 원본 T_LOG300 잉크 범위(실측)
NAMES = ['T_LOG6', 'T_LOG18', 'T_LOG31', 'T_LOG50', 'T_LOG75', 'T_LOG100', 'T_LOG150', 'T_LOG175', 'T_LOG200', 'T_LOG300', 'T_LOG350']


def base_kr():
    u = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)
    r = u[..., 0]
    ys, xs = np.where(r > 40)
    r = r[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    bw, bh = BOX[2] - BOX[0] + 1, BOX[3] - BOX[1] + 1
    s = min(bw / r.shape[1], bh / r.shape[0])
    nw, nh = round(r.shape[1] * s), round(r.shape[0] * s)
    sm = np.array(Image.fromarray(np.clip(r, 0, 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS), np.float32)
    out = np.zeros((H, W), np.float32)
    x0 = BOX[0] + (bw - nw) // 2; y0 = BOX[1] + (bh - nh) // 2
    out[y0:y0 + nh, x0:x0 + nw] = sm
    return np.clip(out * 248 / 255, 0, 248)


def lut(base, var):
    """원본 T_LOG300 빨강(base) → 원본 변형 빨강(var) 대응표 256칸"""
    t = np.full(256, np.nan)
    for v in np.unique(base):
        t[int(v)] = np.median(var[base == v])
    t[0] = var[base == 0].mean() if (base == 0).any() else 0
    ok = ~np.isnan(t)
    t = np.interp(np.arange(256), np.where(ok)[0], t[ok])
    return np.maximum.accumulate(t)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = Disc(1)
    orig = {n: to_rgb(D.read(n + '.DG2'), W) for n in NAMES}
    b300 = orig['T_LOG300'][0][..., 0].astype(int)
    kb = base_kr()
    out_dir = os.path.join(ROOT, 'work', 'gfx', 'disc1'); os.makedirs(out_dir, exist_ok=True)
    rows = []
    for n in NAMES:
        rgb0, words = orig[n]
        t = lut(b300, rgb0[..., 0].astype(float))
        red = np.interp(kb, np.arange(256), t)
        rgb = np.zeros((H, W, 3), np.uint8); rgb[..., 0] = np.clip(red + 0.5, 0, 248).astype(np.uint8)
        data = to_dg2(rgb, words)
        open(os.path.join(out_dir, n + '.DG2'), 'wb').write(data)
        rows.append((rgb0, rgb))
        print(n, '최대 빨강 원본 %d → 한글 %d' % (rgb0[..., 0].max(), rgb[..., 0].max()))
    S = Image.new('RGB', (W * 2 + 8, (H + 6) * len(rows)), (60, 60, 60))
    for i, (a, b) in enumerate(rows):
        S.paste(Image.fromarray(a), (0, i * (H + 6))); S.paste(Image.fromarray(b), (W + 8, i * (H + 6)))
    pv = os.path.join(ROOT, 'work', 'check', '그림미리보기'); os.makedirs(pv, exist_ok=True)
    S.save(os.path.join(pv, 'T_LOG_원본_한글_11장.png'))
    big = Image.new('RGB', (W * 2 + 8, H), (60, 60, 60)); big.paste(Image.fromarray(rows[9][0]), (0, 0)); big.paste(Image.fromarray(rows[9][1]), (W + 8, 0))
    big.resize((big.width * 2, big.height * 2), Image.NEAREST).save(os.path.join(pv, 'T_LOG300_원본_한글_2배.png'))


if __name__ == '__main__':
    main()
