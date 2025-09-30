import sqlite3
import pandas as pd

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

