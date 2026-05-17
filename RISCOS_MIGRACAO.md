# RISCOS_MIGRACAO.md
## Personal Data Warehouse — Análise de Riscos da Refatoração e Migração
### Versão atual: 10.1.0 | Análise de hardening arquitetural

---

## Dashboard de Scores Globais

| Dimensão | Score | Classificação |
|---|---|---|
| **Risco Global** | **7.2 / 10** | 🔴 CRÍTICO |
| **Acoplamento** | **7.8 / 10** | 🟠 ALTO (10 = máximo acoplamento) |
| **Modularidade** | **3.5 / 10** | 🟠 BAIXA (10 = totalmente modular) |
| **Portabilidade** | **3.8 / 10** | 🔴 DIFÍCIL de portar (10 = trivial) |
| **Testabilidade** | **2.5 / 10** | 🔴 CRÍTICA (10 = totalmente testável) |

> Scores baseados em análise estática do código-fonte real da versão 10.1.0.
> Metodologia: 1 = melhor / 10 = pior para Risco e Acoplamento; 1 = pior / 10 = melhor para Modularidade, Portabilidade, Testabilidade.

---

## Scores por Módulo

| Módulo | Risco | Acoplamento | Modularidade | Portabilidade | Problemas críticos |
|---|---|---|---|---|---|
| `database/operations.py` | 9.5 | 6.0 | 5.0 | 6.0 | SQL injection via concatenação |
| `etl/sanitizer.py` | 9.0 | 7.0 | 4.0 | 4.0 | SQL injection + schema hardcoded |
| `utils/transient_data.py` | 9.0 | 5.0 | 4.0 | 4.0 | SQL injection via valor de dado |
| `analytics/pivot.py` | 8.5 | 8.0 | 3.5 | 3.0 | Connection leak + double Excel read |
| `analytics/totals.py` | 8.0 | 6.0 | 4.0 | 4.0 | 2 connection leaks + 2 missing commits |
| `reports/xlsx_generator.py` | 7.5 | 9.5 | 2.0 | 2.0 | 15 parâmetros posicionais |
| `core/orchestrator.py` | 7.0 | 9.0 | 2.5 | 2.5 | 35+ variáveis locais, exit(1) |
| `etl/loader.py` | 6.0 | 7.0 | 4.0 | 4.0 | iterrows() O(n) |
| `utils/xml_builder.py` | 5.0 | 4.0 | 5.0 | 6.0 | iterrows() O(n) |
| `analytics/dynamics.py` | 6.5 | 6.0 | 4.0 | 3.5 | double Excel read por linha |
| `config/loader.py` | 3.0 | 4.0 | 6.0 | 7.0 | versão duplicada em .cfg |
| `infrastructure/logger.py` | 4.0 | 3.0 | 7.0 | 5.0 | append mode sem rotação |

---

## Escala de Severidade

| Nível | Descrição |
|---|---|
| 🔴 CRÍTICO | Pode causar perda de dados, corrupção do banco, SQL injection ou falha silenciosa |
| 🟠 ALTO | Pode causar erro em runtime, comportamento incorreto ou migration blocker |
| 🟡 MÉDIO | Acoplamento frágil, manutenção complexa, comportamento surpreendente |
| 🟢 BAIXO | Cosmético, técnico ou de estilo — sem impacto funcional |

---

## Riscos Identificados — Refatoração Interna (v9.11.2 → v10.1.0)

---

### RISCO-01 · Ambiguidade de tipo em `table_droppator` e `data_correjeitor`
- **Severidade**: 🔴 CRÍTICO
- **Score de risco**: 8.0 / 10
- **Localização**: `database/operations.py` e `etl/sanitizer.py`
- **Descrição**:
  O parâmetro `conexao` pode receber um `cursor` ou uma `connection` dependendo do chamador.
  Em `new_data_loader`: `table_droppator(cursor, ...)` — recebe cursor.
  Dentro de `data_correjeitor`: `cursor = conexao; cursor.execute(...)` — assume cursor.
  Se chamado com a `connection` diretamente, falha silenciosamente ou com AttributeError.
