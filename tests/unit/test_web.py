from __future__ import annotations

import unittest
from unittest.mock import patch

from app.application.atualizar_tabela import ResultadoAtualizacao
from app.web import criar_app, extrair_spreadsheet_id


class InterfaceWebTest(unittest.TestCase):
    def setUp(self):
        self.app = criar_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_extrai_id_de_url_ou_valor_direto(self):
        spreadsheet_id = "abc123_XYZ"
        url = (
            "https://docs.google.com/spreadsheets/d/"
            f"{spreadsheet_id}/edit?gid=42"
        )

        self.assertEqual(extrair_spreadsheet_id(url), spreadsheet_id)
        self.assertEqual(
            extrair_spreadsheet_id(f"  {spreadsheet_id}  "),
            spreadsheet_id,
        )

    def test_renderiza_dashboard(self):
        resposta = self.client.get("/")

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Demografia Sheets", resposta.data)
        self.assertIn(b"Atualizar tabela demogr", resposta.data)

    @patch("app.web.atualizar_tabela")
    def test_api_retorna_resultado_estruturado(self, atualizar):
        atualizar.return_value = ResultadoAtualizacao(
            spreadsheet_id="planilha-123",
            nome_aba_origem="Respostas",
            nome_aba_destino="Planilha1",
            total_respostas=52,
            total_linhas_tabela=18,
            total_ja_realizaram=29,
            total_nunca_realizaram=23,
            total_conhecem=44,
        )

        resposta = self.client.post(
            "/api/atualizar",
            json={
                "planilha": (
                    "https://docs.google.com/spreadsheets/d/"
                    "planilha-123/edit"
                ),
                "gid_origem": 123,
                "aba_destino": "Planilha1",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        dados = resposta.get_json()
        self.assertTrue(dados["sucesso"])
        self.assertEqual(dados["resultado"]["total_respostas"], 52)
        self.assertEqual(
            dados["resultado"]["link_planilha"],
            "https://docs.google.com/spreadsheets/d/planilha-123/edit",
        )

    def test_api_valida_campos_obrigatorios(self):
        resposta = self.client.post(
            "/api/atualizar",
            json={
                "planilha": "",
                "gid_origem": "invalido",
                "aba_destino": "",
            },
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(resposta.get_json()["sucesso"])


if __name__ == "__main__":
    unittest.main()
