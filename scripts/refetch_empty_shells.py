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
    #    ⚠️ 2026-09-28 移除三個誤判來源（實測誤殺個人補助頁）：
    #      · `統一編號` —— 政府網站**頁尾都有**（機關統編），
    #        嘉義急難救助 3,700 字的頁面也命中 → 完全沒有鑑別力
    #      · `營利事業登記` —— 整站列表頁裡**別的補助項目**會提到
    #      · `立案證明` / `設立登記證` 保留但不單獨成立（見下方 hits 門檻）
    RECIPIENT = (
        "受補助單位名稱", "受補助單位應", "申請單位提送", "申請單位應檢具",
        "領據上須書名", "補助單位之銀行帳戶",
    )
    # 🔴 這些片語指出「申請人是雇主/事業單位」
    APPLICANT = (
        "雇主應於", "雇主得於", "雇主申請", "雇主檢附", "雇主提出申請",
        "事業單位申請", "事業單位應", "由事業單位", "本補助之申請人為雇主",
        "申請人為事業單位", "僱用單位申請",
    )
    hits = sum(1 for p in RECIPIENT + APPLICANT if p in txt)

    # 🔴 片語清單永遠列不完 —— 補一條「形狀」判準（2026-09-28 第二輪）
    #    ⚠️ 嘉義那筆溜過去：頁面寫的是「雇主**已依照**職能復健…」與
    #       「**雇主提供**職業災害勞工輔助設施補助申請書」，
    #       我列的「雇主應於／雇主檢附／雇主申請」一個都沒命中。
    #    🔴 這正是我自己三輪前寫過的教訓（NOT_AMOUNT 補三輪每輪漏下一種），
    #       卻在同一支腳本裡用同樣的形狀再犯一次。
    #    ⇒ 改判「**申請書／申請表的主體是誰**」：
    #      官方表單的命名一定含主體（「雇主提供…補助申請書」），
    #      那比動詞片語穩定得多。
    #    ⚠️ 2026-09-28 收緊：不可含「機構」「團體」「申請單位」「公司」——
    #       「機構、團體等，得檢具申請書」是**手語翻譯服務的申請窗口**，
    #       出現在花蓮社會處的整站列表裡，害它被判成法人補助。
    #    🔴 只留「明確是企業/雇主」的主體。
    if re.search(r"(雇主|事業單位|受補助單位|營利事業)"
                 r"[^。\n]{0,20}(申請書|申請表|補助收據|領據)", txt):
        hits += 2

    # 🔴 資格條款的主詞是雇主/單位 ⇒ 那是法人補助
    #    「(一)雇主已依照職能復健專業機構建議提供輔助設施」
    if re.search(r"[（(][一二三四五六七八九\d][)）]\s*"
                 r"(雇主|事業單位|申請單位|僱用單位)", txt):
        hits += 2

    # 🔴 第三輪（2026-09-28）：改數「主體」而不是數「片語」。
    #    ⚠️ 花蓮「新建托兒設施最高補助500萬」溜過去：
    #       「事業單位」出現 **10 次**（「請有意申請經費補助之事業單位」
    #       「鼓勵事業單位提供員工托兒服務」），但我的片語要
    #       「事業單位申請／應／由」才算 —— 這頁用的全是別的寫法。
    #
    # 🔴🔴 第四輪修正（同日）：原本的「密度」判準錯得更根本，已丟棄。
    #    實測誤殺兩筆個人補助頁，原因有兩個，而且都不是調門檻能解的：
    #    ① **長度偏誤**：花蓮社會處那頁是 146,466 字元的整站列表，
    #       自然累積 13 次法人詞 —— 越長的頁面越容易被誤判。
    #    ② 🔴 **「申請單位」有兩種相反的意思**：
    #         「受理申請單位：…兒童發展通報轉介中心」← 民眾去申請的窗口
    #         「請有意申請補助之事業單位提出」        ← 申請人是法人
    #       同一個詞，一個是「去哪裡辦」，一個是「誰能辦」。
    #    ⇒ 密度永遠分不出這兩者。改用「**申請人身分的直接宣告**」。
    #
    # 判準：頁面明確寫出「補助對象／申請對象是法人」。
    #   ⚠️ 只認宣告句，不認提及 —— 提及會被長頁面和窗口說明汙染。
    if re.search(r"(補助|申請|受補助)(對象|資格)[^。\n]{0,30}"
                 r"(事業單位|雇主|公司|法人|營利事業|立案[^。\n]{0,6}機構)", txt):
        hits += 2
    # 「請…之事業單位申請」這種句型：主體 + 動作直接相連
    if re.search(r"(請|有意|欲)[^。\n]{0,14}"
                 r"(事業單位|雇主|營利事業)[^。\n]{0,10}"
                 r"(申請|提出|檢附|備齊)", txt):
        hits += 2
    # 🔴 「僱用人數達N人以上的雇主應…」＝法定義務對象是企業
    if re.search(r"(僱用|雇用)[^。\n]{0,12}人數[^。\n]{0,12}"
                 r"(雇主|事業單位|公司)", txt):
        hits += 2

    if hits >= 2:
        return True
    # 單一命中時要有第二個獨立訊號：整頁完全沒有「民眾/本人」視角的字
    # 🔴 導覽選單不算內容（2026-09-28）：花蓮那頁的「縣民」兩次都在
    #    「[縣民園地](...)」選單連結裡，卻讓 1-hit 規則失效。
    #    ⇒ 比對前先把 markdown 連結整行剝掉。
    body = re.sub(r"^\s*-?\s*\[[^\]]*\]\([^)]*\)\s*$", "", txt, flags=re.M)
    body = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body)
    if hits == 1 and not re.search(r"申請人本人|民眾|市民|縣民|本人親自|"
                                   r"被害人|失業勞工|求職者|勞工本人", body):
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

    # 🔴 語意單位不可被 2-gram 拆碎（Lonck 2026-09-29 選 B）。
    #    ⚠️ 踩雷：新竹縣「照顧者現金津貼」抓到**敬老卡點數新聞**
    #       （敬老卡 13 次、愛心卡 14 次、🔴 「照顧者」0 次、「津貼」0 次），
    #       只因為那頁有 1 次「長照**照顧**」——
    #       核心詞「照顧者現金」被切成 照顧/顧者/者現/現金，「照顧」就過關了。
    #    🔴 「照顧者」是**領錢的人**，「照顧」是任何照護語境 ——
    #       2-gram 把這個區別磨掉了。這是第二次（上次「環保節能」沾到冷氣）。
    #
    #    判準：只收「**前兩字單獨看意思完全不同**」的詞。
    #    ⚠️ 不可無差別列入 —— 「生育」「租金」這種兩字詞本來就不會被拆錯，
    #       列進來只會讓判準變成 A（整串命中），失去容忍官方用詞差異的能力。
    #
    # 🔴 一個語意單位可能有多種官方寫法，必須列成**同義群組**（2026-09-29）：
    #    ⚠️ 第一版只寫「照顧者」，結果誤殺花蓮那筆正確的補助頁 ——
    #       官方標題是「醫療及**住院照顧費**用補助」、內文寫
    #       「特別**照顧津貼**」，**「照顧者」出現 0 次**。
    #    🔴 而那頁「照顧」出現 14 次 —— 跟被擋下的敬老卡新聞（1 次）
    #       只差在「照顧」後面接什麼字。
    #    ⇒ 群組內任一寫法整串命中即可；群組本身仍不接受 2-gram 拆解。
    SEMANTIC_UNITS = (
        # 照顧者津貼：領錢的人 vs 任何照護語境
        ("照顧者", "特別照顧", "照顧津貼", "照顧費", "照顧補助"),
        ("發展遲緩", "早期療育"),
        ("社會住宅",),          # ← 住宅：住宅修繕、住宅地震保險
        ("食物銀行",),          # ← 銀行：金融機構
        ("急難救助", "急難慰問", "急難紓困", "急難"),
        ("敬老卡", "愛心卡", "敬老悠遊卡"),   # ← 敬老：敬老禮金
        ("重陽禮金", "重陽敬老"),
        ("電動機車", "電動二輪", "電動自行車"),
        ("坐月子", "孕產婦", "產後護理"),
        ("外籍看護", "外籍家庭看護", "仲介費"),
        ("新住民",),
        ("實體書店",),
        ("健保費", "健康保險費"),   # ← 健保：健保給付
        ("社會安全網",),
        ("精神病患", "精神疾病"),
        ("航空票價", "醫療代金", "就醫交通"),
    )
    units: list[str] = []
    for grp in SEMANTIC_UNITS:
        if any(u in topic for u in grp):
            units.extend(grp)
    if units:
        # 🔴 主題含語意單位 ⇒ 群組內至少一個必須**整串**出現，不接受 2-gram
        if not any(u in txt for u in units):
            return False
        return True

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


