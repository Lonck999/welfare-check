"""青年創業獎勵 994–997 依原文編條件（2026-10-29）。比照 98 青年創業貸款用 has_startup_intent（問卷「有創業意願或正在籌備」）。
   年齡：嘉義市／嘉義縣／花蓮營業稅 18–45；花蓮獎勵「申請截止日年滿 18 歲且未滿 46 歲」⇒ ageMax 45。
   設籍：只有花蓮獎勵明寫「設籍花蓮縣」（年限未寫）⇒ 不編 minResidencyMonths；其餘以營運／登記地為準，放 unchecked。
   用法：python batch_import554_20261029.py [--apply]"""
import json, sys, psycopg2
S = '~/.hermes/cache/welfare_b_rerun_*/p*/NN.txt 正文'
X = {
 994: ('嘉義市', {'ageMin': 18, 'ageMax': 45, 'requiredFlags': ['has_startup_intent'],
        'uncheckedConditions': ['營業稅籍登記在嘉義市之中小企業（創業啟動類或營運模式優化類）', '115 年受理至 4/30，已截止；年度計畫，留意 116 年公告']},
       '嘉義市勞青處「青年創業獎勵補助計畫的申請資格及最高可補助多少?」：18–45歲青年，營業稅籍登記在嘉義市之中小企業皆可提出申請，一般補助經費最高 50 萬元，指定區域最高再加碼空間裝修費 40 萬元，合計最高 90 萬元'),
 995: ('嘉義縣', {'ageMin': 18, 'ageMax': 45, 'requiredFlags': ['has_startup_intent'],
        'uncheckedConditions': ['在嘉義縣實際營運且完成公司或商業登記之店家；新創事業組須為負責人（設立未滿 8 年），接班傳承組須為創辦人二親等內接班人',
                                '須自籌至少 10 萬元；累計獲縣府青創補助未超過 150 萬', '115 年受理至 2/24，已截止；年度計畫，留意 116 年公告']},
       '嘉義縣勞青處【公告】115年嘉義縣青年創業獎勵補助計畫：實施對象為在嘉義縣實際營運且完成公司或商業登記之店家，申請人須為 18歲至45歲之中華民國國民；每案補助 30萬元，評分前兩名每案 40萬元，自籌款至少 10萬元'),
 996: ('花蓮縣', {'ageMin': 18, 'ageMax': 45, 'requiredFlags': ['has_startup_intent'],
        'uncheckedConditions': ['設籍花蓮縣，實際營運或預定營運地點在花蓮縣',
                                '申請日前三年內上過創業輔導相關課程 10 小時以上',
                                '新創設立組：核定後 60 日內完成公司或商業及稅籍登記；創業發展組：事業設立未滿 5 年',
                                '補助不超過核定總經費 70%，須自籌至少 30%', '115 年受理至 9/25，已截止；年度計畫，留意 116 年公告']},
       '花蓮縣青年發展中心「115年度花蓮縣青年創業獎勵補助計畫申請須知（修正版）」：申請人為中華民國國民，申請截止日已年滿 18 歲且未滿 46 歲，並設籍花蓮縣；每案最高補助新臺幣 100 萬元，且不得超過核定計畫總經費 70%'),
 997: ('花蓮縣', {'ageMin': 18, 'ageMax': 45, 'requiredFlags': ['has_startup_intent'],
        'uncheckedConditions': ['已於花蓮縣完成公司、商業或稅籍登記，事業設立未滿 5 年（經認定之新創事業未滿 8 年）',
                                '資本額 1,000 萬元以下，前一年度營業額未達 500 萬元', '未曾接受其他機關同性質營業稅補助', '受理至年度經費用罄']},
       '花蓮縣政府新聞「全國首創！花蓮縣青年創業營業稅補助上路 每年最高補助10萬元」：申請對象為年滿18歲至45歲之中華民國國民，並依法於花蓮縣完成公司、商業或稅籍登記；事業體須為設立未滿5年'),
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, county, eligibility_conditions from benefits where id = any(%s) and is_active', (list(X),))
rows = {r[0]: r[1:] for r in cur.fetchall()}; assert set(rows) == set(X), set(X) - set(rows)
for bid, (county, add, src) in sorted(X.items()):
    c, ec = rows[bid]; assert c == county and (ec or {}).get('counties') == [county], (bid, c, ec)
    new = {'counties': [county], **add, '_source': '2026-10-29 依原文編條件：' + src}
    print(bid, {k: v for k, v in new.items() if k not in ('_source', 'uncheckedConditions')})
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, updated_at=now() where id=%s', (json.dumps(new, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)', len(X))
