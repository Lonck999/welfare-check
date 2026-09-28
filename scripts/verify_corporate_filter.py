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

print("")
print(str(ok) + "/" + str(tot))
sys.exit(0 if ok == tot else 1)
