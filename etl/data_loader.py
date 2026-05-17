"""
etl.data_loader — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Observação: a função 'data_loader' foi renomeada para 'new_data_loader'
na refatoração interna da v9.10.0 e mantida como alias neste stub.

Migração recomendada:
    # Antes (< 10.1.0)
    from etl.data_loader import data_loader
    from etl import data_loader as dl; dl.data_loader(...)

    # Depois (>= 10.1.0)
    from pdw.etl.loader import new_data_loader
"""
import warnings

warnings.warn(
    "'etl.data_loader' foi movido para 'pdw.etl.loader' na versão 10.1.0. "
    "A função 'data_loader' está disponível como alias de 'new_data_loader'. "
    "Atualize seu import para: from pdw.etl.loader import new_data_loader. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.etl.loader import (
    new_data_loader,
    read_guiding_sheet,
    process_accounting_sheet,
    process_non_accounting_sheet,
)

# Alias retroativo: data_loader era o nome público antes da v9.10.0
data_loader = new_data_loader

__all__ = [
    "data_loader",
    "new_data_loader",
    "read_guiding_sheet",
    "process_accounting_sheet",
    "process_non_accounting_sheet",
]
