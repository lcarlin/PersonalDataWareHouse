import sqlite3
import pandas as pd


def transient_data_exportator(sqlite_database, dir_out, out_extension, file_name, transient_data_table, origing_column):
    print('Exporting Transient data into individual Sheelts ... .. .  ')
    file_full_path = dir_out + file_name + '.' + datetime.datetime.now().strftime(
        "%Y%m%d.%H%M%S") + '.' + out_extension
    connection = sqlite3.connect(sqlite_database)
    xlsx_writer = pd.ExcelWriter(file_full_path, engine='xlsxwriter', date_format='yyyy-mm-dd')
    guiding_df = pd.read_sql(f"select distinct {origing_column} from {transient_data_table}", connection)
    conn = connection.cursor()

    for i, linhas in guiding_df.iterrows():
        excel_sheet = f"{linhas.Origem}"
        message = f'   . .. ... Step: {i + 1:04} :-> Exporting Sheet {excel_sheet.ljust(25)} to {file_full_path}'
        sql_statment = f"SELECT * FROM {transient_data_table} where {origing_column} = '{linhas.Origem}' and EXPORT_DATE is null order by 1;"
        df_out = pd.read_sql(sql_statment, connection)
        if len(df_out) > 0:
            print(message)
            df_out.to_excel(xlsx_writer, sheet_name=excel_sheet, index=False)
            conn.execute(
                f"UPDATE {transient_data_table} SET EXPORT_DATE = datetime('now') WHERE {origing_column} = '{linhas.Origem}'; ")
            conn.execute('COMMIT; ')

    connection.close()
    xlsx_writer.close()
    return file_full_path
