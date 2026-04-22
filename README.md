# Text2SQL Rocket Lab

Projeto Python para a atividade GenAI Rocket Lab 2026.

## Objetivo

Receber perguntas em linguagem natural, gerar SQL de leitura com Gemini 2.5 Flash Lite, executar no SQLite e responder com analise em texto.

## Stack

- Python
- PydanticAI (`pydantic-ai-slim[google]`)
- Gemini 2.5 Flash Lite
- SQLite
- FastAPI (backend API)
- React + Vite + TypeScript (frontend)

## Estrutura

- `main.py`: CLI interativa e modo one-shot
- `backend/app/main.py`: API FastAPI para o agente
- `frontend/`: aplicacao React para interacao com o agente
- `src/text2sql/config.py`: configuracoes
- `src/text2sql/db.py`: acesso ao banco + guardrails
- `src/text2sql/agent.py`: agente e tools
- `src/text2sql/service.py`: orquestracao do fluxo

## Execucao fullstack (Backend + Frontend)

Esse passo a passo é para a execução do backend e frontend, a criação e modelagem do agente em si fica na pasta 'src'

1. Inicie o backend (porta 8000):
   
   `python -m venv venv`

   `.\venv\Scripts\activate`

   `pip install -e .`

   `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload`

2. Em outro terminal, inicie o frontend (porta 5173):

   `cd .\frontend\`

   `pnpm install`

   `pnpm dev`

3. Abra no navegador:

   `http://localhost:5173`

## Pre-requisitos

1. Python 3.11+
2. Node.js 20+ e pnpm (para rodar o frontend Vite)
3. Arquivo `banco.db` na raiz do projeto (ou configure `DB_PATH` no `.env`)
4. Chave Gemini (Google AI Studio)

Se ainda nao tiver o pnpm instalado, rode:

`corepack enable`

## Setup para rodar apenas o agente

1. Criar ambiente virtual:

   `python -m venv venv`

2. Ativar ambiente virtual:

   `./venv/Scripts/Activate.ps1`

3. Instalar dependencias:

   `pip install -e .`

4. Criar `.env` a partir do exemplo:

   `Copy-Item .envexample .env`

5. Editar `.env` e preencher pelo menos:

   - `GOOGLE_API_KEY=sua_chave`
   - `MODEL_NAME=gemini-2.5-flash-lite`
   - `DB_PATH=./banco.db`

## Troubleshooting

### Erro de API key invalida/expirada (400)

1. Gere nova chave no Google AI Studio.
2. Atualize `GOOGLE_API_KEY` no `.env`.
3. Execute novamente com o ambiente virtual ativo.

### Erro de cota excedida (429)

1. Aguarde o tempo indicado na mensagem de erro.
2. Tente outra chave/projeto com cota disponivel.
3. Reduza testes repetidos em curto intervalo.

### Erro de banco nao encontrado

1. Confirme se `banco.db` esta na raiz do projeto.
2. Ou ajuste `DB_PATH` no `.env` para o caminho correto.

### SQL bloqueado por seguranca

O projeto permite apenas leitura (`SELECT`/`WITH ... SELECT`).
Comandos de escrita sao bloqueados por guardrails.