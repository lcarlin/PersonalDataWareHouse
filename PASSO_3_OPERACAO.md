# PASSO 3 — OPERAÇÃO E UTILIZAÇÃO
## Personal Data Warehouse v10.1.0
### Guia completo de uso do dia a dia

---

## Como o PDW funciona — visão geral

O PDW é um programa de linha de comando. Ele não tem janela gráfica — executa no terminal (Linux) ou no PowerShell/Prompt de Comando (Windows).

O fluxo de trabalho é sempre o mesmo:

```
Você atualiza           O PDW lê a           O PDW gera
sua planilha   →→→→→→   planilha e   →→→→→→  os relatórios
Excel (PDW.xlsx)        processa os          (PDW_REPORTS.v2.xlsx,
                        dados                CSV, JSON, XML)
```

**Tempo típico de execução**: 10 a 120 segundos, dependendo da quantidade de dados e da velocidade do computador.

---

## Parte 1 — Formas de executar o PDW

Existem quatro formas de executar o PDW. Escolha a que mais se adapta ao seu uso:

| Método | Sistema | Quando usar |
|---|---|---|
| `RunPDW.sh` | Linux | Uso diário — verifica automaticamente se a planilha foi alterada |
| `RunPDW.ps1` | Windows | Uso diário — verifica automaticamente se a planilha foi alterada |
| `Run_PDW.bat` | Windows | Uso simples — executa sempre, sem verificações |
| `python PersonalDataWareHouse.py` | Ambos | Desenvolvimento e testes |

---

### Método 1 — RunPDW.sh (Linux, recomendado)

Este script é inteligente: ele só executa o PDW se a planilha Excel foi modificada depois da última execução. Isso evita processar dados iguais desnecessariamente.

**Como executar:**

```bash
cd ~/pdw-app
bash RunPDW.sh
```

Ou, se você tornou o script executável:

```bash
~/pdw-app/RunPDW.sh
```

**O que o script faz, passo a passo:**

1. Verifica se já existe uma execução em andamento (arquivo `.lock`)
2. Exibe informações sobre o banco de dados e a planilha (datas de modificação)
3. Compara a data da planilha com a data do banco de dados
4. **Se a planilha for mais nova que o banco**: ativa o ambiente virtual e executa o PDW
5. **Se o banco for mais novo que a planilha**: exibe mensagem "não há necessidade de executar" e encerra
6. Ao final, remove o arquivo `.lock` e aguarda tecla

**Exemplo de saída no terminal:**

```
>===================================================================================================================<
Banco-de-dados    :-> /home/joao/PDW/dados/PDW.db
Ultima Atulizacao :-> 2026-05-17 10:30:00
>===================================================================================================================<
Planilha          :-> /home/joao/PDW/dados/PDW.xlsx
Ultima Atulizacao :-> 2026-05-17 11:45:00
>===================================================================================================================<
Ultimo host       :-> joao-notebook
host Atual        :-> joao-notebook
>===================================================================================================================<
[O PDW começa a processar...]
Pressione qualquer tecla para sair...
```

---

### Método 2 — RunPDW.ps1 (Windows, recomendado)

Funciona de forma similar ao RunPDW.sh, mas para Windows via PowerShell.

**Como executar:**

1. Abra o **PowerShell** (`Win + X` → Windows PowerShell)
2. Navegue até a pasta do programa:
   ```powershell
   cd C:\PDW\app
   ```
3. Execute o script:
   ```powershell
   .\RunPDW.ps1
   ```

Se aparecer erro de política de execução, execute antes:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Alternativa — executar com duplo clique:**

1. No Windows Explorer, navegue até a pasta do programa
2. Clique com o botão direito em `RunPDW.ps1`
3. Selecione **"Executar com PowerShell"**

**O que o script faz:**

1. Verifica arquivo `.lock` (evita execução dupla)
2. Verifica se os arquivos `PDW.xlsx` e `PDW.db` existem
3. Compara datas de modificação
4. Se a planilha for mais nova: executa o PDW e copia o Excel atualizado para o Dropbox
5. Se o banco for mais novo: exibe mensagem e encerra
6. Remove o arquivo `.lock` ao final

---

