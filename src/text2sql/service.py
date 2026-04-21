"""Orquestracao do fluxo pergunta -> SQL -> resposta."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .agent import Deps, build_agent
from .config import Settings, load_settings
from .db import AuditLogger, DatabaseManager


class TextToSQLService:
    """Servico principal do agente Text-to-SQL."""

    def __init__(self, settings: Settings | None = None):
        # Carrega sempre o .env do proprio projeto para evitar conflito
        # com outros arquivos .env existentes no workspace.
        project_root = Path(__file__).resolve().parents[2]
        env_path = project_root / ".env"
        load_dotenv(dotenv_path=env_path, override=True)
        self.settings = settings or load_settings()

        if not self.settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY nao configurada. Defina no .env")

        if not self.settings.db_path.exists():
            raise FileNotFoundError(
                f"Banco SQLite nao encontrado em: {self.settings.db_path}"
            )

        self.db = DatabaseManager(
            db_path=self.settings.db_path,
            default_limit=self.settings.query_row_limit,
            timeout_seconds=self.settings.query_timeout_seconds,
        )
        self.audit = AuditLogger(Path("./logs/query_audit.jsonl"))
        self.agent = build_agent(
            model_name=self.settings.model_name,
            api_key=self.settings.google_api_key,
        )

    @staticmethod
    def _extract_retry_seconds(error_message: str) -> int | None:
        """Extrai o tempo de espera sugerido pela API em mensagens de rate limit."""
        match = re.search(r"Please retry in\s*([0-9]+(?:\.[0-9]+)?)s", error_message)
        if not match:
            return None
        return max(1, int(float(match.group(1))))

    @staticmethod
    def _format_ascii_table(rows: list[dict[str, Any]]) -> str:
        """Formata linhas em tabela textual simples com índice."""
        if not rows:
            return "(0 linhas)"

        columns: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in columns:
                    columns.append(key)

        def stringify(value: Any) -> str:
            if value is None:
                return "NULL"
            return str(value)

        widths = {column: len(column) for column in columns}
        widths["#"] = max(1, len(str(len(rows))))
        normalized_rows: list[dict[str, str]] = []
        for row in rows:
            normalized = {column: stringify(row.get(column, "")) for column in columns}
            normalized_rows.append(normalized)
            for column, value in normalized.items():
                widths[column] = max(widths[column], len(value))

        def render_header() -> str:
            parts = [f"{'#':<{widths['#']}}"]
            parts.extend(f"{column:<{widths[column]}}" for column in columns)
            return "  ".join(parts)

        def render_row(index: int, values: dict[str, str]) -> str:
            parts = [f"{index:<{widths['#']}}"]
            parts.extend(f"{values[column]:<{widths[column]}}" for column in columns)
            return "  ".join(parts)

        lines = [render_header()]
        for idx, row in enumerate(normalized_rows, start=1):
            lines.append(render_row(idx, row))
        return "\n".join(lines)

    async def ask(
        self,
        question: str,
        message_history: list[Any] | None = None,
        verbose: bool = True,
    ) -> tuple[str, list[Any]]:
        """Executa uma pergunta no agente e retorna resposta + historico atualizado."""
        history = message_history or []
        deps = Deps(db=self.db, audit=self.audit, user_question=question)

        # Faz 1 retry automatico para erros de quota temporaria (429).
        max_attempts = 3
        lines: list[str] = []
        tool_call_name = ""
        tool_result_text = ""
        result = None
        current_question = question

        for attempt in range(max_attempts):
            lines = []
            tool_call_name = ""
            try:
                async with self.agent.iter(current_question, deps=deps, message_history=history) as run:
                    async for node in run:
                        if self.agent.is_call_tools_node(node):
                            async with node.stream(run.ctx) as stream:
                                async for event in stream:
                                    tool_name = getattr(getattr(event, "part", None), "tool_name", None)
                                    if tool_name and verbose and not tool_call_name:
                                        tool_call_name = tool_name

                                    if hasattr(event, "result"):
                                        result_payload = getattr(event.result, "content", None)
                                        if isinstance(result_payload, str):
                                            tool_result_text = result_payload
                                        elif result_payload is not None:
                                            tool_result_text = str(result_payload)

                    result = run.result

                # Reparo automatico: força nova tentativa quando a query nao eh aceita.
                if (
                    "Somente consultas SELECT sao permitidas." in tool_result_text
                    or "Comando SQL potencialmente perigoso detectado." in tool_result_text
                ) and attempt < max_attempts - 1:
                    current_question = (
                        f"{question}\n\n"
                        "A tentativa anterior falhou por violar regra de leitura. "
                        "Tente novamente com uma consulta estritamente SELECT (ou WITH ... SELECT), "
                        "sem comandos de escrita e sem multiplas statements."
                    )
                    continue

                break
            except Exception as exc:
                error_text = str(exc)
                is_rate_limited = "status_code: 429" in error_text or "RESOURCE_EXHAUSTED" in error_text
                is_last_attempt = attempt == max_attempts - 1
                if not is_rate_limited or is_last_attempt:
                    raise

                wait_seconds = self._extract_retry_seconds(str(exc)) or 60
                if verbose:
                    lines.append(
                        f"[RATE LIMIT] Limite temporario atingido. Tentando novamente em {wait_seconds}s..."
                    )
                await asyncio.sleep(wait_seconds + 1)

        if result is None:
            raise RuntimeError("Falha inesperada ao obter resultado do agente.")

        output = result.output
        formatted_tool_result = tool_result_text
        if tool_result_text and verbose:
            try:
                parsed = json.loads(tool_result_text)
                if isinstance(parsed, dict):
                    rows_preview = parsed.get("rows_preview", [])
                    if isinstance(rows_preview, list):
                        formatted_tool_result = self._format_ascii_table(rows_preview)
            except json.JSONDecodeError:
                pass

        response = (
            (f"[TOOL CALL] {tool_call_name}\n\n" if tool_call_name and verbose else "")
            + ("\n".join(lines) + "\n\n" if lines else "")
            + (f"[TOOL RESULT]\n{formatted_tool_result}\n\n" if tool_result_text and verbose else "")
            + f"Conclusao: {output.conclusion}\n\n"
            + f"SQL executado: {output.sql_executed}\n\n"
            + f"Confianca: {output.confidence}"
        )

        new_history = history + result.new_messages()
        # Janela deslizante para evitar crescimento indefinido.
        max_messages = self.settings.max_history_messages
        if len(new_history) > max_messages:
            new_history = new_history[-max_messages:]

        return response, new_history

    def sanity_check_tables(self) -> tuple[bool, str]:
        """Confere se as tabelas esperadas do enunciado estao presentes."""
        expected = {
            "dim_consumidores",
            "dim_produtos",
            "dim_vendedores",
            "fat_pedidos",
            "fat_pedido_total",
            "fat_itens_pedidos",
            "fat_avaliacoes_pedidos",
        }
        existing = set(self.db.list_tables())
        missing = sorted(expected - existing)
        if missing:
            return False, f"Tabelas ausentes: {', '.join(missing)}"
        return True, "Schema minimo da atividade validado."
