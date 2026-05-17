# DEPLOY_GUIDE.md
## Personal Data Warehouse — Guia Completo de Deploy e Configuração
### Versão 10.1.0

---

## 1. Pré-requisitos

### 1.1 Runtime

| Componente | Versão mínima | Notas |
|---|---|---|
| Python | 3.9+ | 3.9+ obrigatório para `ET.indent()` |
| SQLite3 | 3.35.0+ | Embutido no Python; `RETURNING` requer 3.35+ |
| Sistema Operacional | Linux, macOS, Windows | Testado em Linux (Ubuntu 22+) e Windows 10/11 |

### 1.2 Dependências Python

```bash
pip install pandas>=1.5.0 numpy>=1.23.0 openpyxl>=3.0.0 xlrd>=2.0.0 xlsxwriter>=3.0.0 PyYAML>=6.0.0
```

Ou via script:
```bash
bash InstalaDependencias.sh
```

### 1.3 Dependências Opcionais (relatórios analíticos avançados)

```bash
pip install matplotlib>=3.6.0 seaborn>=0.12.0 scipy>=1.9.0 fpdf2>=2.7.0
```

---

## 2. Estrutura de Diretórios em Runtime

```
/caminho/de/trabalho/
├── PDW.xlsx                  ← arquivo de entrada (configurável em INPUT_FILE)
├── PDW_QUERIES.yaml          ← queries SQL para relatórios (configurável em YAML_SQL_FILE)
├── PersonalDataWareHouse.cfg ← configuração principal
│
├── PDW.db                    ← banco SQLite gerado
│
├── PDW_REPORTS.v2.xlsx       ← relatório Excel gerado
├── PDW_REPORTS.v2.YYYYMMDD.HHMMSS.csv      ← exportação CSV (se EXPORT_OTHER_TYPES=True)
├── PDW_REPORTS.v2.YYYYMMDD.HHMMSS.json.gz  ← exportação JSON gzip
├── PDW_REPORTS.v2.YYYYMMDD.HHMMSS.xml.gz   ← exportação XML gzip
│
└── PDW.lnx.log               ← arquivo de log (configurável em LOG_FILE)
```

---

## 3. Arquivo de Configuração: `PersonalDataWareHouse.cfg`

### Formato

Formato INI padrão (`configparser` Python). Sensível a espaços em branco nos valores.

```ini
[DIRECTORIES]
DIR_IN = /caminho/para/entrada/
DIR_OUT = /caminho/para/saida/
DATABASE_DIR = /caminho/para/banco/
LOG_DIR = /caminho/para/logs/

[FILE_TYPES]
TYPE_IN = xlsx
TYPE_OUT = xlsx
DB_FILE_TYPE = db
LOG_FILE = PDW.lnx.log
INPUT_FILE = PDW
OUT_DB_FILE = PDW
OUT_RPT_FILE = PDW_REPORTS.v2
TRANSIENT_DATA_FILE = Lancamentos_Gerais_TMP

[SETTINGS]
CURRENT_VERSION = 10.1.0
API_VERSION = 2.0.0
GUIDING_TABLE = GUIDING
TYPES_OF_ENTRIES = TiposLancamentos
GENERAL_ENTRIES_TABLE = LANCAMENTOS_GERAIS
RUN_DATA_LOADER = False
RUN_REPORTS = True
OVERWRITE_DB = True
CREATE_PIVOT = True
RPT_SINGLE_FILE = True
PARALLELS = 89
MULTITHREADING = False
SAVE_DISCARTED_DATA = False
DISCARTED_DATA_TABLE = discarted_data
ANUAL_PIVOT_TABLE = HistoricoAnual
FULL_PIVOT_TABLE = HistoricoGeral
RUN_DINAMIC_REPORT = True
DIN_REPORT_GUIDING = General_din_reports
EXPORT_TRANSIENT_DATA = False
TRANSIENT_DATA_TABLE = Transient_data
TRANSIENT_DATA_COLUMN = Origem
EXPORT_OTHER_TYPES = False
DAYLY_PROGRESS = contagem_diaria
SPLT_PAYMNT_TAB = PARCELAMENTOS
OUT_RES_PMNT_TAB = Resumo_Parcelamentos
MONTHLY_SUMMATIES = Resumido_In_Out
YAML_SQL_FILE = PDW_QUERIES.yaml
```

---

## 4. Referência Completa de Parâmetros

