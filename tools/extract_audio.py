# -*- coding: utf-8 -*-
"""소리 든 FILM 의 PCM 조각을 이어 → work/audio/D<n>_<이름>.wav (16 kHz 모노, 받아쓰기용) + work/audio_src/ 원래 표본율 wav
  FILM 소리: 16비트 = 빅 엔디언 부호 · 8비트 = 부호 있음(새턴 FILM)"""
import os, struct, subprocess, sys, wave
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from iso import Disc, ROOT
import filmcpk
FF = r'C:/claude/utils/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe'
OUT = os.path.join(ROOT, 'work', 'audio'); SRC = os.path.join(ROOT, 'work', 'audio_src')
os.makedirs(OUT, exist_ok=True); os.makedirs(SRC, exist_ok=True)
for n in (1, 2):
    D = Disc(n)
    for p, l, s in D.files:
        if not p.endswith('.CPK'):
            continue
        key = 'D%d_%s' % (n, p[1:-4])
        dst = os.path.join(OUT, key + '.wav')
        if os.path.exists(dst):
            continue
        d = D.read(p); f = filmcpk.read(d)
        fd = f['head'][16:48]; rate = struct.unpack_from('>H', fd, 24)[0]; ch, bits = fd[21], fd[22]
        if not rate or not bits:
            continue
        pcm = b''.join(c for c, e in zip(f['chunks'], f['stab']) if e[2] == 0xFFFFFFFF)
        if bits == 16:
            a = np.frombuffer(pcm[:len(pcm) // 2 * 2], '>i2').astype('<i2')
        else:
            a = (np.frombuffer(pcm, 'i1').astype(np.int16) << 8)
        assert ch == 1, (p, ch)
        sp = os.path.join(SRC, key + '.wav')
        w = wave.open(sp, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(a.tobytes()); w.close()
        subprocess.run([FF, '-v', 'error', '-y', '-i', sp, '-ar', '16000', '-ac', '1', dst], check=True)
        print(key, rate, bits, round(len(a) / rate, 1), flush=True)
