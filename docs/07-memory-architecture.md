# 记忆架构

## 1. 概述

kuxing 的记忆系统采用分层设计，支持多轮任务执行时的上下文持久化和智能传递。v0.5.0 引入了结构化会话记忆和 MEMORY.md 索引系统，进一步提升了记忆管理的可维护性。

### 核心特性

- **分层记忆**：项目私有 / 全局共享 / 知识沉淀三层分离
- **结构化会话记忆**：10 个标准化 section 跟踪执行状态
- **记忆索引**：MEMORY.md 快速定位相关记忆
- **自动压缩**：LLM 智能压缩防止记忆膨胀
- **环境变量**：支持 `${VAR_NAME}` 语法

---

## 2. 分层记忆系统

### 2.1 记忆层次架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      分层记忆系统                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  高优先级 ◄─────────────────────────────────────────────────► 低 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Level 1: 项目私有记忆 (memory/{project}/context.md)    │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  用途：项目特定的代码路径、配置、已知问题                 │    │
│  │                                                         │    │
│  │  内容：                                                 │    │
│  │  ├─ SDK 路径配置                                        │    │
│  │  ├─ 参考文档路径                                         │    │
│  │  ├─ 项目特定信息                                        │    │
│  │  └─ 已知问题和特殊处理                                   │    │
│  │                                                         │    │
│  │  优先级：★★★☆☆ (最高)                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Level 2: 会话记忆 (memory/{project}/session.md)      │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  用途：跟踪当前执行状态，下一步计划                       │    │
│  │                                                         │    │
│  │  内容（10 个 section）：                                │    │
│  │  ├─ 执行标题                                           │    │
│  │  ├─ 当前状态 ←─── 每轮更新                              │    │
│  │  ├─ 任务规格                                           │    │
│  │  ├─ 关键文件 ←─── 自动添加                              │    │
│  │  ├─ 工作流程                                           │    │
│  │  ├─ 错误与修正 ←─── 遇错时更新                          │    │
│  │  ├─ 代码库文档                                         │    │
│  │  ├─ 学习总结 ←─── 自动提取                              │    │
│  │  ├─ 关键结果                                           │    │
│  │  └─ 工作日志 ←─── 每轮追加                              │    │
│  │                                                         │    │
│  │  优先级：★★★☆☆ (高)                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Level 3: 全局共享记忆 (shared_context/context.md)      │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  用途：跨项目共享的配置和信息                             │    │
│  │                                                         │    │
│  │  内容：                                                 │    │
│  │  ├─ SDK 路径 (${ANDROID_SDK_HOME})                     │    │
│  │  ├─ 账号配置 (${HARBOR_USERNAME})                        │    │
│  │  └─ 跨项目共享信息                                       │    │
│  │                                                         │    │
│  │  优先级：★★☆☆☆ (中)                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Level 4: 轮次记忆 (rounds/round_*.json)               │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  用途：每轮输入输出的完整记录                             │    │
│  │                                                         │    │
│  │  内容：                                                 │    │
│  │  ├─ 轮次号和时间戳                                      │    │
│  │  ├─ 任务描述                                            │    │
│  │  ├─ 输入上下文                                          │    │
│  │  ├─ Claude 调用记录                                      │    │
│  │  └─ 执行结果                                            │    │
│  │                                                         │    │
│  │  优先级：★☆☆☆☆ (低，但详细)                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Level 5: 知识沉淀 (knowledge_base.md)                 │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  用途：历史发现、最佳实践、避坑指南                       │    │
│  │                                                         │    │
│  │  内容：                                                 │    │
│  │  ├─ 历史发现                                            │    │
│  │  ├─ 最佳实践                                           │    │
│  │  ├─ 避坑指南                                            │    │
│  │  └─ 经验总结                                            │    │
│  │                                                         │    │
│  │  优先级：☆☆☆☆☆ (最低)                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 记忆文件位置

