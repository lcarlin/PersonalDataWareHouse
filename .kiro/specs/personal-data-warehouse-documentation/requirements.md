# Requirements Document

## Introduction

The Personal Data Warehouse (PDW) is a comprehensive ETL (Extract, Transform & Load) system designed to process financial and accounting data from Excel workbooks into a SQLite database. The system provides data validation, transformation, pivot table generation, and comprehensive reporting capabilities for personal financial management and analysis.

The system operates as a configurable data processing pipeline that can handle multiple Excel sheets containing accounting entries, transform them into normalized database tables, and generate various analytical reports in multiple formats (CSV, JSON, XML, XLSX).

## Requirements

### Requirement 1: Data Extraction and Loading

**User Story:** As a financial data analyst, I want to extract data from Excel workbooks and load it into a SQLite database, so that I can have a centralized repository for all my financial information.

#### Acceptance Criteria

1. WHEN the system processes an Excel workbook THEN it SHALL read all sheets defined in the guiding configuration table
2. WHEN a sheet is marked as "LOADABLE" in the guiding table THEN the system SHALL extract all data from that sheet
3. WHEN a sheet is marked as "ACCOUNTING" THEN the system SHALL apply financial data transformations and validations
4. WHEN the data loading process completes THEN the system SHALL create corresponding SQLite tables for each processed sheet
5. IF the database already exists and overwrite is enabled THEN the system SHALL replace existing tables with new data
6. WHEN loading accounting data THEN the system SHALL consolidate all entries into a general entries table (LANCAMENTOS_GERAIS)

### Requirement 2: Data Transformation and Validation

**User Story:** As a data quality manager, I want the system to validate and transform raw financial data, so that I can ensure data consistency and accuracy in my reports.

#### Acceptance Criteria

1. WHEN processing accounting entries THEN the system SHALL validate that required fields (Data, TIPO) are not null
2. WHEN invalid data is found AND save_discarded_data is enabled THEN the system SHALL store discarded records in a separate table
3. WHEN processing financial amounts THEN the system SHALL convert text values to numeric format and round to 2 decimal places
4. WHEN processing dates THEN the system SHALL extract and populate day of week, month, year, and year-month fields
5. WHEN processing descriptions THEN the system SHALL normalize text by replacing special characters and removing extra spaces
6. WHEN data transformation completes THEN the system SHALL sort records by date in descending order

### Requirement 3: Configuration Management

**User Story:** As a system administrator, I want to configure the system behavior through external configuration files, so that I can customize processing without modifying code.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL read configuration from PersonalDataWareHouse.cfg file
2. WHEN a custom configuration file is provided as parameter THEN the system SHALL use that file instead of the default
3. WHEN configuration version doesn't match system version THEN the system SHALL terminate with an error message
4. WHEN required directories don't exist THEN the system SHALL terminate with appropriate error messages
5. WHEN configuration parameters are invalid THEN the system SHALL provide clear error messages
6. WHEN the system runs THEN it SHALL validate all file paths and directory structures before processing

### Requirement 4: Pivot Table Generation

**User Story:** As a financial analyst, I want the system to generate pivot tables from my accounting data, so that I can analyze trends and patterns over time.

#### Acceptance Criteria

1. WHEN pivot table creation is enabled THEN the system SHALL generate monthly summary pivot tables
2. WHEN creating monthly pivots THEN the system SHALL aggregate debits by transaction type and year-month
3. WHEN creating annual pivots THEN the system SHALL aggregate debits by transaction type and year
4. WHEN generating pivot tables THEN the system SHALL create both sum and count aggregations
5. WHEN pivot tables are created THEN the system SHALL use transaction types from the types configuration table
6. WHEN pivot generation completes THEN the system SHALL store results in designated history tables

### Requirement 5: Dynamic Reporting

**User Story:** As a business user, I want to generate dynamic reports based on configurable templates, so that I can create custom analytical views of my data.

#### Acceptance Criteria

1. WHEN dynamic reporting is enabled THEN the system SHALL read report definitions from the guiding sheet
2. WHEN processing dynamic reports THEN the system SHALL create individual tables for each report configuration
3. WHEN building dynamic reports THEN the system SHALL aggregate specified columns from pivot tables
4. WHEN dynamic report generation completes THEN the system SHALL store results in designated report tables
5. IF report configuration is invalid THEN the system SHALL log appropriate error messages

### Requirement 6: File Export and Reporting

**User Story:** As an end user, I want to export processed data in multiple formats, so that I can use the information in other applications and share reports.

#### Acceptance Criteria

1. WHEN export is enabled THEN the system SHALL generate CSV files with semicolon separators
2. WHEN other file types are enabled THEN the system SHALL generate JSON and XML exports
3. WHEN exporting large files THEN the system SHALL compress JSON and XML files using gzip
4. WHEN generating Excel reports THEN the system SHALL create comprehensive workbooks with multiple sheets
5. WHEN exporting data THEN the system SHALL format dates and numbers according to locale conventions
6. WHEN export completes THEN the system SHALL report the number of records exported

### Requirement 7: Monthly and Payment Summaries

**User Story:** As a financial manager, I want to generate monthly summaries and payment installment reports, so that I can track financial performance and payment schedules.

#### Acceptance Criteria

1. WHEN monthly summaries are enabled THEN the system SHALL aggregate credits and debits by month and data source
2. WHEN generating monthly summaries THEN the system SHALL calculate net position (credits minus debits)
3. WHEN processing installment payments THEN the system SHALL create payment schedule summaries
4. WHEN generating payment summaries THEN the system SHALL calculate month-over-month differences
5. WHEN summary generation completes THEN the system SHALL store results in designated summary tables

### Requirement 8: Logging and Monitoring

**User Story:** As a system operator, I want comprehensive logging of system operations, so that I can monitor performance and troubleshoot issues.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL create or append to a log file
2. WHEN processing completes THEN the system SHALL log start time, end time, and total execution duration
3. WHEN logging system information THEN it SHALL include version, hostname, and operating system
4. WHEN errors occur THEN the system SHALL log detailed error information
5. WHEN the system runs THEN it SHALL display progress information with color-coded output
6. WHEN processing steps complete THEN the system SHALL log the number of records processed

### Requirement 9: Database Operations

**User Story:** As a database administrator, I want the system to manage database operations efficiently, so that I can ensure data integrity and optimal performance.

#### Acceptance Criteria

1. WHEN connecting to the database THEN the system SHALL use SQLite3 with appropriate connection parameters
2. WHEN creating tables THEN the system SHALL drop existing tables if overwrite is enabled
3. WHEN processing completes THEN the system SHALL commit all transactions to ensure data persistence
4. WHEN creating indexes THEN the system SHALL optimize query performance for common access patterns
5. WHEN managing database views THEN the system SHALL create views for data source management
6. WHEN database operations fail THEN the system SHALL provide clear error messages and rollback transactions

### Requirement 10: Error Handling and Recovery

**User Story:** As a system user, I want robust error handling and recovery mechanisms, so that I can identify and resolve issues quickly.

#### Acceptance Criteria

1. WHEN file operations fail THEN the system SHALL provide specific error messages about missing files or directories
2. WHEN configuration errors occur THEN the system SHALL terminate gracefully with descriptive error messages
3. WHEN data validation fails THEN the system SHALL continue processing valid records and report invalid ones
4. WHEN database operations fail THEN the system SHALL rollback transactions and report the error
5. WHEN Excel file reading fails THEN the system SHALL report specific sheet or file access issues
6. WHEN the system encounters unexpected errors THEN it SHALL log the error and exit with appropriate status codes