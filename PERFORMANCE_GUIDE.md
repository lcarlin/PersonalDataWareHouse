# PERFORMANCE_GUIDE.md
## Personal Data Warehouse — Hardening de Performance e Gargalos
### Versão 10.1.0 | Análise: 2026-05-17

---

## Scores Globais

| Dimensão | Score | Escala | Impacto |
|---|---|---|---|
| **Risco de Performance** | **6.8 / 10** | 1=sem risco, 10=crítico | ↑ requer ação |
| **Vazamentos de Conexão** | **9.0 / 10** | 1=nenhum, 10=crítico | 🔴 crítico |
| **Eficiência de I/O** | **5.5 / 10** | 1=ótimo, 10=péssimo | → monitorar |
| **Consumo de Memória** | **6.0 / 10** | 1=ótimo, 10=péssimo | → monitorar |
| **Qualidade de SQL** | **4.0 / 10** | 1=ótimo, 10=péssimo | → aceitável |
| **Acoplamento** | **8.0 / 10** | 1=baixo, 10=alto | 🔴 crítico |
| **Modularidade** | **5.5 / 10** | 1=baixa, 10=alta | → monitorar |
| **Portabilidade** | **4.0 / 10** | 1=baixa, 10=alta | 🟠 alto risco |

---

## 1. Vazamentos de Conexão SQLite — 🔴 CRÍTICO (Score: 9/10)

### 1.1 `create_pivot_history` — conexão nunca fechada

**Arquivo**: `pdw/analytics/pivot.py`

```python
def create_pivot_history(data_base_file, types_table, entries_table, out_table_General, out_table_Anual):
    connection = sqlite3.connect(data_base_file)
    # ... operações ...
    connection.commit()
    # ❌ NUNCA chama connection.close()
```

**Impacto**: A conexão vai para o garbage collector do Python. Em CPython puro isso funciona (GC imediato por refcount), mas em PyPy, Jython ou ambientes de teste com GC não-determinístico, a conexão pode permanecer aberta e bloquear a próxima fase do pipeline com `sqlite3.OperationalError: database is locked`.

**Impacto adicional**: 4 tabelas são criadas nesta função (`out_table_General`, `out_table_General_QTD`, `out_table_Anual`, `out_table_Anual_QTD`). Se ocorrer exceção entre criações, o commit parcial não é revertido — dados inconsistentes permanecem.

---

### 1.2 `monthly_summaries` — 3 tabelas escritas sem close e sem commit

**Arquivo**: `pdw/analytics/totals.py`

```python
def monthly_summaries(db_file, in_table, out_table):
    db_conn = sqlite3.connect(db_file)
    # ... 3x df_agrupado.to_sql(out_table, db_conn, ...) ...
    # ❌ Sem db_conn.commit()
    # ❌ Sem db_conn.close()
```

**Impacto crítico**: `to_sql()` usa autocommit internamente no SQLite, então os dados geralmente persistem. Porém a ausência de `commit()` explícito é um risco em modos de transação explícita (`isolation_level != None`). Sem `close()`, a conexão fica aberta durante todo `run_reports`.

---

### 1.3 `split_paymnt_resume` — conexão sem close

**Arquivo**: `pdw/analytics/totals.py`

```python
def split_paymnt_resume(db_file, split_paymnt_table, out_table):
    db_conn = sqlite3.connect(db_file)
    # ... df_agrupado.to_sql(out_table, db_conn, ...) ...
    # ❌ Sem db_conn.commit()
    # ❌ Sem db_conn.close()
```

---

### Inventário completo de conexões

| Função | Módulo | connect() | commit() | close() | Status |
|---|---|---|---|---|---|
| `new_data_loader` | etl/loader.py | ✅ | ✅ | ✅ | ✅ OK |
| `totalizador_diario` | analytics/totals.py | ✅ | ✅ | ✅ | ✅ OK |
| `create_pivot_history` | analytics/pivot.py | ✅ | ✅ | ❌ | 🔴 LEAK |
| `create_dinamic_reports` | analytics/pivot.py | ✅ | ❌ | ✅ | 🟠 RISCO |
| `monthly_summaries` | analytics/totals.py | ✅ | ❌ | ❌ | 🔴 LEAK |
| `split_paymnt_resume` | analytics/totals.py | ✅ | ❌ | ❌ | 🔴 LEAK |
| `general_entries_file_exportator` | reports/exporter.py | ✅ | ❌ | ✅ | 🟡 OK* |
| `xlsx_report_generator` | reports/xlsx_generator.py | ✅ | ❌ | ✅ | 🟡 OK* |
| `transient_data_exportator` | utils/transient_data.py | ✅ | ✅ via cursor | ✅ | 🟡 FRÁGIL |

