import sqlite3
import pandas as pd

def create_dinamic_reports(sqlite_database, excel_file, din_report_guinding, full_pivot):
    # todo: put some Fancy  output Message
    print('Creating Dynamic Reports for summarized history ... .. . ')
    conn = sqlite3.connect(sqlite_database)
    # with the name of the din_report_guinding , reads the Sheets do be loaded
    data_frame = pd.read_excel(excel_file, sheet_name=din_report_guinding)
    # We have to write this dataframe on db to use the tables further
    number_lines = data_frame.to_sql(din_report_guinding, conn, index=False, if_exists="replace")
    print(f'Dynamic Reports Table Created! Total of Dynamic Reports :-> \033[31m{str(number_lines).rjust(6)}\033[0m ')
    # Now we have to create Single tables of each din report , based on the names of the sheets
    for i, linhas in data_frame.iterrows():
        # now for each din report, we have to read the correspondig excel sheet
        report_table = linhas.DEST_TABLE
        report_xl_sheet = linhas.SHEETY
        report_description = linhas.REPORT_NAME
        print(
            f'\033[34m   . .. ... Step: {i + 1:04} : Creating Dynamic Report Table\033[0m  :-> \033[33m"{report_description}"\033[0m ')
        columns_of_report = pd.read_excel(excel_file, sheet_name=report_xl_sheet)

        # finally, create the table to be used in the future
        # number_lines = columns_of_report.to_sql(report_xl_sheet, conn, index=False, if_exists="replace")
        # print(f'                                        Dynamic Reports :-> {report_table} ')
        # Now, for each dynamic report, read the corresponding Sheet
        df_single_sheet = pd.read_excel(excel_file, sheet_name=report_xl_sheet)
        # here we have to Build de Dynamic table
        base_sql_string = "SELECT "
        sum_tables = " ("
        for j in df_single_sheet.index:
            column_name = df_single_sheet['COLUMN_NAME'][j]
            base_sql_string += "HG.'" + column_name + "',"
            if j > 0:
                sum_tables += "HG.'" + column_name + "'+"

        # At the end of the Loop, fix the Strings
        sum_tables = sum_tables[:-1] + ")"

        base_sql_string = base_sql_string + sum_tables + f' as "Valor Total" FROM {full_pivot} HG; '
        # Now, run the SQL Query to build the Data-frame
        df = pd.read_sql_query(base_sql_string, conn)
        # writes the data-frame into a table on SQLite
        df.to_sql(report_table, conn, if_exists='replace', index=False)

    # Here is the end of the First Loop
    conn.close()
