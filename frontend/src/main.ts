import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import * as Sentry from '@sentry/vue'

const app = createApp(App)

const dsn = import.meta.env.VITE_SENTRY_DSN
if (dsn && import.meta.env.PROD) {
  Sentry.init({
    app,
    dsn,
    // 表單會收集出生年月日、收入、財產、身心障礙/罕病狀態等敏感資料，
    // 不把使用者資訊或 HTTP 內容送給 Sentry，只保留錯誤堆疊本身。
    sendDefaultPii: false,
  })
}

app.mount('#app')
