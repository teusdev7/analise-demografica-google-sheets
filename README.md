# Tabela demográfica no Google Sheets

Aplicação Python que lê respostas de uma aba do Google Sheets, calcula os
cruzamentos demográficos e atualiza uma tabela formatada na aba `Planilha1`.

## Arquitetura

```text
buscadedados/
|-- app/
|   |-- application/
|   |   `-- atualizar_tabela.py
|   |-- domain/
|   |   `-- tabela_demografica.py
|   |-- infrastructure/
|   |   `-- google_sheets.py
|   |-- __main__.py
|   |-- cli.py
|   `-- config.py
|-- credentials/
|   `-- credenciais.json
|-- .github/workflows/
|   `-- tests.yml
|-- tests/
|   `-- unit/
|       |-- test_google_sheets.py
|       `-- test_tabela_demografica.py
|-- planilha_para_tabela.py
|-- config.example.json
|-- config.local.json
|-- requirements.txt
`-- README.md
```

Responsabilidades:

- `domain`: classificação das respostas, contagens e percentuais;
- `infrastructure`: autenticação, leitura, escrita e formatação no Sheets;
- `application`: sequência completa do processamento;
- `cli`: argumentos e tratamento de erros do terminal;
- `planilha_para_tabela.py`: entrada compatível mantida na raiz.

## Instalação

```powershell
python -m pip install -r requirements.txt
```

## Execução

O comando permanece o mesmo:

```powershell
python .\planilha_para_tabela.py
```

Também é possível executar como pacote:

```powershell
python -m app
```

Antes da primeira execução, copie o exemplo de configuração:

```powershell
Copy-Item .\config.example.json .\config.local.json
```

Preencha `config.local.json` com:

- ID da planilha;
- `gid` da aba de respostas;
- nome da aba de resultado;
- caminho da credencial.

`config.local.json` e `credentials/credenciais.json` são ignorados pelo Git.

Outra origem ou destino pode ser informado sem editar o código:

```powershell
python .\planilha_para_tabela.py `
  --spreadsheet-id "ID_DA_PLANILHA" `
  --gid-origem 123456 `
  --aba-destino "Planilha1"
```

## Percentuais

Os percentuais são calculados por coluna:

- `Total`: todas as respostas válidas;
- `Já realizaram`: participantes que já realizaram o exame;
- `Nunca realizaram`: participantes que nunca realizaram;
- `Conhecimento`: respostas `Sim`.

Cada coluna soma aproximadamente 100% dentro de cada bloco demográfico.
Diferenças de 0,1 ponto percentual podem ocorrer por arredondamento.

## Credenciais

O arquivo `credentials/credenciais.json` é local e ignorado pelo Git. A
planilha precisa estar compartilhada com o e-mail da conta de serviço.

Nunca publique nem envie o conteúdo desse arquivo.

## Testes

```powershell
python -m unittest discover -s tests -v
```

O workflow `.github/workflows/tests.yml` executa os mesmos testes
automaticamente no GitHub Actions.
