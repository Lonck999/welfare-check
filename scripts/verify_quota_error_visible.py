"""verify: 配額錯誤不可被當成「這頁沒內容」。

🔴 2026-09-29 踩雷：Firecrawl 額度用完時回
   'Payment Required: Insufficient credits to perform this request'，
   而 extract() 的重試清單只有 TUNNEL|timeout|proxy|502|503|429 ——
   ⇒ 不重試、直接回 ""，**看起來跟「政府沒公開這項補助」一模一樣**。
   那一輪 60 筆裡 50 筆被記成「找不到官方頁」，全是假的。

判準：配額/授權類錯誤必須 **raise**（大聲失敗），
      真的空頁必須 **回 ""**（安靜跳過）。
🔴 兩個方向都要測 —— 只測前者的話，「永遠都 raise」也會全綠。
"""
import json
import sys

sys.path.insert(0, "/Users/lonck/Agent/welfare-check/scripts")
import fetch_local_benefit as F  # noqa: E402

ok = 0
tot = 0


def case(label, err_text, content, expect_raise):
    """用假的 _run_tool 回傳值驗 extract() 的分支。"""
    global ok, tot
    tot += 1
    payload = {"results": [{"url": "https://x.gov.tw/a",
                            "content": content,
                            "error": err_text}]}
    orig = F._run_tool
    F._run_tool = lambda *a, **k: json.dumps(payload)
    raised = None
    try:
        out = F.extract("https://x.gov.tw/a", retries=1)
    except Exception as e:                                # noqa: BLE001
        raised = str(e)
        out = None
    finally:
        F._run_tool = orig
    good = (raised is not None) == expect_raise
    ok += good
    got = ("RAISE: " + raised[:46]) if raised else ("return %r" % (out or "")[:20])
    print(("  OK  " if good else "  BAD ") + label + " -> " + got
          + ("" if good else "  expect raise=%s" % expect_raise))


print("-- MUST RAISE: quota / payment errors --")
case("firecrawl insufficient credits",
     "Payment Required: Failed to scrape. Insufficient credits to "
     "perform this request. For more credits, you can upgrade your plan",
     "", True)
case("quota exceeded", "API quota exceeded for this month", "", True)
case("credit limit", "You have reached your credit limit", "", True)

print("-- MUST NOT RAISE: genuinely empty page --")
case("empty page, no error", "", "", False)
case("404 not found", "Not Found (404)", "", False)
case("robots blocked", "Blocked by robots.txt", "", False)

print("-- MUST NOT RAISE: page has content --")
case("normal page", "", "補助金額每月5,000元。" * 40, False)

print("")
print(str(ok) + "/" + str(tot))
sys.exit(0 if ok == tot else 1)
