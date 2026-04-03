# 安装指南

## 1. 环境要求

### 系统要求

| 要求 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.8+ | 3.10+ |
| Claude CLI | 最新版本 | 最新版本 |
| 磁盘空间 | 100MB | 500MB |

### 依赖项

| 依赖 | 版本 | 说明 |
|------|------|------|
| pyyaml | - | 配置文件解析 |
| claude | - | Claude Code CLI |

---

## 2. 安装步骤

### 步骤 1：检查 Python 环境

```bash
# 检查 Python 版本
python3 --version

# 如果版本低于 3.8，请升级 Python
# Ubuntu/Debian:
sudo apt-get update && sudo apt-get install python3.10

# macOS:
brew install python@3.10
```

### 步骤 2：安装 Claude CLI

Claude CLI 是苦行僧的核心依赖，必须先安装：

```bash
# 使用 npm 安装
npm install -g @anthropic-ai/claude-code

# 或使用 Claude 官方安装脚本
# 参考: https://docs.anthropic.com/en/docs/claude-code
```

**验证安装：**

```bash
claude --version
```

### 步骤 3：安装苦行僧

**方式一：下载release**

```bash
# 下载最新版本
wget https://github.com/your-repo/kuxing/releases/latest/kuxing.tar.gz

# 解压
tar -xzf kuxing.tar.gz
cd kuxing
```

**方式二：从源码安装**

```bash
# 克隆仓库
git clone https://github.com/your-repo/kuxing.git
cd kuxing

# 安装依赖
pip install -r requirements.txt
```

**方式三：直接使用**

```bash
# 将项目路径添加到 PATH 或创建符号链接
ln -s /path/to/kuxing/cli.py /usr/local/bin/kuxing
chmod +x /usr/local/bin/kuxing
```

### 步骤 4：验证安装

```bash
# 进入项目目录
cd /path/to/kuxing

# 运行版本检查
python cli.py --version

# 查看可用命令
python cli.py --help
```

---

## 3. 目录结构

安装后，苦行僧的目录结构如下：

```
kuxing/
├── cli.py                 # 命令行入口
├── scheduler.py           # 调度器核心
├── memory_store.py        # 记忆存储
├── config_schema.py      # 配置验证
├── prompts.py             # Prompt 模板
├── memory_updater.py      # 记忆更新
├── llm_compressor.py      # LLM 压缩器
├── session_memory.py      # 会话记忆
├── state.py               # 状态管理
├── claude_invoker.py      # Claude 调用
├── task_queue.py          # 任务队列
├── memory/                 # 记忆存储目录
│   ├── default/           # 默认项目记忆
│   │   ├── rounds/       # 执行轮次记录
│   │   ├── config.yaml   # 保存的配置
│   │   ├── MEMORY.md     # 记忆索引
│   │   ├── session.md    # 会话记忆
│   │   └── context.md    # 项目上下文
│   └── shared/           # 全局共享记忆
│       └── context.md
├── examples/             # 配置示例
│   ├── simple.yaml
│   ├── loop.yaml
│   └── parallel.yaml
└── tests/                # 测试文件
```

---

## 4. 快速配置

### 环境变量（可选）

创建 `~/.kuxing/env` 文件配置默认环境变量：

```bash
# Claude API 配置
export ANTHROPIC_API_KEY="sk-..."

# SDK 路径
export ANDROID_SDK_HOME="/opt/android-sdk"
export SDK_PATH="/opt/sdk"

# 常用路径
export WORKSPACE="/path/to/workspace"
```

### 全局共享记忆（可选）

创建全局共享记忆模板：

```bash
python cli.py init-context --global
```

编辑生成的 `~/.kuxing/shared/context.md`：

```markdown
# 全局公共记忆

## SDK 路径
- Android SDK: ${ANDROID_SDK_HOME}
- NDK: ${ANDROID_NDK_HOME}

## 常用参考文档
- API规范: /docs/api-spec.yaml
- 设计文档: /docs/design.md

## 账号配置（使用 ${VAR_NAME} 引用环境变量）
- Harbor: ${HARBOR_USERNAME}
- GitLab: ${GITLAB_TOKEN}
```

---

## 5. 依赖检查

苦行僧会自动检查依赖。如果遇到问题，手动检查：

```bash
# Python 版本
python3 --version  # 需要 3.8+

# pyyaml
python3 -c "import yaml; print(yaml.__version__)"  # 需要已安装

# Claude CLI
claude --version  # 需要已安装且在 PATH 中
```

### 常见问题

**Q: 提示 "缺少 pyyaml 库"**

```bash
pip install pyyaml
```

**Q: 提示 "无法确认Claude是否可用"**

```bash
# 检查 claude 命令是否可用
which claude

# 如果不可用，重新安装 Claude CLI
npm install -g @anthropic-ai/claude-code
```

---

## 6. 卸载

```bash
# 删除项目目录
rm -rf /path/to/kuxing

# 删除全局记忆（可选）
rm -rf ~/.kuxing

# 删除符号链接（如果创建了）
rm /usr/local/bin/kuxing
```

---

## 下一步

- [快速开始](./03-quick-start.md) - 5 分钟快速上手
- [命令参考](./04-commands.md) - 完整命令文档
- [配置指南](./05-config-guide.md) - YAML 配置详解
