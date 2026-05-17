"""
reports.monthly_data — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from reports.monthly_data import monthly_summaries

    # Depois (>= 10.1.0)
    from pdw.analytics.totals import monthly_summaries
"""
import warnings

warnings.warn(
    "'reports.monthly_data' foi movido para 'pdw.analytics.totals' na versão 10.1.0. "
    "Atualize seu import para: from pdw.analytics.totals import monthly_summaries. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.analytics.totals import monthly_summaries

__all__ = ["monthly_summaries"]
