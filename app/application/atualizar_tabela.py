"""Caso de uso que atualiza a tabela demográfica."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from app.domain.tabela_demografica import (
    avisar_respostas_nao_classificadas,
    calcular_indicadores,
    montar_tabela_demografica,
)
from app.infrastructure.google_sheets import (
    autenticar_sheets,
    escrever_e_formatar_planilha,
    ler_dataframe_da_aba,
    localizar_aba_por_gid,
)


@dataclass(frozen=True)
class ResultadoAtualizacao:
    spreadsheet_id: str
    nome_aba_origem: str
    nome_aba_destino: str
    total_respostas: int
    total_linhas_tabela: int
    total_ja_realizaram: int
    total_nunca_realizaram: int
    total_conhecem: int

    @property
    def link_planilha(self) -> str:
        return (
            "https://docs.google.com/spreadsheets/d/"
            f"{self.spreadsheet_id}/edit"
        )

    def para_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "link_planilha": self.link_planilha,
        }


def atualizar_tabela(
    *,
    spreadsheet_id: str,
    gid_origem: int,
    aba_destino: str,
    credenciais: Path,
    informar: Callable[[str], None] = print,
) -> ResultadoAtualizacao:
    if not spreadsheet_id:
        raise ValueError(
            "O ID da planilha não foi configurado. Copie "
            "config.example.json para config.local.json e preencha os dados."
        )

    informar("[1/5] Autenticando na Google Sheets API...")
    conta, servico_sheets = autenticar_sheets(credenciais)
    informar(f"Conta autenticada: {conta.service_account_email}")

    informar(f"[2/5] Localizando a aba de origem pelo gid={gid_origem}...")
    nome_aba_origem = localizar_aba_por_gid(
        servico_sheets,
        spreadsheet_id,
        gid_origem,
    )
    if nome_aba_origem == aba_destino:
        raise ValueError(
            "A aba de origem e a aba de destino são a mesma. Escolha outro "
            "nome com --aba-destino para não apagar as respostas."
        )
    informar(f'Aba encontrada: "{nome_aba_origem}".')

    informar("[3/5] Lendo as respostas e montando o DataFrame...")
    dataframe = ler_dataframe_da_aba(
        servico_sheets,
        spreadsheet_id,
        nome_aba_origem,
    )
    if dataframe.empty:
        raise ValueError("Nenhuma resposta preenchida foi encontrada.")
    informar(f"DataFrame criado com {len(dataframe)} resposta(s).")
    avisar_respostas_nao_classificadas(dataframe)

    informar("[4/5] Calculando os cruzamentos demográficos...")
    tabela, linhas_de_secao = montar_tabela_demografica(dataframe)
    informar(f"Tabela calculada com {len(tabela) - 1} linha(s) de dados.")

    informar(f'[5/5] Atualizando a aba "{aba_destino}"...')
    escrever_e_formatar_planilha(
        servico_sheets,
        spreadsheet_id,
        aba_destino,
        tabela,
        linhas_de_secao,
    )
    informar("Concluído. A tabela foi atualizada a partir da própria planilha.")

    indicadores = calcular_indicadores(dataframe)
    return ResultadoAtualizacao(
        spreadsheet_id=spreadsheet_id,
        nome_aba_origem=nome_aba_origem,
        nome_aba_destino=aba_destino,
        total_respostas=indicadores.total_respostas,
        total_linhas_tabela=len(tabela) - 1,
        total_ja_realizaram=indicadores.total_ja_realizaram,
        total_nunca_realizaram=indicadores.total_nunca_realizaram,
        total_conhecem=indicadores.total_conhecem,
    )


def executar(args: argparse.Namespace) -> int:
    atualizar_tabela(
        spreadsheet_id=args.spreadsheet_id,
        gid_origem=args.gid_origem,
        aba_destino=args.aba_destino,
        credenciais=args.credenciais,
    )
    return 0