### Método 3 — Run_PDW.bat (Windows, mais simples)

O arquivo `.bat` executa o PDW diretamente, sem verificações de data.

**Como executar:**

1. No Windows Explorer, dê **duplo clique** em `Run_PDW.bat`

Ou no Prompt de Comando:

```cmd
cd C:\PDW\app
Run_PDW.bat
```

---

### Método 4 — Linha de comando direta (todos os sistemas)

Este método é útil para testes, depuração ou quando você quer controle total.

**Linux:**

```bash
# Ativar o ambiente virtual
source ~/pdw/bin/activate

# Executar com o arquivo de configuração padrão
cd ~/pdw-app
python PersonalDataWareHouse.py

# Ou com um arquivo de configuração específico
python PersonalDataWareHouse.py /caminho/para/outra_config.cfg

# Desativar o ambiente virtual ao terminar
deactivate
```

**Windows (PowerShell):**

```powershell
# Ativar o ambiente virtual
cd C:\PDW\app
.\venv\Scripts\Activate.ps1

# Executar
python PersonalDataWareHouse.py

# Ou com configuração específica
python PersonalDataWareHouse.py C:\PDW\config_alternativo.cfg

# Desativar ao terminar
deactivate
```

---

## Parte 2 — Entendendo a saída do programa

### Mensagens durante a execução

Durante o processamento, o PDW exibe mensagens no terminal. Aqui está o que cada mensagem significa:

| Mensagem | O que está acontecendo |
|---|---|
| `Loading configuration...` | Lendo o arquivo `.cfg` |
| `Version check OK` | Versão no `.cfg` bate com a versão do código |
| `Starting data loader...` | Iniciando a carga de dados da planilha |
| `Reading sheet: NomeDaAba` | Lendo uma aba específica da planilha |
| `Dropping table: NOME_TABELA` | Apagando tabela antiga no banco (OVERWRITE_DB = True) |
| `Loading data to LANCAMENTOS_GERAIS...` | Salvando dados na tabela principal |
| `Creating pivot history...` | Gerando a tabela de histórico |
| `Creating dynamic reports...` | Gerando relatórios dinâmicos |
| `Generating Excel report...` | Criando o arquivo `.xlsx` de saída |
| `Done.` | Processo concluído com sucesso |

### Mensagens de aviso (não são erros)

| Mensagem | O que significa | O que fazer |
|---|---|---|
| `A planilha não foi alterada...` | A planilha não mudou desde a última execução | Nada — é comportamento esperado |
| `Sheet NomeDaAba not found` | Uma aba esperada não existe na planilha | Verificar o nome da aba no GUIDING |
| `No data to process in sheet X` | A aba existe mas está vazia | Normal se a aba estiver sem dados |

### Mensagens de erro comuns

| Mensagem | Causa provável | Solução |
|---|---|---|
| `Version mismatch` | Versão no `.cfg` diferente do código | Verificar `CURRENT_VERSION` no `.cfg` |
| `Config file not found` | Arquivo `.cfg` não encontrado | Verificar se o `.cfg` está na pasta correta |
| `Input file not found: PDW.xlsx` | Planilha não encontrada em `DIR_IN` | Verificar caminho em `DIR_IN` e nome em `INPUT_FILE` |
| `No module named pandas` | Biblioteca não instalada | Ativar ambiente virtual e `pip install pandas` |
| `Permission denied` | Sem permissão para escrever na pasta | Verificar permissões da pasta `DIR_OUT` |
| `database is locked` | Outra execução em andamento | Aguardar terminar ou remover o arquivo `.lock` |

---

## Parte 3 — Arquivos gerados pelo PDW

Após a execução, você encontrará estes arquivos na pasta `DIR_OUT` / `DATABASE_DIR`:

| Arquivo | Localização | O que contém |
|---|---|---|
| `PDW.db` | `DATABASE_DIR` | Banco de dados SQLite com todos os lançamentos |
| `PDW_REPORTS.v2.xlsx` | `DIR_OUT` | Relatório principal com todas as abas analíticas |
| `Lancamentos_Gerais_TMP.csv` | `DIR_OUT` | Exportação CSV de todos os lançamentos |
| `Lancamentos_Gerais_TMP.json.gz` | `DIR_OUT` | Exportação JSON comprimida |
| `Lancamentos_Gerais_TMP.xml.gz` | `DIR_OUT` | Exportação XML comprimida |
| `PDW.lnx.log` | `LOG_DIR` | Histórico de execuções com timestamps |

