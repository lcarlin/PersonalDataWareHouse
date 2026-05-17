# LOGGING_GUIDE.md
## Personal Data Warehouse — Guia do Sistema de Log
### Versão 10.1.0

---

## 1. Visão Geral

O PDW usa um sistema de log simples baseado em **arquivo de texto plano** (`.log`), gerenciado pelo módulo `pdw/infrastructure/logging.py`. Não há dependências externas para logging — apenas stdlib Python (`os`, `datetime`, `open()`).

**Características:**
- Arquivo de log append-on-run (uma linha por execução bem-sucedida)
- Cada linha é delimitada por `|` (pipe)
- A última linha é lida no início para exibir a data da última execução
- Sem rotação automática — o arquivo cresce indefinidamente

---

## 2. Localização e Nome do Arquivo

```
LOG_DIR + LOG_FILE
```

Exemplos:
```
/home/user/pdw/PDW.lnx.log      # Linux
C:\pdw\PDW.win.log               # Windows (convenção)
```

O arquivo é criado automaticamente na primeira execução se não existir.

---

## 3. Formato do Arquivo de Log

### 3.1 Linha de Criação (primeira linha)

```
New LOG created at :-> DD/MM/YYYY HH:MM:SS
```

Exemplo:
```
New LOG created at :-> 13/12/2022 14:30:00
```

Esta linha é escrita apenas uma vez, na criação do arquivo.

---

### 3.2 Linha de Execução (uma por run)

```
YYYY/MM/DD HH:MM:SS | Version: X.Y.Z | Host: hostname | OS: Linux | Runs: N | Time: T.TTs | Last: PREV_DATE
```

**Campos (delimitados por ` | `):**

| Campo | Formato | Descrição |
|---|---|---|
| `YYYY/MM/DD HH:MM:SS` | `%Y/%m/%d %H:%M:%S` | Timestamp de início da execução |
| `Version: X.Y.Z` | string | Versão do PDW |
| `Host: hostname` | string | Nome do host (via `os.uname()` no Linux ou `platform.uname().node` no Windows) |
| `OS: Platform` | string | Sistema operacional (`Linux`, `Windows`, `Darwin`) |
| `Runs: N` | int | Número total de execuções anteriores (contagem de linhas do arquivo antes desta) |
| `Time: T.TTs` | float com 2 casas | Tempo total de execução em segundos |
| `Last: PREV_DATE` | string | Data/hora da execução anterior (primeira parte da linha anterior) |

---

### 3.3 Exemplo de Arquivo de Log Real

```
New LOG created at :-> 13/12/2022 14:30:00
2022/12/13 14:30:05 | Version: 1.0.0 | Host: desktop-lca | OS: Linux | Runs: 0 | Time: 12.43s | Last: none
2023/01/15 09:00:12 | Version: 2.0.0 | Host: desktop-lca | OS: Linux | Runs: 1 | Time: 15.87s | Last: 2022/12/13 14:30:05
2023/03/22 18:45:03 | Version: 5.2.1 | Host: desktop-lca | OS: Linux | Runs: 2 | Time: 9.21s | Last: 2023/01/15 09:00:12
2026/05/17 23:00:01 | Version: 10.1.0 | Host: server-pdw | OS: Linux | Runs: 3 | Time: 47.33s | Last: 2023/03/22 18:45:03
```

---

## 4. Fluxo de Gerenciamento do Log

### 4.1 Abertura (`open_log`)

```python
def open_log(log_file_cfg):
    # 1. Verifica se arquivo existe
    # 2. Se não existe: cria com linha "New LOG created at..."
    # 3. Abre em modo 'r+' (leitura e escrita sem truncar)
    # 4. Conta linhas (= número de runs anteriores)
    # 5. Lê última linha → extrai campo [0] como last_run_date
    # 6. Retorna (file_handle, number_of_runs, last_run_date)
```

**Casos especiais:**
- Arquivo vazio (`size == 0`): trata como 0 runs, last_run_date = `'none'`
- Arquivo inexistente: cria e trata como novo

---

### 4.2 Construção da Linha de Log (em `orchestrator.py`)

```python
elapsed = round(time.time() - start, 2)
log_line = (
    f"{started}"
    f" | Version: {current_version}"
    f" | Host: {hostname}"
    f" | OS: {os_pataform}"
    f" | Runs: {number_of_runs}"
    f" | Time: {elapsed}s"
    f" | Last: {last_run_date}\n"
)
```

---

### 4.3 Finalização (`finalize_log`)

```python
def finalize_log(log_file, log_line):
    log_file.write(log_line)   # append ao final
    log_file.close()
```

O handle está em modo `r+` com seek implícito ao final — a escrita ocorre ao final do arquivo.

---

## 5. Output de Console

Além do arquivo de log, o PDW imprime progresso no stdout. Este output não é redirecionado para o log.

### 5.1 Mensagens de Progresso

