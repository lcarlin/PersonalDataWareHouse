# ENDPOINTS.md
## Personal Data Warehouse — Inventário de Funções Públicas (Contratos de API)
### Versão 10.1.0

> **Nota**: O PDW é um sistema batch CLI, não uma aplicação web. "Endpoints" aqui significa
> as funções públicas invocáveis — os contratos de interface do sistema.

---

## Sumário de Funções Públicas

| # | Função | Módulo | Categoria |
|---|---|---|---|
| 1 | `run_pipeline` | `pdw.core.orchestrator` | Orquestração |
| 2 | `load_config` | `pdw.config.loader` | Configuração |
| 3 | `open_log` | `pdw.infrastructure.logging` | Log |
| 4 | `finalize_log` | `pdw.infrastructure.logging` | Log |
| 5 | `new_data_loader` | `pdw.etl.loader` | ETL |
| 6 | `read_guiding_sheet` | `pdw.etl.loader` | ETL |
| 7 | `process_accounting_sheet` | `pdw.etl.loader` | ETL |
| 8 | `process_non_accounting_sheet` | `pdw.etl.loader` | ETL |
| 9 | `sanitize_entries_dataframe` | `pdw.etl.sanitizer` | ETL |
| 10 | `data_correjeitor` | `pdw.etl.sanitizer` | ETL |
| 11 | `table_droppator` | `pdw.database.operations` | Database |
| 12 | `save_dataframe_to_database` | `pdw.database.operations` | Database |
| 13 | `sort_dataframe_by_date` | `pdw.database.operations` | Database |
| 14 | `create_pivot_history` | `pdw.analytics.pivot` | Analytics |
| 15 | `create_dinamic_reports` | `pdw.analytics.pivot` | Analytics |
| 16 | `totalizador_diario` | `pdw.analytics.totals` | Analytics |
| 17 | `monthly_summaries` | `pdw.analytics.totals` | Analytics |
| 18 | `split_paymnt_resume` | `pdw.analytics.totals` | Analytics |
| 19 | `general_entries_file_exportator` | `pdw.reports.exporter` | Reports |
| 20 | `xlsx_report_generator` | `pdw.reports.xlsx_generator` | Reports |
| 21 | `gerar_todos_relatorios_integrado` | `pdw.reports.novos_relatorios` | Reports |
| 22 | `gzip_compressor` | `pdw.utils.compression` | Utils |
| 23 | `dataframe_to_xml` | `pdw.utils.xml_utils` | Utils |
| 24 | `transient_data_exportator` | `pdw.utils.transient_data` | Utils |
| 25 | `get_month_names` | `pdw.utils.localization` | Utils |
| 26 | `get_weekday_names` | `pdw.utils.localization` | Utils |

---

## Detalhamento por Função

---

### 1. `run_pipeline`

**Módulo**: `pdw.core.orchestrator`

```python
def run_pipeline(param_file: str) -> None
```

**Descrição**: Ponto de entrada do pipeline completo. Orquestra toda a execução: config → log → ETL → pivot → reports → log.

**Parâmetros**:
| Nome | Tipo | Descrição |
|---|---|---|
| `param_file` | `str` | Caminho para arquivo .cfg customizado. `""` usa `PersonalDataWareHouse.cfg` no CWD. |

**Retorno**: `None`

**Side effects**:
- Lê arquivo `.cfg`
- Lê/cria arquivo `.log`
- Lê arquivo Excel `.xlsx`
- Cria/sobrescreve banco SQLite `.db`
- Cria arquivos de relatório `.xlsx`, `.csv`, `.json.gz`, `.xml.gz`
- Imprime progresso no stdout
- Chama `exit(1)` em caso de erro de configuração

**Erros esperados**: Chama `exit(1)` (não lança exceção) em:
- Versão do .cfg diferente da versão do pacote
- Diretórios de entrada/saída inexistentes
- Arquivo Excel não encontrado
- `MULTITHREADING=True`

---

### 2. `load_config`

