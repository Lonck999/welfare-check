<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type { FormOptions, HouseholdMember, QuestionnaireAnswers } from '../types'

const props = defineProps<{ options: FormOptions }>()
const emit = defineEmits<{ submit: [answers: QuestionnaireAnswers] }>()

const answers = reactive<QuestionnaireAnswers>({
  birthDate: '',
  county: '',
  district: '',
  gender: undefined,
  maritalStatus: 'single',
  pregnantOrPostpartumSelf: false,
  pregnantOrPostpartumSpouse: false,
  miscarriageRecently: false,
  familySpecialCircumstances: [],
  householdMembers: [],
  housingStatus: '' as QuestionnaireAnswers['housingStatus'],
  selfAnnualIncome: 0,
  selfAssets: 0,
  employmentStatus: '' as QuestionnaireAnswers['employmentStatus'],
  workCounty: undefined,
  selfDisabilityCard: false,
  selfCatastrophicIllnessCard: false,
  selfRareDisease: false,
  selfRecentMajorSurgery: false,
  hasForeignCaregiver: false,
  hadOccupationalInjury: false,
  nonCohabitingFamily: [],
  specialIdentities: [],
  involuntaryUnemployment6mo: false,
  majorMedicalExpense: false,
  naturalDisasterDamage: false,
  domesticViolenceOrTrafficking: false,
  otherAcuteHardship: false,
  hasStartupIntent: false,
  infertilityTreatmentNeeded: false,
  wantsToQuitSmoking: false,
  legalDisputeNeedsConsultation: false,
  wantsAdultEducation: false,
  isStudent: false,
  developmentalDelayChild: false,
})

const STEP_SKIP_NO_MEMBERS = new Set(['membersRegistration', 'memberHealth'])
const NON_ACTIVE_EMPLOYMENT = new Set(['unemployed_seeking', 'unemployed_not_seeking', 'retired', 'homemaker'])

const ALL_STEPS = [
  'birthDate',
  'location',
  'gender',
  'marital',
  'pregnancy',
  'members',
  'membersRegistration',
  'housing',
  'assets',
  'income',
  'employment',
  'workCounty',
  'health',
  'memberHealth',
  'nonCohabiting',
  'identityAndUrgency',
  'lifePlans',
  'studentAndChild',
] as const

function isStepVisible(step: (typeof ALL_STEPS)[number]): boolean {
  if (STEP_SKIP_NO_MEMBERS.has(step) && answers.householdMembers.length === 0) return false
  if (step === 'workCounty' && NON_ACTIVE_EMPLOYMENT.has(answers.employmentStatus)) return false
  return true
}

const visibleSteps = computed(() => ALL_STEPS.filter(isStepVisible))
const stepIndex = ref(0)
const currentStep = computed(() => visibleSteps.value[stepIndex.value])
const isLastStep = computed(() => stepIndex.value === visibleSteps.value.length - 1)
const progressLabel = computed(() => `第 ${stepIndex.value + 1} 題 / 共 ${visibleSteps.value.length} 題`)

const errors = ref<string[]>([])

function validateCurrentStep(): boolean {
  errors.value = []
  const step = currentStep.value
  if (step === 'birthDate' && !answers.birthDate) errors.value.push('請填寫出生年月日')
  if (step === 'location' && !answers.county) errors.value.push('請選擇居住縣市')
  if (step === 'housing' && !answers.housingStatus) errors.value.push('請選擇住宅狀況')
  if (step === 'employment' && !answers.employmentStatus) errors.value.push('請選擇就業身分')
  if (step === 'workCounty' && !answers.workCounty) errors.value.push('請選擇工作地點縣市')
  return errors.value.length === 0
}

function next() {
  if (!validateCurrentStep()) return
  if (isLastStep.value) {
    emit('submit', JSON.parse(JSON.stringify(answers)))
    return
  }
  stepIndex.value += 1
}

