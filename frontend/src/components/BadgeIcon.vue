<script setup lang="ts">
export type BadgeIconName = 'house' | 'bottle' | 'care' | 'access' | 'elder' | 'grad'

defineProps<{ name: BadgeIconName }>()
</script>

<template>
  <svg viewBox="0 0 48 48" class="badge-icon" aria-hidden="true">
    <template v-if="name === 'house'">
      <path d="M24 6 L42 22 L6 22 Z" fill="var(--hero-ink)" />
      <rect x="10" y="22" width="28" height="18" rx="2" fill="var(--hero-solid)" />
      <rect x="21" y="30" width="6" height="10" fill="var(--hero-ink)" />
      <circle cx="31" cy="29" r="3" fill="var(--hero-chip-bg)" />
    </template>

    <template v-else-if="name === 'bottle'">
      <path d="M22 6 Q24 4 26 6 L26 12 L22 12 Z" fill="var(--hero-ink)" />
      <rect x="18" y="12" width="12" height="5" rx="2" fill="var(--hero-ink)" />
      <rect x="17" y="17" width="14" height="25" rx="4" fill="var(--hero-solid)" />
      <rect x="17" y="27" width="14" height="10" fill="var(--hero-chip-bg)" opacity="0.5" />
    </template>

    <template v-else-if="name === 'care'">
      <path
        d="M24 40 C10 30 6 20 12 14 C16 10 22 12 24 18 C26 12 32 10 36 14 C42 20 38 30 24 40 Z"
        fill="var(--hero-solid)"
      />
      <rect x="21" y="19" width="6" height="16" fill="var(--hero-chip-bg)" />
      <rect x="15" y="25" width="18" height="6" fill="var(--hero-chip-bg)" />
    </template>

    <template v-else-if="name === 'access'">
      <circle cx="30" cy="10" r="4" fill="var(--hero-ink)" />
      <path
        d="M28 16 L28 24 L34 24 M20 24 L28 24 M28 20 L20 28"
        stroke="var(--hero-ink)"
        stroke-width="4"
        fill="none"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <circle cx="20" cy="32" r="10" fill="none" stroke="var(--hero-solid)" stroke-width="4" />
      <circle cx="36" cy="38" r="3" fill="var(--hero-ink)" />
    </template>

    <template v-else-if="name === 'elder'">
      <circle cx="22" cy="12" r="7" fill="var(--hero-ink)" />
      <path d="M22 19 Q14 22 14 34 L14 42 L30 42 L30 34 Q30 22 22 19 Z" fill="var(--hero-solid)" />
      <line x1="32" y1="24" x2="38" y2="42" stroke="var(--hero-ink)" stroke-width="3" stroke-linecap="round" />
      <circle cx="32" cy="22" r="3" fill="var(--hero-ink)" />
    </template>

    <template v-else-if="name === 'grad'">
      <path d="M24 8 L44 18 L24 28 L4 18 Z" fill="var(--hero-ink)" />
      <path d="M14 22 L14 30 Q24 36 34 30 L34 22 L24 27 Z" fill="var(--hero-solid)" />
      <line x1="40" y1="19" x2="40" y2="30" stroke="var(--hero-ink)" stroke-width="2" />
      <circle cx="40" cy="32" r="2.5" fill="var(--hero-ink)" />
    </template>
  </svg>
</template>

<style scoped>
.badge-icon {
  display: block;
}
</style>
