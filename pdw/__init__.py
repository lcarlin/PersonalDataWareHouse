"""
#############################################################################################
# Author  : Carlin, Luiz A. .'.
# e-mail  : luiz.carlin@gmail.com
# Date    : 13-DEC-2022
# purpose : Import Sheets from Excel Workbook into SQLite3 Tables
#           ET&L -> Extract, Transform & Loader
#############################################################################################
# Version control
# Date       #  Version #    What                                      #   Who
# 2022-12-26 #  8       # Merge With Version 6.1 and 7                 # Carlin, Luiz A. .'.
# 2023-04-12 #  9.0.4   # Export date in several formats in            #
#                       # LANCAMENTOS_GERAIS                           # Carlin, Luiz A. .'.
# 2023-04-20 #  9.1.0   # Run dinamic reports based on anual           #
#                       # info                                         # Carlin, Luiz A. .'.
# 2023-08-23 #  9.1.5   # create Index Main table                      # Carlin, Luiz A. .'.
#                       # Do not create intermediate tables            #
#                       #  Anymore for Accounting Sheets               #
#                       # Now the export function                      #
#                       #   Just Export data                           #
#                       # New Columns on the main Table                #
# 2023-10-05 #  9.2.0   # Export Transient data from API Tab           # Carlin, Luiz A. .'.
# 2023-12-20 #  9.3.0   # Data Validator: verify if tehe is            # Carlin, Luiz A. .'.
#                       #  Any invalid data on main fields             #
# 2024-04-03 #  9.3.2   # remove INPLACE NPN MAN                       # Carlin, Luiz A. .'.
#                       # CHANGES Encoding from ansi CP1252            #
# 2024-04-04 #  9.3.2   # files "MesAno" changed to AnoMEs             # Carlin, Luiz A. .'.
# 2024-05-28 #  9.4.0   # Pivot Table Improvment                       # Carlin, Luiz A. .'.
# 2024-08-08 #  9.4.4   # TimeStamp and Separator on LOG               # Carlin, Luiz A. .'.
# 2024-09-02 #  9.5.0   # totaling daily amount of data In             # Carlin, Luiz A. .'.
#                       # General Reports                              #
# 2024-10-03 #  9.6.0   # payment in installments summary              # Carlin, Luiz A. .'.
# 2024-10-22 #  9.6.1   # New Pivot Tables with COUNT of               # Carlin, Luiz A. .'.
#                       # totals                                       # Carlin, Luiz A. .'.
# 2024-11-06 #  9.7.0   # Generating summaries of all                  # Carlin, Luiz A. .'.
#                       #   accounting tables                          #
# 2024-12-09 #  9.7.0   # Genenal Entries Resumes (Y/M)                # Carlin, Luiz A. .'.
# 2025-01-20 #  9.8.0   # Optimizing Data Loader funciont              # Carlin, Luiz A. .'.
# 2025-09-25 #  9.8.1   # put Round at data loader                     # Carlin, Luiz A. .'.
# 2025-09-25 #  9.9.0   # Improvements on Dataframe Sanity             # Carlin, Luiz A. .'.
# 2025-11-26 #  9.10.0  # ReFactoring of Data_loader function          # Carlin, Luiz A. .'.
# 2025-11-28 #  9.11.1  # Refactoring od XLSREPORT with YAML file      # Carlin, Luiz A. .'.
# 2026-01-22 #  9.11.1  # Encodindig utf-8-sig on csv exporting        # Carlin, Luiz A. .'.
#                       # remove  "  from descrição field              #
# 2026-02-10 #  9.11.2  # Cosmetics: number of executions              # Carlin, Luiz A. .'.
# 2026-05-17 # 10.1.0   # Modularização arquitetural incremental        # Carlin, Luiz A. .'.
#                       # Separação em pacote pdw/ por competência     #
#############################################################################################
# Current Version : 10.1.0
#############################################################################################
# TODO: GUI Interface
# TODO: Use config file as parameters? (done)
# TODO: read encrypted excel file ?
# TODO: Write encrypted Excel file ?
# TODO: Remove parallel items (Done)
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

__version__ = "10.1.0"
