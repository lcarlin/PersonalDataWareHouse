"""
pdw.compat — Camada de Compatibilidade Retroativa
===================================================
Versão introduzida: 10.1.0
Remoção planejada:  11.0.0

Este módulo centraliza todos os aliases e re-exports que mantêm
compatibilidade com o código escrito para as versões anteriores ao PDW 10.1.0.

Mapa de migração de imports
----------------------------

Caminho legado (< 10.1.0)                       →  Novo caminho (>= 10.1.0)
-----------------------------------------------------------------------
database.drop_table.table_droppator             →  pdw.database.operations.table_droppator
etl.data_loader.data_loader                     →  pdw.etl.loader.new_data_loader
reports.general_exportator.general_entries_...  →  pdw.reports.exporter.general_entries_file_exportator
reports.monthly_data.monthly_summaries          →  pdw.analytics.totals.monthly_summaries
reports.split_paymnts.split_paymnt_resume       →  pdw.analytics.totals.split_paymnt_resume
reports.xlsx_reports.xlsx_report_generator      →  pdw.reports.xlsx_generator.xlsx_report_generator
reports.novos_relatorios.gerar_todos_...        →  pdw.reports.novos_relatorios.gerar_todos_relatorios_integrado
utils.compressor.gzip_compressor                →  pdw.utils.compression.gzip_compressor
utils.correjeitor.data_correjeitor              →  pdw.etl.sanitizer.data_correjeitor
utils.daily_totalizer.totalizador_diario        →  pdw.analytics.totals.totalizador_diario
utils.dinamic_reports.create_dinamic_reports    →  pdw.analytics.pivot.create_dinamic_reports
utils.pivot_tables.create_pivot_history         →  pdw.analytics.pivot.create_pivot_history
utils.transient_data.transient_data_exportator  →  pdw.utils.transient_data.transient_data_exportator
utils.xml_df.dataframe_to_xml                   →  pdw.utils.xml_utils.dataframe_to_xml
PersonalDataWareHouse.main                      →  pdw.main.main  (shim mantido em PersonalDataWareHouse.py)

Alias de nome de função
------------------------
data_loader   →  new_data_loader   (nome renomeado na v9.10.0→v10.1.0)
"""

import warnings

# ─── Infraestrutura de banco ────────────────────────────────────────────────
from pdw.database.operations import table_droppator, save_dataframe_to_database, sort_dataframe_by_date

# ─── ETL ────────────────────────────────────────────────────────────────────
from pdw.etl.loader import (
    new_data_loader,
    read_guiding_sheet,
    process_accounting_sheet,
    process_non_accounting_sheet,
)
# Alias de compatibilidade: data_loader era o nome antigo de new_data_loader
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

# ─── Ponto de entrada ───────────────────────────────────────────────────────
from pdw.main import main


def _deprecated_import_warning(old_path, new_path):
    warnings.warn(
        f"'{old_path}' foi movido para '{new_path}' na versão 10.1.0. "
        f"O caminho antigo será removido na versão 11.0.0.",
        DeprecationWarning,
        stacklevel=3,
    )


__all__ = [
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
    # Entry point
    "main",
]
