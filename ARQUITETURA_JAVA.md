# ARQUITETURA_JAVA.md
## Personal Data Warehouse — Guia de Reimplementação em Java/Spring Batch
### Versão 10.1.0 → Java 21 + Spring Batch 5.x

---

## 1. Visão Geral da Tradução Arquitetural

O PDW é um sistema **batch ETL single-user**. A tradução mais direta para Java é **Spring Batch**, que implementa nativamente os conceitos de Job → Step → Reader/Processor/Writer que o PDW implementa manualmente.

### Mapeamento Conceitual

| Conceito PDW (Python) | Conceito Java (Spring Batch) |
|---|---|
| `run_pipeline()` | `Job` com vários `Step`s |
| `load_config()` | `@ConfigurationProperties` + `application.properties` |
| `new_data_loader()` | `Step` com `ItemReader` (Excel) + `ItemProcessor` + `ItemWriter` (JDBC) |
| `sanitize_entries_dataframe()` | `ItemProcessor<ExcelRow, LancamentoEntity>` |
| `create_pivot_history()` | `Step` com `JdbcBatchItemWriter` ou `@Query` nativa |
| `xlsx_report_generator()` | `Step` com `FlatFileItemWriter` ou Apache POI writer |
| `general_entries_file_exportator()` | `Step` com writers para CSV/JSON/XML |
| `pd.DataFrame` | `List<LancamentoEntity>` ou Tablesaw `Table` |
| SQLite (via sqlite3 stdlib) | SQLite via JDBC (`org.xerial:sqlite-jdbc`) |
| `.cfg` (INI format) | `application.properties` / `application.yml` |
| `PDW_QUERIES.yaml` | SQL em arquivo `.sql` ou `@Query` annotations |

---

## 2. Estrutura de Projeto Java Recomendada

```
pdw-java/
├── pom.xml                              ← dependências Maven
├── src/
│   └── main/
│       ├── java/
│       │   └── com/pdw/
│       │       ├── PdwApplication.java          ← @SpringBootApplication + main()
│       │       │
│       │       ├── config/
│       │       │   ├── PdwProperties.java        ← @ConfigurationProperties
│       │       │   └── BatchConfig.java          ← definição dos Jobs e Steps
│       │       │
│       │       ├── domain/
│       │       │   ├── Lancamento.java           ← entidade principal
│       │       │   ├── Tipo.java                 ← tipos de lançamento
│       │       │   ├── Parcelamento.java         ← parcelamentos
│       │       │   └── GuidingRow.java           ← linha da aba GUIDING
│       │       │
│       │       ├── etl/
│       │       │   ├── ExcelReader.java          ← lê Excel com Apache POI
│       │       │   ├── LancamentoProcessor.java  ← sanitização (= sanitizer.py)
│       │       │   └── JdbcLancamentoWriter.java ← salva no SQLite
│       │       │
│       │       ├── analytics/
│       │       │   ├── PivotTableBuilder.java    ← = pivot.py
│       │       │   └── TotalsCalculator.java     ← = totals.py
│       │       │
│       │       ├── reports/
│       │       │   ├── ExcelReportWriter.java    ← = xlsx_generator.py (Apache POI)
│       │       │   ├── CsvExporter.java          ← = exporter.py (CSV)
│       │       │   ├── JsonExporter.java         ← = exporter.py (JSON)
│       │       │   └── XmlExporter.java          ← = exporter.py (XML)
│       │       │
│       │       └── infrastructure/
│       │           ├── PdwLogger.java            ← = infrastructure/logging.py
│       │           └── SqliteConfig.java         ← datasource SQLite
│       │
│       └── resources/
│           ├── application.properties            ← = PersonalDataWareHouse.cfg
│           └── queries/
│               └── pdw-queries.sql               ← = PDW_QUERIES.yaml
```

---

## 3. `pom.xml` — Dependências Maven

```xml
<project>
    <groupId>com.pdw</groupId>
    <artifactId>personal-data-warehouse</artifactId>
    <version>10.1.0</version>
    <packaging>jar</packaging>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.3.0</version>
    </parent>

    <properties>
        <java.version>21</java.version>
    </properties>

    <dependencies>
        <!-- Spring Batch -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-batch</artifactId>
        </dependency>

        <!-- SQLite JDBC -->
        <dependency>
            <groupId>org.xerial</groupId>
            <artifactId>sqlite-jdbc</artifactId>
            <version>3.45.1.0</version>
        </dependency>

        <!-- Apache POI (Excel) -->
        <dependency>
            <groupId>org.apache.poi</groupId>
            <artifactId>poi-ooxml</artifactId>
            <version>5.2.5</version>
        </dependency>

        <!-- SnakeYAML (queries YAML) -->
        <dependency>
            <groupId>org.yaml</groupId>
            <artifactId>snakeyaml</artifactId>
        </dependency>

        <!-- Jackson (JSON export) -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
        </dependency>

        <!-- Lombok (opcional — reduz boilerplate) -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>

        <!-- Testes -->
        <dependency>
            <groupId>org.springframework.batch</groupId>
            <artifactId>spring-batch-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.assertj</groupId>
            <artifactId>assertj-core</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

---

## 4. Entidade Principal: `Lancamento.java`

```java
package com.pdw.domain;

