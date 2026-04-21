"""CLI do projeto Text-to-SQL Rocket Lab."""

from __future__ import annotations

import asyncio
import sys

from src.text2sql.service import TextToSQLService


async def run_cli() -> None:
    service = TextToSQLService()

    ok, message = service.sanity_check_tables()
    print(message)

    if not ok:
        print("Ajuste o banco.db antes de continuar.")
        return

    history: list = []

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
        try:
            response, _ = await service.ask(question, history, verbose=True)
            print("\n" + "=" * 72)
            print(response)
            print("=" * 72)
        except Exception as exc:
            if "status_code: 429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                print(
                    "Erro 429: cota do Gemini excedida. "
                    "Aguarde o tempo de retry ou use outra chave/projeto com quota disponivel."
                )
            else:
                print(f"Erro: {type(exc).__name__}: {exc}")
        return

    print("\nPackIt - CLI interativa para gerenciamento de estoque e clientes")
    print("Digite sua pergunta ou 'sair' para encerrar.")

    while True:
        question = input("\nPergunta: ").strip()
        if question.lower() in {"sair", "exit", "quit", "q"}:
            print("Encerrando.")
            break
        if not question:
            continue

        try:
            response, history = await service.ask(question, history, verbose=True)
            print("\n" + "-" * 72)
            print(response)
            print("-" * 72)
        except Exception as exc:
            if "status_code: 429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                print(
                    "Erro 429: cota do Gemini excedida. "
                    "Aguarde o tempo de retry ou use outra chave/projeto com quota disponivel."
                )
            else:
                print(f"Erro: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    asyncio.run(run_cli())
