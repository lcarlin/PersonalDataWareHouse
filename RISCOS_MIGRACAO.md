# RISCOS_MIGRACAO.md
## Personal Data Warehouse — Riscos da Refatoração
### Versão atual: 9.11.2 → Versão alvo: 10.1.0

---

## Escala de Severidade

| Nível | Descrição |
|---|---|
| 🔴 CRÍTICO | Pode causar perda de dados, corrupção do banco ou falha silenciosa |
| 🟠 ALTO | Pode causar erro em runtime ou comportamento diferente do esperado |
| 🟡 MÉDIO | Pode causar confusão de manutenção ou acoplamento frágil |
| 🟢 BAIXO | Cosmético, técnico ou de estilo — sem impacto funcional |

---

## Riscos Identificados

---

### RISCO-01 · Ambiguidade de tipo em `table_droppator` e `data_correjeitor`
- **Severidade**: 🔴 CRÍTICO
- **Localização**: `table_droppator` (L490–493) e `data_correjeitor` (L461–488)
- **Descrição**:
  O parâmetro `conexao` em ambas as funções é nomeado como "conexão",
  mas pode receber **ou um `cursor`** ou **uma `connection`** dependendo do chamador:
  - Em `new_data_loader` (L832): `table_droppator(cursor, ...)` → recebe `cursor`
  - Em `new_data_loader` (L879): `data_correjeitor(cursor, ...)` → recebe `cursor`
  - Dentro de `data_correjeitor`: `cursor = conexao; cursor.execute(...)` → OK se for cursor
  - O objeto `cursor` em `new_data_loader` é criado como `cursor = conn.cursor()` (L829)

  O problema: se no futuro alguém chamar `table_droppator(conn, ...)` com a `connection`
  diretamente (lógica razoável pelo nome do parâmetro), o `cursor.execute()` falhará,
  pois `connection.execute()` não existe no sqlite3 padrão sem a interface simplificada.
- **Impacto durante extração**: Ao mover `table_droppator` para `database/operations.py`,
  a assinatura precisa ser clarificada — sem renomear a função pública.
- **Mitigação**: Documentar explicitamente que o parâmetro deve ser um `cursor`, não connection.
  Não alterar a assinatura durante esta fase de modularização.

---

### RISCO-02 · SQL hardcoded com nomes de tabelas não parametrizados em `data_correjeitor`
- **Severidade**: 🔴 CRÍTICO
- **Localização**: `data_correjeitor` (L475–480)
- **Código afetado**:
  ```python
  lista_acoes.append(('DELETE FROM Parcelamentos WHERE 1 = 1 AND (DATA IS NULL OR "Tipo Lançamento" is null) ;', ...))
  lista_acoes.append((f'DROP VIEW IF EXISTS Origens; ', ...))
  lista_acoes.append((f"create view Origens as select TABLE_NAME as nome from GUIDING gd where ...", ...))
  ```
- **Descrição**:
  Os nomes `Parcelamentos`, `Origens` e `GUIDING` são **hardcoded no corpo da função**
  e não são passados como parâmetros. Se o arquivo `.cfg` usar nomes diferentes para
  estas tabelas, o SQL não refletirá isso — a limpeza de dados ocorrerá na tabela errada
  ou falhará silenciosamente (DELETE com WHERE que não encontra linhas não gera erro).
- **Impacto durante extração**: Ao mover para `etl/sanitizer.py`, esta dependência
  implícita no schema deve ser documentada no docstring da função.
- **Mitigação**: NÃO alterar o SQL agora (fora do escopo). Documentar o schema esperado.

---

### RISCO-03 · `gzip_compressor` remove o arquivo original — operação destrutiva sem rollback
- **Severidade**: 🟠 ALTO
- **Localização**: `gzip_compressor` (L533–541)
- **Código afetado**:
  ```python
  os.remove(arquivo_origem)  # linha 541 — executado APÓS a compressão
  ```
- **Descrição**:
  A função comprime o arquivo e remove o original. Se a abertura do arquivo de saída
  falhar no meio (disco cheio, permissão, etc.), o `gzip.open` pode ter criado um `.gz`
  corrompido — e o `os.remove` **ainda será executado** porque está fora do bloco `with`.
  O arquivo original é perdido.
- **Impacto durante extração**: A lógica deve ser preservada exatamente ao mover para
  `utils/compression.py`. Não alterar o comportamento.
- **Mitigação**: Ao extrair o módulo, adicionar comentário explícito sobre o risco.
  Não alterar o código (fora do escopo desta refatoração).

---

