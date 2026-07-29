import type { BenefitGroup, BenefitResult, CheckResponse } from './types'

const INCOME_LABEL: Record<CheckResponse['computed']['incomeThresholdResult'], string> = {
  low_income: '低收入戶門檻內',
  mid_low_income: '中低收入戶門檻內',
  above_threshold: '超過中低收入戶門檻',
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderBenefitCard(b: BenefitResult, kind: 'confirmed' | 'possible'): string {
  const badge = kind === 'confirmed' ? '✅ 確定符合' : '⚠️ 可能符合'
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
          .map(
            (loc) =>
              `<li>${escapeHtml(loc.name)}${loc.website ? ` <a href="${escapeHtml(loc.website)}">${escapeHtml(loc.website)}</a>` : ''}</li>`,
          )
          .join('')}</ul>`
      : ''
  return `
    <article class="card ${kind}">
      <h3><span class="badge ${kind}">${badge}</span> ${escapeHtml(b.name)} ${urgentBadge}</h3>
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
  return `
  <h2>${escapeHtml(label)}：✅ 確定符合（${group.confirmed.length} 項）</h2>
  ${group.confirmed.map((b) => renderBenefitCard(b, 'confirmed')).join('') || '<p>目前沒有確定符合的項目。</p>'}

  <h2>${escapeHtml(label)}：⚠️ 可能符合（${group.possible.length} 項，需補充資料確認）</h2>
  ${group.possible.map((b) => renderBenefitCard(b, 'possible')).join('') || '<p>沒有需要補充資料確認的項目。</p>'}`
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
  body { font-family: system-ui, 'Segoe UI', Roboto, sans-serif; max-width: 720px; margin: 0 auto; padding: 32px 20px; color: #222; }
  h1 { font-size: 24px; }
  h2 { font-size: 19px; margin-top: 32px; }
  h3 { font-size: 16px; display: flex; align-items: center; gap: 8px; }
  .card { border: 1px solid #ddd; border-left-width: 4px; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; }
  .card.confirmed { border-left-color: #1a7f37; }
  .card.possible { border-left-color: #b3690a; }
  .badge { font-size: 12px; padding: 2px 8px; border-radius: 999px; }
  .badge.confirmed { background: rgba(26,127,55,0.12); color: #1a7f37; }
  .badge.possible { background: rgba(179,105,10,0.12); color: #b3690a; }
  .badge.urgent { background: rgba(179,105,10,0.12); color: #b3690a; }
  .missing { color: #b3690a; }
  .source, .notes, .agency { font-size: 13px; opacity: 0.85; }
  .disclaimer { font-size: 13px; opacity: 0.8; border-top: 1px solid #ddd; margin-top: 32px; padding-top: 16px; }
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
