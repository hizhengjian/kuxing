# Kuxing v0.5.0 完整运行流程图

## 1. 初始化流程 (init)

```
用户执行: python cli.py init --config examples/test.yaml
    │
    ▼
加载配置文件
    ├─ 读取 config.yaml
    ├─ 解析项目信息
    └─ 验证配置有效性
    │
    ▼
创建记忆目录结构
    ├─ memory/{project_slug}/
    │   ├─ session.md          ← 会话记忆（10个结构化section）
    │   ├─ MEMORY.md            ← 记忆索引
    │   ├─ context.md           ← 项目上下文
    │   ├─ knowledge_base.md    ← 知识沉淀
    │   ├─ state.json           ← 执行状态
    │   ├─ config.yaml          ← 配置副本
    │   ├─ rounds/              ← 轮次记录
    │   └─ logs/                ← 日志文件
    │
    ▼
初始化 SessionMemory
    ├─ 创建 10 个 section
    ├─ 设置初始状态
    └─ 保存到 session.md
    │
    ▼
初始化完成 ✅
```

## 2. 执行流程 (run)

```
用户执行: python cli.py --config examples/test.yaml run
    │
    ▼
加载配置和状态
    ├─ 读取 config.yaml
    ├─ 读取 state.json
    └─ 读取 MEMORY.md 索引
    │
    ▼
初始化 Scheduler
    ├─ 创建 SessionMemory
    ├─ 创建 MemoryStore
    ├─ 创建 LLMCompressor
    ├─ 创建 ClaudeInvoker
    └─ 创建 TaskQueue
    │
    ▼
判断执行模式
    ├─ serial → run_until_complete()
    ├─ parallel → run_until_complete()
    └─ loop → run_loop_mode()
    │
    ▼
【循环模式执行】
    │
    ▼
Round 1 开始
    │
    ├─ 构建 prompt
    │   ├─ 系统提示词
    │   ├─ 任务描述
    │   ├─ 会话记忆摘要 ← session.md
    │   ├─ 项目上下文 ← context.md
    │   └─ 知识沉淀 ← knowledge_base.md
    │
    ├─ 调用 claude 命令
    │   └─ claude -p "完整prompt..."
    │
    ├─ 解析结果
    │   ├─ 提取 <result> 标签内容
    │   ├─ 解析 files_modified
    │   ├─ 解析 summary
    │   └─ 解析 next_hints
    │
    ├─ 更新记忆
    │   ├─ SessionMemory.extract_from_result()
    │   │   ├─ 更新"当前状态"
    │   │   ├─ 更新"工作日志"
    │   │   └─ 保存到 session.md
    │   │
    │   ├─ MemoryUpdater.update_from_result()
    │   │   └─ 更新 context.md
    │   │
    │   └─ MemoryStore.save_round()
    │       └─ 保存到 rounds/round_0001.json
    │
    ├─ 检查记忆大小
    │   ├─ session.md > 20KB?
    │   ├─ context.md > 30KB?
    │   └─ knowledge_base.md > 25KB?
    │       │
    │       └─ YES → 调用 LLMCompressor
    │           └─ claude -p "压缩以下内容..."
    │
    └─ 保存状态
        └─ state.json
    │
    ▼
Round 2 开始
    │
    ├─ 构建 prompt（包含 Round 1 的上下文）
    │   ├─ 系统提示词
    │   ├─ 任务描述
    │   ├─ 会话记忆摘要 ← 包含 Round 1 的结果
    │   ├─ 项目上下文 ← 包含 Round 1 发现的路径
    │   └─ 知识沉淀
    │
    ├─ 调用 claude 命令
    │
    ├─ 解析结果
    │
    ├─ 更新记忆
    │   ├─ SessionMemory 更新
    │   ├─ context.md 更新
    │   └─ rounds/round_0002.json 保存
    │
    ├─ 检查记忆大小
    │
    └─ 保存状态
    │
    ▼
达到 max_rounds (2)
    │
    ▼
执行完成
    ├─ 生成执行摘要
    │   ├─ total_rounds: 2
    │   ├─ completed_tasks: 2
    │   ├─ failed_tasks: 0
    │   └─ elapsed_seconds: 72.4
    │
    └─ 返回结果 ✅
```

## 3. 记忆系统工作流程

