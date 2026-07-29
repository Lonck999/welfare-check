<script setup lang="ts">
import type { BenefitResult, CheckResponse } from '../types'
import { downloadReport } from '../reportDownload'

const props = defineProps<{ result: CheckResponse }>()
defineEmits<{ restart: [] }>()

const INCOME_LABEL: Record<CheckResponse['computed']['incomeThresholdResult'], string> = {
  low_income: '低收入戶門檻內',
  mid_low_income: '中低收入戶門檻內',
  above_threshold: '超過中低收入戶門檻',
}

function benefitKey(b: BenefitResult) {
  return `${b.id}`
}

function handlePrint() {
  window.print()
}

function handleDownload() {
  downloadReport(props.result)
}
</script>

<template>
  <div class="results-view">
    <div class="result-actions no-print">
      <button type="button" class="secondary-btn" @click="handlePrint">🖨️ 列印／存成 PDF</button>
      <button type="button" class="secondary-btn" @click="handleDownload">⬇️ 下載 HTML 報告</button>
    </div>

    <p class="data-freshness">
      查詢日期：{{ result.generatedAt }}
      <span v-if="result.oldestVerifiedDate">｜本次結果中最舊的資料查證日期：{{ result.oldestVerifiedDate }}（資料庫每週更新一次，個別項目仍可能已有異動，請以各單位最新公告為準）</span>
    </p>

    <section class="computed-summary">
      <h2>預審計算結果</h2>
      <ul>
        <li>實際年齡：{{ result.computed.age }} 歲</li>
        <li>人均月所得：約 {{ result.computed.perCapitaMonthlyIncome.toLocaleString() }} 元</li>
        <li>人均動產：約 {{ result.computed.perCapitaAssets.toLocaleString() }} 元</li>
        <li>居住縣市最低生活費：{{ result.computed.minLivingExpense.toLocaleString() }} 元</li>
        <li>所得門檻比對：{{ INCOME_LABEL[result.computed.incomeThresholdResult] }}</li>
      </ul>
    </section>

    <section class="benefit-list">
      <h2>✅ 確定符合（{{ result.confirmed.length }} 項）</h2>
      <article v-for="b in result.confirmed" :key="benefitKey(b)" class="benefit-card confirmed">
        <h3>
          {{ b.name }}
          <span v-if="b.isTimeSensitive" class="badge urgent">⚠️ 有時限</span>
        </h3>
        <p class="agency">主管機關：{{ b.agency }}<span v-if="b.county">（{{ b.county }}）</span></p>
        <p>{{ b.description }}</p>
        <p v-if="b.applicationPeriod" class="period">申請時間：{{ b.applicationPeriod }}</p>
        <ul v-if="b.documents.length > 0" class="documents">
          <li v-for="doc in b.documents" :key="doc">{{ doc }}</li>
        </ul>
        <ul v-if="b.locations.length > 0" class="locations">
          <li v-for="(loc, i) in b.locations" :key="i">
            {{ loc.name }}
            <a v-if="loc.website" :href="loc.website" target="_blank" rel="noopener">{{ loc.website }}</a>
          </li>
        </ul>
        <p v-if="b.notes" class="notes">備註：{{ b.notes }}</p>
        <p class="source">
          <a :href="b.sourceUrl" target="_blank" rel="noopener">資料來源</a>
          <span class="verified-date">（查證日期：{{ b.lastVerifiedDate }}）</span>
        </p>
      </article>
      <p v-if="result.confirmed.length === 0" class="empty">目前沒有確定符合的項目。</p>
    </section>

    <section class="benefit-list">
      <h2>⚠️ 可能符合（{{ result.possible.length }} 項，需補充資料確認）</h2>
      <article v-for="b in result.possible" :key="benefitKey(b)" class="benefit-card possible">
        <h3>
          {{ b.name }}
          <span v-if="b.isTimeSensitive" class="badge urgent">⚠️ 有時限</span>
        </h3>
        <p class="agency">主管機關：{{ b.agency }}<span v-if="b.county">（{{ b.county }}）</span></p>
        <p>{{ b.description }}</p>
        <p class="missing">還缺：{{ b.missingConditions.join('、') }}</p>
        <p class="source">
          <a :href="b.sourceUrl" target="_blank" rel="noopener">資料來源</a>
          <span class="verified-date">（查證日期：{{ b.lastVerifiedDate }}）</span>
        </p>
      </article>
      <p v-if="result.possible.length === 0" class="empty">沒有需要補充資料確認的項目。</p>
    </section>

    <button type="button" class="secondary-btn no-print" @click="$emit('restart')">重新查詢</button>
  </div>
</template>
