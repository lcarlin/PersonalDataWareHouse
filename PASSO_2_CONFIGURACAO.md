# PASSO 2 — CONFIGURAÇÃO
## Personal Data Warehouse v10.1.0
### Guia completo de configuração

---

## Visão geral

O PDW usa **dois arquivos de configuração** que você precisa ajustar:

| Arquivo | O que faz | Quão frequente edita |
|---|---|---|
| `PersonalDataWareHouse.cfg` | Define caminhos, nomes de arquivos e o que o PDW vai executar | Uma vez na instalação + quando mudar de pasta |
| `PDW_QUERIES.yaml` | Define as consultas SQL dos relatórios Excel | Quando quiser personalizar os relatórios |

---

## Parte 1 — Configurando o arquivo `PersonalDataWareHouse.cfg`

Este é o arquivo mais importante. Abra-o em qualquer editor de texto (Bloco de Notas, VS Code, Gedit, nano, etc.).

O arquivo tem **três seções**: `[DIRECTORIES]`, `[FILE_TYPES]` e `[SETTINGS]`.

---

### Seção `[DIRECTORIES]` — Onde ficam os arquivos

Esta seção define os caminhos das pastas usadas pelo PDW.

```ini
[DIRECTORIES]
DIR_IN =  /home/lcarlin/Dropbox/PDW_DRPBX/
DIR_OUT =  /home/lcarlin/Dropbox/PDW_DRPBX/
DATABASE_DIR = /home/lcarlin/Dropbox/PDW_DRPBX/
LOG_DIR = /home/lcarlin/Dropbox/PDW_DRPBX/
```

