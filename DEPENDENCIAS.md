# DEPENDENCIAS.md
## Personal Data Warehouse — Mapa Completo de Dependências
### Versão 10.1.0

---

## 1. Dependências Python (Runtime)

### Obrigatórias

| Biblioteca | Versão mínima | Módulo(s) PDW | Propósito |
|---|---|---|---|
| `pandas` | ≥ 1.5.0 | todos os ETL/analytics/reports | DataFrames, leitura Excel, escrita SQLite, pivot tables |
| `numpy` | ≥ 1.23.0 | `etl/sanitizer.py`, `etl/loader.py`, `reports/novos_relatorios.py` | NaN handling, operações numéricas |
| `openpyxl` | ≥ 3.0.0 | (via pandas) | Leitura de Excel .xlsx |
| `xlrd` | ≥ 2.0.0 | (via pandas) | Leitura de Excel .xls (legacy) |
| `xlsxwriter` | ≥ 3.0.0 | `reports/xlsx_generator.py` | Escrita de Excel .xlsx com engine xlsxwriter |
| `pyyaml` | ≥ 6.0.0 | `reports/xlsx_generator.py` | Leitura do arquivo de queries SQL |

### Stdlib (sem instalação adicional)

| Biblioteca | Versão | Módulo(s) PDW | Propósito |
|---|---|---|---|
| `sqlite3` | stdlib | `etl/loader.py`, `analytics/*`, `reports/*` | Banco de dados local |
| `configparser` | stdlib | `config/loader.py` | Leitura do arquivo .cfg (INI format) |
| `datetime` | stdlib | `core/orchestrator.py`, `infrastructure/logging.py`, `utils/transient_data.py` | Timestamps, formatação de datas |
| `os` | stdlib | múltiplos | Operações de sistema de arquivos |
| `platform` | stdlib | `core/orchestrator.py` | Detecção de OS e hostname |
| `sys` | stdlib | `pdw/main.py` | Argumentos de linha de comando |
| `threading` | stdlib | `core/orchestrator.py` | Importado (não usado — feature desabilitada) |
| `time` | stdlib | `core/orchestrator.py` | Medição de tempo de execução |
| `xml.etree.ElementTree` | stdlib | `utils/xml_utils.py` | Geração de XML |
| `gzip` | stdlib | `utils/compression.py` | Compressão de arquivos |
| `shutil` | stdlib | `utils/compression.py` | Cópia de streams de arquivo |

### Opcionais (apenas `pdw/reports/novos_relatorios.py`)

| Biblioteca | Propósito | Instalação |
|---|---|---|
| `matplotlib` | Geração de gráficos | `pip install matplotlib` |
| `seaborn` | Gráficos estatísticos | `pip install seaborn` |
| `scipy` | Regressão linear para previsão | `pip install scipy` |
| `fpdf2` | Geração de PDF | `pip install fpdf2` |

---

## 2. Grafo de Dependências por Módulo

```
pdw/config/loader.py
  └── configparser (stdlib)

pdw/infrastructure/logging.py
  └── os (stdlib)
  └── datetime (stdlib)

pdw/utils/localization.py
  └── (sem dependências externas)

pdw/utils/compression.py
  └── gzip (stdlib)
  └── shutil (stdlib)
  └── os (stdlib)

pdw/utils/xml_utils.py
  └── xml.etree.ElementTree (stdlib)

pdw/database/operations.py
  └── (sem imports externos — recebe conn/cursor como parâmetro)

pdw/etl/sanitizer.py
  └── numpy
  └── pandas
  └── pdw.utils.localization
  └── pdw.database.operations

pdw/etl/loader.py
  └── sqlite3 (stdlib)
  └── pandas
  └── numpy
  └── pdw.database.operations
  └── pdw.etl.sanitizer

pdw/analytics/totals.py
  └── sqlite3 (stdlib)
  └── pandas

pdw/analytics/pivot.py
  └── sqlite3 (stdlib)
  └── pandas

pdw/reports/exporter.py
  └── sqlite3 (stdlib)
  └── pandas
  └── pdw.utils.compression
  └── pdw.utils.xml_utils

pdw/reports/xlsx_generator.py
  └── sqlite3 (stdlib)
  └── pandas
  └── yaml (pyyaml)
  └── pdw.analytics.totals

pdw/core/orchestrator.py
  └── datetime (stdlib)
  └── os (stdlib)
  └── platform (stdlib)
  └── threading (stdlib) [importado, não usado]
  └── time (stdlib)
  └── pdw.config.loader
  └── pdw.infrastructure.logging
  └── pdw.etl.loader
  └── pdw.analytics.pivot
  └── pdw.analytics.totals
  └── pdw.reports.exporter
  └── pdw.reports.xlsx_generator
```

---

## 3. Equivalências em Outras Linguagens

### Java / Spring Batch

