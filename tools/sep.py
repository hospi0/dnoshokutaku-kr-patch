# -*- coding: utf-8 -*-
r"""동영상 소리에서 목소리만 분리(demucs htdemucs) → work/vocals/<키>.npy (16 kHz 모노 float32)
  (게임 천국 tools/sep.py 에서 가져옴 2026-11-22 — 원래 표본율 work/audio_src/<키>.wav 를 44.1 kHz 로 올려 넣음)
  C:\claude\utils\whisper-venv\Scripts\python.exe tools/sep.py D1_RT_01 …"""
import os, sys, wave
import numpy as np
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'work', 'vocals')


def source(k):
    w = wave.open(os.path.join(ROOT, 'work', 'audio_src', k + '.wav')); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
    x = np.interp(np.arange(0, len(x), sr / 44100), np.arange(len(x)), x).astype(np.float32)
    return np.stack([x, x])


def main():
    os.makedirs(OUT, exist_ok=True)
    m = get_model('htdemucs'); m.eval()
    for k in sys.argv[1:]:
        a = source(k)
        with torch.no_grad():
            src = apply_model(m, torch.from_numpy(np.ascontiguousarray(a))[None], device='cpu', split=True, overlap=0.25)[0]
        v = src[m.sources.index('vocals')].mean(0).numpy()
        v16 = v[np.round(np.arange(0, len(v), 44100 / 16000)).astype(int).clip(0, len(v) - 1)]
        np.save(os.path.join(OUT, k + '.npy'), v16.astype(np.float32))
        print('%s %.1fs vocals rms %.4f / 원래 %.4f' % (k, len(v) / 44100, np.sqrt((v ** 2).mean()), np.sqrt((a.mean(0) ** 2).mean())), flush=True)


if __name__ == '__main__':
    main()
