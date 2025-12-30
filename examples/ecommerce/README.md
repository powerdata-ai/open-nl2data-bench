# OpenNL2SQL-Bench Examples

This directory contains example datasets and questions for testing the OpenNL2SQL-Bench framework.

## Directory Structure

```
examples/
└── ecommerce/
    ├── questions/           # Test questions in YAML format
    │   ├── L1_001_count_users.yaml
    │   ├── L1_002_avg_order.yaml
    │   ├── L2_001_top_products.yaml
    │   └── L3_001_monthly_buyers.yaml
    └── README.md            # This file
```

## Ecommerce Domain

### Database Schema

The ecommerce example assumes the following simplified schema:

```sql
-- Users table
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id INT PRIMARY KEY,
    product_name VARCHAR(200),
    category VARCHAR(50),
    price DECIMAL(10, 2)
);

-- Orders table
CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    amount DECIMAL(10, 2),
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Order Items table
CREATE TABLE order_items (
    id INT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### Questions by Complexity

**Level 1 (L1) - Basic Queries:**
- Single table queries
- Simple aggregations (COUNT, AVG, SUM)
- No JOINs or complex logic

**Level 2 (L2) - Intermediate Queries:**
- Multiple table JOINs
- GROUP BY with aggregations
- ORDER BY and LIMIT
- Basic ranking and filtering

**Level 3 (L3) - Advanced Queries:**
- Complex JOINs and subqueries
- HAVING clauses
- Date/time functions
- Complex business logic
- Window functions

## Running Examples

### Using Mock Adapter (No Database Required)

Run all questions:
```bash
onb test run -q examples/ecommerce/questions
```

Run with filtering:
```bash
# Only L1 questions
onb test run -q examples/ecommerce/questions -l L1

# Only L1 and L2
onb test run -q examples/ecommerce/questions -l L1 -l L2

# Specific tags
onb test run -q examples/ecommerce/questions -t aggregation

# Verbose output
onb test run -q examples/ecommerce/questions -v

# Save results to JSON
onb test run -q examples/ecommerce/questions -o results.json
```

### Using Real Database

1. Create a configuration file `config.yaml`:

```yaml
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: ${DB_PASSWORD}  # Environment variable
  database: ecommerce_test
  ssl: false

sut:
  name: "YourNL2SQLSystem"
  type: "custom"
  version: "1.0.0"
  config:
    api_endpoint: "http://localhost:8000/nl2sql"
    api_key: ${API_KEY}  # Environment variable
```

2. Set environment variables:
```bash
export DB_PASSWORD=your_password
export API_KEY=your_api_key
```

3. Run tests:
```bash
onb test run -c config.yaml -q examples/ecommerce/questions
```

## Creating Custom Questions

Use the YAML format:

```yaml
id: domain_L{level}_{number}  # e.g., ecommerce_L1_001
version: "1.0"
domain: domain_name  # e.g., ecommerce, finance
complexity: L1|L2|L3|L4|L5
question:
  en: "English question"
  zh: "中文问题"
golden_sql: "SELECT ..."
dependencies:
  tables:
    - table1
    - table2
  features:
    - JOIN
    - GROUP BY
tags:
  - tag1
  - tag2
comparison_rules:  # Optional
  row_order_matters: true|false
  float_tolerance: 0.01
  float_comparison_mode: "relative_error"|"absolute_error"
metadata:  # Optional
  difficulty: easy|medium|hard
  estimated_time_ms: 100
  author: "Your Name"
```

## License

Copyright 2025 PowerData Community

Licensed under the Apache License, Version 2.0
