# MATRIZ_COMPARATIVA_FLASK_VS_JAVA.md
## Personal Data Warehouse — Matriz Comparativa: Python Batch vs. Alternativas de Reescrita
### Versão 10.1.0

> **Contexto**: O PDW é um sistema **batch CLI**, não uma aplicação web/Flask.
> Este documento compara a implementação Python atual com implementações equivalentes
> em Java, Rust, Go, Node.js e C++ para auxiliar na decisão de reescrita.

---

## 1. Matriz de Comparação Principal

| Critério | Python 3.9+ (atual) | Java 21 + Spring Batch | Rust + Tokio | Go 1.22 | Node.js 20 + TypeScript | C++ 20 |
|---|---|---|---|---|---|---|
| **Curva de aprendizado** | Baixa | Média-Alta | Alta | Média | Média | Alta |
| **Tamanho do código** | 1x (base) | ~3x | ~2x | ~2x | ~2x | ~4x |
| **Performance ETL** | Média | Alta | Muito Alta | Alta | Média | Muito Alta |
| **Ecossistema batch** | Bom (pandas) | Excelente (Spring Batch) | Limitado | Bom | Limitado | Limitado |
| **Leitura Excel** | Nativa (openpyxl) | Apache POI (verboso) | calamine (bom) | excelize (bom) | SheetJS (bom) | xlnt (bom) |
| **Escrita Excel** | xlsxwriter (simples) | Apache POI (verboso) | rust_xlsxwriter | excelize | exceljs | libxlsxwriter |
| **SQLite** | stdlib (sqlite3) | JDBC (xerial) | rusqlite | go-sqlite3 | better-sqlite3 | SQLiteCpp |
| **DataFrame/pivot** | pandas (excelente) | Tablesaw / custom SQL | Polars (excelente) | gota (limitado) | danfojs (limitado) | xtensor (baixo nível) |
| **Maturidade da stack** | Alta | Muito Alta | Crescente | Alta | Alta | Alta |
| **Deploy** | pip + venv | JAR standalone | Binário estático | Binário estático | node_modules (pesado) | Binário estático |
| **Manutenibilidade** | Alta | Média (verbose) | Média (borrow checker) | Alta | Média | Baixa |
| **Tipo de erro mais comum** | Runtime (duck typing) | Compile-time | Compile-time (strict) | Compile-time | Compile-time (TS) | Compile-time + UB |
| **Tempo de startup** | ~1-2s (imports) | ~3-5s (JVM) | ~0.01s | ~0.01s | ~0.5s | ~0.01s |
| **Consumo de memória** | Médio (pandas) | Médio-alto (JVM heap) | Baixo | Baixo | Médio | Baixo |

---

## 2. Análise por Componente

### 2.1 Leitura de Configuração (.cfg / INI)

| Linguagem | Solução | Equivalência ao configparser | Notas |
|---|---|---|---|
| Python (atual) | `configparser` (stdlib) | — | Leitura direta, tipo bool via `getboolean` |
| Java | `java.util.Properties` / `@ConfigurationProperties` | Alta | Spring Boot faz parsing automático para POJOs |
| Rust | `config-rs` crate | Alta | Suporta INI, TOML, YAML, env vars |
| Go | `viper` | Alta | Unifica configuração de múltiplas fontes |
| Node.js | `dotenv` + `config` npm | Média | Converte para JS object |
| C++ | `libconfig` | Alta | Parse de INI/libconfig format |

**Recomendação**: Para paridade funcional exata (INI format), Java com `@ConfigurationProperties` ou Go com `viper` são as melhores opções.

---

### 2.2 Leitura de Excel

| Linguagem | Biblioteca | Detecta tipo automático? | Suporta .xls e .xlsx? | Memória para 50k linhas |
|---|---|---|---|---|
| Python (atual) | pandas + openpyxl | Sim (inferência) | Sim (openpyxl + xlrd) | ~50MB |
| Java | Apache POI | Não (por célula) | Sim (HSSF + XSSF) | ~80MB |
| Rust | calamine | Sim | Sim | ~20MB |
| Go | excelize | Não | .xlsx apenas | ~40MB |
| Node.js | SheetJS (xlsx) | Sim | Sim | ~60MB |
| C++ | xlnt | Não | .xlsx apenas | ~30MB |

**Maior pegadinha**: Apache POI requer verificação de tipo por célula (STRING vs NUMERIC vs DATE). O pandas faz isso automaticamente.

