"""
utils.dinamic_reports — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from utils.dinamic_reports import create_dinamic_reports

    # Depois (>= 10.1.0)
    from pdw.analytics.pivot import create_dinamic_reports
"""
import warnings

warnings.warn(
    "'utils.dinamic_reports' foi movido para 'pdw.analytics.pivot' na versão 10.1.0. "
    "Atualize seu import para: from pdw.analytics.pivot import create_dinamic_reports. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.analytics.pivot import create_dinamic_reports

__all__ = ["create_dinamic_reports"]
