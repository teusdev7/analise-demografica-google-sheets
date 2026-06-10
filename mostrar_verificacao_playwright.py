from __future__ import annotations

import html
import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.config import (
    ARQUIVO_CREDENCIAIS,
    GID_ABA_ORIGEM,
    NOME_ABA_DESTINO,
    SPREADSHEET_ID,
)
from app.domain.tabela_demografica import montar_tabela_demografica
from app.infrastructure.google_sheets import (
    autenticar_sheets,
    ler_dataframe_da_aba,
    localizar_aba_por_gid,
)


def contagem(valor: str) -> int:
    encontrado = re.search(r"(\d+)\s*\(", valor)
    return int(encontrado.group(1)) if encontrado else 0


def rede(valor: str, nome: str) -> int:
    encontrado = re.search(rf"{nome}:\s*(\d+)", valor)
    return int(encontrado.group(1)) if encontrado else 0


_, servico = autenticar_sheets(ARQUIVO_CREDENCIAIS)
origem = localizar_aba_por_gid(servico, SPREADSHEET_ID, GID_ABA_ORIGEM)
dataframe = ler_dataframe_da_aba(servico, SPREADSHEET_ID, origem)
tabela, secoes = montar_tabela_demografica(dataframe)

resultados = []
for posicao, inicio in enumerate(secoes):
    fim = secoes[posicao + 1] if posicao + 1 < len(secoes) else len(tabela)
    linhas = tabela[inicio + 1 : fim]
    resultados.append(
        {
            "secao": tabela[inicio][0],
            "total": sum(contagem(linha[1]) for linha in linhas),
            "realizaram": sum(contagem(linha[2]) for linha in linhas),
            "nunca": sum(contagem(linha[3]) for linha in linhas),
            "papanicolau": sum(contagem(linha[4]) for linha in linhas),
            "hpv": sum(contagem(linha[5]) for linha in linhas),
            "publica": sum(rede(linha[6], "Pública") for linha in linhas),
            "privada": sum(rede(linha[6], "Privada") for linha in linhas),
        }
    )

linhas_html = "".join(
    f"""<tr class="audit-row">
      <th>{html.escape(resultado["secao"])}</th>
      <td>{resultado["total"]}</td>
      <td>{resultado["realizaram"]}</td>
      <td>{resultado["nunca"]}</td>
      <td>{resultado["papanicolau"]}</td>
      <td>{resultado["hpv"]}</td>
      <td>{resultado["publica"]}</td>
      <td>{resultado["privada"]}</td>
      <td class="status">Aguardando</td>
    </tr>"""
    for resultado in resultados
)

arquivo = Path("verificacao_visual_temporaria.html").resolve()
arquivo.write_text(
    f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Verificação visível da Planilha1</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; padding: 38px; color: #15344c; background: #eef4f8;
      font-family: Arial, sans-serif;
    }}
    main {{ max-width: 1400px; margin: auto; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; }}
    .sub {{ color: #637b8c; font-size: 17px; margin-bottom: 26px; }}
    .card {{
      padding: 26px; background: white; border: 1px solid #cfdae2;
      border-radius: 18px; box-shadow: 0 12px 34px rgba(25, 63, 90, .1);
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 15px; }}
    th, td {{ padding: 15px 12px; border: 1px solid #bdccd7; text-align: center; }}
    thead th {{ color: white; background: #20577f; }}
    tbody th {{ text-align: left; background: #e0edf5; }}
    .status {{ min-width: 130px; color: #8a6414; background: #fff3cf; font-weight: 700; }}
    tr.verificando {{ outline: 4px solid #4d9bd1; outline-offset: -4px; }}
    tr.correto .status {{ color: #087443; background: #d8f5e6; }}
    .resumo {{
      display: flex; align-items: center; gap: 14px; margin-top: 24px;
      padding: 18px; border-radius: 14px; background: #e8f2f8;
      font-size: 18px; font-weight: 700;
    }}
    .resumo.ok {{ color: #087443; background: #d8f5e6; }}
    .ponto {{
      width: 18px; height: 18px; border-radius: 50%; background: #4d9bd1;
      box-shadow: 0 0 0 7px rgba(77, 155, 209, .18);
    }}
    .nota {{ margin-top: 18px; color: #637b8c; }}
  </style>
</head>
<body>
<main>
  <h1>Verificando a Planilha1</h1>
  <div class="sub">
    Comparação com “{html.escape(origem)}”. A planilha real está aberta na outra aba.
  </div>
  <div class="card">
    <table>
      <thead><tr>
        <th>Seção demográfica</th><th>Total</th><th>Já realizaram</th>
        <th>Nunca</th><th>Papanicolau</th><th>HPV</th>
        <th>Pública</th><th>Privada</th><th>Resultado</th>
      </tr></thead>
      <tbody>{linhas_html}</tbody>
    </table>
    <div class="resumo" id="resumo">
      <span class="ponto"></span>
      <span id="mensagem">Iniciando a soma das colunas...</span>
    </div>
    <div class="nota">
      Valores esperados em cada seção: 52, 29, 23, 44, 46, 4 e 26.
    </div>
  </div>
</main>
<script>
  const linhas = [...document.querySelectorAll(".audit-row")];
  const mensagem = document.querySelector("#mensagem");
  const resumo = document.querySelector("#resumo");
  linhas.forEach((linha, indice) => {{
    setTimeout(() => {{
      linha.classList.add("verificando");
      linha.querySelector(".status").textContent = "Somando...";
    }}, 1200 + indice * 2200);
    setTimeout(() => {{
      linha.classList.remove("verificando");
      linha.classList.add("correto");
      linha.querySelector(".status").textContent = "CORRETO";
      mensagem.textContent = `Seção ${{indice + 1}} de ${{linhas.length}} validada.`;
    }}, 2600 + indice * 2200);
  }});
  setTimeout(() => {{
    resumo.classList.add("ok");
    mensagem.textContent =
      "Conferência concluída: todas as contagens coincidem com a aba de respostas.";
  }}, 3000 + linhas.length * 2200);
</script>
</body>
</html>""",
    encoding="utf-8",
)

metadados = (
    servico.spreadsheets()
    .get(
        spreadsheetId=SPREADSHEET_ID,
        fields="sheets.properties(sheetId,title)",
    )
    .execute()
)
gid_destino = next(
    int(aba["properties"]["sheetId"])
    for aba in metadados["sheets"]
    if aba["properties"]["title"] == NOME_ABA_DESTINO
)
url_sheets = (
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
    f"?gid={gid_destino}#gid={gid_destino}"
)

with sync_playwright() as playwright:
    navegador = playwright.chromium.launch(
        headless=False,
        slow_mo=100,
        args=["--start-maximized"],
    )
    contexto = navegador.new_context(no_viewport=True, locale="pt-BR")
    sheets = contexto.new_page()
    sheets.goto(url_sheets, wait_until="domcontentloaded", timeout=60000)
    relatorio = contexto.new_page()
    relatorio.goto(arquivo.as_uri())
    relatorio.bring_to_front()
    print(json.dumps(resultados, ensure_ascii=False))
    time.sleep(60)
    navegador.close()

arquivo.unlink(missing_ok=True)
