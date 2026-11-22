# -*- coding: utf-8 -*-
r"""D의 식탁 디스크 빌드(2026-11-22) — 원본 트랙 1 사본에 바꾼 파일을 «제자리»로 쓰고 MODE1 EDC/ECC 재계산
  바꾼 파일(전부 원본과 같은 크기여야 함 — 아니면 실패):
    work/kr/D<n>_<이름>.CPK   (tools/moviesub.py 자막 영상)
    work/gfx/disc<n>/*.DG2    (tools/gfx_kr.py 안내판·엔딩 인사, tools/gfx_logo.py 제목 로고)
  검산: 다시 읽어 바꾼 파일 바이트 일치 · 바꾸지 않은 파일 바이트 원본 일치 · 바뀐 섹터가 바꾼 파일 섹터 밖에 없음.
  출력: dist/build/D no Shokutaku (Japan) (Disc n)/ (트랙 1 패치본 + 원본 트랙 2·cue 복사)
  python tools/build.py               → 계획만(아무것도 안 씀)
  python tools/build.py --write [--install]   ⛔하스피 허락 받고. --install = F:\hospi\roms\ss roms\<디스크 이름>\ 트랙 1 덮어쓰기
"""
import glob, hashlib, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from iso import Disc, ROMS
from cdrom_ecc import recalc_sector

F_DIR = r'F:\hospi\roms\ss roms'
OUT = os.path.join(ROOT, 'dist', 'build')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 22), b''):
            h.update(c)
    return h.hexdigest()


def changes(n):
    ch = {}
    for p in glob.glob(os.path.join(ROOT, 'work', 'kr', 'D%d_*.CPK' % n)):
        ch[os.path.basename(p)[3:]] = open(p, 'rb').read()
    for p in glob.glob(os.path.join(ROOT, 'work', 'gfx', 'disc%d' % n, '*.DG2')):
        ch[os.path.basename(p)] = open(p, 'rb').read()
    return ch


def build(n, write, install):
    D = Disc(n)
    files = {p.lstrip('/'): (l, s) for p, l, s in D.files}
    ch = changes(n)
    plan = []
    for name, data in sorted(ch.items()):
        assert name in files, ('디스크에 없는 파일', n, name)
        l, s = files[name]
        assert len(data) == s, ('크기 다름 — 제자리 불가', n, name, len(data), s)
        plan.append((name, l, data))
    print('== 디스크 %d: 바꿀 파일 %d개' % (n, len(plan)))
    for name, l, data in plan:
        print('   %-14s LBA %6d  %9d B' % (name, l, len(data)))
    if not write:
        return
    title = 'D no Shokutaku (Japan) (Disc %d)' % n
    src_dir = os.path.dirname(ROMS[n])
    out_dir = os.path.join(OUT, title); os.makedirs(out_dir, exist_ok=True)
    t1 = os.path.join(out_dir, os.path.basename(ROMS[n]))
    shutil.copyfile(ROMS[n], t1)
    for f in os.listdir(src_dir):
        if f != os.path.basename(ROMS[n]):
            shutil.copyfile(os.path.join(src_dir, f), os.path.join(out_dir, f))
    dirty = set()
    with open(t1, 'r+b') as fh:
        for name, l, data in plan:
            for i in range(0, len(data), 2048):
                lba = l + i // 2048
                fh.seek(lba * 2352); sec = bytearray(fh.read(2352))
                chunk = data[i:i + 2048]
                sec[16:16 + len(chunk)] = chunk          # 끝 섹터 나머지는 원본 그대로
                fh.seek(lba * 2352); fh.write(recalc_sector(bytes(sec)))
                dirty.add(lba)
    # 검산
    N = Disc.__new__(Disc); N.n = n; N.f = open(t1, 'rb')
    N.files = D.files
    for name, l, data in plan:
        assert N.read(name) == data, ('되읽기 불일치', name)
    size = os.path.getsize(ROMS[n]); assert os.path.getsize(t1) == size
    a = open(ROMS[n], 'rb'); b = open(t1, 'rb'); bad = []
    for s in range(size // 2352):
        x = a.read(2352); y = b.read(2352)
        if x != y and s not in dirty:
            bad.append(s)
    assert not bad, ('바꾼 파일 밖 섹터가 바뀜', bad[:10])
    print('   검산 통과(바뀐 섹터 %d개 전부 바꾼 파일 안) · 트랙 1 md5 %s' % (len(dirty), md5(t1)))
    if install:
        dst = os.path.join(F_DIR, title, os.path.basename(ROMS[n]))
        assert os.path.exists(dst), ('F: 원래 트랙 없음', dst)
        shutil.copyfile(t1, dst)
        assert md5(dst) == md5(t1)
        print('   F: 설치(원래 폴더 트랙 1 덮어씀) %s' % dst)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    for n in (1, 2):
        build(n, '--write' in sys.argv, '--install' in sys.argv)


if __name__ == '__main__':
    main()
