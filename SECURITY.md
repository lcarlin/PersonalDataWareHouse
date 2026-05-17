# SECURITY.md
## Personal Data Warehouse — Hardening Arquitetural de Segurança
### Versão 10.1.0 | Análise: 2026-05-17

---

## Scores Globais

| Dimensão | Score | Escala | Tendência |
|---|---|---|---|
| **Risco Geral** | **7.2 / 10** | 1=baixo risco, 10=crítico | ↑ requer ação |
| **SQL Injection** | **8.5 / 10** | 1=seguro, 10=crítico | ↑ crítico |
| **Path Safety** | **6.0 / 10** | 1=seguro, 10=crítico | → monitorar |
| **Input Validation** | **4.5 / 10** | 1=seguro, 10=crítico | → monitorar |
| **Secret Exposure** | **2.0 / 10** | 1=seguro, 10=crítico | ↓ ok |

**Escala de severidade**:

| Nível | Cor | Critério |
|---|---|---|
| CRÍTICO | 🔴 | Exploração trivial, impacto destrutivo |
| ALTO | 🟠 | Exploração possível com acesso local, impacto alto |
| MÉDIO | 🟡 | Exploração requer condições específicas |
| BAIXO | 🟢 | Impacto cosmético ou teórico |
| INFO | ⚪ | Observação de qualidade, sem risco direto |

---

## 1. SQL Injection por Concatenação de String — 🔴 CRÍTICO

### 1.1 `table_droppator` — concatenação pura

**Arquivo**: `pdw/database/operations.py:3`

```python
# VULNERÁVEL — table_name concatenado sem sanitização
def table_droppator(conexao, table_name):
    cursor = conexao
    cursor.execute("DROP TABLE IF EXISTS " + table_name)
```

**Vetor**: Qualquer chamador que passe `table_name` derivado de input externo (ex: aba GUIDING do Excel) pode injetar SQL arbitrário.

```python
# Exemplo de exploit via planilha Excel (coluna TABLE_NAME da aba GUIDING):
# TABLE_NAME = "foo; DROP TABLE LANCAMENTOS_GERAIS; --"
# → cursor.execute("DROP TABLE IF EXISTS foo; DROP TABLE LANCAMENTOS_GERAIS; --")
```

**Impacto**: Destruição de qualquer tabela no banco SQLite, incluindo `LANCAMENTOS_GERAIS`.

**Mitigação obrigatória**:
```python
import re

_VALID_TABLE_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]{0,63}$')

def table_droppator(conexao, table_name: str) -> None:
    if not _VALID_TABLE_RE.match(table_name):
        raise ValueError(f"Nome de tabela inválido: {table_name!r}")
    cursor = conexao
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
```

---

### 1.2 `data_correjeitor` — múltiplas queries com nomes hardcoded e concatenados

**Arquivo**: `pdw/etl/sanitizer.py:60-80`

```python
# VULNERÁVEL — entries_table e types_sheet concatenados diretamente
lista_acoes.append((f"create table {useless_table} as select * from {entries_table} ...", "..."))
lista_acoes.append((f"Delete from {types_sheet} WHERE ...", "..."))
lista_acoes.append((f'DROP VIEW IF EXISTS Origens; ', "..."))
lista_acoes.append((f"create view Origens as select TABLE_NAME as nome from GUIDING ...", "..."))
```

**Problema duplo**:
1. `useless_table`, `entries_table`, `types_sheet` são concatenados em SQL
2. `Parcelamentos`, `GUIDING`, `Origens` estão hardcoded — se o usuário nomear a tabela de forma diferente no .cfg, estas queries operam na tabela errada silenciosamente

**Impacto**: SQL arbitrário se qualquer um dos parâmetros contiver `;`.

**Mitigação**:
```python
# Validar TODOS os nomes de tabela antes de qualquer execução
_ALLOWED = frozenset({
    'LANCAMENTOS_GERAIS', 'TiposLancamentos', 'PARCELAMENTOS',
    'GUIDING', 'Origens', 'discarted_data', 'HistoricoGeral', 'HistoricoAnual'
})

def _safe_table(name: str) -> str:
    if name not in _ALLOWED and not re.match(r'^[A-Za-z_][A-Za-z0-9_]{0,63}$', name):
        raise ValueError(f"Nome de tabela não permitido: {name!r}")
    return f'"{name}"'
```

