# 苦行僧 (Kuxing)

Claude Code 多轮任务调度系统 - 跨会话持续执行多轮任务

## 功能特点

- **多轮执行**: 支持串行、并行、循环三种执行模式
- **状态持久化**: 通过文件系统保存每轮执行上下文
- **智能记忆**: 每轮知道之前几轮做了什么，下一轮该做什么
- **断点续传**: 中断后可继续，从上次位置执行
- **配置驱动**: 通过YAML配置文件定义任务流程
- **多项目并行**: 支持同时运行多个独立项目，每个项目有独立记忆空间

## 安装

### 前置要求

- Python 3.8+
- Claude Code CLI (`claude` 命令在 PATH 中)

### 安装步骤

```bash
# 1. 克隆或拷贝项目
git clone <repo-url> ~/kuxing
cd ~/kuxing

# 2. 安装依赖
pip install -r requirements.txt

# 3. 验证安装
python cli.py --help
```

### 依赖说明

| 依赖 | 说明 |
|------|------|
| Python 3.8+ | 运行环境 |
| pyyaml | 配置文件解析 |

其他均为 Python 标准库，无需额外安装。

## 快速开始

### 方式 1：使用 create-task 命令（推荐）

```bash
# 交互式创建任务
python cli.py create-task --project-name "我的项目"

# 按提示输入：
# - 代码路径
# - 文档路径
# - 项目描述
# - 账号信息（可选）
# - 偏好设置（可选）
# - 最大轮次

# 自动生成：
# - examples/我的项目.yaml（配置文件）
# - memory/我的项目/context.md（项目记忆）
# - shared_context/context.md（全局记忆）

# 直接运行
python cli.py run --config examples/我的项目.yaml
```

### 方式 2：手动创建配置文件

### 1. 查看帮助

```bash
cd ~/kuxing
python cli.py --help
```

### 2. 启动单项目

```bash
# 使用示例配置运行
python cli.py run --config examples/claude-code-50rounds.yaml

# 强制使用循环模式
python cli.py run --config examples/claude-code-50rounds.yaml --loop

# 限制最大轮次
python cli.py run --config examples/claude-code-50rounds.yaml --max-rounds 10
```

### 3. 启动多项目并行

```bash
# 并行运行 examples/ 下所有配置
python cli.py parallel

# 只运行指定的几个配置
python cli.py parallel --config examples/claude-code-50rounds.yaml examples/write_docs.yaml

# 循环模式持续运行
python cli.py parallel --loop
```

### 4. 查看状态

```bash
# 查看当前项目状态
python cli.py status

# 查看执行历史
python cli.py show --history

# 查看指定轮次详情
python cli.py show --round 5
```

### 5. 继续执行（中断后）

```bash
python cli.py resume
```

### 6. 重置（清空记忆，切换项目）

```bash
# 只清空轮次记忆，保留配置
python cli.py reset --confirm

# 清空所有记忆（包括配置）
python cli.py reset --confirm --clear-all
```

## 完整使用案例：以 Claude Code 源码分析为例

### 需求背景

需要对 Claude Code 的源码目录进行全景分析，生成完整的文档。由于代码量巨大（37个模块），需要分成50轮来完成，每轮聚焦一个或几个相关模块。

### 配置文件

创建 `examples/claude-code-50rounds.yaml`：