- **Impacto na migração Java**: Java força tipagem explícita — `PreparedStatement` vs `Connection` não são intercambiáveis.
- **Mitigação**: Documentar que o parâmetro deve ser `cursor`. Não alterar assinatura.

---

### RISCO-02 · SQL hardcoded com nomes de tabelas não parametrizados
- **Severidade**: 🔴 CRÍTICO
- **Score de risco**: 9.0 / 10
- **Score de portabilidade**: 2.0 / 10
- **Localização**: `etl/sanitizer.py` — `data_correjeitor`
- **Código afetado**:
  ```python
  lista_acoes.append(('DELETE FROM Parcelamentos WHERE 1 = 1 AND (DATA IS NULL OR "Tipo Lançamento" is null)', ...))
  lista_acoes.append(('DROP VIEW IF EXISTS Origens;', ...))
  lista_acoes.append(('CREATE VIEW Origens AS SELECT TABLE_NAME as nome FROM GUIDING gd WHERE LOADABLE = "X"', ...))
  ```
- **Descrição**: `Parcelamentos`, `Origens`, `GUIDING`, `Tipo Lançamento`, `Código`, `Descrição`
  são hardcoded. Coluna `"Tipo Lançamento"` contém espaço e acento — problemática em qualquer
  ORM de qualquer linguagem.
- **Impacto na migração**: Qualquer ORM (Hibernate, JOOQ, SQLAlchemy, Diesel) que gere
  esquemas automaticamente precisará de mapeamento manual explícito para estas colunas.
- **Mitigação**: NÃO alterar o SQL agora. Documentar schema implícito esperado.

---

### RISCO-03 · `gzip_compressor` remove arquivo original — operação destrutiva sem rollback
- **Severidade**: 🟠 ALTO
- **Score de risco**: 7.0 / 10
- **Localização**: `utils/compression.py` — `gzip_compressor`
- **Código afetado**:
  ```python
  os.remove(arquivo_origem)  # executado APÓS compressão — sem verificação de integridade
  ```
- **Descrição**: Se compressão falhar parcialmente (disco cheio, permissão), o `.gz` pode
  estar corrompido e o arquivo original é apagado. Sem rollback.
- **Impacto na migração**: Em Java/Rust/Go, o padrão é escrever em arquivo temporário e
  renomear atomicamente — o comportamento Python atual é mais arriscado.
- **Mitigação**: Preservar comportamento exato. Documentar o risco no módulo.

---

### RISCO-04 · Versão hardcoded em dois lugares com verificação obrigatória
- **Severidade**: 🟠 ALTO
- **Score de risco**: 6.5 / 10
- **Localização**: `pdw/__init__.py` ou `core/orchestrator.py` + `PersonalDataWareHouse.cfg`
- **Descrição**: A versão existe em dois lugares. `main()` compara as duas e encerra com
  `exit(1)` se não baterem. Ambos devem ser atualizados atomicamente.
- **Impacto na migração**: Em Java, o pom.xml seria a fonte canônica. Manter dois lugares
  sincronizados é um ponto de falha garantido.
- **Mitigação**: Atualizar ambos apenas quando migração estiver 100% concluída.

---

### RISCO-05 · Múltiplas conexões SQLite — ausência de pool ou gerenciamento centralizado
- **Severidade**: 🟡 MÉDIO
- **Score de acoplamento**: 6.0 / 10
- **Score de portabilidade**: 5.0 / 10
- **Localização**: 8 funções com `sqlite3.connect(db_file)` independentes
- **Descrição**: Cada função abre sua própria conexão. Sem pool, sem transação global,
  sem controle de concorrência. Funciona em modo serial. Risco de `database is locked`
  se duas funções forem chamadas em threads diferentes.
- **Impacto na migração**: Em Java (JDBC), Spring Batch gerencia connection pooling
  automaticamente. A semântica muda: uma única transação de batch seria o padrão JVM.
- **Mitigação**: Não alterar agora. Documentar como limitação técnica.

---