### Seção `[DIRECTORIES]`

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `DIR_IN` | string (path) | Sim | Diretório de entrada (Excel + YAML). Deve terminar com `/`. Deve existir. |
| `DIR_OUT` | string (path) | Sim | Diretório de saída (relatórios). Deve terminar com `/`. Deve existir. |
| `DATABASE_DIR` | string (path) | Sim | Diretório do banco SQLite. Deve terminar com `/`. Deve existir. |
| `LOG_DIR` | string (path) | Sim | Diretório dos arquivos de log. Deve terminar com `/`. Deve existir. |

**Notas:**
- Caminhos relativos são resolvidos a partir do diretório de execução do script.
- No Windows, use barras invertidas duplas (`\\`) ou barras simples (`/`).
- Todos os diretórios devem ter permissão de leitura e escrita.

---

### Seção `[FILE_TYPES]`

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `TYPE_IN` | string | `xlsx` | Extensão do arquivo de entrada Excel. Suporta `xlsx` (openpyxl) e `xls` (xlrd). |
| `TYPE_OUT` | string | `xlsx` | Extensão dos arquivos de relatório. Atualmente apenas `xlsx` é usado. |
| `DB_FILE_TYPE` | string | `db` | Extensão do banco de dados SQLite. Convenção: `db` ou `sqlite3`. |
| `LOG_FILE` | string | `PDW.lnx.log` | Nome do arquivo de log (sem caminho — caminho vem de `LOG_DIR`). |
| `INPUT_FILE` | string | `PDW` | Nome do arquivo Excel de entrada (sem extensão). Arquivo completo: `DIR_IN + INPUT_FILE + '.' + TYPE_IN`. |
| `OUT_DB_FILE` | string | `PDW` | Nome base do banco SQLite (sem extensão). Arquivo completo: `DATABASE_DIR + OUT_DB_FILE + '.' + DB_FILE_TYPE`. |
| `OUT_RPT_FILE` | string | `PDW_REPORTS.v2` | Nome base dos relatórios de saída. |
| `TRANSIENT_DATA_FILE` | string | `Lancamentos_Gerais_TMP` | Nome base para exportação de dados transientes (feature desabilitada). |

---

### Seção `[SETTINGS]`

| Parâmetro | Tipo | Padrão | Obrigatório | Descrição |
|---|---|---|---|---|
| `CURRENT_VERSION` | string | — | **Sim** | Deve corresponder exatamente a `__version__` em `pdw/__init__.py`. Mismatch causa `exit(1)`. |
| `API_VERSION` | string | `2.0.0` | Não | Versão da API — documentação interna, não usado em código. |
| `GUIDING_TABLE` | string | `GUIDING` | Sim | Nome da aba Excel que contém a configuração de quais sheets processar. |
| `TYPES_OF_ENTRIES` | string | `TiposLancamentos` | Sim | Nome da aba Excel e tabela SQLite de tipos de lançamentos. |
| `GENERAL_ENTRIES_TABLE` | string | `LANCAMENTOS_GERAIS` | Sim | Nome da tabela SQLite consolidada de lançamentos. |
| `RUN_DATA_LOADER` | boolean | `False` | Não | `True`: executa ETL (Excel→SQLite). `False`: pula ETL (usa DB existente). |
| `RUN_REPORTS` | boolean | `True` | Não | `True`: gera relatórios a partir do SQLite. |
| `OVERWRITE_DB` | boolean | `True` | Não | `True`: sobrescreve DB existente. `False`: cria DB com timestamp no nome. |
| `CREATE_PIVOT` | boolean | `True` | Não | `True`: cria tabelas pivot históricas mensais e anuais. |
| `RPT_SINGLE_FILE` | boolean | `True` | Não | `True`: todos os relatórios em um único `.xlsx`. Comportamento atual. |
| `PARALLELS` | int | `89` | Não | Número de threads paralelas — **ignorado**. Feature desabilitada (MULTITHREADING=False). |
| `MULTITHREADING` | boolean | `False` | Não | **Sempre deve ser `False`**. `True` causa `exit(1)` imediato. |
| `SAVE_DISCARTED_DATA` | boolean | `False` | Não | `True`: salva no SQLite registros com TIPO ou Data nulos (descartados na limpeza). |
| `DISCARTED_DATA_TABLE` | string | `discarted_data` | Não | Nome da tabela SQLite para dados descartados (usado se `SAVE_DISCARTED_DATA=True`). |
| `ANUAL_PIVOT_TABLE` | string | `HistoricoAnual` | Não | Nome da tabela SQLite para pivot anual. |
| `FULL_PIVOT_TABLE` | string | `HistoricoGeral` | Não | Nome da tabela SQLite para pivot histórico completo. |
| `RUN_DINAMIC_REPORT` | boolean | `True` | Não | `True`: executa relatórios dinâmicos configurados na aba `DIN_REPORT_GUIDING`. |
| `DIN_REPORT_GUIDING` | string | `General_din_reports` | Não | Nome da aba Excel que configura relatórios dinâmicos. |
| `EXPORT_TRANSIENT_DATA` | boolean | `False` | Não | Feature comentada no código. Não tem efeito funcional na versão atual. |
| `TRANSIENT_DATA_TABLE` | string | `Transient_data` | Não | Nome da tabela de dados transientes (feature desabilitada). |
| `TRANSIENT_DATA_COLUMN` | string | `Origem` | Sim | Nome da coluna que identifica a origem/fonte de cada lançamento. |
| `EXPORT_OTHER_TYPES` | boolean | `False` | Não | `True`: exporta também CSV, JSON.gz e XML.gz além do Excel. |
| `DAYLY_PROGRESS` | string | `contagem_diaria` | Não | Nome da tabela SQLite para totalização diária. |
| `SPLT_PAYMNT_TAB` | string | `PARCELAMENTOS` | Sim | Nome da aba Excel e tabela SQLite de parcelamentos. |
| `OUT_RES_PMNT_TAB` | string | `Resumo_Parcelamentos` | Não | Nome da aba no relatório Excel para resumo de parcelamentos. |
| `MONTHLY_SUMMATIES` | string | `Resumido_In_Out` | Não | Nome da aba no relatório Excel para sumarizações mensais. |
| `YAML_SQL_FILE` | string | `PDW_QUERIES.yaml` | Sim | Nome do arquivo YAML com queries SQL para relatórios (sem caminho — resolve com `DIR_IN`). |

