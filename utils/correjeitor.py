"""
utils.correjeitor — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from utils.correjeitor import data_correjeitor

    # Depois (>= 10.1.0)
    from pdw.etl.sanitizer import data_correjeitor
"""
import warnings

warnings.warn(
    "'utils.correjeitor' foi movido para 'pdw.etl.sanitizer' na versão 10.1.0. "
    "Atualize seu import para: from pdw.etl.sanitizer import data_correjeitor. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.etl.sanitizer import data_correjeitor
from pdw.database.operations import table_droppator

__all__ = ["data_correjeitor", "table_droppator"]
