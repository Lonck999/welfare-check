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
from split_subsidy_items import (  # noqa: E402
    SubsidyItem, latest_only, same_topic, split_items,
)

SP = re.compile(r"\s+")
# 🔴 這些字出現在描述裡＝這筆是空殼
EMPTY_MARK = re.compile(r"未查得|查無|待補|尚未")

# 🔴 Firecrawl 整站抓不到的網域（2026-09-27 實測）
#    屏東 pthg.gov.tw：ERR_TUNNEL_CONNECTION_FAILED，8/8 全失敗
#    但 curl 測 HTTP 200、181KB ⇒ **網站是好的，是 Firecrawl proxy 到不了**
#    ⚠️ 不跳過的話每筆要耗完重試（實測約 5 分鐘），334 筆裡約 15 筆
#       ⇒ 白等 75 分鐘，而且結果一定是「找不到」
#    🔴 標註成「工具限制」而不是「官方沒有」—— 兩者完全不同，
#       日後換抽取後端就能補，不可記成「這個縣市沒補助」
UNREACHABLE_COUNTY = {
    "屏東縣": "pthg.gov.tw 整站 Firecrawl 抓不到（proxy 問題，非官方無資料）",
}


def own_domain(url: str, county: str) -> bool:
    """🔴 只採信該縣市自己的網域 —— 上一輪就是漏了這步抓到別縣市的。"""
    doms = COUNTY_DOMAIN.get(county)
    if not doms:
        return False
    return any(d in url for d in doms)


def topic_hit(txt: str, topic: str) -> bool:
    """🔴 抓回來的頁面主題對不對（2026-09-27 加，這是最嚴重的一個洞）。

    ⚠️ 踩雷經過：查「瓦斯費補助」抓回**冷氣汰換補助**的頁面 ——
       金門記成「750~1,000,000 元」、雲林「300~2,000,000 元」。
    🔴 這比「沒抓到」糟糕得多：使用者看到的是**完全錯的補助**，
       而金額、資格、來源網址全都長得很正常，**沒有任何訊號**。
       根因是搜尋找不到那個主題時，會回「最接近的補助頁」。

    判準：主題的**核心詞**至少要有一個出現在正文裡。
      「瓦斯費補助（地方明細）」→ 核心詞「瓦斯」
      ⚠️ 不能用整個主題名比對 —— 官方用語與我們的分類名常常不同
         （已知三例：房屋修繕 vs 住宅設施設備、
           中低醫療看護 vs 傷病醫療暨看護費用、生育獎勵金 vs 生育津貼）
      ⇒ 拆成 2 字詞組，任一命中即可；但**必須是主題特有的詞**，
        所以先剝掉「補助/津貼/地方/明細」這類到處都有的字。
    """
    # 🔴 括號內常是**最關鍵的限定詞**，不可整段剝掉（2026-09-27 踩到）：
    #    「環保節能補助（電動機車地方加碼）」剝掉括號 → 只剩「環保節能」
    #    ⇒ 真正的電動機車補助頁反而被判「主題不符」而誤殺
    #    ⇒ 改成把括號換成分隔符，內容一併參與比對
    clean = re.sub(r"[（()）]", "／", topic)
    clean = re.sub(r"補助|津貼|獎勵金|補貼|方案|地方|明細|加碼|優惠|"
                   r"縣市政府|工作地點|其他|福利|入口|申請|／", "", clean).strip()
    # 剝完太短（例如「食物銀行」剝成「食物銀行」還算長，但「租金補貼」剝成「租金」）
    if len(clean) < 2:
        return True          # 🔴 無法判斷就放行，交給人工抽查 —— 不誤殺
    grams = {clean[i:i + 2] for i in range(len(clean) - 1)}
    return any(g in txt for g in grams)


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
                # 🔴 主題必須對得上 —— 否則會抓回「最接近的補助頁」
                #    （實測：查瓦斯費抓到冷氣汰換，金額記成 750~1,000,000）
                if not topic_hit(txt, topic):
                    print(f"      ⏭ 主題不符，跳過：{u[:56]}")
                    continue
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
        # 🔴 已知整站抓不到的縣市：直接標註原因，不浪費 5 分鐘重試
        if county in UNREACHABLE_COUNTY:
            why = UNREACHABLE_COUNTY[county]
            miss += 1
            print(f"      ⏭ 跳過（{why}）")
            if args.apply:
                cur.execute("""UPDATE benefits
                                  SET description = %s,
                                      last_verified_date = CURRENT_DATE
                                WHERE id = %s""",
                            (f"{county}{re.sub(r'[（(].*?[)）]', '', name).strip()}。"
                             f"🔴 本筆內容尚未取得 —— 原因是抓取工具限制"
                             f"（{why}），**不是該縣市沒有這項補助**。"
                             f"請逕洽 {county}政府相關局處，或日後改用其他"
                             f"抽取後端重新取得。", bid))
                conn.commit()
            continue
        hit = best_page(county, name)
        if not hit:
            miss += 1
            print("      🔴 找不到該縣市官方頁 → 保持原樣不動")
            continue
        url, txt = hit
        # 🔴 C 方案優先：先試著把一頁拆成多個補助項目
        #    拆得出來 → 主筆用「最新年度的主項目」，其餘寫進描述
        #    拆不出來 → fallback 回 A（整頁一筆，列出金額出處）
        items = latest_only(split_items(txt))
        if len(items) >= 2:
            # 🔴 主項目：先過同義詞比對（Lonck 2026-09-26 選 B）
            #    ⚠️ 原本 fallback 是「取金額最大」—— 宜蘭那次剛好對
            #       （生育津貼 20,000 > 產檢交通費 3,000），但主項目金額
            #       **不保證**比附屬項目大，那個 fallback 只是運氣好。
            main = next((i for i in items if same_topic(i.name, name)), None)
            fallback = main is None
            if main is None:
                main = max(items, key=lambda i: i.amount_max or 0)
            others = [i for i in items if i is not main]
            amin, amax, unit = (main.amount_min, main.amount_max,
                                main.amount_unit)
            ev = main.evidence
            extra = ("　⚠️ 同一頁另有：" +
                     "；".join(f"{i.name} {i.amount_min:,} 元"
                               + (f"（{i.period} 年起）" if i.period else "")
                               for i in others[:4]) + "。")
            print(f"      🔸 拆出 {len(items)} 項　主項目「{main.name}」"
                  f"{amin}~{amax}"
                  + ("　🔴 同義詞對不上→取金額最大（推測）" if fallback else ""))
            # 🔴 fallback 時必須讓使用者看得出「這是推測的」
            #    ⚠️ 不標的話，推測出來的主項目跟比對出來的長得一模一樣
            if fallback:
                extra += ("🔴 主項目由金額大小推測（官方頁的項目名與本筆名稱"
                          "對不上），請點來源網址確認哪一項才是你要申請的。")
        else:
            amin, amax, unit, ev = extract_amounts(txt)
            extra = ""
            main = None
        desc = build_desc(county, name, url, txt, amin, amax, unit, ev) + extra
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
