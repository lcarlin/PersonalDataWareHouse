import numpy as np
import pandas as pd

from pdw.utils.localization import get_month_names, get_weekday_names
from pdw.database.operations import table_droppator

## ------------------------------------------------------------------------------------------
# new stuff
"""
Módulo refatorado do data_loader
Separado em funções modulares com responsabilidades únicas

"""
# ============================================================================
# FUNÇÕES DE SANITIZAÇÃO E TRANSFORMAÇÃO
# ============================================================================

def clean_description_text(text_series):
    """
    Limpa e padroniza o texto das descrições.

    Args:
        text_series (pd.Series): Série com textos para limpar

    Returns:
        pd.Series: Série com textos limpos
    """
    return (
        text_series
        .str.replace(r"[;,]", "|", regex=True)  # Substitui vírgula e ponto-vírgula
        .str.replace("∴", " .'. ")  # Substitui caractere especial
        .str.replace("ś", "s")  # Remove acentuação
        .str.replace('"','' ) # remover o " 2026-01-22
        .str.strip()  # Remove espaços extras
    )

def add_temporal_columns(df):
    """
    Adiciona colunas relacionadas a datas (mês, ano, dia da semana, etc).

    Args:
        df (pd.DataFrame): DataFrame com coluna 'Data'

    Returns:
        pd.DataFrame: DataFrame com colunas adicionadas
    """
    df.insert(1, 'DIA_SEMANA', np.nan)
    df.insert(6, 'Mes', 'MM')
    df.insert(7, 'Ano', 'yyyy')
    df.insert(8, 'MES_EXTENSO', np.nan)
    df.insert(9, 'AnoMes', 'YYYY/MM')
    return df

def enrich_dataframe_with_dates(df):
    """
    Enriquece o DataFrame com informações temporais derivadas da coluna Data.

    Args:
        df (pd.DataFrame): DataFrame com coluna 'Data' do tipo datetime

    Returns:
        pd.DataFrame: DataFrame enriquecido
    """
    dt = df['Data'].dt
    meses = get_month_names()
    dias_semana = get_weekday_names()

    return df.assign(
        MES_EXTENSO=dt.month.map(meses),
        DIA_SEMANA=dt.dayofweek.map(dias_semana),
        Mes=dt.strftime("%m"),
        Ano=dt.strftime("%Y"),
        AnoMes=dt.strftime("%Y/%m")
    )

def sanitize_financial_columns(df):
    """
    Converte e limpa as colunas financeiras (Credito e Debito).

    Args:
        df (pd.DataFrame): DataFrame com colunas 'Credito' e 'Debito'

    Returns:
        pd.DataFrame: DataFrame com colunas sanitizadas
    """
    return df.assign(
        Credito=pd.to_numeric(df['Credito'], errors='coerce').round(2).fillna(0),
        Debito=pd.to_numeric(df['Debito'], errors='coerce').round(2).fillna(0)
    )


def sanitize_entries_dataframe(df, remove_nulls=True):
    """
    Sanitiza e enriquece o DataFrame consolidado de lançamentos.

    Args:
        df (pd.DataFrame): DataFrame bruto de lançamentos
        remove_nulls (bool): Se deve remover registros com TIPO ou Data nulos

    Returns:
        pd.DataFrame: DataFrame sanitizado e enriquecido
    """
    print(f'\033[34m   . .. ... Sanitizing DataFrame       :-> \033[0m', end=' ')
    if remove_nulls:
        df = df.dropna(subset=['TIPO'])
        df = df.dropna(subset=['Data'])

    df = add_temporal_columns(df)
    df = sanitize_financial_columns(df)
    df = enrich_dataframe_with_dates(df)
    df['DESCRICAO'] = clean_description_text(df['DESCRICAO'])
    print(f'\033[32mDone !!! \033[0m')
    return df


def data_correjeitor(conexao, types_sheet, entries_table, save_useless, useless_table):
    print(f'Normalizing data on {entries_table} Table ...')
    cursor = conexao
    lista_acoes = []
    if save_useless:
        print(f'   . .. ... Saving discated Data')
        table_droppator(cursor, useless_table)
        lista_acoes.append((
            f"create table {useless_table} as select * from {entries_table} where (data is null or tipo is null); ",
            "Saving Useless"))
        lista_acoes.append((f"delete from {entries_table} where (data is null or tipo is null);", "Deleting Useless"))

    lista_acoes.append(
        (f"Delete from {types_sheet} WHERE ( Código IS NULL or Descrição IS NULL) ;", "Deleting NULL info"))
    lista_acoes.append(('DELETE FROM Parcelamentos WHERE 1 = 1 AND (DATA IS NULL OR "Tipo Lançamento" is null) ;',
                        "Deleting Parcelamentos"))
    # lista_acoes.append((f'create index SHAWASKA on {entries_table}  (DATA, TIPO, DESCRICAO) ',"(Re)creating Index"))
    lista_acoes.append((f'DROP VIEW IF EXISTS Origens; ', "Dropping View"))
    lista_acoes.append((
                       f"create view Origens as select TABLE_NAME as nome from GUIDING gd where gd.LOADABLE = 'X' AND GD.ACCOUNTING = 'X';",
                       "Creating View"))

    for i in range(0, len(lista_acoes)):
        sql_string = lista_acoes[i][0]
        action_desc = lista_acoes[i][1].ljust(25)
        print(f'\033[34m   . .. ... Step: {i + 1:04} :-> {action_desc} ;\033[0m', end=' ')
        cursor.execute(sql_string)
        print(f'\033[31mLines Affected: {str(cursor.rowcount).rjust(5)}\033[0m')

## end of new stuff
## ------------------------------------------------------------------------------------------
