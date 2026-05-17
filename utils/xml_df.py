"""
utils.xml_df — módulo legado (PDW < 10.1.0).
Remoção planejada: PDW 11.0.0.

Migração recomendada:
    # Antes (< 10.1.0)
    from utils.xml_df import dataframe_to_xml

    # Depois (>= 10.1.0)
    from pdw.utils.xml_utils import dataframe_to_xml
"""
import warnings

warnings.warn(
    "'utils.xml_df' foi movido para 'pdw.utils.xml_utils' na versão 10.1.0. "
    "Atualize seu import para: from pdw.utils.xml_utils import dataframe_to_xml. "
    "Este módulo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

from pdw.utils.xml_utils import dataframe_to_xml

__all__ = ["dataframe_to_xml"]
