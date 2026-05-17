"""
reports.xlsx_reports — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from reports.xlsx_reports import xlsx_report_generator

    # Depois (>= 10.1.0)
    from pdw.reports.xlsx_generator import xlsx_report_generator
"""
import warnings

warnings.warn(
    "'reports.xlsx_reports' foi movido para 'pdw.reports.xlsx_generator' na versão 10.1.0. "
    "Atualize seu import para: from pdw.reports.xlsx_generator import xlsx_report_generator. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.reports.xlsx_generator import xlsx_report_generator

__all__ = ["xlsx_report_generator"]
