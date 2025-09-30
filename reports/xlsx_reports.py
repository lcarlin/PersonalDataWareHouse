import sqlite3
import pandas as pd
from utils.daily_totalizer import totalizador_diario

def xlsx_report_generator(sqlite_database, dir_out, file_name, write_multiple_files, out_extension, entries_table,
                          dynamic_reports, dyn_rep_tab, gera_hist, anual_hist, full_hist, day_prog, splt_pmnt_res,
                          mont_summ):
    # TODO: put the Dynamic Reports statments . How? IDK
    ## PUT here the contagem cumulada call
    totalizador_diario(sqlite_database, entries_table, day_prog)
    print('Exporting Summarized data ... .. .  ')
    connection = sqlite3.connect(sqlite_database)
    file_full_path = dir_out + file_name + '.' + out_extension
    lista_consultas = []
    if write_multiple_files:
        xlsx_writer = pd.ExcelWriter(file_full_path, engine='xlsxwriter', date_format='yyyy-mm-dd')

    if gera_hist:
        lista_consultas.append([
            f"select * from {full_hist} where date(SUBSTR(AnoMes,1,4)||'-'||SUBSTR(AnoMes,6,2)||'-'||'01') >= date('now','-13 month');" \
            , full_hist + "12Meses"])
        lista_consultas.append([f"select * from {full_hist};", f"{full_hist}"])
        lista_consultas.append([f"select * from {anual_hist};", f"{anual_hist}"])
        ###
        lista_consultas.append([
            f"select * from {full_hist}_QTD where date(SUBSTR(AnoMes,1,4)||'-'||SUBSTR(AnoMes,6,2)||'-'||'01') >= date('now','-13 month');" \
            , full_hist + "_QTD12Meses"])
        lista_consultas.append([f"select * from {full_hist}_QTD;", f"{full_hist}_QTD"])
        lista_consultas.append([f"select * from {anual_hist}_QTD;", f"{anual_hist}_QTD"])
        ##

    lista_consultas.append([f"select tipo as Categoria, sum(debito) as Valor , count(1) as QTD from {entries_table}" \
                            " where Data >= date('now','-1 month')  and Data <= date('now', '+1 day') and debito > 0 " \
                            " group by tipo order by 2 desc;", "Ultimos30Dias"])
    # lista_consultas.append(
    #     ["SELECT substr (LG.DATA, 9,2 ) || '/' || substr (LG.DATA, 6,2 ) || '/' || substr(LG.DATA, 1,4) AS Quando " \
    #      ", LG.DIA_SEMANA as 'Dia da Semana' " \
    #      ", LG.Tipo as 'Tipo' " \
    #      ", LG.DESCRICAO  as 'Descricao/Lancamento' " \
    #      ", replace (LG.Credito, '.', ',') as 'Credito' " \
    #      ", replace (LG.DEBITO, '.', ',') as 'Debito' " \
    #      ", char(39)|| substr(LG.DATA, 9,2) as Dia" \
    #      ", char(39)|| mes as 'Mes' " \
    #      # ", char(39)|| cast (mes as text) as 'Mes' " \
    #      # ", char(39)||cast (ano as text) as 'Ano' " \
    #      ", char(39)|| ano as 'Ano' " \
    #      #", char(39)||cast (AnoMes as text )  as 'Ano/Mes' " \
    #      ", LG.MES_EXTENSO as 'Mes Por Extenso' " \
    #      ", char(39)|| AnoMes as 'Ano/Mes' " \
    #      ", LG.ORIGEM  as Origem " \
    #      f" FROM {entries_table} LG ;", entries_table])
    lista_consultas.append(["select Ano || ' - ' || Mes as 'Referência', count(1) as 'Total' " \
                            ", round( cast (count(1) as float)  / ( case Mes when '01' then 31" \
                            " when '02' then 28 when '03' then 31 when '04' then 30 when '05' then 31" \
                            " when '06' then 30 when '07' then 31 when '08' then 31 when '09' then 30" \
                            " when '10' then 31 when '11' then 30 when '12' then 31 end ),2) as 'Por Dia'" \
                            f" from {entries_table} group by  Ano || ' - ' || Mes " \
                            " order by  Ano || ' - ' || Mes desc ;", "Iterações_Mensais"])
    lista_consultas.append(["SELECT DIA_SEMANA, COUNT(1) AS TOTAL " \
                            f" FROM {entries_table} LG " \
                            " WHERE Data >= date('now','-13 month') " \
                            " GROUP BY DIA_SEMANA " \
                            " ORDER BY 2 DESC ;", "Iterações_Semanais_12M"])
    lista_consultas.append(["select dois.AnoMes as Referencia , round(dois.debitos,2) as Débito ," \
                            " round(dois.creditos,2) as Créditos , round(dois.creditos - dois.debitos,2 ) " \
                            " as ""Posição"" from ( SELECT AnoMes , sum (lg.Debito) as debitos , Sum (lg.Credito) " \
                            f" as Creditos FROM {entries_table} LG where LG.TIPO not in " \
                            " ('cartões de Crédito','Transf. Bco') GROUP BY AnoMes order by Ano desc, mes DESC ) dois ;"
                               , "Debitos Mensais"])

    lista_consultas.append([f"SELECT origem, count(1) as Total FROM {entries_table} " \
                            "group by origem ORDER BY Total desc ; ", "Histórico de Uso"])
    lista_consultas.append([f"SELECT * FROM {day_prog} ORDER BY 1 DESC;", "Contagem dia-a-dia"])
    lista_consultas.append([f"SELECT * FROM {splt_pmnt_res} ORDER BY 1 DESC;", "Resumo de Parcelamentos"])
    lista_consultas.append([f"SELECT * FROM {mont_summ} ;", "Resumos_In_out Mensal"])
    lista_consultas.append([f"SELECT * FROM {mont_summ}_ANUAL ;", "Resumos_In_out Anual"])
    lista_consultas.append([f"SELECT * FROM {mont_summ}_full ;", "Resumos_In_out FULL"])
    lista_consultas.append(["select  TIPO ,AnoMes,  sum(Credito) as Creditos, sum (debito)  as Debitos" \
                            f" from {entries_table} lg " \
                            " group by AnoMes , Tipo order by 1,2 ; ", "Resumo Mensal Lancto"])
    lista_consultas.append(["select  TIPO ,Ano,  sum(Credito) as Creditos, sum (debito)  as Debitos" \
                            f" from {entries_table} lg " \
                            " group by Ano , Tipo order by 1,2 ; ", "Resumo Anual Lancto"])

    if gera_hist and dynamic_reports:
        df_dyn = pd.read_sql(f"select * from {dyn_rep_tab}", connection)
        for i, linhas in df_dyn.iterrows():
            lista_consultas.append([f"SELECT * FROM {linhas.DEST_TABLE} ;", f"{linhas.REPORT_NAME}"])

    for k in range(0, len(lista_consultas)):
        consulta = lista_consultas[k]
        sql_statment = consulta[0]
        excel_sheet = consulta[1]
        # print(sql_statment)
        df_out = pd.read_sql(sql_statment, connection)

        if write_multiple_files:
            message = f'\033[34m   . .. ... Step: {k + 1:04} :-> Exporting Sheet {excel_sheet.ljust(27)} \033[33mto {file_full_path}\033[0m'
            df_out.to_excel(xlsx_writer, sheet_name=excel_sheet, index=False)
        else:
            file_full_path = dir_out + excel_sheet + '.v2.' + out_extension
            message = f'   . .. ... Step: {k + 1:04} :-> Exporting {file_full_path} to file(s) '
            df_out.to_excel(file_full_path, sheet_name=excel_sheet, index=False, date_format='DD/MM/YYYY')

        print(message)

    connection.close()
    if write_multiple_files:
        xlsx_writer.close()