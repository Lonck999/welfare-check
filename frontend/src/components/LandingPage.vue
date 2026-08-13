<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import BadgeIcon, { type BadgeIconName } from './BadgeIcon.vue'
import LegalNotice from './LegalNotice.vue'

const CATEGORIES: { icon: BadgeIconName; label: string; sub: string; tint: string }[] = [
  { icon: 'housing', label: '住宅', sub: '租金補貼・社會住宅', tint: 'var(--urgent-bg)' },
  { icon: 'care', label: '醫療長照', sub: '長照・喘息服務', tint: 'var(--confirmed-bg)' },
  { icon: 'family', label: '家庭育兒', sub: '生育給付・托育補助', tint: 'var(--possible-bg)' },
  { icon: 'study', label: '就學就業', sub: '就學貸款・就業獎勵', tint: '#dfeaf2' },
]

defineEmits<{ start: [] }>()

const sectionRefs = ref<HTMLElement[]>([])

function setSectionRef(el: Element | null) {
  if (el instanceof HTMLElement && !sectionRefs.value.includes(el)) {
    sectionRefs.value.push(el)
  }
}

/**
 * 刻意不用 IntersectionObserver：若使用者按 End 鍵或快速捲動直接跳到頁尾，
 * 某個區塊可能從「在視窗下方」直接變成「在視窗上方」，中間從未真正進入過視窗，
 * IntersectionObserver 的 isIntersecting 永遠不會被觸發，導致該區塊卡在 opacity:0 永久看不到。
 * 改用捲動時直接檢查 getBoundingClientRect，只要區塊頂端進入視窗範圍內就顯示，不管是怎麼捲過去的。
 */
function revealVisibleSections() {
  for (const el of sectionRefs.value) {
    if (el.classList.contains('is-visible')) continue
    if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add('is-visible')
  }
}

onMounted(() => {
  revealVisibleSections()
  window.addEventListener('scroll', revealVisibleSections, { passive: true })
  window.addEventListener('resize', revealVisibleSections)
})

onUnmounted(() => {
  window.removeEventListener('scroll', revealVisibleSections)
  window.removeEventListener('resize', revealVisibleSections)
})
</script>