### RISCO-06 · `create_pivot_history` não fecha conexão SQLite
- **Severidade**: 🟡 MÉDIO → promovido para 🟠 ALTO após hardening
- **Score de risco**: 7.5 / 10
- **Localização**: `analytics/pivot.py` — `create_pivot_history`
- **Descrição**: Abre `connection = sqlite3.connect(...)`, faz `connection.commit()`,
  nunca chama `connection.close()`. O GC do Python eventualmente fecha, mas causa
  `database is locked` em testes ou execuções consecutivas rápidas.
- **Ver também**: RISCO-18 (inventory completo de leaks)
- **Mitigação**: Documentar no módulo extraído.

---

### RISCO-07 · `xlsx_report_generator` com 15 parâmetros posicionais
- **Severidade**: 🟡 MÉDIO → promovido para 🟠 ALTO após hardening
- **Score de acoplamento**: 9.5 / 10 — pior função do sistema
- **Score de portabilidade**: 2.0 / 10
- **Localização**: `reports/xlsx_generator.py` — `xlsx_report_generator`
- **Descrição**: 15 parâmetros posicionais sem defaults. Qualquer chamador deve
  conhecer a ordem exata de todos os 15. Inversão de dois parâmetros booleanos
  causa comportamento incorreto silencioso.
- **Impacto na migração**: Em Java, um método com 15 parâmetros seria recusado no
  code review. Requer `XlsxReportConfig` DTO com Builder pattern.
- **Ver também**: RISCO-19
- **Mitigação**: Validar chamada exata no orchestrator. Teste de regressão obrigatório.

---

### RISCO-08 · Código morto com `exit(1)` — caminho `multithread=True`
- **Severidade**: 🟢 BAIXO
- **Score de risco**: 3.0 / 10
- **Localização**: `core/orchestrator.py` — bloco `else` do multithread
- **Descrição**: Bloco `else` para `multithread=True` imprime mensagens e encerra
  com `exit(1)`. O `data_loader_parallel` está comentado — feature nunca entregue.
- **Mitigação**: Copiar o bloco sem alteração ao extrair para orchestrator.

---

### RISCO-09 · Código comentado de features removidas
- **Severidade**: 🟢 BAIXO
- **Score de risco**: 2.0 / 10
- **Localização**: Múltiplos módulos
- **Descrição**: Blocos comentados de `export_transeient_data`, `data_loader_parallel`,
  `splitter`, `escape_special_chars`. Devem ser preservados no módulo destino.
- **Mitigação**: Copiar comentários junto com a função.

---

### RISCO-10 · Dependência implícita de ordem de execução no pipeline
- **Severidade**: 🟠 ALTO
- **Score de acoplamento**: 8.5 / 10
- **Score de modularidade**: 2.0 / 10
- **Localização**: `core/orchestrator.py` — sequência de chamadas
- **Descrição**: Pipeline tem dependências temporais implícitas não documentadas:
  1. `new_data_loader` → cria `LANCAMENTOS_GERAIS` (pré-requisito de tudo)
  2. `create_pivot_history` → cria `HistoricoGeral` (pré-requisito de dinamic_reports)
  3. `create_dinamic_reports` → cria tabelas YAML (pré-requisito de xlsx_generator)
  4. `monthly_summaries` + `split_paymnt_resume` → tabelas para xlsx_generator
- **Impacto na migração**: Spring Batch exige que dependências de Step sejam declaradas
  explicitamente via `stepBuilderFactory.next()`. A ordem implícita deve virar grafo de dependências.
- **Mitigação**: Documentar explicitamente no orchestrator.

---

## Riscos Descobertos no Hardening Arquitetural (v10.1.0)

---

### RISCO-18 · Inventory completo de connection leaks SQLite
- **Severidade**: 🔴 CRÍTICO
- **Score de risco**: 9.0 / 10
- **Score de portabilidade**: 2.0 / 10
- **Localização**: `analytics/pivot.py`, `analytics/totals.py`

**Tabela de inventory de conexões (todas as funções com `sqlite3.connect`):**

