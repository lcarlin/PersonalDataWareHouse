# TEST_PLAN.md
## Personal Data Warehouse — Plano de Testes
### Versão 10.1.0

---

## 1. Estratégia de Testes

### 1.1 Pirâmide de Testes

```
         ┌─────────────────────┐
         │   E2E / Regression  │  5%  ← pipeline completo com fixtures
         │─────────────────────│
         │   Integration Tests │  25% ← módulos + SQLite real
         │─────────────────────│
         │    Unit Tests       │  70% ← funções isoladas, sem I/O
         └─────────────────────┘
```

### 1.2 Ferramentas

| Ferramenta | Propósito | Versão |
|---|---|---|
| `pytest` | Test runner principal | ≥ 7.0 |
| `pytest-cov` | Cobertura de código | ≥ 4.0 |
| `pytest-mock` | Mocking | ≥ 3.0 |
| `openpyxl` | Criar fixtures Excel | (já dependência) |
| `sqlite3` | Banco em memória para testes | stdlib |

---

## 2. Estrutura de Diretórios de Teste

```
tests/
├── conftest.py              ← fixtures compartilhadas
├── fixtures/
│   ├── sample.xlsx          ← arquivo Excel mínimo de teste
│   ├── sample.cfg           ← configuração de teste
│   ├── sample_queries.yaml  ← queries YAML de teste
│   └── expected/
│       ├── lancamentos.csv  ← output esperado para comparação
│       └── pivot.csv        ← pivot esperado
│
├── unit/
│   ├── test_config_loader.py
│   ├── test_sanitizer.py
│   ├── test_database_operations.py
│   ├── test_localization.py
│   ├── test_compression.py
│   └── test_xml_utils.py
│
├── integration/
│   ├── test_etl_loader.py
│   ├── test_analytics_pivot.py
│   ├── test_analytics_totals.py
│   ├── test_reports_exporter.py
│   └── test_xlsx_generator.py
│
└── e2e/
    └── test_full_pipeline.py
```

---

## 3. Fixtures de Teste (`conftest.py`)

```python
import pytest
import sqlite3
import tempfile
import os
import pandas as pd
from openpyxl import Workbook


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d + "/"


@pytest.fixture
def sample_sqlite_db(tmp_dir):
    """Banco SQLite em arquivo temporário com dados mínimos."""
    db_path = tmp_dir + "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE LANCAMENTOS_GERAIS (
            Data TEXT, TIPO TEXT, DESCRICAO TEXT,
            Credito REAL, Debito REAL, Origem TEXT,
            Mes TEXT, DiaSemana TEXT
        )
    """)
    conn.executemany(
        "INSERT INTO LANCAMENTOS_GERAIS VALUES (?,?,?,?,?,?,?,?)",
        [
            ("2025-01-15", "Alimentação", "Mercado XYZ", 0.0, 150.00, "Nubank", "Janeiro", "Quarta-Feira"),
            ("2025-01-20", "Salário",     "Salário Jan", 8000.0, 0.0,  "BB",     "Janeiro", "Segunda-Feira"),
            ("2025-02-10", "Alimentação", "Restaurante", 0.0, 80.00,   "Nubank", "Segunda-Feira", "Fevereiro"),
        ]
    )
    conn.execute("CREATE TABLE TiposLancamentos (TIPO TEXT, CATEGORIA TEXT)")
    conn.executemany("INSERT INTO TiposLancamentos VALUES (?,?)", [
        ("Alimentação", "Despesa Fixa"),
        ("Salário", "Receita"),
    ])
    conn.execute("""
        CREATE TABLE PARCELAMENTOS (
            DESCRICAO TEXT, Valor REAL, Parcelas INTEGER, Inicio TEXT
        )
    """)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def sample_excel_file(tmp_dir):
    """Arquivo Excel mínimo com estrutura esperada pelo PDW."""
    path = tmp_dir + "PDW.xlsx"
    wb = Workbook()

    # Aba GUIDING
    ws = wb.create_sheet("GUIDING")
    ws.append(["TABLE_NAME", "ACCOUNTING", "LOADABLE"])
    ws.append(["Nubank", "X", "X"])
    ws.append(["BB", "X", "X"])
    ws.append(["PARCELAMENTOS", "", "X"])

    # Aba contábil: Nubank
    ws = wb.create_sheet("Nubank")
    ws.append(["Data", "TIPO", "DESCRICAO", "Credito", "Debito"])
    ws.append(["2025-01-15", "Alimentação", "Mercado XYZ", 0.0, 150.00])
    ws.append(["2025-01-20", "Salário", "Salário Jan", 8000.0, 0.0])

    # Aba contábil: BB
    ws = wb.create_sheet("BB")
    ws.append(["Data", "TIPO", "DESCRICAO", "Credito", "Debito"])
    ws.append(["2025-02-10", "Alimentação", "Restaurante", 0.0, 80.00])

    # Aba não-contábil: PARCELAMENTOS
    ws = wb.create_sheet("PARCELAMENTOS")
    ws.append(["DESCRICAO", "Valor", "Parcelas", "Inicio"])
    ws.append(["TV Parcelada", 3000.0, 12, "2025-01-01"])

    # Remove aba padrão
    del wb["Sheet"]

    wb.save(path)
    return path
```