| Dependência Python | Equivalente Java | Maven Artifact |
|---|---|---|
| `pandas` (DataFrames) | Apache Commons CSV + POI + Stream API | `org.apache.poi:poi-ooxml` |
| `pandas` (pivot tables) | Apache Spark / custom aggregation | — |
| `openpyxl` / `xlrd` | Apache POI (HSSF/XSSF) | `org.apache.poi:poi-ooxml:5.x` |
| `xlsxwriter` | Apache POI XSSF | `org.apache.poi:poi-ooxml:5.x` |
| `sqlite3` | JDBC SQLite | `org.xerial:sqlite-jdbc:3.x` |
| `pyyaml` | SnakeYAML | `org.yaml:snakeyaml:2.x` |
| `configparser` | java.util.Properties | stdlib |
| `numpy` | Apache Commons Math | `org.apache.commons:commons-math3` |
| `xml.etree.ElementTree` | javax.xml.parsers / JAXB | stdlib |
| `gzip` | java.util.zip.GZIPOutputStream | stdlib |
| `datetime` | java.time.LocalDateTime | stdlib |
| Pipeline orchestration | Spring Batch | `org.springframework.batch:spring-batch-core` |
| DataFrame-like | Tablesaw | `tech.tablesaw:tablesaw-core` |

### Rust

| Dependência Python | Equivalente Rust | Crate |
|---|---|---|
| `pandas` | Polars | `polars = "0.x"` |
| `openpyxl` / Excel read | calamine | `calamine = "0.x"` |
| `xlsxwriter` | rust_xlsxwriter | `rust_xlsxwriter = "0.x"` |
| `sqlite3` | rusqlite | `rusqlite = "0.x"` |
| `pyyaml` | serde_yaml | `serde_yaml = "0.x"` |
| `configparser` | config-rs | `config = "0.x"` |
| `gzip` | flate2 | `flate2 = "1.x"` |
| `xml.etree` | quick-xml | `quick-xml = "0.x"` |

### Go

| Dependência Python | Equivalente Go | Pacote |
|---|---|---|
| `pandas` | gota/dataframe | `github.com/go-gota/gota` |
| Excel read | excelize | `github.com/xuri/excelize/v2` |
| Excel write | excelize | `github.com/xuri/excelize/v2` |
| `sqlite3` | mattn/go-sqlite3 | `github.com/mattn/go-sqlite3` |
| `pyyaml` | gopkg.in/yaml.v3 | stdlib-like |
| `configparser` | viper | `github.com/spf13/viper` |
| `gzip` | compress/gzip | stdlib |
| `xml.etree` | encoding/xml | stdlib |

### Node.js / TypeScript

| Dependência Python | Equivalente Node.js | Pacote npm |
|---|---|---|
| `pandas` | danfojs | `danfojs-node` |
| Excel read | xlsx (SheetJS) | `xlsx` |
| Excel write | exceljs | `exceljs` |
| `sqlite3` | better-sqlite3 | `better-sqlite3` |
| `pyyaml` | js-yaml | `js-yaml` |
| `configparser` | dotenv + config | `config` |
| `gzip` | zlib | stdlib (Node.js) |
| `xml.etree` | fast-xml-parser | `fast-xml-parser` |

### C++

| Dependência Python | Equivalente C++ | Biblioteca |
|---|---|---|
| `pandas` | xtensor + custom | `xtensor` |
| Excel read | libxlsxwriter / xlnt | `xlnt` |
| Excel write | libxlsxwriter | `libxlsxwriter` |
| `sqlite3` | SQLiteCpp | `SQLiteCpp` |
| `pyyaml` | yaml-cpp | `yaml-cpp` |
| `configparser` | libconfig | `libconfig` |
| `gzip` | zlib | `zlib` |
| `xml.etree` | pugixml | `pugixml` |

---

## 4. Versões Recomendadas para Produção

```toml
# requirements.txt (PDW 10.1.0)
pandas>=1.5.0,<3.0.0
numpy>=1.23.0,<3.0.0
openpyxl>=3.0.0
xlrd>=2.0.0
xlsxwriter>=3.0.0
PyYAML>=6.0.0

# Opcionais para novos_relatorios
matplotlib>=3.6.0
seaborn>=0.12.0
scipy>=1.9.0
fpdf2>=2.7.0
```

---

## 5. Versões Mínimas de Python

| Funcionalidade usada | Versão mínima Python |
|---|---|
| f-strings | 3.6+ |
| `ET.indent()` | 3.9+ |
| `dict` preserva inserção | 3.7+ |
| `dataclasses` (não usados, mas recomendados para reescrita) | 3.7+ |
| Walrus operator `:=` (não usado) | 3.8+ |
| **Recomendado para PDW** | **3.9+** |

---

## 6. Dependências de Infraestrutura (não-Python)

| Componente | Descrição | Versão |
|---|---|---|
| SQLite3 | Banco de dados embutido | ≥ 3.35.0 (para `RETURNING`) |
| Sistema de arquivos | Necessário para log, input, output, db | qualquer |
| Permissões de escrita | DIR_OUT, DATABASE_DIR, LOG_DIR | obrigatório |
| Microsoft Excel format | .xlsx (OOXML) | Office 2007+ |

---

## 7. Dependências de Desenvolvimento (não-runtime)

| Ferramenta | Propósito | Versão |
|---|---|---|
| `pyinstaller` | Gera executável standalone | ≥ 5.0 |
| `pytest` | Testes unitários | ≥ 7.0 |
| `pytest-cov` | Cobertura de código | ≥ 4.0 |