*OK porque são somente leitura (sem escrita que precise de commit explícito).

### Correção sistêmica recomendada

```python
# Padrão com context manager — garante close mesmo em exceção
from contextlib import contextmanager

@contextmanager
def get_connection(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Uso:
def create_pivot_history(data_base_file, ...):
    with get_connection(data_base_file) as connection:
        # ... operações ...
        # commit e close automáticos
```

---

## 2. Acoplamento Excessivo — 🔴 CRÍTICO (Score: 8/10)

### 2.1 `xlsx_report_generator` — 15 parâmetros posicionais

**Arquivo**: `pdw/reports/xlsx_generator.py:1`

```python
def xlsx_report_generator(
    sqlite_database,      # 1
    dir_out,             # 2
    file_name,           # 3
    write_multiple_files, # 4
    out_extension,       # 5
    entries_table,       # 6
    dynamic_reports,     # 7
    dyn_rep_tab,         # 8
    gera_hist,           # 9
    anual_hist,          # 10
    full_hist,           # 11
    day_prog,            # 12
    splt_pmnt_res,       # 13
    mont_summ,           # 14
    yaml_queries_file    # 15
):
```

**Impacto**: Qualquer alteração de ordem, adição ou remoção de parâmetro quebra silenciosamente o chamador em `orchestrator.py`. O índice 8 (`gera_hist`) e o índice 9 (`anual_hist`) são especialmente confusos — ambos são booleano/string respectivamente.

**Score de acoplamento**: 9.5/10 — pior função do sistema.

**Mitigação (dataclass)**:
```python
from dataclasses import dataclass

@dataclass
class XlsxReportConfig:
    sqlite_database: str
    dir_out: str
    file_name: str
    write_multiple_files: bool
    out_extension: str
    entries_table: str
    dynamic_reports: bool
    dyn_rep_tab: str
    gera_hist: bool
    anual_hist: str
    full_hist: str
    day_prog: str
    splt_pmnt_res: str
    mont_summ: str
    yaml_queries_file: str

def xlsx_report_generator(config: XlsxReportConfig) -> None:
    ...
```

---

### 2.2 `orchestrator.py` — 35+ variáveis locais desempacotadas do dict cfg

**Arquivo**: `pdw/core/orchestrator.py:35-68`

```python
current_version    = cfg['current_version']
config_file        = cfg['config_file']
dir_file_in        = cfg['dir_file_in']
# ... 32 variáveis mais ...
```

**Impacto**: Cada nova configuração requer 3 alterações: `load_config()`, o dict em `loader.py`, e o desempacotamento em `orchestrator.py`. Violação sutil do DRY.

---

### 2.3 `data_correjeitor` — acoplamento com schema hardcoded

**Arquivo**: `pdw/etl/sanitizer.py:60-80`

```python
# Hardcoded: 'Parcelamentos', 'GUIDING', 'Origens', 'Código', 'Descrição'
lista_acoes.append(('DELETE FROM Parcelamentos WHERE ...', ...))
lista_acoes.append(("create view Origens as select TABLE_NAME ... from GUIDING ...", ...))
lista_acoes.append((f"Delete from {types_sheet} WHERE ( Código IS NULL or Descrição IS NULL)", ...))
```

**Impacto**: A função assume implicitamente que:
1. A tabela `Parcelamentos` existe (nome hardcoded)
2. A tabela `GUIDING` existe (nome hardcoded)
3. `TiposLancamentos` tem colunas `Código` e `Descrição` (nomes hardcoded com acento)
4. A view a ser criada se chama `Origens` (hardcoded)

Qualquer um desses nomes mudando no Excel/cfg quebra silenciosamente.

**Score de acoplamento**: 8.5/10

---

## 3. Gargalos de I/O — 🟠 ALTO (Score: 6/10)

### 3.1 `dataframe_to_xml` — `iterrows()` em Python puro

**Arquivo**: `pdw/utils/xml_utils.py`

```python
def dataframe_to_xml(df, filename):
    root = ET.Element('data')
    for index, row in df.iterrows():  # ❌ O(n) loop Python puro
        item = ET.SubElement(root, 'item')
        for col_name, col_value in row.items():  # ❌ loop interno
            ET.SubElement(item, col_name).text = str(col_value)
    tree.write(filename, encoding='utf-8', xml_declaration=True)
```

**Benchmark estimado**: Para 50.000 linhas × 11 colunas:
- `iterrows()`: ~8s (Python puro, boxing/unboxing de tipos)
- Alternativa vectorizada: ~0.5s