# ── 目標集合（--target）──────────────────────────────────────────
# 🔴 兩種要重抓的資料，成因完全不同：
#
#   empty　　　　　　描述寫著「未查得／查無／待補／尚未」＝**誠實的空殼**
#                   使用者看得出來沒資料（KNOWN-ISSUES W-004）
#
#   excerpt-mismatch 佐證片段講的是**別的縣市**（KNOWN-ISSUES W-001）
#                   ⚠️ 比空殼危險 —— 有網址、有原文、有查證日期，
#                   **每個欄位都填滿了**，使用者無從分辨
#
# 🔴 mismatch 的 SQL 必須把「臺」正規化成「台」，
#    否則「臺東縣 vs 台東縣」被判成不符（實測多報 11 筆）。
# 🔴 判準是「提到別的縣市 **且** 沒提到自己」，不是「提到別的縣市」——
#    一篇比較全台補助的文章提到 22 個縣市是正常的（不加這條多報 51 筆）。
_COUNTY_RE = (
    "(台北市|新北市|桃園市|台中市|台南市|高雄市|基隆市|新竹市|新竹縣"
    "|苗栗縣|彰化縣|南投縣|雲林縣|嘉義市|嘉義縣|屏東縣|宜蘭縣|花蓮縣"
    "|台東縣|澎湖縣|金門縣|連江縣)"
)

