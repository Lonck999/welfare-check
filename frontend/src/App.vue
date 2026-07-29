<script setup lang="ts">
import { onMounted, ref } from 'vue'
import WelfareForm from './components/WelfareForm.vue'
import ResultsView from './components/ResultsView.vue'
import LegalNotice from './components/LegalNotice.vue'
import { fetchFormOptions, submitCheck } from './api'
import type { CheckRequestBody, CheckResponse, FormOptions } from './types'

const step = ref<'loading-options' | 'form' | 'submitting' | 'results' | 'error'>('loading-options')
const options = ref<FormOptions | null>(null)
const result = ref<CheckResponse | null>(null)
const errorMessage = ref('')

async function loadOptions() {
  step.value = 'loading-options'
  try {
    options.value = await fetchFormOptions()
    step.value = 'form'
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '載入失敗'
    step.value = 'error'
  }
}

async function handleSubmit(body: CheckRequestBody) {
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
  <main class="app">
    <header class="app-header">
      <h1>台灣福利補助查詢助手</h1>
      <p>填寫基本資料，立即比對可能符合的福利、補助、優惠與計畫。</p>
    </header>

    <p v-if="step === 'loading-options'" class="status-msg">載入表單中…</p>

    <WelfareForm v-if="step === 'form' && options" :options="options" @submit="handleSubmit" />

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
  </main>
</template>
