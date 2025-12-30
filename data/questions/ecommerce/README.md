# Question Bank Structure

## Overview

The question bank for OpenNL2Data-Bench follows a **scenario-driven** design approach. Questions are organized by business domain and difficulty level, based on a realistic e-commerce company schema.

## Directory Structure

```
data/questions/ecommerce/
├── README.md                    # This file
├── schema_metadata.yaml         # Schema information and business context
├── order/                       # Order domain questions
│   ├── L1_basic.yaml           # Basic queries (single table, simple filters)
│   ├── L2_intermediate.yaml    # Intermediate queries (joins, aggregations)
│   ├── L3_advanced.yaml        # Advanced queries (subqueries, window functions)
│   ├── L4_expert.yaml          # Expert queries (complex business logic)
│   ├── L5_master.yaml          # Master queries (multi-dimensional analysis)
│   └── L6_ninja.yaml           # Ninja queries (extreme edge cases)
├── payment/                     # Payment domain questions
│   ├── L1_basic.yaml
│   └── ...
├── logistics/                   # Logistics domain questions
│   ├── L1_basic.yaml
│   └── ...
└── aftersales/                  # After-sales domain questions
    ├── L1_basic.yaml
    └── ...
```

## Question Format (YAML)

Each question file contains an array of question objects with the following structure:

```yaml
questions:
  - question_id: "ORD-L1-001"
    difficulty_level: "L1"  # L1-L6
    business_department: "订单管理"
    question_text: "查询今天创建的所有订单"

    # Business context
    business_scenario: "订单中心日常运营"
    expected_insight: "了解当日订单量"

    # SQL information
    target_tables:
      - "ord_order_main"
    sql_patterns:
      - "simple_filter"
      - "date_function"

    golden_sql: |
      SELECT
          order_id,
          order_no,
          user_id,
          total_amount,
          actual_amount,
          order_status,
          order_time
      FROM ord_order_main
      WHERE DATE(order_time) = CURRENT_DATE
        AND is_deleted = 0
      ORDER BY order_time DESC;

    # Expected result structure (for validation)
    result_columns:
      - order_id
      - order_no
      - user_id
      - total_amount
      - actual_amount
      - order_status
      - order_time

    # Quality assessment
    data_quality_tier: "high"  # high/medium/low

    # Metadata
    created_by: "PowerData Team"
    created_at: "2025-01-01"
    tags:
      - "订单查询"
      - "日期过滤"
      - "基础查询"
```

## Difficulty Levels

### L1: Basic (基础)
- **Query Complexity**: Single table, simple WHERE conditions
- **SQL Features**: SELECT, WHERE, ORDER BY, LIMIT
- **Business Complexity**: Direct queries, no calculations
- **Example**: "查询今天的订单"

### L2: Intermediate (中级)
- **Query Complexity**: 2-3 table joins, basic aggregations
- **SQL Features**: JOIN, GROUP BY, HAVING, simple functions
- **Business Complexity**: Cross-table queries, basic metrics
- **Example**: "统计每个用户的订单数量和总金额"

### L3: Advanced (高级)
- **Query Complexity**: Multiple joins, subqueries, complex aggregations
- **SQL Features**: Subqueries, CASE WHEN, window functions (basic)
- **Business Complexity**: Multi-dimensional analysis, conditional logic
- **Example**: "分析用户的复购率和平均订单价值"

### L4: Expert (专家)
- **Query Complexity**: Complex subqueries, advanced window functions
- **SQL Features**: CTEs, advanced window functions, complex JOINs
- **Business Complexity**: Cohort analysis, funnel analysis
- **Example**: "计算用户生命周期价值（LTV）和留存率"

### L5: Master (大师)
- **Query Complexity**: Multi-level CTEs, recursive queries, advanced analytics
- **SQL Features**: Recursive CTEs, PIVOT, advanced window functions
- **Business Complexity**: Predictive metrics, complex business rules
- **Example**: "基于RFM模型进行用户分层分析"

### L6: Ninja (忍者)
- **Query Complexity**: Edge cases, extreme performance optimization
- **SQL Features**: All above + database-specific optimizations
- **Business Complexity**: Real-world edge cases, data quality issues
- **Example**: "处理订单拆分后的金额分摊和优惠券分配"

## Data Quality Tiers

Questions are designed to test system robustness across different schema quality levels:

### High Quality (80%)
- Clean table and column names (full words, clear meanings)
- Complete comments on all tables and columns
- Proper normalization and relationships
- Standard naming conventions

### Medium Quality (15%)
- Reasonable abbreviations (e.g., `usr_` instead of `user_`)
- Partial comments (only on important columns)
- Acceptable design patterns

### Low Quality (5%)
- Cryptic abbreviations (e.g., `t1`, `c_nm`)
- No comments
- Poor design choices (denormalization, inconsistent naming)

## Question Design Principles

1. **Scenario-Driven**: Questions reflect real business needs
2. **Progressive Difficulty**: Clear progression from L1 to L6
3. **Business Context**: Every question has business justification
4. **Diverse Patterns**: Cover different SQL patterns and techniques
5. **Realistic Data**: Questions assume realistic data distributions
6. **Edge Cases**: Include edge cases and data quality issues

## Example Question Categories by Department

### 订单管理 (Order Management)
- 订单查询和统计
- 订单状态流转分析
- 订单金额计算
- 订单拆分和合并

### 支付管理 (Payment Management)
- 支付流水查询
- 支付成功率分析
- 退款统计
- 账户余额管理

### 物流管理 (Logistics Management)
- 发货单查询
- 物流时效分析
- 库存查询和预警
- 配送路线优化

### 售后服务 (After-Sales Service)
- 退款退货统计
- 客服工单分析
- 售后满意度评价
- 质检统计分析

## Quality Assurance

Each question should be reviewed for:

1. **SQL Correctness**: SQL syntax is valid for all target databases
2. **Business Accuracy**: Result reflects correct business logic
3. **Performance**: Query is reasonably efficient
4. **Clarity**: Question text is clear and unambiguous
5. **Testability**: Expected results can be validated programmatically

## Contributing

When adding new questions:

1. Follow the YAML format strictly
2. Assign appropriate difficulty level
3. Include complete business context
4. Test SQL on actual schema
5. Add relevant tags for categorization
6. Update this README if adding new categories

## References

- Schema Definition: `data/schemas/`
- Schema Generator: `onb/schemas/generator.py`
- E-commerce Domain Models: `onb/schemas/ecommerce/`