---

## 4. Testes Unitários

### 4.1 `test_config_loader.py`

```python
import pytest
import configparser
from pdw.config.loader import load_config


def test_load_config_default_file(tmp_path, monkeypatch):
    """Deve ler PersonalDataWareHouse.cfg do CWD quando param_file vazio."""
    cfg_content = """
[DIRECTORIES]
DIR_IN = /tmp/in/
DIR_OUT = /tmp/out/
DATABASE_DIR = /tmp/db/
LOG_DIR = /tmp/log/

[FILE_TYPES]
TYPE_IN = xlsx
TYPE_OUT = xlsx
DB_FILE_TYPE = db
LOG_FILE = test.log
INPUT_FILE = PDW
OUT_DB_FILE = PDW
OUT_RPT_FILE = PDW_REPORTS
TRANSIENT_DATA_FILE = tmp

[SETTINGS]
CURRENT_VERSION = 10.1.0
API_VERSION = 2.0.0
GUIDING_TABLE = GUIDING
TYPES_OF_ENTRIES = TiposLancamentos
GENERAL_ENTRIES_TABLE = LANCAMENTOS_GERAIS
RUN_DATA_LOADER = False
RUN_REPORTS = True
OVERWRITE_DB = True
CREATE_PIVOT = True
RPT_SINGLE_FILE = True
PARALLELS = 1
MULTITHREADING = False
SAVE_DISCARTED_DATA = False
DISCARTED_DATA_TABLE = discarted_data
ANUAL_PIVOT_TABLE = HistoricoAnual
FULL_PIVOT_TABLE = HistoricoGeral
RUN_DINAMIC_REPORT = False
DIN_REPORT_GUIDING = General_din_reports
EXPORT_TRANSIENT_DATA = False
TRANSIENT_DATA_TABLE = Transient_data
TRANSIENT_DATA_COLUMN = Origem
EXPORT_OTHER_TYPES = False
DAYLY_PROGRESS = contagem_diaria
SPLT_PAYMNT_TAB = PARCELAMENTOS
OUT_RES_PMNT_TAB = Resumo_Parcelamentos
MONTHLY_SUMMATIES = Resumido_In_Out
YAML_SQL_FILE = PDW_QUERIES.yaml
"""
    cfg_file = tmp_path / "PersonalDataWareHouse.cfg"
    cfg_file.write_text(cfg_content)
    monkeypatch.chdir(tmp_path)

    result = load_config("")
    assert result['run_loader'] == False
    assert result['run_reports'] == True
    assert result['guiding_table'] == 'GUIDING'
    assert result['general_entries_table'] == 'LANCAMENTOS_GERAIS'


def test_load_config_version_mismatch_exits(tmp_path, monkeypatch):
    """Deve chamar exit(1) quando versão do .cfg não bate."""
    # ... cria .cfg com CURRENT_VERSION = 9.0.0
    with pytest.raises(SystemExit) as exc_info:
        load_config(str(tmp_path / "wrong_version.cfg"))
    assert exc_info.value.code == 1


def test_load_config_missing_file_exits():
    """Deve chamar exit(1) quando arquivo não existe."""
    with pytest.raises(SystemExit) as exc_info:
        load_config("/nonexistent/path/config.cfg")
    assert exc_info.value.code == 1


def test_load_config_returns_all_keys(tmp_path, monkeypatch):
    """Retorno deve conter todas as 32 chaves esperadas."""
    # ... setup
    result = load_config(str(tmp_path / "test.cfg"))
    expected_keys = [
        'current_version', 'config_file', 'dir_file_in', 'dir_file_out',
        'dir_log', 'dir_db', 'in_file', 'in_type', 'out_type', 'out_db',
        'output_name', 'db_file_type', 'log_file_cfg', 'multithread',
        'overwrite_db', 'run_loader', 'run_reports', 'multi_rept_file',
        'guiding_table', 'types_of_entries', 'general_entries_table',
        'create_pivot', 'save_discarted_data', 'discarted_data_table',
        'full_hist_table', 'anual_hist_table', 'origem_dados',
        'other_file_types', 'dinamic_reports', 'din_report_guinding',
        'dayly_progress', 'split_paymnt_table', 'out_table',
        'monthly_summarie', 'queries_file',
    ]
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"
```