```
kuxing/
├── shared_context/                    # 全局共享记忆（项目内）
│   └── context.md                    # 全局配置和共享信息
│
├── memory/                           # 运行时记忆目录
│   └── {project_slug}/
│       ├── config.yaml               # 项目配置
│       ├── state.json                # 调度器状态
│       ├── context.md                # 项目私有记忆
│       ├── session.md                # 会话记忆 (v0.5.0)
│       ├── knowledge_base.md         # 知识沉淀
│       ├── MEMORY.md                 # 记忆索引 (v0.5.0)
│       │
│       └── rounds/                   # 轮次记忆
│           ├── round_0001.json       # 第 1 轮
│           ├── round_0002.json       # 第 2 轮
│           └── ...
```

---

## 3. MEMORY.md 索引系统 (v0.5.0)

### 3.1 索引文件格式

```markdown
# 项目记忆索引

最后更新：2026-04-03 17:30:00

---

## 会话记忆
- [当前会话](session.md) — Round 3，正在执行文档编写

## 项目背景
- [项目信息](context.md) — 代码路径、文档路径、SDK 配置

## 知识沉淀
- [历史经验](knowledge_base.md) — 最佳实践、避坑指南

---

**使用说明**：
- 每次执行前，先读取此索引文件
- 根据任务需要，按需加载相关记忆文件
- 新增记忆时，同步更新此索引
```

### 3.2 索引更新流程

**实际索引文件示例**：

```markdown
# 项目记忆索引

最后更新：2026-04-03 17:30:00

---

## 会话记忆
- [当前会话](session.md) — Round 3，正在执行文档编写

## 项目背景
- [项目信息](context.md) — 代码路径、文档路径、SDK 配置
- [kuxing 调度器](memory/kuxing/session.md) — v0.5.0 核心流程

## 知识沉淀
- [历史经验](knowledge_base.md) — 最佳实践、避坑指南

---

**使用说明**：
- 每次执行前，先读取此索引文件
- 根据任务需要，按需加载相关记忆文件
- 新增记忆时，同步更新此索引
```

**代码中的索引更新**：

```python
# 初始化时自动创建索引
memory_store.create_memory_index()

# 会话开始时更新索引
memory_store.update_memory_index(
    section="会话记忆",
    title=f"Round {round_num}",
    filename="session.md",
    description=f"Round {round_num} 执行状态"
)

# 新增关键文件时更新索引
memory_store.update_memory_index(
    section="项目背景",
    title="新增文件",
    filename="session.md",
    description="更新了关键文件列表"
)
```

```
┌─────────────────────────────────────────────────────────────────┐
│                      索引更新流程 (v0.5.0)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  场景 1: 初始化项目                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Scheduler.initialize()                                 │    │
│  │      │                                                  │    │
│  │      ▼                                                  │    │
│  │  MemoryStore.create_memory_index()                     │    │
│  │      │                                                  │    │
│  │      ▼                                                  │    │
│  │  创建初始索引文件，包含所有记忆文件的引用               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  场景 2: 会话开始时                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  SessionMemory.initialize()                             │    │
│  │      │                                                  │    │
│  │      ▼                                                  │    │
│  │  MemoryStore.update_memory_index()                      │    │
│  │      │                                                  │    │
│  │      ▼                                                  │    │
│  │  更新"会话记忆" section，添加/更新当前会话条目          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  场景 3: 记忆文件更新时                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  MemoryUpdater / SessionMemory 自动更新                  │    │
│  │      │                                                  │    │
│  │      ▼                                                  │    │
│  │  业务逻辑完成后自动更新索引（如果需要）                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 结构化会话记忆 (v0.5.0)

### 4.1 SessionMemory 模板

```markdown
# 执行标题
_{task_name} - Round {round_num}_

# 当前状态
_正在执行什么？待完成的任务？下一步计划？_


# 任务规格
_用户要求做什么？设计决策？关键约束？_


# 关键文件
_重要文件及其作用（文件路径:行号 格式）_


# 工作流程
_执行的命令及顺序，如何解释输出_


# 错误与修正
_遇到的错误及解决方法，失败的尝试_


# 代码库文档
_重要系统组件，如何协同工作_


# 学习总结
_什么有效？什么无效？应避免什么？_


# 关键结果
_如果用户要求特定输出，在此记录完整结果_


