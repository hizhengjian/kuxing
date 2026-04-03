# Claude Code 记忆系统分析与 kuxing 改进建议

## 日期
2026-04-03

## 概述

本文档分析 Claude Code 的记忆系统实现，并提出 kuxing 项目可以借鉴的改进方向。

---

## Claude Code 记忆系统核心特性

### 1. 多层次记忆架构

```
~/.claude/
├── projects/<项目哈希>/
│   └── memory/              # 项目级记忆
│       ├── MEMORY.md        # 记忆索引（自动加载）
│       ├── user_*.md        # 用户偏好
│       ├── feedback_*.md    # 工作方式反馈
│       ├── project_*.md     # 项目上下文
│       └── reference_*.md   # 外部资源指针
└── memory/                  # 全局记忆（跨项目）
    ├── MEMORY.md
    └── *.md
```

**与 kuxing 对比**：
- ✅ kuxing 已有三层记忆：全局共享、项目私有、知识沉淀
- ✅ kuxing 已将全局记忆移到项目内（v0.3.0）
- ⚠️ kuxing 缺少记忆索引文件（MEMORY.md）
- ⚠️ kuxing 缺少记忆类型分类（user/feedback/project/reference）

### 2. 记忆文件格式（YAML Frontmatter + Markdown）

```markdown
---
name: 用户是高级 Go 工程师
description: 用户有 10 年 Go 经验，对前端不熟悉
type: user
---

用户有 10 年 Go 开发经验，在当前项目中第一次接触前端 React 代码。
解释前端概念时应使用 Go 的类比。
```

**与 kuxing 对比**：
- ❌ kuxing 当前使用纯 Markdown，无结构化元数据
- ❌ kuxing 无法快速检索特定类型的记忆
- ❌ kuxing 无法根据 description 判断记忆相关性

### 3. 会话记忆（Session Memory）

**核心机制**：
- 使用 **forked subagent** 在后台自动提取会话信息
- 不中断主对话流程
- 定期更新会话记忆文件

**会话记忆模板结构**：
```markdown
# Session Title
_5-10 word descriptive title_

# Current State
_What is actively being worked on right now?_

# Task specification
_What did the user ask to build?_

# Files and Functions
_Important files and their purpose_

# Workflow
_Bash commands and their order_

# Errors & Corrections
_Errors encountered and fixes_

# Codebase and System Documentation
_Important system components_

# Learnings
_What worked well? What to avoid?_

# Key results
_Exact output if user asked for specific result_

# Worklog
_Step by step summary_
```

**触发条件**：
```typescript
shouldExtractMemory(messages: Message[]): boolean {
  // 1. 初始化阈值：达到一定 token 数后开始提取
  if (!isSessionMemoryInitialized()) {
    if (!hasMetInitializationThreshold(currentTokenCount)) {
      return false
    }
  }
  
  // 2. 更新阈值：同时满足 token 增长 AND 工具调用次数
  const hasMetTokenThreshold = hasMetUpdateThreshold(currentTokenCount)
  const hasMetToolCallThreshold = toolCallsSinceLastUpdate >= threshold
  
  // 3. 安全时机：最后一轮没有工具调用（自然对话间隙）
  const hasToolCallsInLastTurn = hasToolCallsInLastAssistantTurn(messages)
  
  return (hasMetTokenThreshold && hasMetToolCallThreshold) ||
         (hasMetTokenThreshold && !hasToolCallsInLastTurn)
}
```

**与 kuxing 对比**：
- ❌ kuxing 无会话记忆概念
- ❌ kuxing 只在每轮执行后提取，无法捕获对话中的上下文
- ❌ kuxing 无结构化的会话状态跟踪

### 4. 自动记忆提取（Forked Subagent）

**工作流程**：
```
主对话进行中
    │
    ▼
后台检测：shouldExtractMemory() == true
    │
    ▼
Fork 子 Agent（不阻塞主对话）
    │
    ├── 读取当前会话记忆文件
    ├── 分析最近的对话内容
    ├── 使用 Edit 工具更新记忆文件
    └── 完成后静默返回
    │
    ▼
主对话继续（用户无感知）
```

**关键代码**：
```typescript
// 使用 forked agent 提取记忆
const result = await runForkedAgent({
  systemPrompt: buildSessionMemoryUpdatePrompt(currentNotes, notesPath),
  messages: recentMessages,
  tools: [FileEditTool],
  // ... 其他配置
})
```

**与 kuxing 对比**：
- ❌ kuxing 使用简单的正则表达式提取（`_extract_paths()`, `_extract_commands()`）
- ❌ kuxing 无法理解语义，只能匹配模式
- ❌ kuxing 无法提取复杂的上下文信息

### 5. 记忆大小控制