| Parâmetro | O que é | Exemplo Linux | Exemplo Windows |
|---|---|---|---|
| `DIR_IN` | Pasta onde está a planilha Excel de entrada | `/home/joao/dados/pdw/` | `C:\PDW\dados\` |
| `DIR_OUT` | Pasta onde serão salvos os relatórios gerados | `/home/joao/dados/pdw/` | `C:\PDW\dados\` |
| `DATABASE_DIR` | Pasta onde fica o banco de dados `.db` | `/home/joao/dados/pdw/` | `C:\PDW\dados\` |
| `LOG_DIR` | Pasta onde fica o arquivo de log | `/home/joao/dados/pdw/` | `C:\PDW\dados\` |

> **Dica prática**: Para começar, use a **mesma pasta** para todos os quatro caminhos. Isso simplifica o gerenciamento dos arquivos.

> **ATENÇÃO para Windows**: Use barras invertidas (`\`) e inclua a barra no final. Exemplo:
> ```ini
> DIR_IN = C:\Users\SeuNome\PDW\dados\
> ```

> **ATENÇÃO para caminhos com espaço no Windows**: Se o caminho tiver espaço (ex: `C:\Meus Documentos\`), **não use aspas** — o PDW não precisa e elas podem causar problemas.

---

### Seção `[FILE_TYPES]` — Nomes e extensões dos arquivos

```ini
[FILE_TYPES]
TYPE_IN = xlsx
TYPE_OUT = xlsx
DB_FILE_TYPE = db
LOG_FILE = PDW.lnx.log
INPUT_FILE = PDW
OUT_DB_FILE = PDW
OUT_RPT_FILE = PDW_REPORTS.v2
TRANSIENT_DATA_FILE = Lancamentos_Gerais_TMP
```

| Parâmetro | O que é | Valor padrão | Quando alterar |
|---|---|---|---|
| `TYPE_IN` | Extensão da planilha de entrada | `xlsx` | Raramente (não use `.xls`) |
| `TYPE_OUT` | Extensão dos arquivos de saída | `xlsx` | Raramente |
| `DB_FILE_TYPE` | Extensão do banco de dados | `db` | Nunca altere |
| `LOG_FILE` | Nome do arquivo de log | `PDW.lnx.log` | Se quiser outro nome; use `.win.log` no Windows |
| `INPUT_FILE` | Nome da planilha de entrada (sem extensão) | `PDW` | Se sua planilha tiver outro nome |
| `OUT_DB_FILE` | Nome do banco de dados (sem extensão) | `PDW` | Se quiser outro nome para o `.db` |
| `OUT_RPT_FILE` | Nome do relatório Excel de saída (sem extensão) | `PDW_REPORTS.v2` | Se quiser outro nome para o relatório |
| `TRANSIENT_DATA_FILE` | Nome do arquivo temporário de dados | `Lancamentos_Gerais_TMP` | Raramente |

**Exemplo**: Se `INPUT_FILE = PDW` e `TYPE_IN = xlsx`, o PDW vai procurar pelo arquivo `PDW.xlsx` na pasta `DIR_IN`.

---

### Seção `[SETTINGS]` — Comportamento do programa

Esta é a seção mais importante para o dia a dia. Aqui você controla **o que o PDW vai fazer** em cada execução.

```ini
[SETTINGS]
CURRENT_VERSION = 10.1.0
```

> **NUNCA altere `CURRENT_VERSION`**. O programa verifica se a versão no `.cfg` bate com a versão do código. Se não bater, ele se recusa a executar.

---

#### Controles principais de execução

| Parâmetro | O que faz | Valores | Padrão |
|---|---|---|---|
| `RUN_DATA_LOADER` | Carrega dados da planilha Excel para o banco | `True` / `False` | `False` |
| `RUN_REPORTS` | Gera os relatórios Excel de saída | `True` / `False` | `True` |
| `OVERWRITE_DB` | Apaga e recria o banco do zero antes de carregar | `True` / `False` | `True` |

**Combinações comuns:**

| Situação | RUN_DATA_LOADER | RUN_REPORTS | OVERWRITE_DB |
|---|---|---|---|
| Carregar dados novos E gerar relatórios | `True` | `True` | `True` |
| Apenas gerar relatórios (dados já carregados) | `False` | `True` | `False` |
| Apenas carregar dados, sem gerar relatórios | `True` | `False` | `True` |
| Testar: carregar sem apagar banco existente | `True` | `True` | `False` |

> **Atenção**: `OVERWRITE_DB = True` apaga **todos os dados** do banco antes de recarregar. Use `False` apenas quando souber que os dados já estão corretos no banco.

---

#### Nomes das tabelas no banco de dados

Estes parâmetros definem os nomes das tabelas internas do banco SQLite. **Não altere** a menos que saiba o que está fazendo.

| Parâmetro | O que é | Padrão |
|---|---|---|
| `GUIDING_TABLE` | Tabela-guia que define quais abas da planilha carregar | `GUIDING` |
| `TYPES_OF_ENTRIES` | Tabela de tipos de lançamentos | `TiposLancamentos` |
| `GENERAL_ENTRIES_TABLE` | Tabela principal com todos os lançamentos | `LANCAMENTOS_GERAIS` |

---

#### Configurações de pivot table (tabela histórica)

| Parâmetro | O que faz | Valores | Padrão |
|---|---|---|---|
| `CREATE_PIVOT` | Gera a tabela de histórico (pivot) | `True` / `False` | `True` |
| `ANUAL_PIVOT_TABLE` | Nome da tabela de histórico anual no banco | nome | `HistoricoAnual` |
| `FULL_PIVOT_TABLE` | Nome da tabela de histórico completo no banco | nome | `HistoricoGeral` |

---

#### Configurações de relatórios dinâmicos

| Parâmetro | O que faz | Valores | Padrão |
|---|---|---|---|
| `RUN_DINAMIC_REPORT` | Gera relatórios dinâmicos baseados na planilha-guia | `True` / `False` | `True` |
| `DIN_REPORT_GUIDING` | Nome da aba na planilha que define os relatórios dinâmicos | nome da aba | `General_din_reports` |
| `RPT_SINGLE_FILE` | Coloca todos os relatórios em um único arquivo Excel | `True` / `False` | `True` |

---

#### Configurações de dados descartados

| Parâmetro | O que faz | Valores | Padrão |
|---|---|---|---|
| `SAVE_DISCARTED_DATA` | Salva registros que foram descartados durante o carregamento | `True` / `False` | `False` |
| `DISCARTED_DATA_TABLE` | Nome da tabela onde os dados descartados são salvos | nome | `discarted_data` |

---

#### Configurações de parcelamentos

| Parâmetro | O que faz | Padrão |
|---|---|---|
| `SPLT_PAYMNT_TAB` | Nome da aba da planilha com dados de parcelamentos | `PARCELAMENTOS` |
| `OUT_RES_PMNT_TAB` | Nome da tabela de resumo de parcelamentos | `Resumo_Parcelamentos` |

---

#### Configurações de resumos mensais

| Parâmetro | O que faz | Padrão |
|---|---|---|
| `MONTHLY_SUMMATIES` | Nome da tabela de resumo mensal | `Resumido_In_Out` |

---

#### Configurações de progresso diário

| Parâmetro | O que faz | Padrão |
|---|---|---|
| `DAYLY_PROGRESS` | Nome da tabela de contagem diária de lançamentos | `contagem_diaria` |

---

#### Configurações avançadas (normalmente não altere)

| Parâmetro | O que faz | Padrão | Observação |
|---|---|---|---|
| `PARALLELS` | Número de registros processados em paralelo | `89` | Não altere |
| `MULTITHREADING` | Habilita processamento multi-thread | `False` | **Mantenha False** — feature desabilitada |
| `API_VERSION` | Versão interna da API | `2.0.0` | Não altere |
| `YAML_SQL_FILE` | Nome do arquivo YAML com as consultas SQL | `PDW_QUERIES.yaml` | Altere só se renomear o arquivo YAML |

---

#### Configurações de dados transientes (avançado)

| Parâmetro | O que faz | Padrão |
|---|---|---|
| `EXPORT_TRANSIENT_DATA` | Exporta dados de uma coluna específica | `False` |
| `TRANSIENT_DATA_TABLE` | Nome da tabela de dados transientes | `Transient_data` |
| `TRANSIENT_DATA_COLUMN` | Nome da coluna para filtrar dados transientes | `Origem` |
| `EXPORT_OTHER_TYPES` | Exporta outros tipos de lançamentos | `False` |

---

## Exemplo completo do arquivo `.cfg`

### Para Linux (pasta única para tudo):

```ini
[DIRECTORIES]
DIR_IN = /home/joao/PDW/dados/
DIR_OUT = /home/joao/PDW/dados/
DATABASE_DIR = /home/joao/PDW/dados/
LOG_DIR = /home/joao/PDW/dados/

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
RUN_DATA_LOADER = True
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

