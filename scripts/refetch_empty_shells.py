#!/usr/bin/env python3
"""重抓 363 筆「本次搜尋未查得」的空殼描述。

🔴 這批的真相（2026-09-25 實查）：
   · 363 筆只有 **38 個不重複主題** —— 是「主題 × 縣市」的複製品
     （22 × 孕產婦補助、22 × 瓦斯費補助、22 × 急難慰問金…）
   · 集中在**沒有開放資料集**的縣市（金門/澎湖/連江/嘉義市各 19）
   · 66 筆的 source_url 指向衛福部首頁或月子中心部落格（yannigo.com）
     —— **那是不能給使用者點的來源**

🔴 為什麼這次能抓到、上次抓不到：
   ① 上次搜尋沒有縣市網域驗證 ⇒ 抓到別縣市的頁面
   ② **抽取器不認中文數字** ⇒ 法規頁抓到了卻回報「0 個金額」
      （已於 283f861 修好，雙向驗證 12/12）

🔴 寫入原則（前面所有教訓的總和）：
   · 找不到官方頁 → **保持原樣不動**，不寫入任何東西
   · 找到頁但抽不到金額 → 寫描述與來源，金額留 None
   · 🔴 只採信該縣市自己的網域（COUNTY_DOMAIN，22 縣市實測過）
   · 🔴 一律先 --dry-run，確認後才 --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time

import psycopg2

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from extract_amounts_from_desc import extract_amounts  # noqa: E402
from fetch_local_benefit import (  # noqa: E402
    COUNTY_DOMAIN, extract, search, strip_noise,
)

SP = re.compile(r"\s+")
# 🔴 這些字出現在描述裡＝這筆是空殼
EMPTY_MARK = re.compile(r"未查得|查無|待補|尚未")


def own_domain(url: str, county: str) -> bool:
    """🔴 只採信該縣市自己的網域 —— 上一輪就是漏了這步抓到別縣市的。"""
    doms = COUNTY_DOMAIN.get(county)
    if not doms:
        return False
    return any(d in url for d in doms)


def best_page(county: str, topic: str, tries: int = 2
              ) -> tuple[str, str] | None:
    """回傳 (url, 正文)。找不到回 None。"""
    # 主題名常帶「（地方明細）」這種尾巴，去掉才搜得到
    clean = re.sub(r"[（(].*?[)）]", "", topic).strip()
    queries = [f"{county} {clean} 補助 金額",
               f"{county} {clean} 申請 資格"]
    seen: set[str] = set()
    for q in queries[:tries]:
        try:
            res = search(q, 8)
        except Exception as e:
            print(f"      🔴 搜尋失敗 {str(e)[:40]}")
            continue
        for r in res:
            u = r.get("url", "")
            if u in seen or not own_domain(u, county):
                continue
            seen.add(u)
            try:
                txt = strip_noise(extract(u) or "")
            except Exception:
                continue
            if len(txt) >= 400:
                return u, txt
    return None


def build_desc(county: str, topic: str, url: str, txt: str,
               amin, amax, unit, ev: list[str] | None = None) -> str:
    """從正文組描述。🔴 只取原文，不生成內容。"""
    clean = re.sub(r"[（(].*?[)）]", "", topic).strip()
    parts = [f"{county}{clean}。"]
    if amin:
        rng = (f"{amin:,} 元" if amin == amax
               else f"{amin:,}~{amax:,} 元")
        u = {"monthly": "每月", "yearly": "每年",
             "one_time": "一次性"}.get(unit or "", "")
        parts.append(f"補助金額 {u} {rng}（官方頁面實抓）。")
        # 🔴 把證據原文列出來（2026-09-26 加）：
        #    同一頁常有多個補助混在一起 —— 宜蘭那頁的 3,000 元
        #    其實是「產檢交通費」不是生育津貼，區間變成 3,000~20,000
        #    ⚠️ 而那個區間看起來完全合理，**使用者無從分辨**。
        #    列出原文至少讓人一眼看出它抓了哪幾句。
        if ev:
            parts.append("金額出處：" + "；".join(ev[:3]) + "。")
    # 抓資格句（原文，不改寫）
    # ⚠️ 政府公文的資格句常寫成「應符合下列規定：」後面接編號清單
    #    ⇒ 一併吃掉冒號後的內容，否則只抓到「應符合下列規定：」一句廢話
    elig = re.findall(
        r"[^。\n]{0,20}(?:應符合|申請資格|補助對象|資格條件|得申請|符合下列)"
        r"[^。]{6,150}", txt)
    for s in elig[:2]:
        parts.append(SP.sub(" ", s).strip() + "。")
    if not amin:
        parts.append("🔴 金額未在官方頁面列出，詳見來源網址。")
    parts.append(f"（來源：{url}）")
    return "".join(parts)[:1800]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--topic", help="只跑這個主題（子字串比對）")
    ap.add_argument("--limit", type=int, default=0, help="最多處理幾筆")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    sql = """SELECT id, county, name FROM benefits
              WHERE description ~ '未查得|查無|待補|尚未'
                AND county IS NOT NULL"""
    params: list = []
    if args.topic:
        sql += " AND name LIKE %s"
        params.append(f"%{args.topic}%")
    sql += " ORDER BY name, county"
    cur.execute(sql, params)
    rows = cur.fetchall()
    if args.limit:
        rows = rows[: args.limit]
    print(f"待處理 {len(rows)} 筆\n")

    ok = miss = 0
    for bid, county, name in rows:
        print(f"  · {county} {name[:34]}")
        hit = best_page(county, name)
        if not hit:
            miss += 1
            print("      🔴 找不到該縣市官方頁 → 保持原樣不動")
            continue
        url, txt = hit
        amin, amax, unit, ev = extract_amounts(txt)
        desc = build_desc(county, name, url, txt, amin, amax, unit, ev)
        ok += 1
        print(f"      ✅ {url[:66]}")
        print(f"         {len(txt)} 字　金額 {amin}~{amax}　描述 {len(desc)} 字")
        if not args.apply:
            continue
        cur.execute("""UPDATE benefits
                          SET description=%s, source_url=%s,
                              source_excerpt=%s,
                              amount_min=%s, amount_max=%s, amount_unit=%s,
                              amount_note=%s,
                              last_verified_date=CURRENT_DATE
                        WHERE id=%s""",
                    (desc, url, SP.sub(" ", txt[:900]),
                     amin, amax, unit,
                     ("官方頁面實抓：" + "；".join(ev)) if ev else None,
                     bid))
        conn.commit()
        time.sleep(1)

    print(f"\n{'✅ 已寫入' if args.apply else '（dry-run）'}"
          f"　成功 {ok}　找不到官方頁 {miss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