**限制**：
- 每个 section 最多 2000 tokens
- 总记忆文件最多 12000 tokens
- 超出时自动压缩旧内容

**压缩策略**：
```typescript
// 分析每个 section 的大小
const sectionSizes = analyzeSectionSizes(content)
const totalTokens = roughTokenCountEstimation(content)

// 生成压缩提示
if (totalTokens > MAX_TOTAL_SESSION_MEMORY_TOKENS) {
  prompt += `CRITICAL: The session memory file is currently ~${totalTokens} tokens, 
             which exceeds the maximum of ${MAX_TOTAL_SESSION_MEMORY_TOKENS} tokens. 
             You MUST condense the file to fit within this budget.`
}
```

**与 kuxing 对比**：
- ❌ kuxing 无记忆大小限制
- ❌ kuxing 记忆文件可能无限增长
- ❌ kuxing 无自动压缩机制

### 6. 记忆与上下文压缩的集成

**关键特性**：
- 上下文压缩时，记忆内容不丢失
- 记忆跨越压缩边界持续存在
- 压缩后的摘要 + 记忆 = 完整上下文

```
完整压缩触发
    │
    ▼
读取所有记忆文件内容
    │
    ▼
将记忆 + 对话摘要一起生成新的上下文
    │
    ▼
记忆跨越压缩边界持续存在
```

**与 kuxing 对比**：
- ✅ kuxing 记忆文件独立于执行状态，天然持久化
- ⚠️ kuxing 无上下文压缩机制（因为是多轮独立执行）

---

## kuxing 可以借鉴的改进

### 改进 1：引入记忆索引文件（MEMORY.md）

**目标**：快速定位和加载相关记忆

**实现**：
```markdown
# 项目记忆索引

## 用户偏好
- [用户角色](user_role.md) — C++ 专家，嵌入式开发
- [工作习惯](user_preferences.md) — 喜欢详细注释，使用中文文档

## 项目上下文
- [项目背景](project_background.md) — RK3588 视频处理系统
- [关键路径](project_paths.md) — 代码、文档、配置文件路径
- [账号信息](project_credentials.md) — GitLab、Harbor 账号

## 工作反馈
- [测试策略](feedback_testing.md) — 不要 mock 硬件，使用真实设备测试
- [代码风格](feedback_style.md) — 函数不超过 50 行，使用 clang-format

## 外部资源
- [文档位置](reference_docs.md) — 技术文档在 Confluence
- [问题追踪](reference_issues.md) — Bug 在 Jira PROJ-123
```

**修改文件**：
- `memory_store.py`：添加 `create_memory_index()` 方法
- `scheduler.py`：启动时加载 MEMORY.md

### 改进 2：记忆文件使用 YAML Frontmatter

**目标**：结构化元数据，便于检索和过滤

**实现**：
```python
# memory_store.py

def write_memory_with_metadata(self, filename: str, name: str, 
                                description: str, memory_type: str, 
                                content: str):
    """写入带元数据的记忆文件"""
    frontmatter = f"""---
name: {name}
description: {description}
type: {memory_type}
created_at: {datetime.now().isoformat()}
---

{content}
"""
    filepath = self.memory_dir / filename
    filepath.write_text(frontmatter, encoding='utf-8')

def load_memory_by_type(self, memory_type: str) -> List[Dict]:
    """按类型加载记忆"""
    memories = []
    for file in self.memory_dir.glob('*.md'):
        if file.name == 'MEMORY.md':
            continue
        content = file.read_text(encoding='utf-8')
        # 解析 YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1])
                if metadata.get('type') == memory_type:
                    memories.append({
                        'metadata': metadata,
                        'content': parts[2].strip()
                    })
    return memories
```

### 改进 3：引入会话记忆（Session Memory）

**目标**：跟踪每轮执行的详细状态

