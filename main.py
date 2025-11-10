"""
####################################################################################
# Author  : Carlin, Luiz A. .'.
# e-mail  : luiz.carlin@gmail.com
# Date    : 13-DEC-2022
# purpose : Import Sheets from Excel Workbook into SQLite3 Tables
#           ET&L -> Extract, Transform & Loader
####################################################################################
# Version control
# Date       # Version #    What                            #   Who
# 2022-12-26 # 8       # Merge With Version 6.1 and 7       # Carlin, Luiz A. .'.
# 2023-04-12 # 9.0.4   # Export date in several formats in  #
#                      # LANCAMENTOS_GERAIS                 # Carlin, Luiz A. .'.
# 2023-04-20 # 9.1.0   # Run dinamic reports based on anual #
#                      # info                               # Carlin, Luiz A. .'.
# 2023-08-23 # 9.1.5   # create Index Main table            # Carlin, Luiz A. .'.
#                      # Do not create intermediate tables  #
#                      #  Anymore for Accounting Sheets     #
#                      # Now the export function            #
#                      #   Just Export data                 #
#                      # New Columns on the main Table      #
# 2023-10-05 # 9.2.0   # Export Transient data from API Tab.# Carlin, Luiz A. .'.
# 2023-12-20 # 9.3.0   # Data Validator: verify if tehe is  # Carlin, Luiz A. .'.
#                      #  Any invalid data on main fields   #
# 2024-04-03 # 9.3.2   # remove INPLACE NPN MAN             # Carlin, Luiz A. .'.
#                      # CHANGES Encoding from ansi CP1252  #
# 2024-04-04 # 9.3.2   # files "MesAno" changed to AnoMEs   # Carlin, Luiz A. .'.
# 2024-05-28 # 9.4.0   # Pivot Table Improvment             # Carlin, Luiz A. .'.
# 2024-08-08 # 9.4.4   # TimeStamp and Separator on LOG     # Carlin, Luiz A. .'.
# 2024-09-02 # 9.5.0   # totaling daily amount of data In   # Carlin, Luiz A. .'.
#                      # General Reports                    #
# 2024-10-03 # 9.6.0   # payment in installments summary    # Carlin, Luiz A. .'.
# 2024-10-22 # 9.6.1   # New Pivot Tables with COUNT of     # Carlin, Luiz A. .'.
#                      # totals                             # Carlin, Luiz A. .'.
# 2024-11-06 # 9.7.0   # Generating summaries of all        # Carlin, Luiz A. .'.
#                      #   accounting tables                #
# 2024-12-09 # 9.7.0   # Genenal Entries Resumes (Y/M)      # Carlin, Luiz A. .'.
# 2025-01-20 # 9.8.0   # Optimizing Data Loader funciont    # Carlin, Luiz A. .'.
# 2025-09-25 # 9.8.1   # put Round at data loader           # Carlin, Luiz A. .'.
# 2025-09-25 # 9.9.0   # Improvements on Dataframe Sanity   # Carlin, Luiz A. .'.
# 2025-09-30 # 10.0.0  # dividir as funções em arquivos exte# Carlin, Luiz A. .'.
####################################################################################
# Current Version : 9.9.0
####################################################################################
# TODO: GUI Interface
# TODO: Use config file as parameters? (done)
# TODO: read encrypted excel file ?
# TODO: Write encrypted Excel file ?
# TODO: Remove parallel items ?
# TODO: be able to use another databases ?
# TODO: Refactor code to be able to use another types od database
# TODO: Version Number in main module (done)
# TODO: Hostname + version in log (done)
# TODO: Put HistoricoGeral table name in Parameter file (done)
# TODO: Put HistoricoAnual table name in Parameter file (done)
# TODO: Create saparated output directories (log, report and database) (done)
# TODO: Transiet data writer/export (done)
# TODO:
# TODO:
# TODO:
####################################################################################
Dependencies:
pip install pandas
pip install xlsxwriter
pip install xlrd
pip install openpyxl
pip install sqlalchemy
pip install numpy
pip install pyinstaller

pip install lxml
pip install tabulate
pip install tables0
pyinstaller -F -i "G:\\Meu Drive\\PDW\\DataWareHouse02.ico" .\\XL_importer.v9.py

"""

