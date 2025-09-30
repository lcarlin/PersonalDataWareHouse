import sqlite3
import pandas as pd

def monthly_summaries (db_file, in_table, out_table):
    print(f'Generating summaries of all accounting sheets into {out_table} table ... .. .')
    db_conn = sqlite3.connect(db_file)
    sql_statment = f'SELECT * FROM {in_table} ;'
    df_entrada = pd.read_sql(sql_statment, db_conn)

    df_agrupado = df_entrada.groupby(['AnoMes', 'Origem']).agg(
        CREDITO=('Credito', 'sum'),
        DEBITO=('Debito', 'sum')
    ).reset_index()
    df_agrupado['Posição'] = df_agrupado['CREDITO'] - df_agrupado['DEBITO']
    df_agrupado = df_agrupado.sort_values(by=['Origem', 'AnoMes']).reset_index(drop=True)

    df_agrupado_anual = df_entrada.groupby(['Ano', 'Origem']).agg(
        CREDITO=('Credito', 'sum'),
        DEBITO=('Debito', 'sum')
    ).reset_index()
    df_agrupado_anual['Posição'] = df_agrupado_anual['CREDITO'] - df_agrupado_anual['DEBITO']
    df_agrupado_anual = df_agrupado_anual.sort_values(by=['Origem', 'Ano']).reset_index(drop=True)

    df_agrupado_full = df_entrada.groupby('Origem').agg(
        CREDITO=('Credito', 'sum'),
        DEBITO=('Debito', 'sum')
    ).reset_index()
    df_agrupado_full['Posição'] = df_agrupado_full['CREDITO'] - df_agrupado_full['DEBITO']
    df_agrupado_full = df_agrupado_full.sort_values(by='Origem').reset_index(drop=True)

    df_agrupado.to_sql(out_table, db_conn, index=False, if_exists='replace')
    df_agrupado_anual.to_sql(out_table + '_ANUAL', db_conn, index=False, if_exists='replace')
    df_agrupado_full.to_sql(out_table + '_FULL', db_conn, index=False, if_exists='replace')

