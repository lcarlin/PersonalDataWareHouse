# COMPATIBILITY_GUIDE.md
## Personal Data Warehouse — Guia de Compatibilidade Retroativa
### Versão 9.x → 10.1.0

---

## Visão Geral

A versão 10.1.0 realizou uma modularização arquitetural completa do monolito `PersonalDataWareHouse.py`.
Para garantir que código existente continue funcionando **sem nenhuma alteração**, três camadas de compatibilidade foram implementadas:

| Camada | Descrição | Remoção Planejada |
|---|---|---|
| **Facade** | `PersonalDataWareHouse.py` re-exporta todos os 25 nomes públicos | Nunca (arquivo principal) |
| **Stubs legados** | Módulos `database/`, `etl/`, `reports/`, `utils/` redirecionam para `pdw/` | PDW 11.0.0 |
| **pdw.compat** | Módulo centralizado com todos os aliases | PDW 11.0.0 |

---

## Cenários de Compatibilidade

---

### Cenário 1 — Execução via CLI (RunPDW.sh, RunPDW.ps1, Run_PDW.bat)

**Status: Totalmente compatível. Nenhuma alteração necessária.**

```bash
# Funciona exatamente como antes
python PersonalDataWareHouse.py
python PersonalDataWareHouse.py /path/to/custom.cfg

# Novo modo alternativo (a partir de 10.1.0)
python -m pdw
python -m pdw /path/to/custom.cfg
```

Os scripts `RunPDW.sh`, `RunPDW.ps1` e `Run_PDW.bat` **não precisam de alteração**.

---

### Cenário 2 — Import do módulo principal (from PersonalDataWareHouse import X)

**Status: Totalmente compatível. Nenhuma alteração necessária.**

```python
# Todos estes imports continuam funcionando em 10.1.0:
from PersonalDataWareHouse import main
from PersonalDataWareHouse import new_data_loader
from PersonalDataWareHouse import data_loader           # alias retroativo
from PersonalDataWareHouse import xlsx_report_generator
from PersonalDataWareHouse import create_pivot_history
from PersonalDataWareHouse import general_entries_file_exportator
from PersonalDataWareHouse import monthly_summaries
from PersonalDataWareHouse import split_paymnt_resume
from PersonalDataWareHouse import create_dinamic_reports
from PersonalDataWareHouse import totalizador_diario
from PersonalDataWareHouse import table_droppator
from PersonalDataWareHouse import gzip_compressor
from PersonalDataWareHouse import dataframe_to_xml
from PersonalDataWareHouse import data_correjeitor
from PersonalDataWareHouse import transient_data_exportator
from PersonalDataWareHouse import gerar_todos_relatorios_integrado
from PersonalDataWareHouse import get_month_names
from PersonalDataWareHouse import get_weekday_names
from PersonalDataWareHouse import sanitize_entries_dataframe
from PersonalDataWareHouse import save_dataframe_to_database
from PersonalDataWareHouse import sort_dataframe_by_date
```

---

### Cenário 3 — Imports pelos caminhos dos módulos legados (< 10.1.0)

**Status: Compatível com `DeprecationWarning`. Funcionam, mas emitem aviso de depreciação.**

```python
# Caminho legado → ainda funciona, emite DeprecationWarning
from database.drop_table import table_droppator
from etl.data_loader import data_loader
from etl.data_loader import new_data_loader
from reports.general_exportator import general_entries_file_exportator
from reports.monthly_data import monthly_summaries
from reports.split_paymnts import split_paymnt_resume
from reports.xlsx_reports import xlsx_report_generator
from reports.novos_relatorios import gerar_todos_relatorios_integrado
from utils.compressor import gzip_compressor
from utils.correjeitor import data_correjeitor
from utils.daily_totalizer import totalizador_diario
from utils.dinamic_reports import create_dinamic_reports
from utils.pivot_tables import create_pivot_history
from utils.transient_data import transient_data_exportator
from utils.xml_df import dataframe_to_xml
```

Para suprimir os avisos durante uma transição gradual:
```python
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from utils.compressor import gzip_compressor
```

---

### Cenário 4 — Import via old main.py

**Status: Compatível com `DeprecationWarning`.**

```python
# Ainda funciona, emite aviso
import main
main.main("/path/to/config.cfg")
```

---

### Cenário 5 — Uso via pdw.compat (novo)

**Status: Novo. Para código que quer importar pelo nome sem especificar o módulo.**

```python
from pdw.compat import new_data_loader, create_pivot_history, monthly_summaries
# Todos os 25 nomes públicos + alias data_loader disponíveis
```

---

## Mapa Completo de Migração de Imports

