# -*- coding: utf-8 -*-
r"""3차 받아쓰기(2026-11-22) — demucs 목소리(work/vocals/*.npy)로 large-v3 · kotoba-v2 두 모델, VAD 끔·프롬프트 없음·낱말 시각
  → work/asr3/<키>.<모델>.json   C:\claude\utils\whisper-venv\Scripts\python.exe tools/asr3.py 키…"""
import json, os, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'work', 'asr3')
MODELS = {'v3': 'large-v3', 'kotoba': 'kotoba-tech/kotoba-whisper-v2.0-faster'}


def main():
    from faster_whisper import WhisperModel
    os.makedirs(OUT, exist_ok=True)
    only = os.environ.get('ONLY')
    for tag, name in MODELS.items():
        if only and tag != only: continue
        m = WhisperModel(name, device='cuda', compute_type='float16')
        for k in sys.argv[1:]:
            a = np.load(os.path.join(ROOT, 'work', 'vocals', k + '.npy'))
            a = a / max(1e-4, np.abs(a).max()) * 0.9
            segs, _ = m.transcribe(a, language='ja', beam_size=5, condition_on_previous_text=False, vad_filter=False,
                                   word_timestamps=(tag == 'v3'), no_speech_threshold=0.9)   # kotoba 는 낱말 정렬에서 접근 위반으로 뻗음
            segs = [[round(s.start, 2), round(s.end, 2), s.text.strip(), round(s.no_speech_prob, 2), round(s.avg_logprob, 2),
                     [[round(w.start, 2), round(w.end, 2), w.word] for w in (s.words or [])]] for s in segs]
            json.dump({'key': k, 'model': tag, 'segs': segs}, open(os.path.join(OUT, '%s.%s.json' % (k, tag)), 'w', encoding='utf-8'), ensure_ascii=False)
            print(tag, k, len(segs), flush=True)
        del m


if __name__ == '__main__':
    main()
