#!/usr/bin/env python3
"""匯入縣市「社會福利/救助項目」開放資料集 → benefits。

🔴 為什麼走這條路（2026-09-24 定案，Lonck 的問題逼出來的）：
   搜尋引擎回的是「符合這句話的頁」，**不會回「全部」**——
   你永遠不知道自己漏了什麼。今天試抓命中率只有 25%。
   ⇒ 要做到「不漏」，來源必須**能被列舉**（有完整清單可下載）。

🔴 這批資料的欄位是政府統一標準（實測臺北/嘉義/臺南三市一致）：
   補助名稱／年齡上下限／設籍條件／身份1~3／收入條件／動產／不動產／
   其他條件／應備文件／收件洽辦單位／聯絡電話／詳細資訊連結
   —— 幾乎直接對應我們的 eligibility_conditions + benefit_documents
      + benefit_locations，不必再靠搜尋猜。

⚠️ 但它只涵蓋**社會救助類**。醫療、就業、住宅、一般優惠都不在裡面，
   那些需要另外的列舉來源（勞動部、衛福部、各縣市「福利自己查」）。
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import urllib.request
from typing import Any

import psycopg2

# 🔴 來源清單：每個縣市的「社會福利/救助項目」開放資料下載網址。
#    ⚠️ 必須是**資料下載網址**，不是 data.gov.tw 的頁面網址
#    （那頁是 JS 渲染的，urllib 抓不到連結）。
SOURCES: dict[str, dict[str, str]] = {
    "臺南市": {
        "url": "https://soa.tainan.gov.tw/Api/Service/Get/"
               "d1ba24c7-7c97-420d-9f35-ff95ac9dd36d",
        "dataset": "https://data.gov.tw/dataset/79613",
        "agency": "臺南市政府社會局",
    },
    "嘉義市": {
        "url": "https://data.chiayi.gov.tw/opendata/api/getResource?"
               "oid=deb7f8fb-7de2-4a84-aca0-8bdb89614798&"
               "rid=af79b45a-5853-4ec3-a100-cf616cb840cb",
        "dataset": "https://data.gov.tw/dataset/109139",
        "agency": "嘉義市政府社會處",
    },
    "臺北市": {
        "url": "https://data.taipei/api/dataset/"
               "246337a0-751e-4523-a6c7-c185119b13d8/resource/"
               "549a3347-df6e-4bed-b818-368210d01544/download",
        "dataset": "https://data.gov.tw/dataset/129839",
        "agency": "臺北市政府社會局",
    },
}

# 欄位別名：各縣市欄位名有小差異（臺北 14 欄、嘉義/臺南 17 欄）
ALIAS: dict[str, tuple[str, ...]] = {
    "name": ("補助名稱",),
    "age_min": ("補助對象年齡下限",),
    "age_max": ("補助對象年齡上限",),
    "county_cond": ("設籍條件",),
    "income_max": ("收入條件每人每月上限", "收入條件每人每月上限金額"),
    "movable_max": ("動產條件每人上限",),
    "realty_max": ("不動產條件每戶上限",),
    "other": ("其他條件",),
    "docs": ("應備文件",),
    "office": ("收件洽辦單位",),
    "phone": ("聯絡電話", "聯繫方式"),
    "ext": ("分機",),
    "link": ("詳細資訊[連結]", "詳細資訊網址", "詳細資訊"),
}
IDENTITY_KEYS = ("身份1", "身份2", "身份3", "身份")


def pick(row: dict[str, Any], key: str) -> str:
    for k in ALIAS[key]:
        if k in row and str(row[k]).strip():
            return str(row[k]).strip()
    return ""


def to_int(s: str) -> int | None:
    """🔴 轉不出來就回 None，不可預設 0 —— 0 會變成
    『收入上限 0 元』這種沒人符合的條件，而且完全不報錯。"""
    s = re.sub(r"[,\s元]", "", s or "")
    return int(s) if re.fullmatch(r"\d+", s) else None


def fetch(url: str) -> list[dict[str, Any]]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=60).read()
    txt = raw.decode("utf-8-sig", "replace")
    try:
        d = json.loads(txt)
        return d.get("data", d) if isinstance(d, dict) else d
    except json.JSONDecodeError:
        return list(csv.DictReader(io.StringIO(txt)))


def build_eligibility(row: dict[str, Any], county: str) -> dict[str, Any]:
    """對應到既有的 eligibility_conditions 結構。

    🔴 鍵名必須與現有 491 筆一致（ageMin/ageMax/counties/
       incomeThreshold/requiredIdentities）—— 自己另創鍵名的話
       比對程式查不到，而且**不會報錯，只會少給補助**。
    """
    e: dict[str, Any] = {"counties": [county]}
    if (v := to_int(pick(row, "age_min"))) is not None:
        e["ageMin"] = v
    if (v := to_int(pick(row, "age_max"))) is not None:
        e["ageMax"] = v
    if (v := to_int(pick(row, "income_max"))) is not None:
        e["incomeMonthlyMax"] = v
    if (v := to_int(pick(row, "movable_max"))) is not None:
        e["movableAssetsMax"] = v
    if (v := to_int(pick(row, "realty_max"))) is not None:
        e["realEstateMax"] = v
    ids = [str(row[k]).strip() for k in IDENTITY_KEYS
           if k in row and str(row[k]).strip()]
    if ids:
        e["requiredIdentities"] = ids
    if other := pick(row, "other"):
        e["otherConditions"] = other[:500]
    return e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--county", required=True, choices=list(SOURCES))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    src = SOURCES[args.county]
    rows = fetch(src["url"])
    print(f"{args.county}：抓到 {len(rows)} 筆")

    # 🔴 來源自己就有重複（實測臺南「兒童與少年未來教育及發展帳戶」
    #    出現兩次）—— 不去重會在資料庫裡留下兩筆一模一樣的補助。
    seen: set[str] = set()
    uniq: list[dict[str, Any]] = []
    dup = 0
    for r in rows:
        nm = pick(r, "name")
        if not nm:
            continue
        key = re.sub(r"\s+", "", nm)
        if key in seen:
            dup += 1
            continue
        seen.add(key)
        uniq.append(r)
    print(f"  來源自身重複 {dup} 筆 → 去重後 {len(uniq)} 筆")

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    # 🔴 與現有資料比對：同縣市同名視為已存在
    cur.execute("SELECT name FROM benefits WHERE county = %s", (args.county,))
    existing = {re.sub(r"\s+", "", n) for (n,) in cur.fetchall()}

    new, collide = [], []
    for r in uniq:
        key = re.sub(r"\s+", "", pick(r, "name"))
        (collide if key in existing else new).append(r)
    print(f"  與現有 {len(existing)} 筆比對："
          f"新增 {len(new)}　已存在 {len(collide)}")

    if collide:
        print("  已存在的（不覆蓋，保留舊資料）：")
        for r in collide[:5]:
            print(f"    · {pick(r, 'name')[:34]}")

    print("\n  新增樣本（前 3 筆）：")
    for r in new[:3]:
        e = build_eligibility(r, args.county)
        print(f"    · {pick(r, 'name')[:32]}")
        print(f"      資格 {json.dumps(e, ensure_ascii=False)[:96]}")
        print(f"      洽辦 {pick(r, 'office')[:28]}　"
              f"文件 {'有' if pick(r, 'docs') else '🔴 無'}")

    if not args.apply:
        print("\n（dry-run，未寫入。加 --apply 才會真的寫）")
        return 0

    ins = 0
    for r in new:
        nm = pick(r, "name")
        elig = build_eligibility(r, args.county)
        link = pick(r, "link") or src["dataset"]
        phone = pick(r, "phone")
        if ext := pick(r, "ext"):
            phone = f"{phone} 分機 {ext}"
        # 🔴 source_excerpt 存**來源原文**（NOT NULL），不可塞空字串假裝有
        excerpt = " ／ ".join(
            f"{k}：{str(r[k]).strip()[:120]}"
            for k in ("身份1", "身份2", "身份3", "其他條件", "應備文件")
            if k in r and str(r[k]).strip())[:900] or f"{src['dataset']} 開放資料"
        cur.execute("""
            INSERT INTO benefits
              (name, agency, county, description, search_group,
               application_period, eligibility_conditions, source_url,
               source_excerpt, last_verified_date, is_active, deadline_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s,
                    CURRENT_DATE, true, 'unknown')
            RETURNING id""",
            (nm, src["agency"], args.county,
             f"{args.county}{nm}。"
             + (f"其他條件：{pick(r, 'other')[:300]}"
                if pick(r, "other") else ""),
             "現金與生活補助類",
             "",                       # 🔴 來源沒有期限欄位 → 留空，不猜
             json.dumps(elig, ensure_ascii=False), link, excerpt))
        bid = cur.fetchone()[0]
        ins += 1
        if docs := pick(r, "docs"):
            for d in re.split(r"\n|\d+\.\s*|、", docs):
                d = d.strip()
                if len(d) > 3:
                    cur.execute("""INSERT INTO benefit_documents
                                     (benefit_id, document_name, obtain_location)
                                   VALUES (%s, %s, %s)""",
                                (bid, d[:200], pick(r, "office")[:200] or None))
        if office := pick(r, "office"):
            cur.execute("""INSERT INTO benefit_locations
                             (benefit_id, name, phone)
                           VALUES (%s, %s, %s)""",
                        (bid, office[:200], phone[:100] or None))
    conn.commit()
    print(f"\n✅ 寫入 {ins} 筆")
    return 0


if __name__ == "__main__":
    sys.exit(main())
