# Personal Data Warehouse (PDW)
## Sistema de ET&L Pessoal — Versão 10.1.0

---

## Visão Geral

O **Personal Data Warehouse** é um sistema batch de **Extract, Transform & Load (ET&L)** desenvolvido para processar dados financeiros pessoais armazenados em planilhas Excel e carregá-los em um banco de dados SQLite, gerando relatórios em múltiplos formatos.

```
┌─────────────┐    ┌───────────────┐    ┌──────────────┐    ┌──────────────────┐
│  PDW.xlsx   │───▶│  ET&L Engine  │───▶│  PDW.db      │───▶│  Relatórios      │
│ (Entrada)   │    │  (pdw/etl/)   │    │  (SQLite3)   │    │  .xlsx .csv      │
│             │    │               │    │              │    │  .json.gz .xml.gz│
└─────────────┘    └───────────────┘    └──────────────┘    └──────────────────┘
        ▲                   ▲
        │                   │
┌───────────────┐   ┌───────────────┐
│  .cfg         │   │  .yaml        │
│  (Config INI) │   │  (SQL Queries)│
└───────────────┘   └───────────────┘
```

---

## Domínio

**Problema resolvido**: Agregação e análise de múltiplas fontes de lançamentos financeiros pessoais (contas bancárias, cartões, investimentos) distribuídas em diferentes abas de uma planilha Excel.

**Entidades principais**:

| Entidade | Descrição | Tabela SQLite |
|---|---|---|
| Lançamento | Movimentação financeira (crédito ou débito) | `LANCAMENTOS_GERAIS` |
| Tipo | Categoria do lançamento (ex: Alimentação, Transporte) | `TiposLancamentos` |
| Origem | Conta/fonte do lançamento (nome da aba Excel) | coluna `Origem` |
| Parcelamento | Compra parcelada com múltiplas parcelas | `PARCELAMENTOS` |
| Guia | Configuração de quais abas processar | `GUIDING` |

---

## Arquitetura em Uma Página

```
PersonalDataWareHouse.py   ← ponto de entrada (facade compatível com v9.x)
         │
         ▼
    pdw/main.py
         │
         ▼
    pdw/core/orchestrator.py          ← orquestrador do pipeline
    ├── pdw/config/loader.py          ← leitura do .cfg
    ├── pdw/infrastructure/logging.py ← gestão do log
    │
    ├── pdw/etl/loader.py             ← carrega Excel → SQLite
    │   ├── pdw/etl/sanitizer.py      ← transforma e limpa dados
    │   │   ├── pdw/utils/localization.py
    │   │   └── pdw/database/operations.py
    │   └── pdw/database/operations.py
    │
    ├── pdw/analytics/pivot.py        ← tabelas pivot
    │
    ├── pdw/analytics/totals.py       ← sumarizações
    │   └── (chamado por xlsx_generator)
    │
    ├── pdw/reports/exporter.py       ← exporta CSV/JSON/XML
    │   ├── pdw/utils/compression.py
    │   └── pdw/utils/xml_utils.py
    │
    └── pdw/reports/xlsx_generator.py ← gera Excel a partir de YAML
        └── pdw/analytics/totals.py
```

---

## Início Rápido

### Pré-requisitos

```bash
Python >= 3.8
pip install pandas openpyxl xlrd xlsxwriter numpy pyyaml
```

### Instalação

```bash
git clone <repo>
cd PersonalDataWareHouse
bash InstalaDependencias.sh   # instala dependências via pip
```

### Configuração Mínima

Edite `PersonalDataWareHouse.cfg`:

```ini
[DIRECTORIES]
DIR_IN  = /caminho/para/entrada/
DIR_OUT = /caminho/para/saida/
DATABASE_DIR = /caminho/para/banco/
LOG_DIR = /caminho/para/logs/

[FILE_TYPES]
INPUT_FILE = PDW          # nome do arquivo Excel (sem extensão)
OUT_DB_FILE = PDW         # nome do banco SQLite (sem extensão)
OUT_RPT_FILE = PDW_REPORTS.v2

[SETTINGS]
CURRENT_VERSION = 10.1.0  # deve bater com __version__ do pacote
RUN_DATA_LOADER = True
RUN_REPORTS = True
```

### Execução

```bash
# Modo padrão
python PersonalDataWareHouse.py

# Com arquivo de configuração customizado
python PersonalDataWareHouse.py /caminho/para/custom.cfg

# Via pacote
python -m pdw
python -m pdw /caminho/para/custom.cfg

# Via shell script (Linux/macOS)
bash RunPDW.sh
```

---

## Estrutura do Projeto