---

### 1.3 `totalizador_diario` — f-string direta em SQL

**Arquivo**: `pdw/analytics/totals.py:8`

```python
# VULNERÁVEL
df = pd.read_sql_query(f"select * from {in_table}", conn)
```

**Contexto**: `in_table` vem de `cfg['general_entries_table']` → do arquivo `.cfg` → controlado pelo usuário local. Risco menor que o 1.1, mas o padrão é perigoso.

---

### 1.4 `monthly_summaries` — múltiplas f-strings em SQL

**Arquivo**: `pdw/analytics/totals.py:16`

```python
sql_statment = f'SELECT * FROM {in_table} ;'
df_entrada = pd.read_sql(sql_statment, db_conn)
# ... e também:
df_agrupado.to_sql(out_table, db_conn, ...)         # out_table concatenado em SQL interno
df_agrupado_anual.to_sql(out_table + '_ANUAL', ...) # concatenação de sufixo em nome de tabela
```

---

### 1.5 `create_pivot_history` — f-strings em SELECT e coluna dinâmica

**Arquivo**: `pdw/analytics/pivot.py:8-10`

```python
sql_statment_types = f'SELECT Descrição as TIPO FROM {types_table} ;'
sql_statment_summary = f'SELECT * FROM {entries_table} ;'
```

**Agravante**: `pivot_full = pivot_full[df_types['TIPO']]` — usa valores de `Descrição` da tabela como nomes de colunas do pivot. Se um valor de `Descrição` contiver caracteres especiais, o pandas pode falhar ou produzir resultados inesperados.

---

### 1.6 `transient_data_exportator` — SQL injection via valor de dado

**Arquivo**: `pdw/utils/transient_data.py:16-22`

```python
# VULNERÁVEL — linhas.Origem é um valor do banco usado em SQL
sql_statment = f"SELECT * FROM {transient_data_table} where {origing_column} = '{linhas.Origem}' and EXPORT_DATE is null order by 1;"
conn.execute(f"UPDATE {transient_data_table} SET EXPORT_DATE = datetime('now') WHERE {origing_column} = '{linhas.Origem}'; ")
```

**Este é o caso mais grave**: `linhas.Origem` é um valor de dado vindo do próprio banco SQLite, que por sua vez vem do nome de abas do Excel. Se uma aba for nomeada `' OR '1'='1`, a query completa vaza.

**Mitigação**:
```python
# Usar parâmetros posicionais
cursor.execute(
    f"SELECT * FROM {transient_data_table} WHERE {origing_column} = ? AND EXPORT_DATE IS NULL ORDER BY 1",
    (linhas.Origem,)
)
cursor.execute(
    f"UPDATE {transient_data_table} SET EXPORT_DATE = datetime('now') WHERE {origing_column} = ?",
    (linhas.Origem,)
)
```

---

### 1.7 `create_dinamic_reports` — SQL construído de nomes de colunas do Excel

**Arquivo**: `pdw/analytics/pivot.py:54-67`

```python
# VULNERÁVEL — column_name vem diretamente de célula Excel
for j in df_single_sheet.index:
    column_name = df_single_sheet['COLUMN_NAME'][j]
    base_sql_string += "HG.'" + column_name + "',"
```

**Agravante**: `column_name` é conteúdo de célula Excel. Um valor como `'; DROP TABLE LANCAMENTOS_GERAIS; --` seria incorporado diretamente na query SQL.

---

### 1.8 `xlsx_report_generator` — queries do YAML injetadas sem validação

**Arquivo**: `pdw/reports/xlsx_generator.py:51-57`

```python
# SQL vem do arquivo YAML sem validação
sql = query_item['sql'].format(**variables)
# ...
df_out = pd.read_sql(sql_statment, connection)
```

**Contexto**: O YAML é controlado pelo usuário local. O risco é baixo para uso pessoal, mas alto em cenários multi-usuário.

---

## 2. Path Traversal — 🟠 ALTO

### 2.1 Construção de caminhos por concatenação de string

**Arquivo**: `pdw/core/orchestrator.py:56-65`

