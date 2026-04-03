# 更新日志

## [0.4.0] - 2026-04-03

### 新增功能

#### 1. create-task 命令 ⭐
- **交互式创建任务**：通过问答方式收集项目信息
- **自动生成配置**：自动生成 YAML 配置文件
- **自动生成记忆**：同时生成项目记忆和全局记忆
- **使用方式**：
  ```bash
  python cli.py create-task --project-name "我的项目"
  ```
- **优势**：
  - 一次性完成配置和记忆初始化
  - 无需手动编辑模板
  - 自动提取路径、账号等信息
  - 后续可手动追加内容

#### 2. 自动记忆更新
- **新增 MemoryUpdater 类**：自动从执行结果中提取信息
- **自动提取路径**：发现新的代码路径、文档路径
- **自动提取命令**：记录执行过的命令
- **自动记录错误**：保存遇到的问题和错误信息
- **实现位置**：`memory_updater.py`
- **集成方式**：在 `scheduler.py` 中每轮执行后自动调用

### 改进

#### 1. 工作流程优化
- **之前**：用户需要手动创建配置文件、手动初始化记忆、手动编辑模板
- **现在**：一条命令完成所有初始化，自动生成配置和记忆

#### 2. 记忆系统增强
- **自动更新**：每轮执行后自动更新项目记忆
- **智能提取**：从执行结果中提取关键信息
- **持续积累**：随着执行轮次增加，记忆越来越丰富

#### 3. 文档更新
- 更新 `README.md`：添加 create-task 使用说明
- 更新 `QUICKSTART.md`：推荐使用 create-task 命令
- 新增使用场景说明

### 技术细节

#### create-task 命令流程
```
1. 交互式收集信息
   ├─ 代码路径（可多个）
   ├─ 文档路径（可多个）
   ├─ 项目描述
   ├─ 账号信息（可选）
   ├─ 偏好设置（可选）
   └─ 最大轮次

2. 生成配置文件
   └─ examples/{project_slug}.yaml

3. 生成项目记忆
   └─ memory/{project_slug}/context.md

4. 生成全局记忆（如果有账号/偏好）
   └─ shared_context/context.md

5. 显示运行命令
```

#### MemoryUpdater 工作原理
```python
class MemoryUpdater:
    def update_from_result(self, result: dict):
        # 1. 提取新路径
        new_paths = self._extract_paths(summary)
        if new_paths - self.discovered_paths:
            self._append_paths(new_paths)
        
        # 2. 提取新命令
        new_commands = self._extract_commands(summary)
        if new_commands - self.discovered_commands:
            self._append_commands(new_commands)
        
        # 3. 提取错误信息
        if 'error' in summary or 'failed' in summary:
            error_info = self._extract_error(summary)
            self._append_error(error_info)
```

### 使用示例

#### 示例 1：创建代码分析任务

```bash
$ python cli.py create-task --project-name "代码分析"

🤖 创建任务: 代码分析
==================================================

📂 代码路径（每行一个，输入空行结束）:
  路径: /home/user/project/src
  路径: /home/user/project/include
  路径: 

📄 文档路径（每行一个，输入空行结束）:
  路径: /home/user/project/docs
  路径: 

📝 项目描述（可选）: 分析C++代码并生成文档

🔐 是否需要保存账号信息？(y/n): y
账号信息（格式：服务名 账号 密码，每行一个，输入空行结束）:
  GitLab zhangsan abc123
  

⚙️  是否需要保存偏好设置？(y/n): y
偏好设置（每行一个，输入空行结束）:
  喜欢详细注释
  使用中文文档
  

🔄 最大轮次（默认50）: 50

🔄 正在生成配置和记忆文件...

✅ 已生成配置: examples/代码分析.yaml
✅ 已生成项目记忆: memory/代码分析/context.md
✅ 已生成全局记忆: shared_context/context.md

🚀 可以运行了：
   python cli.py run --config examples/代码分析.yaml

💡 提示：
   - 可以手动编辑 memory/代码分析/context.md 追加项目信息
   - 可以手动编辑 shared_context/context.md 追加全局信息
```

#### 示例 2：自动记忆更新

```bash
# 运行任务
$ python cli.py run --config examples/代码分析.yaml

# Round 1 执行后，自动更新 memory/代码分析/context.md：
## 新发现的路径 (2026-04-03 15:30:00)
- /home/user/project/src/main.cpp
- /home/user/project/include/utils.h

## 新发现的命令 (2026-04-03 15:30:00)
- `gcc -o test test.c`
- `make clean`

# Round 2 遇到错误，自动记录：
## 遇到的问题 (2026-04-03 15:35:00)
- 编译失败，缺少头文件 stdio.h
```

