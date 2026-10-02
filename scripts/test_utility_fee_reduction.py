#!/usr/bin/env python3
"""驗 id 45「水電費減免」不可退回錯誤版本（W-007 ③，2026-10-02）。

🔴 這支在防什麼

id 45 原本的描述有**四個查證後不成立的主張**，而它們看起來完全合理：

  · 「每月用電 110 度以下免收基本電費」—— 110 度是 101 年以前的級距，
    真正的出處是 97 年台電「打算成立社會關懷基金」的構想（2008 自由時報）
  · 法源「對低收入戶用電優待辦法」—— 全國法規資料庫全文檢索**查無此法**
  · 「台水減免基本水費」—— 台水只有漏水減免，營業章程無低收入戶減免
  · 「全國性」—— 《社會救助法》§16 七款沒有水電費，且是「得」不是「應」

⚠️ 為什麼需要回歸測試而不只是改掉它：
   ① `npm run seed` 會從 seed-data 檔重灌 ⇒ **DB 與 seed 檔必須同步**，
      只改 DB 的話下次 seed 就退回去，而且不會有任何訊號
   ② 「110 度」這種數字在未來的重新查證中**很容易又被抓回來**
      （getgrant 等媒體站仍然這樣寫，而它們 SEO 排名比法規資料庫高）

🔴 判準（不是「描述要長」，是「不可出現已證偽的主張」）

跑法：python3 scripts/test_utility_fee_reduction.py
"""
import os
import pathlib
import sys

import psycopg2

BENEFIT_ID = 45
SEED = pathlib.Path(__file__).resolve().parents[1] / \
    'backend/src/db/seed-data/20-utility-fee-reduction.ts'

PASS = FAIL = 0


def ck(name: str, ok: bool, hint: str = '') -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f'  ✅ {name}')
    else:
        FAIL += 1
        print(f'  🔴 FAIL {name}' + (f'  {hint}' if hint else ''))


# 🔴 已證偽的主張 —— 這些字串不可出現在描述的「斷言」位置。
#    ⚠️ 判準要小心：新描述裡**刻意**提到「110 度」是為了說明它是過時的，
#       所以不能單純檢查字串不存在 —— 要檢查它有沒有被標為過時。
DISPROVEN_CLAIMS = [
    ('對低收入戶用電優待辦法', '查無此法（全國法規資料庫全文檢索）'),
]


def main() -> int:
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        print('⏭️  沒有 DATABASE_URL —— 跳過 DB 檢查')
        print('🔴 這不算通過（需要 set -a && . backend/.env && set +a）')
        return 2

    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute('select name, description, notes, source_url, source_tier '
                'from benefits where id = %s', (BENEFIT_ID,))
    row = cur.fetchone()
    conn.close()
    if not row:
        print(f'🔴 找不到 id={BENEFIT_ID}')
        return 1
    name, desc, notes, url, tier = row

    print('【①】DB：不可出現已證偽的法源')
    for claim, why in DISPROVEN_CLAIMS:
        ck(f'描述不引用「{claim}」', claim not in desc, why)

    print('\n【②】DB：「110 度」只能以「過時」的身分出現')
    # 🔴 不是「不准提」—— 新描述刻意提它是為了破除誤解。
    #    判準是：提到它的同一段必須同時說明它過時／非現行。
    has_110 = '110 度' in desc or '110度' in desc
    if has_110:
        ok = any(k in desc for k in ('以前', '過時', '並非現行', '已將', '提高'))
        ck('提到 110 度時有標明它非現行', ok,
           '只寫「110 度免收基本電費」就是退回舊版')
        ck('🔴 不可寫成肯定句「可申請…110 度以下免收」',
           '可向台電申請每月用電 110 度以下免收' not in desc)
    else:
        ck('沒提 110 度（也可接受）', True)

    print('\n【③】DB：核心結論在（中央無全國性規定）')
    ck('說明中央沒有全國性規定',
       '中央沒有' in desc and '全國性' in desc,
       '這是整筆的結論，沒有它就等於沒改')
    ck('引用《社會救助法》第 16 條', '社會救助法' in desc and '16' in desc)
    ck('說明條文是「得」不是「應」', '得' in desc and '可自行決定' in desc)
    ck('給出可行做法（公所／社會局／1957）',
       any(k in desc for k in ('公所', '社會局', '1957')),
       '只說「沒有」不給路，對使用者等於沒用')

    print('\n【④】DB：來源與 tier')
    ck('source_url 指向法規資料庫', 'law.moj.gov.tw' in url, url)
    ck('🔴 tier 不可標 official', tier != 'official',
       f'實際 {tier} —— 沒有官方頁面支持「全國低收入戶水電費減免」，'
       '標 official 會讓未來的人不再查證')
    ck('notes 說明原法源查無此法',
       '查無此法' in (notes or ''), (notes or '')[:80])

    print('\n【⑤】🔴 seed 檔必須與 DB 同步（否則 npm run seed 會退回）')
    if not SEED.exists():
        ck('seed 檔存在', False, str(SEED))
    else:
        ts = SEED.read_text(encoding='utf-8')
        ck('seed 檔含新描述的結論句', '中央沒有「全國性低收入戶水電費減免」' in ts)
        ck('🔴 seed 檔已無舊的肯定句',
           '可向台電申請每月用電 110 度以下免收' not in ts,
           '留著的話下次 seed 就退回舊版，而且完全靜默')
        ck('seed 檔 sourceUrl 已換', 'law.moj.gov.tw' in ts)
        # 🔴 判準不是「不准提」—— notes 裡刻意說明「查無此法」是要保留的。
        #    ⚠️ 這跟【②】的 110 度是同一個形狀，我第一版只在②處理了，
        #       ⑤ 寫成單純的字串不存在 ⇒ 測試自己紅燈（而程式是對的）。
        #    判準：不可出現在**肯定引用**的位置（description 的「依…辦法」句型）。
        ck('seed 檔不把查無的辦法當法源引用',
           '依台灣電力公司「對低收入戶用電優待辦法」' not in ts
           and '依「對低收入戶用電優待辦法」' not in ts,
           'notes 裡說明它查無此法是**要保留的**，不可一併刪掉')
        ck('🔴 seed 檔有保留「查無此法」的說明',
           '查無此法' in ts,
           '刪掉的話，未來重新查證的人會再把 110 度抓回來')
        # 🔴 negative control：22 筆瓦斯費地方明細不該被這次改動波及
        ck('🔴 negative control：22 筆瓦斯仍用共用常數',
           'lastVerifiedDate: LAST_VERIFIED_DATE,' in ts
           and 'GAS_UNCONFIRMED_NOTE' in ts,
           '少了這條，「把整個檔案改爛」也會全綠')

    print('\n【⑥】新描述不可被空殼偵測器判成 empty')
    try:
        import importlib.util
        p = pathlib.Path(__file__).resolve().parent / 'description_substance.py'
        s = importlib.util.spec_from_file_location('ds_t', p)
        ds = importlib.util.module_from_spec(s)
        s.loader.exec_module(ds)
        # 🔴 簽章是 verdict(desc, name) —— 參數順序寫反會得到 'empty'，
        #    而那個結果看起來像「偵測器抓到問題」（我 2026-10-02 真的誤判過一次，
        #    還寫了三段錯誤的根因分析）。
        v, why = ds.verdict(desc, name)
        ck(f'verdict = ok（實際 {v}：{why}）', v == 'ok')
    except Exception as e:  # noqa: BLE001
        ck('載入 description_substance', False, f'{type(e).__name__}: {e}')

    print(f'\n{PASS}/{PASS + FAIL} 通過')
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
