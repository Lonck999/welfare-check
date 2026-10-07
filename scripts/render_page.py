#!/usr/bin/env python3
"""把一個 SPA 頁面渲染後抽出純文字（給「網址是否真的對應這筆資料」的查證用）。

🔴 為什麼需要它：桃園 e-services 的單筆頁面是 SPA ——
`web_extract` 只拿到頁尾（約 150 字），看起來像「死網址／空殼」，
但渲染後有 1,200+ 字的完整內容。
⚠️ 用 `web_extract` 的結果判斷那個網址死活會得到相反的結論。

🔴 一定要 kill 子行程：55 支 spawn Chrome 的腳本都沒做，
留下永生瀏覽器且完全靜默（實測 75 行程 / 10.7 GB）。

用法：
    render_page.py <url> [<url> ...] [--json out.json] [--budget 12000]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
import shutil

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def strip_html(raw: str) -> str:
    s = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"\s+", " ", t).strip()


def render(url: str, budget: int = 12000, timeout: int = 90) -> tuple[str, str]:
    """回傳 (<title>, 純文字)。失敗時 text 為空字串。"""
    profile = tempfile.mkdtemp(prefix="render_page_")
    try:
        p = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
             "--no-default-browser-check", f"--virtual-time-budget={budget}",
             "--dump-dom", f"--user-data-dir={profile}", url],
            capture_output=True, text=True, timeout=timeout,
        )
        raw = p.stdout
    except subprocess.TimeoutExpired:
        return ("", "")
    finally:
        # 🔴 不可省：逾時的 Chrome 不會自己死
        subprocess.run(["pkill", "-f", profile], capture_output=True)
        shutil.rmtree(profile, ignore_errors=True)
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    return (html.unescape(m.group(1)).strip() if m else "", strip_html(raw))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--json")
    ap.add_argument("--budget", type=int, default=12000)
    ap.add_argument("--chars", type=int, default=0,
                    help="印出前 N 字（0 = 只印長度與標題）")
    args = ap.parse_args()

    out = []
    for u in args.urls:
        title, text = render(u, args.budget)
        out.append({"url": u, "title": title, "chars": len(text), "text": text})
        print(f"[{len(text):>6} 字] {title or '(無標題)'}　{u}")
        if args.chars:
            print("   ", text[:args.chars].replace("\n", " "))
    if args.json:
        json.dump(out, open(args.json, "w"), ensure_ascii=False, indent=1)
        print(f"\n→ {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
