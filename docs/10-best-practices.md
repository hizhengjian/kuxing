# 最佳实践指南

本文档汇集了苦行僧（kuxing）使用过程中的最佳实践，涵盖项目组织、配置优化、记忆系统使用、调试技巧等多个方面。

---

## 目录

- [1. 项目组织最佳实践](#1-项目组织最佳实践)
- [2. 配置优化建议](#2-配置优化建议)
- [3. 记忆系统使用技巧](#3-记忆系统使用技巧)
- [4. 调试和问题排查](#4-调试和问题排查)
- [5. 性能优化建议](#5-性能优化建议)
- [6. 常见错误与规避](#6-常见错误与规避)

---

## 1. 项目组织最佳实践

### 1.1 目录结构规范

推荐的项目结构：

```
projects/
└── my-project/
    ├── config.yaml              # 任务配置
    ├── memory/                  # 运行时记忆（自动生成）
    │   ├── config.yaml
    │   ├── state.json
    │   ├── session.md
    │   └── MEMORY.md
    └── outputs/                  # 任务输出（可选）
        ├── docs/
        └── logs/
```

**要点**：
- 将配置和记忆目录放在一起，方便管理
- 使用有意义的项目名称（避免中文和特殊字符）
- 定期备份 `memory/` 目录

### 1.2 配置文件组织

#### Good Example

```yaml
# config.yaml
project_name: "RK3588-ISP-Driver"
project_path: "/home/dev/rk3588-isp"
execution_mode: loop

loop_config:
  max_rounds: 100
  check_interval: 30
  stop_on_error: false

memory_config:
  context_summary_lines: 50
  auto_memory_update: true
  max_context_chars: 30000

tasks:
  - name: analyze_isp
    description: "分析 ISP 驱动架构"
    prompt: |
      分析 /home/dev/rk3588-isp/driver/isp.c 的结构：
      1. 主要函数和数据结构
      2. 与 V4L2 的集成方式
      3. 帧处理流程
```

#### Bad Example

```yaml
# config.yaml
project_name: "项目1"
project_path: "/home/user/xxx"
execution_mode: serial

tasks:
  - name: task1
    prompt: "分析代码"
```

### 1.3 任务拆分原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **单一职责** | 每个任务只做一件事 | "分析 ISP 驱动" 而非 "分析并优化 ISP" |
| **粒度适中** | 单任务 10-30 分钟完成 | 复杂任务拆分为多个子任务 |
| **依赖明确** | 使用 `depends_on` 声明依赖 | `depends_on: [analyze_isp]` |
| **可独立运行** | 任务应能独立调试 | 避免跨任务的状态依赖 |

### 1.4 多项目并行管理

当同时管理多个项目时，推荐使用并行命令：

```bash
# 创建多个项目的任务目录
mkdir -p ~/kuxing-projects/{project-a,project-b,project-c}

# 使用 parallel 命令同时运行（见 04-commands.md）
python cli.py parallel \
  --projects "project-a,project-b,project-c" \
  --max-concurrent 2
```

---

## 2. 配置优化建议

### 2.1 执行模式选择

| 场景 | 推荐模式 | 原因 |
|------|----------|------|
| 文档写作、代码生成 | `serial` | 任务有明确顺序依赖 |
| 代码重构、测试验证 | `loop` | 需要多轮迭代优化 |
| 多项目同时分析 | `parallel` | 任务相互独立 |
| 长时间监控 | `loop` | 持续运行直到满足退出条件 |

### 2.2 循环模式配置

```yaml
# 推荐配置（长任务）
loop_config:
  max_rounds: 50              # 最大轮次，防止无限循环
  check_interval: 10           # 状态检查间隔（秒）
  stop_on_error: false        # 遇错不停止，持续调试
  continue_on_empty: true     # 输出为空时继续（可能是等待输入）

# 推荐配置（短任务）
loop_config:
  max_rounds: 10
  check_interval: 5
  stop_on_error: true         # 短任务遇错停止以便检查
  continue_on_empty: false
```

### 2.3 记忆配置优化

```yaml
# 大项目推荐配置
memory_config:
  context_summary_lines: 100   # 更多上下文行数
  auto_memory_update: true     # 自动更新记忆
  max_context_chars: 50000     # 更大的上下文限制

# 小项目推荐配置
memory_config:
  context_summary_lines: 30
  auto_memory_update: false    # 手动控制记忆更新
  max_context_chars: 30000
```

### 2.4 环境变量配置

在 `~/.bashrc` 或 `~/.zshrc` 中设置：

```bash
# 苦行僧配置
export KUXING_MAX_ROUNDS=100
export KUXING_CONTEXT_LINES=50
export KUXING_AUTO_UPDATE=true

# Claude CLI 配置
export CLAUDE_CODE_CONFIG_DIR=~/.claude
```

---

## 3. 记忆系统使用技巧

### 3.1 MEMORY.md 索引维护

每次任务结束后，自动更新 MEMORY.md：

```markdown
# MEMORY.md

最后更新：2026-04-03 17:30:00

---

## 当前会话
- [Round 3: ISP 驱动分析](session.md) — 进度 60%

## 项目背景
- [RK3588 ISP 架构](context.md) — 更新于 Round 1
- [V4L2 集成方案](knowledge_base.md#v4l2) — 关键设计决策

## 知识沉淀
- [ISP 驱动模式](knowledge_base.md#isp-driver) — 常见问题汇总
- [调试技巧](knowledge_base.md#debugging) — 经验总结

## 关键文件
- `/home/dev/rk3588-isp/driver/isp.c` — 主驱动
- `/home/dev/rk3588-isp/include/isp.h` — 头文件

---

**使用说明**：按需加载，不要每次读取全部记忆。
```

### 3.2 结构化会话记忆（session.md）

v0.5.0 的 session.md 模板：

```markdown
# 会话记忆 - Round 3

## 执行标题
ISP 驱动分析 - 第三轮：帧处理流程深度分析

## 当前状态
### 进度
- [x] 分析主函数流程
- [x] 识别关键数据结构
- [ ] 分析帧处理回调

### 下一步计划
1. 分析 isp_process_frame() 函数
2. 绘制帧处理流程图
3. 识别潜在性能瓶颈

## 关键文件
- `driver/isp.c` — 已分析 70%
- `driver/isp-regulator.c` — 待分析

## 工作日志
### Round 3
- 分析了 isp_init() 和 isp_start_stream()
- 发现了帧同步问题（已记录到 context.md）

### Round 2
- 完成数据结构分析
- 识别出 5 个主要模块

## 错误与修正
- Round 2: 误判了中断处理方式 → 已通过阅读 datasheet 修正

## 待处理问题
- [ ] 帧处理回调的具体实现
- [ ] 内存缓冲区管理策略
```

### 3.3 知识沉淀（knowledge_base.md）

定期将重要发现沉淀到知识库：

```markdown
# 知识沉淀

## ISP 驱动模式

### 初始化序列
1. 获取资源（时钟、 regulators、GPIO）
2. 映射寄存器地址
3. 配置默认参数
4. 注册 V4L2 设备
5. 申请中断处理函数

### 常见问题
- **问题**：中断丢失导致帧花屏
  **原因**：中断处理函数执行时间过长
  **解决**：将处理分为顶半部和底半部

- **问题**：帧不同步
  **原因**：时间戳处理逻辑错误
  **解决**：参考 v4l2-compliance 测试结果

## 调试技巧
- 使用 `v4l2-ctl --all` 查看设备状态
- 使用 `media-ctl` 查看媒体拓扑
- 使用示波器测量 XVCLK 时钟
```

### 3.4 上下文分段策略

对于大项目，使用分段上下文：

```yaml
# 大型项目配置
memory_config:
  context_summary_lines: 50

tasks:
  - name: analyze_module_a
    prompt: |
      仅分析模块 A（driver/module_a/）：
      1. 入口函数
      2. 核心数据结构
      3. 与其他模块的接口
      注意事项：不要分析模块 B 和 C

  - name: analyze_module_b
    depends_on: [analyze_module_a]
    prompt: |
      基于模块 A 的分析结果，分析模块 B：
      1. 模块 B 的入口和接口
      2. 如何调用模块 A
      3. 数据流分析
```

---

## 4. 调试和问题排查

### 4.1 调试模式启用

```bash
# 启用调试模式
export KUXING_DEBUG=true

# 或者运行时启用
python cli.py --config config.yaml run --debug
```

### 4.2 日志获取

```bash
# 查看最近的错误日志
tail -100 memory/{project}/logs/error.log

# 查看任务执行历史
python cli.py show --project-name "项目名" --history

# 查看完整状态
python cli.py status --verbose
```

### 4.3 常见问题快速排查

| 问题 | 检查项 | 解决方案 |
|------|--------|----------|
| 任务卡住不动 | `ps aux \| grep claude` | 检查 Claude Code 进程是否挂起 |
| 上下文丢失 | 检查 memory/ 目录 | 确认文件存在且可读 |
| 记忆不更新 | 检查 auto_memory_update | 确认配置正确 |
| 配置加载失败 | `python cli.py validate` | 检查 YAML 语法 |

### 4.4 断点恢复流程

```bash
# 1. 查看当前状态
python cli.py status --project-name "项目名"

# 2. 查看最后几轮的执行情况
python cli.py show --project-name "项目名" --last 3

# 3. 如需回退到特定轮次
python cli.py reset --project-name "项目名" --round 5

# 4. 从指定轮次恢复
python cli.py resume --project-name "项目名" --from-round 5
```

### 4.5 Claude Code 无响应处理

```bash
# 方法 1：等待超时（默认 5 分钟）
# 系统会自动检测并处理

# 方法 2：手动杀掉无响应进程
pkill -f "claude"

# 方法 3：重置任务状态
python cli.py reset --project-name "项目名" --force

# 方法 4：清除 Claude Code 缓存
rm -rf ~/.claude/cache/*
```

---

## 5. 性能优化建议

### 5.1 上下文大小控制

```yaml
memory_config:
  context_summary_lines: 50    # 控制摘要行数
  max_context_chars: 30000    # 限制最大字符数
```

**优化原则**：
- 只保留必要的上下文
- 将详细技术细节放到知识沉淀中
- 使用分段分析避免上下文溢出

### 5.2 任务并行优化

```bash
# 并行执行多个独立项目
python cli.py parallel \
  --projects "proj-a,proj-b,proj-c" \
  --max-concurrent 2    # 限制并发数，避免资源竞争

# 在配置中设置
execution_mode: parallel
parallel_config:
  max_workers: 2
```

### 5.3 记忆文件压缩

v0.5.0 自动压缩过大的文件：

| 文件 | 阈值 | 压缩方式 |
|------|------|----------|
| session.md | > 20,000 字符 | LLM 压缩 |
| context.md | > 30KB | LLM 压缩 |
| knowledge_base.md | > 25KB | LLM 压缩 |

**手动触发压缩**：

```bash
# 强制压缩所有记忆文件
python cli.py compress --project-name "项目名"

# 仅压缩指定文件
python cli.py compress --project-name "项目名" --file session.md
```

### 5.4 轮次检查优化

```yaml
loop_config:
  check_interval: 10    # 合理设置检查间隔
  max_idle_seconds: 300 # 无活动超时（秒）
```

---

## 6. 常见错误与规避

### 6.1 配置错误

#### 错误 1：YAML 语法错误

```yaml
# 错误：缺少引号或特殊字符未转义
project_name: 项目-名称  # 可能出错

# 正确：使用引号包裹
project_name: "项目-名称"
```

#### 错误 2：循环依赖

```yaml
# 错误：A 依赖 B，B 依赖 A
tasks:
  - name: a
    depends_on: [b]  # 循环依赖！
  - name: b
    depends_on: [a]  # 循环依赖！

# 正确：线性依赖
tasks:
  - name: a
  - name: b
    depends_on: [a]
```

#### 错误 3：路径不存在

```bash
# 运行前验证路径
python cli.py --config config.yaml validate
# 或
python cli.py --config config.yaml run --dry-run
```

### 6.2 记忆系统错误

#### 错误 1：记忆文件损坏

```bash
# 检查文件完整性
ls -la memory/{project}/

# 恢复备份（如果有）
cp memory/{project}/.backup/session.md memory/{project}/session.md

# 或重新初始化
python cli.py init-context --project-name "项目"
```

#### 错误 2：上下文溢出

```yaml
# 原因：任务输出或上下文积累过多
# 解决：增加压缩阈值或清理历史

memory_config:
  max_context_chars: 50000  # 提高限制

# 或手动清理
rm memory/{project}/rounds/*.json  # 清理轮次历史
```

### 6.3 执行错误

#### 错误 1：任务卡在等待状态

```
症状：长时间显示 "等待输入" 但实际无响应
原因：任务进入需要用户交互的 Claude Code 模式

解决：
1. 在 prompt 中明确说明不需要交互
2. 使用 Ctrl+C 中断
3. 重置任务：python cli.py reset --project-name "项目"
```

#### 错误 2：重复执行相同轮次

```
症状：同一轮次被多次执行
原因：任务中断后恢复时未正确保存状态

解决：
1. 检查 memory/{project}/state.json 是否损坏
2. 手动编辑 state.json 修正轮次
3. 使用 reset 命令重置：python cli.py reset --project-name "项目"
```

#### 错误 3：依赖任务未完成就执行

```
症状：后置任务失败，提示依赖不存在
原因：depends_on 配置的任务未成功完成

解决：
1. 检查前置任务的执行状态
2. 确保前置任务设置了 continue_on_error: false
3. 按顺序重新执行
```

### 6.4 规避建议

| 场景 | 建议 |
|------|------|
| **长时间任务** | 设置合理的 `max_rounds`，避免无限循环 |
| **重要任务** | 定期备份 memory/ 目录 |
| **多项目并行** | 使用 `max-concurrent` 限制并发，避免资源竞争 |
| **复杂任务** | 先在小数据集上测试，验证后再处理完整数据 |
| **调试模式** | 使用 `--dry-run` 验证配置后再执行 |

### 6.5 紧急恢复流程

```bash
# 1. 停止所有运行中的任务
pkill -f "claude"
pkill -f "python.*cli.py"

# 2. 备份当前状态
cp -r memory/{project} memory/{project}.backup.$(date +%Y%m%d%H%M%S)

# 3. 检查配置文件
python cli.py --config memory/{project}/config.yaml validate

# 4. 重置到安全状态
python cli.py reset --project-name "项目"

# 5. 从最近成功的轮次恢复
python cli.py resume --project-name "项目" --from-round 5
```

---

## 附录：配置检查清单

开始任务前，检查以下配置：

- [ ] `project_name`：是否唯一，避免与其他项目冲突
- [ ] `project_path`：路径是否存在
- [ ] `execution_mode`：是否适合任务类型
- [ ] `loop_config.max_rounds`：是否设置了合理的上限
- [ ] `memory_config`：是否根据项目规模调整
- [ ] `tasks`：任务依赖是否正确，无循环依赖

---

**最后更新**：2026-04-03
**版本**：v0.5.0
