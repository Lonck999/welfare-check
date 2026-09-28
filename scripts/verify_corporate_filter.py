"""verify is_corporate_page: real texts, both directions."""
import sys
sys.path.insert(0, '/Users/lonck/Agent/welfare-check/scripts')
from refetch_empty_shells import is_corporate_page

ok = 0
tot = 0


def t(txt, exp, label):
    global ok, tot
    tot += 1
    r = is_corporate_page(txt)
    good = (r == exp)
    ok += good
    print(("  OK  " if good else "  BAD ") + label + " -> " + str(r)
          + ("" if good else "  expect " + str(exp)))


print("-- MUST BLOCK: corporate pages that slipped through --")
t("補助申請計畫，申請金額在新臺幣兩百萬元。(二)申請單位提送之領據，應符合下列規定："
  "領據上須書名「臺中巿政府環境保護局」抬頭、受補助單位名稱及統一編號",
  True, "taichung energy (corp)")
t("雇主應於僱用之日起30日內檢附下列文件申請：1.申請書 2.公司登記證明 "
  "3.受補助單位之銀行帳戶封面影本", True, "employer subsidy")
t("補助總金額以20萬元為上限。二、申請資格及條件：(一)雇主已依照職能復健專業機構"
  "建議提供輔助設施。雇主應於核定後檢附領據", True, "chiayi workplace (corp)")

print("-- MUST PASS: individual benefits that mention employers --")
t("為鼓勵失業勞工受僱特定行業從事工作。符合失業勞工條件之一者：1.連續失業30日以上 "
  "2.非自願離職者。經由公立就業服務機構推介，經雇主僱用後，其受僱期間得向"
  "公立就業服務機構申請核發就業獎勵津貼", False, "queue-gong incentive (person)")
t("服務對象：1.失業高齡者。失業勞工向公立就業服務機構辦理求職登記。"
  "失業勞工經就業服務機構推介予雇主僱用，並於同一事業單位就業滿30日",
  False, "cross-region job (person)")
t("補助遭受職場性騷擾之被害人運用心理諮商，及協助雇主提供或轉介被害人運用"
  "性別平等工作法第13條第2項所定之心理諮商，以保障受僱者及求職者權益",
  False, "harassment counselling (person)")
t("經需求評估中心及受補助單位專業團隊評估適合於社區居住與生活者。"
  "實際居住本市且年滿18歲以上者，領有身心障礙證明者", False, "community living (person)")
t("每一新生兒補助新臺幣2萬元，由新生兒之父或母親自向戶籍所在地公所申請，"
  "市民請檢附戶口名簿", False, "birth grant (person)")
t("中低收入戶瓦斯費補助，每戶每月300元，請民眾攜帶身分證親自到區公所辦理",
  False, "gas subsidy (person)")

print("-- MUST BLOCK: real cached page (16,341 chars, not synthetic) --")
# 🔴 人造文本會不知不覺照著判準寫 —— 真實頁面才抓得到判準的盲區。
#    ⚠️ 這頁曾溜過第一版濾網：它寫「雇主**已依照**…」與
#       「**雇主提供**…補助申請書」，而我列的片語是「雇主應於/檢附/申請」。
_REAL = ("/Users/lonck/.hermes/cache/web/ly.chiayi.gov.tw-9d34c6e86a.md")
try:
    with open(_REAL, encoding="utf-8") as f:
        t(f.read(), True, "chiayi employer subsidy (REAL page)")
except FileNotFoundError:
    print("  SKIP (cached page missing) - run web_extract on"
          " https://ly.chiayi.gov.tw/cl.aspx?n=9220")

# 🔴 第二個真實頁面（2026-09-28 第三輪）：花蓮「新建托兒設施最高補助500萬」
#    ⚠️ 它溜過前兩版濾網 —— 「事業單位」出現 10 次但全是我沒列的句型
#       （「請有意申請經費補助之事業單位」「鼓勵事業單位提供員工托兒服務」），
#       而「縣民」兩次都在**導覽選單**「[縣民園地](...)」裡，
#       讓「1 命中 + 無個人視角」那條規則失效。
_REAL2 = ("/Users/lonck/.hermes/cache/web/www.hl.gov.tw-5c0f214cb0.md")
try:
    with open(_REAL2, encoding="utf-8") as f:
        t(f.read(), True, "hualien childcare facility 500w (REAL page)")
