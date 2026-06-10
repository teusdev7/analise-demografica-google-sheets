"""Interface web local da aplicação."""

from __future__ import annotations

import argparse
import re
import threading
import webbrowser
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
from googleapiclient.errors import HttpError

from app.application.atualizar_tabela import atualizar_tabela
from app.config import (
    ARQUIVO_CREDENCIAIS,
    GID_ABA_ORIGEM,
    NOME_ABA_DESTINO,
    SPREADSHEET_ID,
)


PADRAO_URL_PLANILHA = re.compile(
    r"https?://docs\.google\.com/spreadsheets/d/([^/?#]+)",
    re.IGNORECASE,
)


def extrair_spreadsheet_id(valor: str) -> str:
    """Aceita uma URL completa do Sheets ou somente o ID."""
    texto = valor.strip()
    correspondencia = PADRAO_URL_PLANILHA.search(texto)
    if correspondencia:
        return correspondencia.group(1)
    return texto


def validar_gid(valor: Any) -> int:
    try:
        gid = int(valor)
    except (TypeError, ValueError) as erro:
        raise ValueError("O GID da aba de origem deve ser um número.") from erro
    if gid < 0:
        raise ValueError("O GID da aba de origem não pode ser negativo.")
    return gid


def criar_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False

    @app.get("/")
    def pagina_inicial() -> str:
        url_planilha = (
            "https://docs.google.com/spreadsheets/d/"
            f"{SPREADSHEET_ID}/edit"
            if SPREADSHEET_ID
            else ""
        )
        return render_template(
            "index.html",
            url_planilha=url_planilha,
            gid_aba_origem=GID_ABA_ORIGEM,
            nome_aba_destino=NOME_ABA_DESTINO,
            credenciais_prontas=ARQUIVO_CREDENCIAIS.is_file(),
        )

    @app.get("/health")
    def health() -> Any:
        return jsonify(
            status="ok",
            credenciais_prontas=ARQUIVO_CREDENCIAIS.is_file(),
        )

    @app.post("/api/atualizar")
    def api_atualizar() -> Any:
        dados = request.get_json(silent=True) or {}
        spreadsheet_id = extrair_spreadsheet_id(
            str(dados.get("planilha", ""))
        )
        if not spreadsheet_id:
            return jsonify(
                sucesso=False,
                mensagem="Informe a URL ou o ID da planilha.",
            ), 400

        try:
            gid_origem = validar_gid(dados.get("gid_origem"))
            aba_destino = str(dados.get("aba_destino", "")).strip()
            if not aba_destino:
                raise ValueError("Informe o nome da aba de destino.")
            if len(aba_destino) > 100:
                raise ValueError(
                    "O nome da aba de destino deve ter até 100 caracteres."
                )

            mensagens: list[str] = []
            resultado = atualizar_tabela(
                spreadsheet_id=spreadsheet_id,
                gid_origem=gid_origem,
                aba_destino=aba_destino,
                credenciais=ARQUIVO_CREDENCIAIS,
                informar=mensagens.append,
            )
            return jsonify(
                sucesso=True,
                mensagem="Tabela atualizada com sucesso.",
                resultado=resultado.para_dict(),
                etapas=mensagens,
            )
        except (FileNotFoundError, ValueError, OSError) as erro:
            return jsonify(
                sucesso=False,
                mensagem=str(erro),
            ), 400
        except HttpError as erro:
            status = getattr(erro.resp, "status", 500)
            mensagem = (
                "Não foi possível acessar o Google Sheets. Verifique o "
                "compartilhamento da planilha e a ativação da API."
                if status in (401, 403, 404)
                else "A API do Google retornou um erro inesperado."
            )
            return jsonify(
                sucesso=False,
                mensagem=mensagem,
            ), int(status) if isinstance(status, int) else 500

    return app


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inicia a interface web local do Demografia Sheets."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Endereço local do servidor (padrão: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Porta do servidor (padrão: 5000).",
    )
    parser.add_argument(
        "--sem-navegador",
        action="store_true",
        help="Não abre o navegador automaticamente.",
    )
    return parser


def main() -> int:
    args = criar_parser().parse_args()
    url = f"http://{args.host}:{args.port}"
    if not args.sem_navegador:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print(f"Interface disponível em {url}")
    criar_app().run(
        host=args.host,
        port=args.port,
        debug=False,
        use_reloader=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