```java
// Java — verificação manual de tipo
switch (cell.getCellType()) {
    case NUMERIC:
        if (DateUtil.isCellDateFormatted(cell))
            return cell.getLocalDateTimeCellValue().toLocalDate();
        return cell.getNumericCellValue();
    case STRING:
        return cell.getStringCellValue();
    case BLANK:
        return null;
}
```

```python
# Python — pandas faz isso automaticamente
df = pd.read_excel(file, sheet_name=sheet)
```

---

### 2.3 Transformação de Dados (= `sanitize_entries_dataframe`)

| Linguagem | Paradigma | Verbosidade | Performance |
|---|---|---|---|
| Python (atual) | Operações vetorizadas (pandas) | Baixa | Média (GIL, overhead pandas) |
| Java | Streams / loop imperativo | Alta | Alta (JIT) |
| Rust | Iterators + Polars | Média | Muito Alta |
| Go | Loop imperativo | Média | Alta |
| Node.js | Array methods / danfojs | Média | Média |
| C++ | Loop + STL | Alta | Muito Alta |

**Exemplo — limpar DESCRICAO em cada linguagem**:

```python
# Python (atual) — 1 linha
df['DESCRICAO'] = df['DESCRICAO'].str.replace(r"[;,]", "|", regex=True).str.strip()
```

```java
// Java — explícito mas claro
entries.stream()
    .map(e -> e.withDescricao(
        e.descricao().replaceAll("[;,]", "|").strip()
    ))
    .collect(Collectors.toList());
```

```rust
// Rust — Polars
df.lazy()
    .with_column(col("DESCRICAO").str().replace_all(lit("[;,]"), lit("|"), true))
    .collect()?
```

```go
// Go — loop imperativo
for i := range entries {
    entries[i].Descricao = strings.TrimSpace(
        regexp.MustCompile(`[;,]`).ReplaceAllString(entries[i].Descricao, "|"),
    )
}
```

---

### 2.4 SQLite

| Linguagem | Biblioteca | Connection pooling? | Prepared statements? | Async? |
|---|---|---|---|---|
| Python (atual) | `sqlite3` (stdlib) | Não (conn-per-function) | Sim (?) | Não |
| Java | xerial JDBC | Sim (HikariCP) | Sim | Não (JDBC é sync) |
| Rust | rusqlite | Não nativo | Sim | Sim (tokio-rusqlite) |
| Go | mattn/go-sqlite3 | Sim (database/sql) | Sim | Sim (goroutines) |
| Node.js | better-sqlite3 | Não | Sim | Não (sync API) |
| C++ | SQLiteCpp | Não | Sim | Não |

---

### 2.5 Geração de Relatórios Excel

| Linguagem | Biblioteca | Formatação de células? | Charts? | Simplicidade |
|---|---|---|---|---|
| Python (atual) | xlsxwriter | Sim | Sim | Alta |
| Java | Apache POI XSSF | Sim | Sim | Baixa (verboso) |
| Rust | rust_xlsxwriter | Sim | Não | Média |
| Go | excelize | Sim | Sim | Média |
| Node.js | exceljs | Sim | Sim | Alta |
| C++ | libxlsxwriter | Sim | Não | Baixa |

---

### 2.6 Parsing de YAML (queries SQL)

| Linguagem | Biblioteca | Equivalência | Notas |
|---|---|---|---|
| Python (atual) | `pyyaml` (`yaml.safe_load`) | — | Simples dict de string→string |
| Java | `snakeyaml` | Alta | Mapeia para `Map<String, QueryConfig>` |
| Rust | `serde_yaml` | Alta | Deserializa para struct tipada |
| Go | `gopkg.in/yaml.v3` | Alta | Mapeia para `map[string]QueryConfig` |
| Node.js | `js-yaml` | Alta | Parse para objeto JS |
| C++ | `yaml-cpp` | Alta | Parse para `YAML::Node` |

---

## 3. Recomendação por Caso de Uso

### 3.1 Caso: Máxima paridade funcional com mínimo esforço

**Recomendação: Java + Spring Batch**

- Ecossistema batch mais maduro
- Spring Batch implementa nativamente job/step/retry/skip
- Apache POI para Excel (API verbosa mas completa)
- `sqlite-jdbc` drop-in para SQLite
- Maior time de desenvolvimento Java disponível no mercado

**Trade-off**: Tempo de startup (~3-5s), verbosidade, JVM overhead.