### Abas do relatório Excel (PDW_REPORTS.v2.xlsx)

O arquivo de relatório contém várias abas, cada uma com um tipo de análise:

| Aba | O que mostra |
|---|---|
| `HistoricoGeral` | Pivot table com todo o histórico de lançamentos |
| `HistoricoAnual` | Pivot table com histórico por ano |
| `HistoricoGeral12Meses` | Histórico dos últimos 12 meses |
| `Ultimos30Dias` | Resumo por categoria dos últimos 30 dias |
| `Iterações_Mensais` | Contagem de lançamentos por mês |
| `Iterações_Semanais_12M` | Contagem por dia da semana (12 meses) |
| `Debitos Mensais` | Débitos e créditos por mês |
| `Histórico de Uso` | Lançamentos agrupados por origem |
| `Contagem dia-a-dia` | Progressão diária de lançamentos |
| `Resumo de Parcelamentos` | Resumo dos parcelamentos cadastrados |
| `Resumos_In_out Mensal` | Entradas e saídas por mês |
| `Resumo Mensal Lancto` | Resumo mensal por tipo de lançamento |
| `Resumo Anual Lancto` | Resumo anual por tipo de lançamento |
| Abas dinâmicas | Relatórios definidos em `General_din_reports` |

---

## Parte 4 — Entendendo o arquivo de log

O arquivo `PDW.lnx.log` (Linux) ou `PDW.win.log` (Windows) registra cada execução do PDW.

### Formato do log

Cada linha do log representa uma execução:

```
2026/05/17 10:30:00 Started | 2026/05/17 10:31:45 Ended | 105.3 TotalSecs | Version 10.1.0 | Hostname meu-notebook | OS Linux
```

| Campo | O que é |
|---|---|
| `2026/05/17 10:30:00 Started` | Data e hora de início |
| `2026/05/17 10:31:45 Ended` | Data e hora de término |
| `105.3 TotalSecs` | Tempo total de execução em segundos |
| `Version 10.1.0` | Versão do PDW |
| `Hostname meu-notebook` | Nome do computador que executou |
| `OS Linux` | Sistema operacional |

### Para visualizar o log

**Linux:**

```bash
# Ver as últimas 10 execuções
tail -10 ~/PDW/dados/PDW.lnx.log

# Ver todas as execuções
cat ~/PDW/dados/PDW.lnx.log

# Monitorar em tempo real durante execução
tail -f ~/PDW/dados/PDW.lnx.log
```

**Windows (PowerShell):**

```powershell
# Ver as últimas 10 execuções
Get-Content C:\PDW\dados\PDW.win.log -Tail 10

# Monitorar em tempo real
Get-Content C:\PDW\dados\PDW.win.log -Wait
```

---

## Parte 5 — Cenários de uso comuns

### Cenário 1: Uso semanal — atualizar dados e gerar relatórios

**Situação**: Você atualiza a planilha Excel toda semana com novos lançamentos e quer gerar os relatórios atualizados.

**Configuração no `.cfg`:**

```ini
RUN_DATA_LOADER = True
RUN_REPORTS = True
OVERWRITE_DB = True
```

**Passos:**
1. Atualize a planilha `PDW.xlsx` com os novos lançamentos
2. Salve a planilha
3. Execute o PDW (via RunPDW.sh ou RunPDW.ps1)
4. Aguarde a execução terminar
5. Abra `PDW_REPORTS.v2.xlsx` para ver os relatórios atualizados

---

### Cenário 2: Apenas gerar novos relatórios (dados já carregados)

**Situação**: Os dados já estão no banco mas você modificou o `PDW_QUERIES.yaml` e quer regenerar apenas os relatórios, sem reprocessar a planilha.

**Configuração no `.cfg`:**

```ini
RUN_DATA_LOADER = False
RUN_REPORTS = True
OVERWRITE_DB = False
```

