# INVENTARIO_API.md
## Personal Data Warehouse — Inventário Completo de Funções
### Versão analisada: 9.11.2 | Versão alvo: 10.1.0

---

## Resumo Executivo

| Métrica | Valor |
|---|---|
| Arquivo analisado | `PersonalDataWareHouse.py` |
| Tamanho | ~989 linhas |
| Total de funções | 25 |
| Imports de stdlib | `sqlite3`, `datetime`, `os`, `platform`, `sys`, `threading`, `time`, `xml.etree.ElementTree`, `gzip`, `shutil` |
| Imports de terceiros | `pandas`, `numpy`, `configparser`, `yaml` |
| Dependências externas | arquivo `.cfg`, arquivo `.yaml`, arquivo `.xlsx`, banco `.db` |

---

## Inventário Completo de Funções

---

### F-01 · `main(param_file)`
- **Linhas**: 95–315
- **Responsabilidades**:
  - Ponto de entrada da aplicação
  - Leitura e validação do arquivo de configuração (`.cfg`)
  - Gerenciamento do arquivo de log (criação, leitura, escrita)
  - Detecção de plataforma (Windows/Linux) para hostname
  - Validação de existência de diretórios e arquivo de entrada
  - Orquestração de todo o pipeline de execução
  - Exibição de informações de runtime no console
- **Chama**: `new_data_loader`, `create_pivot_history`, `create_dinamic_reports`, `monthly_summaries`, `general_entries_file_exportator`, `split_paymnt_resume`, `xlsx_report_generator`
- **Chamada por**: `__main__` (ponto de entrada do script)
- **Responsabilidade dominante**: **Infraestrutura + Orquestração**
- **Side effects**: Cria arquivo de log, escreve no log, imprime no console, termina processo com `exit(1)` em erros
- **Acoplamentos identificados**:
  - Lê variável `current_version = "9.11.2"` hardcoded — deve bater com o `.cfg`
  - Abre e fecha `log_file` manualmente com `open()` — gestão manual de recurso
  - Parâmetro `multithread=True` causa `exit(1)` imediato — código morto presente

---

### F-02 · `split_paymnt_resume(db_file, split_paymnt_table, out_table)`
- **Linhas**: 317–330
- **Responsabilidades**:
  - Lê tabela de parcelamentos do SQLite
  - Agrupa por mês/ano
  - Calcula quantidade, valor e diferenças (diff)
  - Escreve resultado em nova tabela SQLite
- **Chama**: *(nada)*
- **Chamada por**: `main`
- **Responsabilidade dominante**: **Domínio financeiro — sumarização de parcelamentos**
- **Side effects**: Escreve tabela no banco SQLite
- **Dependências de dados**: Tabela de parcelamentos deve existir e conter colunas `Data`, `Debito`

---

### F-03 · `monthly_summaries(db_file, in_table, out_table)`
- **Linhas**: 332–361
- **Responsabilidades**:
  - Lê tabela geral de lançamentos
  - Agrega por `AnoMes + Origem` (mensal), por `Ano + Origem` (anual) e por `Origem` (full)
  - Calcula posição (Crédito − Débito)
  - Escreve 3 tabelas de resultado no SQLite
- **Chama**: *(nada)*
- **Chamada por**: `main`
- **Responsabilidade dominante**: **Domínio financeiro — sumarização mensal/anual**
- **Side effects**: Escreve 3 tabelas no banco SQLite (`out_table`, `out_table_ANUAL`, `out_table_FULL`)
- **Dependências de dados**: Tabela `in_table` com colunas `AnoMes`, `Origem`, `Credito`, `Debito`, `Ano`

---

### F-04 · `create_dinamic_reports(sqlite_database, excel_file, din_report_guinding, full_pivot)`
- **Linhas**: 364–407
- **Responsabilidades**:
  - Lê planilha guia de relatórios dinâmicos do Excel
  - Persiste a planilha guia no SQLite
  - Para cada relatório dinâmico: lê colunas configuradas, constrói SQL dinâmico, executa e salva resultado
- **Chama**: *(nada)*
- **Chamada por**: `main`
- **Responsabilidade dominante**: **Analytics — geração de relatórios dinâmicos baseados em configuração Excel**
- **Side effects**: Cria/substitui múltiplas tabelas no SQLite
- **Acoplamentos identificados**:
  - Constrói SQL dinamicamente por concatenação de strings — nomes de colunas vêm do Excel
  - Referencia coluna `full_pivot` diretamente na query (tabela pivot deve existir previamente)
  - Lê colunas `DEST_TABLE`, `SHEETY`, `REPORT_NAME`, `COLUMN_NAME` do Excel — schema implícito

