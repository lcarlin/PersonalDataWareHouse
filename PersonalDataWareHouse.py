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

import sqlite3
import pandas as pd
import datetime
import numpy as np
import configparser
import os, platform, sys
import threading
import time
import xml.etree.ElementTree as ET
import gzip
import shutil



def parallel_df(db_file, xls_file, config_dict, general_out_table, index):
    db_connection = sqlite3.connect(db_file)
    tmp_table_name = config_dict['table_to_load']
    print(f'   . .. ... .... Begin of Thread Number :-> {index}  ; Table/Sheet Name :-> {tmp_table_name} ')
    data_frame = pd.read_excel(xls_file, sheet_name=config_dict['table_to_load'])
    if 'X' == config_dict['isAccounting'] and 'X' == config_dict['isCleanable']:
        # delete records with null 'TIPO'
        data_frame['TIPO'].replace('', np.nan, inplace=True)
        data_frame.dropna(subset=['TIPO'], inplace=True)
        # delete records with null DATA column
        data_frame['Data'].replace('', np.nan, inplace=True)
        data_frame.dropna(subset=['Data'], inplace=True)
        general_entries_df = data_frame[["Data", "TIPO", "DESCRICAO", "Credito", "Debito"]].copy()
        general_entries_df.insert(1, 'DIA_SEMANA', np.nan)
        general_entries_df['Mes'] = 'MM'
        general_entries_df['Ano'] = 'YYYY'
        general_entries_df['AnoMes'] = 'YYYY/MM'
        general_entries_df['Origem'] = config_dict['table_to_load']
        # Ja joga os dados limpos na lançamentos gerais
        general_entries_df.to_sql(general_out_table, db_connection, index=False, if_exists="append")

    # grava a tabela (UNITÁRIA) do data_frame do BD
    data_frame.to_sql(config_dict['table_to_load'], db_connection, index=False, if_exists="replace")
    db_connection.commit()
    db_connection.close()
    print(f'   . .. ... .... End of Thread Number :-> {index}  ; Table/Sheet Name :-> {tmp_table_name} ')