```yaml
project_name: "Claude Code 源码全景分析 50轮"
project_path: "/home/zhengjian/claudecode_projects/claude-code"
description: "深入分析Claude Code源码的每个重点模块"

mode: loop  # 循环模式

tasks:
  - id: task_analyze_and_plan
    type: agent
    description: "分析所有模块，规划50轮文档任务"
    prompt_template: |
      请分析 {project_path}/src/ 目录下的所有模块：

      1. 列出所有子目录和主要文件
      2. 识别37个模块中最重要的30-40个重点模块
      3. 为每个重点模块规划要生成的文档内容：
         - 模块名称和功能概述
         - 核心数据结构
         - 主要函数和流程
         - 需要的图表类型

      输出一个详细的50轮计划，每轮对应一个或多个模块的文档生成。
    expected_output: "生成 docs/50-round-plan.md，包含50轮的详细规划"

  - id: task_execute_round
    type: agent
    description: "执行单轮文档生成"
    prompt_template: |
      {context_summary}

      ## 本轮任务

      请根据上面的规划，执行当前轮次的文档生成任务。

      要求：
      1. 仔细阅读相关源码
      2. 使用文档方法论（First Principles, 5W2H, STAR, Feynman）组织内容
      3. 包含以下类型的图表：
         - ASCII 图：架构图、流程图、状态机
         - PlantUML 图：组件图、序列图（保存 .puml 源文件，生成 .svg 和 .png）
         - draw.io 图：复杂系统设计（保存 .drawio 源文件，生成 .svg 和 .png）
      4. 图表文件保存到 docs/images/ 目录
      5. 文档用中文写，包含详细的代码注释和解释

      每轮完成后，输出：
      - 创建/更新的文档列表
      - 生成的图表文件列表
      - 下一轮建议（下一个要分析的模块）
    expected_output: "生成/更新对应的文档，包含完整的图表"

loop_config:
  first_task_id: task_analyze_and_plan  # 第一轮执行规划任务
  task_id: task_execute_round           # 后续轮次执行文档生成
  max_rounds: 50                        # 50轮
  stop_condition: ""                    # 留空则不自动停止，直到达到max_rounds
  interval_seconds: 30                  # 每轮之间休息30秒
```

### 配置字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `project_name` | 项目名称（用于显示和日志） | "Claude Code 源码分析" |
| `project_path` | 要分析的项目路径 | "/home/user/claude-code" |
| `description` | 项目描述 | "深入分析源码..." |
| `mode` | 执行模式 | `serial` / `parallel` / `loop` |
| `tasks` | 任务列表 | 见下方详细说明 |
| `loop_config` | 循环模式配置 | 见下方详细说明 |

### tasks 字段详解

```yaml
tasks:
  - id: task_1                    # 任务唯一ID
    type: agent                   # 任务类型（目前固定为 agent）
    description: "任务描述"        # 简短描述
    prompt_template: |             # 任务执行的Prompt模板
      {context_summary}            # 系统会自动注入上下文
      {project_path}              # 可在模板中使用变量
    expected_output: "预期输出"    # 预期输出说明
    depends_on: []                 # 依赖的任务ID（串行模式）
```

**模板变量**：

| 变量 | 说明 |
|------|------|
| `{context_summary}` | 自动注入的历史上下文（自动替换，不需要在配置中定义） |
| `{project_path}` | 配置中定义的 `project_path` 字段值 |

### loop_config 详解

```yaml
loop_config:
  first_task_id: task_analyze_and_plan  # 第一轮执行的任务ID
  task_id: task_execute_round            # 后续轮次执行的任务ID
  max_rounds: 50                          # 最大轮次限制
  stop_condition: ""                      # 停止条件（留空则直到max_rounds停止）
  interval_seconds: 30                    # 轮次之间休息秒数
```

**stop_condition 格式**：
- 留空 `""`：不自动停止，直到达到 `max_rounds`
- `"连续N次成功"`：连续成功N次后自动停止

### 执行流程

1. **Round 1**: 执行 `first_task_id` 指定的任务（本例中是 `task_analyze_and_plan`）
   - 生成 50 轮计划文档
   - 输出结构化的轮次规划

2. **Round 2-N**: 执行 `task_id` 指定的循环任务（本例中是 `task_execute_round`）
   - 每次读取上一轮的输出和建议
   - 自动决定下一轮要分析哪个模块
   - 生成对应模块的文档

3. **每轮之间的上下文传递**：
   - 自动保存本轮的执行结果、创建的文件、生成的摘要
   - 下一轮自动获得 `context_summary`，包含：
     - 前几轮的摘要
     - 当前进度
     - 建议的下一轮任务

### 运行示例

