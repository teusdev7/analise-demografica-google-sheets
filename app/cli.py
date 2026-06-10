"""Interface de linha de comando."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from googleapiclient.errors import HttpError

from app.application.atualizar_tabela import executar
from app.config import (
    ARQUIVO_CREDENCIAIS,
    GID_ABA_ORIGEM,
    NOME_ABA_DESTINO,
    SPREADSHEET_ID,
)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Lê respostas de uma aba do Google Sheets e atualiza a tabela "
            "demográfica em outra aba da mesma planilha."
        )
    )
    parser.add_argument(
        "--spreadsheet-id",
        default=SPREADSHEET_ID,
        help=f"ID da planilha (padrão: {SPREADSHEET_ID}).",
    )
    parser.add_argument(
        "--gid-origem",
        type=int,
        default=GID_ABA_ORIGEM,
        help=f"GID da aba com respostas (padrão: {GID_ABA_ORIGEM}).",
    )
    parser.add_argument(
        "--aba-destino",
        default=NOME_ABA_DESTINO,
        help=f'Nome da aba de destino (padrão: "{NOME_ABA_DESTINO}").',
    )
    parser.add_argument(
        "--credenciais",
        type=Path,
        default=ARQUIVO_CREDENCIAIS,
        help=f"Arquivo da conta de serviço (padrão: {ARQUIVO_CREDENCIAIS}).",
    )
    return parser


def main() -> int:
    args = criar_parser().parse_args()
    try:
        return executar(args)
    except (FileNotFoundError, ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
    except HttpError as erro:
        status = getattr(erro.resp, "status", "desconhecido")
        print(f"Erro da API Google (HTTP {status}): {erro}", file=sys.stderr)
        if status in (401, 403, 404):
            print(
                "Verifique se a planilha foi compartilhada com a conta de "
                "serviço e se a Google Sheets API está ativada.",
                file=sys.stderr,
            )
    return 1
