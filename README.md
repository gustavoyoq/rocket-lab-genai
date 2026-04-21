# Text2SQL Rocket Lab

Projeto Python para a atividade GenAI Rocket Lab 2026.

## Objetivo

Receber perguntas em linguagem natural, gerar SQL de leitura com Gemini 2.5 Flash Lite, executar no SQLite e responder com analise em texto.

## Stack

- Python
- PydanticAI (`pydantic-ai-slim[google]`)
- Gemini 2.5 Flash Lite
- SQLite

## Estrutura

- `main.py`: CLI interativa e modo one-shot
- `src/text2sql/config.py`: configuracoes
- `src/text2sql/db.py`: acesso ao banco + guardrails
- `src/text2sql/agent.py`: agente e tools
- `src/text2sql/service.py`: orquestracao do fluxo

## Pre-requisitos

1. Python 3.11+
2. Arquivo `banco.db` na raiz do projeto (ou configure `DB_PATH` no `.env`)
3. Chave Gemini (Google AI Studio)

## Setup

1. Entre na pasta do projeto:
   - `cd text2sql-rocketlab`
2. Crie e ative um ambiente virtual.
3. Instale dependencias:
   - `pip install -e .`
4. Crie `.env` com base em `.env.example`.
5. Configure:
   - `GOOGLE_API_KEY=...`
   - `MODEL_NAME=gemini-2.5-flash-lite`
   - `DB_PATH=./banco.db`

## Como executar

### Modo interativo

- `python main.py`

### Modo one-shot

- `python main.py "Top 10 produtos mais vendidos"`

## Guardrails implementados

- Apenas SQL `SELECT`
- Bloqueio de comandos perigosos (`UPDATE`, `DELETE`, `DROP`, etc.)
- Bloqueio de multiplas statements
- `LIMIT` padrao em consultas sem limite
- Timeout de execucao SQL
- Log de auditoria em `logs/query_audit.jsonl`

## Proximos passos opcionais

- Expor endpoint via FastAPI reutilizando `TextToSQLService`
- Adicionar bateria automatizada de testes por categoria de pergunta
