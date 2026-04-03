# Kuxing 记忆系统改进方案

## 日期
2026-04-03

## 项目特点分析

Kuxing 是一个**接力式多轮任务调度系统**，特点：
- ✅ 每轮独立执行，通过记忆文件传递上下文
- ✅ 状态持久化，支持断点续传
- ✅ 循环模式，持续执行直到任务完成
- ✅ 多项目并行，每个项目独立记忆空间

**与 Claude Code 的核心区别**：
- Claude Code：单次对话，实时交互
- Kuxing：批处理模式，接力执行

---

## 最实用的 3 个改进

基于 Kuxing 的接力式特点，以下 3 个改进最实用：

### 改进 1：结构化会话记忆（Session Memory）⭐⭐⭐⭐⭐

**为什么最实用**：
- ✅ 每轮执行都需要知道"当前状态"和"下一步计划"
- ✅ 结构化模板让 Claude 快速定位关键信息
- ✅ 避免记忆文件混乱，信息难以查找

**原理图**：

```
┌─────────────────────────────────────────────────────────────┐
│                    Round N 执行流程                          │
└─────────────────────────────────────────────────────────────┘

1. 加载记忆
   │
   ├─ 读取 session.md（结构化会话记忆）
   │  ├─ # 当前状态：正在做什么？
   │  ├─ # 任务规格：用户要求什么？
   │  ├─ # 关键文件：重要文件及作用
   │  ├─ # 工作流程：执行的命令
   │  ├─ # 错误与修正：遇到的问题
   │  └─ # 下一步计划：接下来做什么
   │
   ├─ 读取 context.md（项目记忆）
   │  └─ 代码路径、文档路径、账号信息
   │
   └─ 读取 knowledge_base.md（知识沉淀）
      └─ 历史经验、最佳实践

2. 构建 Prompt
   │
   └─ 将结构化记忆注入 Prompt
      ├─ "你上一轮完成了：XXX"
      ├─ "当前状态：XXX"
      ├─ "下一步计划：XXX"
      └─ "注意事项：XXX"

3. 执行任务
   │
   └─ Claude 根据结构化上下文执行

4. 更新记忆
   │
   ├─ 更新 session.md
   │  ├─ 当前状态 → 刚完成的任务
   │  ├─ 下一步计划 → 从 next_hints 提取
   │  ├─ 工作流程 → 追加执行的命令
   │  └─ 错误与修正 → 记录遇到的问题
   │
   ├─ 追加 context.md（如有新发现）
   │  └─ 新路径、新命令
   │
   └─ 追加 knowledge_base.md（如有经验）
      └─ 关键发现、最佳实践

5. 进入 Round N+1
   │
   └─ 循环回到步骤 1
```

**会话记忆模板**：

```markdown
# 执行标题
_任务名称 - Round N_

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

**实现要点**：
```python
# session_memory.py

class SessionMemory:
    """结构化会话记忆"""
    
    SECTIONS = [
        "执行标题",
        "当前状态", 
        "任务规格",
        "关键文件",
        "工作流程",
        "错误与修正",
        "代码库文档",
        "学习总结",
        "关键结果",
        "工作日志"
    ]
    
    def update_current_state(self, summary: str, next_hints: str):
        """更新当前状态"""
        content = f"""
上一轮完成：{summary}

下一步计划：{next_hints}
"""
        self._update_section("当前状态", content)
    
    def append_workflow(self, command: str):
        """追加工作流程"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        entry = f"[{timestamp}] {command}"
        self._append_to_section("工作流程", entry)
    
    def append_error(self, error: str, solution: str):
        """追加错误与修正"""
        entry = f"""