### Para Windows:

A única diferença é a seção `[DIRECTORIES]`:

```ini
[DIRECTORIES]
DIR_IN = C:\Users\SeuNome\PDW\dados\
DIR_OUT = C:\Users\SeuNome\PDW\dados\
DATABASE_DIR = C:\Users\SeuNome\PDW\dados\
LOG_DIR = C:\Users\SeuNome\PDW\dados\
```

---

## Parte 2 — Configurando os scripts de execução

### RunPDW.sh (Linux)

Abra o arquivo `RunPDW.sh` em um editor de texto e ajuste as três variáveis no início:

```bash
# Ajuste estas três linhas:
dirPDW="/home/SEU_USUARIO/PDW/dados"     # sua pasta de dados
dirScript="${dirPDW}"                     # pasta do programa (pode ser a mesma)
envBin="/home/SEU_USUARIO/pdw/bin"       # pasta bin do ambiente virtual
```

Depois de editar, torne o script executável:

```bash
chmod +x ~/pdw-app/RunPDW.sh
```

### RunPDW.ps1 (Windows — PowerShell)

Abra o arquivo `RunPDW.ps1` e ajuste as variáveis no início:

```powershell
# Ajuste estas linhas:
$dirPDW = "C:\Users\SeuNome\PDW\dados"           # sua pasta de dados
$dirScript = "C:\Users\SeuNome\PDW\app"           # pasta do programa
$pythonExe = "C:\Users\SeuNome\AppData\Local\Programs\Python\Python312\python.exe"
```

Para saber o caminho correto do Python no Windows:

```powershell
where python
```

### Run_PDW.bat (Windows — Prompt de Comando)

Abra o `Run_PDW.bat` e ajuste:

```batch
cd "C:\Users\SeuNome\PDW\app"
C:\Users\SeuNome\AppData\Local\Programs\Python\Python311\python.exe PersonalDataWareHouse.py
```

---

## Parte 3 — Estrutura da planilha Excel de entrada

O arquivo Excel de entrada (`PDW.xlsx` por padrão) precisa ter uma estrutura específica de abas (sheets). O PDW lê a aba **GUIDING** para saber quais abas processar.

### Aba obrigatória: GUIDING

A aba `GUIDING` é a "tabela de controle". Ela define quais abas da planilha serão carregadas no banco de dados.

Colunas obrigatórias da aba GUIDING:

| Coluna | O que é | Exemplo |
|---|---|---|
| `TABLE_NAME` | Nome da aba da planilha a ser processada | `Conta_Corrente` |
| `ACCOUNTING` | Indica se é uma aba contábil (`X`) ou não (vazio) | `X` |
| `LOADABLE` | Indica se deve ser carregada nesta execução (`X`) | `X` |

**Exemplo de aba GUIDING:**

| TABLE_NAME | ACCOUNTING | LOADABLE |
|---|---|---|
| Conta_Corrente | X | X |
| Poupanca | X | X |
| Cartao_Credito | X | X |
| PARCELAMENTOS | | X |
| TiposLancamentos | | X |

### Abas de lançamentos (contábeis)

Cada aba marcada com `ACCOUNTING = X` no GUIDING deve ter as seguintes colunas mínimas:

| Coluna | Tipo | Descrição |
|---|---|---|
| `Data` | Data (`dd/mm/aaaa`) | Data do lançamento |
| `Descrição` | Texto | Descrição do lançamento |
| `Débito` | Número | Valor saindo (gasto) |
| `Crédito` | Número | Valor entrando (recebimento) |
| `Origem` | Texto | Identificador da fonte dos dados |

> **Dica**: O nome exato das colunas deve bater com o que está no código. Colunas com acentos e espaços devem ser digitadas exatamente como aparecem.

### Aba PARCELAMENTOS (opcional)

