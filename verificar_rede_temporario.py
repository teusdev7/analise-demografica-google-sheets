from app.config import (
    ARQUIVO_CREDENCIAIS,
    GID_ABA_ORIGEM,
    SPREADSHEET_ID,
)
from app.domain.tabela_demografica import (
    PERGUNTA_REDE_ATENDIMENTO,
    classificar_rede_atendimento,
)
from app.infrastructure.google_sheets import (
    autenticar_sheets,
    ler_dataframe_da_aba,
    localizar_aba_por_gid,
)


_, servico = autenticar_sheets(ARQUIVO_CREDENCIAIS)
aba_origem = localizar_aba_por_gid(
    servico,
    SPREADSHEET_ID,
    GID_ABA_ORIGEM,
)
dataframe = ler_dataframe_da_aba(
    servico,
    SPREADSHEET_ID,
    aba_origem,
)
contagens = (
    dataframe[PERGUNTA_REDE_ATENDIMENTO]
    .map(classificar_rede_atendimento)
    .value_counts(dropna=False)
    .to_dict()
)
print(f"REDE_ORIGEM={contagens}")

valores = (
    servico.spreadsheets()
    .values()
    .get(
        spreadsheetId=SPREADSHEET_ID,
        range="Planilha1!A1:G4",
    )
    .execute()
    .get("values", [])
)
for linha in valores:
    print(linha)