---

### F-05 · `general_entries_file_exportator(data_base_file, dir_out, file_out, table_name, other_types)`
- **Linhas**: 409–443
- **Responsabilidades**:
  - Exporta lançamentos gerais para CSV (UTF-8-sig)
  - Se `other_types=True`: exporta também JSON (gzipado) e XML (gzipado)
  - Aplica formatação de data via SQL (dd-mm-yyyy)
  - Substitui ponto por vírgula em valores financeiros via SQL
- **Chama**: `gzip_compressor`, `dataframe_to_xml`
- **Chamada por**: `main`
- **Responsabilidade dominante**: **Exportação de dados — múltiplos formatos**
- **Side effects**: Cria arquivos em disco; delega remoção de arquivos temporários ao `gzip_compressor`
- **Acoplamentos identificados**:
  - SQL hardcoded com formatação específica de colunas (SUBSTR, CHAR, REPLACE)
  - Sufixo `.v2` hardcoded no nome do arquivo de saída

---

### F-06 · `dataframe_to_xml(df, filename)`
- **Linhas**: 446–458
- **Responsabilidades**:
  - Converte um DataFrame pandas em arquivo XML com indentação
  - Usa `xml.etree.ElementTree` da stdlib
- **Chama**: *(nada — apenas stdlib)*
- **Chamada por**: `general_entries_file_exportator`
- **Responsabilidade dominante**: **Utilitário — conversão de formato**
- **Side effects**: Cria arquivo XML em disco
- **Notas**: Função pura de transformação + I/O. Candidata ideal para `utils/xml_utils.py`

---

### F-07 · `data_correjeitor(conexao, types_sheet, entries_table, save_useless, useless_table)`
- **Linhas**: 461–488
- **Responsabilidades**:
  - Normaliza e limpa o banco após carga
  - Salva dados descartados (opcional)
  - Remove registros nulos da tabela de tipos
  - Deleta parcelamentos inválidos
  - Remove e recria view `Origens`
- **Chama**: `table_droppator`
- **Chamada por**: `new_data_loader`
- **Responsabilidade dominante**: **Qualidade de dados / ETL — pós-processamento**
- **Side effects**: DDL (DROP TABLE, CREATE VIEW), DML (DELETE), escreve no console
- **Acoplamentos perigosos identificados**:
  - SQL hardcoded: `'DELETE FROM Parcelamentos WHERE ...'` — nome `Parcelamentos` **não parametrizado**
  - SQL hardcoded: `CREATE VIEW Origens as SELECT ... FROM GUIDING` — nome `GUIDING` **não parametrizado**
  - Parâmetro chamado `conexao` mas na prática recebe um `cursor` (de `new_data_loader`) — naming inconsistente
  - Internamente faz `cursor = conexao` — a função aceita cursor OU connection de forma implícita

---

### F-08 · `table_droppator(conexao, table_name)`
- **Linhas**: 490–493
- **Responsabilidades**:
  - Executa `DROP TABLE IF EXISTS` no SQLite
- **Chama**: *(nada)*
- **Chamada por**: `data_correjeitor`, `new_data_loader`
- **Responsabilidade dominante**: **Infraestrutura de banco de dados**
- **Side effects**: DDL — destrói tabela se existir
- **Acoplamentos perigosos identificados**:
  - Parâmetro `conexao` é usado como cursor (`cursor.execute(...)`) mas pode receber connection ou cursor dependendo do chamador — **ambiguidade de tipo**

---

### F-09 · `create_pivot_history(data_base_file, types_table, entries_table, out_table_General, out_table_Anual)`
- **Linhas**: 496–530
- **Responsabilidades**:
  - Cria 4 tabelas pivot: mensal por valor, mensal por quantidade, anual por valor, anual por quantidade
  - Ordena colunas conforme sequência da tabela de tipos
- **Chama**: *(nada)*
- **Chamada por**: `main`
- **Responsabilidade dominante**: **Analytics — tabelas pivot históricas**
- **Side effects**: Cria/substitui 4 tabelas no SQLite; `connection.commit()` sem fechar a conexão
- **Notas**: Único lugar que chama `connection.commit()` sem `connection.close()` — a conexão é aberta e commitada mas não fechada explicitamente nesta função

---

### F-10 · `gzip_compressor(arquivo_origem)`
- **Linhas**: 533–541
- **Responsabilidades**:
  - Comprime arquivo para `.gz`
  - Remove o arquivo original após compressão
