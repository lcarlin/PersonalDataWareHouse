"""
utils.compressor — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from utils.compressor import gzip_compressor

    # Depois (>= 10.1.0)
    from pdw.utils.compression import gzip_compressor
"""
import warnings

warnings.warn(
    "'utils.compressor' foi movido para 'pdw.utils.compression' na versão 10.1.0. "
    "Atualize seu import para: from pdw.utils.compression import gzip_compressor. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.utils.compression import gzip_compressor

__all__ = ["gzip_compressor"]
