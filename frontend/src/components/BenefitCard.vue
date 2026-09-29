<script setup lang="ts">
import type { BenefitResult } from '../types'

defineProps<{ benefit: BenefitResult; verdict: 'confirmed' | 'possible' }>()

const PRIORITY_EMOJI: Record<BenefitResult['priority'], string> = {
  urgent: '🔴',
  normal: '🟠',
  review: '🟡',
}

/**
 * 🔴 C-2 來源等級的顯示文字。
 *
 * ⚠️ 用詞刻意不寫「可信／不可信」—— 媒體整理文常常正確，
 *    真正的差別是「政策改了誰會回頭改」：官網會，媒體不會。
 *    講成可信度會誤導使用者直接忽略 media 那批。
 *
 * 🔴 分類邏輯的唯一來源是資料庫的 source_tier
 *    （由 ~/.hermes/scripts/welfare_source_tier.py 寫入）。
 *    這裡**只負責顯示**，絕不在前端重判一次網域 ——
 *    兩份判準必然漂移，而漂移看起來像資料問題不像程式問題。
 */
const SOURCE_TIER_LABEL: Record<string, { text: string; hint: string }> = {
  official: { text: '政府官網', hint: '來源為主管機關官方網站' },
  opendata: {
    text: '政府開放資料',
    hint: '來源為 data.gov.tw 資料集頁面，非原始公告頁，細節請洽主管機關',
  },
  ngo: { text: '民間團體', hint: '來源為基金會或民間服務單位官網' },
  media: {
    text: '媒體整理',
    hint: '來源為媒體或整理型網站。內容可能正確，但政策異動時不一定會更新，請以主管機關公告為準',
  },
  unknown: { text: '來源待確認', hint: '尚未判定來源類型' },
}
</script>

<template>
  <article class="benefit-card" :class="verdict">
    <h3>
      <span class="priority-dot">{{ PRIORITY_EMOJI[benefit.priority] }}</span>
      {{ benefit.name }}
      <span v-if="benefit.isTimeSensitive" class="badge urgent">⚠️ 有時限</span>
    </h3>
    <p class="agency">主管機關：{{ benefit.agency }}<span v-if="benefit.county">（{{ benefit.county }}）</span></p>
    <p>{{ benefit.description }}</p>
    <p v-if="benefit.applicationPeriod" class="period">申請時間：{{ benefit.applicationPeriod }}</p>
    <ul v-if="benefit.documents.length > 0" class="documents">
      <li v-for="doc in benefit.documents" :key="doc.name">
        {{ doc.name }}
        <span v-if="doc.obtainLocation" class="obtain-location">（{{ doc.obtainLocation }}）</span>
      </li>
    </ul>
    <ul v-if="benefit.locations.length > 0" class="locations">
      <li v-for="(loc, i) in benefit.locations" :key="i">
        {{ loc.name }}
        <span v-if="loc.address">{{ loc.address }}</span>
        <span v-if="loc.phone">☎ {{ loc.phone }}</span>
        <a v-if="loc.website" :href="loc.website" target="_blank" rel="noopener">{{ loc.website }}</a>
      </li>
    </ul>
    <p v-if="benefit.notes" class="notes">備註：{{ benefit.notes }}</p>
    <p v-if="verdict === 'possible' && benefit.missingConditions.length > 0" class="missing">
      還缺：{{ benefit.missingConditions.join('、') }}
    </p>
    <p class="source">
      <a :href="benefit.sourceUrl" target="_blank" rel="noopener">資料來源</a>
      <span
        v-if="benefit.sourceTier && SOURCE_TIER_LABEL[benefit.sourceTier]"
        class="source-tier"
        :class="`tier-${benefit.sourceTier}`"
        :title="SOURCE_TIER_LABEL[benefit.sourceTier].hint"
      >{{ SOURCE_TIER_LABEL[benefit.sourceTier].text }}</span>
      <span class="verified-date">（查證日期：{{ benefit.lastVerifiedDate }}）</span>
    </p>
    <p
      v-if="benefit.sourceTier === 'media'"
      class="tier-warning"
    >
      ⚠️ 本筆依據為媒體或整理型網站，政策異動時不一定會更新 ——
      申請前請以主管機關公告為準。
    </p>
  </article>
</template>