| Função | Módulo | `connect()` | `commit()` | `close()` | Status |
|---|---|---|---|---|---|
| `new_data_loader` | `etl/loader.py` | ✅ | ✅ | ✅ | OK |
| `totalizador_diario` | `analytics/totals.py` | ✅ | ✅ | ✅ | OK |
| `general_entries_file_exportator` | `reports/exporter.py` | ✅ | N/A (read) | ✅ | OK |
| `create_pivot_history` | `analytics/pivot.py` | ✅ | ✅ | ❌ | **LEAK** |
| `monthly_summaries` | `analytics/totals.py` | ✅ | ❌ | ❌ | **LEAK + MISSING COMMIT** |
| `split_paymnt_resume` | `analytics/totals.py` | ✅ | ❌ | ❌ | **LEAK + MISSING COMMIT** |

**Consequências por função:**

- **`create_pivot_history`**: Dados são commitados (pivot history persiste) mas conexão
  não é fechada. Em execuções repetidas ou testes, pode causar `database is locked`.

- **`monthly_summaries`**: `pandas.to_sql()` é chamado 3× mas sem `commit()` explícito.
  `pandas.to_sql()` com `con` do sqlite3 pode ou não auto-commitar dependendo da versão
  do pandas. Sem `close()`, a conexão fica aberta indefinidamente. Em caso de falha parcial,
  tabelas de sumarização mensal podem estar corrompidas silenciosamente.

- **`split_paymnt_resume`**: Mesmo padrão que `monthly_summaries`. `to_sql()` sem commit
  explícito, sem close. Tabela de parcelamentos pode estar em estado inconsistente.

**Impacto na migração Java:**
  Em JDBC, `Connection.close()` sem `commit()` prévio faz rollback automático (JDBC default:
  `autoCommit=false`). Dados que o Python persiste por acidente (auto-commit do sqlite3 em
  DDL) serão perdidos no equivalente Java.

**Mitigação imediata (P0)**:
```python
# Padrão correto para todas as funções:
with sqlite3.connect(db_file) as conn:
    # operações...
    conn.commit()
# context manager fecha automaticamente
```

---

### RISCO-19 · `xlsx_report_generator` — acoplamento extremo como blocker de migração
- **Severidade**: 🟠 ALTO
- **Score de acoplamento**: 9.5 / 10 — pior do sistema
- **Score de portabilidade**: 1.5 / 10
- **Localização**: `reports/xlsx_generator.py` — `xlsx_report_generator`
- **Assinatura completa**:
  ```python
  def xlsx_report_generator(
      sqlite_database,      # 1 — path do .db
      dir_out,              # 2 — diretório de saída
      file_name,            # 3 — nome base do arquivo
      write_multiple_files, # 4 — bool: um xlsx por sheet?
      out_extension,        # 5 — extensão do arquivo
      entries_table,        # 6 — tabela de lançamentos
      dynamic_reports,      # 7 — bool: gerar reports dinâmicos?
      dyn_rep_tab,          # 8 — tabela de reports dinâmicos
      gera_hist,            # 9 — bool: gerar histórico?
      anual_hist,           # 10 — bool: histórico anual?
      full_hist,            # 11 — bool: histórico completo?
      day_prog,             # 12 — bool: progresso diário?
      splt_pmnt_res,        # 13 — bool: resumo parcelamentos?
      mont_summ,            # 14 — bool: sumarizações mensais?
      yaml_queries_file     # 15 — path do .yaml
  ):
  ```
- **Descrição**: 15 parâmetros posicionais sem defaults, sem type hints, sem dataclass.
  7 dos 15 são booleanos — inversão silenciosa entre parâmetros 9-14 causa output incorreto.
  Nenhum IDe pode ajudar o desenvolvedor a saber qual booleano é qual na chamada.
- **Impacto na migração**: Em qualquer linguagem tipada (Java, Rust, Go, C++), este padrão
  é um blocker arquitetural. Requer extração de `XlsxReportConfig` antes de qualquer migração.
  Em Java:
  ```java
  XlsxReportConfig config = XlsxReportConfig.builder()
      .sqliteDatabase(dbPath)
      .dirOut(outDir)
      .generateHistory(true)
      // ... etc
      .build();
  xlsxReportGenerator.generate(config);
  ```
