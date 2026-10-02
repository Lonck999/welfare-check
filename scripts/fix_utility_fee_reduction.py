#!/usr/bin/env python3
"""W-007 ③：id 45「水電費減免」—— 內容本身是錯的，不是網址壞掉。

🔴 為什麼不是「換個官方來源」就好（Lonck 2026-09-29 原本選換來源，查完發現換不了）

這筆的四個主張**逐條查證後全部不成立**：

  ① 「每月用電 110 度以下免收基本電費」
     · 110 度是 **101 年以前**的第一級距（經濟部 101-05-15 電價合理化方案原文：
       「第 1 級距用電量由現行 110 度提高到 120 度」）—— 過時 14 年
     · getgrant 自己另一頁寫「112 度」，同站兩個數字互相矛盾
     · 🔴 查到「110 度」最早的出處是 2008-04-28 自由時報：台電「**打算**成立
       社會關懷基金」補貼低收入戶電費 —— 那是 18 年前的**構想**

  ② 法源「對低收入戶用電優待辦法」
     🔴 **這部法不存在**。全國法規資料庫全文檢索「低收入戶用電」→ 查無。

  ③ 台電真正的優惠對象（電業法 §52、§53）
     各級學校、社福機構、護理之家 —— **沒有低收入戶**
     （台電 2024-06-26 新聞稿；另 106 年公告是「身心障礙者維生器材」）

  ④ 「台水減免基本水費」
     · 台水官網 Notice/Detail/7911 只有「用戶內線地下漏水水費減免」
     · 台水營業章程 36 條讀完：只有市政用水減 50%、軍眷優待、漏水減免
     🔴 **沒有低收入戶水費減免**

  ⑤ 《社會救助法》§16 七款特殊救助（本次 curl 原文確認）
     產婦及嬰兒營養補助／托兒／教育／喪葬／居家服務／生育／其他必要之救助
     🔴 **沒有水費、電費、瓦斯** —— 關鍵字四個全部不在條文裡
     ⚠️ 且首句是「直轄市、縣（市）主管機關**得**視實際需要及財力」
        —— 「得」不是「應」⇒ 各縣市自訂、**可以不辦**
        ⇒ 「全國性」這個範圍本身就不成立

✅ 唯一查到的實證：臺北市自己辦的「中低收入戶免收分段加壓維護管理費」
   ⚠️ 那是**免收加壓維護費**（每度 2.5 元）不是減免水費，且是臺北市不是台水。
   🔴 本次找不到可用的官方網址（北水處兩個候選網址實測都 404），
      所以**只在描述裡提到它、不當來源** —— 猜的網址不可寫進資料。

━━ 改法（Lonck 2026-09-29 選「換官方來源」，查完改為「改寫內容＋降級」）

描述改成誠實的版本：中央無全國性規定，依各縣市辦理。
`source_tier` 已經是 `media`（getgrant 是媒體彙整站），**維持 media 不升級** ——
🔴 不可改成 `official`，因為沒有任何官方頁面支持「全國低收入戶水電費減免」。

⚠️ 這支只改 id 45 一筆，不碰 22 筆瓦斯費地方明細
（那些的描述本來就誠實寫「未查得，需洽當地」）。

跑法：
  python3 scripts/fix_utility_fee_reduction.py --dry-run   # 先看
  python3 scripts/fix_utility_fee_reduction.py             # 真的寫
"""
import argparse
import os
import sys

import psycopg2

BENEFIT_ID = 45

# 🔴 寫入前必須成立的身分檢查 —— 用 id 認人很危險（seed 重灌後 id 會變）
MUST_MATCH_NAME = '水電費減免'
MUST_MATCH_URL = 'getgrant.tw/grants/mohw-lowincome-utility-reduce'

NEW_DESCRIPTION = (
    '🔴 中央沒有「全國性低收入戶水電費減免」的規定，實際以各縣市自行辦理為主。\n'
    '\n'
    '查證結果（2026-10-02）：\n'
    '· 《社會救助法》第 16 條列舉的 7 項特殊項目救助為：產婦及嬰兒營養補助、'
    '托兒補助、教育補助、喪葬補助、居家服務、生育補助、其他必要之救助及服務 —— '
    '**不含水費、電費、瓦斯費**。且條文為「直轄市、縣（市）主管機關『得』視實際需要'
    '及財力提供」，各縣市可自行決定是否辦理。\n'
    '· 台電依《電業法》第 52、53 條提供電價優惠的對象是**各級學校、社會福利機構、'
    '護理之家**，不含低收入戶家庭用電。\n'
    '· 台灣自來水公司的水費減免為「用戶內線地下漏水減免」，營業章程亦無低收入戶減免。\n'
    '· 常見流傳的「每月用電 110 度以下免收基本電費」為 101 年以前的電價級距'
    '（經濟部 101 年電價合理化方案已將第 1 級距由 110 度提高至 120 度），'
    '且其出處為 97 年台電研議中的社會關懷基金構想，並非現行制度。\n'
    '\n'
    '✅ 實際可行的查詢方式：向**戶籍地公所或縣市政府社會局（處）**洽詢'
    '當地是否辦理水電費相關補助，或撥 1957 福利諮詢專線。\n'
    '· 已查到的地方實例：臺北市對中低收入戶免收「分段加壓給水維護管理費」'
    '（每度 2.5 元，由臺北自來水事業處辦理，非台水公司）。'
)