```python
# VULNERÁVEL — concatenação pura sem os.path.join e sem normalização
input_file = dir_file_in + in_file + '.' + in_type
pdw_sql_file = dir_file_in + queries_file
sqlite_database = dir_db + out_db + '.' + db_file_type
```

**Vetor**: Se `in_file = "../../../etc/cron.d/evil"` no .cfg:
```
dir_file_in + "../../../etc/cron.d/evil.xlsx"
→ /home/user/pdw/../../../etc/cron.d/evil.xlsx
→ /etc/cron.d/evil.xlsx (com permissão do usuário)
```

**Impacto**: Leitura de qualquer arquivo legível pelo processo; escrita em qualquer diretório gravável.

**Mitigação**:
```python
import pathlib

def safe_join(base: str, *parts: str) -> str:
    base_path = pathlib.Path(base).resolve()
    result = (base_path / pathlib.Path(*parts)).resolve()
    if not str(result).startswith(str(base_path)):
        raise ValueError(f"Path traversal detectado: {result}")
    return str(result)

input_file = safe_join(dir_file_in, in_file + '.' + in_type)
```

---

### 2.2 Ausência de validação de extensão de arquivo

**Arquivo**: `pdw/core/orchestrator.py:59-67`

O sistema valida se o arquivo Excel existe (`os.path.isfile(input_file)`) mas não valida a extensão nem o conteúdo (magic bytes). Um arquivo `.xlsx` corrompido ou malicioso pode causar comportamento inesperado no `openpyxl`.

---

## 3. Permissões e Exposição de Dados — 🟡 MÉDIO

### 3.1 Dados financeiros sem proteção de permissão de arquivo

**Arquivos gerados** (sem `chmod` explícito):
```
PDW.db            → herda umask do processo
PDW_REPORTS.v2.xlsx → herda umask do processo
*.csv, *.json.gz, *.xml.gz → herda umask do processo
```

**Problema**: Em sistemas multi-usuário com `umask 022`, todos os arquivos são `644` (legível por todos).

**Mitigação**:
```python
import os
os.chmod(sqlite_database, 0o600)   # após criação
os.chmod(report_file, 0o600)
```

---

### 3.2 Credenciais e caminhos sensíveis no log

**Arquivo**: `pdw/infrastructure/logging.py` + `pdw/core/orchestrator.py`

```python
# Linha de log expõe caminhos completos de arquivo e hostname
log_line = started + ' Started |' + ... + f'Version {current_version} | Hostname {hostname}'
```

O log não expõe senhas (não há autenticação), mas expõe:
- Hostname do servidor
- Caminhos completos dos diretórios
- Versão exata do sistema

**Impacto**: Baixo para uso pessoal. Relevante se o log for compartilhado.

---

## 4. Execução de Código via YAML — 🟡 MÉDIO

### 4.1 `yaml.safe_load` está sendo usado corretamente

**Arquivo**: `pdw/reports/xlsx_generator.py:19`

```python
queries_config = yaml.safe_load(file)  # ✅ SEGURO
```

O uso de `yaml.safe_load` é correto. Porém, as queries SQL dentro do YAML são executadas sem sanitização — um arquivo YAML com queries destrutivas (`DROP TABLE`, `DELETE FROM`) seria executado diretamente.

**Mitigação**: Implementar allowlist de comandos SQL permitidos no YAML (apenas `SELECT`).

---

## 5. Tratamento de Exceções — 🟠 ALTO

### 5.1 `exit(1)` impossibilita recuperação e testes

**Ocorrências confirmadas**:

| Arquivo | Linha | Condição |
|---|---|---|
| `pdw/config/loader.py` | ~25 | versão incompatível |
| `pdw/config/loader.py` | ~30 | arquivo .cfg não encontrado |
| `pdw/config/loader.py` | ~33 | erro de parsing |
| `pdw/core/orchestrator.py` | ~75 | DIR_IN inexistente |
| `pdw/core/orchestrator.py` | ~79 | DIR_OUT inexistente |
| `pdw/core/orchestrator.py` | ~83 | arquivo Excel inexistente |
| `pdw/core/orchestrator.py` | ~91 | MULTITHREADING=True |
| `pdw/reports/xlsx_generator.py` | ~35 | YAML não carregado |

