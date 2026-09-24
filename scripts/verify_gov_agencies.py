#!/usr/bin/env python3
"""驗證機關清單的正確性與「存在證明」完整性。

🔴 為什麼需要這支：2026-09-24 第一版的錯誤是
   **文件數字與 JSON 內容對不起來、welfare_hint 全 0**
   —— 兩邊都「看起來正常」，只有比對才發現。

用法：python scripts/verify_gov_agencies.py
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = HERE.parent / "福利發放單位清查.md"

ok = fail = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✅ {label}")
    else:
        fail += 1
        print(f"  🔴 {label}　{detail}")


def main() -> int:
    gov = json.loads((HERE / "gov_agencies.json").read_text())
    ngo = json.loads((HERE / "ngo_welfare_orgs.json").read_text())
    doc = DOC.read_text()
    b = gov["buckets"]

    print("① 分類結果符合官方定義")
    check("中央二級 = 35（15部+9會+3獨立+主計/人事/央行/故宮+省府等）",
          len(b["central2"]) == 35, f"實際 {len(b['central2'])}")
    check("縣市政府 = 22", len(b["local_gov"]) == 22,
          f"實際 {len(b['local_gov'])}")
    check("二級全部直屬行政院",
          all(x["parent"] == "行政院" for x in b["central2"]))
    check("三級直屬部會的 parent 以 部/委員會/總處/總署 結尾",
          all(x["parent"].endswith(("部", "委員會", "總處", "總署"))
              for x in b["central3_top"]))

    print("\n② 🔴 已裁撤機關不可出現（第一版用維基 regex 撈到一堆）")
    allnames = {x["name"] for v in b.values() for x in v}
    for dead in ("內政部兒童局", "行政院衛生署", "交通部電信總局",
                 "行政院勞工委員會", "行政院青年輔導委員會"):
        check(f"不含已裁撤「{dead}」", dead not in allnames)
    check("排除筆數有記錄且 > 0",
          gov["_meta"]["dropped_dissolved"] > 0)

    print("\n③ 🔴 非行政院體系不可出現（第一版 central2=78 的原因）")
    for bad in ("世新大學", "中華郵政股份有限公司", "南投縣議會",
                "中央研究院", "國史館"):
        check(f"不含「{bad}」", bad not in allnames)
    check("無任何名稱以 大學/議會/公司 結尾",
          not [n for n in allnames
               if re.search(r"(大學|議會|公司|銀行|醫院)$", n)])

    # 🔴 2026-09-24 同日第二次踩同一個坑：排除 regex 綁了 `$`，
    #    而學校正式名稱是「國立岡山高級中**學**」—— `高中$` 一個都不 match。
    #    55 所高中混進 central3_top（佔 25%），39 所被判成有發補助。
    #    ⇒ 這條改成「出現即檢查」，不綁結尾。
    schools = [n for n in allnames
               if re.search(r"(中學|學校|大學|學院|高中|高職|國小|國中|"
                            r"專科|幼兒園)", n)]
    check("🔴 清單裡沒有任何學校（不綁結尾的檢查）",
          not schools, f"殘留 {len(schools)} 筆，例：{schools[:3]}")

    print("\n④ 存在證明（使用者要求：能證明它真的存在）")
    flat = [x for v in b.values() for x in v]
    withcode = [x for x in flat if x["evidence"]["org_code"]]
    withaddr = [x for x in flat if x["evidence"]["address"]]
    check(f"全部 {len(flat)} 筆都有機關代碼", len(withcode) == len(flat),
          f"缺 {len(flat) - len(withcode)}")
    check("有地址的 ≥ 99%", len(withaddr) / len(flat) >= 0.99,
          f"{len(withaddr)}/{len(flat)}")
    check("每筆 evidence 都帶 source_url",
          all(x["evidence"].get("source_url") for x in flat))
    check("機關代碼格式正確（10 碼英數）",
          all(re.fullmatch(r"[A-Z0-9]{10}", x["evidence"]["org_code"])
              for x in withcode))

    print("\n⑤ 🔴 welfare_hint 必須真的有作用（第一版全是 0）")
    hint_n = sum(1 for x in flat if x["welfare_hint"])
    check("hint 數量 > 0", hint_n > 0, f"實際 {hint_n}")
    check("hint 不是全部（否則等於沒篩）", hint_n < len(flat))
    check("衛福部社會及家庭署 hint=True",
          any(x["name"] == "衛生福利部社會及家庭署" and x["welfare_hint"]
              for x in flat))
    # 🔴 negative control：hint 不可靠這件事必須是真的
    energy = [x for x in flat if x["name"] == "經濟部能源署"]
    check("經濟部能源署存在", bool(energy))
    check("🔴 能源署 hint=False（證明 hint 會漏掉真的發補助的機關）",
          bool(energy) and not energy[0]["welfare_hint"],
          "若這條變綠代表 hint 改過，文件的警告要一起更新")

    print("\n⑥ 實際發過補助的機關都在 central3_top")
    top = {x["name"] for x in b["central3_top"]}
    for a in ("勞動部勞動力發展署", "勞動部勞工保險局",
              "衛生福利部國民健康署", "衛生福利部社會及家庭署",
              "衛生福利部中央健康保險署", "經濟部能源署"):
        check(f"{a}", a in top)

    print("\n⑦ 民間單位清單完整")
    orgs = ngo["ngo_from_mohw_pdf"]
    check("21 筆", len(orgs) == 21, f"實際 {len(orgs)}")
    check("項次 1~21 連續無缺",
          sorted(x["idx"] for x in orgs) == list(range(1, 22)))
    check("🔴 無幽靈機構（地址欄誤判產生的）",
          not [x for x in orgs if x["org"].startswith("樓")])
    check("名稱無重複", len({x["org"] for x in orgs}) == len(orgs))
    check("每筆都有 source_url",
          all(x.get("source_url") for x in orgs))
    check("慈濟在清單裡（第一版被表頭吃掉）",
          any("慈濟" in x["org"] for x in orgs))
    check("萬海名稱完整（非斷行殘片）",
          any(x["org"] == "財團法人萬海航運社會福利慈善事業基金會"
              for x in orgs))

    print("\n⑧ 🔴 文件數字必須與 JSON 一致（第一版就是這裡錯）")
    for label, n in (("中央二級", len(b["central2"])),
                     ("三級直屬部會", len(b["central3_top"])),
                     ("地方一級局處", len(b["local_dept"])),
                     ("民間單位", len(orgs))):
        check(f"文件提到 {label} = {n}", f"**{n}**" in doc or f"| {n} |" in doc,
              "文件與 JSON 對不起來 —— 重跑腳本並更新文件")
    total = sum(len(v) for v in b.values())
    check(f"文件合計 = {total}", f"**{total:,}**" in doc or f"{total:,}" in doc,
          f"實際合計 {total}")

    print("\n⑨ 補助證據（e政府申辦服務）")
    ev_path = HERE / "agencies_with_benefits.json"
    if not ev_path.exists():
        check("agencies_with_benefits.json 存在", False,
              "先跑 agency_benefit_evidence.py")
    else:
        bev = json.loads(ev_path.read_text())
        ags = bev["agencies"]
        check("有補助證據的機關 > 0", len(ags) > 0)
        check("每個機關都帶 evidence（機關代碼）",
              all(a["evidence"].get("org_code") for a in ags.values()))
        check("每個機關都有至少一筆服務",
              all(a["benefit_service_count"] > 0 for a in ags.values()))
        check("_meta 記錄了來源網址",
              bev["_meta"].get("source_url", "").startswith("https://data.gov.tw"))
        check("🔴 _meta 明寫「不能證明沒有」的警告",
              "不能證明" in bev["_meta"].get("caveat", ""))
        # 🔴 negative control：e 政府收錄不全這件事必須是真的
        for miss in ("衛生福利部國民健康署", "經濟部能源署"):
            check(f"🔴 {miss} 在 e政府查無（證明資料不完整）",
                  miss not in ags,
                  "若這條變綠代表 e政府補上了，流程文件的警告要更新")
        for has in ("勞動部勞工保險局", "衛生福利部中央健康保險署"):
            check(f"{has} 有證據", has in ags)

        print("\n⑩ 🔴 流程文件的實查結果必須與資料庫一致")
        # ⚠️ 這節原本比對「e政府證據數」，但 2026-09-24 逐一查證完成後，
        #    流程文件改記**實查結果**（478 個機關的有無），
        #    那才是使用者會看的數字。e政府證據數只是中間產物。
        flow = (HERE.parent / "福利清查流程.md").read_text()
        check("流程文件已改記實查結果（非 e政府中間數字）",
              "全部查完" in flow and "478" in flow,
              "流程文件還停在 e政府階段 —— 重跑查證並更新")

    print("\n⑪ 🔴 查證結果的證據純度（資料庫）")
    try:
        import psycopg2
        with psycopg2.connect(dbname="welfare_check") as c, c.cursor() as cur:
            cur.execute("""SELECT count(*) FROM agency_verification
                            WHERE stage <= 4 AND status = 'pending'""")
            pending = cur.fetchone()[0]
            check("階段 1-4 全部查完", pending == 0, f"還有 {pending} 未查")

            # 🔴 2026-09-24：39 筆（11%）的證據來自學校／採購網／公報／
            #    法規庫 —— 「在官方網域」不等於「在講這個機關」。
            #    ⚠️ 例外：`data.gov.tw/dataset/146973` 是 e 政府申辦服務
            #    「資料集本身」，那是合法來源（60 筆靠它證實），
            #    不可跟「拿某個資料集頁面當某機關的證據」混為一談。
            cur.execute(r"""SELECT count(*) FROM agency_verification
                             WHERE has_benefit
                               AND evidence_url <>
                                   'https://data.gov.tw/dataset/146973'
                               AND evidence_url ~
                             '(\.edu\.tw|gazette\.nat|ppg\.ly|president\.gov'
                             '|data\.gov\.tw|data\.nat|laws?\..*gov\.tw'
                             '|pcc\.gov)'""")
            bad_src = cur.fetchone()[0]
            check("🔴 沒有不可靠來源（學校/採購網/公報/法規庫）",
                  bad_src == 0, f"殘留 {bad_src} 筆")

            cur.execute("""SELECT count(*) FROM agency_verification
                            WHERE has_benefit
                              AND (evidence_url IS NULL OR evidence_url = '')""")
            no_url = cur.fetchone()[0]
            check("每個「有補助」的機關都有證據網址",
                  no_url == 0, f"{no_url} 筆缺網址")

            # 🔴 negative control：has_benefit=False 不該存在 ——
            #    我們從不寫 False，因為「查不到」≠「沒有」
            cur.execute("""SELECT count(*) FROM agency_verification
                            WHERE has_benefit IS FALSE""")
            false_n = cur.fetchone()[0]
            check("🔴 沒有任何機關被標成『確定沒有補助』",
                  false_n == 0,
                  f"{false_n} 筆 —— 「查不到」不可寫成 False")
            cur.execute("""SELECT stage, count(*) FILTER (WHERE has_benefit),
                                  count(*)
                             FROM agency_verification
                            WHERE stage <= 4 GROUP BY 1 ORDER BY 1""")
            rows = cur.fetchall()
            # 🔴 流程文件的表格數字必須真的來自資料庫，不是手打的。
            #    2026-09-24 第一版就是文件與檔案對不起來（詳見單位清查 ⑤）。
            flow_txt = (HERE.parent / "福利清查流程.md").read_text()
            for stage, yes, total in rows:
                check(f"流程文件階段{stage}：有補助 {yes} / 合計 {total}",
                      f"**{yes}**" in flow_txt and f"| {total} |" in flow_txt,
                      "文件數字與資料庫對不起來 —— 重跑並更新")
            tot_yes = sum(r[1] for r in rows)
            tot_all = sum(r[2] for r in rows)
            check(f"流程文件合計：{tot_yes} / {tot_all}",
                  f"**{tot_yes}**" in flow_txt and f"**{tot_all}**" in flow_txt)

    except Exception as e:                      # pragma: no cover
        check("資料庫檢查可執行", False, str(e)[:120])

    print(f"\n{'=' * 46}\n通過 {ok}　失敗 {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