# 工作日志
_逐步执行摘要（时间戳 + 简短描述）_
```

### 4.2 Section 说明

| Section | 用途 | 更新频率 | 更新方式 |
|---------|------|----------|----------|
| **执行标题** | 任务名 + 轮次 | 每轮 | 自动更新轮次号 |
| **当前状态** | 执行进度 + 下一步 | 每轮 | 自动从结果提取 |
| **任务规格** | 用户原始需求 | 初始化时 | 手动/自动 |
| **关键文件** | 相关文件列表 | 遇新文件时 | 自动添加 |
| **工作流程** | 执行步骤 | 执行命令时 | 自动追加 |
| **错误与修正** | 错误记录 | 遇错误时 | 自动添加 |
| **代码库文档** | 系统理解 | 理解系统时 | 手动添加 |
| **学习总结** | 经验记录 | 学到经验时 | 自动提取 |
| **关键结果** | 最终输出 | 任务完成时 | 手动添加 |
| **工作日志** | 详细日志 | 每轮 | 自动追加 |

### 4.3 实际会话记忆示例

**Round 1 初始化后**：

```markdown
# 执行标题
_文档整理 - Round 1_

# 当前状态
_正在执行什么？待完成的任务？下一步计划？_

# 任务规格
完善 kuxing 项目文档，包括：
- 项目概览 (01-overview.md)
- 安装指南 (02-installation.md)
- 快速开始 (03-quick-start.md)
```

**Round 3 执行后**：

```markdown
# 执行标题
_文档整理 - Round 3_

# 当前状态
**上一轮完成**：
完成了 docs/02-installation.md 和 docs/03-quick-start.md

**下一步计划**：
继续完善 docs/04-commands.md 和 docs/05-config-guide.md

**更新时间**：2026-04-03 15:30:00

# 任务规格
完善 kuxing 项目文档，包括：
- 项目概览 (01-overview.md) ✅
- 安装指南 (02-installation.md) ✅
- 快速开始 (03-quick-start.md) ✅
- 命令参考 (04-commands.md) 🔄 进行中

# 关键文件
- `docs/01-overview.md` — 项目概览 (已完善)
- `docs/02-installation.md` — 安装指南 (已完善)
- `docs/03-quick-start.md` — 快速开始 (已完善)
- `docs/04-commands.md` — 命令参考 (编辑中)

# 工作流程
- [10:00] `python cli.py --config examples/write_docs.yaml run`
- [10:15] 更新 01-overview.md
- [10:30] 创建 02-installation.md
- [11:00] 创建 03-quick-start.md
- [11:30] 开始 04-commands.md

# 错误与修正
**错误**：plantuml 命令未找到
**解决方法**：已添加到系统 PATH

# 学习总结
- **有效方法**：每轮执行后自动更新 session.md
- **应避免**：过长的单次执行，应拆分成多轮

# 关键结果
_

# 工作日志
- [2026-04-03 10:00] Round 1: 开始文档整理
- [2026-04-03 10:30] Round 2: 完成 02, 03 文档
- [2026-04-03 11:30] Round 3: 开始 04 文档
```

---

## 5. LLM 压缩机制 (v0.5.0)

### 5.1 压缩触发条件

| 文件 | 大小限制 | 压缩策略 |
|------|----------|----------|
| `session.md` | 20,000 字符 | 保留当前状态，压缩日志和错误 |
| `context.md` | 30,000 字符 | 去重，保留最新信息 |
| `knowledge_base.md` | 25,000 字符 | 保留最佳实践，删除过时经验 |

**实际使用示例**：

```python
# 每轮执行后自动检查
compressor = LLMCompressor()
memory_store.check_and_compress_if_needed(compressor)

# 输出示例：
# ⚠️ session.md 超出限制 (24567 > 20000)，开始压缩...
# ✅ 压缩完成：24567 → 19850 (19.2% 减少)
```

### 5.2 简单截断策略（无 LLM 时）

当 `compressor=None` 时，使用简单的截断策略：

```python
def _simple_truncate(self, content: str, target_size: int) -> str:
    """简单截断（保留前面部分）"""
    if len(content) <= target_size:
        return content

    # 在 section 边界截断
    lines = content.split('\n')
    truncated_lines = []
    current_size = 0

    for line in lines:
        if current_size + len(line) + 1 > target_size:
            break
        truncated_lines.append(line)
        current_size += len(line) + 1

    truncated = '\n'.join(truncated_lines)
    truncated += '\n\n[... 内容已截断，已压缩到目标大小 ...]'

    return truncated