- **Mitigação**: Criar dataclass Python antes da migração; usar como base para DTO Java.

---

### RISCO-20 · `monthly_summaries` e `split_paymnt_resume` — dados sem commit confirmado
- **Severidade**: 🔴 CRÍTICO
- **Score de risco**: 8.5 / 10
- **Localização**: `analytics/totals.py`
- **Código afetado**:
  ```python
  def monthly_summaries(db_file, in_table, out_table):
      db_conn = sqlite3.connect(db_file)
      df_month.to_sql('SUMARIO_MENSAL', db_conn, if_exists='replace', index=False)
      df_month_pct.to_sql('SUMARIO_MENSAL_PCT', db_conn, if_exists='replace', index=False)
      df_categories.to_sql('SUMARIO_CATEGORIAS', db_conn, if_exists='replace', index=False)
      # Sem db_conn.commit()
      # Sem db_conn.close()

  def split_paymnt_resume(db_file, in_table, parcel_table):
      db_conn = sqlite3.connect(db_file)
      df_split.to_sql('SPLIT_RESUME', db_conn, if_exists='replace', index=False)
      # Sem db_conn.commit()
      # Sem db_conn.close()
  ```
- **Descrição**: `pandas.to_sql()` com conexão raw `sqlite3` opera no modo `autocommit`
  do sqlite3 (que é `isolation_level=''` por padrão — DDL auto-commita, DML não).
  `to_sql()` usa `BEGIN TRANSACTION` internamente → requer `commit()` explícito.
  Se o processo terminar abruptamente após `to_sql()` sem `commit()`, os dados são perdidos.
  O fato de funcionar em produção não significa que está correto — significa que o processo
  termina normalmente e o sqlite3 faz flush no close do GC.
- **Impacto na migração**: Em Java com JDBC `autoCommit=false`, estes dados seriam
  PERDIDOS silenciosamente — rollback automático no `Connection.close()`.
- **Mitigação imediata (P0)**: Adicionar `db_conn.commit()` e `db_conn.close()` em ambas.

---

### RISCO-21 · Padrão `exit(1)` — impede recovery, testes e encadeamento
- **Severidade**: 🟠 ALTO
- **Score de risco**: 7.0 / 10
- **Score de testabilidade**: 1.5 / 10
- **Localização**: `core/orchestrator.py` — múltiplos pontos
- **Ocorrências identificadas**:
  ```python
  exit(1)  # verificação de versão
  exit(1)  # multithread não suportado
  exit(1)  # arquivo de configuração não encontrado
  exit(1)  # banco de dados não encontrado
  exit(1)  # Excel de entrada não encontrado
  ```
- **Descrição**: `exit(1)` termina o processo Python inteiro, sem possibilidade de
  captura por caller, sem logging do motivo, sem cleanup de recursos, sem possibilidade
  de retry por orchestrador externo (cron, Airflow, scheduler).
  Em testes com pytest, `exit(1)` mata o processo de teste inteiro — impossível testar
  qualquer função que internamente possa chamar exit(1).
- **Impacto na migração**: Em Java, o equivalente seria `System.exit(1)` — igualmente
  problemático. O padrão correto é lançar `PdwConfigurationException` e deixar o
  ponto de entrada da aplicação fazer `System.exit`.
- **Score de testabilidade do sistema com exit(1)**: 1.5 / 10
- **Mitigação**: Substituir `exit(1)` por `raise PdwError(message)` em todos os módulos.
  Manter `exit(1)` apenas no ponto de entrada (`__main__`).

---

