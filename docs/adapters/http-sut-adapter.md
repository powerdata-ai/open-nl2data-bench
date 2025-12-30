# HTTP API SUT适配器使用示例

## 目录

1. [基础用法](#基础用法)
2. [认证方式](#认证方式)
3. [自定义字段映射](#自定义字段映射)
4. [重试配置](#重试配置)
5. [完整示例](#完整示例)

---

## 基础用法

### 最简单的配置

```yaml
# config.yaml
database:
  type: mysql
  host: localhost
  database: test_db
  user: root
  password: ${DB_PASSWORD}

sut:
  name: "MyNL2SQL"
  type: "http"
  version: "1.0.0"
  config:
    api_url: "https://api.example.com/nl2sql"
    method: "POST"
    timeout: 30
```

运行：
```bash
export DB_PASSWORD=your_password
python -m onb.cli.main test run -c config.yaml -q questions/
```

### 编程方式使用

```python
from onb.adapters.sut.http import HTTPSUTAdapter
from onb.core.types import SUTConfig, SchemaInfo
from onb.runner.test_runner import TestRunner

# 配置HTTP适配器
config = SUTConfig(
    name="MyNL2SQL",
    type="http",
    version="1.0.0",
    config={
        "api_url": "https://api.example.com/nl2sql",
        "method": "POST",
        "timeout": 30.0,
    }
)

# 创建适配器
sut_adapter = HTTPSUTAdapter(config)
sut_adapter.initialize()

# 执行查询
schema = SchemaInfo(...)
result = sut_adapter.query(
    question="How many users?",
    schema=schema,
    language="en"
)

print(f"Generated SQL: {result.generated_sql}")
print(f"Success: {result.success}")
```

---

## 认证方式

### 1. Bearer Token

```yaml
sut:
  config:
    api_url: "https://api.example.com/nl2sql"
    auth_type: "bearer"
    auth_token: "${API_TOKEN}"  # 从环境变量读取
```

请求头将包含：
```
Authorization: Bearer your-token-here
```

### 2. API Key

```yaml
sut:
  config:
    api_url: "https://api.example.com/nl2sql"
    auth_type: "api_key"
    api_key: "${API_KEY}"
```

请求头将包含：
```
X-API-Key: your-api-key-here
```

### 3. Basic Auth

```yaml
sut:
  config:
    api_url: "https://api.example.com/nl2sql"
    auth_type: "basic"
    username: "admin"
    password: "${PASSWORD}"
```

### 4. 自定义Header

```yaml
sut:
  config:
    api_url: "https://api.example.com/nl2sql"
    headers:
      X-Custom-Auth: "custom-value"
      X-Request-ID: "12345"
      X-Client-Version: "1.0.0"
```

---

## 自定义字段映射

如果你的API使用不同的字段名，可以自定义映射：

### 请求字段映射

```yaml
sut:
  config:
    api_url: "https://api.example.com/nl2sql"
    request_mapping:
      question_key: "query"          # 默认: "question"
      schema_key: "database_schema"  # 默认: "schema"
      language_key: "lang"           # 默认: "language"
```

**默认请求格式：**
```json
{
  "question": "How many users?",
  "schema": {...},
  "language": "en"
}
```

**自定义后：**
```json
{
  "query": "How many users?",
  "database_schema": {...},
  "lang": "en"
}
```

### 响应字段映射

```yaml
sut:
  config:
    api_url: "https://api.example.com/nl2sql"
    response_mapping:
      sql_key: "generated_query"     # 默认: "sql"
      data_key: "results"            # 默认: "data"
      error_key: "error_message"     # 默认: "error"
      time_key: "execution_time_ms"  # 默认: "time_ms"
      token_key: "usage"             # 默认: "tokens"
```

**你的API响应：**
```json
{
  "generated_query": "SELECT COUNT(*) FROM users",
  "results": [{"count": 42}],
  "execution_time_ms": 150,
  "usage": {
    "input": 50,
    "output": 30,
    "total": 80
  }
}
```

框架会自动映射到标准格式。

---

## 重试配置

### 配置重试参数

```yaml
sut:
  config:
    api_url: "https://api.example.com/nl2sql"
    retry_count: 3        # 重试次数
    retry_delay: 1.0      # 重试延迟（秒）
    timeout: 30           # 超时时间（秒）
```

### 重试策略

- 第1次失败：等待 1 秒后重试
- 第2次失败：等待 2 秒后重试
- 第3次失败：等待 3 秒后重试
- 仍失败：返回错误

适用场景：
- 网络抖动
- API限流
- 临时服务不可用

---

## 完整示例

### 示例1: 对接OpenAI风格的API

```python
from onb.adapters.sut.http import HTTPSUTAdapter
from onb.core.types import SUTConfig

config = SUTConfig(
    name="OpenAI-NL2SQL",
    type="http",
    version="1.0.0",
    config={
        "api_url": "https://api.openai.com/v1/completions",
        "method": "POST",
        "auth_type": "bearer",
        "auth_token": "sk-...",
        "timeout": 60,
        "retry_count": 3,
        "request_mapping": {
            "question_key": "prompt",
        },
        "response_mapping": {
            "sql_key": "choices.0.text",
            "error_key": "error.message",
        },
    }
)

adapter = HTTPSUTAdapter(config)
adapter.initialize()
```

### 示例2: 对接自定义API

```yaml
# custom_api_config.yaml
sut:
  name: "CustomNL2SQL"
  type: "http"
  version: "2.0.0"
  config:
    api_url: "https://my-company.com/api/v2/text-to-sql"
    method: "POST"

    # 认证
    auth_type: "api_key"
    api_key: "${COMPANY_API_KEY}"

    # 自定义Header
    headers:
      X-Tenant-ID: "production"
      X-Request-Source: "benchmark"

    # 超时和重试
    timeout: 45
    retry_count: 5
    retry_delay: 2.0

    # 请求字段映射
    request_mapping:
      question_key: "natural_language_query"
      schema_key: "db_metadata"
      language_key: "query_language"

    # 响应字段映射
    response_mapping:
      sql_key: "sql_statement"
      data_key: "query_results"
      error_key: "error_info"
      time_key: "processing_time_ms"
      token_key: "token_statistics"
```

使用：
```bash
export COMPANY_API_KEY=your-key
python -m onb.cli.main test run -c custom_api_config.yaml -q questions/
```

### 示例3: 测试多个API

```python
"""对比多个NL2SQL系统"""
from pathlib import Path
from onb.adapters.sut.http import HTTPSUTAdapter
from onb.adapters.database.mysql import MySQLAdapter
from onb.runner.test_runner import TestRunner
from onb.questions.loader import QuestionLoader

# 加载题目
loader = QuestionLoader()
questions = loader.load_questions(Path("questions/"))

# 配置数据库
db_adapter = MySQLAdapter(db_config)
db_adapter.connect()

# 定义多个待测系统
systems = [
    {
        "name": "SystemA",
        "config": SUTConfig(
            name="SystemA",
            type="http",
            version="1.0",
            config={
                "api_url": "https://system-a.com/api/nl2sql",
                "auth_type": "bearer",
                "auth_token": "token-a",
            }
        )
    },
    {
        "name": "SystemB",
        "config": SUTConfig(
            name="SystemB",
            type="http",
            version="1.0",
            config={
                "api_url": "https://system-b.com/text2sql",
                "auth_type": "api_key",
                "api_key": "key-b",
            }
        )
    },
]

# 测试每个系统
results = []
for sys in systems:
    print(f"\nTesting {sys['name']}...")

    adapter = HTTPSUTAdapter(sys['config'])
    adapter.initialize()

    runner = TestRunner(db_adapter, adapter)
    report = runner.run_test_suite(questions)

    results.append({
        "system": sys['name'],
        "accuracy": report.accuracy,
        "avg_time": report.total_duration_seconds / report.total_questions,
        "correct": report.correct_count,
        "total": report.total_questions,
    })

    adapter.cleanup()

# 打印对比结果
import pandas as pd
df = pd.DataFrame(results)
print("\n=== Comparison Results ===")
print(df.sort_values("accuracy", ascending=False))
```

输出：
```
=== Comparison Results ===
    system  accuracy  avg_time  correct  total
0  SystemA      0.95      0.45       38     40
1  SystemB      0.88      0.32       35     40
```

### 示例4: GET方法API

某些API使用GET方法：

```yaml
sut:
  config:
    api_url: "https://api.example.com/query"
    method: "GET"  # 使用GET而非POST
    auth_type: "bearer"
    auth_token: "${TOKEN}"
```

参数将作为URL查询字符串：
```
GET https://api.example.com/query?question=...&schema=...
```

---

## API响应格式要求

### 最小响应格式

```json
{
  "sql": "SELECT COUNT(*) FROM users"
}
```

### 完整响应格式（推荐）

```json
{
  "sql": "SELECT COUNT(*) FROM users",
  "data": [
    {"count": 42}
  ],
  "time_ms": 150,
  "tokens": {
    "input": 50,
    "output": 30,
    "total": 80
  },
  "confidence": 0.95,
  "model_version": "v2.1.0"
}
```

### 错误响应格式

```json
{
  "sql": "",
  "error": "Invalid schema format"
}
```

---

## 调试技巧

### 1. 查看实际HTTP请求

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# httpx会输出详细的请求信息
```

### 2. 测试单个查询

```python
from onb.adapters.sut.http import HTTPSUTAdapter

adapter = HTTPSUTAdapter(config)
adapter.initialize()

result = adapter.query("Test question", schema)

print(f"Success: {result.success}")
print(f"SQL: {result.generated_sql}")
print(f"Error: {result.error}")
print(f"Metadata: {adapter.get_metadata()}")
```

### 3. 检查响应映射

```python
# 打印原始响应（在_parse_response中添加）
import json
print(json.dumps(response_data, indent=2))
```

---

## 常见问题

### Q1: API返回401 Unauthorized

检查认证配置：
```yaml
# Bearer Token
auth_type: "bearer"
auth_token: "${YOUR_TOKEN}"  # 确保环境变量已设置

# API Key
auth_type: "api_key"
api_key: "${YOUR_KEY}"
```

### Q2: 超时错误

增加超时时间：
```yaml
config:
  timeout: 60  # 秒
```

### Q3: 字段映射不生效

确认映射配置正确：
```yaml
response_mapping:
  sql_key: "your_field_name"  # 必须与API响应字段名完全匹配
```

### Q4: 数据格式不匹配

API返回的data字段应该是：
- 列表：`[{col1: val1}, {col2: val2}]`
- 字典：`{col1: val1, col2: val2}` (会被转为单行DataFrame)

---

## 下一步

- 查看[完整API文档](../api-reference.md)
- 了解[测试报告](../reports.md)
- 查看[更多示例](../../examples/)
