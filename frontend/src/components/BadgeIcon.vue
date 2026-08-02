<script setup lang="ts">
/**
 * 首頁「涵蓋哪些面向」的分類圖示。
 * 刻意畫成無描邊的實心色塊，與主視覺插畫（扁平、無外框）同一套語彙；
 * 先前的細線描邊版本跟新主圖放在同一頁會互相打架。
 */
export type BadgeIconName = 'housing' | 'care' | 'family' | 'study'

defineProps<{ name: BadgeIconName }>()
</script>

<template>
  <svg viewBox="0 0 64 64" class="badge-icon" aria-hidden="true">
    <template v-if="name === 'housing'">
      <path d="M32 11 L56 32 h-7 v21 H15 V32 H8 Z" fill="var(--sage-500)" />
      <rect x="26" y="37" width="12" height="16" rx="2" fill="var(--bg)" />
    </template>

    <template v-else-if="name === 'care'">
      <path
        d="M32 52C19 43 10 36 10 25a11 11 0 0 1 22-6 11 11 0 0 1 22 6c0 11-9 18-22 27z"
        fill="var(--sage-500)"
      />
      <path
        d="M17 27h9l4-8 5 15 4-7h8"
        fill="none"
        stroke="var(--bg)"
        stroke-width="3.4"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </template>

    <template v-else-if="name === 'family'">
      <circle cx="24" cy="21" r="10" fill="var(--sage-500)" />
      <circle cx="45" cy="26" r="7.5" fill="var(--sage-200)" />
      <path d="M8 53c0-10 7-16 16-16s16 6 16 16z" fill="var(--sage-500)" />
      <path d="M42 53c0-8 4-13 11-13 4 0 7 2 7 6v7z" fill="var(--sage-200)" />
    </template>

    <template v-else-if="name === 'study'">
      <path d="M6 25 L32 13 L58 25 L32 37 Z" fill="var(--sage-500)" />
      <path d="M18 31v13c0 4 6 7 14 7s14-3 14-7V31l-14 6z" fill="var(--sage-200)" />
      <path d="M57 26v15" stroke="var(--sage-500)" stroke-width="3.6" stroke-linecap="round" />
    </template>
  </svg>
</template>

<style scoped>
.badge-icon {
  display: block;
}
</style>
