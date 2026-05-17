import sqlite3
import pandas as pd


def totalizador_diario(database_file, in_table, out_table):
    print("Totaling the Daily Amount of data ... .. .", end=' ')
    conn = sqlite3.connect(database_file)
    df = pd.read_sql_query(f"select * from {in_table}", conn)
    df_contagem = df.groupby('Data').size().reset_index(name='Contagem')
    df_contagem['Contagem Acumulada'] = df_contagem['Contagem'].cumsum()
    df_contagem = df_contagem[['Data', 'Contagem Acumulada']]
    number_lines = df_contagem.to_sql(out_table, conn, index=False, if_exists="replace")
    print(f'\033[32m Done !!!  {number_lines} Days loaded \033[0m')
    conn.commit()
    conn.close()


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


def split_paymnt_resume(db_file, split_paymnt_table, out_table):
    print('Creating payment in installments Summaries ... .. .  ')
    db_conn = sqlite3.connect(db_file)

    df_parcelamentos = pd.read_sql(f"SELECT * FROM {split_paymnt_table}", db_conn)
    df_parcelamentos['Ano_Mes'] = pd.to_datetime(df_parcelamentos['Data']).dt.to_period('M')
    df_agrupado = df_parcelamentos.groupby('Ano_Mes').agg(Quantidade=('Data', 'size'),
                                                          Valor=('Debito', 'sum')).reset_index()
    df_agrupado['Diff_QTD'] = df_agrupado['Quantidade'].diff().fillna(0)
    df_agrupado['Diff_Vlr'] = df_agrupado['Valor'].diff().fillna(0)
    df_agrupado['Ano_Mes'] = df_agrupado['Ano_Mes'].astype(str)
    df_agrupado['Valor'] = df_agrupado['Valor'].round(2)
    df_agrupado['Diff_Vlr'] = df_agrupado['Diff_Vlr'].round(2)
    df_agrupado.to_sql(out_table, db_conn, index=False, if_exists="replace")
