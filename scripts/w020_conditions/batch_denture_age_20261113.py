"""C-6b ②（2026-11-13）：17 筆「中低收入老人假牙（地方明細）」條件補正。
   問題（e2e_denture_age.py 實測）：條件只有 ageMin 55 ＋ counties ⇒
     · 60 歲非原住民、年收 90 萬也判 confirmed（17/17 筆）
     · 原文「65 歲以上（原住民 55）＋ 符合其一：列冊低收／中低收…」兩段都沒編進去
   修法（沿用 822／948 已上線的寫法，不新增引擎鍵）：
     · 年齡：照每筆原文 —— 多數 65＋原住民 55；409 臺北／410 新北／422 南投原文不同，逐筆依原文
     · 「符合其一」那串 → uncheckedConditions（OR 條件問卷判不了 ⇒ 最高 possible，不會再 confirmed）
   🔴 每筆附原文片段，寫入前 assert 片段在 description 裡（防 id 對錯）。
   🔴 421 彰化：拿掉 minResidencyMonths 36 —— 那句「設籍滿三年」屬同欄另一個計畫（一般老人全口假牙），
      本筆 source_url（中低收計畫 PDF，2026-11-13 讀過 5 頁）沒有設籍年限；留著會把剛遷入的中低收長者刷掉。
   用法：python batch_denture_age_20261113.py [--apply]"""
import json, sys, psycopg2

ONE_OF = '符合其一：列冊低收入戶／中低收入戶、領中低收入老人生活津貼、領身心障礙者生活補助費、經政府全額補助收容安置、經政府補助身障日間照顧及住宿式照顧費用達 50% 以上'
DOC = '經醫師評估缺牙需裝置假牙'
STD = dict(ageMin=65, ageMinByIdentity={'原住民': 55}, unchecked=[ONE_OF, DOC])

# 🔴 413／414／417／421 的 description 併了「第二個計畫」（一般長者、不限中低收），庫裡沒有獨立一列。
#    只寫中低收那串會讓一般長者看到錯的「還缺」⇒ OR 進同一條，並在 KNOWN-ISSUES 記「該拆成獨立列」。
def with_general(general):
    return dict(ageMin=65, ageMinByIdentity={'原住民': 55},
                unchecked=[ONE_OF.replace('符合其一：', '符合其一：①（中低收計畫）') + f'；②（{general}）', DOC])


