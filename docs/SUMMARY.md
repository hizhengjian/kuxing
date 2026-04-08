# 文档总结

本文档汇总了苦行僧（kuxing）项目的所有技术文档，提供快速索引和导航。

## 文档索引

| 文档 | 说明 | 目标读者 |
|------|------|---------|
| [01-overview.md](01-overview.md) | 项目概览、核心特性、v0.5.0 新功能 | 所有用户 |
| [02-installation.md](02-installation.md) | 安装指南、依赖说明、验证步骤 | 新用户 |
| [03-quick-start.md](03-quick-start.md) | 5 分钟快速开始教程 | 入门用户 |
| [04-commands.md](04-commands.md) | 完整 CLI 命令参考 | 所有用户 |
| [05-config-guide.md](05-config-guide.md) | YAML 配置详解、字段说明 | 高级用户 |
| [06-scheduler-architecture.md](06-scheduler-architecture.md) | 调度器架构、核心流程、状态机 | 开发者 |
| [07-memory-architecture.md](07-memory-architecture.md) | 记忆系统架构、三层记忆、压缩机制 | 开发者 |
| [08-troubleshooting.md](08-troubleshooting.md) | 常见问题解答、错误处理 | 所有用户 |
| [09-examples.md](09-examples.md) | 完整使用案例、配置文件示例 | 所有用户 |
| [10-best-practices.md](10-best-practices.md) | 最佳实践、性能优化、注意事项 | 高级用户 |
| [11-contributing.md](11-contributing.md) | 贡献指南、代码规范、测试要求 | 开发者 |

## 文档层级

```
┌─────────────────────────────────────────────────────────────┐
│                     用户入口                                │
├─────────────────────────────────────────────────────────────┤
│  01-overview.md     项目概览、核心特性、v0.5.0 新功能       │
│  02-installation.md 安装指南                               │
│  03-quick-start.md  快速开始（5 分钟教程）                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     使用参考                                │
├─────────────────────────────────────────────────────────────┤
│  04-commands.md      CLI 命令完整参考                       │
│  05-config-guide.md  YAML 配置详解                         │
│  08-troubleshooting.md 常见问题解答                         │
│  09-examples.md      使用案例（6 个完整示例）               │
│  10-best-practices.md 最佳实践                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     技术架构（开发者）                       │
├─────────────────────────────────────────────────────────────┤
│  06-scheduler-architecture.md  调度器架构                   │
│  07-memory-architecture.md     记忆系统架构                  │
│  11-contributing.md             贡献指南                     │
└─────────────────────────────────────────────────────────────┘
```

## 快速导航

### 新用户
1. 阅读 [01-overview.md](01-overview.md) 了解项目
2. 按照 [02-installation.md](02-installation.md) 安装
3. 完成 [03-quick-start.md](03-quick-start.md) 快速开始

### 日常使用
1. 参考 [04-commands.md](04-commands.md) 使用命令
2. 查看 [09-examples.md](09-examples.md) 查找类似案例
3. 遇到问题查看 [08-troubleshooting.md](08-troubleshooting.md)

### 高级配置
1. 阅读 [05-config-guide.md](05-config-guide.md) 深入理解配置
2. 参考 [10-best-practices.md](10-best-practices.md) 优化实践
3. 查看 [07-memory-architecture.md](07-memory-architecture.md) 了解记忆机制

### 开发者
1. 阅读 [06-scheduler-architecture.md](06-scheduler-architecture.md) 理解调度器
2. 阅读 [07-memory-architecture.md](07-memory-architecture.md) 理解记忆系统
3. 参考 [11-contributing.md](11-contributing.md) 贡献代码

## 图表资源

| 图表 | 文件 | 说明 |
|------|------|------|
| 调度器执行序列图 | [images/scheduler-sequence.svg](images/scheduler-sequence.svg) | Scheduler 与组件的完整交互流程 |
| 系统上下文图 | [images/system-context.svg](images/system-context.svg) | kuxing 与外部系统的交互关系（C4 风格） |
| 任务状态图 | [images/task-state.svg](images/task-state.svg) | 任务的完整生命周期状态机 |
| 记忆层次交互图 | [images/memory-layers.svg](images/memory-layers.svg) | 五层记忆系统的架构和交互流程 |
| 配置工作流程图 | [images/config-workflow.svg](images/config-workflow.svg) | 从创建配置到执行任务的完整流程 |
| 案例执行工作流程图 | [images/example-workflow.svg](images/example-workflow.svg) | 案例执行的四个阶段（准备、执行、结果、恢复） |
| 命令执行流程图 | [images/command-flow.svg](images/command-flow.svg) | 命令执行流程与关系，从初始化到执行、管理的完整命令链 |

详见 [images/README.md](images/README.md)。

## 配置示例

| 示例 | 文件 | 用途 |
|------|------|------|
| 文档写作 | `examples/write_docs.yaml` | 串行执行文档任务 |
| 构建监控 | `examples/monitor_build.yaml` | 循环监控构建状态 |
| Claude Code 文档 | `examples/claude-code-docs.yaml` | Claude Code 项目文档生成 |
| 50 轮分析 | `examples/claude-code-50rounds.yaml` | 长任务 50 轮循环执行 |
| 并行测试 | `examples/full-test-v0.5.0.yaml` | 多项目并行执行 |

## 版本信息

- **当前版本**: 0.5.1
- **发布日期**: 2026-04-08
- **主要更新**: 
  - v0.5.1: 修复命令行参数 `--max-rounds` 无法覆盖配置文件的问题
  - v0.5.0: 结构化会话记忆、记忆索引、自动记忆更新

详见 [CHANGELOG.md](../CHANGELOG.md)。

---

**最后更新**: 2026-04-08
