"""Cálculos do cruzamento entre etnia e rede de atendimento."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.domain.tabela_demografica import (
    PERGUNTA_ETNIA,
    PERGUNTA_EXAME,
    PERGUNTA_REDE_ATENDIMENTO,
    classificar_exame,
    classificar_rede_atendimento,
    formatar_n_percentual,
    normalizar_texto,
)


ETNIAS = ["Branco", "Preto", "Pardo", "Indígena", "Amarelo"]


def classificar_etnia(valor: Any) -> str | None:
    """Agrupa variações de gênero e grafia nas cinco etnias solicitadas."""
    texto = normalizar_texto(valor)
    if texto in {"branco", "branca"}:
        return "Branco"
    if texto in {"preto", "preta", "negro", "negra"}:
        return "Preto"
    if texto in {"pardo", "parda"}:
        return "Pardo"
    if texto in {"indigena", "indigena brasileiro"}:
        return "Indígena"
    if texto in {"amarelo", "amarela"}:
        return "Amarelo"
    return None


def montar_tabela_etnia_rede(
    dataframe: pd.DataFrame,
) -> tuple[list[list[str]], int, int, int]:
    """Monta a tabela por rede e inclui quem nunca realizou o exame."""
    exame = dataframe[PERGUNTA_EXAME].map(classificar_exame)
    rede = dataframe[PERGUNTA_REDE_ATENDIMENTO].map(
        classificar_rede_atendimento
    )
    etnia = dataframe[PERGUNTA_ETNIA].map(classificar_etnia)

    realizou = exame.eq("Já realizou")
    rede_publica = realizou & rede.eq("Pública")
    rede_privada = realizou & rede.eq("Privada")
    nunca_realizou = exame.eq("Nunca realizou")
    total_publica = int(rede_publica.sum())
    total_privada = int(rede_privada.sum())
    total_nunca_realizou = int(nunca_realizou.sum())

    tabela = [
        [
            "Etnia",
            f"Rede privada\nTotal = {total_privada} (%)",
            f"Rede pública\nTotal = {total_publica} (%)",
            f"Nunca realizou\nTotal = {total_nunca_realizou} (%)",
        ]
    ]
    for categoria in ETNIAS:
        quantidade_privada = int((etnia.eq(categoria) & rede_privada).sum())
        quantidade_publica = int((etnia.eq(categoria) & rede_publica).sum())
        quantidade_nunca_realizou = int(
            (etnia.eq(categoria) & nunca_realizou).sum()
        )
        tabela.append(
            [
                categoria,
                formatar_n_percentual(quantidade_privada, total_privada),
                formatar_n_percentual(quantidade_publica, total_publica),
                formatar_n_percentual(
                    quantidade_nunca_realizou,
                    total_nunca_realizou,
                ),
            ]
        )

    tabela.append(
        [
            "TOTAL",
            formatar_n_percentual(total_privada, total_privada),
            formatar_n_percentual(total_publica, total_publica),
            formatar_n_percentual(
                total_nunca_realizou,
                total_nunca_realizou,
            ),
        ]
    )
    return tabela, total_privada, total_publica, total_nunca_realizou
