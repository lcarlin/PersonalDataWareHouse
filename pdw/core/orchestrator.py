import datetime
import os
import platform
import threading
import time

from pdw.config.loader import load_config
from pdw.infrastructure.logging import open_log, finalize_log
from pdw.etl.loader import new_data_loader
from pdw.analytics.pivot import create_pivot_history, create_dinamic_reports
from pdw.analytics.totals import monthly_summaries, split_paymnt_resume
from pdw.reports.exporter import general_entries_file_exportator
from pdw.reports.xlsx_generator import xlsx_report_generator


def run_pipeline(param_file):
    # Environment / Variables
    # current date and time
    start = time.time()
    started = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    os_pataform = platform.system()

    # if the system is windows then use the below
    # command to check for the hostname
    if os_pataform == "Windows":
        hostname = platform.uname().node
    else:
        # otherwise use the below command
        hostname = os.uname()[1]

    cfg = load_config(param_file)

    current_version    = cfg['current_version']
    config_file        = cfg['config_file']
    dir_file_in        = cfg['dir_file_in']
    dir_file_out       = cfg['dir_file_out']
    dir_db             = cfg['dir_db']
    in_file            = cfg['in_file']
    in_type            = cfg['in_type']
    out_type           = cfg['out_type']
    out_db             = cfg['out_db']
    output_name        = cfg['output_name']
    db_file_type       = cfg['db_file_type']
    log_file_cfg       = cfg['log_file_cfg']
    multithread        = cfg['multithread']
    overwrite_db       = cfg['overwrite_db']
    run_loader         = cfg['run_loader']
    run_reports        = cfg['run_reports']
    multi_rept_file    = cfg['multi_rept_file']
    guiding_table      = cfg['guiding_table']
    types_of_entries   = cfg['types_of_entries']
    general_entries_table = cfg['general_entries_table']
    create_pivot       = cfg['create_pivot']
    save_discarted_data   = cfg['save_discarted_data']
    discarted_data_table  = cfg['discarted_data_table']
    full_hist_table    = cfg['full_hist_table']
    anual_hist_table   = cfg['anual_hist_table']
    origem_dados       = cfg['origem_dados']
    other_file_types   = cfg['other_file_types']
    dinamic_reports    = cfg['dinamic_reports']
    din_report_guinding   = cfg['din_report_guinding']
    dayly_progress     = cfg['dayly_progress']
    split_paymnt_table = cfg['split_paymnt_table']
    out_table          = cfg['out_table']
    monthly_summarie   = cfg['monthly_summarie']
    queries_file       = cfg['queries_file']

    input_file = dir_file_in + in_file + '.' + in_type
    pdw_sql_file = dir_file_in + queries_file
    if overwrite_db:
        sqlite_database = dir_db + out_db + '.' + db_file_type
    else:
        sqlite_database = dir_db + out_db + '.' + datetime.datetime.now().strftime(
            "%Y%m%d.%H%M%S") + '.' + db_file_type

    if not os.path.exists(dir_file_in):
        print(f'The Input Directory {dir_file_in} does not exists  !!! !! !')
        exit(1)

    if not os.path.exists(dir_file_out):
        print(f'The Output Directory {dir_file_out} does not exists ... .. .')
        exit(1)

    if not os.path.isfile(input_file):
        print(f'The Input Load File {input_file} does not exists in the Input Directory {dir_file_in} ... .. .')
        exit(1)

    log_file, number_of_runs, last_run_date = open_log(log_file_cfg)

    out_line = ">" + ("=" * 120) + "<"
    print(out_line)
    print(f'Current Version         :-> \033[32m{current_version}\033[0m')
    print(f'Last RUN Date           :-> \033[32m{last_run_date}\033[0m')
    print(f'Config/INI File         :-> \033[32m{config_file}\033[0m')
    print(f'YAML Queries File       :-> \033[32m{pdw_sql_file}\033[0m')
    print(f'LOG File                :-> \033[32m{log_file_cfg}\033[0m ')
    print(f'Number of executions    :-> \033[32m{number_of_runs}\033[0m')
    print(f'Excel Sheet  Input file :-> \033[32m{input_file}\033[0m')
    print(f'Output SQLite3 Database :-> \033[32m{sqlite_database}\033[0m')
    print(f'Guiding Excel Sheet     :-> \033[32m{guiding_table}\033[0m')

    print(out_line)
    print("Personal Data Warehouse Processes are Starting | ET&L -> Extract, Transform & Loader !")

    if run_loader:
        print(out_line)
        if not multithread:
            new_data_loader(sqlite_database, types_of_entries, general_entries_table, origem_dados, guiding_table,
                        input_file, save_discarted_data, discarted_data_table)
        else:
            print(f'Bad, Bad Server. Not donuts for you')
            print(f'Threads are evil. Avoid them.')
            print('')
            print('https://www2.eecs.berkeley.edu/Pubs/TechRpts/2006/EECS-2006-1.pdf')
            print('')
            print(
                '    SQLite is threadsafe. We make this concession since many users choose to ignore the advice given in the previous paragraph. ')
            print(
                'But in order to be thread-safe, SQLite must be compiled with the SQLITE_THREADSAFE preprocessor macro set to 1.  ')
            print('Both the Windows and Linux precompiled binaries in the distribution are compiled this way.  ')
            print(
                'If you are unsure if the SQLite library you are linking against is compiled to be threadsafe you can call the sqlite3_threadsafe() interface to find out. ')
            print(' ')
            print('    SQLite is threadsafe because it uses mutexes to serialize access to common data structures.  ')
            print('However, the work of acquiring and releasing these mutexes will slow SQLite down slightly.  ')
            print(
                'Hence, if you do not need SQLite to be threadsafe, you should disable the mutexes for maximum performance.  ')
            print(
                'Under Unix, you should not carry an open SQLite database across a fork() system call into the child process. ')
            print('See the threading mode documentation for additional information. ')
            print(' ')
            exit(1)
            # data_loader_parallel(sqlite_database, types_of_entries, general_entries_table, guiding_table, input_file,
            #                         save_discarted_data, discarted_data_table)
    else:
        print("The execution of the Loaders was ommited ... .. .")

    if create_pivot:
        print(out_line)
        create_pivot_history(sqlite_database, types_of_entries, general_entries_table, full_hist_table,
                             anual_hist_table)
        if dinamic_reports:
            print(out_line)
            create_dinamic_reports(sqlite_database, input_file, din_report_guinding, full_hist_table)
    else:
        print("The Creation of the Pivot Tables was ommited ... .. .")

    if run_reports:

        print(out_line)
        monthly_summaries(sqlite_database, general_entries_table, monthly_summarie)

        print(out_line)
        general_entries_file_exportator(sqlite_database, dir_file_out, general_entries_table + '.FULL',
                                        general_entries_table, other_file_types)
        print(out_line)
        split_paymnt_resume(sqlite_database, split_paymnt_table, out_table)
        print(out_line)
        xlsx_report_generator(sqlite_database, dir_file_out, output_name, multi_rept_file, out_type,
                              general_entries_table, dinamic_reports, din_report_guinding, create_pivot,
                              anual_hist_table, full_hist_table, dayly_progress, out_table, monthly_summarie, pdw_sql_file)

    else:
        print("The Reports Creation ommited ... .. .")

    # if export_transeient_data:
    #     print(out_line)
    #     transient_data_exportator(sqlite_database, dir_file_out, out_type, transient_data_file, transient_data_table,
    #                               origem_dados)

    end = time.time()
    total_running_time: str = f"{end - start:7.2f}"
    log_line = started + ' Started |' + datetime.datetime.now().strftime(
        "%Y/%m/%d %H:%M:%S") + f' Ended | {total_running_time} TotalSecs | Version {current_version} | Hostname {hostname} | OS {os_pataform}' + '\n'

    finalize_log(log_file, log_line)

    print(out_line)
    print("All Personal Data Warehouse processes have ended! ")
    print(log_line[:-1])
    print(out_line)
    # exit(0)
