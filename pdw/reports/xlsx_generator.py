import sqlite3
import pandas as pd
import yaml

from pdw.analytics.totals import totalizador_diario


def xlsx_report_generator(sqlite_database, dir_out, file_name, write_multiple_files, out_extension, entries_table,
                          dynamic_reports, dyn_rep_tab, gera_hist, anual_hist, full_hist, day_prog, splt_pmnt_res,
                          mont_summ, yaml_queries_file):
    """
    Gera relatórios em Excel a partir de queries SQL definidas em arquivo YAML.

    Args:
        yaml_queries_file: Caminho para o arquivo YAML contendo as queries
    """

    # Carrega as queries do arquivo YAML
    queries_config = None
    try:
        # Carrega as queries do arquivo YAML
        with open(yaml_queries_file, 'r', encoding='utf-8') as file:
            queries_config = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{yaml_queries_file}' não foi encontrado.")
    except PermissionError:
        print(f"Erro: Sem permissão para ler o arquivo '{yaml_queries_file}'.")
    except yaml.YAMLError as e:
        print(f"Erro ao processar o YAML: {e}")
    except UnicodeDecodeError:
        print(f"Erro: Problema de codificação ao ler o arquivo '{yaml_queries_file}'.")
    except Exception as e:
        print(f"Erro inesperado ao ler o arquivo: {e}")

    if queries_config is None :
       print('exiting due previous errors ... .. .')
       exit (1)

    print(f'Queries File located :->\033[32m {yaml_queries_file}\033[0m')
    totalizador_diario(sqlite_database, entries_table, day_prog)
    print('Exporting Summarized data ... .. .  ')

    connection = sqlite3.connect(sqlite_database)
    file_full_path = dir_out + file_name + '.' + out_extension
    lista_consultas = []

    if write_multiple_files:
        xlsx_writer = pd.ExcelWriter(file_full_path, engine='xlsxwriter', date_format='yyyy-mm-dd')

    # Monta as queries substituindo os placeholders pelas variáveis
    variables = {
        'entries_table': entries_table,
        'full_hist': full_hist,
        'anual_hist': anual_hist,
        'day_prog': day_prog,
        'splt_pmnt_res': splt_pmnt_res,
        'mont_summ': mont_summ,
        'dyn_rep_tab': dyn_rep_tab
    }

    # Processa queries condicionais (gera_hist)
    if gera_hist:
        for query_item in queries_config.get('queries_gera_hist', []):
            sql = query_item['sql'].format(**variables)
            sheet_name = query_item['sheet_name'].format(**variables)
            lista_consultas.append([sql, sheet_name])

    # Processa queries padrão
    for query_item in queries_config.get('queries_padrao', []):
        sql = query_item['sql'].format(**variables)
        sheet_name = query_item['sheet_name']
        lista_consultas.append([sql, sheet_name])

    # Processa queries dinâmicas
    if gera_hist and dynamic_reports:
        df_dyn = pd.read_sql(f"select * from {dyn_rep_tab}", connection)
        for i, linhas in df_dyn.iterrows():
            lista_consultas.append([f"SELECT * FROM {linhas.DEST_TABLE} ;", f"{linhas.REPORT_NAME}"])

    # Loop de exportação (mantido idêntico)
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
