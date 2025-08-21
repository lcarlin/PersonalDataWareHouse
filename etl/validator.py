
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

    lista_acoes.append((f"Update {entries_table} \
       set Mes = strftime ('%m',data )  \
       , Ano = strftime ('%Y',data )  \
       , AnoMes = strftime ('%Y',data )||'/'||strftime ('%m',data )  ;", "Fixing Dates"))
    lista_acoes.append((f"update {entries_table} set credito = 0 where credito is null ;", "Fixing Credit Info"))
    lista_acoes.append((f"update {entries_table} set debito = 0 where debito is null ;", "Fixing Debit Info"))
    lista_acoes.append(
        (f"Delete from {types_sheet} WHERE ( Código IS NULL or Descrição IS NULL) ;", "Deleting NULL info"))
    lista_acoes.append((
        f"update {entries_table} set descricao = replace (descricao,'∴', '.''.') where descricao like '%∴%' ;",
        "Fixing Special char (1)"))
    lista_acoes.append((
        f"update {entries_table} set descricao = replace (descricao,'ś', '''s') where descricao like '%ś%' ;",
        "Fixing Special char (2)"))
    # lista_acoes.append(f"update {entries_table} set descricao = replace (descricao,'', '''s')  ;")
    lista_acoes.append(
        (f"update {entries_table} set credito  = round(credito,2) where credito > 0  ;", "Rouding Credit info"))
    lista_acoes.append(
        (f"update {entries_table} set debito  = round(debito,2) where debito > 0  ;", "Rouding Debit info"))
    lista_acoes.append((
        f"update {entries_table} set descricao = replace (descricao,',', '|') where descricao like '%,%' ;",
        "Fixing Special char (3)"))
    lista_acoes.append((
        f"update {entries_table} set descricao = replace (descricao,';', '|') where descricao like '%;%' ;",
        "Fixing Special char (4)"))
    lista_acoes.append((f"UPDATE {entries_table} " \
                        "  SET DIA_SEMANA = case cast (strftime('%w', Data ) as integer) " \
                        "  when 0 then 'Domingo' " \
                        "  when 1 then 'Segunda-Feira' " \
                        "  when 2 then 'Terça-Feira' " \
                        "  when 3 then 'Quarta-Feira' " \
                        "  when 4 then 'Quinta-Feira' " \
                        "  when 5 then 'Sexta-Feira' " \
                        "  when 6 then 'Sábado' " \
                        "  else 'UNDEFINED' end " \
                        "    where DIA_SEMANA IS NULL ;", "Fixing Day-Of-Week"))
    lista_acoes.append((f"UPDATE {entries_table} " \
                        "    SET MES_EXTENSO = ( case MES WHEN '01' THEN '01-Janeiro' " \
                        "        WHEN '02' THEN '02-Fevereiro' " \
                        "         WHEN '03' THEN '03-Março' " \
                        "         WHEN '04' THEN '04-Abril' " \
                        "         WHEN '05' THEN '05-Mail' " \
                        "         WHEN '06' THEN '06-Junho' " \
                        "         WHEN '07' THEN '07-Julho' " \
                        "         WHEN '08' THEN '08-Agosto' " \
                        "         WHEN '09' THEN '09-Setembro' " \
                        "         WHEN '10' THEN '10-Outubro' " \
                        "         WHEN '11' THEN '11-Novembro' " \
                        "         WHEN '12' THEN '12-Dezembro' " \
                        "         ELSE 'UNDEFINED' " \
                        "         END ) " \
                        "   WHERE MES_EXTENSO IS NULL ;", "Fixing months"))

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