import java.time.LocalDate;

public record Lancamento(
    LocalDate data,
    String tipo,
    String descricao,
    double credito,
    double debito,
    String origem,   // = coluna TRANSIENT_DATA_COLUMN do .cfg (ex: "Origem")
    String mes,      // nome PT-BR do mês
    String diaSemana // nome PT-BR do dia da semana
) {}
```

---

## 5. Configuração: `application.properties`

```properties
# Equivalentes do PersonalDataWareHouse.cfg

# [DIRECTORIES]
pdw.dir.in=/home/user/pdw/input/
pdw.dir.out=/home/user/pdw/output/
pdw.dir.db=/home/user/pdw/db/
pdw.dir.log=/home/user/pdw/logs/

# [FILE_TYPES]
pdw.file.input=PDW
pdw.file.input.type=xlsx
pdw.file.output=PDW_REPORTS.v2
pdw.file.db=PDW
pdw.file.db.type=db
pdw.file.log=PDW.log
pdw.file.queries=pdw-queries.yml

# [SETTINGS]
pdw.version=10.1.0
pdw.settings.run-loader=false
pdw.settings.run-reports=true
pdw.settings.overwrite-db=true
pdw.settings.create-pivot=true
pdw.settings.export-other-types=false
pdw.settings.guiding-table=GUIDING
pdw.settings.types-table=TiposLancamentos
pdw.settings.entries-table=LANCAMENTOS_GERAIS
pdw.settings.split-table=PARCELAMENTOS
pdw.settings.origin-column=Origem

# Spring Batch (desabilita criação automática de tabelas de metadados)
spring.batch.jdbc.initialize-schema=never
```

---

## 6. Configuração do Job: `BatchConfig.java`

```java
@Configuration
@EnableBatchProcessing
public class BatchConfig {

    @Autowired PdwProperties props;
    @Autowired DataSource dataSource;

    @Bean
    public Job pdwJob(JobRepository jobRepository,
                      Step loaderStep,
                      Step pivotStep,
                      Step reportsStep) {
        return new JobBuilder("pdwJob", jobRepository)
            .start(loaderStep)              // = new_data_loader()
            .next(pivotStep)               // = create_pivot_history()
            .next(reportsStep)             // = xlsx_report_generator() + exporter()
            .build();
    }

    @Bean
    @ConditionalOnProperty(name = "pdw.settings.run-loader", havingValue = "true")
    public Step loaderStep(JobRepository repo, PlatformTransactionManager txm,
                           ExcelReader reader,
                           LancamentoProcessor processor,
                           JdbcLancamentoWriter writer) {
        return new StepBuilder("loaderStep", repo)
            .<ExcelRow, Lancamento>chunk(500, txm)  // chunk de 500 linhas
            .reader(reader)
            .processor(processor)
            .writer(writer)
            .build();
    }
}
```

---

## 7. Reader Excel: `ExcelReader.java`

```java
@Component
public class ExcelReader implements ItemReader<ExcelRow> {

    private final List<ExcelRow> rows = new ArrayList<>();
    private int currentIndex = 0;

    @PostConstruct
    public void load() throws IOException {
        // Equivalente de new_data_loader() + read_guiding_sheet()
        try (Workbook wb = WorkbookFactory.create(new File(props.getInputFile()))) {
            Sheet guiding = wb.getSheet(props.getGuidingTable());
            for (Row row : guiding) {
                String tableName  = row.getCell(0).getStringCellValue();
                String accounting = row.getCell(1).getStringCellValue();
                String loadable   = row.getCell(2).getStringCellValue();

                if ("X".equals(loadable) && "X".equals(accounting)) {
                    Sheet sheet = wb.getSheet(tableName);
                    for (Row dataRow : sheet) {
                        rows.add(ExcelRow.fromRow(dataRow, tableName));
                    }
                }
            }
        }
    }

    @Override
    public ExcelRow read() {
        return currentIndex < rows.size() ? rows.get(currentIndex++) : null;
    }
}
```

---

## 8. Processor (Sanitização): `LancamentoProcessor.java`

```java
@Component
public class LancamentoProcessor implements ItemProcessor<ExcelRow, Lancamento> {

