"""
Ponto de entrada legado — compatibilidade retroativa com PDW < 10.1.0.
Remoção planejada: PDW 11.0.0.
Use PersonalDataWareHouse.py ou `python -m pdw` a partir da versão 10.1.0.
"""
import warnings
import sys

warnings.warn(
    "Invocar 'main.py' diretamente está obsoleto desde PDW 10.1.0. "
    "Use 'PersonalDataWareHouse.py' ou 'python -m pdw [config]'. "
    "Este arquivo será removido na versão 11.0.0.",
    DeprecationWarning,
    stacklevel=1,
)

from pdw.main import main

if __name__ == '__main__':
    input_param_file = ""
    if len(sys.argv) == 2:
        input_param_file = sys.argv[1]
    main(input_param_file)
