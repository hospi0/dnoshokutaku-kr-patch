# -*- coding: utf-8 -*-
r"""음성 받아적기 페이지(2026-11-22, 모노모노 tools/voice_listen.py 에서 가져옴)
  work/voice_draft.tsv 82줄 = 줄마다 그 구간 소리(앞뒤 0.4초 여유, mp3) + 기계 추정(1차·2차) + 고칠 칸(1차로 미리 채움)
  + 말 없는지 확인할 파일 5개(통째). «결과 복사» = «번호\t들은 말» 줄들.
  python tools/voice_listen.py → work/check/voice_listen.html"""
import base64, csv, html, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FF = r'C:/claude/utils/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe'
CHECK = ['D1_OPENING', 'D1_R10M00', 'D2_MU_09', 'D2_R14M37', 'D2_R14M38']

CSS = """:root{--bg:#f6f5f2;--fg:#1d1d1b;--mut:#6b6a66;--card:#fff;--line:#dedbd4;--acc:#b4441c}
@media (prefers-color-scheme:dark){:root{--bg:#1b1a19;--fg:#ece9e3;--mut:#a29e96;--card:#262523;--line:#3a3835;--acc:#e0774f}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,"Malgun Gothic",sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}h1{font-size:20px;margin:8px 0}h2{font-size:17px;margin:24px 0 4px}p.note{color:var(--mut);margin:4px 0 16px}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:2}
button{font:inherit;padding:6px 12px;border:1px solid var(--acc);background:var(--acc);color:#fff;border-radius:6px;cursor:pointer}
.row{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:10px 0}
.row.done{border-left:4px solid #3a8a4a}
.hd{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.id{font-weight:600;font-family:ui-monospace,Consolas,monospace}
.meta{color:var(--mut);font-size:13px}audio{height:32px;max-width:100%}
.g{display:grid;grid-template-columns:72px 1fr;gap:4px 8px;margin-top:6px;font-size:14px}.g>span{color:var(--mut)}
input.t{font:inherit;width:100%;box-sizing:border-box;padding:5px 8px;border:1px solid var(--line);border-radius:5px;background:var(--bg);color:var(--fg)}
label{font-size:13px;color:var(--mut)}textarea{width:100%;height:140px;box-sizing:border-box;font:12px ui-monospace,Consolas,monospace;background:var(--card);color:var(--fg);border:1px solid var(--line);margin-top:12px}"""

JS = r"""function copyOut(){const L=[];document.querySelectorAll('.row').forEach(r=>{const i=r.querySelector('input.t'),t=i.value.trim(),s=r.querySelector('input.s').checked;
if(s)L.push(r.dataset.id+'\t(소리만)');else if(t!==i.defaultValue.trim())L.push(r.dataset.id+'\t'+t)});
const txt=L.length?L.join('\n'):'(고친 줄 없음)';document.getElementById('out').value=txt;
navigator.clipboard.writeText(txt).then(()=>{document.getElementById('msg').textContent=L.length+'줄 복사됨'},()=>{document.getElementById('msg').textContent='아래 칸에서 복사해 주세요'})}
document.addEventListener('input',e=>{const r=e.target.closest('.row');if(r){const i=r.querySelector('input.t');r.classList.toggle('done',i.value.trim()!==i.defaultValue.trim()||r.querySelector('input.s').checked)}});"""


def mp3(key, a=None, b=None):
    cmd = [FF, '-v', 'error']
    if a is not None:
        cmd += ['-ss', '%.2f' % max(0, a - 0.4), '-to', '%.2f' % (b + 0.4)]
    cmd += ['-i', os.path.join(ROOT, 'work', 'audio_src', key + '.wav'), '-ac', '1', '-b:a', '64k', '-f', 'mp3', '-']
    return base64.b64encode(subprocess.run(cmd, capture_output=True, check=True).stdout).decode()


def row(rid, meta, b64, guess, pre, label):
    return ('<div class="row" data-id="%s"><div class="hd"><span class="id">%s</span><span class="meta">%s</span>'
            '<audio controls preload="none" src="data:audio/mpeg;base64,%s"></audio></div><div class="g">%s'
            '<span>들은 말</span><input class="t" value="%s"><span></span><label><input class="s" type="checkbox"> %s</label></div></div>'
            % (rid, rid, meta, b64, guess, html.escape(pre, True), label))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'work', 'voice_draft.tsv'), encoding='utf-8'), delimiter='\t'))
    body = []
    for r in rows:
        a, b = float(r['start']), float(r['end'])
        guess = '<span>2차 추정</span><div class="meta">%s</div>' % html.escape(r['ja_2차(VAD)'] or '—')
        body.append(row(r['id'], '%s · %.1f–%.1f초' % (r['file'], a, b), mp3(r['file'], a, b), guess, r['ja_1차'], '말 아님(소리만, 자막 안 넣음)'))
    body.append('<h2>말이 없는지 확인할 영상 %d개</h2><p class="note">받아쓰기로는 말이 안 잡혔습니다. 대사가 들리면 «들은 말»에 적어 주세요(시각도 같이, 예: «1:05 ○○○»).</p>' % len(CHECK))
    for k in CHECK:
        body.append(row(k, '통째', mp3(k), '', '', '말 없음 확인'))
    page = ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>D의 식탁 받아적기</title><style>' + CSS + '</style></head><body><main><h1>D의 식탁 음성 받아적기</h1>'
            '<p class="note">아버지 대사 %d줄입니다. «들은 말» 칸에 기계 받아쓰기(1차)를 미리 넣어 두었으니 틀린 곳만 고쳐 주세요(일본어로, 또는 뜻만 한국어로). '
            '한 칸에 두 문장이 붙어 있거나 잘렸으면 그대로 적어 주시면 나눔은 제가 합니다. 고친 칸은 왼쪽이 초록색이 됩니다. 다 하면 «결과 복사» → 대화창에 붙여 주세요(고친 줄만 나갑니다).</p>'
            '<div class="bar"><button onclick="copyOut()">결과 복사</button><span id="msg" class="meta"></span></div>' % len(rows) + ''.join(body) +
            '<textarea id="out" placeholder="결과 복사를 누르면 여기에도 나옵니다"></textarea></main><script>' + JS + '</script></body></html>')
    p = os.path.join(ROOT, 'work', 'check', 'voice_listen.html')
    open(p, 'w', encoding='utf-8').write(page)
    print('%d줄 + 확인 %d개 → %s (%d KB)' % (len(rows), len(CHECK), p, os.path.getsize(p) // 1024))


if __name__ == '__main__':
    main()