**Passos:**
1. Modifique o `PDW_QUERIES.yaml` conforme necessário
2. Execute o PDW normalmente
3. O programa vai pular o carregamento de dados e gerar apenas os relatórios

> **Atenção**: Com `RUN_DATA_LOADER = False`, o programa usa os dados que já estão no banco. Se o banco não existir, o programa falhará.

---

### Cenário 3: Primeiro uso — carga inicial de dados históricos

**Situação**: É a primeira vez que você está rodando o PDW com uma planilha cheia de dados históricos.

**Configuração no `.cfg`:**

```ini
RUN_DATA_LOADER = True
RUN_REPORTS = True
OVERWRITE_DB = True
```

**Passos:**
1. Certifique-se de que a planilha `PDW.xlsx` está completa com todos os dados históricos
2. Execute o PDW — pode demorar mais que o normal dependendo do volume de dados
3. Verifique o arquivo de log para confirmar que não houve erros
4. Abra o relatório gerado

---

### Cenário 4: Testar sem apagar dados existentes

**Situação**: Você quer testar uma mudança na planilha sem perder os dados que já estão no banco.

**Configuração no `.cfg`:**

```ini
RUN_DATA_LOADER = True
RUN_REPORTS = True
OVERWRITE_DB = False
```

> **Atenção**: Com `OVERWRITE_DB = False`, os novos dados serão **adicionados** aos existentes, não substituídos. Isso pode gerar duplicatas se os mesmos lançamentos já estiverem no banco.

---

### Cenário 5: Usar arquivo de configuração diferente para cada contexto

**Situação**: Você tem dados pessoais e dados do trabalho em planilhas separadas.

```bash
# Linux — processar dados pessoais
python PersonalDataWareHouse.py /home/joao/PDW/config_pessoal.cfg

# Linux — processar dados do trabalho
python PersonalDataWareHouse.py /home/joao/PDW/config_trabalho.cfg
```

Cada arquivo `.cfg` aponta para uma pasta de dados diferente, com planilhas e bancos separados.

---

## Parte 6 — Consultando o banco de dados diretamente

O banco de dados `PDW.db` é um arquivo SQLite padrão. Você pode abri-lo com qualquer ferramenta SQLite para consultar os dados diretamente.

### Ferramentas recomendadas

| Ferramenta | Sistema | Tipo | Download |
|---|---|---|---|
| **DB Browser for SQLite** | Windows / Linux / Mac | Gráfica (recomendada) | sqlitebrowser.org |
| **DBeaver** | Windows / Linux / Mac | Gráfica (avançada) | dbeaver.io |
| `sqlite3` | Linux | Linha de comando | `sudo apt install sqlite3` |

### Consultando via linha de comando (Linux)

```bash
# Abrir o banco
sqlite3 ~/PDW/dados/PDW.db

# Listar as tabelas disponíveis
.tables

# Ver a estrutura da tabela principal
.schema LANCAMENTOS_GERAIS

# Consultar os últimos 10 lançamentos
SELECT * FROM LANCAMENTOS_GERAIS ORDER BY Data DESC LIMIT 10;

# Sair do sqlite3
.quit
```

### Consultas SQL úteis para análise rápida

```sql
-- Quantos lançamentos existem no total
SELECT COUNT(*) as Total FROM LANCAMENTOS_GERAIS;

-- Lançamentos do mês atual
SELECT * FROM LANCAMENTOS_GERAIS 
WHERE strftime('%Y-%m', Data) = strftime('%Y-%m', 'now')
ORDER BY Data DESC;

-- Soma de débitos por categoria nos últimos 30 dias
SELECT tipo, SUM(Debito) as Total
FROM LANCAMENTOS_GERAIS
WHERE Data >= date('now', '-30 days') AND Debito > 0
GROUP BY tipo
ORDER BY Total DESC;

-- Resumo mensal
SELECT AnoMes, SUM(Debito) as Debitos, SUM(Credito) as Creditos
FROM LANCAMENTOS_GERAIS
GROUP BY AnoMes
ORDER BY AnoMes DESC;
```

---

## Parte 7 — Manutenção e cuidados

### O banco de dados cresceu muito?