---

### 4.2 `test_sanitizer.py`

```python
import pytest
import pandas as pd
import numpy as np
from pdw.etl.sanitizer import sanitize_entries_dataframe, clean_description_text


@pytest.fixture
def raw_entries_df():
    return pd.DataFrame({
        'Data':      ['2025-01-15', '2025-02-10', None,         '2025-03-01'],
        'TIPO':      ['Alimentação', None,          'Salário',   'Alimentação'],
        'DESCRICAO': ['Mercado; XYZ', 'Rest,ant', 'Depósito',  'café∴'],
        'Credito':   [0.0,           0.0,          8000.0,      0.0],
        'Debito':    [150.0,         80.0,         0.0,         np.nan],
        'Origem':    ['Nubank',      'Nubank',     'BB',        'Nubank'],
    })


def test_remove_nulls_tipo(raw_entries_df):
    """Deve remover linhas com TIPO nulo quando remove_nulls=True."""
    result = sanitize_entries_dataframe(raw_entries_df, remove_nulls=True)
    assert result['TIPO'].isna().sum() == 0
    assert len(result) == 3  # 1 linha com TIPO nulo removida


def test_remove_nulls_data(raw_entries_df):
    """Deve remover linhas com Data nula quando remove_nulls=True."""
    result = sanitize_entries_dataframe(raw_entries_df, remove_nulls=True)
    assert result['Data'].isna().sum() == 0


def test_keep_nulls_when_false(raw_entries_df):
    """Deve manter linhas nulas quando remove_nulls=False."""
    result = sanitize_entries_dataframe(raw_entries_df, remove_nulls=False)
    assert len(result) == 4


def test_clean_semicolons(raw_entries_df):
    """Deve substituir ; e , por | em DESCRICAO."""
    result = sanitize_entries_dataframe(raw_entries_df, remove_nulls=True)
    assert 'Mercado| XYZ' in result['DESCRICAO'].values
    assert 'Rest|ant' in result['DESCRICAO'].values


def test_substitui_triangulo(raw_entries_df):
    """Deve substituir ∴ por ' .'. '."""
    result = sanitize_entries_dataframe(raw_entries_df, remove_nulls=False)
    cafe_row = result[result['DESCRICAO'].str.contains(r"\.'\.")]['DESCRICAO']
    assert len(cafe_row) > 0


def test_adiciona_coluna_mes(raw_entries_df):
    """Deve adicionar coluna 'Mes' com nome PT-BR."""
    result = sanitize_entries_dataframe(raw_entries_df, remove_nulls=True)
    assert 'Mes' in result.columns
    assert 'Janeiro' in result['Mes'].values
    assert 'Fevereiro' in result['Mes'].values


def test_adiciona_coluna_dia_semana(raw_entries_df):
    """Deve adicionar coluna 'DiaSemana' com nome PT-BR."""
    result = sanitize_entries_dataframe(raw_entries_df, remove_nulls=True)
    assert 'DiaSemana' in result.columns
    dias_validos = {'Segunda-Feira', 'Terca-Feira', 'Quarta-Feira',
                    'Quinta-Feira', 'Sexta-Feira', 'Sabado', 'Domingo'}
    for dia in result['DiaSemana'].dropna():
        assert dia in dias_validos


def test_preenche_debito_nan_com_zero(raw_entries_df):
    """Deve preencher Debito NaN com 0.0."""
    result = sanitize_entries_dataframe(raw_entries_df, remove_nulls=False)
    assert result['Debito'].isna().sum() == 0
    assert (result['Debito'] >= 0).all()


def test_nao_modifica_dataframe_original(raw_entries_df):
    """Deve retornar novo DataFrame sem modificar o original."""
    original_len = len(raw_entries_df)
    sanitize_entries_dataframe(raw_entries_df, remove_nulls=True)
    assert len(raw_entries_df) == original_len  # original intacto
```