### 破坏性变更

无破坏性变更，完全向后兼容 v0.3.0。

### 升级指南

从 v0.3.0 升级到 v0.4.0：

```bash
# 1. 拉取最新代码
git pull

# 2. 无需额外操作，直接使用新功能
python cli.py create-task --project-name "新项目"

# 3. 现有项目继续正常运行
python cli.py run --config examples/existing-project.yaml
```

---

## [0.3.0] - 2026-04-03

### 新增功能

#### 1. 分层记忆系统优化
- **全局共享记忆路径改为项目内** (`shared_context/context.md`)
  - 之前：`~/.kuxing/shared/context.md`（不便于项目迁移）
  - 现在：`{项目根目录}/shared_context/context.md`（随项目一起迁移）
  - 优势：项目可以直接拷贝到其他机器使用，无需额外配置

#### 2. 环境变量验证
- 在 `memory_store.py` 中增强 `resolve_env_vars()` 方法
- 自动检测未定义的环境变量并警告用户
- 示例：`⚠️  警告: 以下环境变量未定义: ANDROID_SDK_HOME, HARBOR_USERNAME`

#### 3. 自动知识沉淀
- 在 `scheduler.py` 中新增 `_extract_knowledge()` 方法
- 每轮执行成功后自动提取关键发现和经验
- 自动追加到 `knowledge_base.md` 文件
- 关键词触发：发现、注意、问题、解决、优化、改进、建议、经验、教训

#### 4. 完整的单元测试框架
- 新增 `tests/` 目录，包含 34 个测试用例
- 使用 pytest + mock，不消耗 Claude API 配额
- 测试覆盖率：63%（核心模块 70%+）
- 测试速度：0.16 秒完成所有测试
- 测试模块：
  - `test_memory_store.py` - 记忆存储测试（11 个测试）
  - `test_scheduler.py` - 调度器测试（7 个测试）
  - `test_task_queue.py` - 任务队列测试（7 个测试）
  - `test_prompts.py` - Prompt 测试（9 个测试）

### 改进

#### 1. Prompt 解析优化
- 修复 `extract_result_from_output()` 中 `summary` 和 `next_hints` 的解析冲突
- 使用负向前瞻 `(?!...)` 避免贪婪匹配
- 支持更多格式变体

#### 2. 文档更新
- 更新 `README.md`，反映新的记忆路径
- 新增 `tests/README.md`，说明如何运行测试
- 新增 `CHANGELOG.md`，记录版本变更

#### 3. 开发工具
- 新增 `requirements-dev.txt` - 开发依赖（pytest, pytest-cov）
- 新增 `pytest.ini` - pytest 配置
- 更新 `.gitignore` - 忽略测试生成的文件

### 技术细节

#### 记忆系统架构
```
项目根目录/
├── shared_context/          # 全局共享记忆（新位置）
│   └── context.md
└── memory/                  # 项目记忆
    └── {project_slug}/
        ├── context.md       # 项目私有记忆
        └── knowledge_base.md # 自动知识沉淀
```

#### 测试覆盖率详情
| 模块 | 覆盖率 | 说明 |
|------|--------|------|
| state.py | 93% | 数据结构 |
| prompts.py | 82% | Prompt 构建 |
| task_queue.py | 80% | 任务队列 |
| memory_store.py | 76% | 记忆存储 |
| scheduler.py | 73% | 核心调度器 |
| config_schema.py | 61% | 配置加载 |
| claude_invoker.py | 28% | Claude 调用（难以测试） |
| cli.py | 0% | CLI 入口（集成测试） |

### 破坏性变更

⚠️ **全局共享记忆路径变更**
- 如果你之前使用了 `~/.kuxing/shared/context.md`
- 需要手动迁移到项目根目录的 `shared_context/context.md`
- 迁移命令：
  ```bash
  mkdir -p shared_context
  cp ~/.kuxing/shared/context.md shared_context/context.md
  ```

### 使用示例

#### 运行测试
```bash
# 安装测试依赖
pip install -r requirements-dev.txt

# 运行所有测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

#### 初始化记忆
```bash
# 初始化全局共享记忆（现在在项目内）
python cli.py init-context --global

# 初始化项目私有记忆
python cli.py init-context --project --config examples/your-config.yaml
```

---

## [0.2.0] - 2026-04-02

### 新增功能
- 分层记忆系统（全局共享/项目私有/知识沉淀）
- 多项目并行执行
- 循环模式的 first_task 支持

---

## [0.1.0] - 2026-04-01

### 初始版本
- 基础调度器
- 串行/并行/循环三种执行模式
- 状态持久化
- 断点续传
