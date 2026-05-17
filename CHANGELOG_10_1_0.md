# CHANGELOG_10_1_0.md
## Personal Data Warehouse — Release Notes v10.1.0
### Data: 2026-05-17 | Autor: Carlin, Luiz A. .'.

---

## Resumo

A versão 10.1.0 é uma **release de modularização arquitetural incremental**.
Nenhuma regra de negócio foi alterada. Nenhum algoritmo foi modificado.
O comportamento funcional do pipeline é **idêntico** ao da versão 9.11.2.

---

## O que mudou

### Novo: Pacote `pdw/`

O monolito `PersonalDataWareHouse.py` foi decomposto em um pacote Python
estruturado com 14 módulos agrupados por responsabilidade:

```
pdw/
├── __init__.py               ← versão canônica (__version__ = "10.1.0")
├── main.py                   ← ponto de entrada do pacote
├── config/
│   └── loader.py             ← leitura e validação do .cfg
├── core/
│   └── orchestrator.py       ← lógica de orquestração do pipeline
├── infrastructure/
│   └── logging.py            ← gerenciamento do arquivo de log
├── etl/
│   ├── loader.py             ← carregamento de planilhas Excel → SQLite
│   └── sanitizer.py          ← transformação e limpeza de dados
├── database/
│   └── operations.py         ← operações de infraestrutura de banco
├── analytics/
│   ├── pivot.py              ← tabelas pivot e relatórios dinâmicos
│   └── totals.py             ← totalizações e sumarizações
├── reports/
│   ├── exporter.py           ← exportação multi-formato (CSV/JSON/XML)
│   ├── xlsx_generator.py     ← gerador de Excel a partir de YAML
│   └── novos_relatorios.py   ← relatórios analíticos avançados (migrado)
├── utils/
│   ├── compression.py        ← compressão gzip
│   ├── xml_utils.py          ← conversão DataFrame → XML
│   ├── localization.py       ← dicionários PT-BR (meses, dias da semana)
│   └── transient_data.py     ← exportador de dados transientes (migrado)
└── compat/
    └── __init__.py           ← aliases centralizados para migração gradual
```

---

### Novo: Camada de compatibilidade retroativa

Stubs de compatibilidade foram criados para todos os caminhos de import
que existiam na versão anterior ao monolito (estrutura `dad8edf`):

| Módulo legado | Redireciona para |
|---|---|
| `database/drop_table.py` | `pdw.database.operations` |
| `etl/data_loader.py` | `pdw.etl.loader` |
| `reports/general_exportator.py` | `pdw.reports.exporter` |
| `reports/monthly_data.py` | `pdw.analytics.totals` |
| `reports/split_paymnts.py` | `pdw.analytics.totals` |
| `reports/xlsx_reports.py` | `pdw.reports.xlsx_generator` |
| `reports/novos_relatorios.py` | `pdw.reports.novos_relatorios` |
| `utils/compressor.py` | `pdw.utils.compression` |
| `utils/correjeitor.py` | `pdw.etl.sanitizer` |
| `utils/daily_totalizer.py` | `pdw.analytics.totals` |
| `utils/dinamic_reports.py` | `pdw.analytics.pivot` |
| `utils/pivot_tables.py` | `pdw.analytics.pivot` |
| `utils/transient_data.py` | `pdw.utils.transient_data` |
| `utils/xml_df.py` | `pdw.utils.xml_utils` |
| `main.py` (raiz) | `pdw.main` |

---

### Modificado: `PersonalDataWareHouse.py`

O arquivo foi convertido em uma **facade de compatibilidade** que:
- Mantém todos os 25 nomes públicos importáveis diretamente
- Preserva o ponto de entrada `if __name__ == '__main__'` sem alterações
- Re-exporta o alias `data_loader = new_data_loader` para retrocompatibilidade
- Inclui o histórico de versão completo atualizado

---

### Modificado: `PersonalDataWareHouse.cfg`

```diff
- CURRENT_VERSION = 9.11.2
+ CURRENT_VERSION = 10.1.0
```

Esta é a **única alteração** no arquivo de configuração.

---

### Preservado: `legacy/PersonalDataWareHouse.9.11.2.py`