**Mitigação**:
```python
def dataframe_to_xml(df: pd.DataFrame, filename: str) -> None:
    # Abordagem via to_xml do pandas (pandas >= 1.5)
    df.to_xml(filename, index=False, root_name='data', row_name='item',
              encoding='utf-8', xml_declaration=True)
```

---

### 3.2 `create_dinamic_reports` — lê o mesmo arquivo Excel N vezes

**Arquivo**: `pdw/analytics/pivot.py:45-72`

```python
def create_dinamic_reports(sqlite_database, excel_file, din_report_guinding, full_pivot):
    # ...
    data_frame = pd.read_excel(excel_file, sheet_name=din_report_guinding)  # leitura 1
    for i, linhas in data_frame.iterrows():
        columns_of_report = pd.read_excel(excel_file, sheet_name=report_xl_sheet)  # leitura N (dentro do loop!)
        # ...
        df_single_sheet = pd.read_excel(excel_file, sheet_name=report_xl_sheet)  # leitura N+1 (redundante!)
```

**Problema duplo**:
1. O arquivo Excel é aberto e fechado N×2 vezes (uma por aba dinâmica)
2. Para cada aba, `pd.read_excel()` é chamado **2 vezes** com o mesmo parâmetro — `columns_of_report` e `df_single_sheet` fazem a mesma leitura

**Mitigação**:
```python
def create_dinamic_reports(sqlite_database, excel_file, din_report_guinding, full_pivot):
    # Abrir o arquivo uma única vez
    with pd.ExcelFile(excel_file) as workbook:
        data_frame = workbook.parse(din_report_guinding)
        for i, linhas in data_frame.iterrows():
            df_single_sheet = workbook.parse(report_xl_sheet)  # reutiliza handle
            # ... sem segunda leitura
```

---

### 3.3 `xlsx_report_generator` — todo DataFrame em memória antes de escrever

**Arquivo**: `pdw/reports/xlsx_generator.py:65-80`

```python
for k in range(0, len(lista_consultas)):
    df_out = pd.read_sql(sql_statment, connection)  # carrega tudo em memória
    df_out.to_excel(xlsx_writer, sheet_name=excel_sheet, index=False)
```

**Impacto**: Para queries que retornam 100k+ linhas, cada `pd.read_sql()` carrega o DataFrame completo em RAM antes de escrever. Sem streaming.

**Mitigação** (pandas chunksize):
```python
# Para queries grandes, usar chunksize
for chunk in pd.read_sql(sql, connection, chunksize=5000):
    # mas ExcelWriter não suporta append fácil por chunk
    # alternativa: escrever em CSV e depois converter
```

---

### 3.4 Construção de caminhos sem `os.path.join`

**Arquivo**: `pdw/core/orchestrator.py:56-65`

```python
input_file = dir_file_in + in_file + '.' + in_type
```

**Problema**: Depende que `dir_file_in` termine com `/`. Se o usuário omitir a barra no .cfg:
```
DIR_IN = /home/user/pdw
→ input_file = "/home/user/pdwPDW.xlsx"  ← arquivo errado
```

**Mitigação**:
```python
import os
input_file = os.path.join(dir_file_in, f"{in_file}.{in_type}")
```

---

## 4. Consumo de Memória — 🟠 ALTO (Score: 6/10)

### 4.1 `create_pivot_history` — carrega todo LANCAMENTOS_GERAIS em memória

**Arquivo**: `pdw/analytics/pivot.py:12-13`

```python
sql_statment_summary = f'SELECT * FROM {entries_table} ;'
df_summary = pd.read_sql(sql_statment_summary, connection)  # ❌ SELECT * sem filtro
```

**Impacto**: Para 5 anos de dados (~50k lançamentos), `df_summary` pode consumir 50-100MB. O pandas cria cópias intermediárias durante `pivot_table()`, podendo triplicar o consumo: **150-300MB de pico**.

**Mitigação (push down para SQL)**:
```python
# Fazer o GROUP BY no SQLite, não no pandas
sql = """
    SELECT AnoMes, TIPO, SUM(Debito) as total, COUNT(*) as qtd
    FROM LANCAMENTOS_GERAIS
    GROUP BY AnoMes, TIPO
    ORDER BY AnoMes, TIPO
"""
df_grouped = pd.read_sql(sql, connection)
# pivot_table sobre um DataFrame pequeno (~1000 linhas) em vez de 50k
pivot_full = df_grouped.pivot(index='AnoMes', columns='TIPO', values='total').fillna(0)
```

---

### 4.2 `general_entries_file_exportator` — SQL com `char(39)` ineficiente