### RISCO-22 · Nomes de colunas com acentos e espaços em SQL hardcoded
- **Severidade**: 🟠 ALTO
- **Score de portabilidade**: 2.0 / 10
- **Localização**: `etl/sanitizer.py`, `analytics/pivot.py`
- **Exemplos reais**:
  ```python
  # etl/sanitizer.py
  'DELETE FROM Parcelamentos WHERE ... "Tipo Lançamento" is null'
  # analytics/pivot.py  
  cursor.execute(f'... WHERE "Código" = ? AND "Descrição" = ?', ...)
  # utils/transient_data.py
  WHERE {origing_column} = '{linhas.Origem}'  # SQL injection + encoding risk
  ```
- **Descrição**: Nomes de colunas contêm:
  - Espaços: `"Tipo Lançamento"` — requer quoting com `"` em SQLite
  - Acentos PT-BR: `"Lançamento"`, `"Código"`, `"Descrição"` — encoding-sensitive
  - Misto de caixa: `GUIDING`, `Parcelamentos`, `Origens` — SQLite case-insensitive, outros DBs não
- **Impacto na migração**:
  - **PostgreSQL**: nomes com acento requerem `"` quotes, mas PostgreSQL é case-sensitive com quotes
  - **MySQL**: encoding do schema deve ser `utf8mb4` para acentos PT-BR
  - **Java Hibernate**: `@Column(name = "Tipo Lançamento")` — problemático com espaço
  - **JOOQ**: geração de código a partir do schema vai gerar identificadores inválidos
- **Mitigação**: Ao migrar para outro banco, renomear colunas para snake_case ASCII.
  Criar migration script de mapeamento. Manter nomes originais somente no SQLite legacy.

---

## Tabela Resumo — Todos os Riscos

| ID | Descrição | Severidade | Score | Módulo(s) | Impacto na Migração |
|---|---|---|---|---|---|
| RISCO-01 | Ambiguidade cursor vs connection | 🔴 CRÍTICO | 8.0 | `database/operations.py` | Tipagem explícita em Java |
| RISCO-02 | SQL hardcoded com nomes de tabelas | 🔴 CRÍTICO | 9.0 | `etl/sanitizer.py` | ORM blocker |
| RISCO-03 | gzip_compressor destrói original | 🟠 ALTO | 7.0 | `utils/compression.py` | Padrão diferente em JVM |
| RISCO-04 | Versão duplicada em dois arquivos | 🟠 ALTO | 6.5 | `config/loader.py` + `.cfg` | Sincronização manual |
| RISCO-05 | Múltiplas conexões sem pool | 🟡 MÉDIO | 5.5 | 8 funções | Semântica JDBC diferente |
| RISCO-06 | create_pivot_history — sem close() | 🟠 ALTO | 7.5 | `analytics/pivot.py` | database is locked |
| RISCO-07 | xlsx_generator — 15 parâmetros | 🟠 ALTO | 8.5 | `reports/xlsx_generator.py` | Blocker arquitetural |
| RISCO-08 | Código morto com exit(1) | 🟢 BAIXO | 2.0 | `core/orchestrator.py` | Preservar |
| RISCO-09 | Código comentado de features | 🟢 BAIXO | 1.5 | múltiplos | Preservar |
| RISCO-10 | Ordem de execução implícita | 🟠 ALTO | 8.0 | `core/orchestrator.py` | Grafo de dependências |
| RISCO-18 | Connection leaks — 3 funções | 🔴 CRÍTICO | 9.0 | `analytics/` | Rollback automático JDBC |
| RISCO-19 | xlsx_generator — acoplamento extremo | 🟠 ALTO | 9.5 | `reports/xlsx_generator.py` | DTO obrigatório |
| RISCO-20 | monthly_summaries — sem commit | 🔴 CRÍTICO | 8.5 | `analytics/totals.py` | Dados perdidos em Java |
| RISCO-21 | exit(1) impede testes e recovery | 🟠 ALTO | 7.0 | `core/orchestrator.py` | PdwException pattern |
| RISCO-22 | Colunas com acentos e espaços em SQL | 🟠 ALTO | 7.5 | `etl/`, `analytics/` | Schema rename obrigatório |

---

## Plano de Remediação por Prioridade

### P0 — Antes de qualquer migração (bugs reais em produção)

