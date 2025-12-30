# OpenNL2SQL-Bench 使用教程

## 目录

1. [快速演示](#快速演示)
2. [创建自己的测试题目](#创建自己的测试题目)
3. [测试真实的NL2SQL系统](#测试真实的nl2sql系统)
4. [查看和分析结果](#查看和分析结果)
5. [高级用法](#高级用法)

---

## 快速演示

### 1. 安装依赖

```bash
cd /Users/mac/Documents/code/open-nl2sql-bench

# 使用pip安装（开发模式）
pip install -e .

# 或者使用已安装的依赖运行
python -m pytest tests/ -v  # 验证环境正常
```

### 2. 运行第一个测试

使用Mock适配器（不需要真实数据库）快速体验：

```bash
# 运行所有示例题目
python -m onb.cli.main test run -q examples/ecommerce/questions

# 查看详细输出
python -m onb.cli.main test run -q examples/ecommerce/questions -v
```

**输出示例：**
```
OpenNL2SQL-Bench Test Runner

Loading questions from: examples/ecommerce/questions
Loaded 4 questions

Question Statistics:
  Total: 4
  By Domain: {'ecommerce': 4}
  By Complexity: {'L1': 2, 'L2': 1, 'L3': 1}

Running 4 tests...

            Summary
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Metric          ┃ Value     ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Total Questions │ 4         │
│ Correct         │ 0         │
│ Accuracy        │ 0.00%     │
└─────────────────┴───────────┘
```

> **注意**：Mock适配器会生成简单的SQL，主要用于演示框架功能，因此准确率较低是正常的。

---

## 创建自己的测试题目

### 1. 题目文件格式

创建一个YAML文件，例如 `my_question.yaml`：

```yaml
# 题目唯一标识：domain_complexity_number
id: ecommerce_L1_004
version: "1.0"

# 领域分类
domain: ecommerce

# 复杂度级别：L1(基础) L2(中级) L3(高级) L4(专家) L5(大师)
complexity: L1

# 多语言问题
question:
  en: "How many products are in stock?"
  zh: "有多少商品有库存？"

# 标准答案SQL（这是评测的基准）
golden_sql: "SELECT COUNT(*) as count FROM products WHERE stock > 0"

# 依赖信息
dependencies:
  tables:
    - products
  features:
    - COUNT
    - WHERE

# 标签（用于分类和筛选）
tags:
  - basic
  - filtering
  - inventory

# 对比规则（可选）
comparison_rules:
  row_order_matters: false      # 行顺序是否重要
  column_order_matters: false   # 列顺序是否重要
  float_tolerance: 0.01        # 浮点数容差
  float_comparison_mode: "relative_error"  # 或 "absolute_error"

# 元数据（可选）
metadata:
  difficulty: easy
  estimated_time_ms: 100
  author: "Your Name"
  created_at: "2024-01-15"
```

### 2. 创建题目目录

建议按领域组织题目：

```bash
mkdir -p my_questions/retail
mkdir -p my_questions/finance
mkdir -p my_questions/healthcare
```

### 3. 运行自定义题目

```bash
# 运行所有题目
python -m onb.cli.main test run -q my_questions/retail -v

# 只运行L1级别
python -m onb.cli.main test run -q my_questions/retail -l L1

# 运行多个级别
python -m onb.cli.main test run -q my_questions/retail -l L1 -l L2

# 按标签筛选
python -m onb.cli.main test run -q my_questions/retail -t inventory

# 指定语言（默认zh）
python -m onb.cli.main test run -q my_questions/retail --language en
```

---

## 测试真实的NL2SQL系统

### 方法1: 扩展SUT适配器（推荐）

创建自定义SUT适配器 `my_sut_adapter.py`：

```python
"""自定义NL2SQL系统适配器"""
import httpx
import pandas as pd
from typing import Any

from onb.adapters.sut.base import SUTAdapter
from onb.core.types import NL2SQLResponse, SchemaInfo, SUTConfig


class MyNL2SQLAdapter(SUTAdapter):
    """你的NL2SQL系统适配器"""

    def __init__(self, config: SUTConfig):
        super().__init__(config)
        self.api_url = config.config.get("api_url")
        self.api_key = config.config.get("api_key")

    def initialize(self) -> None:
        """初始化适配器"""
        self._initialized = True

    def query(
        self,
        question: str,
        schema: SchemaInfo,
        language: str = "zh",
        **kwargs: Any,
    ) -> NL2SQLResponse:
        """调用你的NL2SQL API"""
        try:
            # 1. 准备请求
            payload = {
                "question": question,
                "schema": schema.to_dict(),
                "language": language,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # 2. 调用API
            response = httpx.post(
                f"{self.api_url}/nl2sql",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

            # 3. 解析响应
            generated_sql = result.get("sql", "")
            result_data = result.get("data", [])

            # 4. 转换为DataFrame
            if result_data:
                result_df = pd.DataFrame(result_data)
            else:
                result_df = None

            # 5. 返回结果
            return NL2SQLResponse(
                generated_sql=generated_sql,
                result_dataframe=result_df,
                success=True,
                total_time_ms=result.get("time_ms", 0),
            )

        except Exception as e:
            return NL2SQLResponse(
                generated_sql="",
                success=False,
                error=str(e),
                total_time_ms=0,
            )

    def cleanup(self) -> None:
        """清理资源"""
        self._initialized = False
```

### 方法2: 使用配置文件

创建 `config.yaml`：

```yaml
# 数据库配置
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: ${DB_PASSWORD}  # 从环境变量读取
  database: test_db
  ssl: false

# SUT系统配置
sut:
  name: "MyNL2SQL"
  type: "custom"
  version: "1.0.0"
  config:
    api_url: "http://localhost:8000"
    api_key: ${API_KEY}  # 从环境变量读取
```

运行测试：

```bash
# 设置环境变量
export DB_PASSWORD=your_password
export API_KEY=your_api_key

# 使用配置文件运行
python -m onb.cli.main test run \
  -c config.yaml \
  -q examples/ecommerce/questions \
  -v
```

### 方法3: 编程方式使用

创建 `run_benchmark.py`：

```python
"""编程方式运行benchmark"""
from pathlib import Path

from onb.adapters.database.mysql import MySQLAdapter
from onb.questions.loader import QuestionLoader
from onb.runner.test_runner import TestRunner
from onb.core.types import DatabaseConfig, ComplexityLevel

# 导入你的自定义适配器
from my_sut_adapter import MyNL2SQLAdapter


def main():
    # 1. 配置数据库
    db_config = DatabaseConfig(
        type="mysql",
        host="localhost",
        port=3306,
        user="root",
        password="your_password",
        database="test_db",
    )

    # 2. 配置SUT
    sut_config = SUTConfig(
        name="MyNL2SQL",
        type="custom",
        version="1.0.0",
        config={
            "api_url": "http://localhost:8000",
            "api_key": "your_key",
        },
    )

    # 3. 初始化适配器
    db_adapter = MySQLAdapter(db_config)
    db_adapter.connect()

    sut_adapter = MyNL2SQLAdapter(sut_config)
    sut_adapter.initialize()

    # 4. 加载题目
    loader = QuestionLoader()
    questions = loader.load_questions(Path("examples/ecommerce/questions"))

    # 按条件筛选
    questions = loader.filter_questions(
        questions,
        complexity=[ComplexityLevel.L1, ComplexityLevel.L2],
    )

    print(f"Loaded {len(questions)} questions")

    # 5. 运行测试
    runner = TestRunner(db_adapter, sut_adapter)
    report = runner.run_test_suite(questions, language="zh")

    # 6. 打印结果
    print(f"\n{'='*50}")
    print(f"Test Report")
    print(f"{'='*50}")
    print(f"SUT Name: {report.sut_name}")
    print(f"Total Questions: {report.total_questions}")
    print(f"Correct: {report.correct_count}")
    print(f"Accuracy: {report.accuracy * 100:.2f}%")
    print(f"Duration: {report.total_duration_seconds:.2f}s")

    # 7. 保存详细结果
    import json
    result_dict = {
        "sut_name": report.sut_name,
        "accuracy": report.accuracy,
        "total_questions": report.total_questions,
        "correct_count": report.correct_count,
        "results": [
            {
                "question_id": r.question.id,
                "status": r.status.value,
                "generated_sql": r.sut_response.generated_sql,
                "match": r.comparison_result.match,
            }
            for r in report.question_results
        ],
    }

    with open("benchmark_results.json", "w") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to benchmark_results.json")

    # 8. 清理
    db_adapter.disconnect()
    sut_adapter.cleanup()


if __name__ == "__main__":
    main()
```

运行：

```bash
python run_benchmark.py
```

---

## 查看和分析结果

### 1. 命令行输出

标准输出包含：
- 📊 统计信息（总数、按域/复杂度/标签分类）
- ✅ 汇总表（准确率、耗时等）
- 📝 详细结果（每个题目的状态）

### 2. JSON结果文件

```bash
# 导出JSON
python -m onb.cli.main test run \
  -q examples/ecommerce/questions \
  -o results.json

# 查看结果
cat results.json
```

JSON格式：
```json
{
  "sut_name": "MockSUT",
  "test_id": "test_20240115_143022",
  "domain": "ecommerce",
  "database_type": "mysql",
  "total_questions": 4,
  "correct_count": 2,
  "accuracy": 0.5,
  "start_time": "2024-01-15T14:30:22.123456",
  "end_time": "2024-01-15T14:30:23.456789",
  "total_duration_seconds": 1.333,
  "results": [
    {
      "question_id": "ecommerce_L1_001",
      "status": "passed",
      "generated_sql": "SELECT COUNT(*) FROM users",
      "match": true,
      "reason": "Results match"
    }
  ]
}
```

### 3. 分析结果

使用Python分析：

```python
import json
import pandas as pd

# 读取结果
with open("results.json") as f:
    data = json.load(f)

# 转换为DataFrame
df = pd.DataFrame(data["results"])

# 统计分析
print(f"总准确率: {data['accuracy'] * 100:.2f}%")
print(f"\n按状态统计:")
print(df['status'].value_counts())

# 找出失败的题目
failed = df[df['status'] == 'failed']
print(f"\n失败的题目:")
for _, row in failed.iterrows():
    print(f"  - {row['question_id']}: {row['reason']}")
```

---

## 高级用法

### 1. 批量测试多个系统

```python
"""对比多个NL2SQL系统"""
from pathlib import Path

systems = [
    {"name": "SystemA", "adapter": SystemAAdapter(...)},
    {"name": "SystemB", "adapter": SystemBAdapter(...)},
    {"name": "SystemC", "adapter": SystemCAdapter(...)},
]

results = []
for sys in systems:
    runner = TestRunner(db_adapter, sys["adapter"])
    report = runner.run_test_suite(questions)
    results.append({
        "system": sys["name"],
        "accuracy": report.accuracy,
        "avg_time": report.total_duration_seconds / report.total_questions,
    })

# 生成对比报告
import pandas as pd
df = pd.DataFrame(results)
print(df.sort_values("accuracy", ascending=False))
```

### 2. 按复杂度分析

```bash
# 分别测试不同难度
for level in L1 L2 L3; do
  echo "Testing $level..."
  python -m onb.cli.main test run \
    -q examples/ecommerce/questions \
    -l $level \
    -o results_$level.json
done

# 汇总分析
python analyze_by_level.py
```

### 3. 自定义对比规则

针对特定题目使用不同的对比规则：

```yaml
# 金融领域 - 对精度要求高
id: finance_L2_001
# ...
comparison_rules:
  float_tolerance: 0.001
  float_comparison_mode: "absolute_error"

# 用户分析 - 顺序不重要
id: analytics_L2_005
# ...
comparison_rules:
  row_order_matters: false
  column_order_matters: false

# 时序数据 - 顺序很重要
id: timeseries_L3_001
# ...
comparison_rules:
  row_order_matters: true
  datetime_tolerance_ms: 1000  # 允许1秒误差
```

### 4. CI/CD集成

在GitHub Actions中使用：

```yaml
# .github/workflows/benchmark.yml
name: NL2SQL Benchmark

on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -e .

    - name: Run benchmark
      env:
        DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        API_KEY: ${{ secrets.API_KEY }}
      run: |
        python -m onb.cli.main test run \
          -c config.yaml \
          -q questions/ \
          -o results.json

    - name: Check accuracy threshold
      run: |
        python -c "
        import json
        with open('results.json') as f:
            data = json.load(f)
        if data['accuracy'] < 0.8:
            print(f'Accuracy {data[\"accuracy\"]} below threshold 0.8')
            exit(1)
        "

    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: benchmark-results
        path: results.json
```

---

## 常见问题

### Q1: 如何调试失败的测试？

```bash
# 使用 -v 查看详细信息
python -m onb.cli.main test run -q questions/ -v

# 单独运行一个题目
python -c "
from onb.questions.loader import QuestionLoader
from onb.runner.test_runner import TestRunner

loader = QuestionLoader()
question = loader.load_question('path/to/question.yaml')
result = runner.run_question(question)

print(f'Expected SQL: {question.golden_sql}')
print(f'Generated SQL: {result.sut_response.generated_sql}')
print(f'Match: {result.comparison_result.match}')
print(f'Reason: {result.comparison_result.reason}')
"
```

### Q2: Mock适配器的局限性？

Mock适配器仅用于演示框架功能，它：
- ✅ 可以测试框架本身
- ✅ 不需要真实数据库
- ❌ 无法准确模拟真实NL2SQL系统
- ❌ 生成的SQL很简单，不适合实际评测

### Q3: 如何添加新的数据库支持？

参考 `onb/adapters/database/mysql.py`，继承 `DatabaseAdapter` 基类：

```python
from onb.adapters.database.base import DatabaseAdapter

class PostgreSQLAdapter(DatabaseAdapter):
    def _build_connection_string(self) -> str:
        return f"postgresql://{self.config.user}:{self.config.password}@..."

    # 实现其他必要方法
```

---

## 下一步

- 📖 阅读 [架构设计文档](../architecture.md)
- 🔧 查看 [API参考](../api-reference.md)
- 💡 浏览 [最佳实践](../best-practices.md)
- 🤝 了解 [贡献指南](../../CONTRIBUTING.md)

---

**有问题？** 欢迎提Issue: https://github.com/PowerDataHub/open-nl2sql-bench/issues
