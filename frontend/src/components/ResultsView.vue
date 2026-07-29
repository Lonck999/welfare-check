<script setup lang="ts">
import { computed, reactive } from 'vue'
import type { BenefitGroup, BenefitResult, CheckResponse } from '../types'
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
  key: string
  label: string
  group: BenefitGroup
}

const overviewSections = computed<OverviewSection[]>(() => [
  { key: 'self', label: '本人', group: props.result.self },
  ...props.result.familyMembers.map((m) => ({ key: `${m.relationship}-${m.county}`, label: `${m.relationship}（${m.age} 歲）`, group: m })),
])

/**
 * 總覽表刻意跟下方詳細卡片分開處理：很多類別本身就會有「中央基準」+「地方加碼」兩筆資料
 * （例如身心障礙補助分「生活補助費，中央基準」與「地方加碼」兩列），這是資料庫設計本身如此、
 * 不是重複建檔，但在總覽表這種一行一項目的快速掃視表格裡，同一個 categoryNumber 出現兩次
 * 看起來會像是重複列出。總覽表只挑每個 categoryNumber 的第一筆代表顯示，完整明細仍看下方卡片。
 */
function dedupeByCategory(list: BenefitResult[]): BenefitResult[] {
  const seen = new Set<number | string>()
  const result: BenefitResult[] = []
  for (const b of list) {
    const key = b.categoryNumber ?? `id-${b.id}`
    if (seen.has(key)) continue
    seen.add(key)
    result.push(b)
  }
  return result
}

const PAGE_SIZE = 10
const pageIndex = reactive<Record<string, number>>({})

function pageKey(sectionKey: string, kind: 'confirmed' | 'possible') {
  return `${sectionKey}-${kind}`
}
function currentPage(sectionKey: string, kind: 'confirmed' | 'possible') {
  return pageIndex[pageKey(sectionKey, kind)] ?? 0
}
function setPage(sectionKey: string, kind: 'confirmed' | 'possible', page: number) {
  pageIndex[pageKey(sectionKey, kind)] = page
}
function paginate(list: BenefitResult[], sectionKey: string, kind: 'confirmed' | 'possible') {
  const page = currentPage(sectionKey, kind)
  return list.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE)
}
function pageCount(list: BenefitResult[]) {
  return Math.max(1, Math.ceil(list.length / PAGE_SIZE))
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
      <p class="hint">
        🔴 有時限優先確認　🟠 確定可申請　🟡 建議確認。同一項目若同時有「中央基準」與「地方加碼」版本，這裡只列一筆代表，完整明細請看下方卡片。
      </p>
      <table>
        <thead>
          <tr>
            <th>對象</th>
            <th>✅ 確定可申請</th>
            <th>⚠️ 建議確認</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="section in overviewSections" :key="section.key">
            <td>{{ section.label }}</td>
            <td>
              <template v-if="dedupeByCategory(section.group.confirmed).length > 0">
                <ul>
                  <li v-for="b in paginate(dedupeByCategory(section.group.confirmed), section.key, 'confirmed')" :key="b.id">
                    {{ b.isTimeSensitive ? '🔴 ' : '' }}{{ b.name }}
                  </li>
                </ul>
                <div v-if="pageCount(dedupeByCategory(section.group.confirmed)) > 1" class="pager">
                  <button
                    type="button"
                    class="pager-btn"
                    :disabled="currentPage(section.key, 'confirmed') === 0"
                    @click="setPage(section.key, 'confirmed', currentPage(section.key, 'confirmed') - 1)"
                  >
                    ‹
                  </button>
                  <span>{{ currentPage(section.key, 'confirmed') + 1 }} / {{ pageCount(dedupeByCategory(section.group.confirmed)) }}</span>
                  <button
                    type="button"
                    class="pager-btn"
                    :disabled="currentPage(section.key, 'confirmed') >= pageCount(dedupeByCategory(section.group.confirmed)) - 1"
                    @click="setPage(section.key, 'confirmed', currentPage(section.key, 'confirmed') + 1)"
                  >
                    ›
                  </button>
                </div>
              </template>
              <span v-else class="empty">無</span>
            </td>
            <td>
              <template v-if="dedupeByCategory(section.group.possible).length > 0">
                <ul>
                  <li v-for="b in paginate(dedupeByCategory(section.group.possible), section.key, 'possible')" :key="b.id">{{ b.name }}</li>
                </ul>
                <div v-if="pageCount(dedupeByCategory(section.group.possible)) > 1" class="pager">
                  <button
                    type="button"
                    class="pager-btn"
                    :disabled="currentPage(section.key, 'possible') === 0"
                    @click="setPage(section.key, 'possible', currentPage(section.key, 'possible') - 1)"
                  >
                    ‹
                  </button>
                  <span>{{ currentPage(section.key, 'possible') + 1 }} / {{ pageCount(dedupeByCategory(section.group.possible)) }}</span>
                  <button
                    type="button"
                    class="pager-btn"
                    :disabled="currentPage(section.key, 'possible') >= pageCount(dedupeByCategory(section.group.possible)) - 1"
                    @click="setPage(section.key, 'possible', currentPage(section.key, 'possible') + 1)"
                  >
                    ›
                  </button>
                </div>
              </template>
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
