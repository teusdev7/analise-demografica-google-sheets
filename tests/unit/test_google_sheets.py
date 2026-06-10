from __future__ import annotations

import unittest

from app.infrastructure.google_sheets import (
    criar_requisicoes_formatacao,
    ler_dataframe_da_aba,
    localizar_aba_por_gid,
)


class RequisicaoFalsa:
    def __init__(self, resultado):
        self.resultado = resultado

    def execute(self):
        return self.resultado


class ValoresFalsos:
    def __init__(self, valores):
        self.valores = valores

    def get(self, **_):
        return RequisicaoFalsa({"values": self.valores})


class PlanilhasFalsas:
    def __init__(self, valores):
        self.valores_recurso = ValoresFalsos(valores)

    def get(self, **_):
        return RequisicaoFalsa(
            {
                "sheets": [
                    {
                        "properties": {
                            "sheetId": 123456,
                            "title": "Respostas ao formulário 1",
                        }
                    }
                ]
            }
        )

    def values(self):
        return self.valores_recurso


class ServicoFalso:
    def __init__(self, valores):
        self.planilhas = PlanilhasFalsas(valores)

    def spreadsheets(self):
        return self.planilhas


class GoogleSheetsTest(unittest.TestCase):
    def test_formatacao_inclui_autoajuste(self):
        requisicoes = criar_requisicoes_formatacao(
            sheet_id=321,
            quantidade_linhas=15,
            linhas_de_secao=[1, 4],
            quantidade_colunas=7,
        )
        autoajustes = [
            requisicao["autoResizeDimensions"]
            for requisicao in requisicoes
            if "autoResizeDimensions" in requisicao
        ]

        self.assertEqual(len(autoajustes), 1)
        self.assertEqual(autoajustes[0]["dimensions"]["endIndex"], 7)
        self.assertEqual(len(requisicoes), 8)

    def test_localiza_aba_por_gid(self):
        servico = ServicoFalso([])

        titulo = localizar_aba_por_gid(servico, "planilha", 123456)

        self.assertEqual(titulo, "Respostas ao formulário 1")

    def test_le_dataframe_e_completa_celulas_ausentes(self):
        cabecalhos = [
            "Idade",
            "Escolaridade",
            "Cor/Etnia",
            "Você possui parceiro fixo?",
            (
                "Já realizou o exame? Se sim, com que frequência? "
                "Em qual período do ano?"
            ),
            "Você sabe o que é o Papanicolau",
            "Você conhece o HPV e a sua forma de transmissão e relação com o câncer?",
            "Realiza o exame em rede pública ou privada?",
        ]
        servico = ServicoFalso(
            [
                cabecalhos,
                [
                    "20",
                    "Superior",
                    "Branca",
                    "Sim",
                    "Não",
                    "Sim",
                    "Sim",
                    "Pública",
                ],
                ["30", "Médio", "Parda", "Não"],
            ]
        )

        dataframe = ler_dataframe_da_aba(
            servico,
            "planilha",
            "Respostas ao formulário 1",
        )

        self.assertEqual(len(dataframe), 2)
        self.assertEqual(dataframe.iloc[1]["Idade"], "30")
        self.assertEqual(
            dataframe.iloc[1]["Você sabe o que é o Papanicolau"],
            "",
        )


if __name__ == "__main__":
    unittest.main()
