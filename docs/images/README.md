# 图表文件说明

本目录包含所有 PlantUML 图表源文件（.puml）和生成的图片（.svg/.png）。

## 文件列表

| 源文件 | 生成文件 | 用途 | 引用位置 |
|--------|---------|------|----------|
| `scheduler-sequence.puml` | `scheduler-sequence.svg`, `scheduler-sequence.png` | 调度器执行序列图 | `06-scheduler-architecture.md` |
| `system-context.puml` | `system-context.svg`, `system-context.png` | 系统上下文图（C4 风格） | `01-overview.md` |
| `task-state.puml` | `task-state.svg`, `task-state.png` | 任务执行流程与状态图 | `06-scheduler-architecture.md` |
| `memory-layers.puml` | `memory-layers.svg`, `memory-layers.png` | 记忆层次交互图 | `07-memory-architecture.md` |
| `config-workflow.puml` | `config-workflow.svg`, `config-workflow.png` | 配置工作流程图 | `05-config-guide.md` |
| `example-workflow.puml` | `example-workflow.svg`, `example-workflow.png` | 案例执行工作流程图 | `09-examples.md` |
| `command-flow.puml` | `command-flow.svg`, `command-flow.png` | 命令执行流程与关系图 | `04-commands.md` |
| `troubleshooting-flow.puml` | `troubleshooting-flow.svg`, `troubleshooting-flow.png` | 问题排查流程图 | `08-troubleshooting.md` |
| `quick-start-flow.puml` | `quick-start-flow.svg`, `quick-start-flow.png` | 快速开始流程图 | `03-quick-start.md` |

## 快速更新图表

```bash
# 进入图表目录
cd /home/zhengjian/claudecode_projects/kuxing/docs/images

# 重新生成所有图表（SVG + PNG）
for f in *.puml; do
    plantuml -tsvg "$f"
    plantuml -tpng "$f"
done

# 或者使用单命令
plantuml -tsvg -tpng *.puml
```

## 图表类型说明

### 1. scheduler-sequence.puml
**类型**: 序列图
**内容**: Scheduler 与 TaskQueue、MemoryStore、ClaudeInvoker 的完整交互流程
**配色**: 调度层（LightBlue）、记忆层（LightGreen）、执行层（LightYellow）

### 2. system-context.puml
**类型**: 系统上下文图（C4 风格）
**内容**: kuxing 与外部系统（文件系统、Claude Code CLI、用户）的交互关系
**配色**: 按系统层级分组

### 3. task-state.puml
**类型**: 状态图
**内容**: 任务在队列、执行、等待、完成的完整生命周期
**配色**: 等待（Pink）、执行（LightGreen）、完成（LightBlue）

### 4. memory-layers.puml
**类型**: 组件交互图
**内容**: 五层记忆系统（会话记忆、项目记忆、全局记忆、轮次记忆、知识沉淀）的架构和交互流程
**配色**: 会话（LightBlue）、项目（LightGreen）、全局（LightYellow）、轮次（Pink）、知识（LightCyan）

### 5. config-workflow.puml
**类型**: 序列图
**内容**: 从创建配置到执行任务的完整工作流程，包括配置验证、任务执行、状态恢复
**配色**: 用户交互（标准）、系统组件（分层配色）

### 6. example-workflow.puml
**类型**: 活动图
**内容**: 案例执行的完整工作流程，包括准备、执行、结果、恢复四个阶段
**配色**: 准备（LightCyan）、执行（LightGreen）、结果（LightYellow）、恢复（Pink）

### 7. command-flow.puml
**类型**: 活动图
**内容**: 命令执行流程与关系，展示从初始化到执行、管理的完整命令链
**配色**: 初始化（LightCyan）、执行（LightGreen）、管理（LightYellow）、辅助工具（Pink）

### 8. troubleshooting-flow.puml
**类型**: 活动图（决策树）
**内容**: 问题排查流程，从遇到问题到解决问题的完整决策路径
**配色**: 安装问题（LightCyan）、配置问题（LightYellow）、执行问题（LightGreen）、记忆问题（Pink）、性能问题（Lavender）

### 9. quick-start-flow.puml
**类型**: 活动图
**内容**: 快速开始流程，展示从创建配置到运行任务的 5 个关键步骤
**配色**: 创建配置（LightCyan）、初始化项目（LightBlue）、运行任务（LightGreen）、查看状态（LightYellow）、下一步（Pink）

## PlantUML 配色规范

### 序列图配色

```plantuml
box "调度层" #LightBlue
end box
box "记忆层" #LightGreen
end box
box "执行层" #LightYellow
end box
```

### 组件图配色

```plantuml
skinparam component {
    BackgroundColor<<cli>> LightBlue
    BackgroundColor<<scheduler>> LightGreen
    BackgroundColor<<memory>> LightYellow
    BackgroundColor<<external>> LightGray
}
```

### Note 配色

```plantuml
note right #FFFACD    ' 关键信息（柠檬绸色）
note right #ADD8E6    ' 配置信息（浅蓝色）
note right #98FB98    ' 成功状态（苍绿色）
note right #FFB6C1    ' 错误信息（浅粉色）
```

## 如何修改图表

### 1. 编辑源文件

```bash
vim /home/zhengjian/claudecode_projects/kuxing/docs/images/scheduler-sequence.puml
```

### 2. 重新生成

```bash
cd /home/zhengjian/claudecode_projects/kuxing/docs/images
plantuml -tsvg -tpng scheduler-sequence.puml
```

### 3. 查看结果

```bash
# 查看生成的 SVG
ls -la *.svg

# 查看生成的 PNG
ls -la *.png
```

## 依赖工具

- **PlantUML**: `brew install plantuml` 或 `apt-get install plantuml`
- **Java**: PlantUML 运行环境（JRE 8+）
- **Graphviz**: 图表布局引擎（可选，用于复杂布局）

## 在文档中嵌入图表

使用相对路径引用：

```markdown
![调度器执行序列图](./images/scheduler-sequence.svg)
![系统上下文图](./images/system-context.svg)
![任务状态图](./images/task-state.svg)
![记忆层次交互图](./images/memory-layers.svg)
![配置工作流程图](./images/config-workflow.svg)
![案例执行工作流程图](./images/example-workflow.svg)
![命令执行流程图](./images/command-flow.svg)
![问题排查流程图](./images/troubleshooting-flow.svg)
![快速开始流程图](./images/quick-start-flow.svg)
```

## 图表维护建议

1. **源文件优先**: 始终保留 .puml 源文件，便于版本控制和修改
2. **同时生成两种格式**: SVG 适合复杂图表缩放查看，PNG 兼容性更好
3. **统一配色**: 在相关图表中使用一致的配色方案
4. **添加图例**: 复杂图表添加图例说明颜色/符号含义

---

**最后更新**: 2026-04-08
**维护建议**: 修改图表前先阅读源文件理解结构，修改后重新生成确保显示正确