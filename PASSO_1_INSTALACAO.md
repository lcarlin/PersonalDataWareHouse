# PASSO 1 — INSTALAÇÃO
## Personal Data Warehouse v10.1.0
### Guia completo de instalação para Windows e Linux

---

## O que é o PDW?

O **Personal Data Warehouse (PDW)** é um programa que lê uma planilha Excel (`.xlsx`), carrega os dados em um banco de dados local (SQLite), e gera relatórios automáticos em Excel, CSV, JSON e XML.

Ele roda completamente no seu computador — sem internet, sem servidor, sem nuvem.

---

## O que você vai precisar

Antes de instalar, verifique se você tem os seguintes itens:

| Item | Versão mínima | Para que serve |
|---|---|---|
| **Python** | 3.9 ou superior | Linguagem em que o PDW é escrito |
| **pip** | Qualquer versão recente | Instalador de bibliotecas Python |
| **Espaço em disco** | 500 MB livres | Para o programa, bibliotecas e dados |
| **Permissão de escrita** | Na pasta de trabalho | Para criar arquivos de saída |

---

## Parte 1 — Instalação no Linux (Ubuntu, Debian, Mint, etc.)

### 1.1 — Verificar se o Python está instalado

Abra um terminal (`Ctrl + Alt + T`) e digite:

```bash
python3 --version
```

Você deve ver algo como `Python 3.11.2`. Se aparecer `command not found`, instale o Python:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

### 1.2 — Criar uma pasta de trabalho para o PDW

Escolha onde você quer guardar os arquivos do PDW. Neste guia, vamos usar `~/Dropbox/PDW_DRPBX/` como a pasta de dados e `~/pdw-app/` como a pasta do programa.

```bash
# Cria a pasta do programa
mkdir -p ~/pdw-app

# Cria a pasta de dados (onde ficam o Excel, o banco e os relatórios)
mkdir -p ~/Dropbox/PDW_DRPBX
```

> **Nota**: Você pode usar qualquer pasta. O importante é lembrar o caminho para configurar depois.

### 1.3 — Copiar os arquivos do PDW para a pasta do programa

Copie todos os arquivos do PDW para a pasta `~/pdw-app/`. A estrutura deve ficar assim:

```
~/pdw-app/
├── PersonalDataWareHouse.py    ← arquivo principal
├── PersonalDataWareHouse.cfg   ← arquivo de configuração
├── PDW_QUERIES.yaml            ← consultas SQL dos relatórios
├── RunPDW.sh                   ← script para executar no Linux
├── pdw/                        ← pasta com os módulos do programa
│   ├── main.py
│   ├── config/
│   ├── core/
│   ├── etl/
│   ├── analytics/
│   ├── reports/
│   ├── database/
│   ├── utils/
│   └── infrastructure/
└── InstalaDependencias.sh      ← script de instalação de bibliotecas
```

### 1.4 — Criar o ambiente virtual Python (recomendado)

Um ambiente virtual isola as bibliotecas do PDW do resto do seu sistema. Isso evita conflitos.

```bash
# Cria o ambiente virtual na pasta ~/pdw (nome que o script RunPDW.sh espera)
python3 -m venv ~/pdw

# Ativa o ambiente virtual
source ~/pdw/bin/activate

# Você verá "(pdw)" no início do prompt — isso indica que o ambiente está ativo
```

### 1.5 — Instalar as bibliotecas necessárias

Com o ambiente virtual ativo, execute:

```bash
pip install pandas xlsxwriter xlrd openpyxl numpy pyyaml lxml
```

Aguarde o download e instalação. Pode levar alguns minutos dependendo da sua conexão.

Para verificar se tudo foi instalado corretamente:

```bash
pip list | grep -E "pandas|xlsxwriter|xlrd|openpyxl|numpy|PyYAML"
```

Você deve ver todas as bibliotecas listadas com suas versões.

### 1.6 — Desativar o ambiente virtual

Quando terminar a instalação:

```bash
deactivate
```

### 1.7 — Verificar a estrutura final de pastas

```bash
ls ~/pdw-app/
ls ~/pdw/bin/python
```

Se o segundo comando mostrar o caminho para o Python, a instalação está correta.

---

## Parte 2 — Instalação no Windows

### 2.1 — Verificar se o Python está instalado

Abra o **Prompt de Comando** (`Win + R` → digite `cmd` → Enter) e digite:

```cmd
python --version
```

Ou o **PowerShell** (`Win + X` → Windows PowerShell) e digite:

```powershell
python --version
```

Você deve ver `Python 3.11.x` ou similar. Se aparecer erro, instale o Python.

### 2.2 — Instalar o Python no Windows (se necessário)

1. Acesse **python.org/downloads** no navegador
2. Clique no botão amarelo **"Download Python 3.x.x"**
3. Execute o instalador baixado
4. **IMPORTANTE**: Na primeira tela do instalador, marque a caixa **"Add Python to PATH"** antes de clicar em Install Now
5. Clique em **"Install Now"**
6. Após a instalação, feche e reabra o Prompt de Comando
7. Digite `python --version` para confirmar

### 2.3 — Criar as pastas de trabalho

No Prompt de Comando ou PowerShell:

```powershell
# Cria a pasta do programa (ajuste o caminho conforme sua preferência)
mkdir "C:\PDW\app"

# Cria a pasta de dados
mkdir "C:\PDW\dados"
```

