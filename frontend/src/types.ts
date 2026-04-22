export type ChatAskRequest = {
  question: string
  session_id?: string | null
  verbose?: boolean
}

export type ChatAskResponse = {
  session_id: string
  tool_call: string | null
  tool_result: string | null
  conclusion: string
  sql_executed: string
  confidence: string
  timestamp: string
  raw_response: string
}
