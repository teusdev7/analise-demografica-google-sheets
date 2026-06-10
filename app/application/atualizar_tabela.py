"""Caso de uso que atualiza a tabela demográfica."""

from __future__ import annotations

import argparse

from app.domain.tabela_demografica import (
    avisar_respostas_nao_classificadas,
    montar_tabela_demografica,
)
from app.infrastructure.google_sheets import (
    autenticar_sheets,
    escrever_e_formatar_planilha,
    ler_dataframe_da_aba,
    localizar_aba_por_gid,
)


def executar(args: argparse.Namespace) -> int:
    if not args.spreadsheet_id:
        raise ValueError(
            "O ID da planilha não foi configurado. Copie "
            "config.example.json para config.local.json e preencha os dados."
        )

    print("[1/5] Autenticando na Google Sheets API...")
    credenciais, servico_sheets = autenticar_sheets(args.credenciais)
    print(f"  Conta autenticada: {credenciais.service_account_email}")

    print(f"[2/5] Localizando a aba de origem pelo gid={args.gid_origem}...")
    nome_aba_origem = localizar_aba_por_gid(
        servico_sheets,
        args.spreadsheet_id,
        args.gid_origem,
    )
    if nome_aba_origem == args.aba_destino:
        raise ValueError(
            "A aba de origem e a aba de destino são a mesma. Escolha outro "
            "nome com --aba-destino para não apagar as respostas."
        )
    print(f'  Aba encontrada: "{nome_aba_origem}".')

    print("[3/5] Lendo as respostas e montando o DataFrame...")
    dataframe = ler_dataframe_da_aba(
        servico_sheets,
        args.spreadsheet_id,
        nome_aba_origem,
    )
    if dataframe.empty:
        raise ValueError("Nenhuma resposta preenchida foi encontrada.")
    print(f"  DataFrame criado com {len(dataframe)} resposta(s).")
    avisar_respostas_nao_classificadas(dataframe)

    print("[4/5] Calculando os cruzamentos demográficos...")
    tabela, linhas_de_secao = montar_tabela_demografica(dataframe)
    print(f"  Tabela calculada com {len(tabela) - 1} linha(s) de dados.")

    print(f'[5/5] Atualizando a aba "{args.aba_destino}"...')
    escrever_e_formatar_planilha(
        servico_sheets,
        args.spreadsheet_id,
        args.aba_destino,
        tabela,
        linhas_de_secao,
    )
    print("Concluído. A tabela foi atualizada a partir da própria planilha.")
    return 0