```bash
# 开始执行
$ python cli.py run --config examples/claude-code-50rounds.yaml

发现已有状态，加载中...
项目: Claude Code 源码全景分析 50轮
模式: loop

============================================================
Round 1 开始 | 任务: 分析所有模块，规划50轮文档任务
============================================================

[Round 1] Claude调用成功 | model: sonnet
[Round 1] 结果:
  status: completed
  files_created: ['docs/50-round-plan.md']
  summary: 生成了50轮计划...

[Round 1] 结束 | 状态: 成功 | 耗时: 125.3秒
------------------------------------------------------------

============================================================
Round 2 开始 | 任务: 执行单轮文档生成
============================================================

[Round 2] Claude调用成功 | model: sonnet
[Round 2] 结果:
  status: completed
  files_created: ['docs/01-overview.md', 'docs/images/arch.puml']
  summary: 生成了系统概览文档...

...

# 查看状态
$ python cli.py status

项目: Claude Code 源码全景分析 50轮
路径: /home/zhengjian/claudecode_projects/claude-code
模式: loop
当前轮次: 10

任务进度:
  总数: 2
  已完成: 2
  待处理: 0

执行轮次: 10
最后活动: 2026-04-03 10:30:00
```

## 多项目并行

### 需求场景

同时运行多个不同的接力任务，每个项目有独立的记忆空间，互不干扰。

### 示例：同时分析两个项目

```bash
# 项目A：Claude Code 源码分析
# 项目B：另一个项目的文档整理

# 创建项目B的配置
cat > examples/project-b.yaml << 'EOF'
project_name: "Project B 文档整理"
project_path: "/path/to/project-b"
mode: loop

tasks:
  - id: task_doc
    type: agent
    description: "整理文档"
    prompt_template: "整理 {project_path} 下的文档..."
    expected_output: "生成完整文档"

loop_config:
  task_id: task_doc
  max_rounds: 20
EOF

# 并行运行两个项目
python cli.py parallel --config examples/claude-code-50rounds.yaml examples/project-b.yaml --loop
```

### 输出示例

```
============================================================
并行执行 2 个项目
============================================================
  [1] Claude Code 源码全景分析 50轮 (examples/claude-code-50rounds.yaml)
  [2] Project B 文档整理 (examples/project-b.yaml)

每个项目使用独立的记忆空间，互不干扰。
按 Ctrl+C 停止所有项目。
============================================================

启动进程: claude-code-50rounds
  命令: python /home/zhengjian/claudecode_projects/kuxing/cli.py run ...
  日志: /home/zhengjian/claudecode_projects/kuxing/parallel_logs/claude-code-50rounds_20260403_103000.log
  PID: 12345

启动进程: project-b
  命令: python /home/zhengjian/claudecode_projects/kuxing/cli.py run ...
  日志: /home/zhengjian/claudecode_projects/kuxing/parallel_logs/project-b_20260403_103000.log
  PID: 12346

============================================================
已启动 2 个项目
查看日志: tail -f /home/zhengjian/claudecode_projects/kuxing/parallel_logs/<项目名>_*.log
============================================================

[10:30:30] 运行中: 2/2
```

### 记忆目录结构

```
memory/
├── claude_code_源码全景分析_50轮/   # 项目A的记忆
│   ├── config.yaml
│   ├── state.json
│   ├── context.md                  # 项目私有记忆
│   ├── knowledge_base.md           # 知识沉淀
│   └── rounds/
│       ├── round_0001.json
│       └── ...
├── project_b_文档整理/              # 项目B的记忆
│   ├── config.yaml
│   ├── state.json
│   ├── context.md                  # 项目私有记忆
│   ├── knowledge_base.md           # 知识沉淀
│   └── rounds/
│       └── ...
└── parallel_logs/                   # 并行运行日志
    ├── claude-code-50rounds_20260403_103000.log
    └── project-b_20260403_103000.log
```

## 分层记忆系统

苦行僧支持分层记忆，让不同项目可以共享公共信息，同时保留项目私有记忆。

### 记忆分层

