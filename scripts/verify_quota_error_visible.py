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
# 🔴 2026-10-01：前三條是「照著 regex 反寫」的案例 —— 它們永遠會過，
#    因為我是看著 regex 編出來的句子。真正的防線測不到。
case("firecrawl insufficient credits",
     "Payment Required: Failed to scrape. Insufficient credits to "
     "perform this request. For more credits, you can upgrade your plan",
     "", True)
case("quota exceeded", "API quota exceeded for this month", "", True)
case("credit limit", "You have reached your credit limit", "", True)

print("-- 🔴 MUST RAISE: 真實後端輸出（逐字貼上，不可改寫）--")
# 🔴 這一組是 2026-10-01 實際從後端收到的字串，不是我編的。
#    舊 regex 寫 `credit limit`，exa 說的是 **credits limit** ⇒ 差一個字母，
#    整條防線對 exa 無聲失效 —— 而換後端這件事沒有任何訊號提醒我重驗。
#
# 🔴 新案例的鐵律：**貼真的，不要照 regex 造。**
#    照 regex 造出來的案例只能證明 regex 等於它自己。
EXA_402 = ('Request failed with status code 402: {"requestId":'
           '"c117e66af492da330c281e739e9f5ccc","error":"You have exceeded '
           'your credits limit. Please top up to keep using Exa at '
           'dashboard.exa.ai","tag":"NO_MORE_CREDITS"}')
case("🔴 exa 402 原文（2026-10-01 實收）", EXA_402, "", True)

# 🔴 每條訊號各給一個「只觸發它自己」的案例 ——
#    上面那串同時命中 4 條（402／exceeded your credits／credits limit／
#    NO_MORE_CREDITS），任一條失效它都還是會過關。
case("只有 402 狀態碼", "Request failed with status code 402", "", True)
case("只有 tag", '{"tag":"NO_MORE_CREDITS"}', "", True)
case("只有 credits limit（複數）", "You have exceeded your credits limit.", "", True)
case("401 未授權（key 失效也不可當成空頁）",
     "Request failed with status code 401: invalid api key", "", True)
case("429 速率限制", "rate limit exceeded, retry later", "", True)

print("-- MUST NOT RAISE: genuinely empty page --")
case("empty page, no error", "", "", False)
case("404 not found", "Not Found (404)", "", False)
case("robots blocked", "Blocked by robots.txt", "", False)
# 🔴 negative control：404／403 這些「頁面真的沒了」的狀態碼
#    不可被新加的 `status code 40[12]` 誤殺 —— 誤殺會讓整批真空頁變成中斷。
case("🔴 403 禁止存取（不是配額）", "Request failed with status code 403", "", False)
case("🔴 404（不是配額）", "Request failed with status code 404", "", False)
case("🔴 400 參數錯", "Request failed with status code 400: bad url", "", False)

print("-- MUST NOT RAISE: page has content --")
case("normal page", "", "補助金額每月5,000元。" * 40, False)

print("")
print(str(ok) + "/" + str(tot))
sys.exit(0 if ok == tot else 1)