**实现**：
```python
# session_memory.py (新文件)

class SessionMemory:
    """会话记忆管理"""
    
    TEMPLATE = """# 执行标题
_{task_name} - Round {round_num}_

# 当前状态
_正在执行什么？待完成的任务？下一步计划？_

# 任务规格
_用户要求做什么？设计决策？_

# 关键文件
_重要文件及其作用_

# 工作流程
_执行的命令及顺序_

# 错误与修正
_遇到的错误及解决方法_

# 学习总结
_什么有效？什么无效？应避免什么？_

# 关键结果
_如果用户要求特定输出，在此记录_

# 工作日志
_逐步执行摘要_
"""
    
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self.session_file = memory_store.memory_dir / 'session.md'
    
    def initialize_session(self, task_name: str, round_num: int):
        """初始化会话记忆"""
        content = self.TEMPLATE.format(
            task_name=task_name,
            round_num=round_num
        )
        self.session_file.write_text(content, encoding='utf-8')
    
    def update_section(self, section_name: str, new_content: str):
        """更新特定 section"""
        content = self.session_file.read_text(encoding='utf-8')
        # 使用正则表达式替换 section 内容
        pattern = f'(# {section_name}\\n_[^_]+_\\n)(.*?)(\\n# |$)'
        replacement = f'\\1{new_content}\\3'
        updated = re.sub(pattern, replacement, content, flags=re.DOTALL)
        self.session_file.write_text(updated, encoding='utf-8')
    
    def extract_from_result(self, result: dict):
        """从执行结果中提取信息并更新会话记忆"""
        summary = result.get('summary', '')
        
        # 更新"当前状态"
        if 'next_hints' in result:
            self.update_section('当前状态', result['next_hints'])
        
        # 更新"错误与修正"
        if 'error' in summary.lower() or '失败' in summary:
            error_info = self._extract_error(summary)
            if error_info:
                self.append_to_section('错误与修正', f"- {error_info}")
        
        # 更新"工作日志"
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {summary[:100]}"
        self.append_to_section('工作日志', f"- {log_entry}")
```

**集成到 scheduler.py**：
```python
from session_memory import SessionMemory

class Scheduler:
    def __init__(self, ...):
        # ...
        self.session_memory = SessionMemory(self.memory_store)
    
    def _execute_round(self, round_num: int, ...):
        # 初始化会话记忆
        if round_num == 1:
            self.session_memory.initialize_session(
                self.config.project_name, 
                round_num
            )
        
        # 执行任务
        result_dict = self._invoke_claude(...)
        
        # 更新会话记忆
        self.session_memory.extract_from_result(result_dict)
        
        # 原有的记忆更新
        self.memory_updater.update_from_result(result_dict)
```

### 改进 4：使用 LLM 提取记忆（替代正则表达式）

**目标**：理解语义，提取更准确的信息

**实现方案 A：本地小模型**
```python
# llm_memory_extractor.py

from transformers import pipeline

class LLMMemoryExtractor:
    """使用本地 LLM 提取记忆"""
    
    def __init__(self):
        # 使用轻量级模型（如 Qwen-1.8B）
        self.extractor = pipeline(
            "text-generation",
            model="Qwen/Qwen-1_8B-Chat",
            device="cpu"
        )
    
    def extract_paths(self, text: str) -> List[str]:
        """使用 LLM 提取路径"""
        prompt = f"""从以下文本中提取所有文件路径和目录路径：

{text}

请只返回路径列表，每行一个路径："""
        
        response = self.extractor(prompt, max_new_tokens=200)
        paths = response[0]['generated_text'].strip().split('\n')
        return [p.strip() for p in paths if p.strip()]
    
    def extract_commands(self, text: str) -> List[str]:
        """使用 LLM 提取命令"""
        prompt = f"""从以下文本中提取所有执行的命令：

{text}

请只返回命令列表，每行一个命令："""
        
        response = self.extractor(prompt, max_new_tokens=200)
        commands = response[0]['generated_text'].strip().split('\n')
        return [c.strip() for c in commands if c.strip()]
```

**实现方案 B：使用 Claude API（轻量调用）**
```python
# llm_memory_extractor.py

class LLMMemoryExtractor:
    """使用 Claude API 提取记忆"""
    
    def __init__(self, claude_invoker):
        self.claude_invoker = claude_invoker
    
    def extract_structured_info(self, text: str) -> dict:
        """一次性提取所有结构化信息"""
        prompt = f"""分析以下执行结果，提取关键信息：

{text}

请以 JSON 格式返回：
{{
  "paths": ["路径1", "路径2"],
  "commands": ["命令1", "命令2"],
  "errors": ["错误1", "错误2"],
  "key_findings": ["发现1", "发现2"]
}}
"""
        
        # 使用 Haiku 模型（便宜快速）
        response = self.claude_invoker.invoke(
            prompt=prompt,
            model="claude-3-haiku-20240307",
            max_tokens=500
        )
        
        # 解析 JSON
        import json
        try:
            return json.loads(response)
        except:
            return {"paths": [], "commands": [], "errors": [], "key_findings": []}
```

### 改进 5：记忆大小控制

**目标**：防止记忆文件无限增长

