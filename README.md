# CRM Contacts API - Performance Benchmarking Project

> **Branch: `optimize_index_trgm`** - This branch implements **pg_trgm Optimization** strategy with query cancellation token support for improved database query performance.

A high-performance Django REST API for managing customer contacts with comprehensive benchmarking tools to measure and optimize database query performance. This branch focuses on PostgreSQL trigram (pg_trgm) extension for advanced text search capabilities and includes query cancellation token support for better handling of long-running queries.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Data Models](#data-models)
- [API Endpoints](#api-endpoints)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Benchmarking](#benchmarking)
- [Optimization Strategies](#optimization-strategies)
- [Performance Testing](#performance-testing)

## 🎯 Overview

This project is a Django-based CRM system designed to handle large-scale contact management with a focus on performance optimization. 

**This branch (`optimize_index_trgm`) implements pg_trgm Optimization** - a strategy that uses PostgreSQL's trigram extension for advanced text search capabilities, providing significant performance improvements for text-based queries. This branch also includes **query cancellation token support** for better handling of long-running queries. This is one of three optimization approaches being tested:

1. **Baseline (No Optimization)** - Standard Django ORM queries without additional optimizations
2. **Index Optimization** - Strategic database indexes on frequently queried fields
3. **pg_trgm Optimization** ⭐ **(This Branch)** - PostgreSQL trigram extension for advanced text search capabilities with query cancellation support

The system can handle millions of records and provides detailed performance metrics, charts, and reports to analyze query performance improvements achieved through trigram indexing and text search optimization.

## ✨ Features

- **RESTful API** with Django REST Framework
- **Advanced Filtering** - Filter by any field from AppUser, Address, or CustomerRelationship
- **Flexible Sorting** - Single and multi-field sorting support
- **Pagination** - Efficient pagination for large datasets
- **Search Functionality** - Full-text search across multiple fields with pg_trgm optimization
- **Query Cancellation Tokens** ⭐ - Support for cancelling long-running queries via `_cancel` parameter
- **Query Timeout Management** - Automatic timeout handling for database queries
- **Performance Benchmarking** - Comprehensive benchmarking suite with:
  - Execution time measurement
  - Query count tracking
  - Visual charts and graphs
  - CSV/JSON export capabilities
  - Pagination performance analysis
- **Data Generation** - Command to generate millions of test records
- **Optimization Testing** - Compare different optimization strategies

## 📁 Project Structure

```
helloagain-1/
├── contacts/                    # Main contacts app
│   ├── models.py               # Data models (AppUser, Address, CustomerRelationship)
│   ├── views.py                # API views and ViewSet
│   ├── serializers.py          # DRF serializers
│   ├── urls.py                 # URL routing
│   ├── benchmarks.py           # Benchmarking utilities
│   └── management/
│       └── commands/
│           ├── benchmark.py    # Benchmark management command
│           └── generate_data.py # Data generation command
├── crm/                        # Django project settings
│   ├── settings.py             # Project configuration
│   └── urls.py                 # Root URL configuration
├── benchmark_results/          # Generated benchmark reports and charts
├── manage.py                   # Django management script
└── README.md                   # This file
```

## 🗄️ Data Models

### AppUser
Main contact/user model with the following fields:
- `first_name`, `last_name` - User names
- `gender` - Gender selection (M/F/O)
- `customer_id` - Unique auto-generated customer identifier (format: CUST-{12-char-hex})
- `phone_number` - Contact phone number
- `created`, `last_updated` - Timestamps (indexed)
- `birthday` - Date of birth
- `address` - Foreign key to Address model

### Address
Address information model:
- `street`, `street_number` - Street details
- `city`, `city_code` - City information
- `country` - Country name

### CustomerRelationship
Customer relationship and loyalty tracking:
- `appuser` - One-to-one relationship with AppUser
- `points` - Loyalty points (indexed)
- `created`, `last_activity` - Activity timestamps (indexed)

## 🔌 API Endpoints

### Base URL
```
/api/contacts/
```

### Available Endpoints

#### List Contacts
```
GET /api/contacts/
```
Returns paginated list of contacts with filtering, sorting, and search capabilities.

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 50)
- `ordering` - Sort fields (comma-separated, prefix with `-` for descending)
  - Example: `?ordering=-created,last_name`
  - Example: `?ordering=-relationship__points,last_name,first_name`
- `search` - Full-text search across multiple fields
- Filter parameters (see below)

**Filter Examples:**
```
# Filter by name
?first_name__icontains=John

# Filter by city
?address__city__icontains=New York

# Filter by points range
?relationship__points__gte=1000

# Multiple filters
?gender=M&relationship__points__gte=5000&address__country__icontains=United
```

#### Get Contact Details
```
GET /api/contacts/{id}/
```
Returns detailed information for a specific contact.

#### Statistics
```
GET /api/contacts/stats/
```
Returns statistics about the contacts database:
- Total contacts count
- Contacts with address
- Contacts with relationship data

#### Query Cancellation
All endpoints support query cancellation via the `_cancel` query parameter:
```
GET /api/contacts/?_cancel=1
```
- Returns HTTP 499 (Client Closed Request) status
- Useful for cancelling long-running queries
- Works with all endpoints (list, retrieve, stats)
- Automatic timeout handling (default: 30 seconds, configurable)

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- pip

### Step 1: Clone the Repository
```bash
git clone git@github.com:iz3n/crm.git
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- Django 5.2.8
- djangorestframework
- django-filter
- psycopg2-binary
- python-decouple
- Faker (for data generation)
- matplotlib, pandas (for benchmarking charts)

### Step 4: Configure Database

Create a `.env` file in the project root (use `.env.example` as a template):

```env
DB_NAME=helloagain_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key
DEBUG=True

# Query cancellation and timeout settings (pg_trgm branch)
QUERY_TIMEOUT=30
ENABLE_QUERY_CANCELLATION=True
```

### Step 5: Run Migrations
```bash
python manage.py migrate
```

### Step 6: Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

## 💻 Usage

### Generate Test Data

Generate large datasets for performance testing:

```bash
# Generate 3 million records (default)
python manage.py generate_data

# Generate custom number of records
python manage.py generate_data --count 1000000

# Use custom batch size
python manage.py generate_data --count 3000000 --batch-size 20000
```

### Run Benchmarks

Run comprehensive performance benchmarks:

```bash
# Run all benchmarks with charts and exports
python manage.py benchmark

# Skip chart generation
python manage.py benchmark --no-charts

# Skip result export
python manage.py benchmark --no-export
```

Benchmark results are saved in the `benchmark_results/` directory:
- JSON files with detailed results
- CSV files for data analysis
- PNG charts visualizing performance metrics

### API Usage Examples

#### Basic List Request
```bash
curl http://localhost:8000/api/contacts/
```

#### Filtered Request
```bash
curl "http://localhost:8000/api/contacts/?first_name__icontains=John&gender=M"
```

#### Sorted Request
```bash
curl "http://localhost:8000/api/contacts/?ordering=-relationship__points,last_name"
```

#### Search Request
```bash
curl "http://localhost:8000/api/contacts/?search=John"
```

#### Request with Cancellation Token
```bash
# Cancel a long-running query
curl "http://localhost:8000/api/contacts/?search=John&_cancel=1"
```

#### Paginated Request
```bash
curl "http://localhost:8000/api/contacts/?page=2&page_size=100"
```

## 📊 Benchmarking

The benchmarking system tests various query scenarios:

1. **Initial List Load** - Basic paginated list retrieval
2. **Filter by Name** - Filtering by first name
3. **Sort by Attribute** - Single and multi-field sorting
4. **Filter and Sort** - Combined filtering and sorting
5. **Multiple Filters** - Complex queries with multiple conditions
6. **Search** - Full-text search across fields
7. **Complex Query** - Multiple filters with sorting
8. **Pagination Performance** - Testing different pages (first, middle, last, random)

### Benchmark Metrics

Each benchmark measures:
- **Execution Time** - Query execution time in milliseconds
- **Query Count** - Number of database queries executed
- **Result Count** - Number of records returned
- **Status Code** - HTTP response status
- **Error Tracking** - Captures timeouts and errors

### Benchmark Output

The benchmark command generates:
- **Console Output** - Real-time progress and results
- **JSON Reports** - Detailed structured data
- **CSV Reports** - Spreadsheet-compatible data
- **Performance Charts** - Visual representations of:
  - Execution time by test
  - Query count analysis
  - Time vs query count correlation
  - Performance distributions
  - Pagination performance graphs

## 🔧 Optimization Strategies

This project supports testing three different optimization approaches:

### 1. Baseline (No Optimization)
Standard Django ORM queries without additional database optimizations. This serves as the baseline for comparison.

**Characteristics:**
- Standard Django indexes (primary keys, foreign keys)
- No additional database indexes
- Standard PostgreSQL text search

### 2. Index Optimization ⭐ **(This Branch)**
Strategic database indexes on frequently queried fields to improve query performance. This branch implements carefully selected indexes based on common query patterns.

**Implemented Indexes:**

**AppUser Model:**
- `created` - Single field index (via `db_index=True`)
- `customer_id` - Unique index (automatic from `unique=True`)
- `['first_name', 'last_name']` - Composite index for name-based searches
- `['address', 'last_name']` - Composite index for address + name queries

**Address Model:**
- `city` - Single field index for city filtering
- `country` - Single field index for country filtering
- `['country', 'city']` - Composite index for country + city queries

**CustomerRelationship Model:**
- `points` - Single field index (via `db_index=True`) for points-based filtering and sorting
- `last_activity` - Single field index (via `db_index=True`) for activity-based queries

**Implementation Details:**
- Indexes added via Django migrations (`0002_alter_appuser_...` and `0003_remove_address_...`)
- Composite indexes created for common multi-field query patterns
- Single-field indexes on frequently filtered/sorted columns
- Indexes optimized for the most common API query patterns

**Expected Performance Improvements:**
- 30-70% faster execution on filtered queries
- 40-60% faster execution on sorted queries
- Significant improvement on combined filter + sort operations
- Better pagination performance on large datasets

### 3. pg_trgm Optimization ⭐ **(This Branch)**
PostgreSQL trigram extension for advanced text search and pattern matching. This branch implements pg_trgm with query cancellation token support.

**Features:**
- Trigram-based text search for significantly better performance on text fields
- GIN indexes on text columns for fast pattern matching
- Improved `LIKE` and `ILIKE` query performance (50-90% faster)
- Better handling of partial text matches and fuzzy searches
- Query cancellation token support for long-running queries
- Automatic query timeout management

**Implementation:**

1. **Enable pg_trgm Extension:**
   The extension is automatically enabled via migration `0004_enable_pg_trgm.py`. If you need to enable it manually:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   ```

2. **Create GIN Trigram Indexes:**
   After enabling the extension, create trigram indexes on text fields for optimal performance:
   ```sql
   -- Create GIN indexes on text fields using trigram operators
   CREATE INDEX idx_appuser_first_name_trgm ON appuser USING gin (first_name gin_trgm_ops);
   CREATE INDEX idx_appuser_last_name_trgm ON appuser USING gin (last_name gin_trgm_ops);
   CREATE INDEX idx_address_city_trgm ON address USING gin (city gin_trgm_ops);
   CREATE INDEX idx_address_country_trgm ON address USING gin (country gin_trgm_ops);
   CREATE INDEX idx_address_street_trgm ON address USING gin (street gin_trgm_ops);
   ```

3. **Query Cancellation Token Support:**
   This branch includes `QueryCancellationMixin` that provides:
   - Request cancellation via `?_cancel=1` query parameter
   - Automatic query timeout (default: 30 seconds, configurable)
   - Database-level statement timeout for PostgreSQL
   - Graceful error handling for cancelled/timeout queries

**Query Cancellation Usage:**
```bash
# Cancel a request by adding _cancel parameter
curl "http://localhost:8000/api/contacts/?_cancel=1"

# The API will return status 499 (Client Closed Request) with cancellation message
```

**Configuration:**
- `QUERY_TIMEOUT` - Set in `.env` file (default: 30 seconds)
- `ENABLE_QUERY_CANCELLATION` - Set in `.env` file (default: True)

## 🧪 Performance Testing

### Running Tests for pg_trgm Optimization (This Branch)

**This branch is configured with pg_trgm extension and query cancellation support.** To run benchmarks:

1. **Ensure migrations are applied:**
   ```bash
   python manage.py migrate
   ```
   This will apply the pg_trgm extension migration (`0004_enable_pg_trgm.py`).

2. **Create Trigram Indexes (if not already created):**
   Connect to your PostgreSQL database and run:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_appuser_first_name_trgm ON appuser USING gin (first_name gin_trgm_ops);
   CREATE INDEX IF NOT EXISTS idx_appuser_last_name_trgm ON appuser USING gin (last_name gin_trgm_ops);
   CREATE INDEX IF NOT EXISTS idx_address_city_trgm ON address USING gin (city gin_trgm_ops);
   CREATE INDEX IF NOT EXISTS idx_address_country_trgm ON address USING gin (country gin_trgm_ops);
   CREATE INDEX IF NOT EXISTS idx_address_street_trgm ON address USING gin (street gin_trgm_ops);
   ```

3. **Run benchmarks:**
   ```bash
   python manage.py benchmark
   ```

4. **Compare with baseline:**
   - Switch to the baseline branch (no optimization)
   - Run the same benchmarks
   - Compare execution times and query counts, especially for text search queries

### Testing Other Optimization Strategies

1. **Baseline Testing:**
   - Switch to baseline branch (no optimization)
   - Run benchmarks to establish baseline metrics

2. **Index Optimization Testing:**
   - Switch to index optimization branch
   - Already configured with strategic indexes
   - Run benchmarks and compare with baseline

3. **pg_trgm Testing:** ⭐ **(Current Branch)**
   - pg_trgm extension enabled via migration
   - Create trigram indexes (see above)
   - Run benchmarks and compare results
   - Test query cancellation with `?_cancel=1` parameter

### Comparing Results

The benchmark system generates comparable metrics across all three strategies:
- Execution time improvements
- Query count reductions
- Pagination performance
- Search query performance
- Complex query handling

### Expected Improvements (pg_trgm Optimization Branch)

Based on the pg_trgm extension and trigram indexes implemented in this branch:

- **Text Search Queries:** 50-90% improvement on queries using:
  - `icontains` filters on text fields (`first_name`, `last_name`, `city`, `country`, `street`)
  - Full-text search across multiple fields
  - Partial text matching and fuzzy searches
  
- **LIKE/ILIKE Operations:** 60-95% improvement on:
  - Pattern matching queries
  - Case-insensitive text searches
  - Partial string matches
  
- **Search Performance:**
  - Name searches: Dramatic speedup from trigram indexes on `first_name` and `last_name`
  - Location searches: Fast queries using trigram indexes on `city`, `country`, and `street`
  - Combined text searches: Excellent performance on multi-field text queries
  
- **Query Cancellation Benefits:**
  - Prevents runaway queries from consuming resources
  - Automatic timeout handling (default: 30 seconds)
  - Better user experience with cancellable long-running requests
  - Database-level statement timeout for PostgreSQL

**Note:** Actual improvements depend on dataset size, query patterns, and database configuration. Benchmark results will show specific performance gains. The pg_trgm optimization is particularly effective for text-heavy search operations.

## 📝 Notes

### pg_trgm Optimization Branch Specific Notes

- **pg_trgm Extension:** Enabled via migration `0004_enable_pg_trgm.py`
- **Trigram Indexes:** Must be created manually after migration (see SQL commands above)
- **Query Cancellation:** Enabled by default, can be configured via `ENABLE_QUERY_CANCELLATION` in `.env`
- **Query Timeout:** Default 30 seconds, configurable via `QUERY_TIMEOUT` in `.env`
- **Permission Requirements:** Database user needs `CREATE EXTENSION` permission for pg_trgm
- **Index Maintenance:** Trigram GIN indexes add some overhead to INSERT/UPDATE but provide massive SELECT improvements
- **Text Search Optimization:** Best performance gains on `icontains`, `LIKE`, and `ILIKE` queries

### Query Cancellation Token Feature

This branch includes a comprehensive query cancellation system:

- **Cancellation Parameter:** Add `?_cancel=1` to any API request to cancel it
- **Automatic Timeout:** Queries exceeding the timeout are automatically cancelled
- **Database-Level Timeout:** PostgreSQL statement timeout is set at the database level
- **Graceful Handling:** Cancelled requests return HTTP 499 status with appropriate error message
- **Context Manager:** Uses `QueryCancellationContext` for automatic timeout management

**Example Usage:**
```bash
# Normal request
curl "http://localhost:8000/api/contacts/?first_name__icontains=John"

# Cancelled request
curl "http://localhost:8000/api/contacts/?first_name__icontains=John&_cancel=1"
```

### General Notes

- The system is designed to handle millions of records efficiently
- Benchmark results are timestamped and saved for comparison
- All queries use `select_related()` to avoid N+1 query problems
- The API supports both paginated and non-paginated responses
- Timeout handling is built into the benchmark system
- Compare benchmark results with baseline and index optimization branches to measure actual improvements
- pg_trgm is particularly effective for text-heavy workloads and search operations

## 🔍 Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check `.env` file configuration
- Ensure database exists: `CREATE DATABASE helloagain_db;`

### Benchmark Timeouts
- Increase `DB_STATEMENT_TIMEOUT` in `.env`
- Reduce dataset size for initial testing
- Check database server resources

### Memory Issues
- Reduce batch size in data generation
- Use smaller page sizes for benchmarks
- Monitor system resources during large operations


**Note:** This project is designed for performance testing and benchmarking. Ensure proper database backups before running large-scale data generation or optimization tests.

