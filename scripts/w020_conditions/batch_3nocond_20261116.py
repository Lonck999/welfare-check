"""C-6b（2026-11-16）：320／324／363 三筆無條件項目補正。

背景：
- 320 TPASS：eligibility_conditions = NULL
- 324 電動機車中央基準：eligibility_conditions = {}
- 363 雲林電動自行車：只有 counties

依原文編條件：
- 320：全國、一般成人電子票證可設定（敬老卡/愛心卡不可）→ openToAll（無限制）
- 324：全國、無特定身分限制、可適用於外籍人士 → openToAll
- 363：雲林縣、設籍限制（3 年內未受補助）→ 加設籍條件
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL not set')

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    updates = [
        # 320 TPASS：全國通用、一般成人電子票證可設定
        # 敬老卡/愛心卡不可設定 → 寫進 uncheckedConditions
        (320, {
            'openToAll': True,
            'uncheckedConditions': [
                '須持一般成人電子票證（悠遊卡、一卡通、愛金卡等），敬老卡／愛心卡等優惠票種不可設定'
            ],
            '_source': 'C-6b 2026-11-16 依 gov.tw 115 年版；見 batch_3nocond_20261116.py'
        }),
        # 324 電動機車中央基準：全國、無特定身分限制
        (324, {
            'openToAll': True,
            'uncheckedConditions': [
                '須新購電動機車（汰舊換新另有加碼）'
            ],
            '_source': 'C-6b 2026-11-16 依經濟部電動機車產業網 115/10/07；見 batch_3nocond_20261116.py'
        }),
        # 363 雲林：設籍雲林 + 3 年內未受縣府此項補助
        # 🔴 但這筆名稱是「電動自行車」，原文是「電動機車」→ 要改名或停用
        (363, {
            'counties': ['雲林縣'],
            'uncheckedConditions': [
                '申請年度前 3 年未受雲林縣此項補助',
                '中低收入戶換購電動機車補助最高 2.5 萬元'
            ],
            '_source': 'C-6b 2026-11-16 依雲林縣 115 年公告；見 batch_3nocond_20261116.py'
        }),
    ]

    for benefit_id, ec in updates:
        # 先讀現有條件
        cur.execute('SELECT eligibility_conditions, name FROM benefits WHERE id = %s', (benefit_id,))
        row = cur.fetchone()
        if not row:
            print(f'❌ id {benefit_id} not found')
            continue
        old_ec, name = row
        old_ec = old_ec or {}
        
        # 合併（保留既有的，新的覆蓋）
        new_ec = {**old_ec, **ec}
        
        cur.execute(
            'UPDATE benefits SET eligibility_conditions = %s, updated_at = NOW() WHERE id = %s',
            (json.dumps(new_ec, ensure_ascii=False), benefit_id)
        )
        print(f'✅ {benefit_id} {name}: {json.dumps(new_ec, ensure_ascii=False)[:100]}...')

    conn.commit()
    cur.close()
    conn.close()
    print('\nDone. 3 筆已更新。')

if __name__ == '__main__':
    main()