### RISCO-04 · Versão hardcoded em dois lugares com verificação de match obrigatória
- **Severidade**: 🟠 ALTO
- **Localização**: `main()` (L100) e `PersonalDataWareHouse.cfg` (linha 18)
- **Código afetado**:
  ```python
  current_version = "9.11.2"   # em main()
  # e
  CURRENT_VERSION = 9.11.2     # em .cfg
  ```
- **Descrição**:
  A versão existe em dois lugares. A função `main` compara as duas e encerra com `exit(1)`
  se não baterem. Durante a migração para 10.1.0, **ambos** devem ser atualizados
  atomicamente. Se apenas o código for atualizado e não o `.cfg`, ou vice-versa,
  a aplicação se recusará a executar.
- **Impacto durante extração**: Quando `config/loader.py` for extraído, a versão esperada
  deve ser importada de um único lugar canônico (ex: `pdw/__init__.py`).
- **Mitigação**: Atualizar ambos apenas quando a migração estiver 100% concluída e testada.

---

### RISCO-05 · Conexões SQLite abertas por função sem pool — múltiplos `connect()` por execução
- **Severidade**: 🟡 MÉDIO
- **Localização**: Múltiplas funções
- **Funções afetadas**:
  `new_data_loader`, `create_pivot_history`, `split_paymnt_resume`,
  `monthly_summaries`, `general_entries_file_exportator`, `totalizador_diario`,
  `xlsx_report_generator`, `create_dinamic_reports`
- **Descrição**:
  Cada função abre sua própria conexão `sqlite3.connect(db_file)` e a fecha
  (ou não — ver RISCO-06). Isso é funcionalmente correto para SQLite em modo serial,
  mas significa que não há controle centralizado de transações.
  Se uma função falhar após escrever dados mas antes de fechar a conexão, dados
  podem ficar em estado parcialmente commitado dependendo do modo WAL do SQLite.
- **Impacto durante extração**: As assinaturas das funções receberão `db_file: str`
  como hoje — sem alteração. O comportamento de conexão individual é preservado.
- **Mitigação**: Não alterar agora. Documentar como limitação técnica.

---

### RISCO-06 · `create_pivot_history` não fecha a conexão SQLite
- **Severidade**: 🟡 MÉDIO
- **Localização**: `create_pivot_history` (L496–530)
- **Código afetado**: A função abre `connection = sqlite3.connect(...)`, faz `connection.commit()` mas **nunca chama `connection.close()`**
- **Descrição**:
  O objeto `connection` vai para garbage collection do Python, que eventualmente
  fechará a conexão. Em ambiente normal isso funciona. Mas com múltiplas chamadas
  ou em contextos de teste, pode causar `database is locked` se outra função
  tentar abrir o mesmo arquivo logo depois.
- **Impacto durante extração**: Ao mover para `analytics/pivot.py`, preservar o
  comportamento atual (não adicionar `connection.close()`).
- **Mitigação**: Documentar no módulo extraído. Não corrigir nesta fase.

---

### RISCO-07 · `xlsx_report_generator` tem 15 parâmetros — alta superfície de acoplamento
- **Severidade**: 🟡 MÉDIO
- **Localização**: `xlsx_report_generator` (L883–975)
- **Descrição**:
  A função recebe 15 parâmetros posicionais. Ao extrair para `reports/xlsx_generator.py`,
  **todos os 15 parâmetros** devem ser passados corretamente pelo `orchestrator.py`.
  Qualquer erro de ordem ou nomenclatura na chamada causará comportamento incorreto
  silencioso (sem exception, dados exportados errados).
- **Impacto durante extração**: O chamador em `orchestrator.py` deve reproduzir
  exatamente a mesma chamada que hoje existe em `main()` (L292–294).
- **Mitigação**: Validar a chamada com teste de regressão antes de declarar migração concluída.

---

### RISCO-08 · Código morto com `exit(1)` — caminho `multithread=True`
- **Severidade**: 🟢 BAIXO
- **Localização**: `main()` (L243–265)
- **Descrição**:
  O bloco `else` para `multithread=True` imprime uma série de mensagens e
  encerra com `exit(1)`. O código `data_loader_parallel` está comentado.
  Durante a extração, este bloco **deve ser preservado integralmente**
  (incluindo comentários) ao mover para `orchestrator.py`.
- **Mitigação**: Copiar o bloco sem qualquer alteração.

---

