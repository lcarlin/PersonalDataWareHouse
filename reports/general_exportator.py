import sqlite3
import pandas as pd
from utils.compressor import gzip_compressor
from utils.xml_df import dataframe_to_xml


def general_entries_file_exportator(data_base_file, dir_out, file_out, table_name, other_types) :
    connection = sqlite3.connect(data_base_file)
    file_full_path = dir_out + file_out + '.v2'
    print(f"Exporting {file_full_path} to file(s) ")
    sqlStatment = "SELECT substr (LG.DATA, 9,2 )||'-'||substr(LG.DATA,6,2 )||'-' || substr(LG.DATA, 1,4) AS Quando " \
                  ", LG.DIA_SEMANA as 'Dia da Semana' " \
                  ", LG.Tipo as 'Tipo' " \
                  ", LG.DESCRICAO  as 'Descricao/Lancamento' " \
                  ", replace (LG.Credito, '.', ',') as 'Credito' " \
                  ", replace (LG.DEBITO, '.', ',') as 'Debito' " \
                  ", char(39)||cast (mes as text) as 'Mes' " \
                  ", char(39)||cast (ano as text) as 'Ano' " \
                  ", char(39)||MES_EXTENSO as 'Mes(Por Extenso)' " \
                  ", char(39)||cast (AnoMes as text )  as 'Ano/Mes' " \
                  ", LG.ORIGEM  as Origem " \
                  f" FROM {table_name} LG ORDER  BY DATA DESC ; "

    df_out = pd.read_sql(sqlStatment, connection)
    row_count = len(df_out.index)
    df_out.to_csv(file_full_path + '.csv', sep=';', index=False, encoding='cp1252')
    if other_types:
        print(f"              Exporting JSON file(s) ")
        df_out.to_json(file_full_path + '.json', orient='records', lines=True, indent=1, force_ascii=False)
        gzip_compressor(file_full_path + '.json')
        # df_out.to_html(file_full_path + '.html')
        # df_out.to_xml(file_full_path + '.xml', parser = 'lxml', pretty_print=True, xml_declaration=True)
        print(f"              Exporting XML file(s) ")
        dataframe_to_xml(df_out, file_full_path + '.xml')
        gzip_compressor(file_full_path + '.xml')

    print(
        f'File(s) export(s) for table "{table_name}" has been created successfully! Total Lines exported :-> {row_count}')
    connection.close()