| Import antigo (< 10.1.0) | Import novo (>= 10.1.0) |
|---|---|
| `from database.drop_table import table_droppator` | `from pdw.database.operations import table_droppator` |
| `from etl.data_loader import data_loader` | `from pdw.etl.loader import new_data_loader` |
| `from etl.data_loader import new_data_loader` | `from pdw.etl.loader import new_data_loader` |
| `from etl.data_loader import read_guiding_sheet` | `from pdw.etl.loader import read_guiding_sheet` |
| `from etl.data_loader import process_accounting_sheet` | `from pdw.etl.loader import process_accounting_sheet` |
| `from etl.data_loader import process_non_accounting_sheet` | `from pdw.etl.loader import process_non_accounting_sheet` |
| `from reports.general_exportator import general_entries_file_exportator` | `from pdw.reports.exporter import general_entries_file_exportator` |
| `from reports.monthly_data import monthly_summaries` | `from pdw.analytics.totals import monthly_summaries` |
| `from reports.split_paymnts import split_paymnt_resume` | `from pdw.analytics.totals import split_paymnt_resume` |
| `from reports.xlsx_reports import xlsx_report_generator` | `from pdw.reports.xlsx_generator import xlsx_report_generator` |
| `from reports.novos_relatorios import gerar_todos_relatorios_integrado` | `from pdw.reports.novos_relatorios import gerar_todos_relatorios_integrado` |
| `from utils.compressor import gzip_compressor` | `from pdw.utils.compression import gzip_compressor` |
| `from utils.correjeitor import data_correjeitor` | `from pdw.etl.sanitizer import data_correjeitor` |
| `from utils.daily_totalizer import totalizador_diario` | `from pdw.analytics.totals import totalizador_diario` |
| `from utils.dinamic_reports import create_dinamic_reports` | `from pdw.analytics.pivot import create_dinamic_reports` |
| `from utils.pivot_tables import create_pivot_history` | `from pdw.analytics.pivot import create_pivot_history` |
| `from utils.transient_data import transient_data_exportator` | `from pdw.utils.transient_data import transient_data_exportator` |
| `from utils.xml_df import dataframe_to_xml` | `from pdw.utils.xml_utils import dataframe_to_xml` |
| `from PersonalDataWareHouse import main` | `from pdw.main import main` |

---

## Alias de Nome de Função

| Nome antigo | Nome novo | Observação |
|---|---|---|
| `data_loader` | `new_data_loader` | Renomeado na v9.10.0; alias mantido indefinidamente em `PersonalDataWareHouse.py` e `pdw.compat` |

---

## Comportamento de `DeprecationWarning`

Os stubs legados emitem `DeprecationWarning` no momento do import, apontando para o arquivo do código que fez o import (não o stub em si, graças a `stacklevel=2`).

**Formato da mensagem:**
```
DeprecationWarning: 'utils.compressor' foi movido para 'pdw.utils.compression' na versão 10.1.0.
Atualize seu import para: from pdw.utils.compression import gzip_compressor.
Este módulo será removido na versão 11.0.0.
```

Para **ver** os avisos (padrão Python — DeprecationWarning só aparece em modo desenvolvimento):
```bash
python -W all PersonalDataWareHouse.py
python -W error::DeprecationWarning PersonalDataWareHouse.py   # trata como erro
```

---

## Funcionalidade Restaurada: `transient_data_exportator`

A função `transient_data_exportator` estava comentada em `main()` desde a v9.x mas **a implementação foi preservada**.
Na v10.1.0, a função foi migrada para `pdw.utils.transient_data` com a correção do bug de `import datetime` ausente.

```python
# Disponível em:
from pdw.utils.transient_data import transient_data_exportator
from PersonalDataWareHouse import transient_data_exportator  # via facade
from utils.transient_data import transient_data_exportator   # via stub legado (com aviso)
```

---

## Funcionalidade com Dependências Opcionais: `gerar_todos_relatorios_integrado`

Esta função requer `matplotlib`, `seaborn`, `scipy` e `fpdf2`.
Se não instalados, a importação funciona mas a **chamada** levanta `ImportError` com mensagem clara.

```bash
pip install matplotlib seaborn scipy fpdf2   # instala dependências opcionais
```

---

## Cronograma de Depreciação

| Versão | Ação |
|---|---|
| **10.1.0** (atual) | Stubs legados emitem `DeprecationWarning`. Todo código existente funciona. |
| **10.x.0** (futuro) | Stubs legados emitem `FutureWarning` (mais visível). |
| **11.0.0** (futuro) | Stubs legados removidos. Imports antigos falharão com `ModuleNotFoundError`. |

**Prazo estimado para 11.0.0**: não definido. Comunicação com 6 meses de antecedência.

---

## Verificação Rápida de Compatibilidade

Execute o seguinte para verificar se seu código usa imports obsoletos:

```bash
grep -rn "from database\.\|from etl\.\|from reports\.\|from utils\.\|import main" \
     --include="*.py" . \
     | grep -v "from pdw\." \
     | grep -v "__pycache__" \
     | grep -v "legacy/"
```

Qualquer linha retornada usa um caminho de import obsoleto que deve ser atualizado antes do PDW 11.0.0.