**Arquivo**: `pdw/reports/exporter.py:12-25`

```python
sqlStatment = "SELECT substr(LG.DATA, 9,2)||'-'||substr(LG.DATA,6,2)||'-'||substr(LG.DATA, 1,4) AS Quando " \
              "... " \
              ", char(39)||cast(mes as text) as 'Mes' " \
              ", char(39)||cast(ano as text) as 'Ano' " \
              # ...
```

**Problema**: `char(39)` é o apóstrofo — o SQL está adicionando `'` no início de campos para forçar tratamento como texto no Excel. Esta transformação é feita **no banco** (SQLite processa cada linha) e depois de volta no Python via pandas. É mais eficiente fazer a transformação no Python após o `pd.read_sql()`.

---

## 5. Eficiência de SQL — 🟡 MÉDIO (Score: 5/10)

### 5.1 Ausência de índices em LANCAMENTOS_GERAIS

**Nenhum índice é criado** após a carga dos dados. As queries analíticas frequentemente filtram por `Data`, `TIPO`, `AnoMes`, `Ano`, `Origem`:

```sql
-- Queries sem índice executam full table scan
SELECT * FROM LANCAMENTOS_GERAIS WHERE AnoMes = '2025/01';  -- full scan
SELECT * FROM LANCAMENTOS_GERAIS ORDER BY DATA DESC;         -- full scan
```

**Impacto**: Para 50k linhas, cada query analítica faz full table scan. Com índices, queries de filtro simples seriam O(log n).

**Mitigação**:
```python
# Após save_dataframe_to_database()
conn.execute("CREATE INDEX IF NOT EXISTS idx_lg_data   ON LANCAMENTOS_GERAIS(Data)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_lg_anomes ON LANCAMENTOS_GERAIS(AnoMes)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_lg_tipo   ON LANCAMENTOS_GERAIS(TIPO)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_lg_origem ON LANCAMENTOS_GERAIS(Origem)")
```

---

### 5.2 PRAGMA SQLite não configurados

**Nenhum** arquivo configura PRAGMAs de performance:

```python
# Nenhuma das funções faz:
conn.execute("PRAGMA journal_mode=WAL")      # não configurado
conn.execute("PRAGMA synchronous=NORMAL")    # não configurado
conn.execute("PRAGMA cache_size=-64000")     # não configurado
conn.execute("PRAGMA temp_store=MEMORY")     # não configurado
```

**Impacto**: Modo padrão do SQLite (`DELETE` journal, `synchronous=FULL`) é 2-3x mais lento para writes em batch. WAL mode permitiria leitores simultâneos sem bloquear o escritor.

---

### 5.3 `split_paymnt_resume` — `pd.to_datetime()` desnecessário

**Arquivo**: `pdw/analytics/totals.py:40`

```python
df_parcelamentos['Ano_Mes'] = pd.to_datetime(df_parcelamentos['Data']).dt.to_period('M')
```

`Data` já está em formato ISO `YYYY-MM-DD` no banco. O `pd.to_datetime()` faz parse completo quando `dt.strftime('%Y-%m')` seria suficiente e mais rápido:

```python
# Mais eficiente — sem conversão para Period
df_parcelamentos['Ano_Mes'] = pd.to_datetime(df_parcelamentos['Data']).dt.strftime('%Y-%m')
```

---

## 6. Concorrência e Threading — 🔴 BLOQUEADO

### 6.1 Threading permanentemente desabilitado

**Arquivo**: `pdw/core/orchestrator.py:89-112`

```python
if run_loader:
    if not multithread:
        new_data_loader(...)
    else:
        print(f'Bad, Bad Server. Not donuts for you')
        # ... 15 linhas de output educativo ...
        exit(1)
```

**Análise**: O código morto de threading representa uma oportunidade de paralelismo nunca implementada. A decisão de usar `exit(1)` em vez de `raise ValueError` torna impossível ativar threading de forma segura no futuro sem alterar o ponto de saída.

**Paralelismo possível sem threading**:
1. Leitura das abas Excel: paralelizável (cada thread lê aba diferente, sem estado compartilhado)
2. Sanitização: paralelizável por aba
3. Escrita no SQLite: deve ser serial (um writer)

---

## 7. Testabilidade — 🟠 ALTO (Score: 6/10)

### 7.1 `exit(1)` em funções de negócio impede teste unitário

```python
# Em load_config():
exit(1)  # ← impossível testar sem SystemExit

# Em orchestrator.py:
exit(1)  # ← impossível testar a lógica pós-erro

# Em xlsx_report_generator():
exit(1)  # ← impossível testar queries inválidas
```

