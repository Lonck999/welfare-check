import * as Sentry from '@sentry/node'

// 表單資料含出生年月日、收入、財產、身心障礙/罕病狀態等敏感資訊，
// 不把使用者資訊或 HTTP 內容送給 Sentry，只保留錯誤堆疊本身。
// 只在正式環境（NODE_ENV=production，Railway 部署時會自動設定）才回報，避免本機開發雜訊灌爆免費額度。
if (process.env.SENTRY_DSN && process.env.NODE_ENV === 'production') {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    dataCollection: {
      userInfo: false,
      httpBodies: [],
    },
  })
}