- **Chama**: *(nada — apenas stdlib)*
- **Chamada por**: `general_entries_file_exportator`
- **Responsabilidade dominante**: **Utilitário — compressão de arquivos**
- **Side effects**: Cria arquivo `.gz`, **remove arquivo original** (operação destrutiva irreversível)
- **Risco**: Se a compressão falhar no meio, o arquivo original já pode ter sido corrompido

---

### F-11 · `totalizador_diario(database_file, in_table, out_table)`
- **Linhas**: 543–553
- **Responsabilidades**:
  - Calcula contagem diária de registros
  - Calcula contagem acumulada por data
  - Persiste resultado no SQLite
- **Chama**: *(nada)*
- **Chamada por**: `xlsx_report_generator`
- **Responsabilidade dominante**: **Analytics — progresso diário acumulado**
- **Side effects**: Cria/substitui tabela no SQLite; `conn.commit()` + `conn.close()`

---

### F-12 · `get_month_names()`
- **Linhas**: 566–586
- **Responsabilidades**:
  - Retorna dicionário `{int: str}` com nomes de meses em português
- **Chama**: *(nada)*
- **Chamada por**: `enrich_dataframe_with_dates`
- **Responsabilidade dominante**: **Utilitário — localização / dicionário de dados**
- **Side effects**: Nenhum — função pura
- **Notas**: Candidata a constante de módulo (`MONTH_NAMES = {...}`) em vez de função

---

### F-13 · `get_weekday_names()`
- **Linhas**: 588–603
- **Responsabilidades**:
  - Retorna dicionário `{int: str}` com nomes de dias da semana em português
- **Chama**: *(nada)*
- **Chamada por**: `enrich_dataframe_with_dates`
- **Responsabilidade dominante**: **Utilitário — localização / dicionário de dados**
- **Side effects**: Nenhum — função pura
- **Notas**: Candidata a constante de módulo em vez de função

---

### F-14 · `read_guiding_sheet(excel_file, sheet_name)`
- **Linhas**: 610–624
- **Responsabilidades**:
  - Lê a planilha guia (GUIDING) do arquivo Excel
  - Retorna DataFrame com configurações das planilhas a processar
- **Chama**: *(nada — usa pandas)*
- **Chamada por**: `new_data_loader`
- **Responsabilidade dominante**: **ETL — leitura de configuração Excel**
- **Side effects**: I/O de leitura de arquivo Excel
- **Notas**: Abre o ExcelFile completo para parsear apenas uma aba — pode ser otimizado, mas fora do escopo agora

---

### F-15 · `process_accounting_sheet(excel_file, sheet_name, origin_col_name)`
- **Linhas**: 627–644
- **Responsabilidades**:
  - Lê uma planilha contábil do Excel
  - Seleciona colunas relevantes (`Data`, `TIPO`, `DESCRICAO`, `Credito`, `Debito`)
  - Adiciona coluna de origem
  - Substitui strings vazias por NaN em `TIPO` e `Data`
- **Chama**: *(nada)*
- **Chamada por**: `new_data_loader`
- **Responsabilidade dominante**: **ETL — extração de planilha contábil**
- **Side effects**: I/O de leitura de arquivo Excel
- **Dependência de schema**: Planilha deve ter exatamente as colunas `Data`, `TIPO`, `DESCRICAO`, `Credito`, `Debito`

---

### F-16 · `process_non_accounting_sheet(excel_file, sheet_name, conn)`
- **Linhas**: 646–659
- **Responsabilidades**:
  - Lê planilha não-contábil do Excel
  - Salva diretamente no SQLite (sem transformações)
- **Chama**: *(nada)*
- **Chamada por**: `new_data_loader`
- **Responsabilidade dominante**: **ETL — carga direta de planilha auxiliar**
- **Side effects**: Leitura de Excel + escrita no SQLite
- **Notas**: Recebe `conn` (connection object) — diferente de F-07 e F-08 que recebem cursor

---

### F-17 · `clean_description_text(text_series)`
- **Linhas**: 665–682
- **Responsabilidades**:
  - Substitui `;` e `,` por `|`
  - Substitui caractere especial `∴` por ` .'. `
  - Remove acento específico (`ś` → `s`)
  - Remove aspas duplas
  - Remove espaços extras (strip)
- **Chama**: *(nada)*
- **Chamada por**: `sanitize_entries_dataframe`
- **Responsabilidade dominante**: **Transformação — limpeza de texto**
- **Side effects**: Nenhum — função pura sobre Series pandas

---

