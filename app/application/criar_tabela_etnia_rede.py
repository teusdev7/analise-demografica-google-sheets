"""Caso de uso para criar a aba de etnia por rede de atendimento."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.domain.etnia_rede import montar_tabela_etnia_rede
from app.infrastructure.google_sheets import (
    autenticar_sheets,
    criar_requisicoes_formatacao,
    escapar_nome_aba,
    ler_dataframe_da_aba,
    localizar_aba_por_gid,
    obter_ou_criar_aba,
)


@dataclass(frozen=True)
class ResultadoEtniaRede:
    nome_aba: str
    gid_aba: int
    total_privada: int
    total_publica: int
    total_nunca_realizou: int
    tabela: list[list[str]]
    link: str


def criar_tabela_etnia_rede(
    *,
    spreadsheet_id: str,
    gid_origem: int,
    nome_aba: str,
    credenciais: Path,
    informar: Callable[[str], None] = print,
) -> ResultadoEtniaRede:
    informar("Autenticando na Google Sheets API")
    _, servico = autenticar_sheets(credenciais)
    informar("Localizando e lendo a aba de respostas")
    aba_origem = localizar_aba_por_gid(servico, spreadsheet_id, gid_origem)
    dataframe = ler_dataframe_da_aba(servico, spreadsheet_id, aba_origem)
    informar(f"{len(dataframe)} respostas carregadas")

    informar("Classificando etnias e redes de atendimento")
    (
        tabela,
        total_privada,
        total_publica,
        total_nunca_realizou,
    ) = montar_tabela_etnia_rede(dataframe)
    informar(
        f"Cálculo concluído: privada={total_privada}, pública={total_publica}, "
        f"nunca realizou={total_nunca_realizou}"
    )

    informar(f'Criando ou localizando a aba "{nome_aba}"')
    sheet_id = obter_ou_criar_aba(servico, spreadsheet_id, nome_aba)
    aba_a1 = escapar_nome_aba(nome_aba)
    informar("Limpando os dados anteriores da aba de destino")
    servico.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"'{aba_a1}'!A:D",
        body={},
    ).execute()
    informar("Escrevendo a tabela de etnia por rede")
    servico.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{aba_a1}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": tabela},
    ).execute()
    informar("Aplicando cabeçalho, bordas e ajuste de colunas")
    requisicoes = criar_requisicoes_formatacao(
        sheet_id=sheet_id,
        quantidade_linhas=len(tabela),
        linhas_de_secao=[len(tabela) - 1],
        quantidade_colunas=4,
    )
    servico.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requisicoes},
    ).execute()

    informar("Conferindo a tabela gravada célula por célula")
    tabela_gravada = (
        servico.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=f"'{aba_a1}'!A1:D{len(tabela)}",
        )
        .execute()
        .get("values", [])
    )
    if tabela_gravada != tabela:
        raise ValueError(
            "A conferência final encontrou diferenças na tabela gravada."
        )
    informar("Conferência concluída sem divergências")

    link = (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        f"?gid={sheet_id}#gid={sheet_id}"
    )
    return ResultadoEtniaRede(
        nome_aba=nome_aba,
        gid_aba=sheet_id,
        total_privada=total_privada,
        total_publica=total_publica,
        total_nunca_realizou=total_nunca_realizou,
        tabela=tabela,
        link=link,
    )