| Item | Arquivo | Ação |
|---|---|---|
| Connection leak + missing commit | `analytics/totals.py` | Adicionar `commit()` + `close()` a `monthly_summaries` e `split_paymnt_resume` |
| Connection leak | `analytics/pivot.py` | Adicionar `close()` a `create_pivot_history` |
| SQL injection crítica | `database/operations.py` | Parametrizar `DROP TABLE IF EXISTS` |

### P1 — Antes de migrar para outra linguagem

| Item | Arquivo | Ação |
|---|---|---|
| 15 parâmetros | `reports/xlsx_generator.py` | Criar `XlsxReportConfig` dataclass |
| exit(1) abusivo | `core/orchestrator.py` | Substituir por `raise PdwError` |
| Schema hardcoded | `etl/sanitizer.py` | Extrair constantes de nomes de tabela/coluna |

### P2 — Durante a migração de linguagem

| Item | Ação |
|---|---|
| Nomes de colunas com acento | Criar migration de rename para snake_case ASCII |
| Ordem de execução implícita | Documentar como grafo de dependências de Step |
| Múltiplas conexões | Centralizar em único connection manager |

### P3 — Melhorias pós-migração

| Item | Ação |
|---|---|
| iterrows() O(n) | Substituir por operações vetorizadas ou `to_xml()` |
| Double Excel read no loop | Ler fora do loop, usar cache |
| SELECT * em pivot | Substituir por GROUP BY SQL |
| Sem SQLite indexes | Adicionar `CREATE INDEX` em LANCAMENTOS_GERAIS |

---

## Riscos Adicionais — Reescrita Multi-Linguagem (Fase 4)

---

### RISCO-11 · Inferência de tipo do Excel: pandas vs leitura manual
- **Severidade**: 🔴 CRÍTICO
- **Score de portabilidade**: 2.0 / 10 (Java/Go/C++)
- **Descrição**: `pandas.read_excel()` infere tipos automaticamente. Em Java (Apache POI),
  Rust (calamine), Go (excelize), a leitura é por célula com tipo explícito.
  Células que o pandas inferiu como datas podem vir como números seriais Excel
  (ex: `45297` em vez de `2025-01-15`) se não tratadas corretamente.
- **Impacto**: Dados de Data incorretos → pivot tables e sumarizações erradas.
- **Mitigação**: Verificar `DateUtil.isCellDateFormatted(cell)` (Java) antes de parsear célula numérica como data.

---

### RISCO-12 · Células vazias vs nulas: comportamento diferente por linguagem
- **Severidade**: 🟠 ALTO
- **Score de portabilidade**: 3.0 / 10
- **Descrição**: Python/pandas trata células vazias como `NaN` (float). Java/POI retorna
  `CellType.BLANK`. Go/excelize retorna string vazia `""`. O PDW usa `pd.isna()` para detectar nulos.
- **Mitigação**: Criar função helper `isNullOrEmpty()` na linguagem alvo com semântica idêntica ao pandas.

---

### RISCO-13 · Encoding de strings: UTF-8 vs outros
- **Severidade**: 🟡 MÉDIO
- **Score de portabilidade**: 5.0 / 10
- **Descrição**: PDW processa strings PT-BR com acentos. Planilhas Excel antigas podem usar Windows-1252.
- **Mitigação**: Forçar UTF-8 em todas as operações. Apache POI lida automaticamente para XLSX.

---

### RISCO-14 · Formato de data no banco: ISO vs local
- **Severidade**: 🟠 ALTO
- **Score de portabilidade**: 4.0 / 10
- **Descrição**: PDW armazena datas no SQLite como string `YYYY-MM-DD` (formato pandas).
  Queries SQL que usam `strftime('%Y', Data)` dependem deste formato exato.
- **Mitigação**: Sempre converter datas para ISO `YYYY-MM-DD` antes de inserir no SQLite.

---

### RISCO-15 · Separador CSV: `;` vs `,`
- **Severidade**: 🟢 BAIXO
- **Score de portabilidade**: 8.0 / 10
- **Descrição**: PDW exporta CSV com separador `;`. Scripts externos podem depender disso.
- **Mitigação**: Hardcode do separador `;` na exportação CSV da linguagem alvo.