---

### 4.3 `test_database_operations.py`

```python
import pytest
import sqlite3
import pandas as pd
from pdw.database.operations import (
    table_droppator, save_dataframe_to_database, sort_dataframe_by_date
)


@pytest.fixture
def conn_and_cursor():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    conn.execute("CREATE TABLE test_table (Data TEXT, Val REAL)")
    conn.execute("INSERT INTO test_table VALUES ('2025-01-01', 100)")
    conn.commit()
    yield conn, cursor
    conn.close()


def test_table_droppator_via_cursor(conn_and_cursor):
    conn, cursor = conn_and_cursor
    table_droppator(cursor, "test_table")
    conn.commit()
    result = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    assert ('test_table',) not in result


def test_table_droppator_nonexistent_table(conn_and_cursor):
    conn, cursor = conn_and_cursor
    # DROP TABLE IF EXISTS — não deve lançar exceção
    table_droppator(cursor, "nonexistent_table")


def test_sort_dataframe_by_date_descending():
    df = pd.DataFrame({'Data': ['2025-01-01', '2025-03-01', '2025-02-01'], 'Val': [1, 3, 2]})
    result = sort_dataframe_by_date(df, ascending=False)
    assert list(result['Data']) == ['2025-03-01', '2025-02-01', '2025-01-01']


def test_sort_dataframe_by_date_ascending():
    df = pd.DataFrame({'Data': ['2025-03-01', '2025-01-01', '2025-02-01'], 'Val': [3, 1, 2]})
    result = sort_dataframe_by_date(df, ascending=True)
    assert list(result['Data']) == ['2025-01-01', '2025-02-01', '2025-03-01']


def test_save_dataframe_to_database(tmp_path):
    db = str(tmp_path / "test.db")
    conn = sqlite3.connect(db)
    df = pd.DataFrame({'Data': ['2025-01-01', '2025-02-01'], 'Val': [100.0, 200.0]})
    n = save_dataframe_to_database(df, conn, "test_out", sort_by_date=False)
    assert n == 2
    result = pd.read_sql("SELECT * FROM test_out", conn)
    assert len(result) == 2
    conn.close()


def test_save_dataframe_sorts_by_date(tmp_path):
    db = str(tmp_path / "test.db")
    conn = sqlite3.connect(db)
    df = pd.DataFrame({'Data': ['2025-01-01', '2025-03-01', '2025-02-01'], 'Val': [1, 3, 2]})
    save_dataframe_to_database(df, conn, "sorted_out", sort_by_date=True)
    result = pd.read_sql("SELECT * FROM sorted_out", conn)
    assert result['Data'].iloc[0] == '2025-03-01'  # mais recente primeiro
    conn.close()
```

