# DIAGRAMA_ARQUITETURA.md
## Personal Data Warehouse — Diagramas de Arquitetura Mermaid
### Versão 10.1.0

> Todos os diagramas usam sintaxe **Mermaid** e são renderizados automaticamente no GitHub.

---

## 1. Diagrama de Módulos

Estrutura completa do pacote `pdw/` agrupada por responsabilidade.

```mermaid
graph LR
    subgraph ENTRY["Entry Points"]
        FAC["PersonalDataWareHouse.py\n(facade)"]
        PDWM["pdw/main.py"]
        SH["RunPDW.sh / RunPDW.ps1 / Run_PDW.bat"]
    end

    subgraph CORE_G["Core"]
        ORCH["pdw/core/orchestrator.py"]
        CFG["pdw/config/loader.py"]
        LOG["pdw/infrastructure/logging.py"]
        INIT["pdw/__init__.py\n__version__ = 10.1.0"]
    end

    subgraph ETL_G["ETL"]
        ETLL["pdw/etl/loader.py"]
        ETLS["pdw/etl/sanitizer.py"]
        DBOP["pdw/database/operations.py"]
    end

    subgraph ANA_G["Analytics"]
        PIV["pdw/analytics/pivot.py"]
        TOT["pdw/analytics/totals.py"]
    end

    subgraph REP_G["Reports"]
        EXP["pdw/reports/exporter.py"]
        XLS["pdw/reports/xlsx_generator.py"]
        NR["pdw/reports/novos_relatorios.py"]
    end

    subgraph UTIL_G["Utils"]
        COMP["pdw/utils/compression.py"]
        XML["pdw/utils/xml_utils.py"]
        LOC["pdw/utils/localization.py"]
        TR["pdw/utils/transient_data.py"]
    end

    subgraph COMPAT_G["Compat + Legacy"]
        COM["pdw/compat/__init__.py"]
        LEG["legacy/PersonalDataWareHouse.9.11.2.py"]
    end

    SH --> FAC
    FAC --> PDWM
    PDWM --> ORCH
    ORCH --> CFG
    ORCH --> LOG
    ORCH --> ETLL
    ORCH --> PIV
    ORCH --> TOT
    ORCH --> EXP
    ORCH --> XLS
    ETLL --> ETLS
    ETLL --> DBOP
    ETLS --> LOC
    ETLS --> DBOP
    EXP --> COMP
    EXP --> XML
    XLS --> TOT
    CFG --> INIT
    COM -.-> ORCH
```

---

## 2. Diagrama de Dependências

Grafo de importações entre módulos. Setas indicam "importa de". Sem ciclos.

```mermaid
graph TD
    MAIN["pdw/main.py"]
    ORCH["pdw/core/orchestrator.py"]
    CFG["pdw/config/loader.py"]
    INIT["pdw/__init__.py"]
    LOG["pdw/infrastructure/logging.py"]
    LOADER["pdw/etl/loader.py"]
    SANIT["pdw/etl/sanitizer.py"]
    OPS["pdw/database/operations.py"]
    PIV["pdw/analytics/pivot.py"]
    TOT["pdw/analytics/totals.py"]
    EXP["pdw/reports/exporter.py"]
    XLS["pdw/reports/xlsx_generator.py"]
    NR["pdw/reports/novos_relatorios.py"]
    COMP["pdw/utils/compression.py"]
    XML["pdw/utils/xml_utils.py"]
    LOC["pdw/utils/localization.py"]

    MAIN --> ORCH
    ORCH --> CFG
    ORCH --> LOG
    ORCH --> LOADER
    ORCH --> PIV
    ORCH --> TOT
    ORCH --> EXP
    ORCH --> XLS
    CFG --> INIT
    LOADER --> SANIT
    LOADER --> OPS
    SANIT --> LOC
    SANIT --> OPS
    EXP --> COMP
    EXP --> XML
    XLS --> TOT

    style INIT fill:#f9f,stroke:#333
    style ORCH fill:#bbf,stroke:#333
    style OPS fill:#bfb,stroke:#333
```

---

## 3. Diagrama de Fluxo de Execução

Pipeline completo com todas as ramificações condicionais.