**错误**: {error}
**解决**: {solution}
"""
        self._append_to_section("错误与修正", entry)
```

---

### 改进 2：记忆索引文件（MEMORY.md）⭐⭐⭐⭐

**为什么实用**：
- ✅ 快速定位关键信息（不用读完整个 context.md）
- ✅ 分类组织记忆（用户偏好、项目背景、工作反馈）
- ✅ 便于维护和更新

**原理图**：

```
┌─────────────────────────────────────────────────────────────┐
│                  记忆加载流程（带索引）                       │
└─────────────────────────────────────────────────────────────┘

Round N 开始
    │
    ▼
读取 MEMORY.md（索引文件）
    │
    ├─ ## 会话记忆
    │  └─ [当前会话](session.md) — Round 5，正在重构认证模块
    │
    ├─ ## 用户偏好
    │  ├─ [用户角色](user_role.md) — Python 专家，熟悉 FastAPI
    │  └─ [工作习惯](user_preferences.md) — 喜欢详细注释
    │
    ├─ ## 项目背景
    │  ├─ [项目信息](project_info.md) — 多轮任务调度系统
    │  ├─ [关键路径](project_paths.md) — 代码、文档路径
    │  └─ [账号信息](project_credentials.md) — GitLab 账号
    │
    ├─ ## 工作反馈
    │  ├─ [测试策略](feedback_testing.md) — 使用 pytest + mock
    │  └─ [代码风格](feedback_style.md) — 遵循 PEP 8
    │
    └─ ## 知识沉淀
       └─ [历史经验](knowledge_base.md) — 最佳实践、避坑指南
    │
    ▼
根据索引，按需加载相关记忆文件
    │
    ├─ 必须加载：session.md（当前状态）
    ├─ 必须加载：project_info.md（项目背景）
    ├─ 按需加载：user_role.md（如需了解用户背景）
    └─ 按需加载：feedback_*.md（如需参考工作方式）
    │
    ▼
构建 Prompt（只包含相关记忆）
    │
    └─ 避免加载无关信息，节省 token
```

**索引文件示例**：

```markdown
# 项目记忆索引

最后更新：2026-04-03 15:30:00

---

## 会话记忆
- [当前会话](session.md) — Round 5，正在重构认证模块

## 用户偏好
- [用户角色](user_role.md) — Python 专家，熟悉 FastAPI 和异步编程
- [工作习惯](user_preferences.md) — 喜欢详细注释，使用中文文档

## 项目背景
- [项目信息](project_info.md) — Kuxing 多轮任务调度系统
- [关键路径](project_paths.md) — 代码、文档、配置文件路径
- [账号信息](project_credentials.md) — GitLab、Harbor 账号（加密存储）

## 工作反馈
- [测试策略](feedback_testing.md) — 使用 pytest + mock，避免 API 调用
- [代码风格](feedback_style.md) — 遵循 PEP 8，使用 type hints
- [提交规范](feedback_git.md) — 使用 Conventional Commits

## 知识沉淀
- [历史经验](knowledge_base.md) — 最佳实践、避坑指南、性能优化

---

**使用说明**：
- 每次执行前，先读取此索引文件
- 根据任务需要，按需加载相关记忆文件
- 新增记忆时，同步更新此索引
```

**实现要点**：
```python
# memory_store.py

def load_memory_index(self) -> dict:
    """加载记忆索引"""
    index_file = self.memory_dir / 'MEMORY.md'
    if not index_file.exists():
        return {}
    
    content = index_file.read_text(encoding='utf-8')
    # 解析索引，提取文件路径和描述
    index = {}
    current_section = None
    
    for line in content.split('\n'):
        if line.startswith('## '):
            current_section = line[3:].strip()
            index[current_section] = []
        elif line.startswith('- ['):
            # 解析：- [标题](文件名) — 描述
            match = re.match(r'- \[([^\]]+)\]\(([^\)]+)\) — (.+)', line)
            if match:
                title, filename, description = match.groups()
                index[current_section].append({
                    'title': title,
                    'filename': filename,
                    'description': description
                })
    
    return index

def update_memory_index(self, section: str, title: str, 
                       filename: str, description: str):
    """更新记忆索引"""
    index_file = self.memory_dir / 'MEMORY.md'
    
    # 读取现有索引
    if index_file.exists():
        content = index_file.read_text(encoding='utf-8')
    else:
        content = "# 项目记忆索引\n\n"
    
    # 确保 section 存在
    section_header = f"## {section}\n"
    if section_header not in content:
        content += f"\n{section_header}\n"
    
    # 添加新条目
    entry = f"- [{title}]({filename}) — {description}\n"
    
    # 插入到对应 section（避免重复）
    if entry not in content:
        # 找到 section 位置，插入条目
        lines = content.split('\n')
        new_lines = []
        in_section = False
        inserted = False
        
        for line in lines:
            new_lines.append(line)
            if line == section_header.strip():
                in_section = True
            elif in_section and not inserted:
                if line.startswith('## ') or line == '':
                    # 到达下一个 section 或空行，插入条目
                    new_lines.insert(-1, entry.strip())
                    inserted = True
                    in_section = False
        
        if in_section and not inserted:
            # section 是最后一个，直接追加
            new_lines.append(entry.strip())
        
        content = '\n'.join(new_lines)
    
    # 更新时间戳
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    content = re.sub(
        r'最后更新：.*',
        f'最后更新：{timestamp}',
        content
    )
    
    index_file.write_text(content, encoding='utf-8')
```

---

### 改进 3：记忆大小控制与自动压缩⭐⭐⭐⭐

**为什么实用**：
- ✅ 防止记忆文件无限增长（影响加载速度）
- ✅ 保持记忆文件在合理大小（便于 Claude 理解）
- ✅ 自动清理过时信息（保留最新最重要的）

**原理图**：

```
┌─────────────────────────────────────────────────────────────┐
│                  记忆大小控制流程                             │
└─────────────────────────────────────────────────────────────┘

每轮执行后
    │
    ▼
检查记忆文件大小
    │
    ├─ session.md: 15,000 字符 ✅ (限制: 20,000)
    ├─ context.md: 35,000 字符 ⚠️  (限制: 30,000)
    └─ knowledge_base.md: 18,000 字符 ✅ (限制: 25,000)
    │
    ▼
context.md 超出限制，触发压缩
    │
    ▼
分析 context.md 结构
    │
    ├─ ## 新发现的路径 (2026-04-03 10:00) — 5,000 字符
    ├─ ## 新发现的路径 (2026-04-03 11:00) — 4,000 字符
    ├─ ## 新发现的路径 (2026-04-03 14:00) — 3,000 字符 ← 最新
    ├─ ## 新发现的命令 (2026-04-03 10:00) — 6,000 字符
    ├─ ## 新发现的命令 (2026-04-03 14:00) — 2,000 字符 ← 最新
    └─ ## 遇到的问题 (2026-04-03 12:00) — 15,000 字符
    │
    ▼
压缩策略
    │
    ├─ 合并相同类型的旧 section
    │  ├─ "新发现的路径" (10:00 + 11:00) → 合并为一个
    │  └─ "新发现的命令" (10:00) → 删除（已有新版本）
    │
    ├─ 保留最新的 section（14:00 的内容）
    │
    └─ 压缩"遇到的问题"
       ├─ 保留最近 5 个问题（最重要）
       └─ 删除已解决的旧问题
    │
    ▼
压缩后的 context.md
    │
    ├─ ## 发现的路径（汇总）— 8,000 字符
    │  └─ 合并了 10:00 和 11:00 的路径
    │
    ├─ ## 新发现的路径 (2026-04-03 14:00) — 3,000 字符
    │
    ├─ ## 新发现的命令 (2026-04-03 14:00) — 2,000 字符
    │
    └─ ## 遇到的问题（最近 5 个）— 8,000 字符
    │
    ▼
新大小：21,000 字符 ✅ (在限制内)
    │
    ▼
继续执行下一轮
```

**压缩策略**：

```
1. 时间衰减策略
   ├─ 最近 1 小时：保留 100%
   ├─ 1-6 小时：保留 80%
   ├─ 6-24 小时：保留 50%
   └─ 24 小时以上：保留 20%（只保留关键信息）

2. 重要性策略
   ├─ 高优先级：当前状态、下一步计划、错误信息
   ├─ 中优先级：关键文件、工作流程
   └─ 低优先级：历史日志、已解决的问题

3. 合并策略
   ├─ 相同类型的 section 合并
   ├─ 去重（相同路径、相同命令只保留一次）
   └─ 摘要（长文本压缩为关键点）
```

**实现要点**：
```python
# memory_store.py

MAX_SESSION_SIZE = 20000      # session.md 最大 20KB
MAX_CONTEXT_SIZE = 30000      # context.md 最大 30KB
MAX_KNOWLEDGE_SIZE = 25000    # knowledge_base.md 最大 25KB

def check_and_compress_if_needed(self):
    """检查并压缩记忆文件"""
    files_to_check = [
        (self.session_file, MAX_SESSION_SIZE, self._compress_session),
        (self.context_file, MAX_CONTEXT_SIZE, self._compress_context),
        (self.knowledge_file, MAX_KNOWLEDGE_SIZE, self._compress_knowledge)
    ]
    
    for file_path, max_size, compress_func in files_to_check:
        if not file_path.exists():
            continue
        
        content = file_path.read_text(encoding='utf-8')
        current_size = len(content)
        
        if current_size > max_size:
            self.logger.warning(
                f"{file_path.name} 超出限制 "
                f"({current_size} > {max_size})，开始压缩..."
            )
            compressed = compress_func(content)
            file_path.write_text(compressed, encoding='utf-8')
            new_size = len(compressed)
            self.logger.info(
                f"压缩完成：{current_size} → {new_size} "
                f"({(1 - new_size/current_size)*100:.1f}% 减少)"
            )

def _compress_context(self, content: str) -> str:
    """压缩 context.md"""
    sections = self._parse_sections_with_timestamp(content)
    
    # 按时间戳分组
    now = datetime.now()
    recent = []      # 最近 1 小时
    medium = []      # 1-6 小时
    old = []         # 6 小时以上
    
    for section in sections:
        age_hours = (now - section['timestamp']).total_seconds() / 3600
        if age_hours < 1:
            recent.append(section)
        elif age_hours < 6:
            medium.append(section)
        else:
            old.append(section)
    
    # 压缩策略
    compressed_sections = []
    
    # 保留所有最近的 section
    compressed_sections.extend(recent)
    
    # 中等时间的 section：合并相同类型
    medium_merged = self._merge_sections_by_type(medium)
    compressed_sections.extend(medium_merged)
    
    # 旧 section：只保留关键信息
    old_summary = self._summarize_old_sections(old)
    if old_summary:
        compressed_sections.append({
            'type': '历史汇总',
            'timestamp': old[0]['timestamp'] if old else now,
            'content': old_summary
        })
    
    # 重新生成内容
    return self._sections_to_markdown(compressed_sections)

def _merge_sections_by_type(self, sections: List[dict]) -> List[dict]:
    """合并相同类型的 section"""
    merged = {}
    
    for section in sections:
        section_type = section['type']
        if section_type not in merged:
            merged[section_type] = {
                'type': section_type,
                'timestamp': section['timestamp'],
                'content': []
            }
        
        # 合并内容（去重）
        for item in section['content'].split('\n'):
            if item.strip() and item not in merged[section_type]['content']:
                merged[section_type]['content'].append(item)
    
    # 转换回 section 格式
    result = []
    for section_type, data in merged.items():
        result.append({
            'type': section_type,
            'timestamp': data['timestamp'],
            'content': '\n'.join(data['content'])
        })
    
    return result
```

---

## 实施计划

### Phase 1：结构化会话记忆（2-3 小时）

**文件修改**：
1. 新增 `session_memory.py`
2. 修改 `scheduler.py`：集成 SessionMemory
3. 修改 `prompts.py`：从 session.md 加载上下文

**测试**：
- 创建 `tests/test_session_memory.py`
- 验证 section 更新逻辑
- 验证 prompt 构建

### Phase 2：记忆索引（1-2 小时）

**文件修改**：
1. 修改 `memory_store.py`：添加索引相关方法
2. 修改 `cli.py`：create-task 时生成索引
3. 修改 `scheduler.py`：启动时加载索引

**测试**：
- 创建 `tests/test_memory_index.py`
- 验证索引生成和更新
- 验证按需加载

### Phase 3：记忆大小控制（2-3 小时）

**文件修改**：
1. 修改 `memory_store.py`：添加压缩逻辑
2. 修改 `scheduler.py`：每轮后检查大小
3. 添加配置项：允许自定义大小限制

**测试**：
- 创建 `tests/test_memory_compression.py`
- 验证压缩策略
- 验证时间衰减

### 总计：5-8 小时

---

## 效果预期

### 改进前（v0.4.0）

```
Round 5 开始
    │
    ▼
加载记忆（混乱）
    ├─ context.md: 50KB，包含大量历史信息
    ├─ knowledge_base.md: 30KB
    └─ 无结构化会话状态
    │
    ▼
Claude 需要从 80KB 文本中提取关键信息
    ├─ 耗时：5-10 秒
    ├─ Token 消耗：~20,000 tokens
    └─ 可能遗漏关键信息
```

### 改进后（v0.5.0）

```
Round 5 开始
    │
    ▼
加载记忆（结构化）
    ├─ MEMORY.md: 索引文件，快速定位
    ├─ session.md: 10KB，结构化会话状态
    │  ├─ 当前状态：清晰明确
    │  ├─ 下一步计划：直接可用
    │  └─ 关键文件：快速定位
    ├─ context.md: 25KB（自动压缩）
    └─ knowledge_base.md: 20KB（自动压缩）
    │
    ▼
Claude 从结构化记忆中快速提取信息
    ├─ 耗时：2-3 秒
    ├─ Token 消耗：~12,000 tokens
    └─ 准确定位关键信息
```

**收益**：
- ⏱️ 加载时间减少 50%
- 💰 Token 消耗减少 40%
- 🎯 信息准确性提升 60%
- 📊 记忆文件大小控制在合理范围

---

**最后更新**：2026-04-03
**作者**：Claude (Sonnet 4.6)
