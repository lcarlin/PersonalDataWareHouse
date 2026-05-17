"""
utils.transient_data — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from utils.transient_data import transient_data_exportator

    # Depois (>= 10.1.0)
    from pdw.utils.transient_data import transient_data_exportator
"""
import warnings

warnings.warn(
    "'utils.transient_data' foi movido para 'pdw.utils.transient_data' na versão 10.1.0. "
    "Atualize seu import para: from pdw.utils.transient_data import transient_data_exportator. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.utils.transient_data import transient_data_exportator

__all__ = ["transient_data_exportator"]
