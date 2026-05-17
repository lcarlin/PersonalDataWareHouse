def table_droppator(conexao, table_name):
    cursor = conexao
    cursor.execute("DROP TABLE IF EXISTS " + table_name)
    print(f"Table {table_name} dropped... ")


def sort_dataframe_by_date(df, ascending=False):
    """
    Ordena o DataFrame pela primeira coluna (Data).

    Args:
        df (pd.DataFrame): DataFrame a ordenar
        ascending (bool): Ordem ascendente (True) ou descendente (False)

    Returns:
        pd.DataFrame: DataFrame ordenado
    """
    return df.sort_values(
        by=df.columns[0],
        ascending=ascending,
        ignore_index=True
    )

def save_dataframe_to_database(df, conn, table_name, sort_by_date=True):
    """
    Salva DataFrame no banco de dados SQLite.

    Args:
        df (pd.DataFrame): DataFrame a salvar
        conn: Conexão SQLite
        table_name (str): Nome da tabela
        sort_by_date (bool): Se deve ordenar por data antes de salvar

    Returns:
        int: Número de linhas salvas
    """
    print(f'\033[34m   . .. ... Writing Dataframe to Table :-> {table_name} :\033[0m', end=' ')
    if sort_by_date:
        df = sort_dataframe_by_date(df, ascending=False)

    df.to_sql(table_name, conn, index=False, if_exists="replace")
    print(f'\033[32mDone !!! \033[0m')
    return len(df)