**Módulo**: `pdw.config.loader`

```python
def load_config(param_file: str) -> dict
```

**Descrição**: Lê e valida o arquivo `.cfg`. Retorna dicionário com todos os parâmetros.

**Parâmetros**:
| Nome | Tipo | Descrição |
|---|---|---|
| `param_file` | `str` | Caminho para arquivo .cfg. `""` usa `PersonalDataWareHouse.cfg`. |

**Retorno**: `dict` com as chaves:

| Chave | Tipo Python | Parâmetro .cfg |
|---|---|---|
| `current_version` | `str` | versão canônica do pacote |
| `config_file` | `str` | nome do arquivo lido |
| `dir_file_in` | `str` | `DIR_IN` |
| `dir_file_out` | `str` | `DIR_OUT` |
| `dir_log` | `str` | `LOG_DIR` |
| `dir_db` | `str` | `DATABASE_DIR` |
| `in_file` | `str` | `INPUT_FILE` |
| `in_type` | `str` | `TYPE_IN` |
| `out_type` | `str` | `TYPE_OUT` |
| `out_db` | `str` | `OUT_DB_FILE` |
| `output_name` | `str` | `OUT_RPT_FILE` |
| `db_file_type` | `str` | `DB_FILE_TYPE` |
| `log_file_cfg` | `str` | `LOG_DIR + LOG_FILE` |
| `multithread` | `bool` | `MULTITHREADING` |
| `overwrite_db` | `bool` | `OVERWRITE_DB` |
| `run_loader` | `bool` | `RUN_DATA_LOADER` |
| `run_reports` | `bool` | `RUN_REPORTS` |
| `multi_rept_file` | `bool` | `RPT_SINGLE_FILE` |
| `guiding_table` | `str` | `GUIDING_TABLE` |
| `types_of_entries` | `str` | `TYPES_OF_ENTRIES` |
| `general_entries_table` | `str` | `GENERAL_ENTRIES_TABLE` |
| `create_pivot` | `bool` | `CREATE_PIVOT` |
| `save_discarted_data` | `bool` | `SAVE_DISCARTED_DATA` |
| `discarted_data_table` | `str` | `DISCARTED_DATA_TABLE` |
| `full_hist_table` | `str` | `FULL_PIVOT_TABLE` |
| `anual_hist_table` | `str` | `ANUAL_PIVOT_TABLE` |
| `origem_dados` | `str` | `TRANSIENT_DATA_COLUMN` |
| `other_file_types` | `bool` | `EXPORT_OTHER_TYPES` |
| `dinamic_reports` | `bool` | `RUN_DINAMIC_REPORT` |
| `din_report_guinding` | `str` | `DIN_REPORT_GUIDING` |
| `dayly_progress` | `str` | `DAYLY_PROGRESS` |
| `split_paymnt_table` | `str` | `SPLT_PAYMNT_TAB` |
| `out_table` | `str` | `OUT_RES_PMNT_TAB` |
| `monthly_summarie` | `str` | `MONTHLY_SUMMATIES` |
| `queries_file` | `str` | `YAML_SQL_FILE` |

**Side effects**: `exit(1)` em erro de arquivo ou versão incompatível.

---

### 3. `open_log`

**Módulo**: `pdw.infrastructure.logging`

```python
def open_log(log_file_cfg: str) -> tuple[IO, int, str]
```

**Parâmetros**:
| Nome | Tipo | Descrição |
|---|---|---|
| `log_file_cfg` | `str` | Caminho completo do arquivo de log |

**Retorno**: `tuple(file_handle, number_of_runs, last_run_date)`
- `file_handle`: objeto arquivo aberto em modo `r+`
- `number_of_runs`: `int` — número de linhas (execuções anteriores)
- `last_run_date`: `str` — timestamp da última execução, ou `'none'` se nova

**Side effects**: Cria o arquivo se não existir. Mantém handle aberto (deve ser fechado via `finalize_log`).

---

### 4. `finalize_log`

**Módulo**: `pdw.infrastructure.logging`

