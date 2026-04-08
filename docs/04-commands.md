# 命令参考

## 命令概览

```
kuxing [全局选项] <子命令> [子命令选项]
```

| 子命令 | 说明 |
|--------|------|
| `init` | 初始化新项目 |
| `init-context` | 初始化记忆模板 |
| `run` | 开始执行任务 |
| `parallel` | 并行执行多个项目 |
| `status` | 查看当前状态 |
| `resume` | 继续执行 |
| `reset` | 重置所有状态 |
| `show` | 显示历史记录 |
| `create-task` | 交互式创建新任务 |

---

## 全局选项

| 选项 | 说明 |
|------|------|
| `--config <path>` | 指定配置文件路径 (YAML) |
| `--version` | 显示版本信息 |

---

## init - 初始化新项目

初始化项目，创建记忆目录并保存配置。

### 命令

```bash
kuxing init --config <配置文件路径>
```

### 选项

| 选项 | 必填 | 说明 |
|------|------|------|
| `--config <path>` | 是 | 任务配置文件路径 (YAML) |

### 示例

```bash
# 初始化项目
python cli.py --config examples/hello-world.yaml init

# 输出
初始化项目: Hello World
项目路径: /tmp/hello-world
执行模式: serial
任务数: 2

记忆目录: /path/to/kuxing/memory/hello-world
初始化完成！
```

---

## init-context - 初始化记忆模板

创建记忆文件模板（全局共享记忆或项目私有记忆）。

### 命令

```bash
kuxing init-context [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `--global` | 初始化全局共享记忆 |
| `--project` | 初始化项目私有记忆 |
| `--config <path>` | 配置文件路径（确定项目） |
| `--force` | 强制覆盖已有文件 |

### 示例

```bash
# 创建全局共享记忆
python cli.py init-context --global

# 创建项目私有记忆
python cli.py init-context --project --config examples/hello-world.yaml