```mermaid
flowchart TD
    A([Início]) --> CLI["CLI: python PersonalDataWareHouse.py"]
    CLI --> PDW_MAIN["pdw/main.py :: main()"]
    PDW_MAIN --> PIPE["orchestrator.py :: run_pipeline()"]

    PIPE --> LCFG["load_config(param_file)"]
    LCFG --> VER{Versão\ncompatível?}
    VER -- Não --> E1([exit 1])
    VER -- Sim --> DIRS{Diretórios\nexistem?}
    DIRS -- Não --> E2([exit 1])
    DIRS -- Sim --> OPLOG["open_log()"]

    OPLOG --> MT{MULTITHREADING\n= True?}
    MT -- Sim --> E3([exit 1])
    MT -- Não --> RLD{RUN_DATA\nLOADER?}

    RLD -- Sim --> ETL["new_data_loader()"]
    ETL --> READ["read_guiding_sheet()"]
    READ --> LOOP["Para cada aba no GUIDING"]
    LOOP --> ACCNT{ACCOUNTING\n= X?}
    ACCNT -- Sim --> PACC["process_accounting_sheet()"]
    ACCNT -- Não --> PNACC["process_non_accounting_sheet()"]
    PACC --> CONCAT["pd.concat(all_entries)"]
    PNACC --> CONCAT
    CONCAT --> SANIT["sanitize_entries_dataframe()"]
    SANIT --> SAVDB["save_dataframe_to_database()"]
    SAVDB --> CORR["data_correjeitor()"]
    CORR --> PIV_Q{CREATE\nPIVOT?}
    RLD -- Não --> PIV_Q

    PIV_Q -- Sim --> PIVO["create_pivot_history()"]
    PIVO --> DIN_Q{RUN_DINAMIC\nREPORT?}
    DIN_Q -- Sim --> DINR["create_dinamic_reports()"]
    DINR --> RPT_Q{RUN\nREPORTS?}
    DIN_Q -- Não --> RPT_Q
    PIV_Q -- Não --> RPT_Q

    RPT_Q -- Sim --> SUMM["monthly_summaries()"]
    SUMM --> EXPRT["general_entries_file_exportator()"]
    EXPRT --> SPLIT["split_paymnt_resume()"]
    SPLIT --> XLSX["xlsx_report_generator()"]
    XLSX --> FLOG["finalize_log()"]
    RPT_Q -- Não --> FLOG

    FLOG --> DONE([exit 0])
```

---

## 4. Diagrama de Integração Externa

Todas as dependências de arquivos e sistemas externos ao processo PDW.

```mermaid
flowchart LR
    subgraph INPUT["Entradas"]
        EXCEL["PDW.xlsx\nArquivo Excel de entrada"]
        CFG_F["PersonalDataWareHouse.cfg\nConfiguração INI"]
        YAML_F["PDW_QUERIES.yaml\nQueries SQL para relatórios"]
    end

    subgraph PROCESS["Personal Data Warehouse"]
        direction TB
        ETL_P["ETL Engine\npdw/etl/loader.py\npdw/etl/sanitizer.py"]
        DB_P[("PDW.db\nSQLite3")]
        ANA_P["Analytics Engine\npdw/analytics/"]
        REP_P["Report Engine\npdw/reports/"]
    end

    subgraph OUTPUT["Saídas"]
        XLSX_O["PDW_REPORTS.v2.xlsx\nRelatório principal"]
        CSV_O["*.YYYYMMDD.HHMMSS.csv\nExportação CSV UTF-8"]
        JSON_O["*.YYYYMMDD.HHMMSS.json.gz\nExportação JSON gzip"]
        XML_O["*.YYYYMMDD.HHMMSS.xml.gz\nExportação XML gzip"]
        LOG_O["PDW.lnx.log\nLog de execução pipe-delimitado"]
    end

    EXCEL --> ETL_P
    CFG_F --> ETL_P
    CFG_F --> REP_P
    YAML_F --> REP_P
    ETL_P --> DB_P
    DB_P --> ANA_P
    ANA_P --> DB_P
    DB_P --> REP_P
    REP_P --> XLSX_O
    REP_P --> CSV_O
    REP_P --> JSON_O
    REP_P --> XML_O
    ETL_P --> LOG_O
    REP_P --> LOG_O
```

---

## 5. Diagrama de Camadas

Arquitetura em camadas do sistema. Dependências fluem de cima para baixo.

