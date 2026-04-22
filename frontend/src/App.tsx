import { useMemo, useState } from 'react'
import type { KeyboardEvent } from 'react'
import './App.css'
import { askAgent } from './services/chatApi'
import type { ChatAskResponse } from './types'

const SESSION_KEY = 'text2sql_session_id'

function getStoredSessionId(): string | null {
  return localStorage.getItem(SESSION_KEY)
}

function setStoredSessionId(sessionId: string): void {
  localStorage.setItem(SESSION_KEY, sessionId)
}

function confidenceClass(confidence: string): string {
  const normalized = confidence.trim().toLowerCase()
  if (normalized === 'high') return 'high'
  if (normalized === 'medium') return 'medium'
  if (normalized === 'low') return 'low'
  return 'unknown'
}

function toFriendlyError(message: string): string {
  const normalized = message.toLowerCase()
  if (normalized.includes('429') || normalized.includes('cota')) {
    return 'Limite temporario de cota excedido. Tente novamente em alguns instantes.'
  }
  if (normalized.includes('401') || normalized.includes('api key') || normalized.includes('chave')) {
    return 'A chave da API parece invalida ou expirada. Verifique as configuracoes do backend.'
  }
  return message || 'Nao foi possivel processar sua pergunta agora.'
}

function App() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [response, setResponse] = useState<ChatAskResponse | null>(null)

  const sessionPreview = useMemo(() => {
    const session = getStoredSessionId()
    if (!session) return '-'
    return `${session.slice(0, 14)}...`
  }, [response])

  async function submitQuestion(): Promise<void> {
    const trimmed = question.trim()
    if (!trimmed || loading) {
      return
    }

    setLoading(true)
    setError('')
    setResponse(null)

    try {
      const data = await askAgent({
        question: trimmed,
        session_id: getStoredSessionId(),
        verbose: true,
      })

      if (data.session_id) {
        setStoredSessionId(data.session_id)
      }

      setResponse(data)
      setQuestion('')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro inesperado'
      setError(toFriendlyError(message))
    } finally {
      setLoading(false)
    }
  }

  function onInputKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
    if (event.key === 'Enter') {
      event.preventDefault()
      void submitQuestion()
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <h1>Pergunte ao agente</h1>
        <p className="subtitle">Faca uma pergunta e o agente respondera com base no banco de dados.</p>
      </section>

      <section className="ask-card">
        <div className="input-row">
          <input
            id="question-input"
            type="text"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder="Faca uma pergunta sobre os dados..."
            maxLength={1000}
            disabled={loading}
          />
          <button type="button" onClick={() => void submitQuestion()} disabled={loading || !question.trim()}>
            {loading ? 'Processando...' : 'Enviar'}
          </button>
        </div>

        <div className="session">Sessao: {sessionPreview}</div>

        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}

        {response && (
          <article className="response-card">
            <div className="section">
              <h2>Resultado da ferramenta</h2>
              <pre>{response.tool_result || '-'}</pre>
            </div>

            <div className="section">
              <h2>Conclusao</h2>
              <p>{response.conclusion || '-'}</p>
            </div>

            <div className="section">
              <h2>SQL executado</h2>
              <pre>{response.sql_executed || '-'}</pre>
            </div>

            <div className="section">
              <h2>Confianca</h2>
              <span className={`confidence ${confidenceClass(response.confidence || '')}`}>
                {response.confidence || 'unknown'}
              </span>
            </div>
          </article>
        )}
      </section>
    </main>
  )
}

export default App
