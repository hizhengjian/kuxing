# 测试运行脚本

## 运行所有测试
```bash
pytest tests/ -v
```

## 运行特定测试文件
```bash
pytest tests/test_memory_store.py -v
```

## 运行带覆盖率报告
```bash
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html
```

## 运行特定测试函数
```bash
pytest tests/test_scheduler.py::test_scheduler_init -v
```

## 快速测试（跳过慢速测试）
```bash
pytest tests/ -v -m "not slow"
```

## 查看覆盖率报告
```bash
# 生成 HTML 报告后
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 测试说明

所有测试都使用 mock 的 Claude 调用器，不会真实调用 Claude API，因此：
- ✅ 测试速度快（秒级完成）
- ✅ 不消耗 API 配额
- ✅ 可以离线运行
- ✅ 结果可预测

## 安装测试依赖

```bash
pip install -r requirements-dev.txt
```