> **Sugestão de estrutura no Windows**:
> - Pasta do programa: `C:\Users\SeuNome\PDW\app\`
> - Pasta de dados: `C:\Users\SeuNome\PDW\dados\`

### 2.4 — Copiar os arquivos do PDW

Copie todos os arquivos do PDW para a pasta do programa (`C:\PDW\app\`). A estrutura deve ser idêntica à descrita na seção 1.3.

### 2.5 — Criar o ambiente virtual Python no Windows

No PowerShell, navegue até a pasta do programa:

```powershell
cd C:\PDW\app

# Cria o ambiente virtual
python -m venv venv

# Ativa o ambiente virtual no PowerShell
.\venv\Scripts\Activate.ps1
```

> **Problema comum**: Se aparecer erro de "política de execução", execute este comando e tente de novo:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 2.6 — Instalar as bibliotecas no Windows

Com o ambiente virtual ativo (você verá `(venv)` no início do prompt):

```powershell
pip install pandas xlsxwriter xlrd openpyxl numpy pyyaml lxml
```

Aguarde a instalação completa.

Para verificar:

```powershell
pip list
```

### 2.7 — Verificar o caminho do Python instalado

O script `RunPDW.ps1` precisa saber onde está o Python. Para descobrir:

```powershell
where python
```

Anote o caminho exibido (exemplo: `C:\Users\SeuNome\AppData\Local\Programs\Python\Python312\python.exe`). Você vai precisar dele na configuração dos scripts de execução.

### 2.8 — Desativar o ambiente virtual

```powershell
deactivate
```

---

## Parte 3 — Verificação da instalação

Independente do sistema operacional, execute este teste para confirmar que tudo está funcionando:

### No Linux:

```bash
source ~/pdw/bin/activate
cd ~/pdw-app
python PersonalDataWareHouse.py --version 2>/dev/null || python PersonalDataWareHouse.py
deactivate
```

### No Windows (PowerShell):

```powershell
cd C:\PDW\app
.\venv\Scripts\Activate.ps1
python PersonalDataWareHouse.py
deactivate
```

Se o programa iniciar e exibir mensagens sobre arquivos de configuração, a instalação foi bem-sucedida.

---

## Parte 4 — Estrutura de pastas explicada

Entender a estrutura de pastas é importante para a configuração:

```
PASTA DO PROGRAMA (onde fica o código)
├── PersonalDataWareHouse.py     → Arquivo principal do programa
├── PersonalDataWareHouse.cfg    → VOCÊ EDITA ESTE ARQUIVO para configurar
├── PDW_QUERIES.yaml             → Consultas SQL dos relatórios (editável)
├── RunPDW.sh / RunPDW.ps1       → Scripts para execução automática
└── pdw/                         → Módulos internos (não editar)

PASTA DE DADOS (onde ficam seus arquivos)
├── PDW.xlsx                     → SUA PLANILHA (entrada de dados)
├── PDW.db                       → Banco de dados gerado (não editar manualmente)
├── PDW_REPORTS.v2.xlsx          → Relatório Excel gerado pelo PDW
├── PDW.lnx.log / PDW.win.log    → Arquivo de log (histórico de execuções)
└── Lancamentos_Gerais_TMP.csv   → Arquivo temporário (gerado automaticamente)
```

> **Importante**: A pasta de dados pode ser a mesma que a do programa, ou podem ser pastas separadas. O arquivo `.cfg` define onde cada tipo de arquivo fica.

---

## Parte 5 — Solução de problemas comuns na instalação

### Erro: "python: command not found" (Linux)

```bash
# Tente com python3 em vez de python
python3 --version

# Ou crie um alias
alias python=python3
```

### Erro: "No module named pip" (Linux)

```bash
sudo apt install python3-pip -y
```

### Erro: "Cannot install pandas — requires build tools" (Linux)

```bash
sudo apt install build-essential python3-dev -y
pip install pandas
```

### Erro ao ativar ambiente virtual no Windows: "cannot be loaded"

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Erro: "pip is not recognized" (Windows)

Reinstale o Python marcando a opção **"Add Python to PATH"** durante a instalação.

### Como saber se o pandas foi instalado corretamente:

```bash
python -c "import pandas; print('pandas OK:', pandas.__version__)"
python -c "import openpyxl; print('openpyxl OK:', openpyxl.__version__)"
python -c "import xlsxwriter; print('xlsxwriter OK:', xlsxwriter.__version__)"
python -c "import yaml; print('pyyaml OK')"
```

Cada linha deve imprimir uma mensagem de OK sem erros.

---

## Resumo rápido — Checklist de instalação

**Linux:**
- [ ] Python 3.9+ instalado (`python3 --version`)
- [ ] Ambiente virtual criado em `~/pdw/`
- [ ] Ambiente virtual ativado (`source ~/pdw/bin/activate`)
- [ ] Bibliotecas instaladas (`pip install pandas xlsxwriter xlrd openpyxl numpy pyyaml lxml`)
- [ ] Arquivos do PDW na pasta do programa
- [ ] Pasta de dados criada

**Windows:**
- [ ] Python 3.9+ instalado com "Add to PATH" marcado
- [ ] Ambiente virtual criado na pasta do programa
- [ ] Bibliotecas instaladas
- [ ] Caminho do Python anotado para configuração dos scripts
- [ ] Pasta de dados criada

---

**Próximo passo**: Com a instalação concluída, siga para o **PASSO 2 — CONFIGURAÇÃO** para ajustar o programa ao seu ambiente e à sua planilha de dados.
