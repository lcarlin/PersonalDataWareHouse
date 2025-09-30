def table_droppator(conexao, table_name):
    cursor = conexao
    cursor.execute("DROP TABLE IF EXISTS " + table_name)
    print(f"Table {table_name} dropped... ")