function back() {
  errors.value = []
  if (stepIndex.value > 0) stepIndex.value -= 1
}

function addMember() {
  answers.householdMembers.push({
    relationship: '',
    birthDate: '',
    sameHukou: false,
  } as HouseholdMember)
}
function removeMember(index: number) {
  answers.householdMembers.splice(index, 1)
}

function addNonCohabitingMember() {
  answers.nonCohabitingFamily.push({
    relationship: '',
    birthDate: '',
    county: '',
    annualIncome: 0,
    assets: 0,
    isSinglePersonHousehold: false,
  })
}
function removeNonCohabitingMember(index: number) {
  answers.nonCohabitingFamily.splice(index, 1)
}

function toggleInArray(arr: string[], value: string) {
  const idx = arr.indexOf(value)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(value)
}

function toggleChronicDisability(member: HouseholdMember, value: string) {
  if (!member.chronicDisability) member.chronicDisability = []
  toggleInArray(member.chronicDisability, value)
}

const sameHukouMembers = computed(() => answers.householdMembers.filter((m) => m.sameHukou))

const CHRONIC_DISABILITY_OPTIONS = [
  { value: 'mobility', label: '行動障礙（需輪椅、長期臥床、無法自行行走）' },
  { value: 'cognitive', label: '認知退化（失智症、記憶喪失、方向感喪失）' },
  { value: 'self_care', label: '生活自理困難（無法自行洗澡、穿衣、如廁、進食）' },
  { value: 'chronic_disease', label: '慢性病功能退化（中風後遺症、帕金森、嚴重糖尿病截肢等）' },
]

const RELATIONSHIP_OPTIONS = ['配偶', '子女', '父親', '母親', '兄弟姊妹', '祖父', '祖母', '岳父', '岳母', '公公', '婆婆', '孫子女', '其他']

type EditableMember = { relationship: string; relationshipIsOther?: boolean }

function isOtherRelationship(relationship: string): boolean {
  return relationship !== '' && !RELATIONSHIP_OPTIONS.slice(0, -1).includes(relationship)
}

/** 下拉選單目前該顯示哪個選項：一旦切到「其他」就維持在「其他」，即使自訂文字還是空的（避免文字框剛切換就消失） */
function relationshipSelectValue(member: EditableMember): string {
  if (member.relationshipIsOther) return '其他'
  if (member.relationship === '') return ''
  return isOtherRelationship(member.relationship) ? '其他' : member.relationship
}
function showOtherRelationshipInput(member: EditableMember): boolean {
  return Boolean(member.relationshipIsOther) || isOtherRelationship(member.relationship)
}
function onRelationshipSelect(member: EditableMember, value: string) {
  if (value === '其他') {
    if (!member.relationshipIsOther) member.relationship = ''
    member.relationshipIsOther = true
  } else {
    member.relationshipIsOther = false
    member.relationship = value
  }
}
function onOtherRelationshipInput(member: EditableMember, value: string) {
  member.relationship = value
}
</script>

