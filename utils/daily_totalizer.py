import sqlite3
import pandas as pd

def totalizador_diario(database_file, in_table, out_table):
    print("Totaling the Daily Amount of data ... .. .")
    conn = sqlite3.connect(database_file)
    df = pd.read_sql_query(f"select * from {in_table}", conn)
    df_contagem = df.groupby('Data').size().reset_index(name='Contagem')
    df_contagem['Contagem Acumulada'] = df_contagem['Contagem'].cumsum()
    df_contagem = df_contagem[['Data', 'Contagem Acumulada']]
    number_lines = df_contagem.to_sql(out_table, conn, index=False, if_exists="replace")
    conn.commit()
    conn.close()
