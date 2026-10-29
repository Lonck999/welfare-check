"""W-022 ⬜ 收尾（2026-10-29）：11 筆占位列的 name／description 依原文改寫。
   10-20 batch_w022_fix_placeholders.py 已依各筆 source_url 正文重編條件，但 name／description 仍是舊的
   「（地方加碼/自辦方案）」「本次搜尋未查得…」——前台卡片標題與說明因此跟條件講的是兩件事。
   🔴 名稱與描述只取自 10-20 讀過的原文（見同目錄 batch_w022_fix_placeholders.py 每筆的「來源頁實為…」）；
      142 雲林讀不到、148 金門是 107 年舊新聞 —— 名稱照實標註，不假裝確認過。
   🔴 寫入前先 curl 一次確認來源頁仍在（本檔 --check），讀不到的那筆不改。
   用法：python batch_w022_rename_20261029.py [--check] [--apply]"""
import json, subprocess, sys, psycopg2

N = {
 130: ('桃園市原住民族租金補貼',
       '桃園市原住民族租金補貼：設籍桃園市之原住民、承租本市房屋，家庭成員人均月所得低於最低生活費 3 倍者可申請；不得重複接受其他住宅補助。詳見官方公告。'),
 131: ('臺中市住宅租金補貼增額補助',
       '臺中市住宅租金補貼增額補助：中央租金補貼計畫戶數以外之複審合格戶，且具特殊條件之一（65 歲以上、原住民、身心障礙、特殊境遇家庭、列冊低收入戶、20–40 歲青年等），每戶每月最高 4,000 元。'),
 132: ('臺南市原住民住宅租金補貼',
       '臺南市原住民住宅租金補貼：成年且設籍臺南市滿 4 個月以上之原住民，承租本市住宅，家庭所得、財產符合規定（市區每月最高 3,800 元；115 年度 9/1–10/31 受理）。'),
 133: ('高雄市增額租金補貼',
       '高雄市增額租金補貼：高雄市自辦之租金補貼增額方案（115/1/1–12/31 受理）。資格條件請見官方公告。'),
 134: ('基隆市中低收入老人租賃房屋租金補助',
       '基隆市中低收入老人租賃房屋租金補助：領有本市中低收入老人生活津貼者，租賃非三親等親屬所有之合法房屋（租期自申請日起剩 4 個月以上），且未獲政府同性質補助。'),
 135: ('新竹市加碼青年租金補貼',
       '新竹市加碼青年租金補貼：設籍並實際租屋於新竹市，且為中央 300 億租金補貼「第三級」核定戶（家庭成員 1 人且未滿 40 歲），市府每年加碼 7,000 元。'),
 136: ('嘉義市青年租屋加碼補助',
       '嘉義市青年租屋加碼補助計畫：設籍且實際租屋於嘉義市之 18–45 歲青年，且為中央 300 億擴大租金補貼核定戶，每戶每月最高加碼 500 元，免另行申請。'),
 142: ('雲林縣租金補貼地方方案（官方頁未讀到，待確認）',
       '雲林縣政府網站以 Cloudflare 阻擋自動讀取，本筆方案內容尚未確認。請洽雲林縣政府城鄉發展處。'),
 148: ('金門縣加碼租金補貼（107 年資料，現行是否辦理未確認）',
       '金門縣曾於 107 年延續辦理加碼租金補貼（有配偶／單身與直系親屬同戶／單身滿 40 歲；家庭年收入不超過 93 萬等）。來源為 107 年新聞，現行是否仍辦理未確認，請洽金門縣政府。'),
 205: ('基隆市工作場所性騷擾被害人心理諮商補助',
       '基隆市法制及勞動處「115 年度協助雇主辦理工作場所性騷擾被害人心理諮商補助」：設籍本市或勞務提供地於本市之職場性騷擾案件申訴人或被害人（或提供／轉介心理諮商之雇主）。'),
 220: ('連江縣身心障礙者久任職場津貼',
       '連江縣身心障礙者久任職場津貼：設籍本縣、經本縣身障職業重建服務窗口轉介就業，於同一事業單位工作滿 2 年（5,000 元）或滿 3 年（10,000 元）；每年 7/1–8/30 申請。'),
}
UNCONFIRMED = {142}   # 讀不到的照實寫，不做存活檢查

conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, name, description, source_url from benefits where id = any(%s) and is_active', (list(N),))
rows = {r[0]: r[1:] for r in cur.fetchall()}
assert set(rows) == set(N), set(N) - set(rows)

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
skip = set()
if '--check' in sys.argv:
    for bid, (_, _, url) in sorted(rows.items()):
        if bid in UNCONFIRMED:
            print(bid, '（不檢查：已知讀不到）'); continue
        r = subprocess.run(['curl', '-sL', '-m', '25', '-A', UA, '-o', '/dev/null', '-w', '%{http_code} %{size_download}', url],
                           capture_output=True, text=True)
        code, size = (r.stdout.split() + ['0', '0'])[:2]
        ok = code == '200' and int(float(size)) > 3000
        print(bid, code, size, '✅' if ok else '🔴 讀不到 ⇒ 這筆不改')
        if not ok:
            skip.add(bid)

for bid, (name, desc) in sorted(N.items()):
    if bid in skip:
        continue
    oname, odesc, _ = rows[bid]
    assert ('地方' in oname) or ('本次搜尋未查得' in (odesc or '')), (bid, '舊名稱／描述已不是占位列，可能已被改過 —— 停下來看')
    print(f'{bid}  {oname}  →  {name}')
    if '--apply' in sys.argv:
        cur.execute('update benefits set name=%s, description=%s, updated_at=now() where id=%s', (name, desc, bid))

if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(N) - len(skip), '筆；跳過', sorted(skip))
else:
    print('(dry-run)', len(N) - len(skip), '筆；跳過', sorted(skip))