### RISCO-09 · Código comentado de features removidas/planejadas
- **Severidade**: 🟢 BAIXO
- **Localização**: `main()` (L156–157, L299–302) e outros
- **Descrição**:
  Existem vários blocos de código comentado referenciando features removidas:
  - `export_transeient_data` / `transient_data_exportator`
  - `data_loader_parallel`
  - `splitter = config.getint(...)` 
  - `escape_special_chars` em `dataframe_to_xml`
  
  Conforme as regras, estes comentários **NÃO devem ser removidos**.
  Devem ser preservados no módulo destino.
- **Mitigação**: Ao extrair cada função, mover os comentários junto com ela.

---

### RISCO-10 · Dependência implícita de ordem de execução no pipeline
- **Severidade**: 🟠 ALTO
- **Localização**: `main()` — ordem de chamadas (L238–294)
- **Descrição**:
  O pipeline tem dependências temporais implícitas:
  1. `new_data_loader` deve rodar antes de tudo (cria `LANCAMENTOS_GERAIS`)
  2. `create_pivot_history` deve rodar antes de `create_dinamic_reports` (cria `HistoricoGeral`)
  3. `create_dinamic_reports` deve rodar antes de `xlsx_report_generator`
     (cria tabelas que o YAML referencia)
  4. `monthly_summaries` e `split_paymnt_resume` devem rodar antes de `xlsx_report_generator`
     (criam tabelas que as queries do YAML usam)
  
  Esta ordem não está documentada — está apenas implícita na sequência do código.
- **Impacto durante extração**: O `orchestrator.py` deve preservar **exatamente** esta sequência.
- **Mitigação**: Documentar explicitamente no `orchestrator.py` extraído.

---

## Tabela Resumo de Riscos

| ID | Descrição | Severidade | Função(ões) | Impacto na Extração |
|---|---|---|---|---|
| RISCO-01 | Ambiguidade cursor vs connection | 🔴 CRÍTICO | `table_droppator`, `data_correjeitor` | Documentar tipo esperado |
| RISCO-02 | SQL com nomes hardcoded | 🔴 CRÍTICO | `data_correjeitor` | Documentar schema implícito |
| RISCO-03 | `gzip_compressor` destrói original | 🟠 ALTO | `gzip_compressor` | Preservar comportamento |
| RISCO-04 | Versão duplicada em dois arquivos | 🟠 ALTO | `main`, `.cfg` | Atualizar atomicamente |
| RISCO-05 | Múltiplas conexões SQLite | 🟡 MÉDIO | 8 funções | Preservar como está |
| RISCO-06 | Conexão não fechada | 🟡 MÉDIO | `create_pivot_history` | Preservar como está |
| RISCO-07 | 15 parâmetros em xlsx_generator | 🟡 MÉDIO | `xlsx_report_generator` | Validar chamada exata |
| RISCO-08 | Código morto com exit(1) | 🟢 BAIXO | `main` | Copiar sem alterar |
| RISCO-09 | Comentários de código removido | 🟢 BAIXO | múltiplas | Preservar junto com função |
| RISCO-10 | Ordem de execução implícita | 🟠 ALTO | `main` → pipeline | Documentar no orchestrator |

---

## Critério de Sucesso da Migração

A migração será considerada bem-sucedida quando:

1. **Funcional**: A saída do pipeline (banco `.db`, arquivos `.xlsx`, `.csv`, `.json.gz`, `.xml.gz`) for **bit-a-bit idêntica** entre v9.11.2 e v10.1.0 para o mesmo arquivo Excel de entrada.
2. **Configuração**: O arquivo `PersonalDataWareHouse.cfg` com `CURRENT_VERSION = 10.1.0` executar sem erros.
3. **Compatibilidade**: O `RunPDW.sh` executar o novo código sem alterações (via shim ou ajuste de path).
4. **Estrutura**: Cada módulo contém apenas as funções listadas no inventário para aquele módulo.
5. **Sem novos imports**: Nenhum novo framework ou biblioteca foi introduzido.

---

## Riscos Adicionais para Reescrita Multi-Linguagem (Fase 4)

Os riscos abaixo se aplicam especificamente ao processo de reescrita completa em outra linguagem.

---

### RISCO-11 · Inferência de tipo do Excel: pandas vs leitura manual — CRÍTICO

**Descrição**: `pandas.read_excel()` infere automaticamente tipos de células (número, data, string, booleano). Em Java (Apache POI), Rust (calamine), Go (excelize), a leitura é por célula com tipo explícito. Células que o pandas inferiu como datas podem vir como números seriais Excel (ex: `45297` em vez de `2025-01-15`) se não tratadas corretamente.

**Impacto**: Dados de Data incorretos → pivot tables e sumarizações erradas.