---

### 3.2 Caso: Performance máxima (arquivos Excel grandes, >100k linhas)

**Recomendação: Rust + Polars**

- Polars é significativamente mais rápido que pandas para operações vetorizadas
- Binário estático, zero overhead de runtime
- Sem GIL — paralelismo real disponível

**Trade-off**: Curva de aprendizado do borrow checker, ecossistema batch menos maduro.

---

### 3.3 Caso: Simplicidade de deploy (single binary, sem runtime)

**Recomendação: Go**

- Binário único sem dependências externas
- `excelize` tem boa paridade com openpyxl/xlsxwriter
- `go-sqlite3` é maduro
- Código Go é simples de manter

**Trade-off**: `gota` para DataFrames é limitado — pivot tables precisam ser implementadas manualmente via SQL.

---

### 3.4 Caso: Reutilizar conhecimento existente da equipe (JavaScript/TypeScript)

**Recomendação: Node.js + TypeScript**

- SheetJS para Excel tem boa cobertura
- `better-sqlite3` é síncrono e simples (equivalente ao Python `sqlite3`)
- TypeScript dá type safety

**Trade-off**: `danfojs` é menos maduro que pandas; `node_modules` pesado para deploy.

---

## 4. Comparação de Linhas de Código Estimadas

| Componente | Python (atual) | Java | Rust | Go | Node.js |
|---|---|---|---|---|---|
| Config loader | ~50 linhas | ~80 linhas | ~60 linhas | ~70 linhas | ~50 linhas |
| ETL (loader + sanitizer) | ~180 linhas | ~400 linhas | ~250 linhas | ~280 linhas | ~220 linhas |
| Database operations | ~40 linhas | ~100 linhas | ~80 linhas | ~80 linhas | ~60 linhas |
| Analytics (pivot + totals) | ~150 linhas | ~300 linhas | ~200 linhas | ~200 linhas | ~180 linhas |
| Reports (xlsx + exporter) | ~200 linhas | ~450 linhas | ~300 linhas | ~350 linhas | ~250 linhas |
| Log + orchestrator | ~120 linhas | ~200 linhas | ~150 linhas | ~150 linhas | ~130 linhas |
| **Total estimado** | **~740 linhas** | **~1.530 linhas** | **~1.040 linhas** | **~1.130 linhas** | **~890 linhas** |

---

## 5. Tempo de Execução Estimado por Linguagem

Para um arquivo PDW.xlsx típico (~5.000 lançamentos, 20 abas):

| Fase | Python (atual) | Java | Rust | Go | Node.js |
|---|---|---|---|---|---|
| Config + Log | ~0.1s | ~0.2s | ~0.01s | ~0.01s | ~0.2s |
| ETL (leitura + carga) | ~8s | ~5s | ~1s | ~3s | ~6s |
| Pivot + analytics | ~5s | ~3s | ~0.5s | ~2s | ~4s |
| Geração de relatórios | ~10s | ~8s | ~3s | ~5s | ~9s |
| **Total estimado** | **~23s** | **~16s** | **~5s** | **~10s** | **~19s** |

*Valores estimados. Variam com hardware e tamanho dos dados.*

---

## 6. Custo de Migração

| Aspecto | Java | Rust | Go | Node.js |
|---|---|---|---|---|
| Risco de regressão funcional | Médio | Alto | Médio | Médio |
| Esforço para paridade de pivot tables | Médio (SQL nativo) | Baixo (Polars) | Alto (manual) | Alto (danfojs limitado) |
| Curva da equipe | Baixa-Média | Alta | Média | Baixa-Média |
| Manutenção de longo prazo | Alta | Média | Alta | Média |

---

## 7. Decisão Recomendada

```
┌─────────────────────────────────────────────────────────────┐
│  RECOMENDAÇÃO PARA REESCRITA DO PDW                         │
│                                                             │
│  1. Se o objetivo é MANUTENIBILIDADE → Java + Spring Batch  │
│  2. Se o objetivo é PERFORMANCE      → Rust + Polars        │
│  3. Se o objetivo é SIMPLICIDADE     → Go                   │
│  4. Se o objetivo é AGILIDADE        → Node.js + TypeScript │
│                                                             │
│  Para uso pessoal (escopo do PDW):                          │
│  → Go oferece o melhor equilíbrio: binário único,           │
│    código simples, performance adequada.                    │
└─────────────────────────────────────────────────────────────┘
```