```python
def finalize_log(log_file: IO, log_line: str) -> None
```

**Parâmetros**:
| Nome | Tipo | Descrição |
|---|---|---|
| `log_file` | `IO` | Handle retornado por `open_log` |
| `log_line` | `str` | Linha formatada com `\n` no final |

**Side effects**: Escreve `log_line` no arquivo e fecha o handle.

---

### 5. `new_data_loader`

**Módulo**: `pdw.etl.loader`

```python
def new_data_loader(
    data_base: str,
    types_sheet: str,
    general_entries_table: str,
    data_origin_col: str,
    guiding_sheet: str,
    excel_file: str,
    save_useless: bool,
    udt: str
) -> None
```

**Descrição**: Orquestra o ETL completo: Excel → SQLite.

**Parâmetros**:
| Nome | Tipo | Descrição |
|---|---|---|
| `data_base` | `str` | Caminho completo do arquivo SQLite |
| `types_sheet` | `str` | Nome da aba/tabela de tipos de lançamentos |
| `general_entries_table` | `str` | Nome da tabela de lançamentos consolidados |
| `data_origin_col` | `str` | Nome da coluna que registra a origem (nome da aba Excel) |
| `guiding_sheet` | `str` | Nome da aba de configuração (GUIDING) |
| `excel_file` | `str` | Caminho completo do arquivo Excel de entrada |
| `save_useless` | `bool` | `True`: mantém registros com TIPO/Data nulos |
| `udt` | `str` | Tabela de dados descartados (parâmetro de `data_correjeitor`) |

**Retorno**: `None`

**Side effects**:
- Cria/sobrescreve banco SQLite
- Dropa e recria `general_entries_table`
- Salva todas as abas configuradas como tabelas SQLite
- Executa `data_correjeitor` (normalização pós-carga)
- Imprime progresso no stdout

---

### 6. `read_guiding_sheet`

**Módulo**: `pdw.etl.loader`

```python
def read_guiding_sheet(excel_file: str, sheet_name: str) -> pd.DataFrame
```

**Retorno**: DataFrame com colunas `TABLE_NAME`, `ACCOUNTING`, `LOADABLE` (e possivelmente outras).

**Side effects**: Leitura de arquivo Excel.

---

### 7. `process_accounting_sheet`

**Módulo**: `pdw.etl.loader`

```python
def process_accounting_sheet(
    excel_file: str,
    sheet_name: str,
    origin_col_name: str
) -> tuple[pd.DataFrame, int]
```

**Retorno**: `(DataFrame, número_de_linhas)`

DataFrame tem colunas: `Data`, `TIPO`, `DESCRICAO`, `Credito`, `Debito`, `{origin_col_name}`

---

### 8. `process_non_accounting_sheet`

**Módulo**: `pdw.etl.loader`

```python
def process_non_accounting_sheet(
    excel_file: str,
    sheet_name: str,
    conn: sqlite3.Connection
) -> int
```

**Retorno**: Número de linhas inseridas no SQLite.

**Side effects**: Escreve tabela no SQLite (nome = `sheet_name`).

---

### 9. `sanitize_entries_dataframe`

**Módulo**: `pdw.etl.sanitizer`

```python
def sanitize_entries_dataframe(
    df: pd.DataFrame,
    remove_nulls: bool = True
) -> pd.DataFrame
```

**Descrição**: Aplica todas as transformações de limpeza ao DataFrame de lançamentos.

**Transformações aplicadas (em ordem)**:
1. Remove linhas com `TIPO` nulo (se `remove_nulls=True`)
2. Remove linhas com `Data` nula (se `remove_nulls=True`)
3. Limpa `DESCRICAO`: remove `;,`, substitui `∴` por ` .'. `, `ś` por `s`, remove `"`
4. Converte `Data` para `datetime`
5. Adiciona coluna `Mes` com nome PT-BR do mês
6. Adiciona coluna `DiaSemana` com nome PT-BR do dia da semana
7. Preenche `Credito` e `Debito` nulos com `0.0`