| 层级 | 位置 | 说明 |
|------|------|------|
| 全局共享 | `shared_context/context.md` | 所有项目共享的 SDK 路径、账号配置等 |
| 项目私有 | `memory/{project}/context.md` | 项目特定的 SDK、参考文件、已知问题等 |
| 知识沉淀 | `memory/{project}/knowledge_base.md` | Claude 每轮自动沉淀的知识发现 |

### 初始化记忆模板

```bash
# 初始化全局共享记忆（所有项目共享）
python cli.py init-context --global

# 初始化项目私有记忆
python cli.py init-context --project --config examples/claude-code-50rounds.yaml

# 查看全局共享记忆
cat shared_context/context.md
```

### 记忆模板示例

**全局共享记忆** (`shared_context/context.md`)：
```markdown
# 全局公共记忆

## SDK 路径
- Android SDK: ${ANDROID_SDK_HOME}
- NDK: ${ANDROID_NDK_HOME}
- Python: /usr/bin/python3

## 常用参考文档
- API规范: /docs/api-spec.yaml
- 设计文档: /docs/design.md

## 账号配置（使用 ${VAR_NAME} 引用环境变量）
- Harbor: ${HARBOR_USERNAME}
- GitLab: ${GITLAB_TOKEN}
```

**项目私有记忆** (`memory/{project}/context.md`)：
```markdown
# 项目私有记忆

## 项目: Claude Code 源码分析

## SDK 路径
- 内部SDK: /home/dev/internal-sdk

## 参考文件
- 架构图: docs/architecture.md
- API文档: docs/api.md

## 已知问题
- 模块A有bug，需要特殊处理
```

### 环境变量引用

在记忆文件中使用 `${VAR_NAME}` 语法引用环境变量：

```markdown
- SDK路径: ${ANDROID_SDK_HOME}
- 账号: ${HARBOR_USERNAME} / ${HARBOR_PASSWORD}
```

系统会自动：
1. 读取 `.md` 文件内容
2. 查找 `${VAR_NAME}` 模式
3. 替换为 `os.environ.get("VAR_NAME")` 的值
4. 不存在的变量保留原样 `${UNKNOWN_VAR}`

### 优先级

当不同层级的记忆有冲突时，**优先级从高到低**：

1. 项目私有记忆 (`memory/{project}/context.md`)
2. 全局共享记忆 (`~/.kuxing/shared/context.md`)
3. 知识沉淀 (`memory/{project}/knowledge_base.md`)

### 知识沉淀机制

每轮执行后，系统会追加知识到 `knowledge_base.md`：

```markdown
# 知识沉淀

## 更新 2026-04-03 10:30:00

本轮发现：
- 模块X使用特殊的配置方式
- 需要注意路径Y下的文件

========================================

## 更新 2026-04-03 11:00:00

本轮发现：
- 找到了性能瓶颈在函数Z
```

后续轮次会自动获得历史知识沉淀作为上下文参考。

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
├── requirements.txt    # 运行依赖
├── requirements-dev.txt # 开发依赖（测试）
├── pytest.ini          # pytest 配置
├── examples/           # 示例配置
│   ├── write_docs.yaml           # 写文档示例
│   ├── monitor_build.yaml        # 监控构建示例
│   ├── claude-code-docs.yaml     # Claude Code 文档示例
│   └── claude-code-50rounds.yaml # 50轮分析示例
├── tests/              # 测试目录
│   ├── __init__.py
│   ├── conftest.py              # pytest fixtures
│   ├── test_memory_store.py     # 记忆存储测试
│   ├── test_scheduler.py        # 调度器测试
│   ├── test_task_queue.py       # 任务队列测试
│   ├── test_prompts.py          # Prompt测试
│   └── README.md                # 测试说明
├── shared_context/     # 全局共享记忆（项目内，便于迁移）
│   └── context.md
├── memory/             # 运行时记忆目录（自动创建）
│   └── {project_slug}/
│       ├── config.yaml
│       ├── state.json
│       ├── context.md          # 项目私有记忆
│       ├── knowledge_base.md   # 知识沉淀
│       ├── rounds/
│       │   ├── round_0001.json
│       │   └── ...
│       └── logs/
│           └── run_YYYYMMDD_HHMMSS.log
└── parallel_logs/       # 并行运行日志（parallel命令）
    └── *.log
