# -*- coding: utf-8 -*-
r"""2차 받아쓰기(2026-11-22) — 1차(tools/asr.py)에서 대사 후보로 보인 파일만, 프롬프트 없이(1차는 프롬프트를 되뇌는 환청),
  VAD 켬 + 낱말 시각 + 언어 자동 판별도 한 번 → work/asr2/<키>.json
  C:\claude\utils\whisper-venv\Scripts\python.exe tools/asr2.py [키…]"""
import json, os, sys, wave
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'work', 'audio'); OUT = os.path.join(ROOT, 'work', 'asr2')
KEYS = ['D1_RT_01', 'D1_RT_02', 'D2_RT_03', 'D2_RT_04', 'D2_RT_05', 'D2_R14M33', 'D2_R14M34', 'D2_R14M35', 'D2_R14M38',
        'D2_R14M37', 'D2_R14GEAR', 'D1_OPENING', 'D1_MU_01', 'D2_MU_09', 'D1_R10M00', 'D1_TITLESE', 'D1_R01M49',
        'D2_R090TO1', 'D2_R091TO0', 'D2_R094TO5', 'D2_R05M06', 'D2_R08M08', 'D1_R12M43']


def load(p):
    w = wave.open(p, 'rb'); return np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768


def main():
    from faster_whisper import WhisperModel
    m = WhisperModel('large-v3', device='cuda', compute_type='float16')
    os.makedirs(OUT, exist_ok=True)
    for k in (sys.argv[1:] or KEYS):
        a = load(os.path.join(SRC, k + '.wav'))
        _, info = m.transcribe(a[:16000 * 30], beam_size=1)
        lang = (info.language, round(info.language_probability, 2))
        segs, _ = m.transcribe(a, language='ja', beam_size=5, condition_on_previous_text=False, vad_filter=True, word_timestamps=True)
        segs = [[round(s.start, 2), round(s.end, 2), s.text.strip(), round(s.no_speech_prob, 2), round(s.avg_logprob, 2)] for s in segs]
        json.dump({'key': k, 'lang': lang, 'sec': round(len(a) / 16000, 2), 'segs': segs}, open(os.path.join(OUT, k + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        print(k, lang, len(segs), flush=True)


if __name__ == '__main__':
    main()
