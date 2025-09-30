import sqlite3
import pandas as pd
def create_pivot_history (data_base_file, types_table, entries_table, out_table_General, out_table_Anual):
    print('Creating pivot Tables ... .. . ')
    connection = sqlite3.connect(data_base_file)

    sql_statment_types = f'SELECT Descrição as TIPO FROM {types_table} ;'
    sql_statment_summary = f'SELECT * FROM {entries_table} ;'

    df_summary = pd.read_sql(sql_statment_summary, connection)
    df_types = pd.read_sql(sql_statment_types, connection)

    print('                      ... .. . to Monthly Values to summarized in history ... .. .')
    pivot_full = df_summary.pivot_table(index='AnoMes', columns='TIPO', values='Debito', aggfunc='sum').fillna(0)
    pivot_full = pivot_full[df_types['TIPO']]
    pivot_full = pivot_full.reset_index()
    pivot_full.to_sql(out_table_General, connection, index=False, if_exists="replace")

    print('                      ... .. . to Monthly total to summarized in history ... .. .')
    pivot_full = df_summary.pivot_table(index='AnoMes', columns='TIPO', values='Debito', aggfunc='count').fillna(0)
    pivot_full = pivot_full[df_types['TIPO']]
    pivot_full = pivot_full.reset_index()
    pivot_full.to_sql(out_table_General + '_QTD', connection, index=False, if_exists="replace")

    print('                      ... .. . to Anual Values to summarized in history ... .. .')
    pivot_anual = df_summary.pivot_table(index='Ano', columns='TIPO', values='Debito', aggfunc='sum').fillna(0)
    pivot_anual = pivot_anual[df_types['TIPO']]
    pivot_anual = pivot_anual.reset_index()
    pivot_anual.to_sql(out_table_Anual, connection, index=False, if_exists="replace")

    print('                      ... .. . to Anual total summarized in history ... .. .')
    pivot_anual = df_summary.pivot_table(index='Ano', columns='TIPO', values='Debito', aggfunc='count').fillna(0)
    pivot_anual = pivot_anual[df_types['TIPO']]
    pivot_anual = pivot_anual.reset_index()
    pivot_anual.to_sql(out_table_Anual + '_QTD', connection, index=False, if_exists="replace")

    connection.commit()