### F-18 · `add_temporal_columns(df)`
- **Linhas**: 684–699
- **Responsabilidades**:
  - Insere colunas temporais com valores placeholder no DataFrame:
    `DIA_SEMANA`, `Mes`, `Ano`, `MES_EXTENSO`, `AnoMes`
  - Usa `df.insert()` para posicionamento preciso de colunas
- **Chama**: *(nada)*
- **Chamada por**: `sanitize_entries_dataframe`
- **Responsabilidade dominante**: **Transformação — estruturação do schema de saída**
- **Side effects**: Modifica o DataFrame in-place (por referência pandas)
- **Notas**: O uso de `df.insert()` com índices fixos (1, 6, 7, 8, 9) é frágil — depende da ordem das colunas do Excel

---

### F-19 · `enrich_dataframe_with_dates(df)`
- **Linhas**: 701–721
- **Responsabilidades**:
  - Preenche as colunas temporais criadas por `add_temporal_columns`
  - Deriva `MES_EXTENSO`, `DIA_SEMANA`, `Mes`, `Ano`, `AnoMes` a partir de `df['Data']`
- **Chama**: `get_month_names`, `get_weekday_names`
- **Chamada por**: `sanitize_entries_dataframe`
- **Responsabilidade dominante**: **Transformação — enriquecimento temporal**
- **Side effects**: Nenhum (usa `df.assign()` — retorna novo DataFrame)
- **Dependência crítica**: Coluna `Data` deve ser do tipo `datetime` antes desta chamada

---

### F-20 · `sanitize_financial_columns(df)`
- **Linhas**: 723–736
- **Responsabilidades**:
  - Converte `Credito` e `Debito` para numérico
  - Arredonda para 2 casas decimais
  - Preenche NaN com 0
- **Chama**: *(nada)*
- **Chamada por**: `sanitize_entries_dataframe`
- **Responsabilidade dominante**: **Transformação — sanitização financeira**
- **Side effects**: Nenhum (usa `df.assign()`)

---

### F-21 · `sanitize_entries_dataframe(df, remove_nulls=True)`
- **Linhas**: 739–760
- **Responsabilidades**:
  - Orquestra todo o pipeline de sanitização do DataFrame consolidado
  - Remove nulos opcionalmente
  - Chama transformações de data, financeiras e de texto em sequência
- **Chama**: `add_temporal_columns`, `sanitize_financial_columns`, `enrich_dataframe_with_dates`, `clean_description_text`
- **Chamada por**: `new_data_loader`
- **Responsabilidade dominante**: **ETL — orquestrador de sanitização**
- **Side effects**: Imprime status no console
- **Notas**: É a função que encapsula toda a etapa Transform do ETL

---

### F-22 · `sort_dataframe_by_date(df, ascending=False)`
- **Linhas**: 762–777
- **Responsabilidades**:
  - Ordena DataFrame pela primeira coluna (assume ser `Data`)
- **Chama**: *(nada)*
- **Chamada por**: `save_dataframe_to_database`
- **Responsabilidade dominante**: **Utilitário — ordenação**
- **Side effects**: Nenhum — retorna novo DataFrame
- **Notas**: Usa `df.columns[0]` implicitamente assumindo que a primeira coluna é `Data` — acoplamento implícito

---

### F-23 · `save_dataframe_to_database(df, conn, table_name, sort_by_date=True)`
- **Linhas**: 779–798
- **Responsabilidades**:
  - Ordena DataFrame (opcional)
  - Persiste DataFrame no SQLite (`if_exists="replace"`)
  - Retorna contagem de linhas
- **Chama**: `sort_dataframe_by_date`
- **Chamada por**: `new_data_loader`
- **Responsabilidade dominante**: **Infraestrutura de banco — persistência de DataFrame**
- **Side effects**: Escreve tabela no SQLite; imprime status no console

---

### F-24 · `new_data_loader(data_base, types_sheet, general_entries_table, data_origin_col, guiding_sheet, excel_file, save_useless, udt)`
- **Linhas**: 803–881
- **Responsabilidades**:
  - Orquestra todo o processo de ETL:
    1. Conecta ao banco
    2. Lê planilha guia
    3. Dropa tabela de destino
    4. Itera planilhas: contábeis (consolida) e não-contábeis (carga direta)
    5. Concatena DataFrames contábeis
    6. Sanitiza e enriquece dados
    7. Persiste no banco
    8. Executa pós-processamento (`data_correjeitor`)
    9. Comita e fecha conexão