except FileNotFoundError:
    print("  SKIP (cached page missing) - run web_extract on"
          " https://www.hl.gov.tw/News_Content.aspx?n=32725&s=180712")

print("-- MUST PASS: real cached PERSONAL benefit pages (false-positive check) --")
# 🔴 這一段是整支測試最重要的部分 —— 誤殺個人補助 = 弱勢者查不到
#    自己能領的錢，比留一筆法人資料嚴重得多。
#
# ⚠️ 2026-09-28 實測抓到「密度判準」根本上是錯的（已丟棄），兩個原因：
#    ① 長度偏誤：花蓮社會處那頁是 **146,466 字元的整站列表**，
#       自然累積 13 次法人詞 —— 越長的頁面越容易被誤判，調門檻沒用。
#    ② 🔴 「申請單位」有兩種**相反**的意思：
#         「受理申請單位：兒童發展通報轉介中心」← 民眾去申請的窗口
#         「請有意申請補助之事業單位提出」      ← 申請人是法人
#    ⇒ 改用「申請人身分的直接宣告」（補助對象/申請資格 + 法人主體）。
import glob as _glob
for _pat, _tag in [("sa.hl.gov.tw", "hualien caregiver 5000"),
                   ("law.chiayi.gov.tw", "chiayi emergency relief"),
                   ("service.ntpc.gov.tw", "ntpc housing repair 50k"),
                   ("older.kcg.gov.tw", "kaohsiung caregiver")]:
    _fs = sorted(_glob.glob("/Users/lonck/.hermes/cache/web/" + _pat + "*.md"))
    # 🔴 寬 glob 會抓到同網域的**別的快取檔**（實測 www.hl.gov.tw-* 有 4 個，
    #    corp_subj 從 11 掉到 1），驗證就會拿錯檔案卻照樣全綠。
    #    ⇒ 挑最大的那個（完整頁面），並印出實際用了哪一個。
    if len(_fs) > 1:
        _fs = [max(_fs, key=lambda p: __import__("os").path.getsize(p))]
    if not _fs:
        print("  SKIP (cached page missing): " + _tag)
        continue
    with open(_fs[0], encoding="utf-8") as f:
        t(f.read(), False, _tag + " (REAL page)")

# ═══ 植入驗證結果（2026-09-28 實測）═══
# 🔴 兩個真實案例各靠**不同**規則擋下，這正是留多條的理由：
#      嘉義雇主補助   → form（「雇主提供…補助申請書」）＋ clause（「(一)雇主」）
#      花蓮托兒設施   → count（「雇用人數達100人以上的雇主」）
#
# 單條植入的結果與解讀：
#      關掉 count  → 14/15  ✅ 花蓮只靠它，有獨立鑑別力
#      關掉 form   → 15/15  ⚠️ 不是無效 —— 嘉義還有 clause 頂著
#      關掉 clause → 15/15  ⚠️ 同上，嘉義還有 form 頂著
#      關掉 decl / req → 15/15  ⚠️ 這批樣本沒觸發到它們
#
# 🔴 依 AGENTS.md 判準：植入不掉分要分清兩種情況 ——
#    「測試漏了」要補斷言，「植入無害」要註明原因。
#    這裡 form/clause 屬於**互相備援**（同一頁兩條都命中），
#    decl/req 屬於**樣本未觸發**，兩者都不該補假斷言湊掉分。
#
# ⚠️ 過程踩到三個假訊號，每一個都讓驗證看起來成功：
#    ① `__pycache__` 讓還原後仍是舊行為 → 每次跑前 rm -rf scripts/__pycache__
#    ② glob "www.hl.gov.tw-*" 抓到**別的快取檔**（corp_subj 11 → 1），
#       害我一度以為三條規則全失效。🔴 指定完整檔名或取最大檔。
#    ③ 🔴 最嚴重：`統一編號` 當法人證據 —— 政府網站**頁尾都有**，
#       嘉義急難救助那頁 3,700 字也命中 ⇒ 完全沒有鑑別力，卻誤殺個人補助。

print("")
print(str(ok) + "/" + str(tot))
sys.exit(0 if ok == tot else 1)
