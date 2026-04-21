"""Modelos Pydantic de entrada e saída do agente."""

from __future__ import annotations

from typing import Annotated

from annotated_types import MinLen
from pydantic import BaseModel, Field


class AnalystResult(BaseModel):
    """Saída estruturada final do agente."""

    conclusion: Annotated[str, MinLen(80)] = Field(
        ..., description="Conclusao analitica em linguagem natural baseada nos resultados SQL, com interpretacao dos dados."
    )
    sql_executed: Annotated[str, MinLen(6)] = Field(
        ..., description="Consulta SQL de leitura executada para gerar a resposta."
    )
    confidence: str = Field(
        ..., description="Nível de confiança: high, medium ou low."
    )


class QueryExecutionResult(BaseModel):
    """Resultado da execução SQL para auditoria interna."""

    sql: str
    row_count: int
    elapsed_ms: int
    rows_preview: list[dict]
