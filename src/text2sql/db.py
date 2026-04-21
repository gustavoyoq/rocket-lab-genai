from __future__ import annotations

import concurrent.futures
import json
import re
import sqlite3
import time
from pathlib import Path

from .models import QueryExecutionResult

READ_ONLY_RE = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE | re.DOTALL)
DANGEROUS_SQL_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH|DETACH|PRAGMA|VACUUM)\b",
    re.IGNORECASE,
)
FENCED_SQL_RE = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


class DatabaseManager:
    def __init__(self, db_path: Path, default_limit: int = 100, timeout_seconds: int = 8):
        self.db_path = Path(db_path)
        self.default_limit = default_limit
        self.timeout_seconds = timeout_seconds

    def _new_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def list_tables(self) -> list[str]:
        with self._new_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row["name"] for row in cursor.fetchall()]

    def describe_table(self, table_name: str) -> str:
        with self._new_connection() as conn:
            cursor = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            row = cursor.fetchone()
            if row is None:
                return f"Tabela '{table_name}' nao encontrada."
            return row["sql"] or ""

    def get_full_schema(self) -> str:
        schemas = [self.describe_table(t) for t in self.list_tables()]
        return "\n\n".join(schema for schema in schemas if schema)

    def _normalize_sql(self, sql: str) -> str:
        cleaned = (sql or "").strip()

        fenced_match = FENCED_SQL_RE.search(cleaned)
        if fenced_match:
            cleaned = fenced_match.group(1).strip()

        cleaned = re.sub(
            r"^\s*(SQL(?:\s+EXECUTADO)?|QUERY)\s*:\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        if cleaned.endswith(";"):
            cleaned = cleaned[:-1].strip()

        return cleaned

    def _assert_safe_select(self, sql: str) -> None:
        cleaned = self._normalize_sql(sql)
        if not READ_ONLY_RE.match(cleaned):
            raise ValueError("Somente consultas SELECT sao permitidas.")
        if DANGEROUS_SQL_RE.search(cleaned):
            raise ValueError("Comando SQL potencialmente perigoso detectado.")
        if ";" in cleaned:
            raise ValueError("Multiplas statements nao sao permitidas.")

    def _ensure_limit(self, sql: str) -> str:
        if re.search(r"\bLIMIT\b", sql, flags=re.IGNORECASE):
            return sql.strip().rstrip(";")
        return f"{sql.strip().rstrip(';')} LIMIT {self.default_limit}"

    def validate_sql(self, sql: str) -> tuple[bool, str]:
        safe_sql = self._ensure_limit(sql)
        try:
            with self._new_connection() as conn:
                conn.execute(f"EXPLAIN QUERY PLAN {safe_sql}")
            return True, "OK"
        except sqlite3.Error as exc:
            return False, str(exc)

    def run_query(self, sql: str) -> QueryExecutionResult:
        normalized_sql = self._normalize_sql(sql)
        self._assert_safe_select(normalized_sql)
        safe_sql = self._ensure_limit(normalized_sql)

        is_valid, message = self.validate_sql(safe_sql)
        if not is_valid:
            raise ValueError(f"SQL invalido para o schema atual: {message}")

        start = time.perf_counter()

        def _query_task() -> list[dict]:
            with self._new_connection() as conn:
                cursor = conn.execute(safe_sql)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_query_task)
            try:
                rows = future.result(timeout=self.timeout_seconds)
            except concurrent.futures.TimeoutError as exc:
                raise TimeoutError(
                    f"Consulta excedeu {self.timeout_seconds}s. Refine filtros e tente novamente."
                ) from exc

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        preview = rows[: min(20, len(rows))]

        return QueryExecutionResult(
            sql=safe_sql,
            row_count=len(rows),
            elapsed_ms=elapsed_ms,
            rows_preview=preview,
        )


class AuditLogger:
    def __init__(self, log_path: Path):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_query(self, user_question: str, result: QueryExecutionResult, status: str) -> None:
        payload = {
            "timestamp": int(time.time()),
            "status": status,
            "question": user_question,
            "execution": result.model_dump(),
        }
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")
