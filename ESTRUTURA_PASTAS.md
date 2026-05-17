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
