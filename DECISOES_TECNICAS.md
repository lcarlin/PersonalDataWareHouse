# DECISOES_TECNICAS.md
## Personal Data Warehouse — Decisões Técnicas da Refatoração
### Versão atual: 9.11.2 → Versão alvo: 10.1.0

---

## DT-01 · Estratégia geral: extração incremental, sem reescrita

**Decisão**: Modularizar por extração direta de funções — sem reescrita de algoritmos,
sem mudança de paradigma, sem novos frameworks.

**Justificativa**: O código funciona corretamente. O objetivo é organização estrutural
para facilitar manutenção futura. Qualquer reescrita introduz risco de regressão.

**Implicação**: Cada função vai para seu módulo exatamente como está hoje — com seus
comentários, docstrings, código comentado e histórico de versão preservados.

---

## DT-02 · Nomenclatura pública preservada

**Decisão**: Nenhuma função pública será renomeada.

**Justificativa**: `RunPDW.sh`, `RunPDW.ps1` e `Run_PDW.bat` invocam o script Python.
Se houvesse chamadas externas às funções (ex: via import), renomear quebraria a interface.
Mesmo que não haja consumidores externos hoje, renomear introduz risco desnecessário.

**Implicação**: `new_data_loader`, `xlsx_report_generator`, `data_correjeitor` etc.
mantêm exatamente os mesmos nomes em seus novos módulos.

---

## DT-03 · Shim de compatibilidade para RunPDW.sh

**Decisão**: O arquivo `PersonalDataWareHouse.py` permanece na raiz como shim
que delega para `pdw.main`.

**Justificativa**: `RunPDW.sh` referencia `pythonScript="PersonalDataWareHouse.py"` 
diretamente (L31 do RunPDW.sh). Alterar o shell script está fora do escopo da
refatoração Python e cria risco de deploy em outros hosts.

**Shim proposto** (não modifica lógica — apenas delega):
```python
# PersonalDataWareHouse.py — compatibility shim v10.1.0
# Mantido para compatibilidade com RunPDW.sh / RunPDW.ps1
from pdw.main import main
import sys

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) == 2 else "")
```

---

## DT-04 · Ordem segura de extração de módulos

**Decisão**: Extrair módulos na ordem de baixo para cima no grafo de dependências
(folhas primeiro, raiz por último). Nunca extrair um módulo que dependa de outro
ainda não extraído.

**Ordem recomendada**:

| Passo | Módulo | Funções | Dependências de PDW |
|---|---|---|---|
| 1 | `utils/localization.py` | `get_month_names`, `get_weekday_names` | Nenhuma |
| 2 | `utils/compression.py` | `gzip_compressor` | Nenhuma |
| 3 | `utils/xml_utils.py` | `dataframe_to_xml` | Nenhuma |
| 4 | `database/operations.py` | `table_droppator`, `save_dataframe_to_database`, `sort_dataframe_by_date` | Nenhuma |
| 5 | `etl/sanitizer.py` | `clean_description_text`, `add_temporal_columns`, `enrich_dataframe_with_dates`, `sanitize_financial_columns`, `sanitize_entries_dataframe`, `data_correjeitor` | `utils/localization`, `database/operations` |
| 6 | `etl/loader.py` | `read_guiding_sheet`, `process_accounting_sheet`, `process_non_accounting_sheet`, `new_data_loader` | `etl/sanitizer`, `database/operations` |
| 7 | `analytics/totals.py` | `totalizador_diario`, `monthly_summaries`, `split_paymnt_resume` | Nenhuma de PDW |
| 8 | `analytics/pivot.py` | `create_pivot_history`, `create_dinamic_reports` | Nenhuma de PDW |
| 9 | `reports/exporter.py` | `general_entries_file_exportator` | `utils/compression`, `utils/xml_utils` |
| 10 | `reports/xlsx_generator.py` | `xlsx_report_generator` | `analytics/totals` |
| 11 | `infrastructure/logging.py` | *(extrair bloco de log de `main`)* | Nenhuma |
| 12 | `config/loader.py` | *(extrair bloco de config de `main`)* | Nenhuma |
| 13 | `core/orchestrator.py` | *(extrair corpo de `main` sem config/log)* | Todos os módulos acima |
| 14 | `pdw/main.py` | *(ponto de entrada `__main__`)* | `core/orchestrator` |
| 15 | `PersonalDataWareHouse.py` | *(shim de compatibilidade)* | `pdw.main` |