```mermaid
graph TB
    subgraph L1["Camada 1 — Entry Point"]
        EP1["PersonalDataWareHouse.py (facade)"]
        EP2["pdw/main.py"]
        EP3["RunPDW.sh / RunPDW.ps1 / Run_PDW.bat"]
    end

    subgraph L2["Camada 2 — Orquestração"]
        OR1["pdw/core/orchestrator.py\nrun_pipeline()"]
        OR2["pdw/config/loader.py\nload_config()"]
        OR3["pdw/infrastructure/logging.py\nopen_log() / finalize_log()"]
    end

    subgraph L3["Camada 3 — Domínio de Negócio"]
        D1["pdw/etl/loader.py\nnew_data_loader()"]
        D2["pdw/etl/sanitizer.py\nsanitize_entries_dataframe()"]
        D3["pdw/analytics/pivot.py\ncreate_pivot_history()"]
        D4["pdw/analytics/totals.py\nmonthly_summaries()"]
        D5["pdw/reports/exporter.py\ngeneral_entries_file_exportator()"]
        D6["pdw/reports/xlsx_generator.py\nxlsx_report_generator()"]
    end

    subgraph L4["Camada 4 — Infraestrutura Técnica"]
        I1["pdw/database/operations.py\ntable_droppator() / save_dataframe_to_database()"]
        I2["pdw/utils/compression.py\ngzip_compressor()"]
        I3["pdw/utils/xml_utils.py\ndataframe_to_xml()"]
        I4["pdw/utils/localization.py\nget_month_names() / get_weekday_names()"]
    end

    subgraph L5["Camada 5 — Recursos Externos"]
        EX1[("PDW.db — SQLite3")]
        EX2["PDW.xlsx — Excel"]
        EX3["PersonalDataWareHouse.cfg — INI"]
        EX4["PDW_QUERIES.yaml — YAML"]
        EX5["Sistema de Arquivos — log / output"]
    end

    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> L5
```

---

## 6. Diagrama de Logging

Ciclo de vida completo do arquivo de log em uma execução.

```mermaid
sequenceDiagram
    autonumber
    participant Orch as orchestrator.py
    participant LogM as infrastructure/logging.py
    participant FS as Sistema de Arquivos
    participant Pipeline as Pipeline (ETL + Reports)

    Orch->>LogM: open_log(log_file_cfg)
    LogM->>FS: os.path.isfile(log_file_cfg)

    alt Arquivo não existe
        LogM->>FS: open(path, 'w') — cria arquivo
        FS-->>LogM: escreve "New LOG created at DD/MM/YYYY HH:MM:SS"
    end

    LogM->>FS: open(path, 'r+')
    LogM->>FS: sum(1 for line in file) → number_of_runs
    LogM->>FS: readlines()[-1].split('|')[0] → last_run_date
    LogM-->>Orch: (file_handle, number_of_runs, last_run_date)

    Note over Orch: start = time.time()

    Orch->>Pipeline: executa ETL + Analytics + Reports
    Pipeline-->>Orch: concluído

    Note over Orch: elapsed = round(time.time() - start, 2)
    Note over Orch: log_line = "YYYY/MM/DD HH:MM:SS | Version: X | Host: Y | OS: Z | Runs: N | Time: Ts | Last: D"

    Orch->>LogM: finalize_log(file_handle, log_line)
    LogM->>FS: file_handle.write(log_line)
    LogM->>FS: file_handle.close()

    Note over FS: Linha adicionada ao final do arquivo
```

---

## 7. Diagrama de Inicialização da Aplicação

Sequência completa desde a invocação CLI até o início do pipeline.