**Impacto para testes**: `pytest.raises(SystemExit)` é necessário em todos os testes de erro — acoplamento com o mecanismo de exit do processo.

**Impacto para Java**: `System.exit(1)` em Java termina a JVM inteira, incluindo outros threads e shutdown hooks. Em Spring Batch, o padrão é lançar `JobExecutionException`.

**Mitigação para reescrita**:
```python
# Substituir exit(1) por exceções customizadas
class PdwConfigError(Exception): pass
class PdwVersionError(PdwConfigError): pass
class PdwDirectoryError(PdwConfigError): pass

# Em load_config:
raise PdwVersionError(f"Versão {parameters_version} != {CURRENT_VERSION}")

# Em main():
try:
    run_pipeline(param_file)
except PdwConfigError as e:
    print(e)
    sys.exit(1)
```

---

### 5.2 Erros vão para stdout, não stderr

**Arquivo**: Todos os módulos

```python
print(f'The Input Directory {dir_file_in} does not exists  !!! !! !')
exit(1)
```

**Impacto**: Scripts de monitoramento que capturam stderr (`2>/dev/null`) perdem as mensagens de erro. Redirecionamento de `>log.txt` captura tanto output normal quanto erros.

---

## 6. Estado Global de Módulo — 🟡 MÉDIO

### 6.1 `_OPTIONAL_DEPS_AVAILABLE` — estado mutável de módulo

**Arquivo**: `pdw/reports/novos_relatorios.py:8-13`

```python
try:
    import matplotlib.pyplot as plt
    # ...
    _OPTIONAL_DEPS_AVAILABLE = True
except ImportError as _e:
    _OPTIONAL_DEPS_AVAILABLE = False
    _OPTIONAL_DEPS_ERROR = str(_e)
```

**Problema para testes**: O estado é definido na importação do módulo e não pode ser redefinido entre testes sem reimportar o módulo. `monkeypatch.setattr` consegue contornar, mas é frágil.

---

### 6.2 Dicionários recriados a cada chamada

**Arquivo**: `pdw/utils/localization.py`

```python
def get_month_names():
    return {1: "01-Janeiro", 2: "02-Fevereiro", ...}  # novo dict a cada chamada
```

**Problema**: Cada chamada cria e descarta um dicionário de 12 entradas. Em loops sobre DataFrames grandes (via `.dt.month.map(meses)`), o `meses` dict é criado uma vez antes do `.map()` — ok. Mas o padrão de função vs constante é semanticamente errado.

**Mitigação**:
```python
# Constantes de módulo — criadas uma vez, reutilizadas sempre
MONTH_NAMES: dict[int, str] = {1: "01-Janeiro", ...}
WEEKDAY_NAMES: dict[int, str] = {0: "Segunda-feira", ...}

def get_month_names() -> dict[int, str]:
    return MONTH_NAMES  # retorna referência, não nova instância
```

---

## 7. Tabela Consolidada de Vulnerabilidades

| ID | Vulnerabilidade | Arquivo | Severidade | Score | Mitigado? |
|---|---|---|---|---|---|
| SEC-01 | SQL injection via `table_droppator` | `database/operations.py:3` | 🔴 CRÍTICO | 9/10 | Não |
| SEC-02 | SQL injection via `data_correjeitor` | `etl/sanitizer.py:60-80` | 🔴 CRÍTICO | 8/10 | Não |
| SEC-03 | SQL injection via `transient_data_exportator` | `utils/transient_data.py:16-22` | 🔴 CRÍTICO | 9/10 | Não |
| SEC-04 | SQL injection via `create_dinamic_reports` | `analytics/pivot.py:54-67` | 🔴 CRÍTICO | 8/10 | Não |
| SEC-05 | SQL injection em analytics (f-strings) | `analytics/totals.py`, `pivot.py` | 🟠 ALTO | 7/10 | Não |
| SEC-06 | Path traversal por concatenação | `core/orchestrator.py:56-65` | 🟠 ALTO | 6/10 | Não |
| SEC-07 | YAML queries sem allowlist de comandos | `reports/xlsx_generator.py:65` | 🟡 MÉDIO | 5/10 | Parcial |
| SEC-08 | Permissões de arquivo sem `chmod` | todos os outputs | 🟡 MÉDIO | 4/10 | Não |
| SEC-09 | `exit(1)` impossibilita tratamento | config/loader.py, orchestrator | 🟠 ALTO | 6/10 | Não |
| SEC-10 | Erros em stdout em vez de stderr | todos | 🟢 BAIXO | 2/10 | Não |
| SEC-11 | Estado global imutável em módulo | `novos_relatorios.py:8-13` | 🟡 MÉDIO | 3/10 | Sim (funciona) |
| SEC-12 | Dicionários recriados a cada chamada | `utils/localization.py` | ⚪ INFO | 1/10 | N/A |

