# 常见问题解答

本文档汇总了使用苦行僧（kuxing）过程中常见的错误、问题及解决方案。

## 目录

- [安装问题](#安装问题)
- [配置问题](#配置问题)
- [执行问题](#执行问题)
- [记忆系统问题](#记忆系统问题)
- [性能问题](#性能问题)

---

## 安装问题

### 1. Python 版本不兼容

**错误信息**：
```
Python version mismatch. Expected 3.8+, got 3.7.x
```

**原因**：苦行僧需要 Python 3.8 或更高版本。

**解决方案**：
```bash
# 检查当前 Python 版本
python3 --version

# 如果版本低于 3.8，使用 pyenv 或 conda 升级
# macOS
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev
```

---

### 2. Claude CLI 未安装或未配置

**错误信息**：
```
Error: Claude CLI not found. Please install Claude CLI first.
```

**解决方案**：
```bash
# 1. 安装 Claude CLI
npm install -g @anthropic-ai/claude-code

# 2. 验证安装
claude --version

# 3. 登录（如果需要）
claude auth

# 4. 设置环境变量（可选）
export CLAUDE_API_KEY=your-api-key
```

---

### 3. 依赖安装失败

**错误信息**：
```
pip install -r requirements.txt failed
```

**解决方案**：
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或升级 pip 后重试
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 配置问题

### 4. YAML 格式错误

**错误信息**：
```
Error: Invalid YAML format in config.yaml
```

**常见原因**：
- Tab 缩进（YAML 只支持空格）
- 缺少引号导致特殊字符被解析
- 重复的键名

**解决方案**：
```bash
# 使用 yaml lint 工具检查
pip install pyyaml
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 常见错误修复
# ❌ 错误：使用 Tab 缩进
tasks:
	- name: task1

# ✅ 正确：使用 2 空格缩进
tasks:
  - name: task1

# ❌ 错误：包含冒号未加引号
description: "这是一个任务: 执行操作"

# ✅ 正确：特殊字符用引号包裹
description: "这是一个任务: 执行操作"
```

---

### 5. 任务依赖循环

**错误信息**：
```
Error: Circular dependency detected in tasks
```

**原因**：任务 A 依赖 B，任务 B 依赖 A，形成循环。

**解决方案**：
```yaml
# ❌ 错误配置
tasks:
  - name: task_a
    depends_on: [task_b]
  - name: task_b
    depends_on: [task_a]

# ✅ 正确配置：移除循环依赖
tasks:
  - name: task_a
  - name: task_b
    depends_on: [task_a]
```

---

### 6. 无效的 执行模式

**错误信息**：
```
Error: Invalid execution_mode. Expected serial/parallel/loop
```

**解决方案**：
```yaml
# 检查 config.yaml 中的 execution_mode
execution_mode: serial  # ✅ 有效值：serial, parallel, loop

# loop 模式需要 loop_config
loop_config:
  max_rounds: 10
  stop_condition: "all_tasks_completed"
```

---

### 7. 路径不存在

**错误信息**：
```
Error: Project path does not exist: /path/to/project
```

**解决方案**：
```bash
# 1. 检查路径是否正确
ls -la /path/to/project

# 2. 使用绝对路径
project_path: "/home/user/my-project"

# 3. 使用相对路径（相对于 config.yaml 所在目录）
project_path: "../my-project"
```

---

## 执行问题

### 8. 任务执行失败

**错误信息**：
```
Task task_name failed with exit code 1
```

**排查步骤**：

1. **查看详细日志**：
```bash
# 查看最近一次执行的日志
python cli.py status --project-name "项目名" --verbose

# 查看特定轮次的日志
python cli.py show --project-name "项目名" --round 5
```

2. **检查任务命令是否正确**：
```yaml
tasks:
  - name: build
    command: "npm run build"  # 确保命令存在且可执行
```

3. **检查工作目录**：
```yaml
tasks:
  - name: build
    command: "npm run build"
    working_dir: "/home/user/project"  # 确保路径正确
```

4. **检查环境变量**：
```bash
# 在项目目录执行命令测试
cd /path/to/project
npm run build
```

---

### 9. 串行模式任务未按顺序执行

**原因**：可能配置了 `parallel: true` 而非 `serial` 模式。

**解决方案**：
```yaml
# 确保使用 serial 模式
execution_mode: serial

# 或者显式设置 parallel: false
tasks:
  - name: task1
    parallel: false
```

---

### 10. 并行模式任务同时失败

**错误信息**：
```
Multiple tasks failed simultaneously in parallel mode
```

**排查**：
1. 检查网络连接
2. 检查资源限制（内存、CPU）
3. 查看各个任务的独立日志

**解决方案**：
```yaml
# 使用串行模式调试
execution_mode: serial

# 或限制并行度
execution_mode: parallel
parallel_config:
  max_parallel: 2  # 限制同时执行的任务数
```

---

### 11. 循环模式无法停止

**错误信息**：
```
Loop mode keeps running, stop_condition not met
```

**排查**：
1. 检查 `stop_condition` 配置
2. 检查 `max_rounds` 限制
3. 查看任务状态

**解决方案**：
```bash
# 手动停止
Ctrl+C

# 或使用 reset 命令重置状态
python cli.py reset --project-name "项目名"

# 确保配置了合理的停止条件
loop_config:
  max_rounds: 100
  stop_condition: "all_tasks_completed"  # 或 "goal_achieved"
```

---

### 12. Claude CLI 调用失败

**错误信息**：
```
Error: Failed to invoke Claude CLI: connection timeout
```

**原因**：网络问题或 Claude API 不可用。

**解决方案**：
```bash
# 1. 检查网络连接
ping api.anthropic.com

# 2. 检查 Claude CLI 状态
claude --version
claude auth

# 3. 设置更长的超时时间
export CLAUDE_TIMEOUT=120

# 4. 使用代理（如果需要）
export HTTPS_PROXY=http://proxy:8080
```

---

### 13. 上下文窗口溢出

**错误信息**：
```
Error: Context window exceeded. Current: 150000, Max: 200000
```

**原因**：项目上下文或会话记忆文件过大。

**解决方案**：

1. **清理历史会话**：
```bash
# 查看记忆目录大小
du -sh memory/

# 清理旧会话（保留最近 N 轮）
python cli.py reset --project-name "项目名" --keep-rounds 10
```

2. **配置自动压缩**：
```yaml
# 在 config.yaml 中启用 LLM 压缩
memory_config:
  llm_compression:
    enabled: true
    max_session_size: 20000  # 字符数
```

3. **清理共享上下文**：
```bash
# 查看共享上下文大小
cat shared_context/context.md | wc -c

# 精简内容
```

---

## 记忆系统问题

### 14. 记忆文件丢失

**错误信息**：
```
Warning: Session memory file not found: memory/project_name/session.md
```

**原因**：
- 首次运行该项目
- 手动删除了记忆文件
- 路径配置错误

**解决方案**：

1. **如果是首次运行，无需处理**，系统会自动创建。

2. **如果是路径问题，检查配置**：
```yaml
memory_dir: "memory"  # 确保目录存在
```

3. **重新初始化**：
```bash
python cli.py init --project-name "项目名"
```

---

### 15. MEMORY.md 索引过期

**问题**：MEMORY.md 内容与实际记忆文件不同步。

**解决方案**：

1. **手动重建索引**：
```bash
# 删除旧索引
rm memory/project_name/MEMORY.md

# 系统会在下次执行时自动创建
```

2. **验证索引**：
```bash
# 查看索引内容
cat memory/project_name/MEMORY.md

# 手动检查对应的记忆文件是否存在
ls -la memory/project_name/
```

---

### 16. 会话记忆结构不完整

**问题**：session.md 缺少必要的 section。

**解决方案**：

1. **检查文件格式**：
```bash
# 查看 session.md 结构
head -50 memory/project_name/session.md
```

2. **手动补全**：
```markdown
<!-- 确保包含以下 section -->
# 会话标题
- **执行轮次**: 5
- **当前状态**: 运行中
- **下一步计划**:
<!-- 其他必要内容 -->
```

3. **使用更新命令**：
```bash
python cli.py update-memory --project-name "项目名"
```

---

### 17. 自动记忆更新失败

**错误信息**：
```
Error: Failed to update memory: permission denied
```

**原因**：记忆目录权限不足。

**解决方案**：
```bash
# 检查目录权限
ls -la memory/project_name/

# 修复权限
chmod 755 memory/project_name/
chmod 644 memory/project_name/*.md
```

---

## 性能问题

### 18. 执行速度慢

**排查**：

1. **检查是否为首次运行**（首次运行需要创建大量文件）。

2. **检查网络延迟**：
```bash
# 测试 API 响应时间
curl -w "%{time_total}" -o /dev/null https://api.anthropic.com
```

3. **检查并行任务数**：
```yaml
# 过多并行任务可能导致资源竞争
execution_mode: parallel
parallel_config:
  max_parallel: 4  # 尝试减少并行数
```

**优化建议**：

- 使用 `serial` 模式代替 `parallel`（减少上下文开销）
- 减少 `context_summary_lines`（减少注入的上下文量）
- 清理不必要的记忆文件

---

### 19. 内存占用过高

**错误信息**：
```
Warning: Memory usage high. Current: 1.5GB
```

**原因**：
- 会话记忆文件过大
- 并行任务过多
- 上下文摘要过长

**解决方案**：

1. **启用 LLM 压缩**：
```yaml
memory_config:
  llm_compression:
    enabled: true
```

2. **减少并行度**：
```yaml
parallel_config:
  max_parallel: 2
```

3. **清理旧记忆**：
```bash
# 保留最近 20 轮记忆
python cli.py reset --project-name "项目名" --keep-rounds 20
```

---

### 20. 磁盘空间不足

**排查**：
```bash
# 检查记忆目录大小
du -sh memory/*

# 检查可用空间
df -h .
```

**清理方案**：
```bash
# 1. 删除旧轮次记录
for dir in memory/*/; do
  # 保留最近 30 轮
  ls -t "$dir"rounds/ | tail -n +31 | xargs -I {} rm -rf "$dir/rounds/{}"
done

# 2. 清理会话记忆（保留最新）
for file in memory/*/session.md; do
  head -100 "$file" > "$file.tmp" && mv "$file.tmp" "$file"
done

# 3. 清理知识沉淀（如果需要）
find memory/ -name "knowledge_base.md" -size +1M -exec truncate -s 500K {} \;
```

---

## 高级问题

### 21. 配置验证失败

**错误信息**：
```
Error: Config validation failed: 'tasks' is a required property
```

**排查步骤**：
```bash
# 1. 检查 config.yaml 语法
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"

# 2. 验证必需字段
# 确保包含：
# - project_name
# - project_path
# - tasks (至少一个)
```

---

### 22. 状态文件损坏

**错误信息**：
```
Error: Failed to load state.json: JSONDecodeError
```

**原因**：状态文件被手动修改或意外损坏。

**解决方案**：
```bash
# 1. 备份损坏的文件
cp memory/project_name/state.json memory/project_name/state.json.bak

# 2. 从轮次记录重建状态
# 查看最新的轮次文件
ls -lt memory/project_name/rounds/ | head -5

# 3. 手动创建基本状态
cat > memory/project_name/state.json << 'EOF'
{
  "project_name": "项目名",
  "current_round": 1,
  "status": "initialized",
  "completed_tasks": [],
  "pending_tasks": ["task1", "task2"]
}
EOF

# 4. 重置执行状态
python cli.py reset --project-name "项目名"
```

---

### 23. 多项目记忆混淆

**问题**：切换项目后使用了错误的记忆。

**原因**：未正确配置 `memory_dir`。

**解决方案**：

1. **每个项目使用独立的记忆目录**：
```bash
# 项目 A
python cli.py run --config project_a.yaml --memory-dir memory/project_a

# 项目 B
python cli.py run --config project_b.yaml --memory-dir memory/project_b
```

2. **或使用项目 slug 自动隔离**：
```bash
# 不同项目名自动使用不同目录
python cli.py run --project-name "项目A" ...
python cli.py run --project-name "项目B" ...
```

---

### 24. 自定义 Prompt 不生效

**问题**：修改 prompts.py 后没有效果。

**排查**：
1. 检查 Prompt 文件语法
2. 确认环境变量配置正确
3. 检查缓存

**解决方案**：
```bash
# 1. 清除 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +

# 2. 重启执行
python cli.py reset --project-name "项目名"
python cli.py run --project-name "项目名"
```

---

## 获取帮助

### 调试模式

启用详细日志：
```bash
# 设置调试环境变量
export KUXING_DEBUG=1

# 或在命令中指定
python cli.py run --project-name "项目名" --verbose
```

### 查看完整日志

```bash
# 查看最近的错误
python cli.py status --project-name "项目名" 2>&1 | grep -i error

# 导出完整日志
python cli.py show --project-name "项目名" --all > debug.log
```

### 提交问题

遇到无法解决的问题时，请提供：

1. `python cli.py --version` 输出
2. 配置文件（脱敏后）
3. 完整错误日志
4. 复现步骤

---

## 相关文档

- [安装指南](./02-installation.md)
- [快速开始](./03-quick-start.md)
- [命令参考](./04-commands.md)
- [配置指南](./05-config-guide.md)
- [调度器架构](./06-scheduler-architecture.md)
- [记忆架构](./07-memory-architecture.md)

---

**最后更新**：2026-04-03
