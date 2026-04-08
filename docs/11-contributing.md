# 贡献指南

本文档面向希望为苦行僧项目贡献代码、文档或提出建议的开发者。

---

## 1. 项目结构

```
kuxing/
├── cli.py                 # 主入口，命令行接口
├── scheduler.py           # 任务调度器核心
├── memory_store.py        # 记忆存储管理器
├── session_memory.py      # 会话记忆（结构化 session.md）
├── memory_updater.py      # 记忆自动更新器
├── llm_compressor.py      # LLM 上下文压缩器
├── claude_invoker.py      # Claude API 调用器
├── config_schema.py       # 配置 schema 验证
├── prompts.py             # Prompt 模板管理
├── state.py               # 状态管理
├── task_queue.py          # 任务队列管理
├── verify_v0.5.0.py      # v0.5.0 验证脚本
├── docs/                  # 项目文档
│   └── images/            # 文档图表（PlantUML 源文件）
├── examples/              # 示例配置
├── memory/                # 记忆存储目录（运行时生成）
│   └── <project-slug>/    # 按项目分组的记忆
├── shared_context/        # 全局共享记忆目录
└── tests/                 # 测试文件
    ├── conftest.py
    ├── test_memory_store.py
    ├── test_memory_updater.py
    ├── test_prompts.py
    ├── test_scheduler.py
    ├── test_session_memory.py
    └── test_task_queue.py
```

**注意**：`memory/` 目录是运行时生成的记忆存储，不是 Python 模块。核心记忆模块以单个文件形式存在于项目根目录。

---

## 2. 开发环境搭建

### 2.1 环境要求

- Python 3.8+
- Claude CLI 已安装并配置

### 2.2 安装开发依赖

```bash
# 克隆项目
git clone <repo-url>
cd kuxing

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

### 2.3 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_memory_updater.py -v

# 生成覆盖率报告
python -m pytest tests/ --cov=. --cov-report=html
```

---

## 3. 代码规范

### 3.1 Python 代码风格

项目遵循 PEP 8 规范，使用以下规则：

| 规则 | 说明 |
|------|------|
| 缩进 | 4 空格 |
| 行长度 | ≤ 100 字符 |
| 命名 | 小写下划线（变量/函数），大驼峰（类） |
| 导入 | 标准库 → 第三方库 → 本地模块 |

### 3.2 文档字符串

使用 Google 风格的文档字符串：

```python
def function_name(param1: str, param2: int) -> bool:
    """简短描述函数功能。

    更详细的说明（如果需要）。

    Args:
        param1: 参数1的说明
        param2: 参数2的说明

    Returns:
        返回值的说明

    Raises:
        ValueError: 何时抛出此异常

    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

### 3.3 提交信息格式

使用 Conventional Commits 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**类型（type）**：

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | 修复 Bug |
| docs | 文档变更 |
| refactor | 重构（不改变功能） |
| test | 测试相关 |
| chore | 构建/工具变更 |
| perf | 性能优化 |

**示例**：

```
feat(scheduler): 添加循环模式超时检测

- 新增 max_loop_duration 配置项
- 超出设定时间后自动终止循环

Closes: #123
```

---

## 4. 分支策略

### 4.1 分支命名

| 分支类型 | 命名格式 | 示例 |
|---------|---------|------|
| 功能分支 | feature/<描述> | feature/memory-compression |
| 修复分支 | fix/<描述> | fix/context-overflow |
| 文档分支 | docs/<描述> | docs/add-api-reference |
| 发布分支 | release/<版本> | release/v0.5.0 |

### 4.2 工作流程

```
1. 从 master 创建功能分支
   git checkout -b feature/new-feature

2. 开发并提交
   git add .
   git commit -m "feat(scope): description"

3. 推送分支
   git push origin feature/new-feature

4. 创建 Pull Request / Merge Request

5. 代码审查通过后合并
```

---

## 5. 测试要求

### 5.1 测试覆盖率

- 核心模块覆盖率 ≥ 80%
- 新功能必须包含测试
- Bug 修复必须包含回归测试

### 5.2 测试命名

```
test_<模块>_<功能>_<场景>
```

**示例**：

```python
def test_memory_updater_compress_large_session():
    """测试会话记忆压缩功能 - 大会话场景"""
    pass

