import sqlite3
import pandas as pd
import numpy as np

from pdw.database.operations import table_droppator, save_dataframe_to_database
from pdw.etl.sanitizer import sanitize_entries_dataframe, data_correjeitor

# ============================================================================
# FUNÇÕES DE LEITURA E PROCESSAMENTO DE EXCEL
# ============================================================================

def read_guiding_sheet(excel_file, sheet_name):
    """
    Lê a planilha de configuração/guia que define quais sheets processar.

    Args:
        excel_file (str): Caminho do arquivo Excel
        sheet_name (str): Nome da planilha guia

    Returns:
        pd.DataFrame: DataFrame com configurações das planilhas
    """

    print(f"Reading Data from Guindig Sheet :->  \033[32m{sheet_name}\033[0m ... .. .  ")
    workbook = pd.ExcelFile(excel_file)
    return workbook.parse(sheet_name=sheet_name)


def process_accounting_sheet(excel_file, sheet_name, origin_col_name):
    """
    Processa uma planilha contábil individual.

    Args:
        excel_file (str): Caminho do arquivo Excel
        sheet_name (str): Nome da planilha a processar
        origin_col_name (str): Nome da coluna que identifica origem dos dados

    Returns:
        tuple: (DataFrame processado, número de linhas)
    """
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    df['TIPO'] = df['TIPO'].replace('', np.nan)
    df['Data'] = df['Data'].replace('', np.nan)
    entries_df = df[["Data", "TIPO", "DESCRICAO", "Credito", "Debito"]].copy()
    entries_df[origin_col_name] = sheet_name
    return entries_df, len(df)

def process_non_accounting_sheet(excel_file, sheet_name, conn):
    """
    Processa e salva uma planilha não-contábil diretamente no banco.

    Args:
        excel_file (str): Caminho do arquivo Excel
        sheet_name (str): Nome da planilha
        conn: Conexão SQLite

    Returns:
        int: Número de linhas processadas
    """
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    return df.to_sql(sheet_name, conn, index=False, if_exists="replace")

# ============================================================================
# 2025-11-26 - FUNÇÃO PRINCIPAL REFATORADA
# ============================================================================
def new_data_loader(data_base, types_sheet, general_entries_table, data_origin_col,
                    guiding_sheet, excel_file, save_useless, udt):
    """
    Carrega dados de planilhas Excel para banco de dados SQLite.

    Esta função orquestra todo o processo de ETL:
    1. Conecta ao banco de dados
    2. Lê configurações da planilha guia
    3. Processa cada planilha conforme configuração
    4. Consolida dados contábeis
    5. Sanitiza e enriquece os dados
    6. Persiste no banco de dados
    7. Executa correções adicionais

    Args:
        data_base (str): Caminho do banco SQLite
        types_sheet (str): Nome da planilha de tipos
        general_entries_table (str): Nome da tabela de lançamentos gerais
        data_origin_col (str): Nome da coluna de origem dos dados
        guiding_sheet (str): Nome da planilha guia com configurações
        excel_file (str): Caminho do arquivo Excel
        save_useless (bool): Se deve manter registros com dados nulos
        udt: Parâmetro adicional para data_correjeitor
    """
    print(f"Connecting to SQLite3 Database ... .. .  ")
    conn = sqlite3.connect(data_base)
    cursor = conn.cursor()

    sheets_dataframe = read_guiding_sheet(excel_file, guiding_sheet)
    table_droppator(cursor, general_entries_table)
    print("Running Loader of the Sheets into database Tables ... .. .  ")

    all_entries = []

    for i, infos in sheets_dataframe.iterrows():
        table_to_load = infos.TABLE_NAME
        is_accounting = infos.ACCOUNTING
        is_loadable = infos.LOADABLE

        print(f'\033[34m   . .. ... Step: {i + 1:04} ; '
              f'Table (Sheet) :-> {table_to_load.strip().ljust(25)} ;\033[0m', end=' ')

        if 'X' == is_loadable:
            if 'X' == is_accounting:
                # Processa planilha contábil
                entries_df, number_lines = process_accounting_sheet(
                    excel_file, table_to_load, data_origin_col
                )
                all_entries.append(entries_df)
            else:
                # Processa planilha não-contábil
                number_lines = process_non_accounting_sheet(
                    excel_file, table_to_load, conn
                )

            print(f'\033[32mLines Created :-> {str(number_lines).rjust(6)} \033[0m')

    if all_entries:
        general_entries_df_full = pd.concat(all_entries, ignore_index=True)
    else:
        # Cria DataFrame vazio com estrutura esperada se não houver dados
        general_entries_df_full = pd.DataFrame(
            columns=["Data", "TIPO", "DESCRICAO", "Credito", "Debito", data_origin_col]
        )

    general_entries_df_full = sanitize_entries_dataframe(
        general_entries_df_full,
        remove_nulls=not save_useless
    )
    save_dataframe_to_database(
        general_entries_df_full,
        conn,
        general_entries_table,
        sort_by_date=True
    )
    conn.commit()
    data_correjeitor(cursor, types_sheet, general_entries_table, save_useless, udt)
    conn.commit()
    conn.close()
