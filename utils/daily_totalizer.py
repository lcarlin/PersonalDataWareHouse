"""
utils.daily_totalizer — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from utils.daily_totalizer import totalizador_diario

    # Depois (>= 10.1.0)
    from pdw.analytics.totals import totalizador_diario
"""
import warnings

warnings.warn(
    "'utils.daily_totalizer' foi movido para 'pdw.analytics.totals' na versão 10.1.0. "
    "Atualize seu import para: from pdw.analytics.totals import totalizador_diario. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.analytics.totals import totalizador_diario

__all__ = ["totalizador_diario"]
