<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

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
    <section class="landing-hero">
      <div class="landing-pixel-bg" aria-hidden="true">
        <div class="pixel-horizon"></div>
        <div class="pixel-cloud pixel-cloud--a"><span></span><span></span><span></span></div>
        <div class="pixel-cloud pixel-cloud--b"><span></span><span></span><span></span></div>
        <div class="pixel-cloud pixel-cloud--c"><span></span><span></span><span></span></div>
      </div>
      <div class="landing-hero-content">
        <h1>你知道自己有什麼權益嗎？</h1>
        <p>逐題問答，幾分鐘內幫你找出所有可能符合資格的政府福利、補助與優惠。</p>
        <button type="button" class="submit-btn landing-cta" @click="$emit('start')">開始查詢我的權益 →</button>
        <p class="landing-microcopy">完全免費・不用註冊・填完即查即丟</p>
      </div>
    </section>

    <section class="landing-section reveal" :ref="(el) => setSectionRef(el as Element)">
      <p class="landing-eyebrow">關於這個網站</p>
      <h2>這個網站在做什麼</h2>
      <p>
        台灣的福利補助分散在近 60 個中央部會與地方單位，光是搞清楚「有哪些」就是一大工程。這個網站整合了
        <strong>58 大類</strong>福利項目——橫跨衛福部、勞動部、教育部、內政部、原民會、客委會、僑委會、退輔會等中央部會，加上地方政府的加碼措施，用逐題問答自動比對哪些你可能符合資格，不用你自己一個一個去查。
      </p>
      <div class="image-placeholder">〔圖片待補：福利分散在多個單位 → 整合成一個網站的示意圖〕</div>
    </section>

    <section class="landing-section reveal" :ref="(el) => setSectionRef(el as Element)">
      <p class="landing-eyebrow">怎麼使用</p>
      <h2>四個步驟</h2>
      <ol>
        <li>花幾分鐘填寫問卷（可以一起填家人的資料）</li>
        <li>系統自動算出你的年齡、家庭人口、所得門檻，比對 58 大類福利</li>
        <li>得到分級結果：🔴 有時限要優先看、✅ 確定符合、⚠️ 建議再確認</li>
        <li>每一項都附上主管機關、要準備的文件、去哪裡申請</li>
      </ol>
      <div class="image-placeholder">〔圖片待補：四個步驟的流程示意圖，或問卷/結果頁截圖〕</div>
    </section>

    <section class="landing-section reveal" :ref="(el) => setSectionRef(el as Element)">
      <p class="landing-eyebrow">初衷</p>
      <h2>為什麼做這個網站</h2>
      <p>
        一趟公車的成人票價 15 元，其實就是你我最常、最直接接觸過的政府福利之一。但大多數人只知道「政府有補助」，卻不知道「補助是什麼」——這些資訊零零星星散落在新聞或網路角落，讓真正需要幫助、本來就該被照顧到的人，常常錯過屬於自己的權益。
      </p>
      <p>這個網站的初衷很簡單：想幫更多人盡快知道——<strong>我有什麼權益？該去哪裡求助？需要準備什麼？</strong></p>
      <div class="image-placeholder">〔圖片待補：情境感插畫，例如公車站牌/排隊等公車的人群剪影〕</div>
    </section>

    <section class="landing-section reveal" :ref="(el) => setSectionRef(el as Element)">
      <p class="landing-eyebrow">查完之後</p>
      <h2>填完之後你會得到什麼</h2>
      <ul>
        <li>網頁上直接看到補助總覽表（確定可申請／建議確認分兩類）+ 每項詳細卡片（機關、文件、申請地點）</li>
        <li>可下載一份自包含的 HTML 報告，離線也能開、方便給家人看</li>
        <li>可以直接列印或存成 PDF</li>
        <li>個資即查即丟，不會被存進資料庫，下載的檔案只留在你自己的裝置上</li>
      </ul>
      <div class="image-placeholder">〔圖片待補：結果頁總覽表/卡片的截圖或示意圖〕</div>
      <button type="button" class="submit-btn landing-cta" @click="$emit('start')">開始查詢我的權益 →</button>
    </section>
  </div>
</template>