O banco SQLite (`PDW.db`) pode ficar fragmentado ao longo do tempo. Para compactá-lo:

```bash
# Linux
sqlite3 ~/PDW/dados/PDW.db "VACUUM;"

# Windows (PowerShell)
& "C:\caminho\sqlite3.exe" "C:\PDW\dados\PDW.db" "VACUUM;"
```

### O log está muito grande?

O arquivo de log cresce a cada execução. Para arquivá-lo:

**Linux:**

```bash
# Renomeia o log atual com a data, começando um novo
mv ~/PDW/dados/PDW.lnx.log ~/PDW/dados/PDW.lnx.log.$(date +%Y%m%d).bak
```

**Windows (PowerShell):**

```powershell
$data = Get-Date -Format "yyyyMMdd"
Rename-Item "C:\PDW\dados\PDW.win.log" "C:\PDW\dados\PDW.win.log.$data.bak"
```

### Backup dos dados

É recomendado fazer backup periódico do banco de dados:

**Linux:**

```bash
# Cópia com timestamp
cp ~/PDW/dados/PDW.db ~/PDW/backup/PDW.$(date +%Y%m%d).db

# Ou usando o comando nativo do SQLite (mais seguro — captura estado consistente)
sqlite3 ~/PDW/dados/PDW.db ".backup ~/PDW/backup/PDW.$(date +%Y%m%d).db"
```

---

## Parte 8 — Solução de problemas

### O programa não inicia

**Verificar:**

```bash
# Confirmar que o Python está no PATH
python --version

# Confirmar que as bibliotecas estão instaladas
python -c "import pandas, openpyxl, xlsxwriter, yaml; print('OK')"

# Confirmar que o arquivo .cfg existe
ls PersonalDataWareHouse.cfg

# Confirmar que a planilha existe
ls ~/PDW/dados/PDW.xlsx
```

---

### Erro: "Version mismatch"

O número em `CURRENT_VERSION` no arquivo `.cfg` não bate com a versão do código.

**Solução**: Abra o `.cfg` e verifique que está:

```ini
CURRENT_VERSION = 10.1.0
```

Se estiver diferente, corrija para `10.1.0`.

---

### Erro: "Input file not found"

O arquivo Excel de entrada não foi encontrado.

**Diagnóstico:**

```bash
# Verificar o que está em DIR_IN
ls /caminho/que/você/colocou/em/DIR_IN/

# A planilha deve estar lá com o nome certo
ls /caminho/em/DIR_IN/PDW.xlsx
```

**Soluções comuns:**
- O caminho em `DIR_IN` está errado — corrija no `.cfg`
- O arquivo se chama `pdw.xlsx` (minúsculas) mas `INPUT_FILE = PDW` (maiúsculas) — no Linux, nomes de arquivo diferenciam maiúsculas de minúsculas
- O caminho não termina com `/` — adicione a barra no final

---

### Erro: "database is locked"

Outra instância do PDW está rodando, ou uma execução anterior travou sem remover o arquivo `.lock`.

**Solução:**

```bash
# Linux — listar e remover arquivo .lock
ls ~/PDW/dados/*.lock
rm ~/PDW/dados/RunPDW.lock

# Verificar se ainda há processo Python rodando
ps aux | grep PersonalDataWareHouse
```

```powershell
# Windows
Get-ChildItem "C:\PDW\dados\" -Filter "*.lock"
Remove-Item "C:\PDW\dados\RunPDW.lock"
```

---

### Erro: "No module named 'pandas'" (ou outra biblioteca)

O ambiente virtual não está ativado, ou a biblioteca não foi instalada.

**Linux:**

```bash
# Ativar o ambiente virtual
source ~/pdw/bin/activate

# Verificar se pandas está instalado
pip list | grep pandas

# Instalar se necessário
pip install pandas
```

**Windows:**

```powershell
cd C:\PDW\app
.\venv\Scripts\Activate.ps1
pip list
pip install pandas
```

---

### O relatório Excel está vazio ou com abas faltando

Causas possíveis:

1. **`RUN_REPORTS = False`** no `.cfg` — verifique e mude para `True`
2. **Tabelas não foram criadas** — rode com `RUN_DATA_LOADER = True` primeiro
3. **Erro no `PDW_QUERIES.yaml`** — verifique a sintaxe do arquivo YAML
4. **Tabela referenciada não existe** — verifique se a variável `{nome_tabela}` no YAML corresponde ao nome configurado no `.cfg`

---

### A planilha não está sendo lida (campos vazios nos relatórios)

1. Verifique se a aba `GUIDING` existe na planilha
2. Verifique se as abas listadas no GUIDING existem na planilha com os nomes exatos
3. Verifique se a coluna `LOADABLE` está marcada com `X` para as abas que devem ser carregadas
4. Verifique se as colunas obrigatórias (`Data`, `Descrição`, etc.) existem nas abas contábeis

---

### O script RunPDW.sh diz "não há necessidade de executar"

Isso acontece quando a data de modificação do banco (`.db`) é mais recente que a da planilha (`.xlsx`).

**Solução**: Se você quer forçar a execução mesmo assim, use o método direto:

```bash
source ~/pdw/bin/activate
cd ~/pdw-app
python PersonalDataWareHouse.py
deactivate
```

Ou "toque" a planilha para atualizar sua data de modificação:

```bash
touch ~/PDW/dados/PDW.xlsx
```

---

## Parte 9 — Automação do PDW

### Agendar execução automática no Linux (cron)

Para executar o PDW automaticamente todo dia às 8h:

```bash
# Abrir o crontab
crontab -e

# Adicionar a linha (ajuste os caminhos):
0 8 * * * /home/joao/pdw-app/RunPDW.sh >> /home/joao/PDW/dados/cron.log 2>&1
```

### Agendar execução automática no Windows (Agendador de Tarefas)

1. Abra o **Agendador de Tarefas** (pesquise "Task Scheduler" no menu Iniciar)
2. Clique em **"Criar Tarefa Básica"**
3. Dê um nome: `Personal Data Warehouse`
4. Frequência: Diariamente, Semanalmente (conforme sua preferência)
5. Horário: escolha um horário de sua preferência
6. Ação: **Iniciar um programa**
7. Programa: `powershell.exe`
8. Argumentos: `-ExecutionPolicy Bypass -File "C:\PDW\app\RunPDW.ps1"`
9. Clique em **Concluir**

---

## Resumo dos comandos mais usados

### Linux

```bash
# Executar com script automático (recomendado)
bash ~/pdw-app/RunPDW.sh

# Executar manualmente
source ~/pdw/bin/activate && cd ~/pdw-app && python PersonalDataWareHouse.py && deactivate

# Ver log
tail -20 ~/PDW/dados/PDW.lnx.log

# Consultar banco diretamente
sqlite3 ~/PDW/dados/PDW.db "SELECT COUNT(*) FROM LANCAMENTOS_GERAIS;"

# Remover lock travado
rm -f ~/PDW/dados/*.lock
```

### Windows (PowerShell)

```powershell
# Executar com script automático (recomendado)
Set-Location C:\PDW\app; .\RunPDW.ps1

# Executar manualmente
cd C:\PDW\app; .\venv\Scripts\Activate.ps1; python PersonalDataWareHouse.py; deactivate

# Ver log
Get-Content C:\PDW\dados\PDW.win.log -Tail 20

# Remover lock travado
Remove-Item "C:\PDW\dados\*.lock" -Force
```

---

## Dicas finais

1. **Faça backup da planilha** antes de rodar o PDW com `OVERWRITE_DB = True` — uma vez que o banco é apagado e recarregado, não há desfazer.

2. **Não edite o arquivo `.db` manualmente** — use apenas o PDW ou ferramentas SQLite em modo somente leitura para consultas.

3. **O arquivo `PDW_QUERIES.yaml` é seguro de editar** — se algo der errado, o pior que acontece é um erro na geração dos relatórios. Os dados no banco não são afetados.

4. **Mantenha o `CURRENT_VERSION` sincronizado** — se você atualizar o código do PDW para uma nova versão, atualize também o `.cfg`.

5. **Se em dúvida, rode com `OVERWRITE_DB = True`** — recarregar os dados do zero da planilha é a forma mais segura de garantir que o banco está correto.
