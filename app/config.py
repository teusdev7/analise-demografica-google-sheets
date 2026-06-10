"""Carrega configuração pública e local da aplicação."""

import json
import os
from pathlib import Path
from typing import Any


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_CONFIG_LOCAL = RAIZ_PROJETO / "config.local.json"


def carregar_configuracao_local() -> dict[str, Any]:
    if not ARQUIVO_CONFIG_LOCAL.is_file():
        return {}
    with ARQUIVO_CONFIG_LOCAL.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def resolver_caminho(valor: str) -> Path:
    caminho = Path(valor)
    if caminho.is_absolute():
        return caminho
    return RAIZ_PROJETO / caminho


_configuracao = carregar_configuracao_local()

SPREADSHEET_ID = os.getenv(
    "SPREADSHEET_ID",
    str(_configuracao.get("spreadsheet_id", "")),
)
GID_ABA_ORIGEM = int(
    os.getenv(
        "GID_ABA_ORIGEM",
        str(_configuracao.get("gid_aba_origem", 0)),
    )
)
NOME_ABA_DESTINO = os.getenv(
    "NOME_ABA_DESTINO",
    str(_configuracao.get("nome_aba_destino", "Planilha1")),
)
ARQUIVO_CREDENCIAIS = resolver_caminho(
    os.getenv(
        "ARQUIVO_CREDENCIAIS",
        str(
            _configuracao.get(
                "arquivo_credenciais",
                "credentials/credenciais.json",
            )
        ),
    )
)

GOOGLE_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]
