#!/usr/bin/env python3
"""驗證 `fix_hccg_fullwidth_urls.py`（新竹市全形逗號網址修正）。

🔴 為什麼需要這支：那支腳本會**改動正式資料**（source_url／description／
   amount_*）。它的三個判準都是被實際踩雷逼出來的，如果哪天有人「簡化」
   掉其中一個，症狀會非常溫和 —— 資料還在、欄位還有值，只是**變差了**。

五個方向：
  ① 全形 → 半形只換網址該換的字元
  ② `detail_block` 兩種頁面版本都要抓得到（完整版／精簡版）
  ③ 🔴 反向：抓不到框必須回 None，不可退回用 regex 撈句子
  ④ 🔴 `usable_amount`：區間一律不填欄位（Lonck 選 A）
  ⑤ 🔴 描述不可比舊的短（重抓的目的是補完整）
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 🔴 先清掉 stale bytecode —— 否則植入後「還原」是假的
#    （2026-09-30 在 verify_welfare_url_check.py 踩過：diff 說一致但測試紅）
for pyc in (HERE / "__pycache__").glob("fix_hccg_fullwidth_urls.*.pyc"):
    pyc.unlink()
shutil.rmtree(HERE / "__pycache__", ignore_errors=True)

sys.path.insert(0, str(HERE))
import fix_hccg_fullwidth_urls as M  # noqa: E402

ok = fail = 0


def ck(label, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✅  {label}")
    else:
        fail += 1
        print(f"  ❌  {label}" + (f"  ← {extra}" if extra else ""))


def eq(label, got, want):
    ck(label, got == want, f"got={got!r} want={want!r}")


# ── ① 全形轉半形 ────────────────────────────────────────────────
print("① 網址全形 → 半形")
U_BAD = ("https://society.hccg.gov.tw/ch/home.jsp?id=139&parentpath=0，3，30"
         "&mcustomize=onemessages_view.jsp&toolsflag=Y"
         "&dataserno=201902210001&t=SocietyOnes&mserno=201603090042")
U_OK = U_BAD.replace("，", ",")
eq("全形逗號被換成半形", M.fix_url(U_BAD), U_OK)
eq("已經是半形的不動", M.fix_url(U_OK), U_OK)
ck("🔴 轉換後不含任何全形逗號", "，" not in M.fix_url(U_BAD))
# 🔴 反向：不可連中文內容裡的標點一起換（那支函式只給網址用）
ck("🔴 其他全形標點也在表內（；：％＆＝）",
   all(c in M.FULLWIDTH for c in "；：％＆＝"))
eq("全形等號", M.fix_url("a＝b"), "a=b")
eq("全形 &", M.fix_url("a＆b"), "a&b")

# ── ② detail_block 兩種版本 ─────────────────────────────────────
print("\n② 🔴 detail_block：同一網站有兩種頁面版本，都要抓得到")
FULL = """低收入戶及中低收入戶資格-新竹市政府社會處

詳細內容：

補助項目 低收入戶重病住院看護費補助 聯絡電話 (03)5352386分機203 補助標準 本市列冊低收入戶者，每人每日最高補助看護費新台幣2,000元整，同一年度最高補助新台幣180,000元整。 應備文件 1.申請人身分證。

相關附件：

新竹市低收入戶重病住院看護費用補助辦法

瀏覽人次：18151 人
"""
SLIM = """低收入戶及中低收入戶資格-新竹市政府社會處

詳細內容：

補助項目 低收入戶喪葬費補助 聯絡電話 (03)5352386分機205 補助對象 本市列冊低收入戶。 補助金額 1. 每案最高補助金額以新台幣三萬元為限。 應備文件 1. 申請表。

 地址：30041新竹市中央路241號(4、5及8樓) 電話：03-5352386 本網站支援IE 9以上 您是本站第： 1665989訪客
