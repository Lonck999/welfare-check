#!/usr/bin/env node
/**
 * 走完 16 題問卷，驗結果頁真的出得來。
 *
 * 🔴 這是唯一能證明「真的可以完整使用」的一步。
 *    首頁截圖漂亮、第一題出得來、API 用 curl 打得通 ——
 *    這三件事全成立的情況下，中間某一題卡住仍然完全可能，
 *    而那個症狀在前面三個檢查裡都看不到。
 */
import { spawn } from 'node:child_process'
import { mkdtemp, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = 9222 + Math.floor(Math.random() * 500)
const profile = await mkdtemp(join(tmpdir(), 'wcflow-'))

const chrome = spawn(CHROME, [
  '--headless=new', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check',
  '--disable-gpu', '--hide-scrollbars', '--window-size=1440,2000', 'about:blank',
], { stdio: 'ignore' })
process.on('exit', () => { try { chrome.kill('SIGKILL') } catch {} })

async function wsUrl() {
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json()
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl
    } catch {}
    await new Promise(r => setTimeout(r, 250))
  }
  throw new Error('Chrome debug port 沒開起來')
}

const ws = new WebSocket(await wsUrl())
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })

let id = 0
const pending = new Map()
const errors = []
// 🔴 在 finally 之外宣告 —— 見下方斷言區的註解
let FAILED = false
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data)
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id) }
  if (m.method === 'Runtime.exceptionThrown') errors.push(m.params?.exceptionDetails?.text ?? 'exception')
  if (m.method === 'Log.entryAdded' && m.params?.entry?.level === 'error') errors.push(m.params.entry.text)
}
const send = (method, params = {}, S) => new Promise((res) => {
  const myId = ++id
  pending.set(myId, res)
  ws.send(JSON.stringify({ id: myId, method, params, sessionId: S }))
})