```
【会话记忆 - SessionMemory】
    │
    ├─ 初始化
    │   └─ 创建 10 个结构化 section
    │       ├─ 执行标题
    │       ├─ 当前状态
    │       ├─ 任务规格
    │       ├─ 关键文件
    │       ├─ 工作流程
    │       ├─ 错误与修正
    │       ├─ 代码库文档
    │       ├─ 学习总结
    │       ├─ 关键结果
    │       └─ 工作日志
    │
    ├─ 每轮执行后
    │   └─ extract_from_result()
    │       ├─ 更新"当前状态"（上一轮完成 + 下一步计划）
    │       ├─ 追加"工作日志"（时间戳 + 摘要）
    │       └─ 更新"执行标题"（轮次号）
    │
    └─ 生成 prompt 摘要
        └─ get_summary_for_prompt()
            ├─ 提取"当前状态"
            ├─ 提取"任务规格"
            ├─ 提取"关键文件"
            ├─ 提取"工作流程"
            └─ 提取"最近的错误"

【项目上下文 - context.md】
    │
    ├─ 自动记录
    │   ├─ 新发现的路径
    │   ├─ 新发现的文档
    │   └─ 新发现的账号
    │
    └─ 自动压缩（超过 30KB）
        └─ LLMCompressor.compress()

【知识沉淀 - knowledge_base.md】
    │
    ├─ 自动提取
    │   ├─ 最佳实践
    │   ├─ 避坑指南
    │   └─ 经验总结
    │
    └─ 自动压缩（超过 25KB）
        └─ LLMCompressor.compress()

【记忆索引 - MEMORY.md】
    │
    ├─ 分类索引
    │   ├─ 会话记忆 → session.md
    │   ├─ 项目背景 → context.md
    │   └─ 知识沉淀 → knowledge_base.md
    │
    └─ 自动更新
        └─ 每次记忆变化时更新索引
```

## 4. LLM 压缩流程

```
【自动触发】
    │
    ├─ 检查文件大小
    │   ├─ session.md > 20KB?
    │   ├─ context.md > 30KB?
    │   └─ knowledge_base.md > 25KB?
    │
    └─ YES → 触发压缩
        │
        ▼
【压缩流程】
    │
    ├─ 读取原文件内容
    │
    ├─ 构建压缩 prompt
    │   └─ "请压缩以下内容到 {target_size} 字符..."
    │
    ├─ 调用 claude 命令
    │   └─ claude -p "压缩prompt..."
    │
    ├─ 解析压缩结果
    │
    ├─ 备份原文件
    │   └─ {filename}.backup_{timestamp}
    │
    └─ 写入压缩后内容
        └─ 保存到原文件
```

## 5. 接力式执行（上下文传递）

```
Round 1
    │
    ├─ 执行任务
    ├─ 生成结果
    │   ├─ summary: "完成了什么"
    │   └─ next_hints: "下一步建议"
    │
    └─ 保存到 SessionMemory
        ├─ 当前状态 = summary + next_hints
        └─ 工作日志 += [时间戳] summary
    │
    ▼
Round 2
    │
    ├─ 读取 SessionMemory
    │   └─ 获取 Round 1 的上下文
    │       ├─ 上一轮完成：summary
    │       └─ 下一步计划：next_hints
    │
    ├─ 构建 prompt（包含上下文）
    │   └─ "### 项目上下文
    │        **上一轮完成**：{Round 1 summary}
    │        **下一步计划**：{Round 1 next_hints}"
    │
    ├─ 执行任务（基于上下文）
    │
    └─ 保存到 SessionMemory
        └─ 更新为 Round 2 的状态
    │
    ▼
Round 3...
```

## 6. 关键特性

### 6.1 结构化会话记忆
- ✅ 10 个固定 section，信息分类清晰
- ✅ 自动提取和更新，无需手动维护
- ✅ 生成 prompt 摘要，只包含关键信息

### 6.2 记忆索引
- ✅ MEMORY.md 提供快速导航
- ✅ 按类型分类（会话、项目、知识）
- ✅ 自动更新索引

### 6.3 LLM 智能压缩
- ✅ 自动检测文件大小
- ✅ 超过限制自动压缩
- ✅ 使用 claude 命令，无需配置 API key
- ✅ 时间衰减策略（1hr=100%, 1-6hr=80%, 6-24hr=50%, 24hr+=20%）

### 6.4 接力式执行
- ✅ 上下文在轮次间自动传递
- ✅ 每轮基于上一轮的结果继续
- ✅ 支持 {round_num} 等变量替换

---

**版本**：v0.5.0  
**日期**：2026-04-03  
**状态**：✅ 已验证
