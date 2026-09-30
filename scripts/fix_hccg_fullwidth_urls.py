#!/usr/bin/env python3
"""修正新竹市 5 筆的全形逗號網址，並用**已知正確的網址**重抓內容。

🔴 Lonck 2026-09-30 決定：方案 A（改半形）＋ 順便重抓內容。

為什麼不走 `refetch_empty_shells.py`：
   那支是「**用搜尋去找頁面**」—— 適用於不知道正確網址的空殼。
   這 5 筆我們**已經知道正確網址**（就是自己存的那個，只是逗號存成全形），
   再去搜尋等於把一個已知答案丟掉、換成一個要猜的過程，
   而且可能搜到別的頁面。⇒ 直接打那個網址。

🔴 W-007 的真相（不要再忘）：
   2026-09-29 判定這 5 筆是「SPA 外殼抓不到」，依據是三個頁面
   **HTML bytes 幾乎一樣大**（246,710／246,139／首頁 255,051）。
   但政府網站的選單與頁尾佔掉絕大多數 bytes，**正文只有幾百字、
   差異完全被淹沒** —— 那個指標根本分不出「同一頁」與「不同頁」。
   實際抽取正文後：777 字，金額、應備文件全在。
   ⇒ 錯的不是推論過程，是**指標選擇**。

寫入原則：
   · 🔴 一律先 `--dry-run`（預設），`--apply` 才寫
   · 🔴 寫之前先備份到 `/tmp/wc_backup/`，且備份**整列**不是只備要改的欄位
   · 抓不到 → 那一筆**整筆不動**（網址也不改），不寫入任何東西
   · 描述只取原文，不生成內容
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent))
from extract_amounts_from_desc import extract_amounts  # noqa: E402
from fetch_local_benefit import extract, strip_noise  # noqa: E402

SP = re.compile(r"\s+")

# 🔴 只處理這 5 筆。寫死 id 是刻意的 ——
#    「全形逗號」這個條件將來可能撈到別的縣市，而那些沒有經過實測。
TARGET_IDS = (748, 749, 750, 751, 752)

# 🔴 全形 → 半形。只換**網址裡**的，不動描述文字
#    （描述裡的全形逗號是正常中文標點）。
FULLWIDTH = {"，": ",", "；": ";", "：": ":", "％": "%", "＆": "&", "＝": "="}


def fix_url(url: str) -> str:
    out = url
    for a, b in FULLWIDTH.items():
        out = out.replace(a, b)
    return out


def detail_block(txt: str) -> str | None:
    """取出頁面自己標好的「詳細內容」區塊。

    🔴 2026-09-30 第一版用通用的資格句 regex（`應符合|申請資格|應備…`）
       去撈句子，結果**把好資料切碎了**：
         · 750 看護費：舊描述完整寫著「每日最高 2,000、年度上限 180,000」，
           我產出的新描述只剩「應備文件 1.申請人身分證」＋「🔴 金額未列出」
           —— **頁面明明寫了，而新版本比舊版本更沒用**
         · 752 醫療：舊的有「出院或就醫 3 個月內提出」「補助健保部分負擔」，
           新的只剩「應備文件 1. 醫療費用申請書」

    ⚠️ 根因：我預設「網頁是雜亂的，要靠 regex 淘金」——
       但這個站**自己就把內容框好了**（`詳細內容：` … `相關附件：`）。
       拿通用工具去處理一個結構良好的來源，等於把結構丟掉。

    🔴 抓不到框就回 None ⇒ 那一筆不動，**不可退回用 regex 撈**
       （退回去正是上面那個把資料弄差的行為）。

    🔴 收尾錨點必須有多個（2026-09-30 第二版踩到）：
       **同一個網站、同一支抽取器，回來的版本不只一種。**
       748／751 這次回的是精簡版 —— 沒有「相關附件：」也沒有「瀏覽人次」，
       正文後面直接接頁尾地址。單一錨點 ⇒ 那兩筆被判「找不到區塊」，
       而內容其實完整在那裡。
       ⚠️ 症狀很溫和（只是少處理兩筆），所以**不會有人覺得可疑** ——
       它看起來就像「這兩頁比較特別」。
    """
    m = re.search(r"詳細內容：\s*(.+?)\s*(?:相關附件：|瀏覽人次|\(PDF\)|"
                  r"地址：30041|本網站支援|$)", txt, re.S)
    if not m:
        return None
    body = SP.sub(" ", m.group(1)).strip()
    # 🔴 頁尾可能仍黏在後面（精簡版沒有明確分隔）—— 再剝一次
    body = re.split(r"\s*地址：30041|\s*本網站支援|\s*您是本站第", body)[0].strip()
    return body if len(body) >= 60 else None


def usable_amount(amin, amax, unit):
    """決定金額能不能填進 `amount_min/max`（Lonck 2026-09-30 選 A）。

    🔴 判準：**只有單一金額（min == max）才填**。

    為什麼不是「抽到就填」：這批頁面是**一頁一補助**的格式，
    所以抽出「區間」不代表這個補助有區間，而代表
    **同一頁混進了不同計算主體的數字**。

    實例（748 低收入戶資格及生活補助）：
      · 11,850 ＝ 一款**家庭**生活費（全戶）
      ·  6,825 ＝ 二款家庭生活費／高中職以上學生
      ·  3,008 ＝ 兒童生活補助費（**每個小孩**）
    壓成「每月 3,008~11,850」後，使用者會讀成「我能領這中間的錢」，
    🔴 **但中間的值一個都不存在** —— 一款戶領 11,850、三款戶的小孩領 3,008。

    ⚠️ 這與 750（每日 2,000／年度上限 180,000）是同一種錯，
       只是 750 剛好被既有的「>20 倍」安全網擋下、748 沒有（3.9 倍）
       —— 🔴 **倍數門檻擋的是「數字差很多」，不是「主體不同」**，
       兩者只是偶爾重疊。真正的判準是後者。

    回傳 (amin, amax, unit, reason)；不填時前三項為 None。
    """
    if amin is None:
        return None, None, None, "頁面未列出可填入欄位的單一金額"
    if amin != amax:
        return (None, None, None,
                f"原文出現多個金額（{amin:,}~{amax:,}），"
                f"分屬不同款別或計算主體，非連續區間")
    return amin, amax, unit, ""


def build_desc(name: str, url: str, body: str,
               amin, amax, unit, reason: str) -> str:
    """組描述。🔴 主體直接用頁面的「詳細內容」原文，不改寫、不摘要。"""
    parts = [f"{name}（新竹市）。"]
    if amin:
        rng = (f"{amin:,} 元" if amin == amax else f"{amin:,}~{amax:,} 元")
        u = {"monthly": "每月", "yearly": "每年",
             "one_time": "一次性"}.get(unit or "", "")
        parts.append(f"補助金額 {u} {rng}（官方頁面實抓）。")
    parts.append(body)
    if not amin:
        # 🔴 不可寫「金額未在官方頁面列出」——
        #    750/748 的頁面都寫得清清楚楚，是**我的欄位裝不下**
        #    （多種單位／多個計算主體）。把自己的限制說成對方的缺漏，
        #    使用者無從分辨，而且會以為那個補助真的沒公布金額。
        parts.append(f"⚠️ 金額未填入欄位：{reason}。詳細級距見上方原文。")
    parts.append(f"（來源：{url}）")
    return "　".join(parts)[:1800]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="真的寫入（預設只是 dry-run）")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    # 🔴 備份整列（不是只備要改的欄位）——
    #    出事時要能完整還原，而「我以為只改了這幾欄」本身就是個假設。
    bak = Path("/tmp/wc_backup")
    bak.mkdir(parents=True, exist_ok=True)
    cur.execute(
        "SELECT row_to_json(b)::text FROM benefits b WHERE b.id = ANY(%s)",
        (list(TARGET_IDS),))
    rows_json = [r[0] for r in cur.fetchall()]
    bfile = bak / "hccg5_full_backup.jsonl"
    bfile.write_text("\n".join(rows_json) + "\n", encoding="utf-8")
    print(f"✅ 已備份 {len(rows_json)} 筆整列 → {bfile}\n")
    if len(rows_json) != len(TARGET_IDS):
        print(f"🔴 備份筆數 {len(rows_json)} ≠ 目標 {len(TARGET_IDS)}，中止")
        return 1

    cur.execute(
        "SELECT id, name, source_url, description, amount_min, amount_max,"
        " amount_unit FROM benefits WHERE id = ANY(%s) ORDER BY id",
        (list(TARGET_IDS),))
    rows = cur.fetchall()

    changes: list[dict] = []
    for bid, name, url, desc, amin0, amax0, unit0 in rows:
        new_url = fix_url(url or "")
        print(f"  · [{bid}] {name}")
        if new_url == url:
            print("      ⏭ 網址沒有全形字元 —— 不在這次範圍")
            continue
        print(f"      網址：全形 → 半形")
        try:
            txt = strip_noise(extract(new_url) or "")
        except Exception as e:                       # noqa: BLE001
            print(f"      🔴 抓取失敗 {type(e).__name__}: {str(e)[:60]}"
                  f" ⇒ 🔴 這一筆整筆不動（網址也不改）")
            continue
        if len(txt) < 200:
            print(f"      🔴 只抓到 {len(txt)} 字（疑似沒抓到正文）"
                  f" ⇒ 🔴 這一筆整筆不動")
            continue

        body = detail_block(txt)
        if body is None:
            print("      🔴 找不到「詳細內容」區塊 ⇒ 🔴 這一筆整筆不動"
                  "（不退回用 regex 撈句子 —— 那會把好資料切碎）")
            continue

        # 🔴 金額只從「詳細內容」區塊抽，不從整頁抽。
        #    ⚠️ 748 實測：整頁抽到 11,850，但那是**同頁別的補助**
        #       （一款家庭生活費），不是「低收入戶資格」本身的金額。
        raw_min, raw_max, raw_unit, ev = extract_amounts(body)
        amin, amax, unit, reason = usable_amount(raw_min, raw_max, raw_unit)
        if reason and raw_min is not None:
            print(f"      ⚠️ 抽到 {raw_min:,}~{raw_max:,} 但不填欄位：{reason}")
        new_desc = build_desc(name, new_url, body, amin, amax, unit, reason)

        # 🔴 不可讓新描述比舊的短 —— 這次重抓的目的就是「補完整」。
        #    變短代表抽取出了問題（第一版 750/752 就是這樣），
        #    而「欄位有被更新」看起來跟「更新成功」一模一樣。
        if len(new_desc) < len(desc or ""):
            print(f"      🔴 新描述 {len(new_desc)} 字 < 舊的 "
                  f"{len(desc or '')} 字 ⇒ 🔴 這一筆整筆不動（重抓應該變完整）")
            continue

        changes.append({
            "id": bid, "name": name,
            "url_old": url, "url_new": new_url,
            "desc_old": desc or "", "desc_new": new_desc,
            "amt_old": (amin0, amax0, unit0),
            "amt_new": (amin, amax, unit),
            "txt_len": len(txt), "ev": ev[:3],
        })
        print(f"      ✅ 抓到 {len(txt)} 字｜金額 {amin}~{amax} {unit}"
              f"｜描述 {len(desc or '')} → {len(new_desc)} 字")

    print(f"\n{'='*66}")
    print(f"可寫入 {len(changes)}/{len(TARGET_IDS)} 筆")
    out = bak / "hccg5_changes.json"
    out.write_text(json.dumps(changes, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"變動明細 → {out}")

    if not args.apply:
        print("\n（dry-run，未寫入。確認後加 --apply）")
        return 0

    for c in changes:
        amin, amax, unit = c["amt_new"]
        # 🔴 抽不到金額時**不要覆蓋掉舊金額** —— 那是「我沒查到」
        #    不是「這個補助沒有金額」，兩者在資料庫裡長得一樣。
        if amin is None:
            cur.execute(
                "UPDATE benefits SET source_url=%s, description=%s,"
                " last_verified_date=CURRENT_DATE WHERE id=%s",
                (c["url_new"], c["desc_new"], c["id"]))
        else:
            cur.execute(
                "UPDATE benefits SET source_url=%s, description=%s,"
                " amount_min=%s, amount_max=%s, amount_unit=%s,"
                " last_verified_date=CURRENT_DATE WHERE id=%s",
                (c["url_new"], c["desc_new"], amin, amax, unit, c["id"]))
    conn.commit()
    print(f"\n✅ 已寫入 {len(changes)} 筆")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
