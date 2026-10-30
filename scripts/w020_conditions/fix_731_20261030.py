"""731 臺中「原住民低收入戶及中低收入戶補助項目」依原文改寫（2026-10-30）。
   FLAG 原因：source_url 與 730 相同（租金補助要點），名稱是資料集標題不是補助名稱。
   查證：
     ① 原始資料集 data.gov.tw 138588（臺中開放資料，2026-04-01 更新）只有 2 列：
        「幼兒托教補助」＝設籍臺中 3 個月以上之原住民中低收入戶，子女課後就托於立案課後托育中心／才藝中心／補習班；
        「建購修繕房屋」＝年滿 20 歲原住民（無金額、無現行頁）
     ② 現行方案：「115年度原住民中低收入戶（含低收入戶）子女課後照顧補助計畫」（西區區公所轉知，2026-06-03 發布）
        ＋ 臺中市服務e櫃台案件頁（申請資格）—— 與資料集第 1 列是同一件事
   ⇒ 731 改寫為課後照顧補助（115 年現行）；「建購修繕房屋」查無現行頁 —— 不新增，記 KNOWN-ISSUES。
   🔴 補助對象是**學生**（原住民身分在孩子身上），填問卷的多半是家長 ⇒ 不設 requiredIdentities（會擋掉非原住民家長），
      原住民身分放 unchecked；家戶條件 mid_low_income＋設籍 4 個月＋家中有未滿 18 歲子女。
   用法：python fix_731_20261030.py [--apply]"""
import json, sys, psycopg2
WEST = 'https://www.west.taichung.gov.tw/831924/832013/832019/3972130'
ESV = 'https://eservices.taichung.gov.tw/AdvSearch/CaseInfo/160/Notices/580077/580003?isHandling=true&isLink=false'
NAME = '臺中市原住民中低收入戶（含低收入戶）子女課後照顧補助'
DESC = ('臺中市原住民族事務委員會：原住民中低收入戶（含低收入戶）子女就讀公私立國小（一年級以上）、國中、日間部高中職，'
        '課後就讀立案安親班或補習班之費用補助；低收入戶家庭優先、中低收入戶次之。分上下半年申請：115 年上半年 7/1–7/25、'
        '下半年 11/1–11/25，向戶籍地區公所申請。不得與原住民課後扶植計畫重複申領。補助金額依計畫核定（頁面未列）。')
EX = ('115年度原住民中低收入戶（含低收入戶）子女課後照顧補助計畫 (一) 受理期限：1、上半年度申請：115 年 7 月 1 日起至 7 月 25 日止。'
      '2、下半年度申請：115 年 11 月 1 日起至 11 月 25 日止。(二) 受理機關：本市各區公所。(三) 補助對象及資格：1、補助對象：公、私立小學、國中及日間部高中職生。'
      '2、補助資格：(1)具原住民身分。(2)設籍本市滿 4 個月以上。(3)原住民中低收入戶 (含低收入戶)；以低收入戶家庭優先補助，中低收入戶次之。')
COND = {'counties': ['臺中市'], 'incomeThreshold': 'mid_low_income', 'minResidencyMonths': 4, 'requiresChildUnder': 18,
        'uncheckedConditions': ['子女具原住民身分，且為列冊原住民中低收入戶（含低收入戶）',
                                '子女就讀公私立國小（一年級以上）、國中或日間部高中職，課後就讀立案安親班或補習班',
                                '115 年下半年受理 11/1–11/25（上半年 7/1–7/25 已截止）；不得與原住民課後扶植計畫重複申領'],
        '_source': f'2026-10-30 FLAG 讀原文改寫：{EX}（{WEST}）；申請資格另見臺中市服務e櫃台（{ESV}）；原始資料集 data.gov.tw/dataset/138588「幼兒托教補助」列'}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select is_active, name, county from benefits where id=731'); a, n, c = cur.fetchone()
assert a and n == '原住民低收入戶及中低收入戶補助項目' and c == '臺中市', (a, n, c)
print('改寫 731', n, '→', NAME)
if '--apply' in sys.argv:
    cur.execute('''update benefits set name=%s, agency='臺中市政府原住民族事務委員會（各區公所受理）', description=%s, source_url=%s,
                   source_excerpt=%s, eligibility_conditions=%s, source_tier='official', validity_status='valid_current',
                   validity_checked_at=now(), deadline_type='annual', application_period='每年上半年 7/1–7/25、下半年 11/1–11/25',
                   notes=null, last_verified_date=current_date, updated_at=now() where id=731''',
                (NAME, DESC, WEST, EX, json.dumps(COND, ensure_ascii=False)))
    assert cur.rowcount == 1
    conn.commit(); print('✅ 改寫 731')
else:
    print('(dry-run)')
