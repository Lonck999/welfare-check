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


def is_corporate_page(txt: str) -> bool:
    """🔴 這頁的**申請人**是法人而不是民眾嗎（2026-09-28 加）。

    ⚠️ Lonck 2026-09-28 點破我的方向錯了：
       這網站是給一般民眾的 ⇒ 法人補助**根本不該被收進來**，
       問題不是「金額要不要擋」，而是**那整筆頁面抓錯了**。
       我原本提的兩個選項都在修金額，等於默認那些頁面可以留著。

    🔴 不可只靠關鍵字 —— 實查 27 筆含「雇主／法人／事業單位」的資料，
       其中至少 4 筆是**給個人的**，那些詞只出現在流程描述裡：
         「缺工就業獎勵」  → 受僱後**向公立就業服務機構**申請（個人領）
         「跨域就業補助」  → 失業勞工本人申請
         「性騷擾心理諮商」→ 協助**雇主轉介**被害人（被害人領）
         「社區居住補助」  → 受補助單位只出現在「評估」環節
       ⇒ 關鍵字命中 ≠ 法人補助，判準必須是「**誰去申請、誰收錢**」。

    判準：申請/受款主體的直接證據，且要**兩個以上**才算。
    """
    # 🔴 這些片語直接指出「收錢的是機構」
    RECIPIENT = (
        "受補助單位名稱", "受補助單位應", "申請單位提送", "申請單位應檢具",
        "領據上須書名", "統一編號", "立案證明", "設立登記證",
        "公司登記證明", "商業登記證明", "法人登記證書",
        "補助單位之銀行帳戶", "營利事業登記",
    )
    # 🔴 這些片語指出「申請人是雇主/事業單位」
    APPLICANT = (
        "雇主應於", "雇主得於", "雇主申請", "雇主檢附", "雇主提出申請",
        "事業單位申請", "事業單位應", "由事業單位", "本補助之申請人為雇主",
        "申請人為事業單位", "僱用單位申請",
    )
    hits = sum(1 for p in RECIPIENT + APPLICANT if p in txt)
    if hits >= 2:
        return True
    # 單一命中時要有第二個獨立訊號：整頁完全沒有「民眾/本人」視角的字
    if hits == 1 and not re.search(r"申請人本人|民眾|市民|縣民|本人親自|"
                                   r"被害人|失業勞工|求職者|勞工本人", txt):
        return True
    return False


def topic_hit(txt: str, topic: str) -> bool:
    """🔴 抓回來的頁面主題對不對（2026-09-27 加，2026-09-28 收緊）。

    ⚠️ 第一版（2-gram 任一命中）**放太寬**，實測漏掉三筆：
       「環保節能補助（電動機車地方加碼）」抓到**冷氣汰換**頁
         —— 核心詞含「節能」，而冷氣汰換頁當然有「節能」
         彰化記成 20,000（窗型冷氣 2 萬）、南投 80,000
       「照顧者現金津貼」抓到**托育補助**頁（臺東 15,000）
    🔴 這是第四類「看起來完全正常的錯誤資料」——
       每修一類就冒出下一類，因為判準的**形狀**不對。

    ⇒ 改成兩層（Lonck 2026-09-28 選 C）：
      ① **必要詞**：括號內的實質限定詞（電動機車／重陽禮金／蘭嶼）
         必須出現 —— 那是這筆補助的定義，不是選項之一
         ⚠️ 但「地方明細／地方加碼／全國概況」是純標籤，不算限定
      ② **排除詞**：已知會混進來的鄰居主題（電動機車 ⇥ 冷氣/照明）
         🔴 排除詞清單永遠列不完，所以它只是安全網，不是主判準
    """
    # 括號內若只是分類標籤，不構成限定條件
    LABEL_ONLY = ("地方明細", "地方加碼", "全國概況", "地方方案",
                  "地方申請入口", "自辦方案", "澄清", "疑似")
    must: list[str] = []
    for grp in re.findall(r"[（(]([^)）]+)[)）]", topic):
        for part in re.split(r"[/、，,]", grp):
            part = re.sub(r"地方|加碼|明細|方案|概況|申請入口|全國", "", part).strip()
            if len(part) >= 2 and not any(l in grp for l in LABEL_ONLY if l == grp.strip()):
                must.append(part)
    # 🔴 ① 必要詞：任一命中即可（同一括號內常是「A/B」的並列選項）
    #    ⚠️ 長必要詞要能部分命中 —— 「65歲以上健保費」在頁面上常寫成
    #       「65歲以上老人健保費補助」（中間插了字），整串比對會誤殺。
    #       ⇒ 超過 4 字的必要詞改用「開頭 3 字 ＋ 結尾 3 字」任一命中。
    def _mhit(m: str) -> bool:
        if m in txt:
            return True
        if len(m) > 4:
            return m[:3] in txt or m[-3:] in txt
        return False

    if must and not any(_mhit(m) for m in must):
        return False

    # 🔴 ② 排除詞：主題特有的「鄰居陷阱」
    EXCLUDE = {
        "電動機車": ("冷氣", "分離式", "空調", "照明", "燈具", "冰箱", "能管系統"),
        "電動自行車": ("冷氣", "空調", "照明", "冰箱"),
        "瓦斯": ("冷氣", "空調", "照明", "燈具"),
        "照顧者": ("托育", "幼兒園", "課後照顧"),
        "重陽": ("冷氣", "空調"),
    }
    for key, bad in EXCLUDE.items():
        if key in topic:
            hits = sum(1 for b in bad if b in txt)
            # ⚠️ 只出現一次可能是順帶提到；**兩個以上**才判定是別的主題
            if hits >= 2 and key not in txt:
                return False

    clean = re.sub(r"[（()）]", "／", topic)
    clean = re.sub(r"補助|津貼|獎勵金|補貼|方案|地方|明細|加碼|優惠|"
                   r"縣市政府|工作地點|其他|福利|入口|申請|／", "", clean).strip()
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
                # 🔴 這頁的申請人是法人 ⇒ 整筆跳過（2026-09-28）
                #    ⚠️ 不是「清掉金額留著描述」—— 這網站是給一般民眾的，
                #       法人補助根本不該收進來，留著等於給錯資訊。
                if is_corporate_page(txt):
                    print("      ⏭ 法人補助頁（申請人是機構/雇主）→ 不收")
                    continue
                # 🔴 主題必須對得上 —— 否則會抓回「最接近的補助頁」
                #    （實測：查瓦斯費抓到冷氣汰換，金額記成 750~1,000,000）
                if not topic_hit(txt, topic):
                    print("      ⏭ 主題不符 → 換下一個結果")
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
        # 🔴 就算沒取到單一金額，也要把抓到的金額原文寫進描述（2026-09-27）
        #    ⚠️ 兩種情況會走到這裡：
        #      ① 頁面真的沒寫金額
        #      ② 區間跨度 >20 倍被安全網擋下（同頁多個不同補助混在一起）
        #    ②的原文對使用者有價值 —— 他能自己看出哪一項是他要的。
        #    不寫的話等於把查到的東西丟掉，而且兩種情況在畫面上分不出來。
        if ev:
            parts.append("⚠️ 該頁出現多種金額，無法判定哪一項屬於本補助："
                         + "；".join(ev[:3]) + "。")
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