X = {  # id: (新年齡設定＋unchecked, 原文片段)
    411: (STD, '設籍本市年滿65歲以上，或年滿55歲以上原住民'),
    412: (dict(ageMin=65, ageMinByIdentity={'原住民': 55},
               unchecked=['65 歲以上須' + ONE_OF[0:].replace('符合其一：', '符合其一：'),
                          '55–64 歲原住民須為列冊低收入戶／中低收入戶', DOC]),
          '設籍本市年滿55歲以上之列冊低（中低）收入戶原住民'),
    413: (with_general('衛生局一般長者全口活動假牙計畫，不限中低收：111/12/25 前設籍且持續在籍，50/12/31 前出生、原住民 60/12/31 前出生，健康牙齒每顎 3 顆以內'),
          '設籍本市年滿65歲以上或年滿55歲以上原住民'),
    414: (with_general('一般老人免費裝假牙計畫，不限中低收：50/12/31 前出生、99/11/26 前曾設籍原高雄縣市且仍在籍；113 年度綜所稅率 20% 以上排除；額滿為止'),
          '65歲以上長輩或民國60年12月31日(含)前出生之55歲以上原住民'),
    415: (STD, '設籍本市年滿65歲以上或年滿55歲以上原住民'),
    417: (with_general('一般身分別老人計畫，不限中低收：年滿 75 歲（40/12/31 前出生）且 110 年前入籍本市、設籍滿 5 年，終身一次'),
          '凡設籍本市年滿65歲以上或年滿55歲以上原住民'),
    419: (STD, '本縣年滿65歲以上或年滿55歲以上原住民'),
    420: (STD, '設籍本縣年滿六十五歲以上或年滿五十五歲以上原住民'),
    421: (with_general('一般老人全口活動假牙計畫，不限中低收：65 歲以上、設籍本縣滿 3 年，需裝全口活動假牙（健康牙齒每顎 3 顆以內），終身一次'),
          '設籍本縣年滿六十五歲以上或年滿五十五歲以上原住民'),
    423: (STD, '設籍本縣年滿65歲以上或55歲以上原住民'),
    425: (STD, '設籍本縣年滿 65 歲以上或年滿 55 歲以上原住民'),
    427: (STD, '年滿65歲以上老人或55歲以上原住民'),
    428: (STD, '年滿65歲以上或年滿55歲以上原住民'),
    430: (dict(ageMin=65, ageMinByIdentity={'原住民': 55},
               unchecked=['設籍須符合其一：溯自申請日連續設籍本縣滿 10 年、或累積設籍滿 20 年（列冊低收／中低收入戶不受設籍年限限制）',
                          '經醫院評估缺牙需裝置活動或固定假牙',
                          '一生最高補助 4 萬元；一般戶超過 2 萬元部分自付 10%']),
          '現設籍本縣且年滿 65 歲以上之長者或年滿 55 歲以上原住民'),
    # 臺北：原文沒有原住民特例；55 歲限列冊低收／中低收，其餘身分 65 歲
    409: (dict(ageMin=55, ageMinByIdentity=None,
               unchecked=['55–64 歲須為列冊本市低收入戶或中低收入戶',
                          '65 歲以上另可為：經本市公費收容安置、領中低收入老人生活津貼、中低收入領收容安置補助、領身心障礙者生活補助費、本市補助身障日照住宿費用達 50% 以上',
                          DOC]),
          '年滿五十五歲以上列冊本市之低收入戶者'),
    # 新北：原住民 55；列冊低收 60；其餘 65 ＋ 符合其一
    410: (dict(ageMin=60, ageMinByIdentity={'原住民': 55},
               unchecked=['60–64 歲（非原住民）須為列冊本市低收入戶',
                          '65 歲以上（原住民 55）須為列冊低收入戶，或符合其一：中低收入戶、領中低收入老人生活津貼、經市府全額補助收容安置、領身心障礙生活補助費、市府補助身障日照住宿費用達 50% 以上',
                          DOC, '5 年內已取得原民局老人假牙補助相同項目者不得申請；事前申請制，向戶籍地區公所申請']),
          '年滿60歲以上列冊本市之低收入戶'),
    # 南投：第一類 65／原住民 55 ＋ 符合其一；第二類 65 歲設籍滿 1 年（一般長者）或 50 歲以上領身障證明
    422: (dict(ageMin=50, ageMinByIdentity=None,
               unchecked=['符合其一：①（第一類）65 歲以上或 55 歲以上原住民，且' + ONE_OF.replace('符合其一：', '符合其一 ') +
                          '；②（第二類）65 歲以上且設籍本縣滿 1 年；③（第二類）50 歲以上領有身心障礙證明', DOC]),
          '設籍本縣年滿五十歲以上領有身心障礙證明'),
}
assert len(X) == 17

conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, name, description, eligibility_conditions from benefits where id = any(%s) and is_active', (list(X),))
rows = {r[0]: r[1:] for r in cur.fetchall()}
assert set(rows) == set(X), set(X) - set(rows)
for bid, (spec, frag) in sorted(X.items()):
    name, desc, ec = rows[bid]
    hay = (desc or '').replace('\u3000', ' ')
    assert frag in hay, (bid, name, '原文片段找不到', frag)
    ec = dict(ec or {})
    assert ec.get('ageMin') == 55, (bid, '預期現值 ageMin 55', ec.get('ageMin'))
    assert 'uncheckedConditions' not in ec, (bid, '已有 unchecked，不可覆蓋')
    ec['ageMin'] = spec['ageMin']
    if spec['ageMinByIdentity']:
        ec['ageMinByIdentity'] = spec['ageMinByIdentity']
    ec['uncheckedConditions'] = spec['unchecked']
    if bid == 421:
        assert ec.pop('minResidencyMonths') == 36
    ec['_source'] = f'C-6b 2026-11-13 依 description 原文（{frag}）補年齡與「符合其一」；見 batch_denture_age_20261113.py'
    print(f"{bid:<4} ageMin {spec['ageMin']}{' 原住民55' if spec['ageMinByIdentity'] else ''}  unchecked {len(spec['unchecked'])}  {name[:20]}")
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, updated_at=now() where id=%s',
                    (json.dumps(ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)', len(X))