```mermaid
sequenceDiagram
    autonumber
    participant User as Usuário / Scheduler
    participant Shell as RunPDW.sh
    participant Facade as PersonalDataWareHouse.py
    participant Main as pdw/main.py
    participant Orch as pdw/core/orchestrator.py
    participant Cfg as pdw/config/loader.py
    participant Log as pdw/infrastructure/logging.py
    participant FS as Sistema de Arquivos

    User->>Shell: bash RunPDW.sh [config.cfg]
    Shell->>Shell: verifica lock file (mkdir PDW_lock)
    Shell->>Facade: python PersonalDataWareHouse.py [config.cfg]

    Facade->>Main: from pdw.main import main
    Main->>Orch: run_pipeline(param_file)

    Orch->>Cfg: load_config(param_file)
    Cfg->>FS: open(PersonalDataWareHouse.cfg)
    Cfg->>Cfg: configparser.read_file(cfg)
    Cfg->>Cfg: verifica CURRENT_VERSION == pdw.__version__

    alt Versão incompatível
        Cfg->>User: print("version does not Match")
        Cfg->>Orch: sys.exit(1)
    end

    Cfg-->>Orch: dict com 35 parâmetros de configuração

    Orch->>FS: os.path.exists(DIR_IN)

    alt DIR_IN não existe
        Orch->>User: print("Input Directory does not exists")
        Orch->>User: sys.exit(1)
    end

    Orch->>Log: open_log(log_file_cfg)
    Log-->>Orch: (file_handle, number_of_runs, last_run_date)

    Orch->>Orch: verifica MULTITHREADING

    alt MULTITHREADING = True
        Orch->>User: sys.exit(1)
    end

    Note over Orch: Pipeline pronto para execução
    Orch->>Orch: executa fases conforme flags do .cfg
```

---

## 8. Diagrama de Endpoints

Todas as 26 funções públicas agrupadas por módulo responsável.

```mermaid
classDiagram
    class Orchestrator {
        <<pdw.core.orchestrator>>
        +run_pipeline(param_file)
    }

    class ConfigLoader {
        <<pdw.config.loader>>
        +load_config(param_file) dict
    }

    class LoggingModule {
        <<pdw.infrastructure.logging>>
        +open_log(log_file_cfg) tuple
        +finalize_log(log_file, log_line)
    }

    class EtlLoader {
        <<pdw.etl.loader>>
        +new_data_loader(db, types, entries, origin, guiding, excel, save, udt)
        +read_guiding_sheet(excel, sheet) DataFrame
        +process_accounting_sheet(excel, sheet, col) tuple
        +process_non_accounting_sheet(excel, sheet, conn) int
    }

    class Sanitizer {
        <<pdw.etl.sanitizer>>
        +sanitize_entries_dataframe(df, remove_nulls) DataFrame
        +data_correjeitor(conexao, types, entries, save, udt)
    }

    class DatabaseOps {
        <<pdw.database.operations>>
        +table_droppator(conexao, table_name)
        +save_dataframe_to_database(df, conn, table, sort) int
        +sort_dataframe_by_date(df, ascending) DataFrame
    }

    class PivotAnalytics {
        <<pdw.analytics.pivot>>
        +create_pivot_history(db, entries, full_hist, anual_hist)
        +create_dinamic_reports(db, excel, din_guiding)
    }

    class TotalsAnalytics {
        <<pdw.analytics.totals>>
        +totalizador_diario(db, entries, dayly)
        +monthly_summaries(db, entries, out, name, dir, multi)
        +split_paymnt_resume(db, split, out, name, dir, multi)
    }

    class Exporter {
        <<pdw.reports.exporter>>
        +general_entries_file_exportator(db, entries, name, dir, type, others)
    }

    class XlsxGenerator {
        <<pdw.reports.xlsx_generator>>
        +xlsx_report_generator(db, yaml, name, dir, multi)
    }

    class NovosRelatorios {
        <<pdw.reports.novos_relatorios>>
        +gerar_todos_relatorios_integrado(db, entries, dir)
    }

    class Utils {
        <<pdw.utils>>
        +gzip_compressor(source, dest)
        +dataframe_to_xml(df, root_tag, row_tag) str
        +transient_data_exportator(db, dir, ext, name, table, col)
        +get_month_names() dict
        +get_weekday_names() dict
    }

    Orchestrator --> ConfigLoader : usa
    Orchestrator --> LoggingModule : usa
    Orchestrator --> EtlLoader : usa
    Orchestrator --> PivotAnalytics : usa
    Orchestrator --> TotalsAnalytics : usa
    Orchestrator --> Exporter : usa
    Orchestrator --> XlsxGenerator : usa
    EtlLoader --> Sanitizer : usa
    EtlLoader --> DatabaseOps : usa
    Sanitizer --> DatabaseOps : usa
    Sanitizer --> Utils : usa
    Exporter --> Utils : usa
    XlsxGenerator --> TotalsAnalytics : usa
```