```

## 日志系统

每次运行会自动生成带时间戳的日志文件：

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

```bash
# 查看最新日志
ls -lt memory/*/logs/

# 实时查看日志
tail -f memory/claude_code_源码全景分析_50轮/logs/run_*.log

# 分析问题
grep "错误" memory/*/logs/*.log

# 查看并行日志
ls -lt parallel_logs/
tail -f parallel_logs/*.log
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

### 任务依赖（串行模式）

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
  stop_condition: ""  # 留空表示直到max_rounds
  # stop_condition: "连续3次成功"  # 或者连续N次成功后停止
  interval_seconds: 30
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
| `init-context [--global] [--project]` | 初始化记忆模板 |
| `run [--config <file>] [--loop] [--max-rounds N]` | 开始执行任务 |
| `parallel [--config <files>] [--loop]` | 并行执行多个项目 |
| `status` | 查看当前状态 |
| `resume [--max-rounds N]` | 继续执行（断点续传） |
| `show --history` | 显示所有历史 |
| `show --round N` | 显示指定轮次 |
| `reset --confirm [--clear-all]` | 重置所有状态 |

## 最佳实践

### 1. 长任务使用 dry-run 测试

```bash
# 先用 dry-run 模式测试配置是否正确
python cli.py run --config examples/claude-code-50rounds.yaml --dry-run
```

### 2. 定期检查状态

```bash
# 检查进度
python cli.py status

# 查看是否有错误
grep "错误" memory/*/logs/*.log
```

### 3. 合理设置 max_rounds

```yaml
loop_config:
  max_rounds: 50  # 根据任务量设置
  stop_condition: ""  # 或设置自动停止条件
```

### 4. 多项目并行时查看日志

```bash
# 查看所有并行项目的日志
tail -f parallel_logs/*.log

# 查看特定项目的日志
tail -f memory/project_a/logs/run_*.log
```

## 常见问题

### Q: 如何切换到新项目？

```bash
# 方法1: 重置当前项目记忆
python cli.py reset --confirm
python cli.py run --config new_project.yaml

# 方法2: 直接用新配置运行（会覆盖memory中的配置）
python cli.py run --config new_project.yaml
```

### Q: 任务中途失败了怎么办？

```bash
# 查看失败原因
grep "错误" memory/*/logs/*.log

# 继续执行（会从上次中断的地方继续）
python cli.py resume
```

### Q: 如何让任务在连续成功后自动停止？

```yaml
loop_config:
  stop_condition: "连续3次成功"  # 连续3次成功则停止
```

### Q: 多项目并行运行时如何查看某个项目的状态？

```bash
# 先指定项目配置
python cli.py --config examples/project-a.yaml status
```

## 注意事项

1. **费用控制**: Claude调用可能产生费用，请注意token使用量
2. **测试模式**: 长时间运行任务建议先用 `--dry-run` 测试
3. **定期备份**: 重要任务建议定期备份 memory 目录
4. **路径访问**: 确保 `project_path` 指定的路径可访问
5. **项目迁移**: 全局共享记忆现在位于 `shared_context/` 目录，可随项目一起迁移

## 开发和测试

### 运行测试

```bash
# 安装测试依赖
pip install -r requirements-dev.txt

# 运行所有测试
pytest tests/ -v

# 运行带覆盖率报告
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 测试说明

- ✅ 所有测试使用 mock Claude 调用器，不消耗 API 配额
- ✅ 测试速度快（秒级完成）
- ✅ 可以离线运行
- ✅ 结果可预测

详见 `tests/README.md`

---

**版本**: 0.3.0
**新功能**: 
- 分层记忆系统（全局共享/项目私有/知识沉淀）
- 多项目并行执行
- 自动知识沉淀
- 环境变量验证
- 完整的单元测试

**作者**: Claude Code
