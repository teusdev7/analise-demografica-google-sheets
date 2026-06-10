from __future__ import annotations

import unittest

import pandas as pd

from app.domain.tabela_demografica import (
    PERGUNTA_CONHECIMENTO,
    PERGUNTA_CONHECIMENTO_HPV,
    PERGUNTA_ESCOLARIDADE,
    PERGUNTA_ETNIA,
    PERGUNTA_EXAME,
    PERGUNTA_IDADE,
    PERGUNTA_PARCEIRO,
    PERGUNTA_REDE_ATENDIMENTO,
    classificar_idade,
    classificar_rede_atendimento,
    montar_tabela_demografica,
)


def criar_registro(**substituicoes: str) -> dict[str, str]:
    registro = {
        PERGUNTA_IDADE: "20",
        PERGUNTA_ESCOLARIDADE: "Superior",
        PERGUNTA_ETNIA: "Branca",
        PERGUNTA_PARCEIRO: "Sim",
        PERGUNTA_EXAME: "Não",
        PERGUNTA_CONHECIMENTO: "Sim",
        PERGUNTA_CONHECIMENTO_HPV: "Sim",
        PERGUNTA_REDE_ATENDIMENTO: "Pública",
    }
    registro.update(substituicoes)
    return registro


class TabelaDemograficaTest(unittest.TestCase):
    def test_classifica_faixas_de_idade(self):
        self.assertEqual(classificar_idade("18-23"), "Até 23 anos")
        self.assertEqual(classificar_idade("23-28"), "23 anos ou mais")
        self.assertEqual(classificar_idade("23"), "Até 23 anos")

    def test_classifica_rede_de_atendimento(self):
        self.assertEqual(classificar_rede_atendimento("Pública"), "Pública")
        self.assertEqual(
            classificar_rede_atendimento("Rede privada"),
            "Privada",
        )
        self.assertIsNone(classificar_rede_atendimento("Nunca realizei"))

    def test_calcula_percentuais_por_coluna(self):
        dataframe = pd.DataFrame(
            [
                criar_registro(),
                criar_registro(
                    **{
                        PERGUNTA_IDADE: "23 anos ou mais",
                        PERGUNTA_ESCOLARIDADE: "Médio",
                        PERGUNTA_ETNIA: "Parda",
                        PERGUNTA_PARCEIRO: "Não",
                        PERGUNTA_EXAME: "Todo ano",
                        PERGUNTA_CONHECIMENTO: "Não",
                        PERGUNTA_CONHECIMENTO_HPV: "Não",
                        PERGUNTA_REDE_ATENDIMENTO: "Privada",
                    }
                ),
                criar_registro(
                    **{
                        PERGUNTA_IDADE: "Até 23 anos",
                        PERGUNTA_EXAME: "No início do ano",
                        PERGUNTA_REDE_ATENDIMENTO: "Privada",
                    }
                ),
                criar_registro(
                    **{
                        PERGUNTA_IDADE: "35",
                        PERGUNTA_ESCOLARIDADE: "Fundamental",
                        PERGUNTA_ETNIA: "Preta",
                        PERGUNTA_PARCEIRO: "Não",
                        PERGUNTA_CONHECIMENTO_HPV: "Não",
                        PERGUNTA_REDE_ATENDIMENTO: "Nunca realizei",
                    }
                ),
            ]
        )

        tabela, linhas_de_secao = montar_tabela_demografica(dataframe)

        self.assertEqual(tabela[0][1], "Total = 4 (%)")
        self.assertIn("Total = 2 (%)", tabela[0][2])
        self.assertIn("Total = 2 (%)", tabela[0][3])
        self.assertIn("Total = 3 (%)", tabela[0][4])
        self.assertIn("Total = 2 (%)", tabela[0][5])
        self.assertIn("Pública = 1 | Privada = 2", tabela[0][6])
        self.assertEqual(linhas_de_secao, [1, 4, 8, 12])
        self.assertEqual(
            tabela[2],
            [
                "Até 23 anos",
                "2 (50,0%)",
                "1 (50,0%)",
                "1 (50,0%)",
                "2 (66,7%)",
                "2 (100,0%)",
                "Pública: 1 (100,0%)\nPrivada: 1 (50,0%)",
            ],
        )
        self.assertEqual(
            tabela[3],
            [
                "23 anos ou mais",
                "2 (50,0%)",
                "1 (50,0%)",
                "1 (50,0%)",
                "1 (33,3%)",
                "0 (0,0%)",
                "Pública: 0 (0,0%)\nPrivada: 1 (50,0%)",
            ],
        )

    def test_mantem_valores_unicos_exatamente_como_informados(self):
        dataframe = pd.DataFrame(
            [
                criar_registro(),
                criar_registro(
                    **{
                        PERGUNTA_IDADE: "21",
                        PERGUNTA_ESCOLARIDADE: "superior",
                        PERGUNTA_ETNIA: "branca",
                        PERGUNTA_EXAME: "Anualmente",
                    }
                ),
            ]
        )

        tabela, _ = montar_tabela_demografica(dataframe)
        rotulos = [linha[0] for linha in tabela]

        self.assertIn("Superior", rotulos)
        self.assertIn("superior", rotulos)
        self.assertIn("Branca", rotulos)
        self.assertIn("branca", rotulos)


if __name__ == "__main__":
    unittest.main()
