# -*- coding: utf-8 -*-
r"""그림 글자 한글화(2026-11-22) — DG2(RGB555 빅 엔디언, 최상위 비트 1)
  ① 안내판 5장(D1ATTEN·D1END·D1MISS·D1RAM·D2ATTEN, 288×176): 다섯 장이 같은 녹슨 판 → 칸마다 «글자 아닌 장»의 화소로 빈 판 하나
     (글자 = 최솟값 >120, 1px 넓힘, ATTENTION 머리 y<30 제외), 다섯 장 모두 글자인 칸은 이웃 평균. 그 위에 흰 갈무리11 가운데 정렬,
     원본 줄 간격 19px·첫 줄 위치는 원문 줄 수에 맞춰 세로 가운데.
  ② 엔딩 인사 3장(MESBEST 224×112 · MESGOOD/MESBAD 224×96): 검은 바탕 + 기울인 나눔명조 ExtraBold, 속 어두운 회색 · 1px 흰 · 1px 베이지 테두리(원본 구조).
  바뀌는 칸만 다시 쓰고 나머지 바이트는 원본 그대로. → work/gfx/<디스크>/<이름>.DG2 · 미리보기 work/check/그림미리보기/<이름>_원본_한글.png
  python tools/gfx_kr.py"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from iso import Disc

GAL = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri11.ttf'
MES_FONT = r'C:/claude/utils/font/nanum-gothic/NanumGothicExtraBold.ttf'   # 명조는 14px 에서 가는 가로획이 끊겨 못 읽음(비교 2026-11-22) → 고딕 ExtraBold
OUTLINE = 4                                       # 흰 테두리 두께(큰 그림 화소 4 = 1px)
MPX = 14                                          # 엔딩 인사 글씨 크기(원본 잉크 높이 약 14)
MYEONG = r'C:\claude\utils\font\nanum-myeongjo\NanumMyeongjoExtraBold.ttf'

PANELS = {   # 이름: (디스크, 줄들)
    'D1ATTEN': (1, ['이 디스크는 디스크 1입니다.', '디스크 2를 넣고 이어서', '플레이해 주세요.', '처음부터 시작하려면', '스타트 버튼을 눌러 주세요.', '(세이브 데이터는 지워집니다)']),
    'D1END': (1, ['디스크 2를 넣어 주세요.']),
    'D1MISS': (1, ['본체 백업 RAM을 확보할 수 없어', '저장하지 못했습니다.', '디스크 2는 플레이할 수 없습니다.']),
    'D1RAM': (1, ['이 게임은 본체 백업 RAM을', '약 5블록 사용합니다.', '이 세가새턴은 저장 용량이 부족해', '디스크 2를 플레이할 수 없습니다.',
                  '저장 데이터 관리 화면에서 세이브 데이터를', '지워 저장 용량을 확보해 주세요.', '스타트 버튼을 누르면', '디스크 1만 플레이할 수 있습니다.']),
    'D2ATTEN': (2, ['이 디스크는 디스크 2입니다.', '디스크 1을 넣고 플레이해 주세요.']),
}
MES = {      # 이름: (줄들 — 앞 공백 = 들여쓰기)
    'MESBEST': ['  이 작품을 감상해 주셔서', '감사합니다.', '  즐겁게 보셨는지요.', '  다음 작품도 기대해 주세요.', '', ' 주식회사 워프 대표 이이노 켄지'],
    'MESGOOD': ['  이 작품을 감상해 주셔서', '감사합니다.', '  하지만 아직 모든 영상을', '보지는 못한 것 같습니다.', '진실까지 앞으로 조금입니다.', '다시 도전해 주시기 바랍니다.'],
    'MESBAD': ['  이 작품을 감상해 주셔서', '감사합니다.', '  하지만 잘못된 운명을', '선택하고 만 것 같습니다.', '다시 도전해 주시기 바랍니다.'],
}


def load(disc, name):
    d = Disc(disc).read(name + '.DG2')
    return d


def to_rgb(d, w):
    a = np.frombuffer(d, '>u2').reshape(-1, w)
    return np.stack([(a & 31) << 3, ((a >> 5) & 31) << 3, ((a >> 10) & 31) << 3], -1).astype(np.uint8), a


def to_dg2(rgb, orig_words):
    r, g, b = (rgb[..., 0].astype(np.uint16) >> 3), (rgb[..., 1].astype(np.uint16) >> 3), (rgb[..., 2].astype(np.uint16) >> 3)
    w = (0x8000 | (b << 10) | (g << 5) | r).astype('>u2')
    same = (rgb >> 3 == np.stack([orig_words & 31, (orig_words >> 5) & 31, (orig_words >> 10) & 31], -1)).all(-1)
    w[same] = orig_words[same]                    # 안 바뀐 칸은 원래 낱말 그대로(최상위 비트 포함)
    return w.tobytes()


def dilate(m, r=1):
    p = np.pad(m, r); out = np.zeros_like(m)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            out |= p[dy:dy + m.shape[0], dx:dx + m.shape[1]]
    return out


def text_mask(rgb):
    m = rgb.min(2) > 120
    m[:30] = False
    return dilate(m)


def plate():
    A = []; W = []
    for n, (disc, _) in PANELS.items():
        rgb, w = to_rgb(load(disc, n), 288); A.append(rgb.astype(int)); W.append(w)
    A = np.stack(A); M = np.stack([text_mask(a.astype(np.uint8)) for a in A])
    P = np.zeros(A.shape[1:], int)
    free = ~M
    cnt = free.sum(0)
    for c in range(3):
        v = np.where(free, A[..., c], 0)
        srt = np.sort(np.where(free, A[..., c], 9999), 0)
        med = np.take_along_axis(srt, np.maximum(cnt - 1, 0)[None] // 2, 0)[0]
        P[..., c] = np.where(cnt > 0, med, 0)
    hole = cnt == 0
    for _ in range(4):                            # 다섯 장 모두 글자인 칸 = 이웃 평균
        if not hole.any(): break
        ys, xs = np.where(hole)
        for y, x in zip(ys, xs):
            nb = [(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if 0 <= y + dy < 176 and 0 <= x + dx < 288 and not hole[y + dy, x + dx]]
            if nb:
                P[y, x] = np.mean([P[q] for q in nb], 0)
        hole = hole & False
    return P.astype(np.uint8)


LAYOUT = {'D1ATTEN': (49, 19), 'D1END': (83, 19), 'D1MISS': (63, 19), 'D1RAM': (44, 15), 'D2ATTEN': (74, 19)}   # 원문 첫 줄 잉크 위·줄 간격(실측)
PANEL_SRC_LINES = {'D1ATTEN': 6, 'D1END': 1, 'D1MISS': 3, 'D1RAM': 8, 'D2ATTEN': 2}
GOTHIC = r'C:/claude/utils/font/nanum-gothic/NanumGothicBold.ttf'
SS = 4                                            # 크게 그려 줄이는 배율(안티에일리어싱)
SHEAR = 0.2                                       # 원본처럼 오른쪽으로 기울임(줄마다 제 높이 가운데 기준 — 위치 안 밀림)


def line_alpha(text, font_path, px, shear=SHEAR):
    """한 줄 → 잉크 덩어리 float 0‥1 [h, w] — 크게 그려 줄마다 기울이고 줄임(잉크 경계로 잘라 냄)"""
    F = ImageFont.truetype(font_path, px * SS)
    d = ImageDraw.Draw(Image.new('L', (8, 8)))
    l, t, r, b = d.textbbox((0, 0), text, font=F)
    pad = int((b - t) * shear) + 2 * SS
    im = Image.new('L', (r - l + 2 * pad, b - t + 2 * SS), 0)
    ImageDraw.Draw(im).text((pad - l, SS - t), text, font=F, fill=255)
    hh = im.height
    im = im.transform(im.size, Image.AFFINE, (1, shear, -shear * hh / 2, 0, 1, 0), Image.BICUBIC)
    a = np.array(im, np.float32) / 255
    ys, xs = np.where(a > 0.02)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    H = -(-a.shape[0] // SS) * SS; W = -(-a.shape[1] // SS) * SS
    a = np.pad(a, ((0, H - a.shape[0]), (0, W - a.shape[1])))
    return a.reshape(H // SS, SS, W // SS, SS).mean((1, 3))


def place(canvas, a, x, y, margin=1):
    h, w = a.shape
    assert x >= margin and y >= 0 and x + w <= canvas.shape[1] - margin and y + h <= canvas.shape[0], ('그림 밖으로 나감', x, y, w, h, canvas.shape)
    canvas[y:y + h, x:x + w] = np.maximum(canvas[y:y + h, x:x + w], a)


def panel_text(base, lines, name, px=13):
    top, LH = LAYOUT[name]
    if name == 'D1RAM': px = 12
    n0 = PANEL_SRC_LINES[name]
    if len(lines) != n0:                          # 줄 수가 원문과 다르면 원문 글자 덩어리 가운데에 맞춤
        top = round(top + (n0 - len(lines)) * LH / 2)
    al = np.zeros(base.shape[:2], np.float32)
    for i, ln in enumerate(lines):
        a = line_alpha(ln, GOTHIC, px)
        place(al, a, round((288 - a.shape[1]) / 2), top + i * LH, 6)
    out = base.astype(np.float32) * (1 - al[..., None]) + np.array([248, 248, 248], np.float32) * al[..., None]
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def ring(a, r):
    """덩어리 a 를 r 화소 넓힌 것(최댓값 걸름)"""
    p = np.pad(a, r); out = np.zeros_like(a)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx <= r * r + r:
                out = np.maximum(out, p[r + dy:r + dy + a.shape[0], r + dx:r + dx + a.shape[1]])
    return out


def line_hi(text, font_path, px, shear):
    """한 줄을 SS 배 크기 그대로(줄이기 전) 0/1 덩어리로 — 기울임 포함, 잉크 경계로 잘라 SS 배수로 맞춤"""
    F = ImageFont.truetype(font_path, px * SS)
    d = ImageDraw.Draw(Image.new('L', (8, 8)))
    l, t, r, b = d.textbbox((0, 0), text, font=F)
    pad = int((b - t) * shear) + 4 * SS
    im = Image.new('L', (r - l + 2 * pad, b - t + 8 * SS), 0)
    ImageDraw.Draw(im).text((pad - l, 4 * SS - t), text, font=F, fill=255)
    hh = im.height
    im = im.transform(im.size, Image.AFFINE, (1, shear, -shear * hh / 2, 0, 1, 0), Image.BICUBIC)
    a = np.array(im) > 127
    ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def mes_img(lines, w, h):
    """엔딩 인사 — 크게(SS 배) 그려 얇은 흰 테두리(OUTLINE 화소)를 큰 그림에서 두르고 줄여서 매끄럽게(하스피 «거칠다·테두리 줄여»)"""
    n = len(lines); LH = min(16, (h - 4) // n)
    top = (h - n * LH) // 2 + 1
    core = np.zeros((h * SS, w * SS), bool)
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        ind = len(ln) - len(ln.lstrip(' '))
        a = line_hi(ln.strip(), MES_FONT, MPX, 0.18)
        x, y = (3 + ind * 8) * SS, (top + i * LH) * SS
        assert x >= 2 * SS and x + a.shape[1] <= (w - 2) * SS and y + a.shape[0] <= h * SS, ('그림 밖으로 나감', ln)
        core[y:y + a.shape[0], x:x + a.shape[1]] |= a
    wh = dilate(core, OUTLINE)                    # 흰 테두리 1px
    be = dilate(wh, 2) & ~wh                      # 그 바깥 아주 얇은 베이지(큰 그림 2화소 = 1/2px)
    wh = wh & ~core
    def down(m):
        return m.reshape(h, SS, w, SS).mean((1, 3)).astype(np.float32)
    ce, we, bb = down(core), down(wh), down(be)
    rgb = (np.array((200, 176, 128), np.float32) * bb[..., None] + np.array((248, 248, 240), np.float32) * we[..., None]
           + np.array((16, 16, 16), np.float32) * ce[..., None])   # 속 = 검정(원본처럼 — 하스피 «원본은 글자가 검은색»)
    return np.clip(rgb + 0.5, 0, 255).astype(np.uint8)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    out = os.path.join(ROOT, 'work', 'gfx'); pv = os.path.join(ROOT, 'work', 'check', '그림미리보기')
    os.makedirs(pv, exist_ok=True)
    P = plate()
    Image.fromarray(P).save(os.path.join(pv, '0_안내판_빈판.png'))
    jobs = [(n, disc, 288, 176, panel_text(P, lines, n)) for n, (disc, lines) in PANELS.items()]
    for n, lines in MES.items():
        d = load(2, n); h = len(d) // 2 // 224
        jobs.append((n, 2, 224, h, mes_img(lines, 224, h)))
    for n, disc, w, h, rgb in jobs:
        orig, words = to_rgb(load(disc, n), w)
        if n in PANELS:                               # 글자 자리(원래 글자 + 새 글자, 1px 넓힘)만 바꿈 — 나머지 바탕은 원본 그대로
            reg = text_mask(orig) | dilate((rgb.astype(int) != P.astype(int)).any(-1), 2)
            rgb = np.where(reg[..., None], rgb, orig)
        data = to_dg2(rgb, words)
        assert len(data) == w * h * 2
        p = os.path.join(out, 'disc%d' % disc); os.makedirs(p, exist_ok=True)
        open(os.path.join(p, n + '.DG2'), 'wb').write(data)
        S = Image.new('RGB', (w * 2 + 8, h), (60, 60, 60)); S.paste(Image.fromarray(orig), (0, 0)); S.paste(Image.fromarray(rgb), (w + 8, 0))
        S.resize((S.width * 2, S.height * 2), Image.NEAREST).save(os.path.join(pv, '%s_원본_한글.png' % n))
        print(n, '바뀐 칸', int((to_rgb(data, w)[1] != words).sum()))


if __name__ == '__main__':
    main()
