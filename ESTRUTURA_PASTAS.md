# ESTRUTURA_PASTAS.md
## Personal Data Warehouse — Estrutura de Diretórios Proposta
### Versão alvo: 10.1.0

---

## Estrutura Proposta

```
pdw/                                  ← Pacote raiz (substitui o arquivo monolítico)
│
├── __init__.py                       ← Expõe versão do pacote: __version__ = "10.1.0"
│
├── main.py                           ← Ponto de entrada (antigo bloco __main__)
│                                        Responsabilidade: apenas invoca orchestrator
│
├── config/
│   ├── __init__.py
│   └── loader.py                     ← Leitura e validação do .cfg
│                                        Extrai: bloco de config reading de main()
│                                        Expõe: load_config(param_file) → dict
│
├── core/
│   ├── __init__.py
│   └── orchestrator.py               ← Lógica de orquestração do pipeline
│                                        Extrai: main() sem o bloco de config e log
│                                        Expõe: run_pipeline(config: dict)
│
├── infrastructure/
│   ├── __init__.py
│   └── logging.py                    ← Gerenciamento do arquivo de log
│                                        Extrai: blocos "begin/end of log block" de main()
│                                        Expõe: open_log(path), write_log(...), close_log(...)
│
├── etl/
│   ├── __init__.py
│   ├── loader.py                     ← Orquestrador ETL + leitura de Excel
│   │                                    Extrai: new_data_loader, read_guiding_sheet,
│   │                                            process_accounting_sheet,
│   │                                            process_non_accounting_sheet
│   └── sanitizer.py                  ← Transformação e limpeza de dados
│                                        Extrai: sanitize_entries_dataframe,
│                                                add_temporal_columns,
│                                                enrich_dataframe_with_dates,
│                                                sanitize_financial_columns,
│                                                clean_description_text,
│                                                sort_dataframe_by_date,
│                                                data_correjeitor
│
├── database/
│   ├── __init__.py
│   └── operations.py                 ← Operações de infraestrutura de banco
│                                        Extrai: table_droppator,
│                                                save_dataframe_to_database
│
├── analytics/
│   ├── __init__.py
│   ├── pivot.py                      ← Tabelas pivot e relatórios dinâmicos
│   │                                    Extrai: create_pivot_history,
│   │                                            create_dinamic_reports
│   └── totals.py                     ← Totalizações e sumarizações
│                                        Extrai: totalizador_diario,
│                                                monthly_summaries,
│                                                split_paymnt_resume
│
├── reports/
│   ├── __init__.py
│   ├── xlsx_generator.py             ← Gerador de Excel via YAML
│   │                                    Extrai: xlsx_report_generator
│   └── exporter.py                   ← Exportação multi-formato
│                                        Extrai: general_entries_file_exportator
│
└── utils/
    ├── __init__.py
    ├── compression.py                ← Utilitário de compressão
    │                                    Extrai: gzip_compressor
    ├── xml_utils.py                  ← Utilitário de conversão XML
    │                                    Extrai: dataframe_to_xml
    └── localization.py               ← Dicionários de localização PT-BR
                                         Extrai: get_month_names, get_weekday_names
                                         Oportunidade: converter para constantes de módulo
```

---

## Arquivos de Suporte (permanecem na raiz)

```
PersonalDataWareHouse.cfg             ← Arquivo de configuração (sem alterações)
PDW_QUERIES.yaml                      ← Queries SQL para relatórios (sem alterações)
RunPDW.sh                             ← Shell script de execução (ajustar path do .py)
RunPDW.ps1                            ← PowerShell script (ajustar path do .py)
Run_PDW.bat                           ← Batch script (ajustar path do .py)
InstalaDependencias.sh                ← Instalador de dependências (sem alterações)
MySql_Loader.sh                       ← Script auxiliar MySQL (sem alterações)
```

---

## Diagrama de Dependências entre Módulos

```
main.py
  └── core/orchestrator.py
        ├── config/loader.py
        ├── infrastructure/logging.py
        ├── etl/loader.py
        │     ├── etl/sanitizer.py
        │     │     ├── utils/localization.py
        │     │     └── database/operations.py  ← table_droppator via data_correjeitor
        │     └── database/operations.py
        ├── analytics/pivot.py
        ├── analytics/totals.py
        ├── reports/xlsx_generator.py
        │     └── analytics/totals.py           ← totalizador_diario
        └── reports/exporter.py
              ├── utils/compression.py
              └── utils/xml_utils.py
```

**Observação**: Nenhum ciclo de dependências existe no grafo proposto acima.
O único ponto de atenção é `database/operations.py` ser usado tanto por `etl/loader.py`
diretamente quanto internamente via `etl/sanitizer.py` (`data_correjeitor` → `table_droppator`).
Isso é aceitável — ambos são consumidores de uma camada mais baixa.

---

## Compatibilidade de Entrada (entry points)

O arquivo de entrada `main.py` na raiz do pacote `pdw/` deve ser invocado como:

```bash
# Modo atual (preservado — para compatibilidade com RunPDW.sh)
python PersonalDataWareHouse.py
python PersonalDataWareHouse.py /path/to/custom.cfg

# Modo novo (v10.1.0)
python -m pdw
python -m pdw /path/to/custom.cfg
```

Para manter compatibilidade total com `RunPDW.sh` durante a transição,
o arquivo `PersonalDataWareHouse.py` original pode permanecer como um **shim** que apenas importa e invoca `pdw.main`:

```python
# PersonalDataWareHouse.py — shim de compatibilidade (NÃO MODIFICA LÓGICA)
from pdw.main import main
import sys
if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) == 2 else "")
```

---

## Ajuste Necessário no Config

