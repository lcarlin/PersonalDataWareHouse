def data_correjeitor(conexao, types_sheet, entries_table, save_useless, useless_table):
    print(f'Normalizing data on {entries_table} Table ...')
    cursor = conexao
    lista_acoes = []
    if save_useless:
        print(f'   . .. ... Saving discated Data')
        table_droppator(cursor, useless_table)
        lista_acoes.append((
            f"create table {useless_table} as select * from {entries_table} where (data is null or tipo is null); ",
            "Saving Useless"))
        lista_acoes.append((f"delete from {entries_table} where (data is null or tipo is null);", "Deleting Useless"))

    lista_acoes.append(
        (f"Delete from {types_sheet} WHERE ( Código IS NULL or Descrição IS NULL) ;", "Deleting NULL info"))
    lista_acoes.append(('DELETE FROM Parcelamentos WHERE 1 = 1 AND (DATA IS NULL OR "Tipo Lançamento" is null) ;',
                        "Deleting Parcelamentos"))
    # lista_acoes.append((f'create index SHAWASKA on {entries_table}  (DATA, TIPO, DESCRICAO) ',"(Re)creating Index"))
    lista_acoes.append((f'DROP VIEW IF EXISTS Origens; ', "Dropping View"))
    lista_acoes.append((
                       f"create view Origens as select TABLE_NAME as nome from GUIDING gd where gd.LOADABLE = 'X' AND GD.ACCOUNTING = 'X';",
                       "Creating View"))

    for i in range(0, len(lista_acoes)):
        sql_string = lista_acoes[i][0]
        action_desc = lista_acoes[i][1].ljust(25)
        print(f'\033[34m   . .. ... Step: {i + 1:04} :-> {action_desc} ;\033[0m', end=' ')
        cursor.execute(sql_string)
        print(f'\033[31mLines Affected: {str(cursor.rowcount).rjust(5)}\033[0m')

