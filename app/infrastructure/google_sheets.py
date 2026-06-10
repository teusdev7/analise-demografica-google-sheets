"""Acesso, leitura, escrita e formatação no Google Sheets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.config import GOOGLE_SHEETS_SCOPES
from app.domain.tabela_demografica import PERGUNTAS_OBRIGATORIAS


def escapar_nome_aba(nome_aba: str) -> str:
    return nome_aba.replace("'", "''")


def autenticar_sheets(caminho_credenciais: Path) -> tuple[Any, Any]:
    """Autentica a conta de serviço e cria o cliente da Google Sheets API."""
    if not caminho_credenciais.is_file():
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado: {caminho_credenciais}"
        )

    credenciais = service_account.Credentials.from_service_account_file(
        str(caminho_credenciais),
        scopes=GOOGLE_SHEETS_SCOPES,
    )
    servico_sheets = build(
        "sheets",
        "v4",
        credentials=credenciais,
        cache_discovery=False,
    )
    return credenciais, servico_sheets


def localizar_aba_por_gid(
    servico_sheets: Any,
    spreadsheet_id: str,
    gid: int,
) -> str:
    """Converte o gid da URL no título atual da aba."""
    metadados = (
        servico_sheets.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            fields="sheets.properties(sheetId,title)",
        )
        .execute()
    )
    for aba in metadados.get("sheets", []):
        propriedades = aba.get("properties", {})
        if int(propriedades.get("sheetId", -1)) == gid:
            return str(propriedades["title"])

    gids = [
        str(aba.get("properties", {}).get("sheetId"))
        for aba in metadados.get("sheets", [])
    ]
    raise ValueError(
        f"A aba com gid={gid} não foi encontrada. GIDs disponíveis: "
        + ", ".join(gids)
    )


def ler_dataframe_da_aba(
    servico_sheets: Any,
    spreadsheet_id: str,
    nome_aba: str,
) -> pd.DataFrame:
    """Lê todas as células preenchidas e usa a primeira linha como cabeçalho."""
    aba_a1 = escapar_nome_aba(nome_aba)
    valores = (
        servico_sheets.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=f"'{aba_a1}'",
            majorDimension="ROWS",
        )
        .execute()
        .get("values", [])
    )
    if not valores:
        raise ValueError(f'A aba "{nome_aba}" está vazia.')

    cabecalhos = [str(valor).strip() for valor in valores[0]]
    duplicados = sorted(
        {
            cabecalho
            for cabecalho in cabecalhos
            if cabecalho and cabecalhos.count(cabecalho) > 1
        }
    )
    if duplicados:
        raise ValueError(
            "Há cabeçalhos duplicados na aba de origem: "
            + " | ".join(duplicados)
        )

    ausentes = [
        pergunta
        for pergunta in PERGUNTAS_OBRIGATORIAS
        if pergunta not in cabecalhos
    ]
    if ausentes:
        raise ValueError(
            "Cabeçalhos obrigatórios não encontrados: "
            + " | ".join(ausentes)
            + ". Cabeçalhos disponíveis: "
            + " | ".join(cabecalhos)
        )

    registros: list[list[str]] = []
    for linha in valores[1:]:
        linha_completa = [*linha, *([""] * (len(cabecalhos) - len(linha)))]
        linha_completa = linha_completa[: len(cabecalhos)]
        if any(str(valor).strip() for valor in linha_completa):
            registros.append(linha_completa)

    dataframe_completo = pd.DataFrame(registros, columns=cabecalhos)
    return dataframe_completo[PERGUNTAS_OBRIGATORIAS].fillna("")


def obter_ou_criar_aba(
    servico_sheets: Any,
    spreadsheet_id: str,
    nome_aba: str,
) -> int:
    metadados = (
        servico_sheets.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            fields="sheets.properties(sheetId,title)",
        )
        .execute()
    )
    for aba in metadados.get("sheets", []):
        propriedades = aba.get("properties", {})
        if propriedades.get("title") == nome_aba:
            return int(propriedades["sheetId"])

    print(f'  A aba "{nome_aba}" não existe; criando...')
    resultado = (
        servico_sheets.spreadsheets()
        .batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {"addSheet": {"properties": {"title": nome_aba}}}
                ]
            },
        )
        .execute()
    )
    return int(
        resultado["replies"][0]["addSheet"]["properties"]["sheetId"]
    )


def criar_requisicoes_formatacao(
    sheet_id: int,
    quantidade_linhas: int,
    linhas_de_secao: list[int],
    quantidade_colunas: int,
) -> list[dict[str, Any]]:
    azul = {"red": 0.12, "green": 0.31, "blue": 0.47}
    azul_claro = {"red": 0.85, "green": 0.92, "blue": 0.97}
    branco = {"red": 1.0, "green": 1.0, "blue": 1.0}
    preto = {"red": 0.0, "green": 0.0, "blue": 0.0}
    cinza = {"red": 0.65, "green": 0.70, "blue": 0.74}
    intervalo_tabela = {
        "sheetId": sheet_id,
        "startRowIndex": 0,
        "endRowIndex": quantidade_linhas,
        "startColumnIndex": 0,
        "endColumnIndex": quantidade_colunas,
    }

    requisicoes: list[dict[str, Any]] = [
        {
            "repeatCell": {
                "range": intervalo_tabela,
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": branco,
                        "textFormat": {
                            "bold": False,
                            "foregroundColor": preto,
                        },
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "WRAP",
                    }
                },
                "fields": (
                    "userEnteredFormat(backgroundColor,textFormat,"
                    "verticalAlignment,wrapStrategy)"
                ),
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": quantidade_colunas,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": azul,
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": branco,
                        },
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "WRAP",
                    }
                },
                "fields": "userEnteredFormat",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 1,
                    "endRowIndex": quantidade_linhas,
                    "startColumnIndex": 1,
                    "endColumnIndex": quantidade_colunas,
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat.horizontalAlignment",
            }
        },
        {
            "updateBorders": {
                "range": intervalo_tabela,
                **{
                    lado: {"style": "SOLID", "color": cinza}
                    for lado in (
                        "top",
                        "bottom",
                        "left",
                        "right",
                        "innerHorizontal",
                        "innerVertical",
                    )
                },
            }
        },
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": quantidade_colunas,
                }
            }
        },
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
    ]

    for linha in linhas_de_secao:
        requisicoes.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": linha,
                        "endRowIndex": linha + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": quantidade_colunas,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": azul_claro,
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": azul,
                            },
                        }
                    },
                    "fields": (
                        "userEnteredFormat(backgroundColor,textFormat)"
                    ),
                }
            }
        )

    return requisicoes


def escrever_e_formatar_planilha(
    servico_sheets: Any,
    spreadsheet_id: str,
    nome_aba: str,
    tabela: list[list[str]],
    linhas_de_secao: list[int],
) -> None:
    """Cria ou limpa a aba de destino, escreve os dados e formata a tabela."""
    sheet_id = obter_ou_criar_aba(servico_sheets, spreadsheet_id, nome_aba)
    quantidade_linhas = len(tabela)
    quantidade_colunas = max(len(linha) for linha in tabela)
    intervalo_destino = f"'{escapar_nome_aba(nome_aba)}'!A:G"
    corpo_requisicao = {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {
                "range": f"'{escapar_nome_aba(nome_aba)}'!A1",
                "values": tabela,
            }
        ],
    }
    requisicoes_formatacao = criar_requisicoes_formatacao(
        sheet_id,
        quantidade_linhas,
        linhas_de_secao,
        quantidade_colunas,
    )
    servico_sheets.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=intervalo_destino,
        body={},
    ).execute()
    servico_sheets.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=corpo_requisicao,
    ).execute()
    servico_sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requisicoes_formatacao},
    ).execute()
    print(f'  Aba "{nome_aba}" atualizada com sucesso.')
    print(f"  Linhas: {quantidade_linhas} | Colunas: {quantidade_colunas}")
