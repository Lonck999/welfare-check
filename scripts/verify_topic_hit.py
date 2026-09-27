import sys; sys.path.insert(0,'/Users/lonck/Agent/welfare-check/scripts')
from refetch_empty_shells import topic_hit
ok=0; tot=0
def t(txt, topic, exp, label):
    global ok,tot; tot+=1
    r=topic_hit(txt,topic); good=(r==exp); ok+=good
    print(("  OK  " if good else "  BAD ")+label+" -> "+str(r)+("" if good else "  expect "+str(exp)))

print("-- MUST BLOCK (real cases that slipped through) --")
t("補助項目分別是窗型冷氣（或分離式冷氣）：2萬元。設備汰換與智慧用電補助對象：集合住宅、服務業及機關與學校，汰換老舊空調、照明設備及建置能管系統",
  "環保節能補助（電動機車地方加碼）", False, "cold-air page vs e-scooter")
t("最高8萬元補助節能設備，冷氣與照明燈具汰換",
  "環保節能補助（電動機車地方加碼）", False, "8万 node cold-air")
t("補助金額依托育類型與子女人數不同，最高可達15,000元，托育人員或幼兒園",
  "照顧者現金津貼（地方明細）", False, "childcare vs caregiver")
t("冷氣汰換補助：每額定總冷氣能力1kW補助2,500元，照明燈具每盞750元",
  "瓦斯費補助（地方明細）", False, "cold-air vs gas")

print("-- MUST PASS (correct pages) --")
t("電動機車購車補助每台最高3,000元，汰舊換新加碼",
  "環保節能補助（電動機車地方加碼）", True, "real e-scooter page")
t("本縣電動自行車購車補助，每輛補助3,000元",
  "電動自行車購車補助（地方加碼）", True, "e-bike page")
t("特別照顧津貼：照顧者每月補助5,000元，需親自照顧中低收入老人",
  "照顧者現金津貼（地方明細）", True, "real caregiver page")
t("中低收入戶瓦斯費補助，每戶每月補助300元",
  "瓦斯費補助（地方明細）", True, "real gas page")
t("重陽敬老禮金每人2,000元，敬老卡加值點數",
  "老人其他福利（重陽禮金/敬老卡，地方明細）", True, "chongyang gift")
t("蘭嶼綠島居民航空票價補貼，每趟補助500元",
  "離島居民航空票價補貼（蘭嶼/綠島）", True, "orchid island")
t("生育津貼每一新生兒補助2萬元",
  "生育獎勵金（地方加碼）", True, "birth (label-only bracket)")
t("65歲以上老人健保費補助全額negative",
  "醫療與健保補助（65歲以上健保費地方加碼）", True, "health insurance 65+")
print("")
print(str(ok)+"/"+str(tot))
sys.exit(0 if ok==tot else 1)