```
PersonalDataWareHouse/
├── PersonalDataWareHouse.py     ← facade de compatibilidade (entry point)
├── PersonalDataWareHouse.cfg    ← configuração do pipeline
├── PDW_QUERIES.yaml             ← queries SQL para relatórios
├── RunPDW.sh                    ← launcher Linux com controle de lock
├── RunPDW.ps1                   ← launcher PowerShell
├── Run_PDW.bat                  ← launcher Windows CMD
│
├── pdw/                         ← pacote principal (v10.1.0)
│   ├── __init__.py              ← versão canônica
│   ├── main.py                  ← entry point do pacote
│   ├── config/loader.py         ← leitura de configuração
│   ├── core/orchestrator.py     ← orquestração
│   ├── infrastructure/logging.py
│   ├── etl/loader.py
│   ├── etl/sanitizer.py
│   ├── database/operations.py
│   ├── analytics/pivot.py
│   ├── analytics/totals.py
│   ├── reports/exporter.py
│   ├── reports/xlsx_generator.py
│   ├── reports/novos_relatorios.py  ← relatórios avançados (deps opcionais)
│   ├── utils/compression.py
│   ├── utils/xml_utils.py
│   ├── utils/localization.py
│   ├── utils/transient_data.py
│   └── compat/__init__.py       ← aliases de compatibilidade
│
├── legacy/
│   └── PersonalDataWareHouse.9.11.2.py   ← monolito original preservado
│
├── database/, etl/, reports/, utils/     ← stubs de compatibilidade v9.x
│
└── docs/                         ← documentação arquitetural
    ├── README.md
    ├── ARQUITETURA_JAVA.md
    └── ...
```

---

## Fluxo de Execução (Resumido)

1. **Config**: Lê `.cfg`, valida versão, constrói caminhos
2. **Log**: Abre arquivo de log, lê última execução
3. **Loader** *(se `RUN_DATA_LOADER=True`)*:
   - Lê aba `GUIDING` do Excel
   - Para cada aba configurada: extrai, transforma, carrega no SQLite
   - Consolida em `LANCAMENTOS_GERAIS`
   - Executa pós-processamento (normalização, view `Origens`)
4. **Pivot** *(se `CREATE_PIVOT=True`)*:
   - Cria tabelas pivot mensais e anuais
   - Gera relatórios dinâmicos configurados no Excel
5. **Reports** *(se `RUN_REPORTS=True`)*:
   - Exporta `LANCAMENTOS_GERAIS` para CSV/JSON/XML
   - Gera sumarizações de parcelamentos e mensais
   - Gera Excel com todas as queries do YAML
6. **Log**: Registra tempo total, versão, hostname

---

## Configuração Completa

Ver `DEPLOY_GUIDE.md` para referência completa de todos os parâmetros.

---

## Módulos por Responsabilidade

| Módulo | Responsabilidade | Funções |
|---|---|---|
| `pdw.core.orchestrator` | Pipeline completo | `run_pipeline` |
| `pdw.config.loader` | Leitura de configuração | `load_config` |
| `pdw.infrastructure.logging` | Gestão de log | `open_log`, `finalize_log` |
| `pdw.etl.loader` | Carga Excel→SQLite | `new_data_loader`, `read_guiding_sheet`, `process_accounting_sheet`, `process_non_accounting_sheet` |
| `pdw.etl.sanitizer` | Transformação e limpeza | `sanitize_entries_dataframe`, `data_correjeitor`, + 4 aux |
| `pdw.database.operations` | Operações de banco | `table_droppator`, `save_dataframe_to_database`, `sort_dataframe_by_date` |
| `pdw.analytics.pivot` | Tabelas pivot | `create_pivot_history`, `create_dinamic_reports` |
| `pdw.analytics.totals` | Totalizações | `totalizador_diario`, `monthly_summaries`, `split_paymnt_resume` |
| `pdw.reports.exporter` | Exportação multi-formato | `general_entries_file_exportator` |
| `pdw.reports.xlsx_generator` | Gerador Excel/YAML | `xlsx_report_generator` |
| `pdw.utils.compression` | Compressão gzip | `gzip_compressor` |
| `pdw.utils.xml_utils` | Conversão XML | `dataframe_to_xml` |
| `pdw.utils.localization` | Nomes PT-BR | `get_month_names`, `get_weekday_names` |
| `pdw.utils.transient_data` | Dados transientes | `transient_data_exportator` |

---

## Licença e Autoria

- **Autor**: Carlin, Luiz A. .'.
- **e-mail**: luiz.carlin@gmail.com
- **Data de início**: 13-DEC-2022
- **Versão atual**: 10.1.0