```

### 5.3 压缩流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM 压缩流程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  每轮执行完成后                                                  │
│        │                                                         │
│        ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  MemoryStore.check_and_compress_if_needed()            │    │
│  │  ├─ 检查 session.md 大小                               │    │
│  │  ├─ 检查 context.md 大小                               │    │
│  │  └─ 检查 knowledge_base.md 大小                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│        │                                                         │
│        ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  if file_size > MAX_SIZE:                              │    │
│  │      │                                                  │    │
│  │      ▼                                                  │    │
│  │  LLMCompressor.compress_memory()                       │    │
│  │      │                                                  │    │
│  │      ├─ 构建压缩 Prompt                                  │    │
│  │      │                                                  │    │
│  │      ├─ 调用 Claude API                                  │    │
│  │      │                                                  │    │
│  │      ├─ 提取压缩结果                                      │    │
│  │      │                                                  │    │
│  │      └─ 验证压缩大小                                      │    │
│  │                                                         │    │
│  │  else:                                                  │    │
│  │      不压缩                                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 压缩策略

**session.md 压缩策略**：
1. 保留"当前状态"和"下一步计划"（最重要）
2. 压缩"工作日志"：只保留最近 10 条
3. 压缩"错误与修正"：只保留未解决的和最近的
4. 合并"关键文件"：去重，只保留文件路径和简短说明
5. 删除过时的"学习总结"

**context.md 压缩策略**：
1. 合并相同类型的 section
2. 去重：相同的路径、命令只保留一次
3. 时间优先：保留最近的信息，删除旧的重复信息
4. 保留关键信息：路径、命令、账号信息必须保留

---

## 6. 自动记忆更新

### 6.1 MemoryUpdater

```python
class MemoryUpdater:
    """自动从执行结果中提取信息并更新记忆"""

    def update_from_result(self, result: dict):
        """从 <result> 标签中提取信息并更新记忆"""
        # 提取文件路径
        files_modified = result.get('files_modified', [])
        files_created = result.get('files_created', [])

        # 更新 context.md
        for file_path in files_modified:
            self._add_to_context(f"修改文件: {file_path}")

        for file_path in files_created:
            self._add_to_context(f"新创建: {file_path}")

        # 提取命令
        if 'command' in result:
            self._add_to_context(f"执行命令: {result['command']}")

        # 提取错误
        if 'error' in result:
            self._add_to_knowledge(f"错误: {result['error']}")
```

### 6.2 SessionMemory 自动提取

```python
class SessionMemory:
    """结构化会话记忆自动提取"""

    def extract_from_result(self, result: dict, round_num: int):
        """从执行结果中自动提取信息"""
        # 更新轮次号
        self.update_round_number(round_num)

        # 更新当前状态
        summary = result.get('summary', '')
        next_hints = result.get('next_hints', '')
        self.update_current_state(summary, next_hints)

        # 添加修改的文件
        for file_path in result.get('files_modified', []):
            self.add_key_file(file_path, "已修改")

        for file_path in result.get('files_created', []):
            self.add_key_file(file_path, "新创建")

        # 添加工作日志
        self.add_worklog(summary[:100])

        # 如果有错误，记录
        if 'error' in summary.lower():
            self.add_error(summary)
```

---

## 7. 环境变量支持

### 7.1 `${VAR_NAME}` 语法

在记忆文件中使用环境变量：

```markdown
# context.md 示例

## SDK 路径
- Android SDK: ${ANDROID_SDK_HOME}
- NDK: ${ANDROID_NDK_HOME}
- Python: ${PYTHON_PATH}