# 🔴 標記前綴。稽核腳本要靠它判斷「這筆已經承認佐證不對了」，
#    所以它必須是**唯一且不會出現在真實原文裡**的字串。
BAD_EXCERPT_MARK = "🔴【佐證與本縣市不符】"

TARGET_SQL = {
    "empty": """SELECT id, county, name FROM benefits
                 WHERE description ~ '未查得|查無|待補|尚未'
                   AND county IS NOT NULL""",
    "excerpt-mismatch": f"""
        SELECT id, county, name FROM benefits
         WHERE county IS NOT NULL
           AND source_excerpt NOT LIKE '{BAD_EXCERPT_MARK}%%'
           AND replace(source_excerpt,'臺','台') ~ '{_COUNTY_RE}'
           AND replace(source_excerpt,'臺','台')
               NOT LIKE '%%' || replace(county,'臺','台') || '%%'""",
}


def mark_bad_excerpt(cur, conn, bid: int, county: str, why: str) -> None:
    """把「佐證講的是別的縣市」這件事標進 source_excerpt 本身。

    🔴 為什麼標在 source_excerpt 而不是 description：
       問題就在這個欄位。標在別的地方等於「修了一個不是問題的地方」，
       而真正錯的那段原文仍然原封不動被 API 吐出去。

    🔴 為什麼**不動 last_verified_date**：
       這一步沒有取得新的佐證，只是承認舊的不對。
       推日期會讓這筆變成「今天剛查證過」——
       **比昨天更可信，而它其實更不可信。**
       ⚠️ 2026-09-29 第一版就是這樣寫的，實跑 45 秒撞到屏東縣才發現。

    原文保留在標記後面：它對「這個補助存在」仍然是證據，
    只是不能拿來支撐「本縣市的金額／條件」。
    """
    cur.execute("SELECT source_excerpt FROM benefits WHERE id = %s", (bid,))
    row = cur.fetchone()
    old = (row[0] if row else "") or ""
    if old.startswith(BAD_EXCERPT_MARK):
        return  # 已標過，不重複疊加
    cur.execute(
        "UPDATE benefits SET source_excerpt = %s WHERE id = %s",
        (f"{BAD_EXCERPT_MARK}本段原文講的並不是{county}"
         f"（來源是跨縣市整理文），**不可用來支撐{county}的金額或條件**。"
         f"重抓狀況：{why}。以下為原文，僅供佐證「這項補助存在」：\n{old}",
         bid))
    conn.commit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--topic", help="只跑這個主題（子字串比對）")
    ap.add_argument("--limit", type=int, default=0, help="最多處理幾筆")
    ap.add_argument("--target", choices=sorted(TARGET_SQL),
                    default="empty",
                    help="要重抓哪一批（empty＝空殼；"
                         "excerpt-mismatch＝佐證講別縣市）")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    sql = TARGET_SQL[args.target]
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

    # 🔴 excerpt-mismatch 的「抓不到」跟 empty 的「抓不到」要做相反的事。
    #
    #    empty：描述本來就空 → 改寫描述說明原因，是**增加資訊**
    #    excerpt-mismatch：問題在 source_excerpt（它講的是別的縣市）
    #      ⇒ 只改 description 等於**完全沒修到那個問題**，
    #        而 last_verified_date 被推到今天 ⇒ 那筆變成「今天剛查證過」
    #        —— 錯的佐證原封不動留著，卻看起來比昨天更可信。
    #
    #    🔴 2026-09-29 實跑 45 秒就撞到：屏東縣 10 筆全部會走這條路。
    is_excerpt_mode = args.target == "excerpt-mismatch"

    ok = miss = failed = marked = 0
    for bid, county, name in rows:
        print(f"  · {county} {name[:34]}")
        # 🔴 已知整站抓不到的縣市：直接標註原因，不浪費 5 分鐘重試
        if county in UNREACHABLE_COUNTY:
            why = UNREACHABLE_COUNTY[county]
            miss += 1
            print(f"      ⏭ 跳過（{why}）")
            if args.apply and is_excerpt_mode:
                marked += 1
                miss -= 1
                mark_bad_excerpt(cur, conn, bid, county, why)
                print("      🔸 佐證標記為「講的是別的縣市」"
                      "（不動 last_verified_date）")
            elif args.apply:
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
            print("      🔴 找不到該縣市官方頁", end="")
            if args.apply and is_excerpt_mode:
                marked += 1
                mark_bad_excerpt(cur, conn, bid, county,
                                 "重抓時找不到該縣市官方頁")
                print(" → 佐證標記為「講的是別的縣市」"
                      "（不動 last_verified_date）")
            else:
                miss += 1
                print(" → 保持原樣不動")
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
        # 🔴 單筆寫入失敗不可讓整批停掉（2026-09-29 踩到）：
        #    exa 回的內容含 NUL(0x00) → psycopg2 ValueError →
        #    **前 17 筆已寫入、後 35 筆一筆都沒跑**，
        #    而 log 尾巴只有 traceback，「做了一半」完全沒有訊號。
        #    ⚠️ 下次看到「空殼少了 17」會以為那批只有 17 筆要處理。
        try:
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
        except Exception as e:                            # noqa: BLE001
            conn.rollback()
            ok -= 1
            failed += 1
            print(f"      🔴 寫入失敗（已跳過這筆，整批繼續）：{str(e)[:90]}")
        time.sleep(1)

    # 🔴 寫入失敗筆數必須出現在結尾摘要 —— 否則它會被算進「找不到官方頁」
    tail = f"　🔴 寫入失敗 {failed}" if failed else ""
    # 🔴 marked 同理：它是「承認佐證不對」不是「修好了」，
    #    不印出來的話跟 ok 混在一起 ⇒ 看起來像整批都修好了。
    tail += f"　🔸 標記佐證不符 {marked}" if marked else ""
    print(f"\n{'✅ 已寫入' if args.apply else '（dry-run）'}"
          f"　成功 {ok}　找不到官方頁 {miss}{tail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
