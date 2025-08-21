
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


    general_entries_df_full.insert(1, 'DIA_SEMANA', np.nan)
    general_entries_df_full.insert(6, 'Mes', 'MM')
    general_entries_df_full.insert(7, 'Ano', 'yyyy')
    general_entries_df_full.insert(8, 'MES_EXTENSO', np.nan)
    general_entries_df_full.insert(9, 'AnoMes', 'YYYY/MM')
    # Convert colunmns "Credito" and "Debito" from str to float
    general_entries_df_full['Credito'] = pd.to_numeric(general_entries_df_full['Credito'], errors='coerce')
    general_entries_df_full['Debito'] = pd.to_numeric(general_entries_df_full['Debito'], errors='coerce')

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



def parallel_df(db_file, xls_file, config_dict, general_out_table, index):
    db_connection = sqlite3.connect(db_file)
    tmp_table_name = config_dict['table_to_load']
    print(f'   . .. ... .... Begin of Thread Number :-> {index}  ; Table/Sheet Name :-> {tmp_table_name} ')
    data_frame = pd.read_excel(xls_file, sheet_name=config_dict['table_to_load'])
    if 'X' == config_dict['isAccounting'] and 'X' == config_dict['isCleanable']:
        # delete records with null 'TIPO'
        data_frame['TIPO'].replace('', np.nan, inplace=True)
        data_frame.dropna(subset=['TIPO'], inplace=True)
        # delete records with null DATA column
        data_frame['Data'].replace('', np.nan, inplace=True)
        data_frame.dropna(subset=['Data'], inplace=True)
        general_entries_df = data_frame[["Data", "TIPO", "DESCRICAO", "Credito", "Debito"]].copy()
        general_entries_df.insert(1, 'DIA_SEMANA', np.nan)
        general_entries_df['Mes'] = 'MM'
        general_entries_df['Ano'] = 'YYYY'
        general_entries_df['AnoMes'] = 'YYYY/MM'
        general_entries_df['Origem'] = config_dict['table_to_load']
        # Ja joga os dados limpos na lançamentos gerais
        general_entries_df.to_sql(general_out_table, db_connection, index=False, if_exists="append")

    # grava a tabela (UNITÁRIA) do data_frame do BD
    data_frame.to_sql(config_dict['table_to_load'], db_connection, index=False, if_exists="replace")
    db_connection.commit()
    db_connection.close()
    print(f'   . .. ... .... End of Thread Number :-> {index}  ; Table/Sheet Name :-> {tmp_table_name} ')

# def data_loader_parallel(data_base, general_entries_table, guindind_sheet, excel_file):


def data_loader_parallel(data_base, types_sheet, general_entries_table, guindind_sheet, excel_file, save_useless, udt):
    conn = sqlite3.connect(data_base, check_same_thread=False)
    work_books = pd.ExcelFile(excel_file)
    sheets_dataframe = work_books.parse(sheet_name=guindind_sheet)
    table_droppator(conn.cursor(), general_entries_table)
    conn.commit()
    jobs = list()
    print("Running Loader of the Sheets into database Tables ... .. .  ")
    for i, infos in sheets_dataframe.iterrows():
        dict_config = {'table_to_load': infos.TABLE_NAME,
                       'isAccounting': infos.ACCOUNTING,
                       'isCleanable': infos.CLEANABLE,
                       'isLoadeable': infos.LOADABLE}

        tmp_table_name = dict_config['table_to_load']
        print(f'   . .. ... Step:->  {i + 1:04} ; Table (Sheet) :-> "{tmp_table_name}"')
        if 'X' == dict_config['isLoadeable']:
            # thread = threading.Thread(target=parallel_df(conn, excel_File, dict_config, General_Entries_table, i + 1))
            thread = threading.Thread(target=parallel_df,
                                      args=(data_base, excel_file, dict_config, general_entries_table, i + 1))
            jobs.append(thread)

    print(f'   . .. ... Starting Multi-Threaging processing')
    for m in jobs:
        m.start()

    print(f'   . .. ... Waiting for Threads to End ')
    # Ensure all  the threads have finished
    for index, tread in enumerate(jobs):
        print(f'   ... .. . Index Of :-> {index}')
        thread.join()

    print(f'   . .. ... All threads has ended ')
    data_correjeitor(conn.cursor(), types_sheet, general_entries_table, save_useless, udt)
    print(f'   . .. ... Data-Loader Done !!! !! ! ')
    conn.commit()
    conn.close()
    # connection.close()