## 账号配置
- Harbor 用户: ${HARBOR_USERNAME}
- GitLab Token: ${GITLAB_TOKEN}
```

### 7.2 环境变量解析

```python
def resolve_env_vars(self, content: str) -> str:
    """替换 ${VAR_NAME} 为环境变量值"""
    pattern = r'\$\{([^}]+)\}'

    def replace_var(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is not None:
            return value
        return f"${{{var_name}}}"  # 保留未定义的变量

    return re.sub(pattern, replace_var, content)
```

---

## 8. 记忆生命周期

### 8.1 文件创建顺序

```
1. 创建项目时
   ├─ memory/{project}/config.yaml     # 配置文件
   ├─ memory/{project}/state.json     # 初始状态
   └─ memory/{project}/MEMORY.md      # 索引文件 (v0.5.0)

2. 首轮执行前
   ├─ memory/{project}/context.md     # 项目记忆
   ├─ memory/{project}/session.md     # 会话记忆 (v0.5.0)
   └─ memory/{project}/knowledge_base.md  # 知识沉淀

3. 每轮执行后
   └─ memory/{project}/rounds/round_*.json  # 轮次记忆
```

### 8.2 记忆清理

| 操作 | 影响范围 | 说明 |
|------|----------|------|
| `reset --confirm` | rounds/ | 清空轮次记忆，保留其他文件 |
| `clear-all` | memory/{project}/ | 删除整个项目记忆目录 |
| 自动压缩 | session/context/knowledge | 保持文件大小在限制内 |

---

## 9. MEMORY.md 与调度器集成 (v0.5.0)

### 9.1 调度器中的索引操作

```
┌─────────────────────────────────────────────────────────────────┐
│                 MEMORY.md 索引操作序列                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 初始化 (Scheduler.initialize)                               │
│     └─► MemoryStore.create_memory_index()                      │
│         └─► 创建初始 MEMORY.md 文件                            │
│                                                                 │
│  2. 会话开始 (SessionMemory.initialize)                         │
│     └─► MemoryStore.update_memory_index()                      │
│         └─► 添加"会话记忆" section 条目                         │
│                                                                 │
│  3. 每轮执行前 (Scheduler.build_prompt)                         │
│     └─► MemoryStore.get_full_context()                         │
│         ├─► 读取 MEMORY.md 定位记忆文件                         │
│         └─► 加载需要的记忆内容                                  │
│                                                                 │
│  4. 每轮执行后 (Scheduler.save_round)                           │
│     └─► SessionMemory.extract_from_result()                     │
│         └─► 更新 session.md 后自动更新 MEMORY.md               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 索引与记忆的关系

```
┌─────────────────────────────────────────────────────────────────┐
│                  MEMORY.md 索引与记忆文件关系                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MEMORY.md (索引文件)                                            │
│  ├── 会话记忆 ──────► session.md (10 个 section)               │
│  ├── 项目背景 ──────► context.md (项目私有记忆)                  │
│  ├── 全局共享 ──────► shared_context/context.md                 │
│  └── 知识沉淀 ──────► knowledge_base.md (历史经验)              │
│                                                                 │
│  每轮调用 get_full_context() 时：                                │
│  1. 读取 MEMORY.md 获取索引                                     │
│  2. 按需加载各记忆文件                                           │
│  3. 组装成完整上下文                                            │
│                                                                 │
│  优点：                                                          │
│  ├─ 无需读取全部文件，按需加载                                   │
│  ├─ 快速定位特定类型的记忆                                       │
│  └─ 索引本身可快速了解项目状态                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 实际工作流程

```python
# 1. 项目初始化
scheduler = Scheduler(config)
scheduler.initialize()
# → 创建 MEMORY.md 索引文件

# 2. 会话开始
session_memory = SessionMemory(project_slug)
session_memory.initialize(task_name)
# → 更新 MEMORY.md，添加"会话记忆"条目

# 3. 每轮执行
context = memory_store.get_full_context()
# → 读取 MEMORY.md，按需加载 context.md, session.md 等

# 4. 每轮完成后
session_memory.extract_from_result(result, round_num)
# → 更新 session.md 的同时，MEMORY.md 中相关描述自动更新
```

---

**最后更新**：2026-04-03
**版本**：v0.5.0