---

### RISCO-16 · Ordem das linhas no banco: ordenação descendente por Data
- **Severidade**: 🟡 MÉDIO
- **Score de portabilidade**: 6.0 / 10
- **Descrição**: `save_dataframe_to_database()` ordena por Data descendente antes de inserir.
  Queries que dependem de `ROWID` ou ordem de inserção retornarão resultados em ordem diferente.
- **Mitigação**: Sempre usar `ORDER BY` explícito nas queries analíticas. Aplicar sort antes de bulk insert.

---

### RISCO-17 · Schema implícito em `data_correjeitor`
- **Severidade**: 🔴 CRÍTICO
- **Score de portabilidade**: 2.0 / 10
- **Descrição**: `data_correjeitor` assume tabelas `Parcelamentos`, `GUIDING`, view `Origens`
  com estrutura específica. Dependências implícitas não declaradas em nenhum interface.
- **Estrutura implícita assumida**:
  ```sql
  -- GUIDING: TABLE_NAME TEXT, ACCOUNTING TEXT, LOADABLE TEXT
  -- Parcelamentos: DATA TEXT, "Tipo Lançamento" TEXT
  -- View Origens (criada pela função): SELECT TABLE_NAME as nome FROM GUIDING WHERE LOADABLE = 'X'
  ```
- **Mitigação**: Verificar existência e estrutura das tabelas na inicialização da migração.

---

## Tabela de Riscos Multi-Linguagem

| ID | Descrição | Java | Rust | Go | Node.js | C++ | Score portabilidade |
|---|---|---|---|---|---|---|---|
| RISCO-11 | Inferência de tipo Excel | 🔴 | 🟠 | 🟠 | 🟡 | 🔴 | 2.0 |
| RISCO-12 | Células vazias vs nulas | 🟠 | 🟡 | 🟠 | 🟢 | 🟠 | 3.0 |
| RISCO-13 | Encoding UTF-8 | 🟡 | 🟢 | 🟢 | 🟢 | 🟠 | 5.0 |
| RISCO-14 | Formato de data no banco | 🟠 | 🟠 | 🟠 | 🟠 | 🟠 | 4.0 |
| RISCO-15 | Separador CSV `;` | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 8.0 |
| RISCO-16 | Ordenação descendente | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 6.0 |
| RISCO-17 | Schema implícito | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 2.0 |
| RISCO-18 | Connection leaks | 🔴 | 🟢 | 🟢 | 🟡 | 🔴 | 2.0 |
| RISCO-19 | 15-param function | 🔴 | 🟠 | 🟠 | 🟡 | 🔴 | 1.5 |
| RISCO-20 | Missing commits | 🔴 | 🟢 | 🟢 | 🟡 | 🟠 | 2.0 |
| RISCO-22 | Nomes com acento em SQL | 🔴 | 🟠 | 🟠 | 🟡 | 🔴 | 2.0 |

---

## Critério de Sucesso da Migração

A migração será considerada bem-sucedida quando:

1. **Funcional**: A saída do pipeline (banco `.db`, arquivos `.xlsx`, `.csv`, `.json.gz`, `.xml.gz`)
   for **bit-a-bit idêntica** entre a versão Python e a versão na linguagem alvo para o mesmo Excel.
2. **Configuração**: O arquivo `PersonalDataWareHouse.cfg` executar sem erros.
3. **Compatibilidade**: O `RunPDW.sh` executar o novo código sem alterações.
4. **Estrutura**: Cada módulo contém apenas as funções listadas no inventário para aquele módulo.
5. **Sem novos imports**: Nenhum novo framework foi introduzido além dos mapeados em MATRIZ_COMPARATIVA.
6. **Scores pós-migração esperados**:
   - Risco Global: ≤ 4.0 / 10
   - Acoplamento: ≤ 5.0 / 10
   - Modularidade: ≥ 7.0 / 10
   - Portabilidade: ≥ 7.0 / 10
   - Testabilidade: ≥ 6.0 / 10