    private static final Map<Integer, String> MES_PT_BR = Map.of(
        1, "Janeiro", 2, "Fevereiro", 3, "Março", 4, "Abril",
        5, "Maio", 6, "Junho", 7, "Julho", 8, "Agosto",
        9, "Setembro", 10, "Outubro", 11, "Novembro", 12, "Dezembro"
    );

    private static final Map<DayOfWeek, String> DIA_SEMANA = Map.of(
        DayOfWeek.MONDAY, "Segunda-Feira",
        DayOfWeek.TUESDAY, "Terca-Feira",
        // ...
    );

    @Override
    public Lancamento process(ExcelRow row) {
        if (row.tipo() == null || row.data() == null) return null; // filtra nulos

        String descLimpa = row.descricao()
            .replaceAll("[;,]", "|")
            .replace("∴", " .'. ")
            .replace("ś", "s")
            .replace("\"", "")
            .strip();

        LocalDate data = row.data().toLocalDate();
        String mes = MES_PT_BR.get(data.getMonthValue());
        String diaSemana = DIA_SEMANA.get(data.getDayOfWeek());

        return new Lancamento(
            data,
            row.tipo(),
            descLimpa,
            row.credito() != null ? row.credito() : 0.0,
            row.debito()  != null ? row.debito()  : 0.0,
            row.origem(),
            mes,
            diaSemana
        );
    }
}
```

---

## 9. Writer SQLite: `JdbcLancamentoWriter.java`

```java
@Component
public class JdbcLancamentoWriter implements ItemWriter<Lancamento> {

    @Autowired JdbcTemplate jdbcTemplate;

    private static final String INSERT_SQL = """
        INSERT INTO LANCAMENTOS_GERAIS
            (Data, TIPO, DESCRICAO, Credito, Debito, Origem, Mes, DiaSemana)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """;

    @Override
    public void write(Chunk<? extends Lancamento> chunk) {
        jdbcTemplate.batchUpdate(INSERT_SQL,
            chunk.getItems(),
            chunk.getItems().size(),
            (ps, l) -> {
                ps.setDate(1, Date.valueOf(l.data()));
                ps.setString(2, l.tipo());
                ps.setString(3, l.descricao());
                ps.setDouble(4, l.credito());
                ps.setDouble(5, l.debito());
                ps.setString(6, l.origem());
                ps.setString(7, l.mes());
                ps.setString(8, l.diaSemana());
            }
        );
    }
}
```

---

## 10. DataSource SQLite: `SqliteConfig.java`

```java
@Configuration
public class SqliteConfig {

    @Value("${pdw.dir.db}${pdw.file.db}.${pdw.file.db.type}")
    private String dbPath;

    @Bean
    @Primary
    public DataSource sqliteDataSource() {
        SQLiteDataSource ds = new SQLiteDataSource();
        ds.setUrl("jdbc:sqlite:" + dbPath);
        return ds;
    }

    // Spring Batch precisa de seu próprio datasource para metadados
    // Use H2 em memória para metadados do Batch:
    @Bean
    @BatchDataSource
    public DataSource batchMetadataDataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript(new ClassPathResource("org/springframework/batch/core/schema-h2.sql"))
            .build();
    }
}
```

---

## 11. Geração de Relatório Excel: `ExcelReportWriter.java`

```java
@Component
public class ExcelReportWriter {

    public void write(Map<String, List<Map<String, Object>>> queryResults,
                      String outputPath) throws IOException {
        try (Workbook wb = new XSSFWorkbook()) {
            for (Map.Entry<String, List<Map<String, Object>>> entry : queryResults.entrySet()) {
                Sheet sheet = wb.createSheet(entry.getKey());
                List<Map<String, Object>> rows = entry.getValue();
                if (rows.isEmpty()) continue;

                // Cabeçalho
                Row header = sheet.createRow(0);
                List<String> cols = new ArrayList<>(rows.get(0).keySet());
                for (int i = 0; i < cols.size(); i++) {
                    header.createCell(i).setCellValue(cols.get(i));
                }

                // Dados
                for (int r = 0; r < rows.size(); r++) {
                    Row row = sheet.createRow(r + 1);
                    for (int c = 0; c < cols.size(); c++) {
                        Object val = rows.get(r).get(cols.get(c));
                        setCellValue(row.createCell(c), val);
                    }
                }
            }
            try (FileOutputStream fos = new FileOutputStream(outputPath)) {
                wb.write(fos);
            }
        }
    }

    private void setCellValue(Cell cell, Object value) {
        if (value instanceof Number n) cell.setCellValue(n.doubleValue());
        else if (value instanceof Boolean b) cell.setCellValue(b);
        else if (value != null) cell.setCellValue(value.toString());
    }
}
```

---

## 12. Sistema de Log Java

```java
@Component
public class PdwLogger {

    private final Path logPath;

