<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import type { CheckRequestBody, FormOptions, HouseholdMemberInput } from '../types'

const props = defineProps<{ options: FormOptions }>()
const emit = defineEmits<{ submit: [body: CheckRequestBody] }>()

const birthDate = ref('')
const county = ref('')
const workCountySameAsCounty = ref(true)
const workCounty = ref('')
const ownsHome = ref<'yes' | 'no' | ''>('')
const hasYoungestChild = ref(false)
const youngestChildAge = ref<number | null>(null)
const hasOldestElder = ref(false)
const oldestElderAge = ref<number | null>(null)
const selectedIdentities = reactive<Set<string>>(new Set())
const selectedFlags = reactive<Set<string>>(new Set())

const members = reactive<HouseholdMemberInput[]>([{ annualIncome: 0, assets: 0 }])

function addMember() {
  members.push({ annualIncome: 0, assets: 0 })
}
function removeMember(index: number) {
  if (members.length > 1) members.splice(index, 1)
}

function toggle(set: Set<string>, value: string) {
  if (set.has(value)) set.delete(value)
  else set.add(value)
}

const errors = ref<string[]>([])

const isValid = computed(() => {
  return Boolean(birthDate.value && county.value && ownsHome.value)
})

function handleSubmit() {
  errors.value = []
  if (!birthDate.value) errors.value.push('請填寫出生年月日')
  if (!county.value) errors.value.push('請選擇居住縣市')
  if (!ownsHome.value) errors.value.push('請選擇是否有自有住宅')
  if (errors.value.length > 0) return

  const body: CheckRequestBody = {
    birthDate: birthDate.value,
    county: county.value,
    workCounty: workCountySameAsCounty.value ? undefined : workCounty.value || undefined,
    ownsHome: ownsHome.value === 'yes',
    householdMembers: members.map((m) => ({
      annualIncome: Number(m.annualIncome) || 0,
      assets: Number(m.assets) || 0,
    })),
    youngestChildAge: hasYoungestChild.value && youngestChildAge.value !== null ? youngestChildAge.value : undefined,
    oldestElderAge: hasOldestElder.value && oldestElderAge.value !== null ? oldestElderAge.value : undefined,
    identities: [...selectedIdentities],
    flags: [...selectedFlags],
  }
  emit('submit', body)
}
</script>

<template>
  <form class="welfare-form" @submit.prevent="handleSubmit">
    <section class="form-section">
      <h2>基本資料</h2>
      <label class="field">
        <span>出生年月日</span>
        <input v-model="birthDate" type="date" required />
      </label>

      <label class="field">
        <span>居住縣市</span>
        <select v-model="county" required>
          <option value="" disabled>請選擇</option>
          <option v-for="c in props.options.counties" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>

      <label class="field checkbox-field">
        <input v-model="workCountySameAsCounty" type="checkbox" />
        <span>工作地點與居住縣市相同（或無固定工作地點）</span>
      </label>

      <label v-if="!workCountySameAsCounty" class="field">
        <span>工作地點縣市</span>
        <select v-model="workCounty">
          <option value="" disabled>請選擇</option>
          <option v-for="c in props.options.counties" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>

      <fieldset class="field">
        <legend>是否有自有住宅</legend>
        <label><input v-model="ownsHome" type="radio" value="yes" /> 有</label>
        <label><input v-model="ownsHome" type="radio" value="no" /> 無</label>
      </fieldset>
    </section>

    <section class="form-section">
      <h2>家庭成員收入與財產</h2>
      <p class="hint">請填寫「應計算人口」（同戶號家人）每人去年綜合所得稅核定所得，以及動產（存款、有價證券、車輛）總額。</p>
      <div v-for="(member, i) in members" :key="i" class="member-row">
        <label class="field inline">
          <span>成員 {{ i + 1 }} 年收入</span>
          <input v-model.number="member.annualIncome" type="number" min="0" />
        </label>
        <label class="field inline">
          <span>成員 {{ i + 1 }} 動產</span>
          <input v-model.number="member.assets" type="number" min="0" />
        </label>
        <button v-if="members.length > 1" type="button" class="remove-btn" @click="removeMember(i)">移除</button>
      </div>
      <button type="button" class="secondary-btn" @click="addMember">+ 新增家庭成員</button>
    </section>

    <section class="form-section">
      <h2>家中子女與長者</h2>
      <label class="field checkbox-field">
        <input v-model="hasYoungestChild" type="checkbox" />
        <span>家中有未成年子女</span>
      </label>
      <label v-if="hasYoungestChild" class="field">
        <span>最年幼子女年齡</span>
        <input v-model.number="youngestChildAge" type="number" min="0" max="17" />
      </label>

      <label class="field checkbox-field">
        <input v-model="hasOldestElder" type="checkbox" />
        <span>家中有 65 歲以上成員</span>
      </label>
      <label v-if="hasOldestElder" class="field">
        <span>最年長成員年齡</span>
        <input v-model.number="oldestElderAge" type="number" min="65" max="120" />
      </label>
    </section>

    <section class="form-section">
      <h2>特殊身分（可複選）</h2>
      <div class="checkbox-grid">
        <label v-for="opt in props.options.identities" :key="opt.value" class="checkbox-item">
          <input
            type="checkbox"
            :checked="selectedIdentities.has(opt.value)"
            @change="toggle(selectedIdentities, opt.value)"
          />
          <span>{{ opt.label }}</span>
        </label>
      </div>
    </section>

    <section class="form-section">
      <h2>其他狀況與需求（可複選）</h2>
      <div class="checkbox-grid">
        <label v-for="opt in props.options.flags" :key="opt.value" class="checkbox-item">
          <input type="checkbox" :checked="selectedFlags.has(opt.value)" @change="toggle(selectedFlags, opt.value)" />
          <span>{{ opt.label }}</span>
        </label>
      </div>
    </section>

    <p v-if="errors.length > 0" class="error-box">
      <span v-for="err in errors" :key="err">{{ err }}</span>
    </p>

    <button type="submit" class="submit-btn" :disabled="!isValid">開始查詢</button>
  </form>
</template>
