<script setup lang="ts">
import type { BenefitResult } from '../types'

defineProps<{ benefit: BenefitResult; verdict: 'confirmed' | 'possible' }>()

const PRIORITY_EMOJI: Record<BenefitResult['priority'], string> = {
  urgent: '🔴',
  normal: '🟠',
  review: '🟡',
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
      <span class="verified-date">（查證日期：{{ benefit.lastVerifiedDate }}）</span>
    </p>
  </article>
</template>
