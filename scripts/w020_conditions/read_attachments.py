"""W-020：新竹市社會處法規頁的正文在附件（odt/pdf/doc）。抓第一個 law/ 附件 → 轉文字 → {id}_att.txt
用法：python _tmp-w020_att.py 819,820,..."""
import re, subprocess, sys, psycopg2, html
from pathlib import Path
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'
C = Path('/Users/lonck/.hermes/cache/welfare_w020')
ids = [int(x) for x in sys.argv[1].split(',')]
cur = psycopg2.connect(dbname='welfare_check').cursor()
cur.execute('select id, name, source_url from benefits where id = any(%s) order by id', (ids,))
for bid, name, url in cur.fetchall():
    out = C / f'{bid}_att.txt'
    if not out.exists():
        if 'uploaddowndoc' in url:
            links = [url]
        else:
            raw = subprocess.run(['curl', '-sL', '-m', '30', '-A', UA, url], capture_output=True).stdout.decode('utf-8', 'ignore')
            links = [html.unescape(h) for h in re.findall(r'href="(/uploaddowndoc\?file=law/[^"]+)"', raw)]
            # 優先 pdf > odt > doc；同檔不同格式只取一個
            rank = lambda h: (0 if '.pdf' in h.lower().split('&')[0] else 1 if '.odt' in h else 2)
            links = sorted(links, key=rank)
            links = ['https://society.hccg.gov.tw' + h for h in links]
        if not links:
            print(f'=== {bid} {name}：🔴 沒有 law/ 附件'); continue
        texts = []
        seen = set()
        for i, L in enumerate(links):
            stem = L.split('file=')[1].split('&')[0].rsplit('.', 1)[0]
            if stem in seen: continue
            seen.add(stem)
            ext = L.split('file=')[1].split('&')[0].rsplit('.', 1)[1].lower()
            f = C / f'{bid}_{i}.{ext}'
            subprocess.run(['curl', '-sL', '-m', '60', '-A', UA, '-o', str(f), L])
            if ext == 'pdf':
                import pypdf
                try: t = '\n'.join((pg.extract_text() or '') for pg in pypdf.PdfReader(str(f)).pages)
                except Exception as e: t = f'(PDF 讀取失敗：{e})'
            else:
                t = subprocess.run(['textutil', '-convert', 'txt', '-stdout', str(f)], capture_output=True, text=True).stdout
            texts.append(f'【附件 {L.split("filedisplay=")[-1][:80]}】\n' + t)
        out.write_text('\n'.join(texts), encoding='utf-8')
    t = out.read_text(encoding='utf-8')
    t = re.sub(r'[ \t\u3000]+', ' ', t); t = re.sub(r'\n\s*\n+', '\n', t)
    print(f'\n=== {bid} {name}｜{len(t)} 字\n{t[:int(sys.argv[2]) if len(sys.argv)>2 else 1800]}')