**Regra de validação por passo**: Após cada extração, executar o pipeline completo
com `RUN_DATA_LOADER = False` e `RUN_REPORTS = True` e verificar que a saída é idêntica.

---

## DT-05 · Tratamento do `data_correjeitor` — posicionamento no módulo `etl/sanitizer.py`

**Decisão**: `data_correjeitor` vai para `etl/sanitizer.py`, não para `database/operations.py`.

**Justificativa**: A função executa lógica de domínio (regras de limpeza de dados,
criação de views com semântica de negócio) mesmo que use primitivas de banco.
O `table_droppator` (pura infraestrutura) vai para `database/operations.py`.
A separação reflete responsabilidade, não tecnologia.

**Atenção**: `data_correjeitor` chama `table_droppator`. Com a extração,
o import em `etl/sanitizer.py` será:
```python
from pdw.database.operations import table_droppator
```

---

## DT-06 · `get_month_names` e `get_weekday_names` — funções vs constantes

**Decisão**: Manter como funções em `utils/localization.py`. **Não converter para constantes.**

**Justificativa**: Converter para constantes mudaria a interface pública (de chamada de
função para acesso a atributo de módulo). Fora do escopo desta fase. A conversão para
constante pode ser feita em uma refatoração posterior com uma mudança de versão menor.

**Estado atual**:
```python
# utils/localization.py
def get_month_names(): ...    # mantido como está
def get_weekday_names(): ...  # mantido como está
```

---

## DT-07 · Gerenciamento de conexões SQLite — status quo preservado

**Decisão**: Cada função continua abrindo e fechando sua própria conexão SQLite.
Não implementar connection pool ou contexto compartilhado nesta fase.

**Justificativa**: A implementação atual funciona corretamente para o caso de uso
serial (um processo, sem concorrência). Introduzir gerenciamento de conexão
centralizado exigiria alterar a assinatura de todas as funções que recebem `db_file: str` —
o que está fora do escopo desta fase.

**Exceção documentada**: `create_pivot_history` não fecha a conexão (ver RISCO-06).
Este comportamento é preservado intencionalmente.

---

## DT-08 · Variável de versão — localização canônica

**Decisão**: Durante a migração, criar `pdw/__init__.py` com:
```python
__version__ = "10.1.0"
```

E em `config/loader.py`, importar a versão deste local único:
```python
from pdw import __version__ as CURRENT_VERSION
```

**Justificativa**: Elimina a duplicação entre `main()` (hardcoded) e `.cfg`
(hardcoded), centralizando em um único arquivo Python. O `.cfg` ainda deve
ser atualizado para `CURRENT_VERSION = 10.1.0` — este requisito não muda.

---

## DT-09 · Comentários, docstrings e código morto — política de preservação

**Decisão**: Todos os comentários, docstrings, código comentado e o histórico de versão
no header do arquivo são preservados **exatamente como estão**.

**Destino do header e histórico de versão**: Permanecem em `pdw/__init__.py` ou
em `PersonalDataWareHouse.py` (shim), garantindo que o histórico não seja perdido.

**Código morto preservado**:
- Bloco `multithread=True` com `exit(1)` → `core/orchestrator.py`
- Comentários de `transient_data_exportator` → `core/orchestrator.py`
- Comentários de `data_loader_parallel` → `core/orchestrator.py`
- Comentários de `escape_special_chars` → `utils/xml_utils.py`

---

## DT-10 · Validação de regressão — estratégia de teste

**Decisão**: Usar comparação binária de saídas antes/depois de cada passo de extração.

**Protocolo mínimo por passo**:
1. Executar pipeline completo com v9.11.2 → salvar outputs como "baseline"
2. Extrair módulo do passo N
3. Executar pipeline completo com versão parcialmente migrada
4. Comparar outputs: banco `.db` (via `diff` de dump SQL), arquivos `.xlsx` (via hash MD5),
   arquivos `.csv` (via `diff`)
5. Só avançar para o passo N+1 se os outputs forem idênticos

