"""
reports.novos_relatorios — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Requerimentos opcionais: matplotlib, seaborn, scipy, fpdf2

Migração recomendada:
    # Antes (< 10.1.0)
    from reports.novos_relatorios import gerar_todos_relatorios_integrado

    # Depois (>= 10.1.0)
    from pdw.reports.novos_relatorios import gerar_todos_relatorios_integrado
"""
import warnings

warnings.warn(
    "'reports.novos_relatorios' foi movido para 'pdw.reports.novos_relatorios' na versão 10.1.0. "
    "Atualize seu import para: from pdw.reports.novos_relatorios import gerar_todos_relatorios_integrado. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.reports.novos_relatorios import gerar_todos_relatorios_integrado

__all__ = ["gerar_todos_relatorios_integrado"]
