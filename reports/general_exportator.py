"""
reports.general_exportator — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from reports.general_exportator import general_entries_file_exportator

    # Depois (>= 10.1.0)
    from pdw.reports.exporter import general_entries_file_exportator
"""
import warnings

warnings.warn(
    "'reports.general_exportator' foi movido para 'pdw.reports.exporter' na versão 10.1.0. "
    "Atualize seu import para: from pdw.reports.exporter import general_entries_file_exportator. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.reports.exporter import general_entries_file_exportator

__all__ = ["general_entries_file_exportator"]
