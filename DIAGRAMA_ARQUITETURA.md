# DIAGRAMA_ARQUITETURA.md
## Personal Data Warehouse — Diagramas de Arquitetura
### Versão 10.1.0

---

## 1. Visão de Alto Nível — Fluxo de Dados

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                          PERSONAL DATA WAREHOUSE                                ║
║                               Fluxo Principal                                   ║
╚══════════════════════════════════════════════════════════════════════════════════╝

  ENTRADA                    PROCESSAMENTO                      SAÍDA
  ───────                    ──────────────                     ─────

  PDW.xlsx              ┌─────────────────────┐         PDW_REPORTS.v2.xlsx
  ┌───────────┐         │                     │         ┌────────────────────┐
  │  GUIDING  │────────▶│    ETL ENGINE       │────────▶│  Múltiplas abas    │
  │  PARCEL.  │         │   (pdw/etl/)        │         │  (queries do YAML) │
  │  TIPOS    │         │                     │         └────────────────────┘
  │  Conta_A  │         └──────────┬──────────┘
  │  Conta_B  │                    │                    LANCAMENTOS_GERAIS.FULL.v2
  │  Conta_C  │                    ▼                    ┌────────────────────┐
  └───────────┘         ┌─────────────────────┐         │  .csv (UTF-8-sig)  │
                        │   PDW.db (SQLite3)  │────────▶│  .json.gz          │
  PersonalDataWareHouse │                     │         │  .xml.gz           │
  .cfg                  │  LANCAMENTOS_GERAIS │         └────────────────────┘
  ┌───────────┐         │  HistoricoGeral     │
  │  [DIR]    │────────▶│  HistoricoAnual     │         PDW.lnx.log
  │  [FILES]  │         │  Resumidos          │         ┌────────────────────┐
  │  [SETTINGS│         │  contagem_diaria    │────────▶│  execution log     │
  └───────────┘         │  (+ tabelas dinâm.) │         │  (append, por run) │
                        └─────────────────────┘         └────────────────────┘
  PDW_QUERIES.yaml
  ┌───────────┐
  │ queries   │────────────────────────────────────────▶ (incluso no xlsx)
  │ _padrao   │
  │ _gera_hist│
  └───────────┘
```

---

## 2. Diagrama de Componentes (C4 — Nível 2)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SISTEMA PDW                                        │
│                                                                             │
│  ┌──────────────────────┐         ┌──────────────────────────────────────┐  │
│  │   ENTRY POINTS       │         │         CORE PIPELINE                │  │
│  │                      │         │                                      │  │
│  │  PersonalDataWareHouse│────────▶│  pdw/core/orchestrator.py           │  │
│  │  .py (facade)        │         │  ┌─────────────────────────────────┐ │  │
│  │                      │         │  │  run_pipeline(param_file)       │ │  │
│  │  pdw/main.py         │         │  │  1. load_config()               │ │  │
│  │  RunPDW.sh           │         │  │  2. open_log()                  │ │  │
│  │  RunPDW.ps1          │         │  │  3. new_data_loader() ?         │ │  │
│  │  Run_PDW.bat         │         │  │  4. create_pivot_history() ?    │ │  │
│  └──────────────────────┘         │  │  5. create_dinamic_reports() ?  │ │  │
│                                   │  │  6. monthly_summaries()  ?      │ │  │
│  ┌──────────────────────┐         │  │  7. general_entries_...() ?     │ │  │
│  │  CONFIGURATION       │         │  │  8. split_paymnt_resume() ?     │ │  │
│  │                      │         │  │  9. xlsx_report_generator() ?   │ │  │
│  │  .cfg (INI)  ────────┼─────────┼─▶│  10. finalize_log()             │ │  │
│  │  .yaml (SQL) ────────┼─────────┼─▶│  (* = condicional por flag)     │ │  │
│  └──────────────────────┘         │  └─────────────────────────────────┘ │  │
│                                   └──────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      CAMADAS DE SERVIÇO                             │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │   ETL       │  │ ANALYTICS   │  │  REPORTS     │  │  UTILS   │ │   │
│  │  │             │  │             │  │              │  │          │ │   │
│  │  │ loader.py   │  │ pivot.py    │  │ exporter.py  │  │compress. │ │   │
│  │  │ sanitizer.py│  │ totals.py   │  │ xlsx_gen.py  │  │xml_utils │ │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  │localiz. │ │   │
│  │         │                │                │           └──────────┘ │   │
│  │         ▼                ▼                ▼                        │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │                  DATABASE (SQLite3)                         │  │   │
│  │  │            pdw/database/operations.py                       │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Fluxo Detalhado do ETL

```
new_data_loader(...)
       │
       ▼
  [1] sqlite3.connect(db_file)
       │
       ▼
  [2] read_guiding_sheet(excel_file, "GUIDING")
       │    └──▶ pd.ExcelFile(excel).parse("GUIDING")
       │         Retorna: DataFrame com TABLE_NAME, ACCOUNTING, LOADABLE
       ▼
  [3] table_droppator(cursor, "LANCAMENTOS_GERAIS")
       │    └──▶ DROP TABLE IF EXISTS LANCAMENTOS_GERAIS
       ▼
  [4] Para cada linha do GUIDING:
       │
       ├── LOADABLE == 'X' e ACCOUNTING == 'X'
       │    └──▶ process_accounting_sheet(excel, sheet, origem)
       │              └──▶ pd.read_excel(excel, sheet)
       │                   └──▶ seleciona: Data, TIPO, DESCRICAO, Credito, Debito
       │                   └──▶ adiciona coluna Origem = sheet
       │                   └──▶ retorna (DataFrame, n_linhas)
       │              └──▶ all_entries.append(df)
       │
       └── LOADABLE == 'X' e ACCOUNTING != 'X'
            └──▶ process_non_accounting_sheet(excel, sheet, conn)
                      └──▶ pd.read_excel → df.to_sql(sheet, conn)
       ▼
  [5] pd.concat(all_entries) → general_entries_df
       ▼
  [6] sanitize_entries_dataframe(df, remove_nulls=True)
       │    ├── dropna(['TIPO', 'Data'])
       │    ├── add_temporal_columns(df)
       │    │       insert: DIA_SEMANA, Mes, Ano, MES_EXTENSO, AnoMes
       │    ├── sanitize_financial_columns(df)
       │    │       Credito/Debito → pd.to_numeric().round(2).fillna(0)
       │    ├── enrich_dataframe_with_dates(df)
       │    │       MES_EXTENSO ← dt.month.map(get_month_names())
       │    │       DIA_SEMANA  ← dt.dayofweek.map(get_weekday_names())
       │    │       Mes, Ano, AnoMes ← dt.strftime()
       │    └── clean_description_text(df['DESCRICAO'])
       │             ;,→|  ∴→.'.  ś→s  "→''  strip()
       ▼
  [7] save_dataframe_to_database(df, conn, "LANCAMENTOS_GERAIS")
       │    └──▶ sort_by_date → df.to_sql("LANCAMENTOS_GERAIS", conn)
       ▼
  [8] conn.commit()
       ▼
  [9] data_correjeitor(cursor, types_sheet, entries_table, ...)
       │    ├── (opcional) cria discarted_data com registros nulos
       │    ├── DELETE FROM TiposLancamentos WHERE Código/Descrição IS NULL
       │    ├── DELETE FROM Parcelamentos WHERE DATA/Tipo IS NULL
       │    ├── DROP VIEW IF EXISTS Origens
       │    └── CREATE VIEW Origens AS SELECT TABLE_NAME FROM GUIDING WHERE LOADABLE='X' AND ACCOUNTING='X'
       ▼
  [10] conn.commit() → conn.close()
```

---

## 4. Fluxo de Geração de Relatórios

```
xlsx_report_generator(...)
       │
       ▼
  [1] yaml.safe_load(yaml_queries_file)
       │    Carrega: queries_gera_hist[], queries_padrao[]
       ▼
  [2] totalizador_diario(db, LANCAMENTOS_GERAIS, contagem_diaria)
       │    └──▶ groupby('Data').size().cumsum() → to_sql
       ▼
  [3] sqlite3.connect(db_file)
       ▼
  [4] Monta lista_consultas:
       │
       ├── if CREATE_PIVOT=True:
       │    └── queries_gera_hist (com placeholders {full_hist}, {anual_hist}, ...)
       │
       ├── queries_padrao (sempre)
       │
       └── if CREATE_PIVOT=True e RUN_DINAMIC_REPORT=True:
            └── SELECT * FROM {dyn_rep_tab} → para cada linha: SELECT * FROM DEST_TABLE
       ▼
  [5] pd.ExcelWriter(file_full_path, engine='xlsxwriter')
       │    (se RPT_SINGLE_FILE=True)
       ▼
  [6] Para cada (sql, sheet_name):
       │    └──▶ pd.read_sql(sql, connection)
       │    └──▶ df.to_excel(writer, sheet_name=sheet_name)
       ▼
  [7] xlsx_writer.close() → connection.close()
```

---

## 5. Schema do Banco de Dados SQLite

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PDW.db — Schema Completo                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LANCAMENTOS_GERAIS (tabela principal)                                      │
│  ┌──────────────┬─────────────────────────────────────────────────────┐    │
│  │ Data         │ TEXT (YYYY-MM-DD) — data da movimentação            │    │
│  │ DIA_SEMANA   │ TEXT — nome do dia em PT-BR                         │    │
│  │ TIPO         │ TEXT — categoria (de TiposLancamentos)              │    │
│  │ DESCRICAO    │ TEXT — descrição da movimentação                    │    │
│  │ Credito      │ REAL — valor creditado (≥0)                        │    │
│  │ Debito       │ REAL — valor debitado (≥0)                         │    │
│  │ Mes          │ TEXT — "MM"                                         │    │
│  │ Ano          │ TEXT — "YYYY"                                       │    │
│  │ MES_EXTENSO  │ TEXT — ex: "01-Janeiro"                            │    │
│  │ AnoMes       │ TEXT — "YYYY/MM"                                   │    │
│  │ Origem       │ TEXT — nome da aba Excel de origem                 │    │
│  └──────────────┴─────────────────────────────────────────────────────┘    │
│                                                                             │
│  GUIDING (configuração de carga)                                            │
│  ┌──────────────┬─────────────────────────────────────────────────────┐    │
│  │ TABLE_NAME   │ TEXT — nome da aba Excel                            │    │
│  │ ACCOUNTING   │ TEXT — 'X' se é contábil                           │    │
│  │ LOADABLE     │ TEXT — 'X' se deve ser carregada                   │    │
│  └──────────────┴─────────────────────────────────────────────────────┘    │
│                                                                             │
│  TiposLancamentos (categorias)                                              │
│  ┌──────────────┬─────────────────────────────────────────────────────┐    │
│  │ Código       │ TEXT — código interno                               │    │
│  │ Descrição    │ TEXT — nome exibido                                 │    │
│  └──────────────┴─────────────────────────────────────────────────────┘    │
│                                                                             │
│  PARCELAMENTOS (compras parceladas)                                         │
│  ┌──────────────┬─────────────────────────────────────────────────────┐    │
│  │ Data         │ TEXT — data da parcela                              │    │
│  │ Tipo Lançamento│TEXT — categoria                                   │    │
│  │ Debito       │ REAL — valor da parcela                            │    │
│  │ (outras)     │ — colunas da planilha Excel                        │    │
│  └──────────────┴─────────────────────────────────────────────────────┘    │
│                                                                             │
│  HistoricoGeral / HistoricoGeral_QTD (pivot mensal)                         │
│  ┌──────────────┬─────────────────────────────────────────────────────┐    │
│  │ AnoMes       │ TEXT — "YYYY/MM" (índice)                          │    │
│  │ <Categoria1> │ REAL — soma/contagem de débitos da categoria        │    │
│  │ <Categoria2> │ REAL — (colunas dinâmicas = TiposLancamentos)      │    │
│  │ ...          │                                                     │    │
│  └──────────────┴─────────────────────────────────────────────────────┘    │
│                                                                             │
│  HistoricoAnual / HistoricoAnual_QTD (pivot anual)                          │
│  ┌──────────────┬─────────────────────────────────────────────────────┐    │
│  │ Ano          │ TEXT — "YYYY" (índice)                              │    │
│  │ <Categoria>  │ REAL — (mesma estrutura do mensal)                 │    │
│  └──────────────┴─────────────────────────────────────────────────────┘    │
│                                                                             │
│  contagem_diaria (progresso diário)                                         │
│  ┌──────────────┬─────────────────────────────────────────────────────┐    │
│  │ Data         │ TEXT                                                │    │
│  │ Contagem Acumulada│INTEGER — total acumulado até esta data        │    │
│  └──────────────┴─────────────────────────────────────────────────────┘    │
│                                                                             │
│  Resumo_Parcelamentos / Resumido_In_Out / _ANUAL / _FULL                    │
│  (tabelas de sumarização — ver INVENTARIO_API.md para schema completo)      │
│                                                                             │
│  VIEW: Origens                                                              │
│  ┌──────────────┬─────────────────────────────────────────────────────┐    │
│  │ nome         │ TEXT — TABLE_NAME de GUIDING onde LOADABLE='X'      │    │
│  │              │        e ACCOUNTING='X'                             │    │
│  └──────────────┴─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Grafo de Dependências entre Módulos

```
                    pdw/__init__.py
                         │
                         ▼
              pdw/config/loader.py
                         │
                    ┌────┴────────────────────────┐
                    ▼                             ▼
         pdw/infrastructure/           pdw/core/orchestrator.py
              logging.py                         │
                                    ┌────────────┼────────────┐
                                    ▼            ▼            ▼
                              pdw/etl/    pdw/analytics/ pdw/reports/
                               loader.py   pivot.py      exporter.py
                                  │        totals.py     xlsx_generator.py
                                  │            │              │
                             ┌────┤            │              │
                             ▼    ▼            │              │
                      sanitizer. database/     │              │
                      py         operations.py │              │
                          │                    │              │
                          ▼                    ▼              ▼
                    pdw/utils/           pdw/analytics/  pdw/utils/
                    localization.py       totals.py      compression.py
                                                         xml_utils.py

Sentido das setas: "depende de"
Nenhum ciclo presente.
```

---

## 7. Diagrama de Sequência — Execução Completa

```
Usuário/Scheduler
     │
     │  python PersonalDataWareHouse.py [config.cfg]
     ▼
PersonalDataWareHouse.py (shim)
     │  from pdw.main import main; main(param_file)
     ▼
pdw/main.py::main()
     │  run_pipeline(param_file)
     ▼
pdw/core/orchestrator.py::run_pipeline()
     │
     ├──▶ config/loader.py::load_config()  ──▶  configparser.read(cfg)
     │         │                                      │
     │         └─ retorna dict cfg                    └─▶ exit(1) se versão errada
     │
     ├──▶ infrastructure/logging.py::open_log()
     │         └─ retorna (file_handle, n_runs, last_date)
     │
     ├── [se RUN_DATA_LOADER=True]
     │    └──▶ etl/loader.py::new_data_loader()
     │              ├──▶ database/operations.py::table_droppator()
     │              ├──▶ etl/loader.py::read_guiding_sheet()
     │              ├──▶ [para cada sheet] process_accounting_sheet() / process_non_accounting_sheet()
     │              ├──▶ etl/sanitizer.py::sanitize_entries_dataframe()
     │              │        ├──▶ utils/localization.py::get_month_names()
     │              │        └──▶ utils/localization.py::get_weekday_names()
     │              ├──▶ database/operations.py::save_dataframe_to_database()
     │              └──▶ etl/sanitizer.py::data_correjeitor()
     │                        └──▶ database/operations.py::table_droppator()
     │
     ├── [se CREATE_PIVOT=True]
     │    ├──▶ analytics/pivot.py::create_pivot_history()
     │    └── [se RUN_DINAMIC_REPORT=True]
     │         └──▶ analytics/pivot.py::create_dinamic_reports()
     │
     ├── [se RUN_REPORTS=True]
     │    ├──▶ analytics/totals.py::monthly_summaries()
     │    ├──▶ reports/exporter.py::general_entries_file_exportator()
     │    │        ├──▶ utils/compression.py::gzip_compressor()
     │    │        └──▶ utils/xml_utils.py::dataframe_to_xml()
     │    ├──▶ analytics/totals.py::split_paymnt_resume()
     │    └──▶ reports/xlsx_generator.py::xlsx_report_generator()
     │              └──▶ analytics/totals.py::totalizador_diario()
     │
     └──▶ infrastructure/logging.py::finalize_log()
```

---

## 8. Diagrama de Estado do Pipeline

```
                    ┌─────────────┐
                    │   INÍCIO    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  LER CONFIG │◀── exit(1) se arquivo não existe
                    └──────┬──────┘◀── exit(1) se versão errada
                           │       ◀── exit(1) se diretório não existe
                    ┌──────▼──────┐
                    │  ABRIR LOG  │
                    └──────┬──────┘
                           │
                  ┌────────┴────────┐
                  │ RUN_DATA_LOADER?│
                  └────────┬────────┘
              Sim ◀─────────┤─────────▶ Não
               │            │            │
               ▼            │            │
        ┌──────────┐         │            │
        │  LOADER  │         │            │
        └─────┬────┘         │            │
              │              │            │
              └──────────────┤            │
                             │◀───────────┘
                    ┌────────┴────────┐
                    │ CREATE_PIVOT?   │
                    └────────┬────────┘
              Sim ◀───────────┤──────────▶ Não
               │             │              │
               ▼             │              │
        ┌──────────┐          │              │
        │  PIVOT   │          │              │
        └─────┬────┘          │              │
              │               │              │
              └───────────────┤              │
                             │◀─────────────┘
                    ┌────────┴────────┐
                    │ RUN_REPORTS?    │
                    └────────┬────────┘
              Sim ◀───────────┤──────────▶ Não
               │             │              │
               ▼             │              │
        ┌──────────┐          │              │
        │ REPORTS  │          │              │
        └─────┬────┘          │              │
              │               │              │
              └───────────────┤              │
                             │◀─────────────┘
                    ┌────────┴────────┐
                    │ FECHAR LOG      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    FIM (exit 0) │
                    └─────────────────┘
```
