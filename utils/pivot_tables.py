"""
utils.pivot_tables — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from utils.pivot_tables import create_pivot_history

    # Depois (>= 10.1.0)
    from pdw.analytics.pivot import create_pivot_history
"""
import warnings

warnings.warn(
    "'utils.pivot_tables' foi movido para 'pdw.analytics.pivot' na versão 10.1.0. "
    "Atualize seu import para: from pdw.analytics.pivot import create_pivot_history. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.analytics.pivot import create_pivot_history

__all__ = ["create_pivot_history"]
