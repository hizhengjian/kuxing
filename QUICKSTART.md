# 快速开始指南

## 🚀 5 分钟上手苦行僧 v0.4.0

### 方式 1：使用 create-task 命令（推荐）⭐

```bash
cd ~/claudecode_projects/kuxing

# 交互式创建任务
python cli.py create-task --project-name "我的项目"

# 按提示输入信息：
# 📂 代码路径: /path/to/code
# 📄 文档路径: /path/to/docs
# 📝 项目描述: 分析代码并生成文档
# 🔐 账号信息: GitLab username password
# ⚙️  偏好设置: 喜欢详细注释
# 🔄 最大轮次: 50

# 自动生成：
# ✅ examples/我的项目.yaml
# ✅ memory/我的项目/context.md
# ✅ shared_context/context.md

# 直接运行
python cli.py run --config examples/我的项目.yaml
```

**优势**：
- 一次性生成配置文件和记忆文件
- 无需手动编辑模板
- 自动提取路径、账号等信息
- 后续可手动追加内容

### 方式 2：手动创建（传统方式）

### 1. 验证安装

```bash
cd ~/claudecode_projects/kuxing

# 检查依赖
python cli.py --version

# 运行测试（可选，验证一切正常）
pip install -r requirements-dev.txt
pytest tests/ -v
```

### 2. 初始化记忆模板

```bash
# 初始化全局共享记忆（新位置：项目内）
python cli.py init-context --global

# 编辑全局记忆，添加你的 SDK 路径、账号等
vim shared_context/context.md
```

**示例配置**：
```markdown
# 全局公共记忆

## SDK 路径
- Android SDK: /home/user/Android/Sdk
- Python: /usr/bin/python3

## 账号配置
- Harbor: ${HARBOR_USERNAME}
- GitLab: ${GITLAB_TOKEN}
```

### 3. 创建你的第一个任务

```bash
# 使用示例配置
cp examples/claude-code-50rounds.yaml my-task.yaml

# 编辑配置
vim my-task.yaml
```

**最小配置示例**：
```yaml
project_name: "我的第一个任务"
project_path: "/path/to/your/project"
mode: serial

tasks:
  - id: task_1
    description: "分析项目结构"
    prompt_template: |
      请分析 {project_path} 的项目结构，列出主要文件和目录。
    expected_output: "生成项目结构文档"
```

### 4. 运行任务

```bash
# 先用 dry-run 测试（不调用 Claude）
python cli.py run --config my-task.yaml --dry-run

# 确认无误后正式运行
python cli.py run --config my-task.yaml
```

### 5. 查看结果

```bash
# 查看状态
python cli.py status

# 查看历史
python cli.py show --history

# 查看知识沉淀（自动生成）
cat memory/我的第一个任务/knowledge_base.md

# 查看日志
ls -lt memory/我的第一个任务/logs/
```

---

## 🎯 常见使用场景

### 场景 1: 代码分析（50 轮）

```yaml
project_name: "深度代码分析"
project_path: "/path/to/codebase"
mode: loop

tasks:
  - id: task_plan
    description: "制定分析计划"
    prompt_template: "分析代码库，制定 50 轮分析计划"
    expected_output: "生成分析计划文档"
  
  - id: task_analyze
    description: "执行分析"
    prompt_template: |
      {context_summary}
      
      根据计划执行本轮分析，生成文档。
    expected_output: "生成模块文档"

loop_config:
  first_task_id: task_plan
  task_id: task_analyze
  max_rounds: 50
```

### 场景 2: 持续监控

```yaml
project_name: "构建监控"
project_path: "/path/to/project"
mode: loop

tasks:
  - id: task_monitor
    description: "监控构建状态"
    prompt_template: |
      检查 {project_path} 的构建状态，如果失败则分析原因。
    expected_output: "构建状态报告"

loop_config:
  task_id: task_monitor
  max_rounds: 100
  stop_condition: "连续3次成功"
  interval_seconds: 300  # 每 5 分钟检查一次
```

### 场景 3: 多项目并行

```bash
# 同时运行多个项目
python cli.py parallel --config \
  project-a.yaml \
  project-b.yaml \
  project-c.yaml \
  --loop

# 查看日志
tail -f parallel_logs/*.log
```

---

## 🔧 高级功能

### 环境变量引用

在记忆文件中使用 `${VAR_NAME}` 引用环境变量：

```markdown
## SDK 路径
- Android SDK: ${ANDROID_SDK_HOME}
- Harbor 账号: ${HARBOR_USERNAME}
```

系统会自动替换，并警告未定义的变量：
```
⚠️  警告: 以下环境变量未定义: ANDROID_SDK_HOME
```

### 知识沉淀

每轮执行后，系统自动提取关键发现：

```markdown
# 知识沉淀

## 更新 2026-04-03 10:30:00

**本轮发现**：
发现了性能瓶颈在函数 X

**经验总结**：
建议使用缓存优化
```

后续轮次会自动参考历史知识。

### 断点续传

```bash
# 任务中断后（Ctrl+C）
python cli.py resume

# 或者指定最大轮次
python cli.py resume --max-rounds 20
```

---

## 🧪 开发和测试

### 运行测试

```bash
# 安装测试依赖
pip install -r requirements-dev.txt

# 运行所有测试（0.16 秒完成）
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### 测试特点

- ✅ 使用 mock，不消耗 API 配额
- ✅ 完全离线运行
- ✅ 速度极快（秒级）
- ✅ 34 个测试用例
- ✅ 63% 代码覆盖率

---

## 📚 文档索引

- `README.md` - 完整使用文档
- `CHANGELOG.md` - 版本更新日志
- `SUMMARY.md` - v0.3.0 完善总结
- `tests/README.md` - 测试说明
- `examples/` - 示例配置文件

---

## ❓ 常见问题

### Q: 如何迁移旧版本的全局记忆？

```bash
# 如果之前使用了 ~/.kuxing/shared/
mkdir -p shared_context
cp ~/.kuxing/shared/context.md shared_context/context.md
```

### Q: 测试失败怎么办？

```bash
# 查看详细错误
pytest tests/ -v --tb=short

# 运行单个测试
pytest tests/test_memory_store.py::test_resolve_env_vars -v
```

### Q: 如何查看某一轮的详细信息？

```bash
# 查看 Round 5 的详情
python cli.py show --round 5

# 或者直接查看 JSON
cat memory/{project_slug}/rounds/round_0005.json | jq
```

### Q: 如何清空记忆重新开始？

```bash
# 只清空轮次记忆，保留配置
python cli.py reset --confirm

# 清空所有记忆（包括配置）
python cli.py reset --confirm --clear-all
```

---

## 🎉 开始使用

```bash
# 1. 初始化
python cli.py init-context --global

# 2. 运行示例
python cli.py run --config examples/write_docs.yaml --dry-run

# 3. 查看结果
python cli.py status
```

祝你使用愉快！🚀
