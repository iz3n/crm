# CRM Contacts API - Performance Benchmarking Project

> **Branch: `optimize_index`** - This branch implements **Index Optimization** strategy for improved database query performance.

A high-performance Django REST API for managing customer contacts with comprehensive benchmarking tools to measure and optimize database query performance. This branch focuses on strategic database indexing to improve query execution times.

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

**This branch (`optimize_index`) implements Index Optimization** - a strategy that adds strategic database indexes on frequently queried fields to significantly improve query performance. This is one of three optimization approaches being tested:

1. **Baseline (No Optimization)** - Standard Django ORM queries without additional optimizations
2. **Index Optimization** ⭐ **(This Branch)** - Strategic database indexes on frequently queried fields
3. **pg_trgm Optimization** - PostgreSQL trigram extension for advanced text search capabilities

The system can handle millions of records and provides detailed performance metrics, charts, and reports to analyze query performance improvements achieved through indexing.

## ✨ Features

- **RESTful API** with Django REST Framework
- **Advanced Filtering** - Filter by any field from AppUser, Address, or CustomerRelationship
- **Flexible Sorting** - Single and multi-field sorting support
- **Pagination** - Efficient pagination for large datasets
- **Search Functionality** - Full-text search across multiple fields
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

### 3. pg_trgm Optimization
PostgreSQL trigram extension for advanced text search and pattern matching.

**Features:**
- Trigram-based text search for better performance on text fields
- GIN indexes on text columns
- Improved `LIKE` and `ILIKE` query performance
- Better handling of partial text matches

**Setup:**
```sql
-- Enable pg_trgm extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create GIN indexes on text fields
CREATE INDEX idx_appuser_first_name_trgm ON appuser USING gin (first_name gin_trgm_ops);
CREATE INDEX idx_appuser_last_name_trgm ON appuser USING gin (last_name gin_trgm_ops);
CREATE INDEX idx_address_city_trgm ON address USING gin (city gin_trgm_ops);
```

## 🧪 Performance Testing

### Running Tests for Index Optimization (This Branch)

**This branch is configured with index optimizations already applied.** To run benchmarks:

1. **Ensure migrations are applied:**
   ```bash
   python manage.py migrate
   ```
   This will apply the index optimization migrations (`0002` and `0003`).

2. **Run benchmarks:**
   ```bash
   python manage.py benchmark
   ```

3. **Compare with baseline:**
   - Switch to the baseline branch (no optimization)
   - Run the same benchmarks
   - Compare execution times and query counts

### Testing Other Optimization Strategies

1. **Baseline Testing:**
   - Switch to baseline branch (no optimization)
   - Run benchmarks to establish baseline metrics

2. **Index Optimization Testing:** ⭐ **(Current Branch)**
   - Already configured with strategic indexes
   - Run benchmarks and compare with baseline

3. **pg_trgm Testing:**
   - Switch to pg_trgm optimization branch
   - Enable pg_trgm extension
   - Create trigram indexes
   - Run benchmarks and compare results

### Comparing Results

The benchmark system generates comparable metrics across all three strategies:
- Execution time improvements
- Query count reductions
- Pagination performance
- Search query performance
- Complex query handling

### Expected Improvements (Index Optimization Branch)

Based on the indexes implemented in this branch:

- **Filtered Queries:** 30-70% improvement on queries filtering by:
  - Name fields (`first_name`, `last_name`)
  - Address fields (`city`, `country`)
  - Relationship fields (`points`, `last_activity`)
  
- **Sorted Queries:** 40-60% improvement on queries sorting by:
  - `created` timestamp
  - `points` (loyalty points)
  - `last_activity` timestamp
  
- **Combined Operations:** 50-80% improvement on queries combining:
  - Filter + Sort operations
  - Multi-field filtering
  - Pagination with filtering/sorting
  
- **Composite Index Benefits:**
  - Name searches: Significant speedup from `['first_name', 'last_name']` index
  - Location queries: Faster queries using `['country', 'city']` composite index
  - Address + Name: Optimized queries using `['address', 'last_name']` index

**Note:** Actual improvements depend on dataset size, query patterns, and database configuration. Benchmark results will show specific performance gains.

## 📝 Notes

### Index Optimization Branch Specific Notes

- **Indexes Applied:** This branch includes strategic indexes optimized for common query patterns
- **Migration Status:** Ensure migrations `0002` and `0003` are applied to have all indexes active
- **Index Maintenance:** Indexes add slight overhead to INSERT/UPDATE operations but significantly improve SELECT performance
- **Query Optimization:** The indexes are designed to work with Django ORM's query patterns and the API's filtering/sorting features

### General Notes

- The system is designed to handle millions of records efficiently
- Benchmark results are timestamped and saved for comparison
- All queries use `select_related()` to avoid N+1 query problems
- The API supports both paginated and non-paginated responses
- Timeout handling is built into the benchmark system
- Compare benchmark results with baseline branch to measure actual improvements

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

