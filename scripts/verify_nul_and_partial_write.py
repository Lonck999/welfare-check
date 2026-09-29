"""verify: 抽取出口必須清掉控制字元，且單筆寫入失敗不可中斷整批。

🔴 2026-09-29 踩雷（換 extract_backend firecrawl → exa 後才出現）：
   exa 回的內容含 NUL (0x00) → psycopg2 直接
   `ValueError: A string literal cannot contain NUL (0x00) characters`
   ⇒ 整支腳本當場掛掉，**前 17 筆已寫入、後 35 筆一筆都沒跑**。
   ⚠️ log 尾巴只有 traceback，「做了一半」完全沒有訊號 ——
      下次看到「空殼少了 17」會以為那批本來就只有 17 筆。

兩個方向都要測：
  ① extract() 必須把控制字元清掉（含 NUL）
  ② 正常內容不可被動到（不能為了清 NUL 把中文/換行也吃掉）
"""
import json
import sys

sys.path.insert(0, "/Users/lonck/Agent/welfare-check/scripts")
import fetch_local_benefit as F  # noqa: E402

ok = 0
tot = 0


def chk(label, cond, detail=""):
    global ok, tot
    tot += 1
    ok += bool(cond)
    print(("  OK  " if cond else "  BAD ") + label
          + (("  " + detail) if detail else ""))


def run_extract(content):
    payload = {"results": [{"url": "https://x.gov.tw/a",
                            "content": content, "error": None}]}
    orig = F._run_tool
    F._run_tool = lambda *a, **k: json.dumps(payload)
    try:
        return F.extract("https://x.gov.tw/a", retries=1)
    finally:
        F._run_tool = orig


print("-- MUST strip control chars --")
body = "補助金額每月5,000元，請攜帶身分證。" * 12          # >200 chars
out = run_extract(body[:120] + "\x00" + body[120:])
chk("NUL removed", "\x00" not in out, "len=%d" % len(out))
chk("content preserved", "5,000" in out and "身分證" in out)

out2 = run_extract(body[:60] + "\x01\x07\x1f\x7f" + body[60:])
chk("other control chars removed",
    not any(c in out2 for c in "\x01\x07\x1f\x7f"))

print("-- MUST NOT damage normal text --")
plain = run_extract(body)
chk("plain text unchanged", plain == body,
    "in=%d out=%d" % (len(body), len(plain)))
nl = "第一行\n第二行\r\n第三行\t有tab\n" * 12
kept = run_extract(nl)
chk("newlines and tabs kept",
    "\n" in kept and "\t" in kept and "第三行" in kept)

print("-- postgres would accept the result --")
chk("no NUL anywhere in stripped output",
    "\x00" not in out and "\x00" not in out2 and "\x00" not in kept)

print("-- batch must not abort on a single write failure --")
src = open("/Users/lonck/Agent/welfare-check/scripts/refetch_empty_shells.py",
           encoding="utf-8").read()
chk("UPDATE wrapped in try/except",
    "try:" in src and "conn.rollback()" in src
    and "寫入失敗（已跳過這筆，整批繼續）" in src)
chk("failed count is initialised", "ok = miss = failed = 0" in src)
chk("failed count reported in summary", "寫入失敗 {failed}" in src)
chk("nonzero exit when any write failed", "return 1 if failed else 0" in src)

print("")
print(str(ok) + "/" + str(tot))
sys.exit(0 if ok == tot else 1)