O arquivo `PersonalDataWareHouse.cfg` não precisa de alterações estruturais.
Apenas a versão deverá ser atualizada quando a migração estiver completa:

```ini
[SETTINGS]
CURRENT_VERSION = 10.1.0   ← atualizar apenas após migração completa e validada
```

---

## Estrutura Equivalente em Outras Linguagens

### Java (Maven)

```
pdw-java/
├── pom.xml
└── src/main/
    ├── java/com/pdw/
    │   ├── PdwApplication.java          ← = PersonalDataWareHouse.py (entry point)
    │   ├── config/PdwProperties.java    ← = pdw/config/loader.py
    │   ├── core/BatchConfig.java        ← = pdw/core/orchestrator.py
    │   ├── domain/Lancamento.java       ← entidade principal (sem equivalente Python)
    │   ├── etl/ExcelReader.java         ← = pdw/etl/loader.py
    │   ├── etl/LancamentoProcessor.java ← = pdw/etl/sanitizer.py
    │   ├── database/JdbcWriter.java     ← = pdw/database/operations.py
    │   ├── analytics/PivotBuilder.java  ← = pdw/analytics/pivot.py
    │   ├── analytics/TotalsCalc.java    ← = pdw/analytics/totals.py
    │   ├── reports/ExcelWriter.java     ← = pdw/reports/xlsx_generator.py
    │   ├── reports/Exporter.java        ← = pdw/reports/exporter.py
    │   └── infrastructure/PdwLogger.java← = pdw/infrastructure/logging.py
    └── resources/
        ├── application.properties       ← = PersonalDataWareHouse.cfg
        └── queries/pdw-queries.yml      ← = PDW_QUERIES.yaml
```

### Rust (Cargo)

```
pdw-rust/
├── Cargo.toml
└── src/
    ├── main.rs                  ← = PersonalDataWareHouse.py + pdw/main.py
    ├── config.rs                ← = pdw/config/loader.py
    ├── etl/
    │   ├── mod.rs
    │   ├── loader.rs            ← = pdw/etl/loader.py
    │   └── sanitizer.rs         ← = pdw/etl/sanitizer.py
    ├── database.rs              ← = pdw/database/operations.py
    ├── analytics/
    │   ├── mod.rs
    │   ├── pivot.rs             ← = pdw/analytics/pivot.py
    │   └── totals.rs            ← = pdw/analytics/totals.py
    ├── reports/
    │   ├── mod.rs
    │   ├── exporter.rs          ← = pdw/reports/exporter.py
    │   └── xlsx_generator.rs    ← = pdw/reports/xlsx_generator.py
    └── utils/
        ├── compression.rs       ← = pdw/utils/compression.py
        ├── xml_utils.rs         ← = pdw/utils/xml_utils.py
        └── localization.rs      ← = pdw/utils/localization.py
```

### Go

```
pdw-go/
├── go.mod
├── main.go                      ← = PersonalDataWareHouse.py + pdw/main.py
└── internal/
    ├── config/loader.go         ← = pdw/config/loader.py
    ├── infrastructure/log.go    ← = pdw/infrastructure/logging.py
    ├── etl/
    │   ├── loader.go            ← = pdw/etl/loader.py
    │   └── sanitizer.go         ← = pdw/etl/sanitizer.py
    ├── database/operations.go   ← = pdw/database/operations.py
    ├── analytics/
    │   ├── pivot.go             ← = pdw/analytics/pivot.py
    │   └── totals.go            ← = pdw/analytics/totals.py
    ├── reports/
    │   ├── exporter.go          ← = pdw/reports/exporter.py
    │   └── xlsx_generator.go    ← = pdw/reports/xlsx_generator.py
    └── utils/
        ├── compression.go       ← = pdw/utils/compression.py
        ├── xml.go               ← = pdw/utils/xml_utils.py
        └── localization.go      ← = pdw/utils/localization.py
```

### Node.js / TypeScript

```
pdw-node/
├── package.json
├── tsconfig.json
└── src/
    ├── index.ts                 ← = PersonalDataWareHouse.py + pdw/main.py
    ├── config/loader.ts         ← = pdw/config/loader.py
    ├── infrastructure/logger.ts ← = pdw/infrastructure/logging.py
    ├── etl/
    │   ├── loader.ts            ← = pdw/etl/loader.py
    │   └── sanitizer.ts         ← = pdw/etl/sanitizer.py
    ├── database/operations.ts   ← = pdw/database/operations.py
    ├── analytics/
    │   ├── pivot.ts             ← = pdw/analytics/pivot.py
    │   └── totals.ts            ← = pdw/analytics/totals.py
    ├── reports/
    │   ├── exporter.ts          ← = pdw/reports/exporter.py
    │   └── xlsxGenerator.ts     ← = pdw/reports/xlsx_generator.py
    └── utils/
        ├── compression.ts       ← = pdw/utils/compression.py
        ├── xmlUtils.ts          ← = pdw/utils/xml_utils.py
        └── localization.ts      ← = pdw/utils/localization.py
```

---

## Regras de Nomenclatura por Linguagem

| Elemento | Python (atual) | Java | Rust | Go | Node.js/TS |
|---|---|---|---|---|---|
| Arquivo | `snake_case.py` | `PascalCase.java` | `snake_case.rs` | `snake_case.go` | `camelCase.ts` |
| Função | `snake_case()` | `camelCase()` | `snake_case()` | `camelCase()` | `camelCase()` |
| Constante | `UPPER_CASE` | `UPPER_CASE` | `UPPER_CASE` | `UPPER_CASE` | `UPPER_CASE` |
| Parâmetro | `snake_case` | `camelCase` | `snake_case` | `camelCase` | `camelCase` |
| Classe/struct | — | `PascalCase` | `PascalCase` | `PascalCase` | `PascalCase` |
