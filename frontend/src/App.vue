<script setup lang="ts">
import { onMounted, ref } from 'vue'
import LandingPage from './components/LandingPage.vue'
import Questionnaire from './components/Questionnaire.vue'
import ResultsView from './components/ResultsView.vue'
import LegalNotice from './components/LegalNotice.vue'
import { fetchFormOptions, submitCheck } from './api'
import type { CheckResponse, FormOptions, QuestionnaireAnswers } from './types'

const step = ref<'landing' | 'loading-options' | 'form' | 'submitting' | 'results' | 'error'>('landing')
const options = ref<FormOptions | null>(null)
const result = ref<CheckResponse | null>(null)
const errorMessage = ref('')

/**
 * 首頁一載入就在背景預抓表單選項，使用者按下開始查詢時多半已經抓好，不用再等待載入畫面。
 * 若預抓失敗但使用者還在首頁（還沒按開始），不強制跳去錯誤畫面打斷閱讀，等他實際按下開始查詢時再重試。
 */
async function loadOptions() {
  try {
    options.value = await fetchFormOptions()
    if (step.value === 'loading-options') step.value = 'form'
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '載入失敗'
    if (step.value !== 'landing') step.value = 'error'
  }
}

function handleStart() {
  if (options.value) {
    step.value = 'form'
  } else {
    step.value = 'loading-options'
    loadOptions()
  }
}

async function handleSubmit(body: QuestionnaireAnswers) {
  step.value = 'submitting'
  try {
    result.value = await submitCheck(body)
    step.value = 'results'
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '查詢失敗'
    step.value = 'error'
  }
}

function restart() {
  result.value = null
  step.value = 'form'
}

onMounted(loadOptions)
</script>

<template>
  <main class="app" :class="{ 'app--landing': step === 'landing' }">
    <LandingPage v-if="step === 'landing'" @start="handleStart" />

    <template v-else>
      <header class="app-header">
        <h1>台灣福利補助查詢助手</h1>
        <p>填寫基本資料，立即比對可能符合的福利、補助、優惠與計畫。</p>
      </header>

      <p v-if="step === 'loading-options'" class="status-msg">載入表單中…</p>

      <Questionnaire v-if="step === 'form' && options" :options="options" @submit="handleSubmit" />

      <p v-if="step === 'submitting'" class="status-msg">查詢比對中，請稍候…</p>

      <ResultsView v-if="step === 'results' && result" :result="result" @restart="restart" />

      <div v-if="step === 'error'" class="error-box">
        <p>{{ errorMessage }}</p>
        <button type="button" class="secondary-btn" @click="loadOptions">重試</button>
      </div>

      <footer class="app-footer no-print">
        <p>本查詢結果是由 AI 整理各單位每個禮拜的最新資訊，每次更新時間為周日的凌晨 01:00，如果資訊有什麼需要我補充的請麻煩在信箱 joe22053814@gmail.com 與我聯繫，實際資格請以各單位最新公告為準。填表資料不會保留，查詢結束即清除。</p>
        <LegalNotice />
      </footer>
    </template>
  </main>
</template>