---

## 8. Modelo de Confiança Revisado

```
[Usuário local]
    ↓ CONFIÁVEL
[PersonalDataWareHouse.cfg]
    ↓ CONFIÁVEL (mas pode ter path traversal)
[PDW processo]
    ↓ NÃO CONFIÁVEL — validar antes de usar em SQL
[PDW.xlsx — dados de entrada]
    ↓ NÃO CONFIÁVEL — nomes de abas, valores de células
[PDW_QUERIES.yaml]
    ↓ SEMI-CONFIÁVEL — queries são executadas como-está
```

**Premissa de segurança atual**: O .cfg e o .yaml são controlados pelo usuário local — portanto confiáveis. O risco real é SQL injection via dados do Excel (nomes de abas e valores de células).

---

## 9. Checklist de Hardening

```
[ ] SEC-01: Substituir concatenação em table_droppator por validação + aspas duplas
[ ] SEC-02: Validar todos os nomes de tabela em data_correjeitor antes de executar
[ ] SEC-03: Substituir f-string por parâmetros posicionais em transient_data_exportator
[ ] SEC-04: Validar column_name em create_dinamic_reports (whitelist de caracteres)
[ ] SEC-05: Substituir f-strings em totalizador_diario, monthly_summaries, split_paymnt_resume
[ ] SEC-06: Substituir concatenação de path por pathlib.Path com verificação de traversal
[ ] SEC-07: Adicionar validação de SELECT-only nas queries YAML
[ ] SEC-08: Adicionar os.chmod(600) após criação de banco e relatórios
[ ] SEC-09: Substituir exit(1) por exceções customizadas + captura em main()
[ ] SEC-10: Redirecionar mensagens de erro para sys.stderr
[ ] SEC-11: Converter get_month_names() em constante de módulo
```

---

## 10. Score de Risco por Módulo

| Módulo | SQL Inj | Path | Exc | Estado | Score Final |
|---|---|---|---|---|---|
| `pdw/database/operations.py` | 🔴 9 | ⚪ 0 | ⚪ 0 | ⚪ 0 | **7.2/10** |
| `pdw/etl/sanitizer.py` | 🔴 8 | ⚪ 0 | 🟢 1 | ⚪ 0 | **6.0/10** |
| `pdw/utils/transient_data.py` | 🔴 9 | 🟡 3 | 🟢 1 | ⚪ 0 | **7.5/10** |
| `pdw/analytics/pivot.py` | 🔴 8 | ⚪ 0 | ⚪ 0 | ⚪ 0 | **6.0/10** |
| `pdw/analytics/totals.py` | 🟠 7 | ⚪ 0 | ⚪ 0 | ⚪ 0 | **5.0/10** |
| `pdw/core/orchestrator.py` | 🟢 1 | 🟠 6 | 🟠 7 | ⚪ 0 | **4.7/10** |
| `pdw/config/loader.py` | 🟢 1 | 🟡 3 | 🟠 7 | ⚪ 0 | **3.7/10** |
| `pdw/reports/xlsx_generator.py` | 🟡 5 | 🟢 1 | 🟠 6 | ⚪ 0 | **4.0/10** |
| `pdw/reports/exporter.py` | 🟡 4 | 🟢 2 | ⚪ 0 | ⚪ 0 | **2.5/10** |
| `pdw/utils/localization.py` | ⚪ 0 | ⚪ 0 | ⚪ 0 | 🟢 1 | **0.5/10** |
| **SISTEMA COMPLETO** | | | | | **🔴 7.2/10** |
