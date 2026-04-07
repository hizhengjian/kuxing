# 完整使用案例

本文档提供了苦行僧（kuxing）的完整使用案例，涵盖从入门到高级的多种场景。

## 目录

- [案例 1：文档写作任务](#案例-1文档写作任务)
- [案例 2：代码重构项目](#案例-2代码重构项目)
- [案例 3：持续集成监控](#案例-3持续集成监控)
- [案例 4：多轮调试任务](#案例-4多轮调试任务)
- [案例 5：循环模式长任务](#案例-5循环模式长任务)
- [案例 6：并行测试套件](#案例-6并行测试套件)

---

## 案例 1：文档写作任务

### 场景

为一个新项目创建完整的技术文档，需要跨多个会话完成。

### 配置文件

```yaml
# examples/write_docs.yaml
project_name: "文档写作项目"
project_path: "/home/user/new-project"
mode: serial

tasks:
  - id: create_overview
    type: agent
    description: "创建项目概览文档"
    prompt_template: |
      为 /home/user/new-project 项目创建 README.md 文档，
      包含：
      1. 项目简介
      2. 核心功能
      3. 快速开始
      4. 项目结构
    expected_output: "README.md 文档，包含项目简介、核心功能、快速开始和项目结构"

  - id: create_api_docs
    type: agent
    description: "创建 API 参考文档"
    depends_on: [create_overview]
    prompt_template: |
      基于现有代码，创建 API 参考文档 docs/api.md，
      包含所有公开接口的说明和使用示例。
    expected_output: "API 参考文档 docs/api.md，包含所有公开接口的说明和使用示例"

  - id: create_guide
    type: agent
    description: "创建开发指南"
    depends_on: [create_overview]
    prompt_template: |
      创建开发指南 docs/DEVELOPMENT.md，
      包含开发环境设置、本地运行、测试方法等。
    expected_output: "开发指南 docs/DEVELOPMENT.md，包含开发环境设置、本地运行、测试方法"

  - id: review_docs
    type: agent
    description: "审阅并完善所有文档"
    depends_on: [create_api_docs, create_guide]
    prompt_template: |
      审阅已创建的文档，检查：
      1. 内容完整性和准确性
      2. 格式一致性
      3. 代码示例可运行性
      4. 修复发现的问题
    expected_output: "审阅报告，列出发现的问题和修复状态"
```

### 执行流程

```bash
# 1. 创建任务配置
python cli.py create-task --project-name "文档写作项目"

# 2. 编辑生成的配置文件
vim examples/write_docs.yaml

# 3. 运行执行
python cli.py --config examples/write_docs.yaml run

# 4. 查看状态
python cli.py status --project-name "文档写作项目"

# 5. 如果中断，可随时恢复
python cli.py resume --project-name "文档写作项目"
```

### 预期输出

```
=== 任务执行状态 ===
项目: 文档写作项目
当前轮次: 4/4
执行模式: serial

任务进度:
  [✓] create_overview (1/4)
  [✓] create_api_docs (2/4)
  [✓] create_guide (3/4)
  [ ] review_docs (4/4)

状态: 运行中 - 等待 review_docs 执行
```

---

## 案例 2：代码重构项目

### 场景

将一个遗留的 Python 2 项目重构为 Python 3，并添加类型注解。

### 配置文件

```yaml
# examples/refactor_python.yaml
project_name: "Python 重构项目"
project_path: "/home/user/legacy-project"
mode: serial

tasks:
  - id: analyze_codebase
    type: agent
    description: "分析现有代码库"
    prompt_template: |
      分析 /home/user/legacy-project 中的所有 Python 文件：
      1. 统计代码行数和文件数
      2. 识别 Python 2 特有语法（print 语句、unicode 等）
      3. 识别过时的库和依赖
      4. 生成重构计划报告
    expected_output: "重构计划报告，包含待转换文件列表"

  - id: update_requirements
    type: agent
    description: "更新依赖文件"
    depends_on: [analyze_codebase]
    prompt_template: |
      1. 将 requirements.txt 转换为 Python 3 兼容版本
      2. 替换已废弃的库（如 pyyaml → pyyaml）
      3. 添加类型检查相关依赖（mypy、typeshed）
    expected_output: "更新的 requirements.txt 文件"

  - id: refactor_core_modules
    type: agent
    description: "重构核心模块"
    depends_on: [update_requirements]
    prompt_template: |
      重构核心模块（src/core/）：
      1. 将 print 语句改为 print() 函数
      2. 添加类型注解
      3. 替换过时的语法
      4. 确保重构后测试通过
    expected_output: "重构后的核心模块文件"

  - id: refactor_utils
    type: agent
    description: "重构工具模块"
    depends_on: [update_requirements]
    prompt_template: |
      重构工具模块（src/utils/）：
      1. 同上类型转换
      2. 保持向后兼容性
    expected_output: "重构后的工具模块文件"

  - id: run_tests
    type: agent
    description: "运行完整测试套件"
    depends_on: [refactor_core_modules, refactor_utils]
    prompt_template: |
      1. 运行 pytest 确保所有测试通过
      2. 运行 mypy 进行类型检查
      3. 生成测试报告
    expected_output: "测试报告，包含测试通过率和类型检查结果"

  - id: final_review
    type: agent
    description: "最终代码审查"
    depends_on: [run_tests]
    prompt_template: |
      1. 审查所有变更
      2. 确保代码质量
      3. 更新文档
    expected_output: "代码审查报告"
```

### 循环模式变体

如果重构任务需要更多轮次（持续到代码质量达标）：

```yaml
# examples/refactor_python_loop.yaml
project_name: "Python 重构项目（循环）"
project_path: "/home/user/legacy-project"
mode: loop

loop_config:
  task_id: refactor_and_test
  max_rounds: 50
  stop_condition: ""
  first_task_id: analyze_codebase

tasks:
  - id: analyze_codebase
    type: agent
    description: "分析现有代码库"
    prompt_template: |
      分析 /home/user/legacy-project 中的所有 Python 文件：
      1. 统计代码行数和文件数
      2. 识别 Python 2 特有语法
      3. 生成重构计划
    expected_output: "重构计划报告"

  - id: refactor_and_test
    type: agent
    description: "循环重构任务"
    prompt_template: |
      继续重构工作：
      1. 选择下一个待重构的模块
      2. 应用 Python 3 转换
      3. 添加类型注解
      4. 运行相关测试
      5. 报告进度

      如果所有模块已完成，检查测试覆盖率是否达标。
    expected_output: "重构后的模块和测试结果"
```

### 执行流程

```bash
# 串行模式（推荐用于此类项目）
python cli.py --config examples/refactor_python.yaml run

# 或使用循环模式（需要手动停止）
python cli.py --config examples/refactor_python_loop.yaml run

# 查看详细状态
python cli.py status --project-name "Python 重构项目" --verbose

# 恢复执行（如中断后）
python cli.py resume --project-name "Python 重构项目"
```

---

## 案例 3：持续集成监控

### 场景

监控一个持续集成流水线，当构建失败时自动分析问题并尝试修复。

### 配置文件

```yaml
# examples/monitor_build.yaml
project_name: "CI 监控项目"
project_path: "/home/user/ci-project"
mode: loop

loop_config:
  task_id: check_build_status
  max_rounds: 100
  stop_condition: ""

tasks:
  - id: check_build_status
    type: agent
    description: "检查 CI 构建状态"
    prompt_template: |
      检查 CI 构建状态：
      1. 查询 CI API 获取最新构建状态
      2. 如果有失败，记录失败信息
      3. 报告当前状态
    expected_output: "构建状态报告"

  - id: analyze_failure
    type: agent
    description: "分析构建失败原因"
    prompt_template: |
      分析构建失败原因：
      1. 下载构建日志
      2. 识别失败步骤和错误信息
      3. 分析错误根因
      4. 生成问题分析报告
    expected_output: "问题分析报告，包含失败原因和修复建议"

  - id: attempt_fix
    type: agent
    description: "尝试修复问题"
    prompt_template: |
      尝试修复问题：
      1. 根据分析结果修复代码
      2. 提交修复
      3. 触发重新构建
      4. 等待构建结果
    expected_output: "修复结果和重新构建状态"

  - id: report_status
    type: agent
    description: "生成状态报告"
    prompt_template: |
      生成状态报告：
      1. 总结本轮执行结果
      2. 如果问题未解决，准备下一轮分析
      3. 更新项目记忆
    expected_output: "状态总结报告"
```

### 环境变量配置

环境变量可在任务 prompt_template 中使用，或通过 shell 预先设置：

```bash
# 设置环境变量后运行
export CI_API_URL="https://api.ci.example.com"
export CI_TOKEN="your-ci-token"
export SLACK_WEBHOOK="your-webhook-url"

python cli.py --config examples/monitor_build.yaml run
```

### 执行流程

```bash
# 设置环境变量
export CI_TOKEN=your-ci-token
export SLACK_WEBHOOK=your-webhook-url

# 启动监控（循环模式）
python cli.py --config examples/monitor_build.yaml run

# 在另一个终端查看状态
watch -n 30 python cli.py status --project-name "CI 监控项目"

# 手动停止
# 按 Ctrl+C 或
python cli.py reset --project-name "CI 监控项目"
```

---

## 案例 4：多轮调试任务

### 场景

调试一个复杂的内存泄漏问题，需要多轮分析才能定位根因。

### 配置文件

```yaml
# examples/debug_memory_leak.yaml
project_name: "内存泄漏调试"
project_path: "/home/user/target-project"
mode: loop

loop_config:
  task_id: debug_cycle
  max_rounds: 20
  stop_condition: ""

tasks:
  - id: initial_analysis
    type: agent
    description: "初步内存分析"
    prompt_template: |
      开始调试内存泄漏问题：
      1. 运行应用并监控内存使用
      2. 使用 memory_profiler 分析内存增长
      3. 生成初步分析报告
    expected_output: "初步分析报告，包含可疑对象列表"

  - id: deep_dive
    type: agent
    description: "深入分析内存泄漏"
    prompt_template: |
      深入分析：
      1. 使用 objgraph 追踪对象增长
      2. 识别可疑的对象类型
      3. 分析垃圾回收行为
      4. 定位可能的泄漏点
    expected_output: "深入分析报告，包含泄漏点定位"

  - id: verify_hypothesis
    type: agent
    description: "验证泄漏假设"
    prompt_template: |
      验证假设：
      1. 添加内存追踪代码
      2. 编写复现脚本
      3. 确认泄漏点
      4. 测量修复前后的内存差异
    expected_output: "验证结果，确认的泄漏点"

  - id: implement_fix
    type: agent
    description: "实现修复"
    prompt_template: |
      实现修复：
      1. 修复已确认的泄漏点
      2. 添加资源清理代码
      3. 确保修复不引入新问题
    expected_output: "修复后的代码变更"

  - id: long_run_test
    type: agent
    description: "长时间运行测试"
    prompt_template: |
      长时间运行测试：
      1. 运行应用至少 1 小时
      2. 监控内存使用曲线
      3. 确认泄漏已修复
      4. 生成最终报告
    expected_output: "测试报告，确认泄漏已修复"

  - id: debug_cycle
    type: agent
    description: "调试循环任务"
    prompt_template: |
      执行调试循环：
      1. 收集新的内存数据
      2. 分析与上一轮的差异
      3. 提出下一个假设
      4. 验证或推翻假设

      当问题解决时，输出 "ISSUE_RESOLVED" 标记。
    expected_output: "调试进度报告"
```

### 执行流程

```bash
# 启动调试会话
python cli.py --config examples/debug_memory_leak.yaml run

# 查看实时日志
python cli.py show --project-name "内存泄漏调试" --round 5 --verbose

# 恢复执行
python cli.py resume --project-name "内存泄漏调试"

# 当问题解决后，停止循环
python cli.py reset --project-name "内存泄漏调试"
```

---

## 案例 5：循环模式长任务

### 场景

训练一个机器学习模型，需要持续调参和评估直到模型收敛。

### 配置文件

```yaml
# examples/ml_training.yaml
project_name: "ML 模型训练"
project_path: "/home/user/ml-project"
mode: loop

loop_config:
  task_id: train_epoch
  max_rounds: 200
  stop_condition: ""

tasks:
  - id: train_epoch
    type: agent
    description: "执行训练轮次"
    prompt_template: |
      执行训练轮次：
      1. 加载最新模型权重
      2. 训练一个 epoch
      3. 在验证集上评估
      4. 记录指标（loss, accuracy, F1）
      5. 保存模型检查点
    expected_output: "训练指标记录，包含 loss、accuracy、F1"

  - id: evaluate_and_adjust
    type: agent
    description: "评估并调整"
    prompt_template: |
      评估并调整：
      1. 分析训练曲线
      2. 检查过拟合/欠拟合
      3. 建议超参数调整
      4. 实施调整（如有必要）
    expected_output: "评估报告和调整建议"

  - id: final_evaluation
    type: agent
    description: "最终评估"
    prompt_template: |
      最终评估：
      1. 在测试集上评估模型
      2. 生成评估报告
      3. 如果达标，输出 "TRAINING_COMPLETE"
      4. 否则继续下一轮
    expected_output: "最终评估报告"
```

### 目标达成条件

```yaml
# 在 prompt 中使用特定标记表示完成
# prompt 中包含：输出 "TRAINING_COMPLETE" 表示训练完成
```

### 执行流程

```bash
# 启动训练
python cli.py --config examples/ml_training.yaml run

# 监控进度
watch -n 60 python cli.py status --project-name "ML 模型训练"

# 查看训练曲线
python cli.py show --project-name "ML 模型训练" | grep -A 5 "accuracy"

# 中断并恢复
Ctrl+C
python cli.py resume --project-name "ML 模型训练"

# 训练完成后
python cli.py reset --project-name "ML 模型训练"
```

---

## 案例 6：并行测试套件

### 场景

在多个平台上并行运行测试，快速获取测试结果。

### 配置文件

```yaml
# examples/parallel_testing.yaml
project_name: "并行测试项目"
project_path: "/home/user/cross-platform-project"
mode: parallel

tasks:
  - id: test_linux_py38
    type: agent
    description: "Linux Python 3.8 测试"
    prompt_template: |
      在 Linux Python 3.8 环境中运行测试：
      1. 设置虚拟环境
      2. 安装依赖
      3. 运行 pytest
      4. 生成测试报告
    expected_output: "测试报告，包含测试用例数和通过率"

  - id: test_linux_py39
    type: agent
    description: "Linux Python 3.9 测试"
    prompt_template: |
      在 Linux Python 3.9 环境中运行测试...
    expected_output: "测试报告"

  - id: test_mac_py38
    type: agent
    description: "macOS Python 3.8 测试"
    prompt_template: |
      在 macOS Python 3.8 环境中运行测试...
    expected_output: "测试报告"

  - id: test_mac_py39
    type: agent
    description: "macOS Python 3.9 测试"
    prompt_template: |
      在 macOS Python 3.9 环境中运行测试...
    expected_output: "测试报告"

  - id: test_windows
    type: agent
    description: "Windows 测试"
    prompt_template: |
      在 Windows 环境中运行测试...
    expected_output: "测试报告"

  - id: aggregate_results
    type: agent
    description: "汇总测试结果"
    depends_on: [test_linux_py38, test_linux_py39, test_mac_py38, test_mac_py39, test_windows]
    prompt_template: |
      汇总所有平台的测试结果：
      1. 收集各平台测试报告
      2. 生成跨平台兼容性报告
      3. 识别平台特定问题
      4. 提出修复建议
    expected_output: "跨平台兼容性报告"
```

### 执行流程

```bash
# 运行并行测试
python cli.py --config examples/parallel_testing.yaml run

# 查看并行执行状态
python cli.py status --project-name "并行测试项目"

# 等待完成后查看汇总结果
python cli.py show --project-name "并行测试项目" --round 6
```

### 预期输出

```
=== 并行测试执行 ===
任务状态:
  [✓] test_linux_py38 - 120 tests, 0 failures
  [✓] test_linux_py39 - 120 tests, 2 failures
  [✓] test_mac_py38 - 118 tests, 1 failure
  [✓] test_mac_py39 - 120 tests, 0 failures
  [✓] test_windows - 115 tests, 5 failures
  [ ] aggregate_results - 汇总中

并行执行时间: 5m 32s
```

---

## 高级配置示例

### 示例 A：多阶段部署

```yaml
# 注意：苦行僧本身不支持条件执行，以下为串行模式的替代方案
project_name: "部署项目"
project_path: "/home/user/deploy"
mode: serial

tasks:
  - id: check_branch
    type: agent
    description: "检查 Git 分支"
    prompt_template: |
      检查当前 Git 分支，输出 "develop" 或 "release"
    expected_output: "分支名称"

  - id: deploy_to_staging
    type: agent
    description: "部署到预发环境"
    prompt_template: |
      部署应用到预发环境...
    expected_output: "部署结果"

  - id: deploy_to_production
    type: agent
    description: "部署到生产环境"
    prompt_template: |
      部署应用到生产环境...
    expected_output: "部署结果"
```

### 示例 B：循环模式持续集成

```yaml
project_name: "持续集成"
project_path: "/home/user/ci"
mode: loop

loop_config:
  task_id: run_tests
  max_rounds: 100
  stop_condition: ""

tasks:
  - id: run_tests
    type: agent
    description: "运行测试"
    prompt_template: |
      运行测试：
      1. 执行完整测试套件
      2. 分析测试结果
      3. 如果有失败，尝试修复
      4. 报告测试状态
    expected_output: "测试报告，包含通过/失败数量"
```

### 示例 C：循环模式 + 停止条件

```yaml
project_name: "质量改进"
project_path: "/home/user/project"
mode: loop

loop_config:
  task_id: improve_quality
  max_rounds: 50
  stop_condition: ""

tasks:
  - id: improve_quality
    type: agent
    description: "持续改进代码质量"
    prompt_template: |
      改进代码质量：
      1. 运行代码质量检查
      2. 修复发现的问题
      3. 优化性能瓶颈
      4. 报告改进进度

      当代码质量达标时，输出 "QUALITY_GOAL_ACHIEVED"
    expected_output: "质量改进报告"
```

---

## 相关文档

- [安装指南](./02-installation.md)
- [快速开始](./03-quick-start.md)
- [命令参考](./04-commands.md)
- [配置指南](./05-config-guide.md)
- [调度器架构](./06-scheduler-architecture.md)
- [记忆架构](./07-memory-architecture.md)
- [常见问题](./08-troubleshooting.md)

---

**最后更新**：2026-04-07