<template>
  <div class="landing">
    <nav class="landing-nav">
      <div class="landing-logo">
        <svg width="36" height="36" viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <path
            d="M24 42c-8-5-15-11-15-19a9 9 0 0116-5.6A9 9 0 0139 23c0 8-7 14-15 19z"
            fill="var(--sage-500)"
          />
          <path d="M17 26h14M24 19v14" stroke="var(--bg)" stroke-width="2.8" stroke-linecap="round" />
        </svg>
        <span>台灣福利地圖</span>
      </div>
      <button type="button" class="submit-btn" @click="$emit('start')">開始查詢</button>
    </nav>

    <section class="landing-hero">
      <!--
        只出 WebP，不附 PNG fallback：不支援 WebP 的瀏覽器（IE11 等）本來就跑不動 Vue 3，
        為此在 repo 裡多放一份 1 MB 的 PNG 不划算。width/height 是為了讓瀏覽器在圖片載入前
        就保留正確高度，避免文字疊層跳動（CLS）。
      -->
      <img
        class="landing-hero-img"
        src="/images/hero-park-1600.webp"
        srcset="
          /images/hero-park-1200.webp 1200w,
          /images/hero-park-1600.webp 1600w,
          /images/hero-park-2400.webp 2400w
        "
        sizes="100vw"
        width="1600"
        height="679"
        fetchpriority="high"
        alt="公園場景，有拄拐杖的長者、推輪椅的照顧者、牽著幼兒的家長與背書包的學生"
      />

      <div class="landing-hero-copy">
        <div class="landing-hero-copy-inner">
          <h1>你有的權益<br />比你以為的多</h1>
          <p class="landing-lede">逐題問答，幾分鐘內比對 58 大類政府福利、補助與優惠。</p>
          <button type="button" class="submit-btn" @click="$emit('start')">開始查詢我的權益</button>
          <p class="landing-microcopy">完全免費・不用註冊・填完即查即丟</p>
        </div>
      </div>
    </section>

    <div class="landing-hero-stacked">
      <h1>你有的權益<br />比你以為的多</h1>
      <p class="landing-lede">逐題問答，幾分鐘內比對 58 大類政府福利、補助與優惠。</p>
      <button type="button" class="submit-btn" @click="$emit('start')">開始查詢我的權益</button>
      <p class="landing-microcopy">完全免費・不用註冊・填完即查即丟</p>
    </div>

    <div class="landing-band-sage">
      <div class="landing-inner">
        <section class="landing-section reveal" :ref="(el) => setSectionRef(el as Element)">
          <div class="landing-about">
            <div>
              <p class="landing-eyebrow">關於這個網站</p>
              <h2>這個網站在做什麼</h2>
              <p>
                台灣的福利補助分散在近 60 個中央部會與地方單位，光是搞清楚「有哪些」就是一大工程。我們把
                <strong>58 大類</strong>整理進資料庫，用逐題問答自動幫你比對，不用你自己一個一個去查。
              </p>
            </div>
            <svg viewBox="0 0 400 250" fill="none" aria-hidden="true">
              <path
                d="M60 190q60-66 140-38t140-66"
                stroke="var(--sage-500)"
                stroke-width="3"
                stroke-linecap="round"
                stroke-dasharray="7 10"
              />
              <rect x="120" y="36" width="98" height="72" rx="12" fill="#ffffff" />
              <path
                d="M138 60h62M138 74h46M138 88h32"
                stroke="var(--sage-200)"
                stroke-width="4"
                stroke-linecap="round"
              />
              <circle cx="60" cy="190" r="13" fill="var(--bg)" />
              <circle cx="200" cy="152" r="13" fill="var(--urgent-bg)" />
              <circle cx="340" cy="86" r="19" fill="var(--possible-bg)" />
              <path
                d="M332 86l6 7 11-14"
                stroke="var(--sage-700)"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
        </section>

        <section class="landing-section reveal" :ref="(el) => setSectionRef(el as Element)" style="padding-top: 0">
          <p class="landing-eyebrow">涵蓋範圍</p>
          <h2>涵蓋哪些面向</h2>
          <p>從現金補助到就業、住宅、醫療、教育與稅務減免。</p>
          <div class="landing-cats">
            <div v-for="cat in CATEGORIES" :key="cat.label" class="landing-cat">
              <div class="landing-cat-disc" :style="{ background: cat.tint }">
                <BadgeIcon :name="cat.icon" />
              </div>
              <div class="landing-cat-label">{{ cat.label }}</div>
              <div class="landing-cat-sub">{{ cat.sub }}</div>
            </div>
          </div>
        </section>

        <section class="landing-section reveal" :ref="(el) => setSectionRef(el as Element)" style="padding-top: 0">
          <p class="landing-eyebrow">怎麼使用</p>
          <h2>四個步驟</h2>
          <ol>
            <li>花幾分鐘填寫問卷（可以一起填家人的資料）</li>
            <li>系統自動算出你的年齡、家庭人口、所得門檻，比對 58 大類福利</li>
            <li>得到分級結果：有時限要優先看、確定符合、建議再確認</li>
            <li>每一項都附上主管機關、要準備的文件、去哪裡申請</li>
          </ol>
        </section>
      </div>
    </div>

    <svg class="landing-wave" viewBox="0 0 1440 96" preserveAspectRatio="none" aria-hidden="true">
      <rect width="1440" height="96" fill="var(--sage-100)" />
      <path
        d="M0 30c200 50 360-28 560-22s320 60 470 42 260-46 410-28v74H0z"
        fill="var(--sage-500)"
      />
    </svg>

    <div class="landing-band-deep">
      <div class="landing-inner">
        <section class="landing-section reveal" :ref="(el) => setSectionRef(el as Element)" style="padding-top: 10px">
          <h2>填完之後你會得到什麼</h2>
          <div class="landing-preview">
            <div class="landing-pcard">
              <span class="landing-tagline urgent">有時限，優先看</span>
              <h3>租金補貼</h3>
              <p>內政部國土管理署・每月最高 8,000 元。附申請文件與受理地點。</p>
            </div>
            <div class="landing-pcard">
              <span class="landing-tagline confirmed">確定符合</span>
              <h3>長期照顧特別扣除額</h3>
              <p>財政部・每人每年 18 萬元。報稅時直接申報。</p>
            </div>
            <div class="landing-pcard">
              <span class="landing-tagline possible">建議再確認</span>
              <h3>中低收入老人生活津貼</h3>
              <p>衛福部・需確認家人動產是否低於門檻。</p>
            </div>
          </div>
          <p style="margin-top: 22px; font-size: 14px; max-width: 620px">
            可下載一份自包含的 HTML 報告，離線也能開、方便給家人看，也可以直接列印或存成 PDF。個資即查即丟，不會被存進資料庫。
          </p>
          <button type="button" class="secondary-btn" style="margin-top: 8px" @click="$emit('start')">
            開始查詢我的權益
          </button>
        </section>
      </div>
    </div>

    <svg class="landing-wave" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true">
      <rect width="1440" height="90" fill="var(--cream-deep)" />
      <path
        d="M0 44c220-44 380 28 580 24s300-54 450-38 260 42 410 24V-4H0z"
        fill="var(--sage-500)"
      />
    </svg>

    <footer class="landing-footer">
      <div class="landing-inner landing-footer-grid">
        <div>
          <div class="landing-logo" style="margin-bottom: 10px">
            <svg width="34" height="34" viewBox="0 0 48 48" fill="none" aria-hidden="true">
              <path
                d="M24 42c-8-5-15-11-15-19a9 9 0 0116-5.6A9 9 0 0139 23c0 8-7 14-15 19z"
                fill="var(--sage-500)"
              />
              <path d="M17 26h14M24 19v14" stroke="var(--cream-deep)" stroke-width="2.8" stroke-linecap="round" />
            </svg>
            <span>台灣福利地圖</span>
          </div>
          <p>
            本查詢結果由 AI 整理各單位資訊，每週日凌晨 01:00 更新。實際資格請以各單位最新公告為準。填表資料不會保留，查詢結束即清除。
          </p>
          <LegalNotice />
        </div>
        <div>
          <h4>關於</h4>
          <p>這個網站在做什麼</p>
          <p>資料從哪裡來</p>
          <p>涵蓋哪些補助</p>
        </div>
        <div>
          <h4>聯絡</h4>
          <p>資訊有誤或需補充，歡迎來信</p>
          <p><a href="mailto:joe22053814@gmail.com">joe22053814@gmail.com</a></p>
        </div>
      </div>
    </footer>
  </div>
</template>
