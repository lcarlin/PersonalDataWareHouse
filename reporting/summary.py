
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

if __name__ == '__main__':
    input_param_file = ""

    if len(sys.argv) == 2:
        input_param_file = sys.argv[1]

    main(input_param_file)

# EOP