---

## 5. Arquivo YAML de Queries: `PDW_QUERIES.yaml`

### Formato Esperado

```yaml
---
# Cada chave de primeiro nível vira uma aba no Excel de relatório
NomeAbaExcel:
  query: "SELECT ... FROM tabela WHERE ..."

OutraAba:
  query: |
    SELECT colA, colB
    FROM LANCAMENTOS_GERAIS
    WHERE strftime('%Y', Data) = '2025'
    ORDER BY Data DESC
```

### Localização

O arquivo é lido de: `DIR_IN + YAML_SQL_FILE`

### Comportamento

- Cada chave do YAML se torna uma aba no arquivo Excel de relatório.
- As queries são executadas contra o banco SQLite configurado.
- Sem limite de queries — cada uma vira uma aba separada.
- A aba é omitida se a query retornar 0 linhas (comportamento do pandas).

---

## 6. Arquivo Excel de Entrada: `PDW.xlsx`

### Abas Obrigatórias

| Aba | Descrição | Colunas requeridas |
|---|---|---|
| `GUIDING` (configurável) | Configuração: quais abas processar | `TABLE_NAME`, `ACCOUNTING`, `LOADABLE` |
| `TiposLancamentos` (configurável) | Tabela de tipos/categorias de lançamentos | Importada como-está |
| `PARCELAMENTOS` (configurável) | Dados de compras parceladas | Importada como-está |

### Estrutura da Aba GUIDING

| Coluna | Tipo | Valores | Descrição |
|---|---|---|---|
| `TABLE_NAME` | string | qualquer | Nome da aba Excel a processar |
| `ACCOUNTING` | string | `X` ou vazio | `X` = planilha contábil (tem colunas Data/TIPO/etc.) |
| `LOADABLE` | string | `X` ou vazio | `X` = aba será carregada no banco |

### Estrutura das Abas Contábeis

| Coluna | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `Data` | date | Sim | Data do lançamento |
| `TIPO` | string | Sim | Tipo/categoria (referência para `TiposLancamentos`) |
| `DESCRICAO` | string | Sim | Descrição do lançamento |
| `Credito` | float | Sim | Valor de crédito (entrada) |
| `Debito` | float | Sim | Valor de débito (saída) |

---

## 7. Modos de Execução

