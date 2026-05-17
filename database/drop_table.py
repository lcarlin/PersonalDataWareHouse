"""
database.drop_table — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from database.drop_table import table_droppator

    # Depois (>= 10.1.0)
    from pdw.database.operations import table_droppator
"""
import warnings

warnings.warn(
    "'database.drop_table' foi movido para 'pdw.database.operations' na versão 10.1.0. "
    "Atualize seu import para: from pdw.database.operations import table_droppator. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.database.operations import table_droppator

__all__ = ["table_droppator"]