Se você usa controle de parcelas, crie uma aba chamada `PARCELAMENTOS` (ou o nome configurado em `SPLT_PAYMNT_TAB`) com as colunas:

| Coluna | Tipo | Descrição |
|---|---|---|
| `Data` | Data | Data do lançamento parcelado |
| `Tipo Lançamento` | Texto | Tipo/categoria do parcelamento |
| outros campos | variado | Conforme sua necessidade |

### Aba General_din_reports (relatórios dinâmicos)

Esta aba define os relatórios dinâmicos. Se `RUN_DINAMIC_REPORT = True`, o PDW lê esta aba para saber quais relatórios adicionais gerar.

---

## Parte 4 — Configurando o arquivo `PDW_QUERIES.yaml`

O arquivo `PDW_QUERIES.yaml` contém as consultas SQL que geram as abas do relatório Excel final.

### Estrutura básica

```yaml
# Queries executadas quando gera_hist = True (CREATE_PIVOT = True)
queries_gera_hist:
  - sql: "select * from {full_hist};"
    sheet_name: "{full_hist}"

# Queries sempre executadas
queries_padrao:
  - sql: "select tipo, sum(debito) from {entries_table} group by tipo;"
    sheet_name: "Resumo por Tipo"
```

### Variáveis disponíveis nas queries

Use `{nome_variavel}` dentro das queries SQL. O PDW substitui automaticamente:

| Variável | Substitui por | Valor no .cfg |
|---|---|---|
| `{entries_table}` | Tabela principal de lançamentos | `GENERAL_ENTRIES_TABLE` |
| `{full_hist}` | Tabela de histórico completo | `FULL_PIVOT_TABLE` |
| `{anual_hist}` | Tabela de histórico anual | `ANUAL_PIVOT_TABLE` |
| `{day_prog}` | Tabela de progresso diário | `DAYLY_PROGRESS` |
| `{splt_pmnt_res}` | Tabela de resumo de parcelamentos | `OUT_RES_PMNT_TAB` |
| `{mont_summ}` | Tabela de resumo mensal | `MONTHLY_SUMMATIES` |

### Como adicionar uma query personalizada

Para adicionar um novo relatório, adicione um item na seção `queries_padrao`:

```yaml
queries_padrao:
  # ... queries existentes ...
  
  # Minha query personalizada
  - sql: >
      select Data, Descrição, Débito, Crédito
      from {entries_table}
      where Data >= date('now', '-7 day')
      order by Data desc;
    sheet_name: "Ultimos 7 Dias"
```

O `sheet_name` define o nome da aba que aparecerá no Excel de relatório.

> **Sintaxe YAML**: Use `>` após `sql:` para queries em múltiplas linhas. Para queries curtas, use aspas: `sql: "SELECT * FROM tabela;"`. O `sheet_name` sempre vai entre aspas.

---

## Parte 5 — Configuração para múltiplos arquivos de configuração

O PDW aceita receber o caminho de um arquivo `.cfg` como parâmetro. Isso permite ter **configurações diferentes** para diferentes propósitos.

**Exemplos de uso**:

```bash
# Linux — usar configuração específica
python PersonalDataWareHouse.py /home/joao/PDW/config_casa.cfg
python PersonalDataWareHouse.py /home/joao/PDW/config_trabalho.cfg
```

```powershell
# Windows — usar configuração específica
python PersonalDataWareHouse.py C:\PDW\config_casa.cfg
python PersonalDataWareHouse.py C:\PDW\config_trabalho.cfg
```

Se nenhum parâmetro for fornecido, o PDW procura pelo arquivo `PersonalDataWareHouse.cfg` na **mesma pasta** onde está o script.

---

## Resumo rápido — Checklist de configuração

- [ ] `PersonalDataWareHouse.cfg` editado com os caminhos corretos de sua máquina
- [ ] `DIR_IN`, `DIR_OUT`, `DATABASE_DIR`, `LOG_DIR` apontam para pastas que existem
- [ ] `INPUT_FILE` bate com o nome real do seu arquivo Excel (sem a extensão `.xlsx`)
- [ ] `CURRENT_VERSION = 10.1.0` (não alterar)
- [ ] `RUN_DATA_LOADER` e `RUN_REPORTS` configurados conforme o que quer executar
- [ ] Script de execução (`RunPDW.sh` ou `RunPDW.ps1`) ajustado com os caminhos corretos
- [ ] Planilha Excel de entrada (`PDW.xlsx`) na pasta `DIR_IN` com a aba `GUIDING` preenchida
- [ ] Arquivo `PDW_QUERIES.yaml` na mesma pasta que o script Python

---

**Próximo passo**: Com a configuração concluída, siga para o **PASSO 3 — OPERAÇÃO** para aprender a executar o PDW e interpretar os resultados.