import datetime
import configparser
import os, platform, sys
import time
import xml.etree.ElementTree as ET
from etl import data_loader as dl
from utils.pivot_tables import create_pivot_history
from utils.dinamic_reports import create_dinamic_reports
from reports.monthly_data import monthly_summaries
from reports.general_exportator import general_entries_file_exportator
from reports.split_paymnts import split_paymnt_resume
from reports.xlsx_reports import xlsx_report_generator
from reports.novos_relatorios import gerar_todos_relatorios_integrado

def main(param_file):
    # Environment / Variables
    # current date and time
    start = time.time()
    started = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    current_version = "10.0.0"
    os_pataform = platform.system()

    # if the system is windows then use the below
    # command to check for the hostname
    if os_pataform == "Windows":
        hostname = platform.uname().node
    else:
        # otherwise use the below command
        hostname = os.uname()[1]

    config = configparser.ConfigParser()
    config_file = 'PersonalDataWareHouse.cfg'

    if len(param_file) > 0:
        config_file = param_file

    try:
        print('Reading configuration file ... .. .')
        with open(config_file) as cfg:
            config.read_file(cfg)

        parameters_version = config['SETTINGS']['CURRENT_VERSION']
        if parameters_version != current_version:
            print(f'The version in parameter file {config_file} does not Match')
            print(f'Informed :-> {parameters_version}')
            print(f'Expected :-> {current_version}')
            exit(1)

        dir_file_in = config['DIRECTORIES']['DIR_IN']
        dir_file_out = config['DIRECTORIES']['DIR_OUT']
        dir_log = config['DIRECTORIES']['LOG_DIR']
        dir_db = config['DIRECTORIES']['DATABASE_DIR']

        out_type = config['FILE_TYPES']['TYPE_OUT']
        out_db = config['FILE_TYPES']['OUT_DB_FILE']
        output_name = config['FILE_TYPES']['OUT_RPT_FILE']
        db_file_type = config['FILE_TYPES']['DB_FILE_TYPE']
        log_file_cfg = dir_log + config['FILE_TYPES']['LOG_FILE']

        splitter = config.getint('SETTINGS', 'PARALLELS')
        multithread = config.getboolean('SETTINGS', 'MULTITHREADING')
        overwrite_db = config.getboolean('SETTINGS', 'OVERWRITE_DB')
        run_loader = config.getboolean('SETTINGS', 'RUN_DATA_LOADER')
        run_reports = config.getboolean('SETTINGS', 'RUN_REPORTS')
        multi_rept_file = config.getboolean('SETTINGS', 'RPT_SINGLE_FILE')
        guiding_table = config['SETTINGS']['GUIDING_TABLE']
        types_of_entries = config['SETTINGS']['TYPES_OF_ENTRIES']
        general_entries_table = config['SETTINGS']['GENERAL_ENTRIES_TABLE']
        create_pivot = config.getboolean('SETTINGS', 'CREATE_PIVOT')
        save_discarted_data = config.getboolean('SETTINGS', 'SAVE_DISCARTED_DATA')
        discarted_data_table = config['SETTINGS']['DISCARTED_DATA_TABLE']
        full_hist_table = config['SETTINGS']['FULL_PIVOT_TABLE']
        anual_hist_table = config['SETTINGS']['ANUAL_PIVOT_TABLE']
        export_transeient_data = config.getboolean('SETTINGS','EXPORT_TRANSIENT_DATA')
        transient_data_table = config['SETTINGS']['TRANSIENT_DATA_TABLE']
        transient_data_file = config['FILE_TYPES']['TRANSIENT_DATA_FILE']
        origem_dados = config['SETTINGS']['TRANSIENT_DATA_COLUMN']
        other_file_types = config.getboolean('SETTINGS', 'EXPORT_OTHER_TYPES')
        new_reports = config.getboolean('SETTINGS', 'NEW_REPORTS')

        dinamic_reports = config.getboolean('SETTINGS', 'RUN_DINAMIC_REPORT')
        din_report_guinding = config['SETTINGS']['DIN_REPORT_GUIDING']
        dayly_progress = config['SETTINGS']['DAYLY_PROGRESS']

        split_paymnt_table = config['SETTINGS']['SPLT_PAYMNT_TAB']
        out_table = config['SETTINGS']['OUT_RES_PMNT_TAB']
        monthly_summarie = config['SETTINGS']['MONTHLY_SUMMATIES']
        in_file_name = config['FILES']['IN_FILE_NAME']


    except FileNotFoundError:
        print(f"Configuration file {config_file} not found !")
        exit(1)
    except configparser.Error as e:
        print(e)
        exit(1)
    except Exception as e:
        print(e)
        exit(1)

    input_file = dir_file_in + in_file_name
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

    # begin of log block
    last_run_date = 'none'
    log_file_exists = os.path.isfile(log_file_cfg)
    is_log_empty = False
    if log_file_exists:
        is_log_empty = os.stat(log_file_cfg).st_size == 0
        if is_log_empty:
            print(f'Log File {log_file_cfg} is Empty ')
    else:
        print(f'Log File {log_file_cfg} does Not Exists yet ')
        new_log_file = open(log_file_cfg, 'w')
        new_log_file.write('New LOG created at :-> ' + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n')
        new_log_file.close()

    log_file = open(log_file_cfg, 'r+')
    if not is_log_empty and log_file_exists:
        last_run_date = log_file.readlines()[-1].split('|')[0]
    # end of LOG block
    out_line = ">" + ("=" * 130) + "<"
    print(out_line)
    print(f'Current Version         :-> {current_version}')
    print(f'Last RUN Date           :-> {last_run_date}')
    print(f'Config/INI File         :-> {config_file}')
    print(f'LOG File                :-> {log_file_cfg} ')
    print(f'Excel Sheet  Input file :-> {input_file}')
    print(f'Output SQLite3 Database :-> {sqlite_database}')
    print(f'Guiding Excel Sheet     :-> {guiding_table}')
    print(out_line)
    print("Personal Data Warehouse Processes are Starting | ET&L -> Extract, Transform & Loader !")

    if run_loader:
        print(out_line)
        if not multithread:
            dl.data_loader(sqlite_database, types_of_entries, general_entries_table, origem_dados, guiding_table,
                        input_file,
                        save_discarted_data, discarted_data_table)
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

    if create_pivot:
        print(out_line)
        create_pivot_history(sqlite_database, types_of_entries, general_entries_table, full_hist_table,
                             anual_hist_table)
        if dinamic_reports:
            print(out_line)
            create_dinamic_reports(sqlite_database, input_file, din_report_guinding, full_hist_table)

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
                              anual_hist_table, full_hist_table, dayly_progress, out_table, monthly_summarie)
        if new_reports:
            gerar_todos_relatorios_integrado(sqlite_database, general_entries_table,dir_file_out)

    if export_transeient_data:
        print(out_line)
        print('transient_data_exportator')
        #transient_data_exportator(sqlite_database, dir_file_out, out_type, transient_data_file, transient_data_table,
        #                          origem_dados)

    end = time.time()
    total_running_time: str = f"{end - start:7.2f}"
    log_line = started + ' Started |' + datetime.datetime.now().strftime(
        "%Y/%m/%d %H:%M:%S") + f' Ended | {total_running_time} TotalSecs | Version {current_version} | Hostname {hostname} | OS {os_pataform}' + '\n'
    log_file.write(log_line)
    log_file.close()

    print(out_line)
    print("All Personal Data Warehouse processes have ended! ")
    print(log_line[:-1])
    print(out_line)
    # exit(0)

if __name__ == '__main__':
    input_param_file = ""

    if len(sys.argv) == 2:
        input_param_file = sys.argv[1]

    main(input_param_file)

# EOP