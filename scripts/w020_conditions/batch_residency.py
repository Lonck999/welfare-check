"""問卷第 2a 題（2026-10-20 Lonck 定 A）：把原文的設籍年限編成 minResidencyMonths。
   🔴 只收「申請人本人須在該縣市設籍滿 N」—— 以下不收（編了會把該看到的人刷掉）：
      · OR：「設籍滿 4 個月 或 勞務提供地在本市」（695、705）
      · 父或母任一方：生育獎勵（250、257、264、265、267、621）—— 問卷問的是填表人本人
      · 固定日期：「101/7/31 前設籍滿 1 年」（612）、「112/1/1 前設籍滿 3 年」（913）、「110 年前入籍」（417）、「114/12/31 前」（227、296）
      · 金門 219「設籍滿 1 年並累積滿 6 年」—— 兩段式
   每筆附原文片段（DB description 讀出），寫入前 assert 片段還在 description 裡，防止 id 對錯。
   用法：python batch_residency.py [--apply]"""
import json, sys, psycopg2
X = {  # id: (月數, 原文片段)
    226: (12, '設籍並實際居住本市滿1年'),
    229: (12, '設籍本市滿一年以上'),
    230: (12, '設籍本市滿 一年'),
    350: (12, '設籍於本市滿1年'),
    418: (12, '設籍本縣滿1年'),
    421: (36, '設籍本縣滿三年以上'),
    559: (4, '設籍本市4個月(含)以上'),
    573: (6, '設籍本市六個月以上'),
    633: (6, '設籍且實際居住本市滿六個月'),
    697: (4, '設籍本市並實際居住四個月以上'),
    698: (4, '並設籍本市4個月以上'),
    700: (4, '設籍本市並實際居住四個月以上'),
    714: (4, '設籍並實際居住本市4個月以上'),
    746: (6, '設籍本市六個月以上'),
    880: (6, '設籍並實際居住本市滿半年以上'),
    887: (12, '設籍本市滿 1 年'),
    902: (6, '設籍並實際居住本市滿半年'),
    942: (36, '設籍滿三年'),
    955: (12, '設籍滿一年'),
    959: (6, '設籍6個月以上'),
    961: (36, '設籍滿三年'),
    963: (12, '設籍滿1年'),
    821: (120, None),  # 新竹愛老津貼：W-020 第 1 批原文讀過「連續設籍並實際居住本市滿 10 年」（附件，不在 description）
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, name, description, eligibility_conditions from benefits where id = any(%s) and is_active', (list(X),))
rows = {r[0]: r[1:] for r in cur.fetchall()}
assert set(rows) == set(X), set(X) - set(rows)
for bid, (months, frag) in sorted(X.items()):
    name, desc, ec = rows[bid]
    if frag:
        # description 或今天讀官方頁寫進 uncheckedConditions 的原文，兩處都算（880/887/902 是後者）
        hay = (desc or '').replace('\u3000', ' ') + json.dumps(ec or {}, ensure_ascii=False).replace(' ', '')
        assert frag in hay or frag.replace(' ', '') in hay, (bid, name, '原文片段找不到')
    ec = dict(ec or {})
    ec['minResidencyMonths'] = months
    # 已經寫進 uncheckedConditions 的設籍敘述 → 拿掉（避免同一條在「還缺」出現兩次）
    if 'uncheckedConditions' in ec:
        # 🔴 不用模式整句刪（第一版「設籍開頭＋<30 字」把 887 的 183 天條件一起刪掉，assert 擋下）—— 一律逐筆明列
        # 設籍和其他條件寫在同一句的：只剪掉設籍那段，其他保留
        CUT = {880: ('設籍並實際居住本市滿半年以上，', '實際居住本市，'),
               902: ('設籍並實際居住本市滿半年，', '實際居住本市，'),
               887: ('設籍本市滿 1 年且最近一年國內居住超過 183 天', '最近一年國內居住超過 183 天')}
        if bid in CUT:
            a, b = CUT[bid]
            n = sum(a in u for u in ec['uncheckedConditions'])
            assert n == 1, (bid, '要剪的句子出現', n, '次')
            ec['uncheckedConditions'] = [u.replace(a, b) for u in ec['uncheckedConditions']]
        if bid == 821:
            a = '截至申請日連續設籍並實際居住本市滿 10 年'
            assert a in ec['uncheckedConditions']
            ec['uncheckedConditions'] = [u for u in ec['uncheckedConditions'] if u != a] + ['設籍須連續（中途遷出要重算）並實際居住本市']
    print(f'{bid:<4} {months:>3} 月  {name[:22]}')
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, updated_at=now() where id=%s', (json.dumps(ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)', len(X))