**Flags úteis para teste parcial**:
```ini
RUN_DATA_LOADER = False   ; testa apenas reports, sem recarregar o banco
RUN_REPORTS = False       ; testa apenas o loader, sem gerar reports
CREATE_PIVOT = False      ; isola o pipeline de ETL puro
```

---

## DT-11 · Imports externos — lista completa e módulo destino

Todos os imports existentes são distribuídos para os módulos que os utilizam.
Nenhum import novo é introduzido.

| Import | Usado em (atual) | Módulo destino |
|---|---|---|
| `sqlite3` | múltiplas funções | `database/operations.py`, `etl/loader.py`, `analytics/*.py`, `reports/*.py` |
| `pandas as pd` | múltiplas funções | `etl/loader.py`, `etl/sanitizer.py`, `analytics/*.py`, `reports/*.py` |
| `datetime` | `main` | `config/loader.py`, `infrastructure/logging.py` |
| `numpy as np` | `etl/sanitizer.py` | `etl/sanitizer.py` |
| `configparser` | `main` | `config/loader.py` |
| `os, platform, sys` | `main` | `config/loader.py`, `infrastructure/logging.py`, `pdw/main.py` |
| `threading` | `main` (importado mas não usado) | `core/orchestrator.py` |
| `time` | `main` | `core/orchestrator.py` |
| `xml.etree.ElementTree as ET` | `dataframe_to_xml` | `utils/xml_utils.py` |
| `gzip` | `gzip_compressor` | `utils/compression.py` |
| `shutil` | `gzip_compressor` | `utils/compression.py` |
| `yaml` | `xlsx_report_generator` | `reports/xlsx_generator.py` |

**Observação**: `threading` está importado no arquivo mas **não é usado** em nenhuma
função extraível — o bloco que usaria threads está comentado. O import deve ser
preservado em `core/orchestrator.py` para manter fidelidade ao código original.

---

## Resumo das Decisões

| ID | Decisão | Impacto |
|---|---|---|
| DT-01 | Extração sem reescrita | Baixo risco de regressão |
| DT-02 | Nomenclatura pública preservada | Zero breaking changes |
| DT-03 | Shim de compatibilidade | RunPDW.sh não precisa de alteração |
| DT-04 | Extração folhas-primeiro | Cada passo é validável isoladamente |
| DT-05 | `data_correjeitor` em `etl/sanitizer` | Separação por responsabilidade |
| DT-06 | Manter funções de localização como funções | Interface pública inalterada |
| DT-07 | Status quo de conexões SQLite | Zero refatoração de interface |
| DT-08 | Versão canônica em `pdw/__init__.py` | Elimina duplicação futuramente |
| DT-09 | Preservar todo código morto e comentários | Histórico mantido |
| DT-10 | Validação binária por passo | Regressão detectada antes de avançar |
| DT-11 | Nenhum import novo | Sem novas dependências |

---

## Decisões Técnicas para Reescrita Multi-Linguagem (Fase 4)

As decisões abaixo se aplicam a quem for reescrever o sistema em Java, Rust, Go, C++ ou Node.js.

---

## DT-12 · Entidade de domínio central: `Lancamento`

**Decisão**: Criar uma entidade/struct/record tipada representando um lançamento financeiro.

**Campos obrigatórios**:
```
data:       date/LocalDate    ← coluna "Data" do Excel
tipo:       string            ← coluna "TIPO"
descricao:  string            ← coluna "DESCRICAO" (pós-sanitização)
credito:    float64           ← coluna "Credito" (0.0 quando nulo)
debito:     float64           ← coluna "Debito" (0.0 quando nulo)
origem:     string            ← nome da aba Excel de origem
mes:        string            ← nome PT-BR do mês (derivado de data)
diaSemana:  string            ← nome PT-BR do dia da semana (derivado de data)
```

**Justificativa**: Python usa DataFrames sem schema explícito. Em linguagens tipadas, uma entidade garante contratos em tempo de compilação e elimina a ambiguidade de tipos por coluna.

---

## DT-13 · Nomes de tabela: allowlist obrigatória

**Decisão**: Toda referência a nome de tabela via variável de configuração deve passar por uma allowlist de valores válidos antes de ser usada em SQL.

**Justificativa**: O Python atual concatena nomes de tabela diretamente em SQL (SQL injection — SEC-01). Em reescritas, usar allowlist explícita.

