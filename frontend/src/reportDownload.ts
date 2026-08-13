import type { BenefitGroup, BenefitResult, CheckResponse } from './types'

const INCOME_LABEL: Record<CheckResponse['computed']['incomeThresholdResult'], string> = {
  low_income: '低收入戶門檻內',
  mid_low_income: '中低收入戶門檻內',
  above_threshold: '超過中低收入戶門檻',
}

const PRIORITY_EMOJI: Record<BenefitResult['priority'], string> = {
  urgent: '🔴',
  normal: '🟠',
  review: '🟡',
}

const PRIORITY_ORDER: Record<BenefitResult['priority'], number> = {
  urgent: 0,
  normal: 1,
  review: 2,
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function byPriority(list: BenefitResult[]): BenefitResult[] {
  return [...list].sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
}

/** 總覽表與行動清單只挑每個 categoryNumber 的第一筆代表，避免「中央基準」＋「地方加碼」重複列出 */
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

function renderBenefitCard(b: BenefitResult, kind: 'confirmed' | 'possible'): string {
  const badge = kind === 'confirmed' ? '✅ 確定符合' : '⚠️ 可能符合'
  const priorityDot = `<span class="priority-dot">${PRIORITY_EMOJI[b.priority]}</span>`
  const urgentBadge = b.isTimeSensitive ? '<span class="badge urgent">⚠️ 有時限</span>' : ''
  const missing =
    kind === 'possible' && b.missingConditions.length > 0
      ? `<p class="missing">還缺：${escapeHtml(b.missingConditions.join('、'))}</p>`
      : ''
  const documents =
    b.documents.length > 0
      ? `<ul>${b.documents
          .map((d) => `<li>${escapeHtml(d.name)}${d.obtainLocation ? `（${escapeHtml(d.obtainLocation)}）` : ''}</li>`)
          .join('')}</ul>`
      : ''
  const locations =
    b.locations.length > 0
      ? `<ul>${b.locations
          .map((loc) => {
            const parts = [escapeHtml(loc.name)]
            if (loc.address) parts.push(escapeHtml(loc.address))
            if (loc.phone) parts.push(`☎ ${escapeHtml(loc.phone)}`)
            if (loc.website) parts.push(`<a href="${escapeHtml(loc.website)}">${escapeHtml(loc.website)}</a>`)
            return `<li>${parts.join('　')}</li>`
          })
          .join('')}</ul>`
      : ''
  return `
    <article class="card ${kind}">
      <h3>${priorityDot}<span class="badge ${kind}">${badge}</span> ${escapeHtml(b.name)} ${urgentBadge}</h3>
      <p class="agency">主管機關：${escapeHtml(b.agency)}${b.county ? `（${escapeHtml(b.county)}）` : ''}</p>
      <p>${escapeHtml(b.description)}</p>
      ${b.applicationPeriod ? `<p>申請時間：${escapeHtml(b.applicationPeriod)}</p>` : ''}
      ${documents}
      ${locations}
      ${b.notes ? `<p class="notes">備註：${escapeHtml(b.notes)}</p>` : ''}
      ${missing}
      <p class="source">資料來源：<a href="${escapeHtml(b.sourceUrl)}">${escapeHtml(b.sourceUrl)}</a>（查證日期：${b.lastVerifiedDate}）</p>
    </article>`
}

function renderBenefitGroup(label: string, group: BenefitGroup): string {
  const confirmed = byPriority(group.confirmed)
  const possible = byPriority(group.possible)
  return `
  <h2>${escapeHtml(label)}：✅ 確定符合（${confirmed.length} 項）</h2>
  ${confirmed.map((b) => renderBenefitCard(b, 'confirmed')).join('') || '<p>目前沒有確定符合的項目。</p>'}

  <h2>${escapeHtml(label)}：⚠️ 可能符合（${possible.length} 項，需補充資料確認）</h2>
  ${possible.map((b) => renderBenefitCard(b, 'possible')).join('') || '<p>沒有需要補充資料確認的項目。</p>'}`
}

interface OverviewSection {
  label: string
  group: BenefitGroup
}

function renderOverviewTable(sections: OverviewSection[]): string {
  const rows = sections
    .map(({ label, group }) => {
      const confirmed = byPriority(dedupeByCategory(group.confirmed))
      const possible = byPriority(dedupeByCategory(group.possible))
      return `
      <tr><th colspan="2">${escapeHtml(label)}</th></tr>
      <tr>
        <td>
          <strong>✅ 確定可申請</strong>
          ${
            confirmed.length > 0
              ? `<ul>${confirmed.map((b) => `<li>${PRIORITY_EMOJI[b.priority]} ${escapeHtml(b.name)}</li>`).join('')}</ul>`
              : '<p class="empty">無</p>'
          }
        </td>
        <td>
          <strong>⚠️ 建議確認</strong>
          ${
            possible.length > 0
              ? `<ul>${possible.map((b) => `<li>${escapeHtml(b.name)}</li>`).join('')}</ul>`
              : '<p class="empty">無</p>'
          }
        </td>
      </tr>`
    })
    .join('')
  return `
  <h2>補助總覽表</h2>
  <p class="hint">🔴 有時限優先確認　🟠 確定可申請　🟡 建議確認。同一項目若同時有「中央基準」與「地方加碼」版本，這裡只列一筆代表，完整明細請見下方各項卡片。</p>
  <table class="overview">
    ${rows}
  </table>`
}

function renderActionList(sections: OverviewSection[]): string {
  const items = sections.flatMap(({ label, group }) =>
    byPriority(dedupeByCategory(group.confirmed)).map(
      (b) =>
        `<li><label><input type="checkbox"> ${PRIORITY_EMOJI[b.priority]} 【${escapeHtml(label)}】${escapeHtml(b.name)}${b.isTimeSensitive ? ' ⚠️ 有時限' : ''}</label></li>`,
    ),
  )
  return `
  <h2>行動清單</h2>
  <p class="hint">依優先順序排列（🔴 有時限最優先），列出所有「✅ 確定可申請」項目，勾選已完成申請的項目。</p>
  ${items.length > 0 ? `<ul class="action-list">${items.join('')}</ul>` : '<p class="empty">目前沒有確定可申請的項目。</p>'}`
}

function overviewSections(result: CheckResponse): OverviewSection[] {
  return [
    { label: '本人', group: result.self },
    ...result.familyMembers.map((m) => ({ label: `${m.relationship}（${m.age} 歲，設籍${m.county}）`, group: m })),
  ]
}

/** 產生對應 SKILL.md 第六步規格的獨立 HTML 報告字串，供瀏覽器下載，不含任何伺服器往返 */
export function buildReportHtml(result: CheckResponse): string {
  return `<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>台灣社會福利補助查詢結果</title>
<style>
  body { font-family: system-ui, 'PingFang TC', 'Microsoft JhengHei', 'Segoe UI', Roboto, sans-serif; max-width: 720px; margin: 0 auto; padding: 32px 20px; color: #665b4d; background: #f9f5e9; }
  h1, h2, h3 { color: #2a2019; }
  h1 { font-size: 24px; }
  h2 { font-size: 19px; margin-top: 32px; }
  h3 { font-size: 16px; display: flex; align-items: center; gap: 8px; }
  a { color: #4f6a41; overflow-wrap: anywhere; }
  .card { background: #fff; border: 1px solid #e2dac7; border-left-width: 4px; border-radius: 0 8px 8px 0; padding: 14px 18px; margin-bottom: 12px; }
  .card.confirmed { border-left-color: #3b6438; }
  .card.possible { border-left-color: #8a6414; }
  .badge { font-size: 12px; padding: 2px 8px; border-radius: 999px; }
  .badge.confirmed { background: #e2f0e4; color: #3b6438; }
  .badge.possible { background: #faf0d2; color: #8a6414; }
  .badge.urgent { background: #fbe6d8; color: #97441f; }
  .missing { color: #8a6414; }
  .source, .notes, .agency { font-size: 13px; color: #7a7062; }
  .priority-dot { margin-right: 4px; }
  .hint { font-size: 13px; color: #7a7062; }
  table.overview { width: 100%; border-collapse: collapse; margin-top: 12px; }
  table.overview th, table.overview td { border: 1px solid #e2dac7; padding: 10px 14px; text-align: left; vertical-align: top; }
  table.overview th { background: #f2ead4; }
  table.overview ul { margin: 6px 0 0; padding-left: 20px; }
  .empty { color: #9a8f7d; }
  ul.action-list { list-style: none; padding: 0; }
  ul.action-list li { padding: 6px 0; border-bottom: 1px dashed #e2dac7; }
  ul.action-list label { cursor: pointer; }
  .disclaimer { font-size: 13px; color: #7a7062; border-top: 1px solid #e2dac7; margin-top: 32px; padding-top: 16px; }
</style>
</head>
<body>
  <h1>台灣社會福利補助查詢結果</h1>
  <p>查詢日期：${result.generatedAt}${result.oldestVerifiedDate ? `｜資料查證日期範圍：最舊 ${result.oldestVerifiedDate}` : ''}</p>

  <h2>預審計算結果</h2>
  <ul>
    <li>實際年齡：${result.computed.age} 歲</li>
    <li>人均月所得：約 ${result.computed.perCapitaMonthlyIncome.toLocaleString()} 元</li>
    <li>人均動產：約 ${result.computed.perCapitaAssets.toLocaleString()} 元</li>
    <li>居住縣市最低生活費：${result.computed.minLivingExpense.toLocaleString()} 元</li>
    <li>所得門檻比對：${INCOME_LABEL[result.computed.incomeThresholdResult]}</li>
  </ul>

  ${renderOverviewTable(overviewSections(result))}

  ${renderActionList(overviewSections(result))}

  ${renderBenefitGroup('本人', result.self)}
  ${result.familyMembers.map((m) => renderBenefitGroup(`${m.relationship}（${m.age} 歲，設籍${m.county}）`, m)).join('')}

  <div class="disclaimer">
    <p>本查詢結果僅供參考，實際資格請以各單位最新公告為準。本站資料庫每週更新一次，個別項目可能已有異動。</p>
    <p>本報告為使用者本機下載留存，網站本身不儲存任何填表資料。</p>
  </div>
</body>
</html>`
}

export function downloadReport(result: CheckResponse) {
  const html = buildReportHtml(result)
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `welfare-result-${result.generatedAt.replace(/-/g, '')}.html`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