    public PdwLogger(@Value("${pdw.dir.log}${pdw.file.log}") String logPath) {
        this.logPath = Path.of(logPath);
    }

    public LogContext open() throws IOException {
        long lineCount = 0;
        String lastRun = "none";

        if (Files.exists(logPath) && Files.size(logPath) > 0) {
            List<String> lines = Files.readAllLines(logPath);
            lineCount = lines.size();
            if (!lines.isEmpty()) {
                lastRun = lines.get(lines.size() - 1).split("\\|")[0].strip();
            }
        } else {
            Files.writeString(logPath,
                "New LOG created at :-> " +
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss")) + "\n",
                StandardOpenOption.CREATE);
        }
        return new LogContext(lineCount, lastRun, Instant.now());
    }

    public void finalize(LogContext ctx, String version, String host, String os) throws IOException {
        double elapsed = Duration.between(ctx.startTime(), Instant.now()).toMillis() / 1000.0;
        String line = String.format("%s | Version: %s | Host: %s | OS: %s | Runs: %d | Time: %.2fs | Last: %s%n",
            LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy/MM/dd HH:mm:ss")),
            version, host, os, ctx.lineCount(), elapsed, ctx.lastRun());
        Files.writeString(logPath, line, StandardOpenOption.APPEND);
    }

    public record LogContext(long lineCount, String lastRun, Instant startTime) {}
}
```

---

## 13. Execução via CLI

```java
@SpringBootApplication
public class PdwApplication implements CommandLineRunner {

    @Autowired JobLauncher jobLauncher;
    @Autowired Job pdwJob;

    public static void main(String[] args) {
        SpringApplication.run(PdwApplication.class, args);
    }

    @Override
    public void run(String... args) throws Exception {
        String configFile = args.length > 0 ? args[0] : "";
        JobParameters params = new JobParametersBuilder()
            .addString("configFile", configFile)
            .addLong("timestamp", System.currentTimeMillis())  // garante unicidade
            .toJobParameters();
        jobLauncher.run(pdwJob, params);
    }
}
```

```bash
# Equivalente de: python PersonalDataWareHouse.py
java -jar pdw.jar

# Com config customizado: python PersonalDataWareHouse.py /path/to/custom.cfg
java -jar pdw.jar /path/to/custom.cfg

# Modo batch com Spring profiles
java -jar pdw.jar --spring.profiles.active=loader-only
```

---

## 14. Diferenças Críticas Python → Java

| Aspecto | Python (PDW) | Java (Reescrita) |
|---|---|---|
| Schema inference | `pandas` infere tipos do Excel automaticamente | Apache POI requer tratamento explícito de tipo por célula |
| NULL handling | `pd.isna()` / `np.nan` | `null` Java — verificação explícita em cada campo |
| Date parsing | `pandas` converte automaticamente | POI retorna `LocalDateTime`; tratar datas serial |
| String ops | Vectorized (`str.replace`) sobre colunas | Loop sobre lista ou Streams |
| SQL injection | Concatenação em `data_correjeitor` | PreparedStatement obrigatório |
| Pivot tables | `pd.pivot_table()` | SQL GROUP BY ou Tablesaw `summarize()` |
| Concorrência | Desabilitada (exit(1) se MULTITHREADING=True) | Spring Batch suporta partitioning — não usar |
| Saída XML | `xml.etree.ElementTree` | JAXB ou `javax.xml.stream` |
| Saída JSON.gz | pandas + gzip stdlib | Jackson + `GZIPOutputStream` |

---

## 15. Checklist de Paridade Funcional

```
[ ] read_guiding_sheet   → ExcelReader lê aba GUIDING com colunas TABLE_NAME/ACCOUNTING/LOADABLE
[ ] process_accounting_sheet  → ExcelReader extrai Data/TIPO/DESCRICAO/Credito/Debito + Origem
[ ] sanitize_entries_dataframe → LancamentoProcessor aplica todas as 7 transformações
[ ] data_correjeitor     → SQL post-load: UPDATE tipos, criar view Origens
[ ] save_dataframe       → JdbcLancamentoWriter com batchUpdate ordenado por data desc
[ ] create_pivot_history → SQL GROUP BY ano/mês salvos em HistoricoGeral + HistoricoAnual
[ ] monthly_summaries    → SQL SELECT com SUM(Credito), SUM(Debito) por mês
[ ] split_paymnt_resume  → SQL SELECT de PARCELAMENTOS + calcula resumo
[ ] general_entries_file_exportator → CSV (;) + JSON.gz + XML.gz
[ ] xlsx_report_generator → lê YAML, executa queries, escreve abas Excel
[ ] Log format           → idêntico ao formato pipe-delimitado do Python
[ ] Config validation    → versão em application.properties === versão do artefato
[ ] exit(1) behavior     → System.exit(1) nos mesmos pontos de falha
```
