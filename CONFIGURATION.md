# Kuxing 配置说明

## 核心原则

**Kuxing 不需要额外的 API 配置！**

只要你的 `claude` 命令可用，就可以直接使用 kuxing。

---

## 前置要求

### 唯一要求：claude 命令可用

```bash
# 验证 claude 命令是否可用
claude --version

# 如果可用，输出类似：
# Claude Code CLI v2.x.x
```

如果 `claude` 命令不可用，请先安装 Claude Code CLI：
- 官方文档：https://docs.anthropic.com/claude/docs/claude-code

---

## 使用流程

### 1. 验证环境

```bash
# 检查 claude 命令
claude --version

# 检查 Python 版本（需要 3.8+）
python --version
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 直接运行

```bash
# 初始化项目
python cli.py init --config examples/test.yaml

# 运行任务
python cli.py --config examples/test.yaml run
```

**就这么简单！** 无需配置任何 API key 或环境变量。

---

## 工作原理

### Kuxing 使用 claude 命令的两个场景

#### 1. 主任务执行（接力式任务）

```python
# 每一轮任务执行
claude -p "你的任务prompt"
```

- **用途**：执行实际的开发任务
- **频率**：每轮都调用
- **配置**：使用你 `claude` 命令的配置

#### 2. 记忆压缩（自动触发）

```python
# 当记忆文件超过大小限制时
claude -p "压缩记忆的prompt"
```

- **用途**：压缩记忆文件
- **频率**：只在文件超过限制时调用
- **配置**：使用你 `claude` 命令的配置

### 统一使用 claude 命令

```
你的 claude 配置
    │
    ├─→ 主任务执行（每轮）
    └─→ 记忆压缩（按需）
```

**无论你的 `claude` 命令配置了什么 API（Claude 官方、MiniMax、或其他），kuxing 都会直接使用。**

---

## 常见问题

### Q1: 需要配置 ANTHROPIC_API_KEY 吗？

**A: 不需要！**

Kuxing 直接使用 `claude` 命令，不需要额外配置环境变量。

### Q2: 我的 claude 命令配置了 MiniMax API，可以用吗？

**A: 可以！**

Kuxing 不关心你的 `claude` 命令使用什么 API，只要 `claude` 命令可用即可。

### Q3: 记忆压缩会额外消耗 API 调用吗？

**A: 会，但很少。**

只有当记忆文件超过大小限制时才会触发压缩：
- session.md > 20KB
- context.md > 30KB
- knowledge_base.md > 25KB

通常 10 轮任务可能只触发 0-3 次压缩。

### Q4: 可以禁用记忆压缩吗？

**A: 可以，但不推荐。**

如果你想禁用压缩，可以修改 `memory_store.py` 中的大小限制：

```python
# memory_store.py
MAX_SESSION_SIZE = 999999999  # 设置为很大的值，实际上禁用压缩
MAX_CONTEXT_SIZE = 999999999
MAX_KNOWLEDGE_SIZE = 999999999
```

但这会导致记忆文件无限增长，影响性能。

### Q5: 如何查看 claude 命令的配置？

```bash
# 查看 claude 配置文件位置
ls ~/.claude/

# 查看配置（如果存在）
cat ~/.claude/config.json
```

---

## 性能说明

### API 调用统计（10 轮任务示例）

| 场景 | 调用次数 | 说明 |
|------|---------|------|
| 主任务执行 | 10 次 | 每轮都调用 |
| 记忆压缩 | 0-3 次 | 只在文件超过限制时调用 |
| **总计** | **10-13 次** | 都使用 `claude` 命令 |

### 成本估算

假设你的 `claude` 命令使用 MiniMax 2.7 API：
- 主任务：10 次 × 每次成本
- 压缩：0-3 次 × 每次成本（通常更少）

**记忆压缩的额外成本很低（约 0-30% 的主任务成本）。**

---

## 总结

### ✅ 你需要做的

1. 确保 `claude` 命令可用
2. 安装 Python 依赖
3. 运行 kuxing

### ❌ 你不需要做的

1. ~~配置 ANTHROPIC_API_KEY~~
2. ~~配置额外的 API~~
3. ~~修改环境变量~~

### 🎯 核心理念

**Kuxing 是 Claude Code 的增强工具，直接使用你的 `claude` 命令配置，无需额外设置。**

---

**版本**：v0.5.0  
**更新日期**：2026-04-03  
**作者**：Claude (Sonnet 4.6)