### 7.1 Modo Padrão (CLI)

```bash
# Usa PersonalDataWareHouse.cfg no diretório atual
python PersonalDataWareHouse.py

# Config customizado
python PersonalDataWareHouse.py /caminho/para/custom.cfg
```

### 7.2 Modo Pacote

```bash
python -m pdw
python -m pdw /caminho/para/custom.cfg
```

### 7.3 Via Script Linux

```bash
bash RunPDW.sh
# RunPDW.sh implementa lock (via mkdir) para evitar execuções simultâneas
```

### 7.4 Via PowerShell (Windows)

```powershell
.\RunPDW.ps1
# ou
.\Run_PDW.bat
```

---

## 8. Flags de Controle de Pipeline

```
RUN_DATA_LOADER=True   → Executa ETL completo
RUN_DATA_LOADER=False  → Pula ETL (usa DB existente)

RUN_REPORTS=True       → Gera relatórios
RUN_REPORTS=False      → Pula relatórios

CREATE_PIVOT=True      → Cria pivot tables históricas
CREATE_PIVOT=False     → Pula pivot

RUN_DINAMIC_REPORT=True  → Gera relatórios dinâmicos por aba
RUN_DINAMIC_REPORT=False → Pula relatórios dinâmicos

EXPORT_OTHER_TYPES=True  → Gera CSV + JSON.gz + XML.gz
EXPORT_OTHER_TYPES=False → Apenas Excel
```

---

## 9. Cenários de Deploy

### 9.1 Execução Única (batch manual)

```bash
cd /home/user/pdw
python PersonalDataWareHouse.py
```

### 9.2 Agendamento via cron (Linux)

```cron
# Executar PDW às 23:00 todo dia
0 23 * * * cd /home/user/pdw && bash RunPDW.sh >> /home/user/pdw/cron.log 2>&1
```

### 9.3 Agendamento via Task Scheduler (Windows)

```
Programa: C:\Python313\python.exe
Argumentos: C:\pdw\PersonalDataWareHouse.py
Diretório inicial: C:\pdw
```

### 9.4 Modo Apenas Relatórios (sem recarregar dados)

```ini
[SETTINGS]
RUN_DATA_LOADER = False
RUN_REPORTS = True
OVERWRITE_DB = True  # não importa quando RUN_DATA_LOADER=False
```

### 9.5 Modo Apenas ETL (sem gerar relatórios)

```ini
[SETTINGS]
RUN_DATA_LOADER = True
RUN_REPORTS = False
```

---

## 10. Diagnóstico de Problemas Comuns

| Sintoma | Causa | Solução |
|---|---|---|
| `The version in parameter file ... does not Match` | Versão no .cfg diferente de `pdw/__init__.__version__` | Atualizar `CURRENT_VERSION` no .cfg |
| `The Input Directory X does not exists` | `DIR_IN` inválido ou sem permissão | Verificar caminho e permissões |
| `Configuration file X not found` | .cfg não encontrado no diretório de execução | Executar do diretório correto ou passar caminho completo |
| `ExcelFile X not found` | Arquivo Excel não encontrado em `DIR_IN` | Verificar `INPUT_FILE` e `DIR_IN` |
| Saída sem dados | `RUN_DATA_LOADER=False` com DB vazio | Executar com `RUN_DATA_LOADER=True` pelo menos uma vez |
| Execução duplicada | `RunPDW.sh` detecta lock (PID em arquivo) | Verificar se processo anterior terminou; remover lock manualmente |
| `MULTITHREADING` causa exit | `MULTITHREADING=True` no .cfg | Manter sempre `MULTITHREADING=False` |

---

## 11. Checklist de Deploy

```
[ ] Python 3.9+ instalado
[ ] pip install pandas openpyxl xlrd xlsxwriter numpy pyyaml
[ ] Diretórios DIR_IN, DIR_OUT, DATABASE_DIR, LOG_DIR criados
[ ] Permissões de leitura/escrita nos 4 diretórios
[ ] PDW.xlsx disponível em DIR_IN
[ ] PDW_QUERIES.yaml disponível em DIR_IN
[ ] PersonalDataWareHouse.cfg editado com caminhos corretos
[ ] CURRENT_VERSION = 10.1.0 no .cfg
[ ] MULTITHREADING = False no .cfg
[ ] Teste: python PersonalDataWareHouse.py (deve imprimir "Reading configuration file ... .. .")
```
