/**
 * 🔴 P4 篩選規則（Lonck 2026-09-24 訂）
 *    「有要幫家人申請才給其他人的選項，沒有就只給自身」
 *
 * ⚠️ 這支測的是 check.ts 裡那段篩選的**判準本身**。
 *    把邏輯抄成純函式測，因為 evaluateAllBenefits 需要真實 DB。
 *    🔴 判準若在 check.ts 改了而這裡沒跟著改，測試會全綠但行為已變 ——
 *       所以下面的 shouldShow 必須與 check.ts 的那四行**逐字對得上**。
 */
import { describe, it, expect } from 'vitest'

/** 與 check.ts 的 P4 篩選逐行對應 */
function shouldShow(roles: string[], wants: string[]): boolean {
  if (roles.length === 0) return true          // 未標註一律保留
  const set = new Set(roles)
  return set.has('self') || wants.some((w) => set.has(w))
}

describe('P4：沒勾「幫家人」就只給自身', () => {
  it('🔴 未標註申請對象的一律保留（未標註 ≠ 不能申請）', () => {
    expect(shouldShow([], [])).toBe(true)
    expect(shouldShow([], ['family'])).toBe(true)
  })

  it('本人能申請的，永遠看得到', () => {
    expect(shouldShow(['self'], [])).toBe(true)
    expect(shouldShow(['self', 'family'], [])).toBe(true)
  })

  it('🔴 只能為別人申請的（喪葬、托育），沒勾就不給', () => {
    expect(shouldShow(['family'], [])).toBe(false)
    expect(shouldShow(['spouse'], [])).toBe(false)
  })

  it('勾了對應角色才出現', () => {
    expect(shouldShow(['family'], ['family'])).toBe(true)
    expect(shouldShow(['spouse'], ['spouse'])).toBe(true)
  })

  it('🔴 negative control：勾了別的角色不會誤放行', () => {
    expect(shouldShow(['family'], ['spouse'])).toBe(false)
    expect(shouldShow(['spouse'], ['household'])).toBe(false)
  })

  it('household（全戶型）要勾 household 才出現', () => {
    expect(shouldShow(['household'], [])).toBe(false)
    expect(shouldShow(['household'], ['household'])).toBe(true)
  })
})