**Retorno**: DataFrame transformado (novo objeto, não modifica in-place).

---

### 10. `data_correjeitor`

**Módulo**: `pdw.etl.sanitizer`

```python
def data_correjeitor(
    conexao,           # cursor SQLite (atenção: nome enganoso — é cursor, não conexão)
    types_sheet: str,
    entries_table: str,
    save_useless: bool,
    useless_table: str
) -> None
```

**Descrição**: Pós-processamento pós-carga via SQL direto.

**Operações SQL executadas**:
1. Atualiza `TIPO` em `LANCAMENTOS_GERAIS` com base em correspondência com `TiposLancamentos`
2. Hardcoded: assume tabela `Parcelamentos` existe no banco
3. Hardcoded: assume tabela `GUIDING` existe no banco
4. Cria view `Origens` se não existir
5. Se `save_useless=False`: deleta entradas com TIPO não reconhecido

**AVISO**: O parâmetro `conexao` deve ser um `cursor` SQLite, apesar do nome sugerir `conexão`.

---

### 11. `table_droppator`

**Módulo**: `pdw.database.operations`

```python
def table_droppator(conexao, table_name: str) -> None
```

**AVISO**: `conexao` pode ser `cursor` ou `connection` — ambos têm método `.execute()`.

**Side effects**: Executa `DROP TABLE IF EXISTS {table_name}` — **sem sanitização do nome da tabela**.

---

### 12. `save_dataframe_to_database`

**Módulo**: `pdw.database.operations`

```python
def save_dataframe_to_database(
    df: pd.DataFrame,
    conn: sqlite3.Connection,
    table_name: str,
    sort_by_date: bool = True
) -> int
```

**Parâmetros**:
| Nome | Tipo | Descrição |
|---|---|---|
| `conn` | `sqlite3.Connection` | Conexão SQLite (não cursor) |
| `sort_by_date` | `bool` | Ordena por primeira coluna descendente antes de salvar |

**Retorno**: `int` — número de linhas salvas.

**Side effects**: Dropa e recria a tabela no SQLite (`if_exists="replace"`).

---

### 13. `sort_dataframe_by_date`

**Módulo**: `pdw.database.operations`

```python
def sort_dataframe_by_date(
    df: pd.DataFrame,
    ascending: bool = False
) -> pd.DataFrame
```

**Retorno**: DataFrame ordenado pela primeira coluna (índice 0), descendente por padrão.

---

### 14. `create_pivot_history`

**Módulo**: `pdw.analytics.pivot`

```python
def create_pivot_history(
    sqlite_database: str,
    general_entries_table: str,
    full_hist_table: str,
    anual_hist_table: str
) -> None
```

**Side effects**: Cria tabelas `full_hist_table` e `anual_hist_table` no SQLite.

---

### 15. `create_dinamic_reports`

**Módulo**: `pdw.analytics.pivot`

```python
def create_dinamic_reports(
    sqlite_database: str,
    excel_file: str,
    din_report_guinding: str
) -> None
```

**Descrição**: Lê a aba de configuração de relatórios dinâmicos do Excel e executa queries correspondentes no SQLite, salvando resultados como tabelas.

---

### 16. `totalizador_diario`

**Módulo**: `pdw.analytics.totals`

```python
def totalizador_diario(
    sqlite_database: str,
    general_entries_table: str,
    dayly_progress: str
) -> None
```

**Side effects**: Cria tabela `dayly_progress` no SQLite com totais por dia.

---

### 17. `monthly_summaries`

**Módulo**: `pdw.analytics.totals`

```python
def monthly_summaries(
    sqlite_database: str,
    general_entries_table: str,
    monthly_summarie: str,
    output_name: str,
    dir_file_out: str,
    multi_rept_file: bool
) -> None
```

**Side effects**: Escreve aba no arquivo Excel de relatório.

---

### 18. `split_paymnt_resume`

**Módulo**: `pdw.analytics.totals`

