import type { CheckResponse, FormOptions, QuestionnaireAnswers } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:3000'

export async function fetchFormOptions(): Promise<FormOptions> {
  const res = await fetch(`${API_BASE_URL}/api/form-options`)
  if (!res.ok) throw new Error('無法載入表單選項，請確認後端服務是否啟動')
  return res.json()
}

export async function submitCheck(body: QuestionnaireAnswers): Promise<CheckResponse> {
  const res = await fetch(`${API_BASE_URL}/api/check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error ?? '查詢失敗，請稍後再試')
  return data
}
