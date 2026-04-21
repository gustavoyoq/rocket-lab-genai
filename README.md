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

### Setup

1. Criar ambiente virtual:

   `python -m venv venv`

2. Ativar ambiente virtual:

   `./venv/Scripts/Activate`

3. Instalar dependencias:

   `pip install -e .`

4. Criar `.env` a partir do exemplo:

   `Copy-Item .env.example .env`

5. Editar `.env` e preencher pelo menos:

   - `GOOGLE_API_KEY=sua_chave`
   - `MODEL_NAME=gemini-2.5-flash-lite`
   - `DB_PATH=./banco.db`


## Como executar

Antes de executar, confirme:

1. O ambiente virtual esta ativo.
2. O arquivo `banco.db` existe na raiz do projeto (ou `DB_PATH` aponta para o caminho correto).
3. O arquivo `.env` tem uma `GOOGLE_API_KEY` valida.

### Modo interativo

1. Rode:

   `python main.py`

2. O sistema deve mostrar:

   `Schema minimo da atividade validado.`

3. Digite perguntas no terminal, por exemplo:

   - `Top 10 produtos mais vendidos`
   - `Quantidade de pedidos por status`
   - `Estados com maior ticket medio`

4. Para sair, digite:

   - `sair`
   - `exit`
   - `q`

### Modo one-shot

1. Rode uma pergunta unica:

   `python main.py "Top 10 produtos mais vendidos"`

2. A aplicacao imprime:

   - `[TOOL CALL]` com a ferramenta usada
   - `[TOOL RESULT]` com resultado formatado
   - `Conclusao`
   - `SQL executado`
   - `Confianca`

## Validacao rapida (smoke test)

1. Teste basico:

   `python main.py "Quantidade de pedidos por status"`

2. Verifique se:

   - Nao houve erro de chave API
   - O SQL foi exibido
   - A resposta veio com conclusao analitica

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

## Guardrails implementados

- Apenas SQL `SELECT`
- Bloqueio de comandos perigosos (`UPDATE`, `DELETE`, `DROP`, etc.)
- Bloqueio de multiplas statements
- `LIMIT` padrao em consultas sem limite
- Timeout de execucao SQL
- Log de auditoria em `logs/query_audit.jsonl`