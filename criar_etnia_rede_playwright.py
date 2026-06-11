#!/usr/bin/env python
"""Cria e confere visualmente a tabela de etnia por rede."""

from __future__ import annotations

import json
import time

from playwright.sync_api import sync_playwright

from app.application.criar_tabela_etnia_rede import criar_tabela_etnia_rede
from app.config import (
    ARQUIVO_CREDENCIAIS,
    GID_ABA_ORIGEM,
    SPREADSHEET_ID,
)


NOME_ABA = "Etnia por rede"


HTML = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Criação da tabela por etnia e rede</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh; padding: 36px; color: #17354c;
      background: linear-gradient(135deg, #edf5fa, #f8fbfd);
      font: 15px/1.45 Arial, sans-serif;
    }
    main { max-width: 1180px; margin: auto; }
    h1 { margin: 0 0 8px; font-size: 32px; }
    .sub { margin-bottom: 26px; color: #60798b; font-size: 17px; }
    .grid { display: grid; grid-template-columns: 390px 1fr; gap: 22px; }
    .card {
      padding: 24px; border: 1px solid #cfdae2; border-radius: 18px;
      background: white; box-shadow: 0 12px 36px rgba(34, 71, 98, .09);
    }
    h2 { margin: 0 0 18px; font-size: 19px; }
    ol { margin: 0; padding: 0; list-style: none; }
    li {
      display: flex; gap: 12px; align-items: center; margin-bottom: 11px;
      padding: 13px; border: 1px solid #dbe4ea; border-radius: 12px;
      color: #6b7f8e; background: #f8fafc;
    }
    .number {
      display: grid; width: 30px; height: 30px; flex: 0 0 auto;
      place-items: center; border-radius: 50%; background: #dce8f0;
      font-weight: 700;
    }
    li.active {
      color: #1e5f8b; border-color: #72add4; background: #edf7fd;
      box-shadow: 0 0 0 3px rgba(75, 151, 201, .13);
    }
    li.done { color: #087443; border-color: #9cd7ba; background: #e9f8f0; }
    li.done .number { color: white; background: #15935b; }
    .message {
      margin-top: 18px; min-height: 58px; padding: 14px; border-radius: 12px;
      color: #225a80; background: #eaf4fa; font-weight: 700;
    }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 14px; border: 1px solid #bccbd5; text-align: center; }
    th { color: white; background: #20577f; }
    td:first-child { text-align: left; font-weight: 700; }
    tr:last-child td { color: #20577f; background: #dcebf4; font-weight: 700; }
    .placeholder { padding: 80px 20px; text-align: center; color: #78909f; }
    .success {
      display: none; margin-top: 18px; padding: 16px; border-radius: 13px;
      color: #087443; background: #dff6e9; font-size: 17px; font-weight: 700;
    }
    .success.visible { display: block; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>Criando a tabela “Etnia por rede”</h1>
  <div class="sub">Acompanhe ao vivo a leitura, o cálculo e a escrita no Google Sheets.</div>
  <div class="grid">
    <section class="card">
      <h2>Progresso da operação</h2>
      <ol id="steps">
        <li><span class="number">1</span>Autenticar e ler respostas</li>
        <li><span class="number">2</span>Classificar etnias e redes</li>
        <li><span class="number">3</span>Calcular quantidades e percentuais</li>
        <li><span class="number">4</span>Criar e preencher a nova aba</li>
        <li><span class="number">5</span>Formatar a tabela</li>
        <li><span class="number">6</span>Conferir célula por célula</li>
      </ol>
      <div class="message" id="message">Preparando o navegador...</div>
      <div class="success" id="success">Tabela criada e conferida sem divergências.</div>
    </section>
    <section class="card">
      <h2>Prévia dos dados calculados</h2>
      <div id="preview" class="placeholder">A tabela aparecerá aqui após o cálculo.</div>
    </section>
  </div>
</main>
<script>
  const steps = [...document.querySelectorAll("#steps li")];
  function progress(index, message) {
    steps.forEach((step, position) => {
      step.classList.toggle("done", position < index);
      step.classList.toggle("active", position === index);
    });
    document.querySelector("#message").textContent = message;
  }
  function showTable(rows) {
    const body = rows.map((row, index) => {
      const tag = index === 0 ? "th" : "td";
      return `<tr>${row.map(value =>
        `<${tag}>${String(value).replaceAll("\\n", "<br>")}</${tag}>`
      ).join("")}</tr>`;
    }).join("");
    document.querySelector("#preview").innerHTML = `<table>${body}</table>`;
    document.querySelector("#preview").className = "";
  }
  function finish(message) {
    steps.forEach(step => { step.classList.remove("active"); step.classList.add("done"); });
    document.querySelector("#message").textContent = message;
    document.querySelector("#success").classList.add("visible");
  }
</script>
</body>
</html>"""


def main() -> int:
    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(
            headless=False,
            slow_mo=120,
            args=["--start-maximized"],
        )
        contexto = navegador.new_context(no_viewport=True, locale="pt-BR")
        painel = contexto.new_page()
        painel.set_content(HTML)
        painel.bring_to_front()

        etapa = 0

        def informar(mensagem: str) -> None:
            nonlocal etapa
            if "Autenticando" in mensagem or "lendo" in mensagem:
                etapa = 0
            elif "respostas carregadas" in mensagem or "Classificando" in mensagem:
                etapa = 1
            elif "Cálculo concluído" in mensagem:
                etapa = 2
            elif "Criando" in mensagem or "Limpando" in mensagem or "Escrevendo" in mensagem:
                etapa = 3
            elif "Aplicando" in mensagem:
                etapa = 4
            elif "Conferindo" in mensagem or "Conferência" in mensagem:
                etapa = 5
            painel.evaluate(
                "([index, text]) => progress(index, text)",
                [etapa, mensagem],
            )
            painel.wait_for_timeout(900)

        try:
            resultado = criar_tabela_etnia_rede(
                spreadsheet_id=SPREADSHEET_ID,
                gid_origem=GID_ABA_ORIGEM,
                nome_aba=NOME_ABA,
                credenciais=ARQUIVO_CREDENCIAIS,
                informar=informar,
            )
            painel.evaluate(
                "(rows) => showTable(rows)",
                resultado.tabela,
            )
            painel.wait_for_timeout(2500)
            painel.evaluate(
                "(message) => finish(message)",
                (
                    f"Finalizado: {resultado.total_privada} na rede privada "
                    f"{resultado.total_publica} na rede pública e "
                    f"{resultado.total_nunca_realizou} nunca realizaram."
                ),
            )
            painel.wait_for_timeout(3000)

            planilha = contexto.new_page()
            planilha.goto(
                resultado.link,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            planilha.bring_to_front()
            print(f"LINK={resultado.link}")
            print(
                json.dumps(
                    resultado.tabela,
                    ensure_ascii=False,
                )
            )
            time.sleep(90)
            navegador.close()
            return 0
        except Exception as erro:
            painel.evaluate(
                "(message) => document.querySelector('#message').textContent = message",
                f"Erro: {erro}",
            )
            time.sleep(60)
            navegador.close()
            raise


if __name__ == "__main__":
    raise SystemExit(main())
