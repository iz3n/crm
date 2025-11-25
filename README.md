# CRM Contacts API - Performance Benchmarking Project

A high-performance Django REST API for managing customer contacts with comprehensive benchmarking tools to measure and optimize database query performance.

## 🌿 Repository Branches

This repository contains three branches, each implementing a different optimization strategy:

- **[`main`](https://github.com/iz3n/crm/tree/main)** - **Baseline (No Optimization)**
  - Standard Django ORM queries without additional optimizations
  - Serves as the baseline for performance comparison

- **[`optimize_index`](https://github.com/iz3n/crm/tree/optimize_index)** - **Index Optimization**
  - Strategic database indexes on frequently queried fields
  - 30-70% improvement on filtered/sorted queries

- **[`optimize_index_trgm`](https://github.com/iz3n/crm/tree/optimize_index_trgm)** - **pg_trgm Optimization**
  - PostgreSQL trigram extension for advanced text search
  - Query cancellation token support
  - 50-90% improvement on text search queries

> **Note:** Each branch contains its own README with branch-specific documentation. Switch between branches to compare different optimization strategies.

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

This project is a Django-based CRM system designed to handle large-scale contact management with a focus on performance optimization. It includes comprehensive benchmarking tools to test and compare different database optimization strategies, including:

1. **Baseline (No Optimization)** - Standard Django ORM queries without additional optimizations
2. **Index Optimization** - Strategic database indexes on frequently queried fields
3. **pg_trgm Optimization** - PostgreSQL trigram extension for advanced text search capabilities

The system can handle millions of records and provides detailed performance metrics, charts, and reports to analyze query performance.

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
pip install -r req.txt
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

### 2. Index Optimization
Strategic database indexes on frequently queried fields to improve query performance.

**Indexed Fields:**
- `customer_id` (unique index)
- `created`, `last_updated` (AppUser)
- `points`, `created`, `last_activity` (CustomerRelationship)
- Additional indexes on filterable fields as needed

**Implementation:**
- Add indexes via Django migrations
- Use `db_index=True` in model fields
- Create composite indexes for common query patterns

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

### Running Tests for Each Optimization Strategy

1. **Baseline Testing:**
   - Use standard Django setup
   - Run benchmarks to establish baseline metrics

2. **Index Optimization Testing:**
   - Apply index migrations
   - Run benchmarks and compare with baseline

3. **pg_trgm Testing:**
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

### Expected Improvements

- **Index Optimization:** 30-70% improvement on filtered/sorted queries
- **pg_trgm Optimization:** 50-90% improvement on text search queries
- **Combined:** Up to 95% improvement on complex text search queries

## 📝 Notes

- The system is designed to handle millions of records efficiently
- Benchmark results are timestamped and saved for comparison
- All queries use `select_related()` to avoid N+1 query problems
- The API supports both paginated and non-paginated responses
- Timeout handling is built into the benchmark system

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

