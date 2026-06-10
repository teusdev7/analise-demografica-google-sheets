"""Classificação e cálculos da tabela demográfica."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd


PERGUNTA_IDADE = "Idade"
PERGUNTA_ESCOLARIDADE = "Escolaridade"
PERGUNTA_ETNIA = "Cor/Etnia"
PERGUNTA_PARCEIRO = "Você possui parceiro fixo?"
PERGUNTA_EXAME = (
    "Já realizou o exame? Se sim, com que frequência? Em qual período do ano?"
)
PERGUNTA_CONHECIMENTO = "Você sabe o que é o Papanicolau"

PERGUNTAS_OBRIGATORIAS = [
    PERGUNTA_IDADE,
    PERGUNTA_ESCOLARIDADE,
    PERGUNTA_ETNIA,
    PERGUNTA_PARCEIRO,
    PERGUNTA_EXAME,
    PERGUNTA_CONHECIMENTO,
]


@dataclass(frozen=True)
class IndicadoresDemograficos:
    total_respostas: int
    total_ja_realizaram: int
    total_nunca_realizaram: int
    total_conhecem: int


def normalizar_texto(valor: Any) -> str:
    """Normaliza texto para comparações sem diferenças de acento ou caixa."""
    if valor is None or pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor).strip().lower())
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def limpar_texto(valor: Any) -> str:
    if valor is None or pd.isna(valor):
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def classificar_idade(valor: Any) -> str | None:
    """Converte idades e faixas nas duas categorias da tabela."""
    texto = normalizar_texto(valor)
    if not texto:
        return None
    if "ate 23" in texto:
        return "Até 23 anos"
    if "23 anos ou mais" in texto or "23 ou mais" in texto:
        return "23 anos ou mais"

    numeros = [int(numero) for numero in re.findall(r"\b\d{1,3}\b", texto)]
    idades = [numero for numero in numeros if 10 <= numero <= 120]
    if not idades:
        return None
    if len(idades) >= 2:
        inicio, fim = idades[0], idades[1]
        if fim <= 23:
            return "Até 23 anos"
        if inicio >= 23:
            return "23 anos ou mais"
    return "Até 23 anos" if idades[0] <= 23 else "23 anos ou mais"


def classificar_parceiro(valor: Any) -> str | None:
    texto = normalizar_texto(valor)
    if texto == "sim":
        return "Possui parceiro fixo"
    if texto == "nao":
        return "Não possui parceiro fixo"
    return None


def classificar_exame(valor: Any) -> str | None:
    texto = normalizar_texto(valor)
    if not texto:
        return None
    if texto == "nao":
        return "Nunca realizou"
    return "Já realizou"


def conhece_papanicolau(valor: Any) -> bool:
    return normalizar_texto(valor) == "sim"


def valores_unicos(serie: pd.Series) -> list[str]:
    """Retorna os valores preenchidos em ordem alfabética."""
    valores = {
        limpar_texto(valor)
        for valor in serie
        if limpar_texto(valor)
    }
    return sorted(valores, key=normalizar_texto)


def formatar_n_percentual(n: int, denominador: int) -> str:
    percentual = (n / denominador * 100) if denominador else 0
    return f"{n} ({percentual:.1f}%)".replace(".", ",")


def calcular_indicadores(
    dataframe: pd.DataFrame,
) -> IndicadoresDemograficos:
    realizacao_exame = dataframe[PERGUNTA_EXAME].map(classificar_exame)
    conhecimento = dataframe[PERGUNTA_CONHECIMENTO].map(conhece_papanicolau)
    return IndicadoresDemograficos(
        total_respostas=len(dataframe),
        total_ja_realizaram=int(
            realizacao_exame.eq("Já realizou").sum()
        ),
        total_nunca_realizaram=int(
            realizacao_exame.eq("Nunca realizou").sum()
        ),
        total_conhecem=int(conhecimento.sum()),
    )


def montar_tabela_demografica(
    dataframe: pd.DataFrame,
) -> tuple[list[list[str]], list[int]]:
    """Calcula contagens e percentuais por coluna."""
    indicadores = calcular_indicadores(dataframe)
    faixa_idade = dataframe[PERGUNTA_IDADE].map(classificar_idade)
    situacao_conjugal = dataframe[PERGUNTA_PARCEIRO].map(classificar_parceiro)
    realizacao_exame = dataframe[PERGUNTA_EXAME].map(classificar_exame)
    conhecimento = dataframe[PERGUNTA_CONHECIMENTO].map(conhece_papanicolau)

    escolaridade = dataframe[PERGUNTA_ESCOLARIDADE].map(limpar_texto)
    etnia = dataframe[PERGUNTA_ETNIA].map(limpar_texto)

    secoes: list[tuple[str, pd.Series, list[str]]] = [
        ("IDADE", faixa_idade, ["Até 23 anos", "23 anos ou mais"]),
        ("ESCOLARIDADE", escolaridade, valores_unicos(escolaridade)),
        ("ETNIA AUTODECLARADA", etnia, valores_unicos(etnia)),
        (
            "SITUAÇÃO CONJUGAL",
            situacao_conjugal,
            ["Possui parceiro fixo", "Não possui parceiro fixo"],
        ),
    ]

    tabela: list[list[str]] = [
        [
            "Dados demográficos",
            f"Total = {indicadores.total_respostas} (%)",
            (
                "Já realizaram o exame preventivo (Papanicolau)\n"
                f"Total = {indicadores.total_ja_realizaram} (%)"
            ),
            (
                "Nunca realizaram o exame preventivo\n"
                f"Total = {indicadores.total_nunca_realizaram} (%)"
            ),
            (
                "Conhecimento sobre o Papanicolau\n"
                f"Total = {indicadores.total_conhecem} (%)"
            ),
        ]
    ]
    linhas_de_secao: list[int] = []

    for titulo_secao, serie_grupo, categorias in secoes:
        linhas_de_secao.append(len(tabela))
        tabela.append([titulo_secao, "", "", "", ""])

        for categoria in categorias:
            mascara = serie_grupo.eq(categoria)
            total_categoria = int(mascara.sum())
            ja_realizaram = int(
                (mascara & realizacao_exame.eq("Já realizou")).sum()
            )
            nunca_realizaram = int(
                (mascara & realizacao_exame.eq("Nunca realizou")).sum()
            )
            conhecem = int((mascara & conhecimento).sum())

            tabela.append(
                [
                    categoria,
                    formatar_n_percentual(
                        total_categoria,
                        indicadores.total_respostas,
                    ),
                    formatar_n_percentual(
                        ja_realizaram,
                        indicadores.total_ja_realizaram,
                    ),
                    formatar_n_percentual(
                        nunca_realizaram,
                        indicadores.total_nunca_realizaram,
                    ),
                    formatar_n_percentual(
                        conhecem,
                        indicadores.total_conhecem,
                    ),
                ]
            )

    return tabela, linhas_de_secao


def avisar_respostas_nao_classificadas(
    dataframe: pd.DataFrame,
    informar: Callable[[str], None] = print,
) -> None:
    verificacoes = [
        (
            "idade",
            dataframe[PERGUNTA_IDADE].map(classificar_idade).isna(),
        ),
        (
            "situação conjugal",
            dataframe[PERGUNTA_PARCEIRO].map(classificar_parceiro).isna(),
        ),
        (
            "realização do exame",
            dataframe[PERGUNTA_EXAME].map(classificar_exame).isna(),
        ),
    ]
    for nome, mascara in verificacoes:
        quantidade = int(mascara.sum())
        if quantidade:
            informar(
                f"  Aviso: {quantidade} resposta(s) sem classificação "
                f"para {nome}."
            )
