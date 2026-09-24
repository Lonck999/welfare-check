#!/usr/bin/env python3
"""驗證 benefits schema 擴充（P1~P4）真的能用。

🔴 判準不是「欄位存在」，是**約束真的會擋、合法值真的放行**。
   只驗欄位存在的話，CHECK 打錯字也會全綠。

跑法：python3 scripts/verify_benefits_schema.py
"""
from __future__ import annotations

import sys

import psycopg2
from psycopg2 import errors

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    mark = "  ✅" if ok else "  🔴"
    print(f"{mark} {name}" + (f"　{detail}" if detail else ""))


def main() -> int:
    conn = psycopg2.connect(dbname="welfare_check")

    print("── ① 新欄位存在且型別正確 ──")
    want = {
        "amount_min": "integer", "amount_max": "integer",
        "amount_unit": "text", "amount_note": "text",
        "deadline_type": "text", "deadline_date": "date",
        "deadline_rule": "jsonb", "effort_level": "smallint",
        "quota_limited": "boolean",
    }
    cur = conn.cursor()
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns
                    WHERE table_name = 'benefits'""")
    have = dict(cur.fetchall())
    for col, typ in want.items():
        got = have.get(col)
        check(f"benefits.{col} 是 {typ}", got == typ, f"實際 {got}")

    print("\n── ② benefit_applicants 表（P4）──")
    cur.execute("""SELECT count(*) FROM information_schema.tables
                    WHERE table_name = 'benefit_applicants'""")
    check("benefit_applicants 表存在", cur.fetchone()[0] == 1)
    cur.execute("""SELECT count(*) FROM information_schema.columns
                    WHERE table_name = 'benefit_applicants'
                      AND column_name IN ('benefit_id','role','relation','note')""")
    check("四個必要欄位都在", cur.fetchone()[0] == 4)

    print("\n── ③ 🔴 CHECK 約束真的會擋（植入非法值）──")
    bad = [
        ("非法 amount_unit",
         "UPDATE benefits SET amount_unit='每個月' WHERE id=(SELECT min(id) FROM benefits)"),
        ("amount_min > amount_max",
         "UPDATE benefits SET amount_min=9000, amount_max=100 "
         "WHERE id=(SELECT min(id) FROM benefits)"),
        ("非法 deadline_type",
         "UPDATE benefits SET deadline_type='常態' WHERE id=(SELECT min(id) FROM benefits)"),
        ("always 卻塞 deadline_date",
         "UPDATE benefits SET deadline_type='always', deadline_date='2026-12-31' "
         "WHERE id=(SELECT min(id) FROM benefits)"),
        ("effort_level=0",
         "UPDATE benefits SET effort_level=0 WHERE id=(SELECT min(id) FROM benefits)"),
        ("非法 applicant role",
         "INSERT INTO benefit_applicants(benefit_id, role) "
         "SELECT min(id), '朋友' FROM benefits"),
        ("非法 relation",
         "INSERT INTO benefit_applicants(benefit_id, role, relation) "
         "SELECT min(id), 'family', '鄰居' FROM benefits"),
    ]
    for name, sql in bad:
        c = conn.cursor()
        try:
            c.execute(sql)
            conn.rollback()
            check(f"擋下：{name}", False, "🔴 沒擋住！")
        except errors.CheckViolation:
            conn.rollback()
            check(f"擋下：{name}", True)
        except Exception as e:                       # noqa: BLE001
            conn.rollback()
            check(f"擋下：{name}", False, f"其他錯誤 {type(e).__name__}")

    print("\n── ④ 🔴 合法值必須放行（negative control）──")
    # 沒有這節的話，「全部都擋」也會讓上一節全綠
    good = [
        ("fixed + deadline_date",
         "UPDATE benefits SET deadline_type='fixed', deadline_date='2026-12-31' "
         "WHERE id=(SELECT min(id) FROM benefits)"),
        ("event + deadline_rule",
         "UPDATE benefits SET deadline_type='event', deadline_date=NULL, "
         """deadline_rule='{"trigger":"childbirth","within_months":6}' """
         "WHERE id=(SELECT min(id) FROM benefits)"),
        ("合法 applicant",
         "INSERT INTO benefit_applicants(benefit_id, role, relation) "
         "SELECT min(id), 'family', 'child' FROM benefits"),
    ]
    for name, sql in good:
        c = conn.cursor()
        try:
            c.execute(sql)
            conn.rollback()
            check(f"放行：{name}", True)
        except Exception as e:                       # noqa: BLE001
            conn.rollback()
            check(f"放行：{name}", False, f"🔴 誤擋 {e}")

    print("\n── ⑤ deadline_type 回填覆蓋率 ──")
    cur.execute("SELECT count(*) FROM benefits WHERE deadline_type IS NULL")
    check("沒有任何 benefits 缺 deadline_type", cur.fetchone()[0] == 0)
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE deadline_type = 'unknown'
                      AND coalesce(application_period, '') <> ''""")
    unk = cur.fetchone()[0]
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE coalesce(application_period, '') <> ''""")
    has_period = cur.fetchone()[0]
    # 🔴 只算「有期限文字卻解析不出」的 —— 來源根本沒有期限欄位的
    #    不算解析失敗，否則這條斷言會在懲罰「誠實留空」。
    check("有期限文字的，解析失敗不超過 10%",
          unk / max(has_period, 1) <= 0.10, f"{unk}/{has_period}")
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE deadline_type = 'unknown'
                      AND coalesce(application_period, '') = ''""")
    no_src = cur.fetchone()[0]
    print(f"     （另有 {no_src} 筆是來源本身沒有期限欄位，留 unknown 是正確的）")

    # 🔴 事件觸發型必須有 trigger —— 沒有的話「錯過就沒了」的提醒發不出來
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE deadline_type='event'
                      AND (deadline_rule IS NULL
                           OR deadline_rule->>'trigger' IS NULL)""")
    no_trig = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM benefits WHERE deadline_type='event'")
    ev = cur.fetchone()[0]
    check("event 型八成以上解得出 trigger",
          ev > 0 and no_trig / ev <= 0.20, f"缺 trigger {no_trig}/{ev}")

    print("\n── ⑥ 既有資料未受損 ──")
    # 🔴 不可寫死筆數 —— 匯入新來源後必然增加。
    #    要驗的是「原有的沒被刪」，不是「總數沒變」。
    cur.execute("SELECT count(*) FROM benefits")
    total_now = cur.fetchone()[0]
    cur.execute("""SELECT count(*) FROM information_schema.tables
                    WHERE table_name = 'benefits_bk_before_opendata'""")
    if cur.fetchone()[0]:
        cur.execute("""SELECT count(*) FROM benefits_bk_before_opendata b
                        WHERE NOT EXISTS (SELECT 1 FROM benefits n
                                           WHERE n.id = b.id)""")
        lost = cur.fetchone()[0]
        check("匯入前的資料一筆都沒掉", lost == 0, f"掉了 {lost} 筆")
    check("benefits 筆數只增不減", total_now >= 499, f"現有 {total_now}")
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE description IS NOT NULL AND length(description) > 50""")
    check("有實質內容的筆數未減少", cur.fetchone()[0] >= 157)

    print("\n── ⑦ 🔴 開放資料匯入品質 ──")
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE agency LIKE '%%社會局' OR agency LIKE '%%社會處'""")
    imported = cur.fetchone()[0]
    if imported:
        # 🔴 同縣市同名不可重複 —— 重複執行匯入就會產生
        cur.execute("""SELECT count(*) FROM (
                         SELECT county, name FROM benefits
                          GROUP BY 1,2 HAVING count(*) > 1) x""")
        dup = cur.fetchone()[0]
        check("沒有同縣市同名的重複補助", dup == 0, f"重複 {dup} 組")

        # 🔴 source_url 必須是真的網址，不可是佔位字串
        cur.execute("""SELECT count(*) FROM benefits
                        WHERE source_url IS NULL OR source_url !~ '^https?://'""")
        bad_url = cur.fetchone()[0]
        check("每筆都有合法 source_url", bad_url == 0, f"{bad_url} 筆沒有")

        # 🔴 資格條件的鍵名必須與既有 491 筆一致，否則比對程式查不到
        #    ⚠️ 既有 64 筆本來就缺（全國性補助沒有縣市限制）——
        #    這裡驗的是「匯入的不可缺」，不是「全庫都要有」。
        cur.execute("""SELECT count(*) FROM benefits
                        WHERE eligibility_conditions IS NOT NULL
                          AND NOT jsonb_exists(eligibility_conditions,
                                               'counties')
                          AND (agency LIKE '%%社會局' OR agency LIKE '%%社會處')
                          AND created_at::date >= CURRENT_DATE - 1""")
        no_cty = cur.fetchone()[0]
        check("匯入的資料都有 counties 鍵", no_cty == 0, f"{no_cty} 筆缺")

        # 🔴 金額欄位不可被填成 0（轉換失敗時的預設值會變成
        #    「收入上限 0 元」＝沒人符合，而且完全不報錯）
        cur.execute("""SELECT count(*) FROM benefits
                        WHERE (eligibility_conditions->>'incomeMonthlyMax')::int = 0
                           OR (eligibility_conditions->>'movableAssetsMax')::int = 0""")
        zero = cur.fetchone()[0]
        check("沒有金額條件被填成 0", zero == 0, f"{zero} 筆是 0")

        # 🔴 county 必須是真的縣市名（2026-09-25 踩到）：
        #    匯入時誤用 SOURCES 的 key，29 筆變成「臺中市-112090」——
        #    那個縣市不存在，臺中使用者永遠查不到，且完全不報錯。
        cur.execute("""SELECT count(*) FROM benefits
                        WHERE county IS NOT NULL AND county <> ''
                          AND county NOT IN (
                            '臺北市','新北市','桃園市','臺中市','臺南市','高雄市',
                            '基隆市','新竹市','新竹縣','苗栗縣','彰化縣','南投縣',
                            '雲林縣','嘉義市','嘉義縣','屏東縣','宜蘭縣','花蓮縣',
                            '臺東縣','澎湖縣','金門縣','連江縣','全國')""")
        bad_cty = cur.fetchone()[0]
        check("county 都是合法縣市名", bad_cty == 0, f"{bad_cty} 筆不合法")

        # 🔴 benefits.county 必須與 eligibility_conditions.counties 一致 ——
        #    兩邊分岔會讓「縣市篩選」與「資格比對」給出不同答案
        cur.execute("""SELECT count(*) FROM benefits
                        WHERE county IS NOT NULL AND county <> ''
                          AND jsonb_exists(eligibility_conditions, 'counties')
                          AND NOT (eligibility_conditions->'counties')
                                   @> to_jsonb(county)""")
        mismatch = cur.fetchone()[0]
        check("county 與 counties 一致", mismatch == 0, f"{mismatch} 筆不一致")

    print("\n" + "=" * 46)
    print(f"通過 {len(PASS)}　失敗 {len(FAIL)}")
    conn.rollback()
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