O monolito original da v9.11.2 foi copiado integralmente para `legacy/`.
Pode ser executado diretamente para comparação ou rollback:

```bash
python legacy/PersonalDataWareHouse.9.11.2.py
```
(Requer atualizar `CURRENT_VERSION` no .cfg para `9.11.2` antes de usar.)

---

## O que NÃO mudou

- Todas as assinaturas de funções públicas
- Todos os algoritmos de negócio
- Todos os formatos de saída (CSV, JSON, XML, XLSX, SQLite)
- Todas as mensagens de erro e de console
- Toda a lógica de validação de configuração
- O formato do arquivo de log
- O contrato do arquivo `.cfg`
- O contrato do arquivo `PDW_QUERIES.yaml`
- O comportamento do RunPDW.sh / RunPDW.ps1 / Run_PDW.bat

---

## Novidades Técnicas

### Alias `data_loader` restaurado

O nome `data_loader` (que era o nome original da função antes da v9.10.0)
foi restaurado como alias público em `PersonalDataWareHouse.py` e em `pdw.compat`:

```python
data_loader = new_data_loader  # alias de compatibilidade
```

### `transient_data_exportator` com bug corrigido

A função `transient_data_exportator` em `pdw/utils/transient_data.py` teve
o bug de `import datetime` ausente (presente no código legado) corrigido.
O comportamento funcional é idêntico.

### `gerar_todos_relatorios_integrado` com dependências opcionais

A função foi migrada para `pdw/reports/novos_relatorios.py` com tratamento
explícito de dependências opcionais (`matplotlib`, `seaborn`, `scipy`, `fpdf2`).
Caso não instaladas, a importação funciona mas a chamada levanta `ImportError`
com mensagem de orientação.

### Novo módulo de configuração com versão canônica

A versão agora tem uma única fonte de verdade:

```python
# pdw/__init__.py
__version__ = "10.1.0"

# pdw/config/loader.py
from pdw import __version__
CURRENT_VERSION = __version__
```

---

## Depreciações

Os seguintes caminhos de import emitem `DeprecationWarning` e serão
**removidos na versão 11.0.0**:

```
database.drop_table
etl.data_loader
reports.general_exportator
reports.monthly_data
reports.split_paymnts
reports.xlsx_reports
reports.novos_relatorios
utils.compressor
utils.correjeitor
utils.daily_totalizer
utils.dinamic_reports
utils.pivot_tables
utils.transient_data
utils.xml_df
main (raiz)
```

---

## Modo de Invocação

```bash
# Modo legado (preservado — sem alteração necessária)
python PersonalDataWareHouse.py
python PersonalDataWareHouse.py /caminho/para/custom.cfg

# Modo pacote (novo a partir de 10.1.0)
python -m pdw
python -m pdw /caminho/para/custom.cfg
```

---

## Verificações Realizadas

| Verificação | Resultado |
|---|---|
| Sintaxe AST — todos os módulos `pdw/` | ✅ PASS |
| Sintaxe AST — todos os stubs legados | ✅ PASS |
| Cobertura — 25/25 funções presentes em exatamente 1 módulo `pdw/` | ✅ PASS |
| Grafo de dependências — ausência de ciclos | ✅ PASS |
| Stubs legados — todos os 18 contratos de re-export verificados | ✅ PASS |
| Versão — `.cfg` e `pdw/__init__.py` sincronizados em `10.1.0` | ✅ PASS |

---

## Rollback para 9.11.2

Para reverter completamente para a versão anterior:

```bash
# 1. Restaurar o monolito original
cp legacy/PersonalDataWareHouse.9.11.2.py PersonalDataWareHouse.py

# 2. Reverter a versão no .cfg
sed -i 's/CURRENT_VERSION = 10.1.0/CURRENT_VERSION = 9.11.2/' PersonalDataWareHouse.cfg

# 3. (Opcional) Remover o pacote pdw/
rm -rf pdw/ database/ etl/ reports/ utils/ importers/ main.py __init__.py
```

Ou simplesmente via git:
```bash
git checkout dad8edf -- PersonalDataWareHouse.py PersonalDataWareHouse.cfg
```