```
Reading configuration file ... .. .
Log File /path/to/PDW.lnx.log does Not Exists yet           ← primeira execução
Connecting to SQLite3 Database ... .. .
Reading Data from Guiding Sheet :->  GUIDING ... .. .
Running Loader of the Sheets into database Tables ... .. .
   . .. ... Step: 0001 ; Table (Sheet) :-> NomeDaAba         ; Lines Created :->    250
   . .. ... Step: 0002 ; Table (Sheet) :-> OutraAba          ; Lines Created :->    183
[...]
Running PDW Reports ... .. .
```

### 5.2 Mensagens de Erro

```
The version in parameter file X does not Match
Informed :-> 9.11.2
Expected :-> 10.1.0

The Input Directory /path/to/dir does not exists  !!! !! !
Configuration file X not found !
```

Todas as mensagens de erro vão para stdout (não stderr) e são seguidas de `exit(1)`.

---

## 6. Parsing do Arquivo de Log

### 6.1 Python

```python
import re

def parse_log(log_path):
    entries = []
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('New LOG') or not '|' in line:
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 7:
                continue
            entry = {
                'timestamp': parts[0],
                'version':   parts[1].replace('Version: ', ''),
                'host':      parts[2].replace('Host: ', ''),
                'os':        parts[3].replace('OS: ', ''),
                'runs':      int(parts[4].replace('Runs: ', '')),
                'time_s':    float(parts[5].replace('Time: ', '').replace('s', '')),
                'last_run':  parts[6].replace('Last: ', ''),
            }
            entries.append(entry)
    return entries
```

### 6.2 Shell (bash)

```bash
# Última execução
tail -1 PDW.lnx.log

# Tempo médio de execução
grep -v "^New LOG" PDW.lnx.log | awk -F'|' '{gsub(/Time: |s/, "", $6); sum+=$6; n++} END {print sum/n "s avg"}'

# Extrair todas as versões
grep -v "^New LOG" PDW.lnx.log | awk -F'|' '{print $2}' | sort | uniq -c
```

### 6.3 PowerShell

```powershell
Get-Content PDW.win.log |
    Where-Object { $_ -notmatch "^New LOG" -and $_ -like "*|*" } |
    ForEach-Object {
        $parts = $_ -split '\s*\|\s*'
        [PSCustomObject]@{
            Timestamp = $parts[0]
            Version   = $parts[1] -replace 'Version: ', ''
            Host      = $parts[2] -replace 'Host: ', ''
            TimeS     = [double]($parts[5] -replace 'Time: |s', '')
        }
    }
```

---

## 7. Monitoramento e Alertas

### 7.1 Detectar Execução Bem-Sucedida

Uma nova linha no log = execução concluída. Para monitoramento:

```bash
# Verificar se PDW rodou hoje
TODAY=$(date +%Y/%m/%d)
if grep -q "^$TODAY" /path/to/PDW.lnx.log; then
    echo "PDW executou hoje"
else
    echo "ALERTA: PDW não executou hoje"
fi
```

### 7.2 Detectar Execução Travada

O PDW não registra no log se terminar com `exit(1)`. Se `RUN_DATA_LOADER=True` mas o banco não foi atualizado, suspeitar de erro.

```bash
# Verificar data de modificação do banco vs última entrada do log
DB_MOD=$(stat -c %Y /path/to/PDW.db)
LOG_DATE=$(tail -1 /path/to/PDW.lnx.log | cut -d'|' -f1 | xargs -I{} date -d{} +%s)
if [ $((DB_MOD - LOG_DATE)) -gt 300 ]; then
    echo "ALERTA: banco mais antigo que o log"
fi
```

---

## 8. Limitações e Recomendações

| Limitação | Impacto | Recomendação |
|---|---|---|
| Sem rotação de arquivo | Log cresce indefinidamente | Implementar logrotate externo |
| Sem níveis de log (INFO/ERROR) | Impossível filtrar por severidade | Adicionar prefixo ao migrar |
| Erros vão para stdout, não log | Execuções com erro não são registradas | Redirecionar stdout+stderr para arquivo externo |
| Sem timestamps intra-execução | Impossível cronometrar etapas individuais | Adicionar `time.time()` por etapa ao migrar |
| Arquivo aberto em `r+` | Race condition se duas instâncias simultâneas | RunPDW.sh usa lock file para prevenir |

---

## 9. Equivalências em Outras Linguagens

### Java (SLF4J + Logback)

```xml
<!-- logback.xml equivalente -->
<appender name="FILE" class="ch.qos.logback.core.FileAppender">
    <file>${LOG_DIR}/PDW.log</file>
    <encoder>
        <pattern>%d{yyyy/MM/dd HH:mm:ss} | Version: ${VERSION} | Host: ${HOST} | %msg%n</pattern>
    </encoder>
</appender>
```

### Rust (tracing / log crate)

```rust
use std::fs::OpenOptions;
use std::io::Write;
// Simples append ao arquivo:
let mut file = OpenOptions::new().append(true).open(&log_path)?;
writeln!(file, "{} | Version: {} | ...", timestamp, version)?;
```

### Go (log package)

```go
f, _ := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
logger := log.New(f, "", 0)
logger.Printf("%s | Version: %s | Host: %s | ...", started, version, hostname)
```
