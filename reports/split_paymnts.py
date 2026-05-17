"""
reports.split_paymnts — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from reports.split_paymnts import split_paymnt_resume

    # Depois (>= 10.1.0)
    from pdw.analytics.totals import split_paymnt_resume
"""
import warnings

warnings.warn(
    "'reports.split_paymnts' foi movido para 'pdw.analytics.totals' na versão 10.1.0. "
    "Atualize seu import para: from pdw.analytics.totals import split_paymnt_resume. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.analytics.totals import split_paymnt_resume

__all__ = ["split_paymnt_resume"]