# 强制覆盖
python cli.py init-context --global --force
```

### 生成的文件

| 类型 | 路径 |
|------|------|
| 全局共享 | `~/.kuxing/shared/context.md` |
| 项目私有 | `memory/<project-slug>/context.md` |

---

## run - 开始执行任务

开始执行任务，支持串行、并行、循环三种模式。

### 命令

```bash
kuxing run [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `--config <path>` | 配置文件路径（默认从 memory 目录查找） |
| `--dry-run` | 模拟执行，不实际调用 Claude |
| `--loop` | 强制使用循环模式 |
| `--max-rounds <n>` | 最大轮次限制（默认: 50） |

### 执行流程

```
1. 加载配置文件
2. 初始化调度器
3. 根据模式执行：
   - serial: 按顺序执行任务
   - parallel: 并行执行独立任务
   - loop: 循环执行直到满足停止条件
4. 保存执行结果
5. 更新记忆
```

### 示例

```bash
# 普通执行（串行模式）
python cli.py run

# 循环模式
python cli.py run --loop

# 指定最大轮次
python cli.py run --loop --max-rounds 100

# 干运行（不实际执行）
python cli.py run --dry-run

# 指定配置文件
python cli.py --config examples/my-task.yaml run
```

### 循环模式

循环模式会持续执行，直到满足以下任一条件：

1. 达到 `max-rounds` 限制
2. 用户按 `Ctrl+C` 中断
3. 配置中指定了停止条件

```bash
# 循环模式执行
python cli.py run --loop

# 限制最大 100 轮
python cli.py run --loop --max-rounds 100
```

---

## parallel - 并行执行多个项目

同时运行多个项目，每个项目有独立的记忆空间。

### 命令

```bash
kuxing parallel [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `--config <paths>` | 配置文件路径列表（默认使用 examples/ 下所有配置） |
| `--loop` | 使用循环模式持续执行 |

### 示例

```bash
# 并行执行 examples/ 下所有配置
python cli.py parallel

# 指定配置文件列表
python cli.py --config examples/task1.yaml --config examples/task2.yaml parallel

# 循环模式
python cli.py parallel --loop
```

### 输出示例

```
============================================================
并行执行 3 个项目
============================================================
  [1] Project A (examples/project-a.yaml)
  [2] Project B (examples/project-b.yaml)
  [3] Project C (examples/project-c.yaml)

每个项目使用独立的记忆空间，互不干扰。
按 Ctrl+C 停止所有项目。
============================================================

启动进程: project-a
  命令: python cli.py --config examples/project-a.yaml run
  日志: parallel_logs/project-a_20260403_103000.log
  PID: 12345

...

[10:30:30] 运行中: 3/3
```

---

## status - 查看当前状态

显示项目的当前执行状态。

### 命令

```bash
kuxing status [选项]
```

### 示例

```bash
python cli.py status

# 指定配置文件
python cli.py --config examples/hello-world.yaml status
```

### 输出示例

```
项目: Hello World
路径: /tmp/hello-world
模式: serial
当前轮次: 2

任务进度:
  总数: 2
  已完成: 1
  待处理: 1

执行轮次: 2
最后活动: 2026-04-03 10:30:25
最后错误: （无）
```

---

## resume - 继续执行

从上次中断的位置继续执行。

### 命令

```bash
kuxing resume [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `--max-rounds <n>` | 最大轮次限制（默认: 50） |

### 示例

```bash
# 继续执行
python cli.py resume

# 限制最大轮次
python cli.py resume --max-rounds 100
```

### 使用场景

1. **用户中断后继续**：`Ctrl+C` 中断后，使用 `resume` 从上次位置继续
2. **程序崩溃后恢复**：程序异常退出，下次运行 `run` 会自动恢复

---

## reset - 重置所有状态

清空执行历史和记忆，但保留配置。**只重置一个项目**，由 `--config` 指定。

### 命令

```bash
kuxing reset [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `--config <path>` | 配置文件路径（**必填**，指定要重置的项目） |
| `--confirm` | 确认重置（防止误操作） |
| `--clear-all` | 清空所有记忆（包括配置） |

### 示例

```bash
# 重置轮次记忆（保留配置）- 只重置指定项目
python cli.py --config examples/update-kuxing-docs.yaml reset --confirm

# 清空所有记忆（包括配置）- 只清空指定项目
python cli.py --config examples/update-kuxing-docs.yaml reset --confirm --clear-all
```

### 重置级别

| 级别 | 保留 | 清空 |
|------|------|------|
| `reset` | 配置 | 轮次历史、状态 |
| `reset --clear-all` | 无 | 所有记忆 |

### 作用域说明

`reset` 命令只影响**一个项目**：
- 使用 `--config` 指定项目配置文件
- 不指定 `--config` 时，查找 memory 目录下最近的一个项目

---

## show - 显示历史记录

显示执行历史记录。

### 命令

```bash
kuxing show [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `--history` | 显示所有历史记录 |
| `--round <n>` | 显示指定轮次的详细信息 |

### 示例

```bash
# 显示所有历史
python cli.py show --history

# 显示第 3 轮详情
python cli.py show --round 3

# 默认显示下次执行的上下文
python cli.py show
```

### 输出示例

```
### Round 1: ✅ 创建文件
时间: 2026-04-03 10:30:01
摘要: 在 /tmp/hello-world 目录下创建了 hello.txt

### Round 2: ✅ 读取验证
时间: 2026-04-03 10:30:15
摘要: 验证了文件内容，包含 "Hello from kuxing!"
```

---

## create-task - 交互式创建新任务

交互式创建新任务的配置和记忆。

### 命令

```bash
kuxing create-task --project-name <项目名称>
```

### 选项

| 选项 | 必填 | 说明 |
|------|------|------|
| `--project-name <name>` / `-p <name>` | 是 | 项目名称 |
| `--config <path>` | 否 | 配置文件路径 |

### 交互流程

```
🤖 创建任务: 我的项目
==================================================

📂 代码路径（每行一个，输入空行结束）:
  路径: /home/user/project
  路径: （直接回车结束）

📄 文档路径（每行一个，输入空行结束）:
  路径: /home/user/project/docs
  路径: （直接回车结束）

📝 项目描述（可选）:
  项目描述: 这是一个测试项目

🔐 是否需要保存账号信息？(y/n): n

⚙️  是否需要保存偏好设置？(y/n): n

🔄 最大轮次（默认50）: 20

🔄 正在生成配置和记忆文件...
✅ 已生成配置: /path/to/kuxing/examples/my-project.yaml
✅ 已生成项目记忆: /path/to/kuxing/memory/my-project/context.md
✅ 项目记忆已初始化

🚀 可以运行了：
   python cli.py --config examples/my-project.yaml run
```

### 生成的文件

1. **配置文件**：`examples/<project-slug>.yaml`
2. **项目记忆**：`memory/<project-slug>/context.md`
3. **会话记忆**：`memory/<project-slug>/session.md`
4. **记忆索引**：`memory/<project-slug>/MEMORY.md`

---

## 环境变量

苦行僧支持在配置和记忆中使用环境变量：

```bash
# 设置环境变量
export SDK_PATH="/opt/sdk"
export ANDROID_SDK_HOME="/opt/android-sdk"
```

```yaml
# 配置中使用
tasks:
  - prompt: |
      SDK 路径: ${SDK_PATH}
      使用 Android SDK: ${ANDROID_SDK_HOME}
```

```markdown
<!-- 记忆中使用 -->
## SDK 路径
- Android SDK: ${ANDROID_SDK_HOME}
- NDK: ${ANDROID_NDK_HOME}
```

---

## 退出码

| 退出码 | 说明 |
|--------|------|
| 0 | 任务全部成功完成 |
| 1 | 有任务失败 |
| 130 | 用户中断（Ctrl+C） |

---

## 下一步

- [配置指南](./05-config-guide.md) - YAML 配置详解
- [调度器架构](./06-scheduler-architecture.md) - 内部工作原理

---

**最后更新**：2026-04-08
- [记忆架构](./07-memory-architecture.md) - 记忆系统详解
