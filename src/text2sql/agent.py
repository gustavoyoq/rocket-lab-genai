from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from .db import AuditLogger, DatabaseManager
from .models import AnalystResult


@dataclass
class Deps:
    db: DatabaseManager
    audit: AuditLogger
    user_question: str


def build_agent(model_name: str, api_key: str) -> Agent:
    provider = GoogleProvider(api_key=api_key)
    model = GoogleModel(model_name, provider=provider)

    text2sql_agent = Agent(
        model,
        output_type=AnalystResult,
        deps_type=Deps,
        retries=3,
    )


    @text2sql_agent.system_prompt
    async def system_prompt(ctx: RunContext[Deps]) -> str:
        schema = ctx.deps.db.get_full_schema()
        return f"""\
Voce e um analista de dados especialista em SQLite para e-commerce.
Sua tarefa e responder perguntas de negocio com base em dados reais do banco.

Regras obrigatorias:
1. Gere SQL APENAS de leitura (SELECT).
2. Antes de concluir, voce deve executar a query usando a tool run_sql_query.
3. Nunca chute resultados: use somente dados retornados pela tool.
4. Se der erro, corrija a query e tente novamente.
5. Produza saida final com conclusion, sql_executed e confidence.
6. A conclusao deve ser ANALITICA: nao apenas listar top N ou repetir linhas.

Regra de qualidade da conclusao:
- Explique ao menos 2 insights obtidos dos dados (padroes, concentracao, empates, diferencas, outliers ou tendencia).
- Traga interpretacao de negocio (o que isso pode significar para vendas, estoque, operacao ou clientes).
- Quando houver ranking, cite brevemente a logica observada (ex.: lideranca isolada, empate, cauda longa).
- Evite resposta telegráfica; escreva um paragrafo analitico e coeso em portugues.
- Se os dados forem insuficientes, diga explicitamente a limitacao e como melhorar a consulta.

Schema atual:
{schema}

Data de hoje: {date.today()}
"""


    @text2sql_agent.tool
    async def run_sql_query(ctx: RunContext[Deps], sql: str) -> str:
        try:
            result = ctx.deps.db.run_query(sql)
            ctx.deps.audit.log_query(ctx.deps.user_question, result, status="success")

            if result.row_count == 0:
                return json.dumps(
                    {
                        "sql": result.sql,
                        "row_count": 0,
                        "message": "A consulta retornou 0 linhas. Tente ajustar filtros.",
                        "elapsed_ms": result.elapsed_ms,
                        "rows_preview": [],
                    },
                    ensure_ascii=False,
                )

            return json.dumps(
                {
                    "sql": result.sql,
                    "row_count": result.row_count,
                    "elapsed_ms": result.elapsed_ms,
                    "rows_preview": result.rows_preview,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            raise ModelRetry(f"Falha ao executar SQL no SQLite: {exc}")


    @text2sql_agent.tool
    async def list_tables(ctx: RunContext[Deps]) -> str:
        return ", ".join(ctx.deps.db.list_tables())


    @text2sql_agent.tool
    async def describe_table(ctx: RunContext[Deps], table_name: str) -> str:
        return ctx.deps.db.describe_table(table_name)

    return text2sql_agent