---

### 4.4 `test_localization.py`

```python
from pdw.utils.localization import get_month_names, get_weekday_names


def test_get_month_names_returns_12_months():
    months = get_month_names()
    assert len(months) == 12
    assert months[1] == 'Janeiro'
    assert months[12] == 'Dezembro'


def test_get_month_names_all_keys():
    months = get_month_names()
    for i in range(1, 13):
        assert i in months


def test_get_weekday_names_returns_7_days():
    days = get_weekday_names()
    assert len(days) == 7


def test_get_weekday_names_monday_is_zero():
    days = get_weekday_names()
    assert days[0] == 'Segunda-Feira'
```

---

## 5. Testes de Integração

### 5.1 `test_etl_loader.py`

```python
def test_new_data_loader_creates_general_entries_table(sample_excel_file, tmp_dir):
    """ETL completo deve criar LANCAMENTOS_GERAIS com dados corretos."""
    db_path = tmp_dir + "test.db"
    new_data_loader(
        data_base=db_path,
        types_sheet="TiposLancamentos",
        general_entries_table="LANCAMENTOS_GERAIS",
        data_origin_col="Origem",
        guiding_sheet="GUIDING",
        excel_file=sample_excel_file,
        save_useless=False,
        udt="discarted_data"
    )
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM LANCAMENTOS_GERAIS", conn)
    conn.close()
    assert len(df) > 0
    assert 'Data' in df.columns
    assert 'TIPO' in df.columns
    assert 'Origem' in df.columns


def test_new_data_loader_origem_column_populated(sample_excel_file, tmp_dir):
    """Coluna Origem deve ter o nome da aba de onde veio o lançamento."""
    db_path = tmp_dir + "test.db"
    new_data_loader(db_path, "TiposLancamentos", "LANCAMENTOS_GERAIS",
                    "Origem", "GUIDING", sample_excel_file, False, "disc")
    conn = sqlite3.connect(db_path)
    origens = pd.read_sql("SELECT DISTINCT Origem FROM LANCAMENTOS_GERAIS", conn)['Origem'].tolist()
    conn.close()
    assert 'Nubank' in origens
    assert 'BB' in origens


def test_non_accounting_sheet_loaded(sample_excel_file, tmp_dir):
    """Aba PARCELAMENTOS (não-contábil) deve ser carregada como tabela."""
    db_path = tmp_dir + "test.db"
    new_data_loader(db_path, "TiposLancamentos", "LANCAMENTOS_GERAIS",
                    "Origem", "GUIDING", sample_excel_file, False, "disc")
    conn = sqlite3.connect(db_path)
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    conn.close()
    assert 'PARCELAMENTOS' in tables['name'].values
```

---

## 6. Testes de Regressão

### 6.1 Paridade de Output com Versão 9.11.2

```python
def test_output_identical_to_legacy(sample_excel_file, tmp_dir):
    """
    Garante que o output do pdw/ é bit-a-bit idêntico ao do monolito legado.
    Executa ambas as versões e compara os bancos SQLite.
    """
    # Executa v10 (nova)
    db_v10 = tmp_dir + "pdw_v10.db"
    run_pipeline_v10(sample_excel_file, db_v10)

    # Executa v9 (legacy)
    db_v9 = tmp_dir + "pdw_v9.db"
    run_pipeline_v9(sample_excel_file, db_v9)

    # Compara LANCAMENTOS_GERAIS
    conn10 = sqlite3.connect(db_v10)
    conn9  = sqlite3.connect(db_v9)
    df10 = pd.read_sql("SELECT * FROM LANCAMENTOS_GERAIS ORDER BY Data, TIPO, DESCRICAO", conn10)
    df9  = pd.read_sql("SELECT * FROM LANCAMENTOS_GERAIS ORDER BY Data, TIPO, DESCRICAO", conn9)
    conn10.close()
    conn9.close()

    pd.testing.assert_frame_equal(df10, df9, check_like=True)
```

---

## 7. Testes E2E

### 7.1 `test_full_pipeline.py`