**Impacto**: Todo teste de path de erro requer `with pytest.raises(SystemExit)` — frágil e verboso.

---

### 7.2 Conexões SQLite não injetáveis

Todas as funções abrem sua própria conexão via `sqlite3.connect(db_path)`. Para testar sem arquivo real:
```python
# Impossível injetar conexão em memória
conn = sqlite3.connect(":memory:")
create_pivot_history(":memory:", ...)  # passa path, não conexão
```

Para testar isoladamente é necessário criar arquivos temporários — mais lento e com dependências de FS.

---

### 7.3 `_OPTIONAL_DEPS_AVAILABLE` não redefinível entre testes

```python
# novos_relatorios.py — estado de módulo definido em import time
_OPTIONAL_DEPS_AVAILABLE = True  # ou False
```

Para testar o branch `not _OPTIONAL_DEPS_AVAILABLE`, é necessário:
```python
import pdw.reports.novos_relatorios as nr
nr._OPTIONAL_DEPS_AVAILABLE = False  # monkey patch direto
```

Frágil — qualquer reimportação reseta o valor.

---

## 8. Scores por Módulo

| Módulo | Conexão | Acoplamento | IO | Testabilidade | Score Risco |
|---|---|---|---|---|---|
| `pdw/analytics/pivot.py` | 🔴 9 | 🟡 5 | 🟠 7 | 🟡 5 | **6.5/10** |
| `pdw/analytics/totals.py` | 🔴 9 | 🟡 4 | 🟡 4 | 🟡 5 | **6.0/10** |
| `pdw/reports/xlsx_generator.py` | 🟡 4 | 🔴 9 | 🟡 5 | 🟠 7 | **6.5/10** |
| `pdw/core/orchestrator.py` | 🟢 2 | 🟠 8 | 🟡 4 | 🟠 7 | **5.5/10** |
| `pdw/etl/sanitizer.py` | 🟢 2 | 🟠 7 | 🟢 2 | 🟡 5 | **4.0/10** |
| `pdw/utils/xml_utils.py` | 🟢 1 | 🟢 2 | 🔴 8 | 🟢 2 | **3.5/10** |
| `pdw/analytics/totals.py` | 🔴 9 | 🟡 4 | 🟢 3 | 🟡 5 | **5.5/10** |
| `pdw/etl/loader.py` | 🟢 2 | 🟡 5 | 🟡 5 | 🟡 5 | **4.0/10** |
| `pdw/database/operations.py` | 🟢 1 | 🟢 2 | 🟢 1 | 🟢 3 | **2.0/10** |
| `pdw/utils/localization.py` | 🟢 1 | 🟢 1 | 🟢 1 | 🟢 1 | **1.0/10** |
| **SISTEMA COMPLETO** | | | | | **🟠 6.8/10** |

---

## 9. Plano de Remediação Priorizado

### P0 — Imediato (impacto em produção)

```
[P0-1] Adicionar conn.close() em create_pivot_history        → analytics/pivot.py
[P0-2] Adicionar conn.commit() + conn.close() em monthly_summaries → analytics/totals.py
[P0-3] Adicionar conn.commit() + conn.close() em split_paymnt_resume → analytics/totals.py
[P0-4] Substituir concatenação de paths por os.path.join()   → orchestrator.py
```

### P1 — Alta prioridade (qualidade e manutenibilidade)

```
[P1-1] Refatorar xlsx_report_generator para receber dataclass em vez de 15 params
[P1-2] Adicionar CREATE INDEX após carga ETL                 → etl/loader.py
[P1-3] Configurar PRAGMA WAL + cache em todas as conexões    → database/operations.py
[P1-4] Substituir iterrows() por df.to_xml() em dataframe_to_xml → utils/xml_utils.py
```

### P2 — Médio prazo (testabilidade e robustez)

```
[P2-1] Substituir exit(1) por exceções customizadas em todos os módulos
[P2-2] Implementar context manager para conexões SQLite
[P2-3] Mover nomes hardcoded de data_correjeitor para parâmetros
[P2-4] Converter get_month_names() / get_weekday_names() em constantes de módulo
[P2-5] Eliminar double-read de Excel em create_dinamic_reports
```

### P3 — Longo prazo (evolução arquitetural)

```
[P3-1] Implementar SELECT com GROUP BY no SQL (evitar carregamento de 50k linhas)
[P3-2] Adicionar streaming via chunksize em xlsx_report_generator
[P3-3] Implementar injeção de conexão para testabilidade
[P3-4] Definir domínio de tabelas válidas (allowlist) centralizado
```
