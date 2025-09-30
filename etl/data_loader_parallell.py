import threading

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


