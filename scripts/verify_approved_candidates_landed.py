#!/usr/bin/env python3
"""verify_approved_candidates_landed.py —— 核准的新福利候選一定要真的進 benefits。

🔴 2026-10-19 建。踩雷：267–275 九筆 10-19 10:39 核准（approved_at 有值），
   但 `welfare_change_review.py` 只提示跑 `import_county_opendata.py` ——
   那支只匯開放資料，來源 B（搜尋）的候選不在裡面 ⇒ **核准了卻永遠不進庫，零訊號**。
   我當時查「待審 0 筆」就以為做完了 —— 那只證明「審完了」，不證明「進庫了」。

判準（直接查資料庫，不依賴任何匯入程式的回報）：
  approved_at IS NOT NULL AND rejected_at IS NULL 的 new_candidate，
  benefit_id 必須非 NULL 且指向一筆存在的 benefits。

negative control：在交易裡植入一筆「核准但 benefit_id NULL」，必須被抓到，然後 ROLLBACK。
"""
from __future__ import annotations
import sys
import psycopg2

SQL = """SELECT l.id, l.new_value FROM benefit_change_log l
          LEFT JOIN benefits b ON b.id = l.benefit_id
         WHERE l.change_type = 'new_candidate'
           AND l.approved_at IS NOT NULL AND l.rejected_at IS NULL
           AND b.id IS NULL"""


def main() -> int:
    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    # negative control（交易內，最後 rollback，不留痕跡）
    cur.execute("""INSERT INTO benefit_change_log (change_type, field_name, new_value, source_url,
                       source_excerpt, detected_at, approved_at, reviewed_by)
                   VALUES ('new_candidate','name','測試縣｜_tmp-negative-control','x','x',
                           now(), now(), '_tmp') RETURNING id""")
    planted = cur.fetchone()[0]
    cur.execute(SQL)
    caught = planted in [r[0] for r in cur.fetchall()]
    conn.rollback()
    cur.execute("SELECT count(*) FROM benefit_change_log WHERE id=%s", (planted,))
    if cur.fetchone()[0]:
        print("🔴 negative control 沒清乾淨")
        return 1
    if not caught:
        print("🔴 negative control 失敗：植入「核准但未進庫」沒被抓到 —— 這支沒有鑑別力")
        return 1

    cur.execute(SQL)
    bad = cur.fetchall()
    if bad:
        print(f"🔴 {len(bad)} 筆新福利已核准但沒進 benefits：")
        for i, v in bad[:10]:
            print(f"   · change_log {i}：{v}")
        print("   → 來源 B：先把欄位寫進 scripts/import_approved_candidates.py 的 ITEMS，再 --apply")
        return 1
    cur.execute("""SELECT count(*) FROM benefit_change_log WHERE change_type='new_candidate'
                    AND approved_at IS NOT NULL AND rejected_at IS NULL""")
    print(f"✅ 核准的 {cur.fetchone()[0]} 筆新福利都已進庫（negative control 通過）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
