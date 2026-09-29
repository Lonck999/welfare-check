"""verify: 語意單位不可被 2-gram 拆碎（topic_hit 的第六類錯誤）。

🔴 2026-09-29 踩雷（第六類「看起來正常的錯誤資料」）：
   新竹縣「照顧者現金津貼」抓到**敬老卡點數新聞**
   （敬老卡 13 次、愛心卡 14 次，🔴「照顧者」0 次、「津貼」0 次），
   只因為那頁有 1 次「長照**照顧**」——
   核心詞「照顧者現金」被切成 照顧/顧者/者現/現金，「照顧」就過關了。

   🔴「照顧者」是**領錢的人**，「照顧」是任何照護語境 ——
      2-gram 把這個區別磨掉了。這是第二次（上次「環保節能」沾到冷氣）。

⇒ Lonck 選 B：保留 2-gram，但語意單位整串比對。

🔴 難點在**同一個語意單位有多種官方寫法**：
   第一版只寫「照顧者」，立刻誤殺花蓮那筆**正確**的補助頁 ——
   官方標題是「醫療及住院**照顧費**用補助」、內文「特別**照顧津貼**」，
   「照顧者」出現 0 次，而「照顧」出現 14 次。
   ⚠️ 跟被擋下的敬老卡新聞（照顧 1 次）只差在「照顧」後面接什麼字。
   ⇒ 必須列成**同義群組**，群組內任一寫法整串命中即可。

🔴 兩個方向都要測：
   ① 主題不符的頁面必須擋下（用真實踩雷頁）
   ② 用詞不同但主題正確的頁面必須放行（誤殺 = 弱勢者查不到能領的錢）
"""
import sys

sys.path.insert(0, "/Users/lonck/Agent/welfare-check/scripts")
from refetch_empty_shells import topic_hit  # noqa: E402

FIX = "/Users/lonck/Agent/welfare-check/tests/fixtures/"
ok = 0
tot = 0


def t(fn, topic, expect, label):
    global ok, tot
    tot += 1
    try:
        with open(FIX + fn, encoding="utf-8") as f:
            txt = f.read()
    except FileNotFoundError:
        print("  SKIP (fixture missing): " + fn)
        return
    got = topic_hit(txt, topic)
    good = (got == expect)
    ok += good
    print(("  OK  " if good else "  BAD ") + label + " -> " + str(got)
          + ("" if good else "  expect " + str(expect)))


CARE = "照顧者現金津貼（地方明細）"

print("-- MUST BLOCK: wrong topic that only shares a 2-gram --")
t("exa_hsinchu_eldercard_news.txt", CARE, False,
  "hsinchu elder-card news (照顧 x1, 照顧者 x0)")

print("-- MUST PASS: correct topic worded differently --")
# 🔴 這兩筆是 B 方案的關鍵 —— 只寫「照顧者」會把它們誤殺
t("exa_hualien_hospital_care.txt", CARE, True,
  "hualien 住院照顧費 (照顧者 x0, 照顧 x14)")
t("exa_taipei_caregiver.txt", CARE, True, "taipei caregiver")
t("exa_kaohsiung_caregiver.txt", CARE, True, "kaohsiung caregiver")
t("exa_keelung_caregiver.txt", CARE, True, "keelung caregiver")

print("-- synthetic: semantic unit must be whole, not 2-gram --")
LONG = "本補助之申請請洽區公所。" * 20        # 撐過長度門檻用


def syn(body, topic, expect, label):
    global ok, tot
    tot += 1
    got = topic_hit(body, topic)
    good = (got == expect)
    ok += good
    print(("  OK  " if good else "  BAD ") + label + " -> " + str(got)
          + ("" if good else "  expect " + str(expect)))


syn("長期照顧服務資源介紹，照顧管理專員將協助評估。" + LONG,
    CARE, False, "『照顧』but no unit -> block")
syn("中低收入老人特別照顧津貼，每月發給照顧者5,000元。" + LONG,
    CARE, True, "『特別照顧』+『照顧者』-> pass")
syn("本市敬老卡點數自10月起翻倍。" + LONG,
    "老人其他福利（重陽禮金/敬老卡，地方明細）", True,
    "敬老卡 topic on 敬老卡 page -> pass")
syn("本縣冷氣汰換補助，每kW補助2,500元，另有照明燈具汰換。" + LONG,
    "環保節能補助（電動機車地方加碼）", False,
    "cold-air page vs 電動機車 -> block")

print("")
print(str(ok) + "/" + str(tot))
sys.exit(0 if ok == tot else 1)
