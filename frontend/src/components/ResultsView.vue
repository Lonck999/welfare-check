<script setup lang="ts">
import { computed } from 'vue'
import type { BenefitGroup, CheckResponse } from '../types'
import { downloadReport } from '../reportDownload'
import BenefitCard from './BenefitCard.vue'

const props = defineProps<{ result: CheckResponse }>()
defineEmits<{ restart: [] }>()

const INCOME_LABEL: Record<CheckResponse['computed']['incomeThresholdResult'], string> = {
  low_income: '低收入戶門檻內',
  mid_low_income: '中低收入戶門檻內',
  above_threshold: '超過中低收入戶門檻',
}

function handlePrint() {
  window.print()
}

function handleDownload() {
  downloadReport(props.result)
}

interface OverviewSection {
  label: string
  group: BenefitGroup
}

const overviewSections = computed<OverviewSection[]>(() => [
  { label: '本人', group: props.result.self },
  ...props.result.familyMembers.map((m) => ({ label: `${m.relationship}（${m.age} 歲）`, group: m })),
])
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
      <h2>預審計算結果（本人）</h2>
      <ul>
        <li>實際年齡：{{ result.computed.age }} 歲</li>
        <li>人均月所得：約 {{ result.computed.perCapitaMonthlyIncome.toLocaleString() }} 元</li>
        <li>人均動產：約 {{ result.computed.perCapitaAssets.toLocaleString() }} 元</li>
        <li>居住縣市最低生活費：{{ result.computed.minLivingExpense.toLocaleString() }} 元</li>
        <li>所得門檻比對：{{ INCOME_LABEL[result.computed.incomeThresholdResult] }}</li>
      </ul>
    </section>

    <section class="overview-table">
      <h2>補助總覽表</h2>
      <p class="hint">🔴 有時限優先確認　🟠 確定可申請　🟡 建議確認</p>
      <table>
        <thead>
          <tr>
            <th>對象</th>
            <th>✅ 確定可申請</th>
            <th>⚠️ 建議確認</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="section in overviewSections" :key="section.label">
            <td>{{ section.label }}</td>
            <td>
              <ul v-if="section.group.confirmed.length > 0">
                <li v-for="b in section.group.confirmed" :key="b.id">{{ b.isTimeSensitive ? '🔴 ' : '' }}{{ b.name }}</li>
              </ul>
              <span v-else class="empty">無</span>
            </td>
            <td>
              <ul v-if="section.group.possible.length > 0">
                <li v-for="b in section.group.possible" :key="b.id">{{ b.name }}</li>
              </ul>
              <span v-else class="empty">無</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="benefit-list">
      <h2>本人：✅ 確定符合（{{ result.self.confirmed.length }} 項）</h2>
      <BenefitCard v-for="b in result.self.confirmed" :key="b.id" :benefit="b" verdict="confirmed" />
      <p v-if="result.self.confirmed.length === 0" class="empty">目前沒有確定符合的項目。</p>
    </section>

    <section class="benefit-list">
      <h2>本人：⚠️ 可能符合（{{ result.self.possible.length }} 項，需補充資料確認）</h2>
      <BenefitCard v-for="b in result.self.possible" :key="b.id" :benefit="b" verdict="possible" />
      <p v-if="result.self.possible.length === 0" class="empty">沒有需要補充資料確認的項目。</p>
    </section>

    <section v-for="member in result.familyMembers" :key="member.relationship + member.county" class="benefit-list family-section">
      <h2>{{ member.relationship }}（{{ member.age }} 歲，設籍{{ member.county }}）</h2>
      <p class="hint">
        依第 13 題填寫的戶籍縣市與年齡比對，資料有限（未收集此對象的自有住宅、特殊身分等資訊），⚠️ 項目較多屬正常現象，建議由本人親自確認。
      </p>
      <h3>✅ 確定符合（{{ member.confirmed.length }} 項）</h3>
      <BenefitCard v-for="b in member.confirmed" :key="b.id" :benefit="b" verdict="confirmed" />
      <p v-if="member.confirmed.length === 0" class="empty">目前沒有確定符合的項目。</p>
      <h3>⚠️ 可能符合（{{ member.possible.length }} 項）</h3>
      <BenefitCard v-for="b in member.possible" :key="b.id" :benefit="b" verdict="possible" />
    </section>

    <button type="button" class="secondary-btn no-print" @click="$emit('restart')">重新查詢</button>
  </div>
</template>
