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
#                       # Camada de compatibilidade retroativa         #
#############################################################################################
# Current Version : 10.1.0
#############################################################################################
# Facade de compatibilidade retroativa — PersonalDataWareHouse.py
#
# Este arquivo mantém todos os nomes públicos que existiam no monolito v9.x
# diretamente importáveis daqui, preservando os contratos:
#
#   from PersonalDataWareHouse import main
#   from PersonalDataWareHouse import new_data_loader
#   from PersonalDataWareHouse import data_loader        ← alias retroativo
#   from PersonalDataWareHouse import xlsx_report_generator
#   ... (todos os 25 nomes públicos + novos alias)
#
# Para invocar diretamente o pacote: python -m pdw [config_file]
####################################################################################
"""

import sys

# ─── Ponto de entrada ───────────────────────────────────────────────────────
from pdw.main import main

# ─── ETL ────────────────────────────────────────────────────────────────────
from pdw.etl.loader import (
    new_data_loader,
    read_guiding_sheet,
    process_accounting_sheet,
    process_non_accounting_sheet,
)

# Alias retroativo: data_loader era o nome público antes da v9.10.0
data_loader = new_data_loader

# ─── Transformação / sanitização ────────────────────────────────────────────
from pdw.etl.sanitizer import (
    data_correjeitor,
    sanitize_entries_dataframe,
    add_temporal_columns,
    enrich_dataframe_with_dates,
    sanitize_financial_columns,
    clean_description_text,
)

# ─── Infraestrutura de banco ────────────────────────────────────────────────
from pdw.database.operations import (
    table_droppator,
    save_dataframe_to_database,
    sort_dataframe_by_date,
)

# ─── Analytics ──────────────────────────────────────────────────────────────
from pdw.analytics.pivot import create_pivot_history, create_dinamic_reports
from pdw.analytics.totals import totalizador_diario, monthly_summaries, split_paymnt_resume

# ─── Relatórios ─────────────────────────────────────────────────────────────
from pdw.reports.exporter import general_entries_file_exportator
from pdw.reports.xlsx_generator import xlsx_report_generator
from pdw.reports.novos_relatorios import gerar_todos_relatorios_integrado

# ─── Utilitários ────────────────────────────────────────────────────────────
from pdw.utils.compression import gzip_compressor
from pdw.utils.xml_utils import dataframe_to_xml
from pdw.utils.transient_data import transient_data_exportator
from pdw.utils.localization import get_month_names, get_weekday_names


__all__ = [
    # Ponto de entrada
    "main",
    # ETL
    "new_data_loader", "data_loader",
    "read_guiding_sheet", "process_accounting_sheet", "process_non_accounting_sheet",
    # Transform
    "data_correjeitor", "sanitize_entries_dataframe", "add_temporal_columns",
    "enrich_dataframe_with_dates", "sanitize_financial_columns", "clean_description_text",
    # Database
    "table_droppator", "save_dataframe_to_database", "sort_dataframe_by_date",
    # Analytics
    "create_pivot_history", "create_dinamic_reports",
    "totalizador_diario", "monthly_summaries", "split_paymnt_resume",
    # Reports
    "general_entries_file_exportator", "xlsx_report_generator", "gerar_todos_relatorios_integrado",
    # Utils
    "gzip_compressor", "dataframe_to_xml", "transient_data_exportator",
    "get_month_names", "get_weekday_names",
]


if __name__ == '__main__':
    input_param_file = ""

    if len(sys.argv) == 2:
        input_param_file = sys.argv[1]

    main(input_param_file)

# EOP