```python
def split_paymnt_resume(
    sqlite_database: str,
    split_paymnt_table: str,
    out_table: str,
    output_name: str,
    dir_file_out: str,
    multi_rept_file: bool
) -> None
```

**Side effects**: Cria tabela `out_table` no SQLite; escreve aba no Excel de relatório.

---

### 19. `general_entries_file_exportator`

**Módulo**: `pdw.reports.exporter`

```python
def general_entries_file_exportator(
    sqlite_database: str,
    general_entries_table: str,
    output_name: str,
    dir_file_out: str,
    out_type: str,
    other_file_types: bool
) -> None
```

**Side effects**:
- Sempre: exporta `.csv` com timestamp
- Se `other_file_types=True`: exporta `.json.gz` e `.xml.gz`

**Formato dos arquivos de saída**:
- CSV: separador `;`, encoding UTF-8, sem índice
- JSON.gz: gzip de JSON orient="records"
- XML.gz: gzip de XML gerado por `dataframe_to_xml`

---

### 20. `xlsx_report_generator`

**Módulo**: `pdw.reports.xlsx_generator`

```python
def xlsx_report_generator(
    sqlite_database: str,
    pdw_sql_file: str,
    output_name: str,
    dir_file_out: str,
    multi_rept_file: bool
) -> None
```

**Descrição**: Lê queries do YAML e executa cada uma contra o SQLite, salvando resultados como abas em um arquivo Excel.

**Side effects**: Cria/append ao arquivo Excel de relatório.

---

### 21. `gerar_todos_relatorios_integrado`

**Módulo**: `pdw.reports.novos_relatorios`

```python
def gerar_todos_relatorios_integrado(
    sqlite_database: str,
    general_entries_table: str,
    dir_file_out: str
) -> None
```

**Pré-requisitos**: `matplotlib`, `seaborn`, `scipy`, `fpdf2` instalados.

**Lança**: `ImportError` com mensagem de instalação se dependências ausentes.

**Side effects**: Gera arquivos de gráficos e PDF em `dir_file_out`.

---

### 22. `gzip_compressor`

**Módulo**: `pdw.utils.compression`

```python
def gzip_compressor(
    source_file: str,
    dest_file: str
) -> None
```

**Side effects**: Cria `dest_file` como gzip de `source_file`. Não remove `source_file`.

---

### 23. `dataframe_to_xml`

**Módulo**: `pdw.utils.xml_utils`

```python
def dataframe_to_xml(
    df: pd.DataFrame,
    root_tag: str,
    row_tag: str
) -> str
```

**Retorno**: String XML com `ET.indent()` aplicado.

---

### 24. `transient_data_exportator`

**Módulo**: `pdw.utils.transient_data`

```python
def transient_data_exportator(
    sqlite_database: str,
    dir_out: str,
    out_extension: str,
    file_name: str,
    transient_data_table: str,
    origing_column: str
) -> None
```

**Nota**: Feature desabilitada no pipeline principal (comentada no orchestrator). Disponível para uso standalone.

**Side effects**: Exporta tabela para Excel com timestamp no nome; executa `UPDATE EXPORT_DATE` no SQLite.

---

### 25. `get_month_names`

**Módulo**: `pdw.utils.localization`

```python
def get_month_names() -> dict[int, str]
```

**Retorno**: `{1: 'Janeiro', 2: 'Fevereiro', ..., 12: 'Dezembro'}`

---

### 26. `get_weekday_names`

**Módulo**: `pdw.utils.localization`

```python
def get_weekday_names() -> dict[int, str]
```

**Retorno**: `{0: 'Segunda-Feira', 1: 'Terca-Feira', ..., 6: 'Domingo'}`

---

## Aliases de Compatibilidade

| Alias | Aponta para | Localização |
|---|---|---|
| `data_loader` | `new_data_loader` | `PersonalDataWareHouse.py`, `pdw.compat`, `etl/data_loader.py` |
| `main` | `run_pipeline` via `pdw.main.main` | `PersonalDataWareHouse.py` |