try {
  const { result: { targetId } } = await send('Target.createTarget', { url: 'about:blank' })
  const { result: { sessionId: S } } = await send('Target.attachToTarget', { targetId, flatten: true })
  await send('Page.enable', {}, S)
  await send('Runtime.enable', {}, S)
  await send('Log.enable', {}, S)
  await send('Page.navigate', { url: 'http://localhost:5173/' }, S)
  await new Promise(r => setTimeout(r, 3500))

  const ev = async (expr) => {
    const { result } = await send('Runtime.evaluate',
      { expression: expr, returnByValue: true, awaitPromise: true }, S)
    if (result?.exceptionDetails) return { __err: result.exceptionDetails.text }
    return result?.result?.value
  }

  await ev(`[...document.querySelectorAll('button,a')].find(e=>/開始查詢/.test(e.textContent||''))?.click()`)
  await new Promise(r => setTimeout(r, 1200))

  // 逐題填：用原生 setter 觸發 Vue 的 v-model
  const fillAndNext = `(() => {
    const setVal = (el, v) => {
      const proto = el.tagName === 'SELECT'
        ? window.HTMLSelectElement.prototype
        : el.tagName === 'TEXTAREA'
          ? window.HTMLTextAreaElement.prototype
          : window.HTMLInputElement.prototype
      const setter = Object.getOwnPropertyDescriptor(proto, 'value').set
      setter.call(el, v)
      el.dispatchEvent(new Event('input', { bubbles: true }))
      el.dispatchEvent(new Event('change', { bubbles: true }))
    }
    const heading = (document.querySelector('h2,h3')||{}).innerText || ''
    const fields = [...document.querySelectorAll('input,select,textarea')]
      .filter(e => e.offsetParent !== null)

    for (const el of fields) {
      if (el.type === 'date') setVal(el, '1955-03-10')
      else if (el.type === 'number') setVal(el, '120000')
      else if (el.type === 'radio') { if (!document.querySelector('input[type=radio][name="'+el.name+'"]:checked')) el.click() }
      else if (el.type === 'checkbox') { /* 留空＝沒有該狀況 */ }
      else if (el.tagName === 'SELECT') {
        const opt = [...el.options].find(o => o.value && o.value !== '')
        if (opt && !el.value) setVal(el, opt.value)
      }
      else if (el.type === 'text') setVal(el, '板橋區')
    }
    const next = [...document.querySelectorAll('button')]
      .find(b => /下一步|看結果|送出|查詢/.test(b.textContent||'') && !b.disabled)
    const label = next ? next.textContent.trim() : 'NO_BUTTON'
    if (next) next.click()
    return { heading, fields: fields.length, clicked: label }
  })()`

  const trace = []
  for (let step = 1; step <= 25; step++) {
    const r = await ev(fillAndNext)
    trace.push(`${step}. ${r?.heading?.slice(0, 26) ?? '?'} [${r?.fields}欄] → ${r?.clicked}`)
    await new Promise(r => setTimeout(r, 900))
    const done = await ev(`/符合|結果|confirmed|項福利|可能符合/.test(document.body.innerText) && !/第 \\d+ 題/.test(document.body.innerText)`)
    if (done === true) { trace.push(`   ✅ 第 ${step} 步之後進入結果頁`); break }
    if (r?.clicked === 'NO_BUTTON') { trace.push('   🔴 找不到可按的下一步'); break }
  }
  console.log(trace.join('\n'))

  const final = await ev(`(() => ({
    textLen: document.body.innerText.length,
    stillForm: /第 \\d+ 題/.test(document.body.innerText),
    head: document.body.innerText.slice(0, 420),
  }))()`)
  console.log('\n=== 最終畫面 ===')
  console.log(JSON.stringify(final, null, 2))

  const { result: { data } } = await send('Page.captureScreenshot',
    { format: 'png', captureBeyondViewport: true }, S)
  await writeFile('/tmp/_wc_result.png', Buffer.from(data, 'base64'))

  console.log(errors.length ? `\n🔴 主控台錯誤 ${errors.length} 筆：\n  ` + errors.slice(0, 5).join('\n  ') : '\n✅ 無主控台錯誤')

  // ── 🔴 斷言 ────────────────────────────────────────────────
  //
  // 少了這一段，這支腳本只會「印一些字然後 exit 0」——
  // 放進 CI 會永遠是綠的，而那正是它壞掉時的樣子。
  //
  // 🔴 「不在問卷畫面」不可以當成「進到結果頁」（實測踩到）：
  //    把 backend 停掉之後，前端跳到一個空的錯誤畫面，
  //    `stillForm === false` 照樣成立 —— 那條斷言在後端全掛時仍是綠的。
  //    判準要問「結果頁該有的東西在不在」，不是「舊畫面走掉了沒」。
  const head = final?.head ?? ''
  const checks = [
    ['不再停留在問卷', final?.stillForm === false],
    ['🔴 真的是結果頁（有預審計算結果）', /預審計算結果/.test(head)],
    ['結果頁有實質內容（>5000 字）', (final?.textLen ?? 0) > 5000],
    ['算出實際年齡', /實際年齡/.test(head)],
    ['算出最低生活費', /最低生活費/.test(head)],
    ['列出補助總覽', /補助總覽/.test(head)],
    ['沒有主控台錯誤', errors.length === 0],
  ]
  console.log('\n=== 斷言 ===')
  let bad = 0
  for (const [name, ok] of checks) {
    console.log(`  ${ok ? '✅' : '❌ FAIL'}  ${name}`)
    if (!ok) bad++
  }
  if (bad) {
    console.log(`\n🔴 ${bad}/${checks.length} 項失敗 —— 截圖：/tmp/_wc_result.png`)
    // 🔴 用 process.exit 而不是 process.exitCode：
    //    finally 區塊裡有 chrome.kill 與 rm，它們會覆蓋 exitCode，
    //    結果是「印了一堆 FAIL 但 rc=0」（實測踩到）。
    FAILED = true
  } else {
    console.log(`\n✅ ${checks.length}/${checks.length} 通過 —— 這個站真的可以完整使用`)
  }
} finally {
  try { ws.close() } catch {}
  chrome.kill('SIGKILL')
  await rm(profile, { recursive: true, force: true }).catch(() => {})
}

// 🔴 在 finally 之後才退出 —— 清理動作（kill / rm）會覆蓋 exitCode，
//    寫在 finally 裡面的 process.exitCode = 1 會被吃掉，
//    症狀是「印了一堆 ❌ FAIL 但 rc=0」，接進 CI 等於沒驗。
if (FAILED) process.exit(1)