<template>
  <form class="questionnaire" @submit.prevent="next">
    <p class="progress">{{ progressLabel }}</p>

    <section v-if="currentStep === 'birthDate'" class="step">
      <h2>第 1 題：出生年月日</h2>
      <p class="hint">系統將自動計算實際年齡，用於比對各補助的精確年齡門檻。</p>
      <input v-model="answers.birthDate" type="date" required />
    </section>

    <section v-if="currentStep === 'location'" class="step">
      <h2>第 2 題：居住地</h2>
      <label class="field">
        <span>居住縣市</span>
        <select v-model="answers.county" required>
          <option value="" disabled>請選擇</option>
          <option v-for="c in props.options.counties" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>
      <label class="field">
        <span>鄉鎮市區（選填）</span>
        <input v-model="answers.district" type="text" placeholder="例：板橋區" />
      </label>
    </section>

    <section v-if="currentStep === 'gender'" class="step">
      <h2>第 3 題：性別</h2>
      <fieldset class="radio-row">
        <label><input v-model="answers.gender" type="radio" value="female" /> 女</label>
        <label><input v-model="answers.gender" type="radio" value="male" /> 男</label>
        <label><input v-model="answers.gender" type="radio" value="other" /> 其他</label>
      </fieldset>
    </section>

    <section v-if="currentStep === 'marital'" class="step">
      <h2>第 4 題：婚姻狀況</h2>
      <fieldset class="radio-col">
        <label><input v-model="answers.maritalStatus" type="radio" value="single" /> 未婚</label>
        <label><input v-model="answers.maritalStatus" type="radio" value="married" /> 已婚</label>
        <label><input v-model="answers.maritalStatus" type="radio" value="divorced" /> 離婚</label>
        <label><input v-model="answers.maritalStatus" type="radio" value="widowed" /> 喪偶</label>
      </fieldset>
    </section>

    <section v-if="currentStep === 'pregnancy'" class="step">
      <h2>第 4a 題：本人或配偶生育狀況</h2>
      <p class="hint">可複選，若無請跳過此題直接下一步。</p>
      <label class="checkbox-row"><input v-model="answers.pregnantOrPostpartumSelf" type="checkbox" /> 本人懷孕中／產後 12 個月內／哺乳中</label>
      <label v-if="answers.maritalStatus === 'married'" class="checkbox-row">
        <input v-model="answers.pregnantOrPostpartumSpouse" type="checkbox" /> 配偶懷孕中／產後 12 個月內
      </label>
      <label class="checkbox-row"><input v-model="answers.miscarriageRecently" type="checkbox" /> 近 1 年內有流產／小產</label>
      <h3>家庭生育特殊狀況（若適用）</h3>
      <label class="checkbox-row">
        <input
          type="checkbox"
          :checked="answers.familySpecialCircumstances.includes('single_parent_custody')"
          @change="toggleInArray(answers.familySpecialCircumstances, 'single_parent_custody')"
        />
        單親且有未成年子女監護權
      </label>
      <label class="checkbox-row">
        <input
          type="checkbox"
          :checked="answers.familySpecialCircumstances.includes('domestic_violence')"
          @change="toggleInArray(answers.familySpecialCircumstances, 'domestic_violence')"
        />
        曾遭受或正在處理家庭暴力相關事宜
      </label>
      <label class="checkbox-row">
        <input
          type="checkbox"
          :checked="answers.familySpecialCircumstances.includes('unmarried_birth')"
          @change="toggleInArray(answers.familySpecialCircumstances, 'unmarried_birth')"
        />
        未婚懷孕或未婚生子
      </label>
    </section>

    <section v-if="currentStep === 'members'" class="step">
      <h2>第 5 題：家庭成員</h2>
      <p class="hint">請列出所有共同生活的家人，不論是否與您同戶籍都要填。</p>
      <div v-for="(member, i) in answers.householdMembers" :key="i" class="member-card">
        <label class="field inline">
          <span>關係</span>
          <select
            :value="relationshipSelectValue(member)"
            @change="onRelationshipSelect(member, ($event.target as HTMLSelectElement).value)"
          >
            <option value="" disabled>請選擇</option>
            <option v-for="opt in RELATIONSHIP_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </label>
        <label v-if="showOtherRelationshipInput(member)" class="field inline">
          <span>請說明關係</span>
          <input
            :value="member.relationship === '其他' ? '' : member.relationship"
            type="text"
            placeholder="例：伯父、外甥"
            @input="onOtherRelationshipInput(member, ($event.target as HTMLInputElement).value)"
          />
        </label>
        <label class="field inline">
          <span>出生年月日</span>
          <input v-model="member.birthDate" type="date" />
        </label>
        <button type="button" class="remove-btn" @click="removeMember(i)">移除</button>
      </div>
      <button type="button" class="secondary-btn" @click="addMember">+ 新增家庭成員</button>
    </section>

    <section v-if="currentStep === 'membersRegistration'" class="step">
      <h2>第 6 題：戶籍狀況</h2>
      <p class="hint">請針對第 5 題每位家人，說明設籍縣市與是否與您同一戶號。</p>
      <div v-for="(member, i) in answers.householdMembers" :key="i" class="member-card">
        <h3>{{ member.relationship || `成員 ${i + 1}` }}</h3>
        <label class="field">
          <span>設籍縣市</span>
          <select v-model="member.registeredCounty">
            <option value="" disabled>請選擇</option>
            <option v-for="c in props.options.counties" :key="c" :value="c">{{ c }}</option>
          </select>
        </label>
        <label class="checkbox-row"><input v-model="member.sameHukou" type="checkbox" /> 與本人同一戶號</label>
      </div>
    </section>

    <section v-if="currentStep === 'housing'" class="step">
      <h2>第 7 題：住宅狀況</h2>
      <fieldset class="radio-col">
        <label><input v-model="answers.housingStatus" type="radio" value="own" /> 自有住宅（名下有房）</label>
        <label><input v-model="answers.housingStatus" type="radio" value="rent" /> 租屋（有合法租賃契約）</label>
        <label><input v-model="answers.housingStatus" type="radio" value="borrow" /> 借住（住在親屬或他人名下的房子）</label>
        <label><input v-model="answers.housingStatus" type="radio" value="other" /> 其他（宿舍、機構等）</label>
      </fieldset>
    </section>

    <section v-if="currentStep === 'assets'" class="step">
      <h2>第 8 題：財產狀況</h2>
      <p class="hint">請針對應計算人口（本人與同戶號家人）分別填寫動產（存款、有價證券、車輛）。</p>
      <label class="field inline">
        <span>本人動產</span>
        <input v-model.number="answers.selfAssets" type="number" min="0" />
      </label>
      <div v-for="member in sameHukouMembers" :key="member.relationship + member.birthDate" class="field inline">
        <span>{{ member.relationship }}動產</span>
        <input v-model.number="member.assets" type="number" min="0" />
      </div>
    </section>

    <section v-if="currentStep === 'income'" class="step">
      <h2>第 9 題：各成員收入</h2>
      <p class="hint">請填寫應計算人口去年綜合所得稅核定所得。</p>
      <label class="field inline">
        <span>本人年收入</span>
        <input v-model.number="answers.selfAnnualIncome" type="number" min="0" />
      </label>
      <div v-for="member in sameHukouMembers" :key="member.relationship + member.birthDate" class="field inline">
        <span>{{ member.relationship }}年收入</span>
        <input v-model.number="member.annualIncome" type="number" min="0" />
      </div>
    </section>

    <section v-if="currentStep === 'employment'" class="step">
      <h2>第 10 題：就業身分</h2>
      <fieldset class="radio-col">
        <label><input v-model="answers.employmentStatus" type="radio" value="employed_insured" /> 受僱員工（有公司加勞保）</label>
        <label><input v-model="answers.employmentStatus" type="radio" value="employed_reduced_hours" /> 受僱員工，因公司減班休息中</label>
        <label><input v-model="answers.employmentStatus" type="radio" value="self_employed" /> 自營作業者／接案／SOHO</label>
        <label><input v-model="answers.employmentStatus" type="radio" value="unemployed_seeking" /> 失業中（求職中）</label>
        <label><input v-model="answers.employmentStatus" type="radio" value="unemployed_not_seeking" /> 待業中（暫未求職）</label>
        <label><input v-model="answers.employmentStatus" type="radio" value="retired" /> 退休</label>
        <label><input v-model="answers.employmentStatus" type="radio" value="homemaker" /> 家管／無工作</label>
      </fieldset>
      <label class="checkbox-row"><input v-model="answers.hasForeignCaregiver" type="checkbox" /> 已聘僱外籍看護工</label>
      <label class="checkbox-row"><input v-model="answers.hadOccupationalInjury" type="checkbox" /> 曾遭遇職業災害</label>
    </section>

    <section v-if="currentStep === 'workCounty'" class="step">
      <h2>第 10a 題：工作地點</h2>
      <label class="field">
        <span>工作地點縣市</span>
        <select v-model="answers.workCounty">
          <option value="" disabled>請選擇</option>
          <option v-for="c in props.options.counties" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>
    </section>

    <section v-if="currentStep === 'health'" class="step">
      <h2>第 11 題：本人身體健康狀況</h2>
      <label class="checkbox-row"><input v-model="answers.selfDisabilityCard" type="checkbox" /> 領有身心障礙手冊／證明</label>
      <label class="checkbox-row"><input v-model="answers.selfCatastrophicIllnessCard" type="checkbox" /> 持有健保重大傷病卡</label>
      <label class="checkbox-row"><input v-model="answers.selfRareDisease" type="checkbox" /> 罕見疾病（領有罕病證明）</label>
      <label class="checkbox-row"><input v-model="answers.selfRecentMajorSurgery" type="checkbox" /> 近期（6 個月內）有重大手術或住院</label>
    </section>

    <section v-if="currentStep === 'memberHealth'" class="step">
      <h2>第 12 題：家庭成員健康狀況</h2>
      <p class="hint">請針對所有家庭成員（含不同戶籍者）分別說明。</p>
      <div v-for="(member, i) in answers.householdMembers" :key="i" class="member-card">
        <h3>{{ member.relationship || `成員 ${i + 1}` }}</h3>
        <label class="checkbox-row"><input v-model="member.disabilityCard" type="checkbox" /> 領有身心障礙手冊／證明</label>
        <label class="checkbox-row"><input v-model="member.catastrophicIllnessCard" type="checkbox" /> 持有健保重大傷病卡</label>
        <label class="checkbox-row"><input v-model="member.rareDisease" type="checkbox" /> 領有罕見疾病證明</label>
        <div class="checkbox-grid">
          <label v-for="opt in CHRONIC_DISABILITY_OPTIONS" :key="opt.value" class="checkbox-item">
            <input
              type="checkbox"
              :checked="member.chronicDisability?.includes(opt.value)"
              @change="toggleChronicDisability(member, opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </section>

    <section v-if="currentStep === 'nonCohabiting'" class="step">
      <h2>第 13 題：非同戶籍家人補助資料（選填）</h2>
      <p class="hint">即使非同戶籍，您的家人（如父母）可能有自己可以申請的補助。</p>
      <div v-for="(member, i) in answers.nonCohabitingFamily" :key="i" class="member-card">
        <label class="field inline">
          <span>關係</span>
          <select
            :value="relationshipSelectValue(member)"
            @change="onRelationshipSelect(member, ($event.target as HTMLSelectElement).value)"
          >
            <option value="" disabled>請選擇</option>
            <option v-for="opt in RELATIONSHIP_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </label>
        <label v-if="showOtherRelationshipInput(member)" class="field inline">
          <span>請說明關係</span>
          <input
            :value="member.relationship === '其他' ? '' : member.relationship"
            type="text"
            placeholder="例：伯父、外甥"
            @input="onOtherRelationshipInput(member, ($event.target as HTMLInputElement).value)"
          />
        </label>
        <label class="field inline">
          <span>出生年月日</span>
          <input v-model="member.birthDate" type="date" />
        </label>
        <label class="field">
          <span>戶籍縣市</span>
          <select v-model="member.county">
            <option value="" disabled>請選擇</option>
            <option v-for="c in props.options.counties" :key="c" :value="c">{{ c }}</option>
          </select>
        </label>
        <label class="field inline">
          <span>個人年收入</span>
          <input v-model.number="member.annualIncome" type="number" min="0" />
        </label>
        <label class="field inline">
          <span>個人動產總額</span>
          <input v-model.number="member.assets" type="number" min="0" />
        </label>
        <label class="checkbox-row"><input v-model="member.isSinglePersonHousehold" type="checkbox" /> 是否獨自一戶（單人戶）</label>
        <button type="button" class="remove-btn" @click="removeNonCohabitingMember(i)">移除</button>
      </div>
      <button type="button" class="secondary-btn" @click="addNonCohabitingMember">+ 新增非同戶籍家人</button>
    </section>

    <section v-if="currentStep === 'identityAndUrgency'" class="step">
      <h2>第 14 題：特殊身分與急難情形</h2>
      <p class="hint">可複選，若無請跳過此題直接下一步。</p>
      <div class="checkbox-grid">
        <label v-for="opt in props.options.identities" :key="opt.value" class="checkbox-item">
          <input
            type="checkbox"
            :checked="answers.specialIdentities.includes(opt.value)"
            @change="toggleInArray(answers.specialIdentities, opt.value)"
          />
          <span>{{ opt.label }}</span>
        </label>
      </div>
      <h3>急難情形</h3>
      <label class="checkbox-row"><input v-model="answers.involuntaryUnemployment6mo" type="checkbox" /> 6 個月內非自願離職或失業</label>
      <label class="checkbox-row"><input v-model="answers.majorMedicalExpense" type="checkbox" /> 近期重大傷病或醫療費用沉重</label>
      <label class="checkbox-row"><input v-model="answers.naturalDisasterDamage" type="checkbox" /> 近期遭遇風災／震災／水災，房屋或財產受損</label>
      <label class="checkbox-row"><input v-model="answers.domesticViolenceOrTrafficking" type="checkbox" /> 受家暴、性侵或人口販賣</label>
      <label class="checkbox-row"><input v-model="answers.otherAcuteHardship" type="checkbox" /> 其他急難情形</label>
    </section>

    <section v-if="currentStep === 'lifePlans'" class="step">
      <h2>第 14a 題：生活計畫與個人需求（選填）</h2>
      <label class="checkbox-row"><input v-model="answers.hasStartupIntent" type="checkbox" /> 有創業意願或正在籌備創業計畫</label>
      <label class="checkbox-row"><input v-model="answers.infertilityTreatmentNeeded" type="checkbox" /> 目前有生育困難（不孕治療中，或有想生育但尚未成功）</label>
      <label class="checkbox-row"><input v-model="answers.wantsToQuitSmoking" type="checkbox" /> 本人或家中成員有吸菸習慣，且有戒菸意願</label>
      <label class="checkbox-row"><input v-model="answers.legalDisputeNeedsConsultation" type="checkbox" /> 目前有法律糾紛或需要法律諮詢</label>
      <label class="checkbox-row"><input v-model="answers.wantsAdultEducation" type="checkbox" /> 想重返學校進修（回流教育／成人進修）</label>
    </section>

    <section v-if="currentStep === 'studentAndChild'" class="step">
      <h2>第 14b 題：在學狀況與兒童發展（選填）</h2>
      <label class="checkbox-row"><input v-model="answers.isStudent" type="checkbox" /> 本人、配偶或子女為國中以上在學學生</label>
      <label class="checkbox-row">
        <input v-model="answers.developmentalDelayChild" type="checkbox" />
        家中有未滿 6 歲子女，有發展遲緩疑似情形或已診斷
      </label>
    </section>

    <p v-if="errors.length > 0" class="error-box">
      <span v-for="err in errors" :key="err">{{ err }}</span>
    </p>

    <div class="step-actions">
      <button v-if="stepIndex > 0" type="button" class="secondary-btn" @click="back">上一步</button>
      <button type="submit" class="submit-btn">{{ isLastStep ? '開始查詢' : '下一步' }}</button>
    </div>
  </form>
</template>