"""
b_full = M.detail_block(FULL)
b_slim = M.detail_block(SLIM)
ck("完整版（有「相關附件：」）抓得到", b_full is not None)
ck("🔴 精簡版（無「相關附件：」「瀏覽人次」）也抓得到 —— 748/751 實際版本",
   b_slim is not None)
ck("完整版含補助標準原文", b_full is not None and "每人每日最高補助看護費" in b_full)
ck("精簡版含補助金額原文", b_slim is not None and "每案最高補助金額" in b_slim)
ck("🔴 完整版不含頁尾（相關附件之後的東西）",
   b_full is not None and "瀏覽人次" not in b_full and "補助辦法" not in b_full)
ck("🔴 精簡版不含頁尾地址", b_slim is not None and "30041" not in b_slim)
ck("🔴 精簡版不含「您是本站第」", b_slim is not None and "您是本站第" not in b_slim)
ck("🔴 精簡版不含「本網站支援」", b_slim is not None and "本網站支援" not in b_slim)

# ── ③ 反向：抓不到必須回 None ───────────────────────────────────
print("\n③ 🔴 反向：抓不到框回 None（不可退回用 regex 撈句子）")
ck("完全沒有「詳細內容：」→ None",
   M.detail_block("這是一個普通頁面 申請資格 本市市民 應備文件 身分證") is None)
ck("有標記但內容太短（<60 字）→ None",
   M.detail_block("詳細內容：\n\n很短\n\n相關附件：") is None)
ck("空字串 → None", M.detail_block("") is None)
# 🔴 這條是整支腳本的核心防線：第一版用通用 regex 撈句子，
#    把 750 的描述從「每日 2,000／年上限 180,000」弄成
#    「應備文件 1.申請人身分證」＋「🔴 金額未列出」。
ck("🔴 detail_block 不可含通用資格句 regex（那正是把資料弄差的做法）",
   "應符合" not in (M.detail_block.__doc__ or "")
   or "不可退回" in (M.detail_block.__doc__ or ""))

# ── ④ usable_amount（Lonck 2026-09-30 選 A）────────────────────
print("\n④ 🔴 usable_amount：區間一律不填欄位")
eq("單一金額 → 填", M.usable_amount(30000, 30000, "one_time")[:3],
   (30000, 30000, "one_time"))
ck("單一金額時 reason 為空", M.usable_amount(30000, 30000, "one_time")[3] == "")
a = M.usable_amount(3008, 11850, "monthly")
eq("🔴 748 的 3,008~11,850 不可填入欄位", a[:3], (None, None, None))
ck("🔴 但要講出為什麼", "不同款別" in a[3] or "計算主體" in a[3], a[3])
ck("🔴 reason 要帶原始數字（讓人能自己判斷）",
   "3,008" in a[3] and "11,850" in a[3], a[3])
b = M.usable_amount(None, None, None)
eq("抽不到 → 不填", b[:3], (None, None, None))
ck("抽不到時也要有理由", bool(b[3]))
# 🔴 反向：不可改用「倍數門檻」——那擋的是「數字差很多」不是「主體不同」
c = M.usable_amount(2000, 2400, "monthly")   # 只差 1.2 倍，但仍是區間
eq("🔴 只差 1.2 倍的區間照樣不填（判準不是倍數）", c[:3], (None, None, None))
d = M.usable_amount(1, 1, "one_time")
eq("邊界：min==max==1 要填", d[:3], (1, 1, "one_time"))

# ── ⑤ build_desc ───────────────────────────────────────────────
print("\n⑤ build_desc：原文為主體，且不可把自己的限制說成官方沒寫")
BODY = "補助對象 本市列冊低收入戶。 補助金額 每案最高新台幣三萬元。"
d1 = M.build_desc("低收入戶喪葬補助", U_OK, BODY, 30000, 30000, "one_time", "")
ck("有金額時寫出金額", "30,000 元" in d1)
ck("🔴 原文完整保留", BODY in d1)
ck("來源網址在描述裡", U_OK in d1)
ck("🔴 有金額時不可出現「未填入欄位」", "未填入欄位" not in d1)

REASON = "原文出現多個金額（3,008~11,850），分屬不同款別或計算主體，非連續區間"
d2 = M.build_desc("低收入戶資格", U_OK, BODY, None, None, None, REASON)
ck("🔴 原文仍完整保留（沒金額不代表要少寫內容）", BODY in d2)
ck("🔴 講出不填的理由", REASON in d2)
ck("🔴 不可寫「金額未在官方頁面列出」——那是把自己的限制說成對方的缺漏",
   "未在官方頁面列出" not in d2)
ck("🔴 引導使用者去看原文級距", "詳細級距" in d2 or "見上方原文" in d2)

# ── ⑥ 端到端：三個判準串起來 ────────────────────────────────────
print("\n⑥ 🔴 端到端：抓頁 → 取框 → 判金額 → 組描述")
for label, page, want_amount in (
        ("完整版・單一金額", SLIM, True),
        ("完整版・多單位（每日2,000／年180,000）", FULL, False)):
    body = M.detail_block(page)
    ck(f"{label}：取得區塊", body is not None)
    if body is None:
        continue
    from extract_amounts_from_desc import extract_amounts
    rmin, rmax, runit, _ = extract_amounts(body)
    amin, _, _, reason = M.usable_amount(rmin, rmax, runit)
    ck(f"{label}：金額{'有' if want_amount else '不'}填入欄位",
       (amin is not None) == want_amount, f"amin={amin} reason={reason}")
    desc = M.build_desc("測試", U_OK, body, amin, rmax if amin else None,
                        runit if amin else None, reason)
    ck(f"{label}：描述含原文", body in desc)
    # 🔴 不管有沒有金額，原文都要在 —— 這是「不可變短」的根本保障
    ck(f"{label}：描述比原文長（有加上標題與來源）", len(desc) > len(body))

# ── ⑦ 🔴 不可變短的守門必須存在於程式碼裡 ──────────────────────
print("\n⑦ 🔴 「新描述不可比舊的短」這道守門必須在")
src = (HERE / "fix_hccg_fullwidth_urls.py").read_text(encoding="utf-8")
ck("🔴 有長度比較的守門", re.search(r"len\(new_desc\)\s*<\s*len\(desc", src)
   is not None)
ck("🔴 守門會 continue（整筆不動），不是只印警告",
   re.search(r"len\(new_desc\)\s*<\s*len\(desc[^)]*\)[\s\S]{0,260}?continue",
             src) is not None)
ck("🔴 detail_block 回 None 時整筆不動",
   re.search(r"body\s+is\s+None[\s\S]{0,200}?continue", src) is not None)
# 🔴 抽不到金額時**不可覆蓋舊金額** ——「我沒查到」與「這補助沒金額」
#    在資料庫裡長得一樣。
#
# ⚠️ 這條斷言前兩版都是假的，而且**兩次都是植入後仍全綠才發現**：
#    ① `(?!amount)` 位置不對，整條失效
#    ② 改成抓 SQL 區塊，但 `if amin is None:` 在檔案裡**出現兩次**
#       （`usable_amount` 裡也有一行），regex 匹配到較早的那個位置
#       ⇒ 捕獲的根本不是 UPDATE 語句
#
# 🔴 改用 AST 定位：找 `main()` 裡那個 `if amin is None:`，
#    取它主體內所有字串常數。文字比對永遠會撞到同名的東西，
#    而撞到時的症狀是**斷言安靜地量錯目標**。
import ast  # noqa: E402

_tree = ast.parse(src)
_main = next((n for n in ast.walk(_tree)
              if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
ck("🔴 找得到 main()", _main is not None)
_sql_none = None
if _main is not None:
    for node in ast.walk(_main):
        if (isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "amin"
                and isinstance(node.test.ops[0], ast.Is)):
            # 🔴 只取 `body`，不可用 ast.walk(node) ——
            #    `ast.If` 節點**包含 orelse**，walk 會把 else 分支
            #    （那裡本來就該有 amount_）一起吃進來 ⇒ 斷言永遠失敗。
            _sql_none = "".join(
                v.value for stmt in node.body for v in ast.walk(stmt)
                if isinstance(v, ast.Constant) and isinstance(v.value, str))
            break
ck("🔴 找得到 main() 裡「抽不到金額」那個分支", _sql_none is not None)
ck("🔴 該分支的 UPDATE 有動 description", 
   _sql_none is not None and "description" in _sql_none)
ck("🔴 該分支的 UPDATE 不可碰 amount_（否則會清掉舊值）",
   _sql_none is not None and "amount_" not in _sql_none,
   (_sql_none or "")[:160])
ck("🔴 寫入前一定先備份整列（row_to_json）", "row_to_json" in src)
ck("🔴 預設是 dry-run（--apply 才寫）", '"--apply"' in src
   and 'action="store_true"' in src)
ck("🔴 備份筆數對不上要中止", re.search(r"!=\s*len\(TARGET_IDS\)[\s\S]{0,140}?"
                                r"return 1", src) is not None)

print(f"\n{'='*66}\n{ok}/{ok + fail} 通過")
sys.exit(1 if fail else 0)