NEW_NOTES = (
    '⚠️ 本筆原描述引用的「對低收入戶用電優待辦法」經全國法規資料庫全文檢索'
    '**查無此法**；「110 度免收基本電費」為過時數字。已於 2026-10-02 改寫為'
    '「中央無全國性規定，依各縣市辦理」。\n'
    '⚠️ 水電費減免屬各縣市自辦項目，有無與額度因縣市而異，須個別查證；'
    '瓦斯多為民營瓦斯行供應，更需洽當地。'
)

NEW_EXCERPT = (
    '《社會救助法》第 16 條：直轄市、縣（市）主管機關得視實際需要及財力，'
    '對設籍於該地之低收入戶或中低收入戶提供下列特殊項目救助及服務：'
    '一、產婦及嬰兒營養補助。二、托兒補助。三、教育補助。四、喪葬補助。'
    '五、居家服務。六、生育補助。七、其他必要之救助及服務。'
)

# 🔴 來源改指法條本身（這是唯一真正支持「中央沒規定」這個結論的官方頁面）
NEW_URL = 'https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=D0050078&flno=16'

# 🔴 tier 維持 media → 改成 opendata？不行。
#    law.moj.gov.tw 是官方法規資料庫 ⇒ official 是對的，
#    但它支持的是「§16 沒有水電費」這個**否定陳述**，
#    而 name 仍叫「水電費減免」⇒ 來源與 name 對不上。
#    ⇒ 維持 media，並在 notes 說明。等 22 縣市逐一盤點完再分拆成地方筆。
NEW_TIER = 'media'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        print('🔴 沒有 DATABASE_URL（先 set -a && . backend/.env && set +a）')
        return 2

    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute(
        'select id, name, source_url, source_tier, description, notes '
        'from benefits where id = %s', (BENEFIT_ID,))
    row = cur.fetchone()
    if not row:
        print(f'🔴 找不到 id={BENEFIT_ID}')
        return 1

    _id, name, url, tier, desc, notes = row

    # 🔴 身分檢查：id 可能因 reseed 而指到別筆
    if MUST_MATCH_NAME not in name:
        print(f'🔴 id {BENEFIT_ID} 的 name 是「{name}」，不含「{MUST_MATCH_NAME}」'
              f'—— 可能已 reseed，整筆不動')
        return 1
    if MUST_MATCH_URL not in (url or ''):
        print(f'🔴 source_url 不是預期的 getgrant 頁（實際 {url}）—— 整筆不動')
        return 1

    print(f'📍 id {_id}　{name}')
    print(f'   tier  : {tier} → {NEW_TIER}')
    print(f'   url   : {url}')
    print(f'         → {NEW_URL}')
    print(f'   desc  : {len(desc)} 字 → {len(NEW_DESCRIPTION)} 字')
    print(f'   notes : {len(notes or "")} 字 → {len(NEW_NOTES)} 字')
    print()
    print('── 舊描述 ──')
    print('  ' + desc[:160] + ('…' if len(desc) > 160 else ''))
    print()
    print('── 新描述 ──')
    for line in NEW_DESCRIPTION.split('\n')[:6]:
        print('  ' + line[:150])
    print('  …')

    if a.dry_run:
        print('\n⏸️  --dry-run：沒有寫入')
        conn.rollback()
        return 0

    cur.execute(
        'update benefits set description = %s, notes = %s, '
        'source_url = %s, source_excerpt = %s, source_tier = %s, '
        'last_verified_date = current_date where id = %s',
        (NEW_DESCRIPTION, NEW_NOTES, NEW_URL, NEW_EXCERPT, NEW_TIER, BENEFIT_ID))
    if cur.rowcount != 1:
        print(f'🔴 rowcount={cur.rowcount}，預期 1 —— rollback')
        conn.rollback()
        return 1
    conn.commit()

    # 🔴 驗終點：重開連線讀回來（同一個 transaction 看得到自己的寫入，不算驗證）
    conn.close()
    conn2 = psycopg2.connect(dsn)
    c2 = conn2.cursor()
    c2.execute('select description, source_url, source_tier, last_verified_date '
               'from benefits where id = %s', (BENEFIT_ID,))
    d2, u2, t2, lv = c2.fetchone()
    conn2.close()

    ok = (d2 == NEW_DESCRIPTION and u2 == NEW_URL and t2 == NEW_TIER)
    print(f'\n{"✅" if ok else "🔴"} 重開連線讀回：{len(d2)} 字 / tier={t2} / '
          f'last_verified={lv}')
    print(f'   url = {u2}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