```python
def test_full_pipeline_with_real_config(tmp_dir, sample_excel_file):
    """Pipeline completo: ETL → pivot → relatórios."""
    # Configurar ambiente
    cfg_path = create_test_config(tmp_dir, sample_excel_file)

    # Executar pipeline
    from pdw.core.orchestrator import run_pipeline
    run_pipeline(cfg_path)

    # Verificar outputs
    assert os.path.exists(tmp_dir + "PDW.db")
    assert os.path.exists(tmp_dir + "PDW_REPORTS.v2.xlsx")

    # Verificar banco tem dados
    conn = sqlite3.connect(tmp_dir + "PDW.db")
    count = conn.execute("SELECT COUNT(*) FROM LANCAMENTOS_GERAIS").fetchone()[0]
    conn.close()
    assert count > 0

    # Verificar log foi escrito
    log_files = [f for f in os.listdir(tmp_dir) if f.endswith('.log')]
    assert len(log_files) == 1
```

---

## 8. Cobertura de Código

### 8.1 Meta de Cobertura

| Módulo | Meta | Prioridade |
|---|---|---|
| `pdw/config/loader.py` | 90% | Alta |
| `pdw/etl/sanitizer.py` | 95% | Alta |
| `pdw/database/operations.py` | 95% | Alta |
| `pdw/utils/localization.py` | 100% | Baixa |
| `pdw/utils/compression.py` | 85% | Média |
| `pdw/etl/loader.py` | 80% | Alta |
| `pdw/analytics/totals.py` | 80% | Média |
| `pdw/reports/exporter.py` | 75% | Média |
| **Total** | **≥ 80%** | — |

### 8.2 Executar Cobertura

```bash
# Instalar
pip install pytest pytest-cov

# Executar com relatório
pytest tests/ --cov=pdw --cov-report=term-missing --cov-report=html

# Ver relatório HTML
open htmlcov/index.html
```

---

## 9. Testes de Compatibilidade Retroativa

### 9.1 Verificar Imports Legados

```python
def test_legacy_import_database_drop_table():
    """Stub legado deve importar sem erro (emite DeprecationWarning)."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from database.drop_table import table_droppator
    assert callable(table_droppator)


def test_legacy_import_emits_deprecation_warning():
    """Stub legado deve emitir DeprecationWarning."""
    with pytest.warns(DeprecationWarning, match="foi movido para"):
        from utils.compressor import gzip_compressor


def test_main_module_facade_exports_25_names():
    """Facade PersonalDataWareHouse.py deve exportar todos os 25 nomes públicos."""
    import importlib
    pdw = importlib.import_module("PersonalDataWareHouse")
    expected_names = [
        'main', 'new_data_loader', 'data_loader', 'read_guiding_sheet',
        'process_accounting_sheet', 'process_non_accounting_sheet',
        'sanitize_entries_dataframe', 'data_correjeitor',
        'table_droppator', 'save_dataframe_to_database', 'sort_dataframe_by_date',
        'create_pivot_history', 'create_dinamic_reports',
        'totalizador_diario', 'monthly_summaries', 'split_paymnt_resume',
        'general_entries_file_exportator', 'xlsx_report_generator',
        'gerar_todos_relatorios_integrado', 'gzip_compressor',
        'dataframe_to_xml', 'transient_data_exportator',
        'get_month_names', 'get_weekday_names',
    ]
    for name in expected_names:
        assert hasattr(pdw, name), f"Missing public name: {name}"


def test_data_loader_alias_is_new_data_loader():
    """data_loader deve ser alias de new_data_loader."""
    import importlib
    pdw = importlib.import_module("PersonalDataWareHouse")
    assert pdw.data_loader is pdw.new_data_loader
```

---

## 10. CI/CD (Integração Contínua)

### GitHub Actions

```yaml
name: PDW Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install pandas openpyxl xlrd xlsxwriter numpy pyyaml
          pip install pytest pytest-cov pytest-mock

      - name: Run tests
        run: pytest tests/ --cov=pdw --cov-report=xml -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```
