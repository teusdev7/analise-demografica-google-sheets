from __future__ import annotations

import unittest

import pandas as pd

from app.domain.etnia_rede import (
    classificar_etnia,
    montar_tabela_etnia_rede,
)
from app.domain.tabela_demografica import (
    PERGUNTA_ETNIA,
    PERGUNTA_EXAME,
    PERGUNTA_REDE_ATENDIMENTO,
)


class EtniaRedeTest(unittest.TestCase):
    def test_classifica_variacoes_de_etnia(self):
        self.assertEqual(classificar_etnia("Branca"), "Branco")
        self.assertEqual(classificar_etnia("Preta"), "Preto")
        self.assertEqual(classificar_etnia("Parda"), "Pardo")
        self.assertEqual(classificar_etnia("Indígena"), "Indígena")
        self.assertEqual(classificar_etnia("Amarela"), "Amarelo")

    def test_considera_apenas_quem_realizou_em_cada_rede(self):
        dataframe = pd.DataFrame(
            [
                {
                    PERGUNTA_ETNIA: "Branca",
                    PERGUNTA_EXAME: "Anualmente",
                    PERGUNTA_REDE_ATENDIMENTO: "Privada",
                },
                {
                    PERGUNTA_ETNIA: "Preta",
                    PERGUNTA_EXAME: "Sim, no início do ano",
                    PERGUNTA_REDE_ATENDIMENTO: "Pública",
                },
                {
                    PERGUNTA_ETNIA: "Parda",
                    PERGUNTA_EXAME: "Não",
                    PERGUNTA_REDE_ATENDIMENTO: "Privada",
                },
            ]
        )

        (
            tabela,
            total_privada,
            total_publica,
            total_nunca_realizou,
        ) = montar_tabela_etnia_rede(dataframe)

        self.assertEqual(total_privada, 1)
        self.assertEqual(total_publica, 1)
        self.assertEqual(total_nunca_realizou, 1)
        self.assertEqual(
            tabela[1],
            ["Branco", "1 (100,0%)", "0 (0,0%)", "0 (0,0%)"],
        )
        self.assertEqual(
            tabela[2],
            ["Preto", "0 (0,0%)", "1 (100,0%)", "0 (0,0%)"],
        )
        self.assertEqual(
            tabela[3],
            ["Pardo", "0 (0,0%)", "0 (0,0%)", "1 (100,0%)"],
        )
        self.assertEqual(
            tabela[-1],
            ["TOTAL", "1 (100,0%)", "1 (100,0%)", "1 (100,0%)"],
        )


if __name__ == "__main__":
    unittest.main()