```java
private static final Set<String> ALLOWED_TABLES = Set.of(
    "LANCAMENTOS_GERAIS", "TiposLancamentos", "PARCELAMENTOS",
    "GUIDING", "HistoricoGeral", "HistoricoAnual"
);
```

---

## DT-14 · Ordem de execução do pipeline: invariante arquitetural

**Decisão**: A ordem das fases do pipeline é uma invariante que deve ser respeitada em qualquer reescrita. Não paralelizar entre fases.

**Ordem obrigatória**:
1. Config + Log (abertura)
2. ETL: Excel → SQLite (se `run_loader=true`)
3. Pivot tables (se `create_pivot=true`)
4. Relatórios dinâmicos (se `run_dinamic_report=true`)
5. Sumarizações mensais + parcelamentos
6. Exportação multi-formato
7. Geração Excel (YAML queries)
8. Log (fechamento)

**Justificativa**: Cada fase depende dos dados criados pela fase anterior no banco SQLite.

---

## DT-15 · Formato do log: contrato de interface externa

**Decisão**: O formato da linha de log (`YYYY/MM/DD HH:MM:SS | Version: X | Host: Y | OS: Z | Runs: N | Time: Ts | Last: D`) é um contrato externo e não deve ser alterado sem versionar o formato.

**Justificativa**: Scripts de monitoramento externos podem parsear este formato. Mudar o delimitador ou a ordem dos campos quebraria esses parsers silenciosamente.

---

## DT-16 · Threading: manter desabilitado

**Decisão**: Em qualquer reescrita, não implementar processamento paralelo entre abas do Excel sem análise cuidadosa do modelo de escrita no SQLite.

**Justificativa**: SQLite suporta apenas um escritor simultâneo. Leitura paralela de abas Excel é segura, mas a escrita no banco deve ser serializada ou usar bulk insert único após coleta paralela.

---

## DT-17 · Configuração: validação de versão obrigatória

**Decisão**: O sistema deve validar na inicialização que a versão em `application.properties` (ou equivalente) corresponde à versão compilada do artefato. Em caso de mismatch: `System.exit(1)` (ou equivalente).

**Justificativa**: A versão no .cfg é o mecanismo de proteção contra executar código novo com config antiga ou vice-versa. Esta validação foi a principal causa de falha de deploy na v9.x e deve ser preservada.

---

## DT-18 · Localização PT-BR: dicionários estáticos

**Decisão**: Meses e dias da semana em PT-BR devem ser mapeados a partir de dicionários/maps estáticos. Não usar `locale` do sistema operacional (não portável).

**Justificativa**: A localização do sistema pode não ter `pt_BR.UTF-8`. O PDW usa dicionários hardcoded para garantir consistência independente do ambiente.

```java
// Correto — dicionário estático
static final Map<Month, String> MES_PT_BR = Map.of(
    Month.JANUARY, "Janeiro", Month.FEBRUARY, "Fevereiro", /* ... */
);

// Errado — depende do locale do sistema
String mes = date.getMonth().getDisplayName(TextStyle.FULL, new Locale("pt", "BR"));
```

---

## DT-19 · Sanitização de DESCRICAO: transformações exatas

**Decisão**: As 5 substituições de `clean_description_text` são regras de negócio e devem ser replicadas exatamente, na mesma ordem.

**Transformações (em ordem)**:
1. `[;,]` → `|` (regex)
2. `∴` → ` .'. `
3. `ś` → `s`
4. `"` → `""` (remove aspas duplas)
5. `strip()` (remove espaços no início/fim)

**Justificativa**: Os dados históricos no banco foram processados com estas substituições. Mudá-las geraria dados inconsistentes com o histórico existente.

---

## DT-20 · Arquivos de saída: nomes com timestamp

**Decisão**: Arquivos exportados (CSV, JSON.gz, XML.gz) devem incluir timestamp no nome para evitar sobrescrita. O arquivo Excel de relatório é sobrescrito (sem timestamp).

**Padrão**:
```
{OUT_RPT_FILE}.YYYYMMDD.HHMMSS.csv
{OUT_RPT_FILE}.YYYYMMDD.HHMMSS.json.gz
{OUT_RPT_FILE}.YYYYMMDD.HHMMSS.xml.gz
{OUT_RPT_FILE}.xlsx                      ← sem timestamp, sobrescreve
```
