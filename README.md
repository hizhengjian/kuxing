# 苦行 (Kuxing)

Claude Code 多轮任务调度系统 - 跨会话持续执行多轮任务

## 功能特点

- **多轮执行**: 支持串行、并行、循环三种执行模式
- **状态持久化**: 通过文件系统保存每轮执行上下文
- **智能记忆**: 每轮知道之前几轮做了什么，下一轮该做什么
- **断点续传**: 中断后可继续，从上次位置执行
- **配置驱动**: 通过YAML配置文件定义任务流程

## 快速开始

### 1. 初始化项目

```bash
cd ~/claudecode_projects/kuxing
python cli.py init --config examples/write_docs.yaml
```

### 2. 开始执行

```bash
python cli.py run
```

### 3. 查看状态

```bash
python cli.py status
python cli.py show --history
```

### 4. 继续执行（中断后）

```bash
python cli.py resume
```

### 5. 重置（清空记忆，切换项目）

```bash
python cli.py reset --confirm
```

## 项目结构

```
kuxing/
├── cli.py              # CLI入口
├── scheduler.py        # 主调度器
├── task_queue.py       # 任务队列（串行/并行/循环）
├── memory_store.py     # 记忆存储
├── state.py            # 状态数据结构
├── config_schema.py    # 配置加载验证
├── prompts.py          # Prompt模板
├── claude_invoker.py   # Claude调用层
├── examples/           # 示例配置
│   ├── write_docs.yaml
│   └── monitor_build.yaml
└── memory/              # 运行时记忆目录（自动创建）
    └── {project_slug}/
        ├── config.yaml
        ├── state.json
        ├── rounds/
        │   ├── round_0001.json
        │   └── ...
        └── logs/
            └── run_YYYYMMDD_HHMMSS.log
```

## 日志系统

每次运行会自动生成带时间戳的日志文件，便于问题排查和执行分析：

```
memory/{project_slug}/logs/run_20260402_143000.log
```

日志包含：
- 轮次开始/结束时间
- 发送的完整 Prompt
- Claude 原始输出（便于分析解析问题）
- 解析后的结果（files_modified, files_created, summary）
- Token 使用量统计
- 成功/失败状态

示例：
```bash
# 查看最新日志
ls -lt memory/*/logs/

# 实时查看日志
tail -f memory/claude_code_源码全景分析_50轮/logs/run_*.log

# 分析问题
grep "错误" memory/*/logs/*.log
```

## 配置说明

### 基本配置

```yaml
project_name: "项目名称"
project_path: "/path/to/project"
mode: serial  # serial | parallel | loop

tasks:
  - id: task_1
    type: agent
    description: "任务描述"
    prompt_template: |
      任务执行的详细指令
    expected_output: "预期输出说明"
```

### 任务依赖

```yaml
tasks:
  - id: task_1
    description: "第一步"

  - id: task_2
    depends_on: [task_1]  # 依赖 task_1 完成
    description: "第二步"
```

### 循环模式

```yaml
mode: loop

tasks:
  - id: task_monitor
    description: "监控任务"

loop_config:
  task_id: task_monitor
  max_rounds: 10
  stop_condition: |
    当成功连续3次时停止
```

## 执行模式

| 模式 | 说明 |
|------|------|
| `serial` | 串行执行，按依赖顺序一个一个任务执行 |
| `parallel` | 并行执行，同时执行多个独立任务 |
| `loop` | 循环执行，反复执行同一个任务直到满足停止条件 |

## CLI 命令

| 命令 | 说明 |
|------|------|
| `init --config <file>` | 初始化新项目 |
| `run` | 开始执行任务 |
| `status` | 查看当前状态 |
| `resume` | 继续执行（断点续传） |
| `show --history` | 显示所有历史 |
| `show --round N` | 显示指定轮次 |
| `reset --confirm` | 重置所有状态 |

## 使用场景

### 场景1: 离开前安排写文档

```bash
# 配置写文档任务
python cli.py init --config examples/write_docs.yaml

# 开始执行（Claude会一轮一轮写完所有文档）
python cli.py run
```

### 场景2: 循环监控构建

```bash
# 配置监控任务
python cli.py init --config examples/monitor_build.yaml

# 开始循环执行
python cli.py run --loop

# 连续3次成功后自动停止
```

### 场景3: 切换项目

```bash
# 重置记忆
python cli.py reset --confirm

# 初始化新项目
python cli.py init --config new_project.yaml
```

## 注意事项

1. Claude调用可能产生费用，请注意token使用量
2. 长时间运行任务建议使用dry-run模式先测试
3. 重要任务建议定期检查状态
4. 确保项目路径可访问

---

**版本**: 0.1.0
**作者**: Claude Code