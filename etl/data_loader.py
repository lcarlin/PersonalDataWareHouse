import sqlite3
import pandas as pd
import numpy as np
from database.drop_table import table_droppator
from utils.correjeitor import data_correjeitor

def data_loader(data_base, types_sheet, general_entries_table, data_origin_col, guindind_sheet, excel_file,
                save_useless, udt):
    print(f"Connecting to SQLite3 Database ... .. .  ")
    conn = sqlite3.connect(data_base)
    work_books = pd.ExcelFile(excel_file)
    print(f"Reading Data from Guindig Sheet :->  {guindind_sheet} ... .. .  ")
    sheets_dataframe = work_books.parse(sheet_name=guindind_sheet)
    table_droppator(conn.cursor(), general_entries_table)
    print("Running Loader of the Sheets into database Tables ... .. .  ")
    first_pass = True
    meses = {1: "01-Janeiro",
             2: "02-Fevereiro",
             3: "03-Março",
             4: "04-Abril",
             5: "05-Maio",
             6: "06-Junho",
             7: "07-Julho",
             8: "08-Agosto",
             9: "09-Setembro",
             10: "10-Outubro",
             11: "11-Novembro",
             12: "12-Dezembro" }

    dias_semana = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo"
    }

    for i, infos in sheets_dataframe.iterrows():
        table_to_load = infos.TABLE_NAME
        is_accounting = infos.ACCOUNTING
        is_cleanable = infos.CLEANABLE
        is_loadeable = infos.LOADABLE
        print(f'\033[34m   . .. ... Step: {i + 1:04} ; Table (Sheet) :-> {table_to_load.strip().ljust(25)} ;\033[0m',
              end=' ')
        if 'X' == is_loadeable:
            data_frame = pd.read_excel(excel_file, sheet_name=table_to_load)
            if 'X' == is_accounting:
                # data_frame['TIPO'].replace('', np.nan, inplace=True)
                # data_frame['Data'].replace('', np.nan, inplace=True)
                # 2024.04.03 - improvment for future pandas 3.0
                # Series through chained assignment using an inplace method.
                # The behavior will change in pandas 3.0. This inplace method will never work because the intermediate
                # object on which we are setting values always behaves as a copy.
                data_frame['TIPO'] = data_frame['TIPO'].replace('', np.nan)
                data_frame['Data'] = data_frame['Data'].replace('', np.nan)

                # if 'X' == is_cleanable and not save_useless:  ## ATENÇÃO A ISSO AQUI
                #     # limpa registros com os Tipos Nulos
                #     data_frame.dropna(subset=['TIPO'], inplace=True)
                #     # limpa registros com as Datas Nulas
                #     data_frame.dropna(subset=['Data'], inplace=True)

                general_entries_df = data_frame[["Data", "TIPO", "DESCRICAO", "Credito", "Debito"]].copy()
                general_entries_df[data_origin_col] = table_to_load
                number_lines = len(data_frame)
                # # Convert colunmns "Credito" and "Debito" from str to float
                # general_entries_df['Credito'] = pd.to_numeric(general_entries_df['Credito'], errors='coerce')
                # general_entries_df['Debito'] = pd.to_numeric(general_entries_df['Debito'], errors='coerce')

                # And put the data cleaned into table  lançamentos gerais
                if first_pass:
                    general_entries_df_full = general_entries_df.copy()
                    first_pass = False
                else:
                    general_entries_df_full = pd.concat([general_entries_df_full, general_entries_df],
                                                        ignore_index=True)

            else:
                # Writes only the tables that aren´t Accounting, because it was already loaded on table general_entries_table
                number_lines = data_frame.to_sql(table_to_load, conn, index=False, if_exists="replace")

            print(f'\033[32mLines Created :-> {str(number_lines).rjust(6)} \033[0m')

    print(f'\033[34m   . .. ... Sanitizing DataFrame       :-> {general_entries_table} :\033[0m', end=' ')

    if  not save_useless:  ## ATENÇÃO A ISSO AQUI
        # limpa registros com os Tipos Nulos
        general_entries_df_full.dropna(subset=['TIPO'], inplace=True)
        # limpa registros com as Datas Nulas
        general_entries_df_full.dropna(subset=['Data'], inplace=True)

    # Add new columns with NULL or default values
    general_entries_df_full.insert(1, 'DIA_SEMANA', np.nan)
    general_entries_df_full.insert(6, 'Mes', 'MM')
    general_entries_df_full.insert(7, 'Ano', 'yyyy')
    general_entries_df_full.insert(8, 'MES_EXTENSO', np.nan)
    general_entries_df_full.insert(9, 'AnoMes', 'YYYY/MM')
    dt = general_entries_df_full['Data'].dt

    # fix the data in several columns
    general_entries_df_full = (
        general_entries_df_full
        .assign(
            Credito=pd.to_numeric(general_entries_df_full['Credito'], errors='coerce').round(2).fillna(0),
            Debito=pd.to_numeric(general_entries_df_full['Debito'], errors='coerce').round(2).fillna(0),
            MES_EXTENSO=dt.month.map(meses),
            DIA_SEMANA=dt.dayofweek.map(dias_semana),
            Mes=dt.strftime("%m"),
            Ano=dt.strftime("%Y"),
            AnoMes=dt.strftime("%Y/%m"),
            # AnoMesNum=dt.strftime("%Y%m"),   # opcional: AAAAMM numérico
            DESCRICAO = (
                general_entries_df_full['DESCRICAO']
                .str.replace(r"[;,]", "|", regex=True)  # troca vírgula e ponto e vírgula por |
                .str.replace("∴", " .'. ")  # troca caractere especial
                .str.replace("ś","s")
                .str.strip()  # remove espaços extras no início/fim
            )
        )
    )

    # sort the data_frame before persist it on the database'
    general_entries_df_full = general_entries_df_full.sort_values(
        by=general_entries_df_full.columns[0],  # Primeira coluna
        ascending=False,  # Ordenação descendente
        ignore_index=True  # Reindexar após ordenação
    )

    print(f'\033[32mDone !!! \033[0m')

    print(f'\033[34m   . .. ... Writing Dataframe fo Table :-> {general_entries_table} :\033[0m', end=' ')
    general_entries_df_full.to_sql(general_entries_table, conn, index=False, if_exists="replace")
    # Just one commit to Save time. This commit is BEFORE the data_correjeitor
    conn.commit()
    print(f'\033[32mDone !!! \033[0m')

    data_correjeitor(conn.cursor(), types_sheet, general_entries_table, save_useless, udt)
    conn.commit()
    conn.close()