**实现**：
```python
# memory_store.py

MAX_MEMORY_SIZE = 50000  # 字符数限制
MAX_SECTION_SIZE = 5000  # 每个 section 限制

def check_and_compress_memory(self):
    """检查并压缩记忆文件"""
    content = self.context_file.read_text(encoding='utf-8')
    
    if len(content) > MAX_MEMORY_SIZE:
        self.logger.warning(f"记忆文件过大 ({len(content)} 字符)，开始压缩...")
        compressed = self._compress_memory(content)
        self.context_file.write_text(compressed, encoding='utf-8')
        self.logger.info(f"压缩完成，新大小: {len(compressed)} 字符")

def _compress_memory(self, content: str) -> str:
    """压缩记忆内容"""
    sections = self._parse_sections(content)
    compressed_sections = []
    
    for section_name, section_content in sections.items():
        if len(section_content) > MAX_SECTION_SIZE:
            # 保留最近的内容，删除旧内容
            lines = section_content.split('\n')
            # 保留最后 50% 的行
            keep_lines = lines[len(lines)//2:]
            compressed_content = '\n'.join(keep_lines)
            compressed_sections.append(f"## {section_name}\n{compressed_content}")
        else:
            compressed_sections.append(f"## {section_name}\n{section_content}")
    
    return '\n\n'.join(compressed_sections)
```

### 改进 6：记忆类型分类

**目标**：按类型组织记忆，便于检索

**实现**：
```python
# memory_types.py

from enum import Enum

class MemoryType(Enum):
    USER = "user"           # 用户偏好、角色、技能
    FEEDBACK = "feedback"   # 工作方式反馈
    PROJECT = "project"     # 项目上下文、背景
    REFERENCE = "reference" # 外部资源指针
    SESSION = "session"     # 会话状态

# memory_store.py

def save_typed_memory(self, memory_type: MemoryType, name: str, 
                      description: str, content: str):
    """保存分类记忆"""
    filename = f"{memory_type.value}_{name.replace(' ', '_')}.md"
    self.write_memory_with_metadata(
        filename=filename,
        name=name,
        description=description,
        memory_type=memory_type.value,
        content=content
    )
    
    # 更新索引
    self._update_memory_index(memory_type, name, filename, description)

def _update_memory_index(self, memory_type: MemoryType, name: str, 
                         filename: str, description: str):
    """更新 MEMORY.md 索引"""
    index_file = self.memory_dir / 'MEMORY.md'
    
    # 读取现有索引
    if index_file.exists():
        content = index_file.read_text(encoding='utf-8')
    else:
        content = "# 项目记忆索引\n\n"
    
    # 按类型分组
    type_section = f"## {memory_type.value.title()}\n"
    if type_section not in content:
        content += f"\n{type_section}\n"
    
    # 添加新条目
    entry = f"- [{name}]({filename}) — {description}\n"
    
    # 插入到对应 section
    # ... (实现细节)
    
    index_file.write_text(content, encoding='utf-8')
```

---

## 实施优先级

### 高优先级（立即实施）

1. **记忆索引文件（MEMORY.md）**
   - 工作量：小
   - 收益：高（快速定位记忆）
   - 实施时间：1-2 小时

2. **YAML Frontmatter**
   - 工作量：中
   - 收益：高（结构化元数据）
   - 实施时间：2-3 小时

3. **记忆大小控制**
   - 工作量：小
   - 收益：高（防止文件过大）
   - 实施时间：1-2 小时

### 中优先级（v0.5.0）

4. **会话记忆（Session Memory）**
   - 工作量：中
   - 收益：中（更详细的状态跟踪）
   - 实施时间：3-4 小时

5. **记忆类型分类**
   - 工作量：中
   - 收益：中（更好的组织）
   - 实施时间：2-3 小时

### 低优先级（v0.6.0+）

6. **LLM 记忆提取**
   - 工作量：大
   - 收益：高（但成本增加）
   - 实施时间：5-8 小时
   - 注意：需要评估成本（API 调用）vs 收益（准确性）

---

## 总结

### Claude Code 的优势

1. ✅ **Forked subagent**：后台提取，不阻塞主流程
2. ✅ **结构化模板**：清晰的 section 划分
3. ✅ **YAML frontmatter**：元数据便于检索
4. ✅ **大小控制**：自动压缩，防止膨胀
5. ✅ **记忆索引**：快速定位相关记忆

### kuxing 的优势

1. ✅ **简单直接**：正则表达式提取，无额外成本
2. ✅ **独立持久化**：记忆文件与执行状态分离
3. ✅ **项目内全局记忆**：便于迁移

### 推荐改进路线

**v0.4.1（快速改进）**：
- 添加 MEMORY.md 索引
- 添加 YAML frontmatter
- 添加记忆大小控制

**v0.5.0（功能增强）**：
- 引入会话记忆（Session Memory）
- 记忆类型分类
- 改进 create-task 命令，自动生成分类记忆

**v0.6.0（智能提取）**：
- 评估 LLM 提取 vs 正则表达式的成本收益
- 如果合适，引入轻量级 LLM 提取
- 或者使用 Claude API 的 Haiku 模型（便宜快速）

---

**最后更新**：2026-04-03
**作者**：Claude (Sonnet 4.6)