---

## 9. Diagrama de Persistência

Schema completo do banco SQLite com relacionamentos lógicos entre tabelas.

```mermaid
erDiagram
    LANCAMENTOS_GERAIS {
        text Data
        text DIA_SEMANA
        text TIPO
        text DESCRICAO
        real Credito
        real Debito
        text Mes
        text Ano
        text MES_EXTENSO
        text AnoMes
        text Origem
    }

    TiposLancamentos {
        text Codigo
        text Descricao
    }

    GUIDING {
        text TABLE_NAME
        text ACCOUNTING
        text LOADABLE
    }

    PARCELAMENTOS {
        text Data
        text TipoLancamento
        real Debito
    }

    HistoricoGeral {
        text AnoMes
        real valores_por_categoria
    }

    HistoricoAnual {
        text Ano
        real valores_por_categoria
    }

    contagem_diaria {
        text Data
        int ContagemAcumulada
    }

    Resumo_Parcelamentos {
        text AnoMes
        int Quantidade
        real Valor
        real Diferenca
    }

    Resumido_In_Out {
        text AnoMes
        real TotalCredito
        real TotalDebito
    }

    Origens_VIEW {
        text nome
    }

    LANCAMENTOS_GERAIS }o--|| TiposLancamentos : "TIPO referencia Codigo"
    LANCAMENTOS_GERAIS }o--|| GUIDING : "Origem referencia TABLE_NAME"
    GUIDING ||--o| Origens_VIEW : "gera view filtrada"
    LANCAMENTOS_GERAIS ||--o{ HistoricoGeral : "pivot por AnoMes"
    LANCAMENTOS_GERAIS ||--o{ HistoricoAnual : "pivot por Ano"
    LANCAMENTOS_GERAIS ||--o{ contagem_diaria : "contagem acumulada"
    PARCELAMENTOS ||--o{ Resumo_Parcelamentos : "resume por mes"
    LANCAMENTOS_GERAIS ||--o{ Resumido_In_Out : "sumariza credito debito"
```

---

## 10. Diagrama de Deploy

Topologia completa de implantação do PDW em ambiente local.

```mermaid
flowchart TD
    subgraph SCHED["Agendamento Externo"]
        CRON["cron job\nLinux"]
        TASK["Task Scheduler\nWindows"]
    end

    subgraph SCRIPTS["Scripts de Entrada"]
        SH["RunPDW.sh\ncontrole de lock"]
        PS["RunPDW.ps1"]
        BAT["Run_PDW.bat"]
    end

    subgraph RUNTIME["Runtime Python 3.9+"]
        VENV["virtualenv / pip\npandas numpy openpyxl xlrd xlsxwriter pyyaml"]
        FAC["PersonalDataWareHouse.py"]
        PKG["pdw/ package\n14 módulos"]
    end

    subgraph CFG_DIR["./ Diretório de Execução"]
        CFG_F["PersonalDataWareHouse.cfg"]
        LOCK["PDW_lock/ (mutex dir)"]
    end

    subgraph DIR_IN_G["DIR_IN/ Entrada"]
        XLSX_IN["PDW.xlsx"]
        YAML_IN["PDW_QUERIES.yaml"]
    end

    subgraph DIR_DB_G["DATABASE_DIR/ Banco"]
        DB_F[("PDW.db\nSQLite3 >= 3.35")]
    end

    subgraph DIR_OUT_G["DIR_OUT/ Saídas"]
        XLSX_OUT["PDW_REPORTS.v2.xlsx"]
        CSV_OUT["*.csv"]
        GZ_OUT["*.json.gz / *.xml.gz"]
    end

    subgraph DIR_LOG_G["LOG_DIR/ Log"]
        LOG_F["PDW.lnx.log\nPDW.win.log"]
    end

    CRON --> SH
    TASK --> PS
    TASK --> BAT
    SH --> LOCK
    SH --> FAC
    PS --> FAC
    BAT --> FAC
    FAC --> PKG
    VENV --> PKG
    CFG_F --> PKG
    XLSX_IN --> PKG
    YAML_IN --> PKG
    PKG --> DB_F
    PKG --> XLSX_OUT
    PKG --> CSV_OUT
    PKG --> GZ_OUT
    PKG --> LOG_F
```