**Mitigação**: Verificar `DateUtil.isCellDateFormatted(cell)` (Java) ou equivalente antes de parsear qualquer célula numérica como data.

---

### RISCO-12 · Células vazias vs nulas: comportamento diferente por linguagem — ALTO

**Descrição**: O Python/pandas trata células vazias como `NaN` (float). Em Java, POI retorna `CellType.BLANK`. Em Go/excelize, células ausentes retornam string vazia `""`. O PDW usa `pd.isna()` para detectar nulos — o equivalente é diferente em cada linguagem.

**Mitigação**: Criar função helper de "is_null_or_empty" na linguagem alvo que mapeia exatamente ao comportamento do pandas (`pd.isna()` retorna True para `None`, `NaN`, `pd.NaT`).

---

### RISCO-13 · Encoding de strings: UTF-8 vs outros — MÉDIO

**Descrição**: O PDW processa strings como `∴` (ponto triplo), `ś` (s com cedilha), caracteres acentuados PT-BR. O Python 3 usa UTF-8 internamente. Planilhas Excel antigas podem usar Windows-1252 em campos de texto.

**Impacto**: Caracteres especiais podem corromper ao ler com encoding incorreto.

**Mitigação**: Forçar UTF-8 em todas as operações de leitura/escrita. Apache POI lida com isso automaticamente para XLSX.

---

### RISCO-14 · Formato de data no banco: ISO vs local — ALTO

**Descrição**: O PDW armazena datas no SQLite como string no formato que o pandas gera ao chamar `to_sql()`. O formato padrão do pandas é `YYYY-MM-DD` para datas e `YYYY-MM-DD HH:MM:SS.ffffff` para timestamps. Queries SQL que usam `strftime('%Y', Data)` dependem desse formato exato.

**Mitigação**: Ao inserir no SQLite, sempre converter datas para string ISO `YYYY-MM-DD`. Verificar com `SELECT * FROM LANCAMENTOS_GERAIS LIMIT 1` que o formato está correto antes de rodar queries de pivot.

---

### RISCO-15 · Separador CSV: `;` vs `,` — BAIXO

**Descrição**: O PDW exporta CSV com separador `;` (ponto e vírgula), não `,`. Scripts externos que consomem o CSV podem quebrar se a reescrita usar `,` como padrão.

**Mitigação**: Hardcode do separador `;` na exportação CSV. Documentar no formato de saída.

---

### RISCO-16 · Ordem das linhas no banco: ordenação descendente por Data — MÉDIO

**Descrição**: `save_dataframe_to_database()` ordena o DataFrame por Data descendente antes de inserir. Reescritas que não preservarem esta ordenação produzirão bancos com linhas em ordem diferente. Queries analíticas que dependem de `ROWID` ou ordem de inserção podem retornar resultados em ordem diferente.

**Mitigação**: Aplicar `ORDER BY Data DESC` antes de qualquer bulk insert no SQLite. Alternativamente, sempre usar `ORDER BY` explícito nas queries analíticas.

---

### RISCO-17 · Tabelas hardcoded em `data_correjeitor`: schema implícito — CRÍTICO

**Descrição**: A função `data_correjeitor` assume que as tabelas `Parcelamentos`, `GUIDING` e a view `Origens` existem com estrutura específica. Em qualquer reescrita, estas dependências implícitas devem ser tornadas explícitas e verificadas na inicialização.

**Estrutura implícita assumida**:
```sql
-- GUIDING deve ter:
TABLE_NAME TEXT, ACCOUNTING TEXT, LOADABLE TEXT

-- Parcelamentos deve ter:
DATA TEXT (ou date), "Tipo Lançamento" TEXT

-- View Origens (criada pela própria função):
SELECT TABLE_NAME as nome FROM GUIDING WHERE LOADABLE = 'X'
```

---

### Tabela de Riscos Multi-Linguagem

| ID | Descrição | Linguagem mais afetada | Severidade |
|---|---|---|---|
| RISCO-11 | Inferência de tipo Excel | Java, Go, C++ | CRÍTICO |
| RISCO-12 | Células vazias vs nulas | Java, Go, Rust | ALTO |
| RISCO-13 | Encoding UTF-8 | Todas | MÉDIO |
| RISCO-14 | Formato de data no banco | Todas | ALTO |
| RISCO-15 | Separador CSV `;` | Todas | BAIXO |
| RISCO-16 | Ordenação descendente | Todas | MÉDIO |
| RISCO-17 | Schema implícito em data_correjeitor | Todas | CRÍTICO |