- **Chama**: `read_guiding_sheet`, `table_droppator`, `process_accounting_sheet`, `process_non_accounting_sheet`, `sanitize_entries_dataframe`, `save_dataframe_to_database`, `data_correjeitor`
- **Chamada por**: `main`
- **Responsabilidade dominante**: **ETL — orquestrador principal**
- **Side effects**: Abre e fecha conexão SQLite, cria/substitui múltiplas tabelas, comita transações
- **Notas**: Parâmetro `udt` tem nome não descritivo — é a tabela de dados descartados (passado para `data_correjeitor`)

---

### F-25 · `xlsx_report_generator(...)`  *(15 parâmetros)*
- **Linhas**: 883–975
- **Responsabilidades**:
  - Carrega queries do arquivo YAML
  - Chama `totalizador_diario`
  - Monta lista de consultas SQL condicionalmente (por flags `gera_hist`, `dynamic_reports`)
  - Executa cada query e exporta resultado para aba Excel
  - Suporta modo arquivo único ou múltiplos arquivos
- **Chama**: `totalizador_diario`
- **Chamada por**: `main`
- **Responsabilidade dominante**: **Relatórios — gerador de Excel a partir de YAML**
- **Side effects**: Lê arquivo YAML, lê SQLite, cria/escreve arquivo(s) `.xlsx`
- **Acoplamentos identificados**:
  - 15 parâmetros — alta complexidade de interface
  - Lê tabela `{dyn_rep_tab}` do SQLite para relatórios dinâmicos — depende de `create_dinamic_reports` ter rodado antes
  - Variáveis de substituição no YAML são hardcoded na função (`variables = {...}`)

---

## Mapa de Dependências (Grafo de Chamadas)

```
main
├── new_data_loader ──────────────────────────────── ETL
│   ├── read_guiding_sheet
│   ├── table_droppator
│   ├── process_accounting_sheet
│   ├── process_non_accounting_sheet
│   ├── sanitize_entries_dataframe ──────────────── Transform
│   │   ├── add_temporal_columns
│   │   ├── sanitize_financial_columns
│   │   ├── enrich_dataframe_with_dates
│   │   │   ├── get_month_names
│   │   │   └── get_weekday_names
│   │   └── clean_description_text
│   ├── save_dataframe_to_database
│   │   └── sort_dataframe_by_date
│   └── data_correjeitor ────────────────────────── Post-ETL
│       └── table_droppator
│
├── create_pivot_history ────────────────────────── Analytics
├── create_dinamic_reports ──────────────────────── Analytics
│
├── monthly_summaries ───────────────────────────── Reports/Aggregation
├── split_paymnt_resume ─────────────────────────── Reports/Aggregation
│
├── general_entries_file_exportator ─────────────── Export
│   ├── gzip_compressor
│   └── dataframe_to_xml
│
└── xlsx_report_generator ───────────────────────── Reports/Excel
    └── totalizador_diario
```

---

## Classificação por Camada

| Função | Camada | Módulo Sugerido |
|---|---|---|
| `main` | Infraestrutura / Orquestração | `core/orchestrator.py` |
| `new_data_loader` | ETL | `etl/loader.py` |
| `read_guiding_sheet` | ETL | `etl/loader.py` |
| `process_accounting_sheet` | ETL | `etl/loader.py` |
| `process_non_accounting_sheet` | ETL | `etl/loader.py` |
| `sanitize_entries_dataframe` | Transform | `etl/sanitizer.py` |
| `add_temporal_columns` | Transform | `etl/sanitizer.py` |
| `enrich_dataframe_with_dates` | Transform | `etl/sanitizer.py` |
| `sanitize_financial_columns` | Transform | `etl/sanitizer.py` |
| `clean_description_text` | Transform | `etl/sanitizer.py` |
| `sort_dataframe_by_date` | Transform | `etl/sanitizer.py` |
| `data_correjeitor` | Transform / DB | `etl/sanitizer.py` |
| `table_droppator` | Database | `database/operations.py` |
| `save_dataframe_to_database` | Database | `database/operations.py` |
| `create_pivot_history` | Analytics | `analytics/pivot.py` |
| `create_dinamic_reports` | Analytics | `analytics/pivot.py` |
| `totalizador_diario` | Analytics | `analytics/totals.py` |
| `monthly_summaries` | Analytics | `analytics/totals.py` |
| `split_paymnt_resume` | Analytics | `analytics/totals.py` |
| `xlsx_report_generator` | Reports | `reports/xlsx_generator.py` |
| `general_entries_file_exportator` | Reports/Export | `reports/exporter.py` |
| `dataframe_to_xml` | Utilitário | `utils/xml_utils.py` |
| `gzip_compressor` | Utilitário | `utils/compression.py` |
| `get_month_names` | Utilitário | `utils/localization.py` |
| `get_weekday_names` | Utilitário | `utils/localization.py` |
