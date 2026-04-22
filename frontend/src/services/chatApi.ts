import type { ChatAskRequest, ChatAskResponse } from '../types'

export async function askAgent(payload: ChatAskRequest): Promise<ChatAskResponse> {
  const response = await fetch('/api/v1/chat/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let message = `Erro ${response.status}`

    try {
      const data = await response.json()
      if (typeof data?.detail === 'string' && data.detail.trim()) {
        message = data.detail
      }
    } catch {
      const text = await response.text()
      if (text.trim()) {
        message = text
      }
    }

    throw new Error(message)
  }

  return (await response.json()) as ChatAskResponse
}
