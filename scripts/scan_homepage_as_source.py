#!/usr/bin/env python3
"""掃全庫：`source_tier = official` 但 `source_url` 只是**網站首頁**。

🔴 起因（2026-09-30，id 46-67 瓦斯費補助）：
   12 筆的 source_url 是 `https://www.mohw.gov.tw/`（衛福部**首頁**），
   描述是「本次搜尋未查得此縣市瓦斯費補助的具體金額與資格門檻」，
   **而 source_tier 全部標成 `official`**。

🔴 為什麼這比「沒有來源」更糟：
   `official` 在這個系統裡的意思是「**這筆資料有官方頁面佐證**」。
   首頁不是任何補助的佐證 —— 它對每一筆補助都同樣「成立」，
   ⇒ 這 12 筆等於**沒有來源，卻掛著官方認證**。
   ⚠️ 而使用者（和未來的我）看到 `official` 就不會再去查。

判準（兩個都要成立才算）：
  ① source_url 是首頁或近乎首頁（無路徑、或路徑只有 `/ch`、`/tw` 這種語系段）
  ② source_tier = 'official'

⚠️ 這是**偵測**腳本，不改任何資料。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg2

# 🔴 這些路徑段只是語系／站台入口，不構成「指向某個補助」
BARE_SEGMENTS = {"", "ch", "tw", "zh-tw", "zh_tw", "index.html", "index.htm",
                 "home", "default.aspx", "index.aspx", "index.php", "en"}


def is_bare_homepage(url: str) -> tuple[bool, str]:
    """這個網址是不是只是首頁。回傳 (是否, 理由)。"""
    if not url:
        return True, "沒有網址"
    try:
        p = urlparse(url)
    except ValueError:
        return False, ""
    if not p.netloc:
        return True, "不是完整網址"
    # 🔴 有 query string 就代表它指向某個東西（?id=xxx&s=yyy）
    if p.query:
        return False, ""
    segs = [s for s in p.path.split("/") if s]
    if not segs:
        return True, "只有網域，沒有路徑"
    if len(segs) == 1 and segs[0].lower() in BARE_SEGMENTS:
        return True, f"路徑只有語系／入口段（/{segs[0]}）"
    return False, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    # 🔴 預設只掃 is_active —— 停用的筆不顯示給使用者，所以它的來源網址
    #    錯不錯都不影響任何人；報它只會讓人去修一個不會被看到的東西。
    #    ⚠️ 2026-10-08 踩到：id 34 拆成三筆後標 is_active=false（刻意保留，
    #    否則月更比對會把它當新缺口再抓一次），而這支仍把它算進
    #    「official ＋ 首頁當來源」⇒ 看起來「修了卻沒變少」。
    #    🔴 這不是誤報而是真缺陷：**偵測器的範圍要跟「使用者看得到什麼」一致**。
    ap.add_argument("--include-inactive", action="store_true",
                    help="連已停用的也掃（查歷史用，預設不掃）")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute(f"""SELECT id, county, name, source_url, source_tier,
                          LENGTH(description), description
                     FROM benefits
                    WHERE source_url IS NOT NULL
                      {"" if args.include_inactive else "AND is_active"}
                    ORDER BY id""")
    rows = cur.fetchall()
    scope = "含已停用" if args.include_inactive else "僅生效中"
    print(f"全庫 {len(rows)} 筆有 source_url（{scope}）\n")

    hits: list[dict] = []
    for bid, county, name, url, tier, dlen, desc in rows:
        bare, why = is_bare_homepage(url)
        if not bare:
            continue
        hits.append({
            "id": bid, "county": county or "全國", "name": name,
            "url": url, "tier": tier, "desc_len": dlen,
            "why": why,
            # 🔴 描述是不是也承認查不到 —— 兩者都成立時最確定
            "empty_shell": bool(desc and
                                any(k in desc for k in
                                    ("未查得", "查無", "待補", "尚未"))),
        })

    by_tier: dict[str, list] = {}
    for h in hits:
        by_tier.setdefault(h["tier"] or "NULL", []).append(h)

    print(f"{'='*70}\n首頁當來源的共 {len(hits)} 筆，按 source_tier 分：")
    for tier, items in sorted(by_tier.items(),
                              key=lambda kv: -len(kv[1])):
        mark = "🔴" if tier == "official" else "⚠️"
        shells = sum(1 for x in items if x["empty_shell"])
        print(f"  {mark} {tier}: {len(items)} 筆"
              f"（其中描述也寫著「未查得」的 {shells} 筆）")

    off = by_tier.get("official", [])
    if off:
        print(f"\n{'='*70}\n🔴 `official` ＋ 首頁當來源 —— 這些是「沒有來源卻掛官方認證」")
        # 依網域分組，看是不是同一批產物
        dom: dict[str, list] = {}
        for h in off:
            dom.setdefault(urlparse(h["url"]).netloc, []).append(h)
        for d, items in sorted(dom.items(), key=lambda kv: -len(kv[1])):
            print(f"\n  ── {d}（{len(items)} 筆）")
            for h in items[:25]:
                flag = "空殼" if h["empty_shell"] else f"{h['desc_len']}字"
                print(f"     [{h['id']}] {h['county']} {h['name'][:26]}"
                      f"　{flag}")
            if len(items) > 25:
                print(f"     （另 {len(items)-25} 筆）")

    out = Path("/tmp/wc_backup/homepage_as_source_scan.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(hits, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n完整結果 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