def test_scheduler_loop_mode_timeout():
    """测试调度器循环模式 - 超时场景"""
    pass
```

### 5.3 测试结构

使用 Arrange-Act-Assert 模式：

```python
def test_example():
    # Arrange - 准备测试数据
    config = {"max_rounds": 5}
    scheduler = Scheduler(config)

    # Act - 执行被测操作
    result = scheduler.run()

    # Assert - 验证结果
    assert result.status == "completed"
    assert result.rounds == 5
```

---

## 6. 文档贡献

### 6.1 文档类型

| 文档 | 说明 | 位置 |
|------|------|------|
| 入门指南 | 安装和快速开始 | docs/02-installation.md, docs/03-quick-start.md |
| 用户文档 | 命令和配置参考 | docs/04-commands.md, docs/05-config-guide.md |
| 架构文档 | 设计和实现细节 | docs/06-scheduler-architecture.md, docs/07-memory-architecture.md |
| 运维文档 | 故障排除和最佳实践 | docs/08-troubleshooting.md, docs/09-examples.md, docs/10-best-practices.md |

### 6.2 文档更新

更新文档时请：

1. 确保内容与代码实现一致
2. 更新文档顶部的"最后更新"日期
3. 如有图表变更，同步更新 `.puml` 源文件
4. 运行文档中的示例命令验证正确性

---

## 7. 问题反馈

### 7.1 Bug 报告

提交 Bug 报告时请包含：

- **问题描述**：清晰描述问题
- **复现步骤**：如何重现问题
- **预期行为**：应该发生什么
- **实际行为**：实际发生了什么
- **环境信息**：Python 版本、操作系统、CLI 版本等
- **日志输出**：相关日志或错误信息

### 7.2 功能请求

提交功能请求时请包含：

- **使用场景**：为什么需要此功能
- **建议方案**：你期望的实现方式
- **替代方案**：你是否考虑过其他方案

### 7.3 模板

```markdown
## Bug 报告模板

**问题描述**：
[清晰描述问题]

**复现步骤**：
1.
2.
3.

**预期行为**：
[描述应该发生什么]

**实际行为**：
[描述实际发生了什么]

**环境信息**：
- OS:
- Python:
- CLI:

**日志**：
```
[粘贴日志]
```
```

---

## 8. 代码审查

### 8.1 审查要点

审查代码时请关注：

- **功能正确性**：代码是否解决了问题
- **代码质量**：是否清晰、可维护
- **测试覆盖**：是否有足够的测试
- **文档更新**：是否同步更新了文档
- **边界条件**：是否处理了边界情况
- **错误处理**：是否有适当的错误处理

### 8.2 审查级别

| 级别 | 说明 | 要求 |
|------|------|------|
| CRITICAL | 安全漏洞、严重 Bug | 必须修复 |
| HIGH | 质量问题、性能问题 | 应该修复 |
| MEDIUM | 代码风格、文档缺失 | 建议修复 |
| LOW | 小的改进建议 | 可以修复 |

---

## 9. 发布流程

### 9.1 版本号规则

遵循语义化版本（SemVer）：

- **MAJOR**：破坏性变更
- **MINOR**：新增功能（向后兼容）
- **PATCH**：Bug 修复（向后兼容）

### 9.2 发布步骤

1. 更新版本号（如有变更）
2. 更新 CHANGELOG.md
3. 创建发布标签
4. 构建发布包
5. 发布到相应平台

---

## 10. 联系方式

- **IssueTracker**: https://github.com/<user>/kuxing/issues
- **讨论群**: [待添加]

---

## 附录 A：常用命令

```bash
# 安装开发版本
pip install -e ".[dev]"

# 运行测试
python -m pytest tests/ -v

# 代码格式化
black .

# 静态检查
mypy .

# 运行文档服务器（预览）
mkdocs serve
```

---

**最后更新**: 2026-04-07
