"""
测试 Scheduler 模块
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from scheduler import Scheduler
from state import TaskState


def test_scheduler_init(temp_dir, sample_config):
    """测试调度器初始化"""
    # 创建配置文件
    config_path = temp_dir / "test_config.yaml"
    config_path.write_text(f"""
project_name: "测试项目"
project_path: "{temp_dir}"
mode: serial
tasks:
  - id: task_1
    description: "任务1"
    prompt_template: "执行任务1"
    expected_output: "完成"
""")

    scheduler = Scheduler(
        base_path=str(temp_dir),
        config_path=str(config_path),
        dry_run=True
    )

    assert scheduler.config.project_name == "测试项目"
    assert scheduler.dry_run is True


def test_scheduler_initialize(temp_dir, sample_config):
    """测试调度器状态初始化"""
    config_path = temp_dir / "test_config.yaml"
    config_path.write_text(f"""
project_name: "测试项目"
project_path: "{temp_dir}"
mode: serial
tasks:
  - id: task_1
    description: "任务1"
    prompt_template: "执行任务1"
    expected_output: "完成"
""")

    scheduler = Scheduler(
        base_path=str(temp_dir),
        config_path=str(config_path),
        dry_run=True
    )

    scheduler.initialize()

    assert scheduler.state is not None
    assert scheduler.state.current_round == 0
    assert len(scheduler.state.tasks) == 1
    assert "task_1" in scheduler.state.tasks


def test_run_single_round_dry_run(temp_dir):
    """测试单轮执行（dry run 模式）"""
    config_path = temp_dir / "test_config.yaml"
    config_path.write_text(f"""
project_name: "测试项目"
project_path: "{temp_dir}"
mode: serial
tasks:
  - id: task_1
    description: "任务1"
    prompt_template: "执行任务1"
    expected_output: "完成"
""")

    scheduler = Scheduler(
        base_path=str(temp_dir),
        config_path=str(config_path),
        dry_run=True
    )

    scheduler.initialize()
    success = scheduler.run_single_round()

    assert success is True
    assert scheduler.state.current_round == 1
    assert scheduler.state.tasks["task_1"].status == "completed"


def test_run_single_round_with_mock_claude(temp_dir, mock_claude_invoker):
    """测试单轮执行（mock Claude）"""
    config_path = temp_dir / "test_config.yaml"
    config_path.write_text(f"""
project_name: "测试项目"
project_path: "{temp_dir}"
mode: serial
tasks:
  - id: task_1
    description: "任务1"
    prompt_template: "执行任务1"
    expected_output: "完成"
""")

    scheduler = Scheduler(
        base_path=str(temp_dir),
        config_path=str(config_path),
        dry_run=False
    )

    # 替换 Claude 调用器
    scheduler.claude_invoker = mock_claude_invoker

    scheduler.initialize()
    success = scheduler.run_single_round()

    assert success is True
    assert scheduler.state.current_round == 1
    assert scheduler.state.tasks["task_1"].status == "completed"
    assert mock_claude_invoker.invoke.called


def test_extract_knowledge(temp_dir):
    """测试知识提取"""
    config_path = temp_dir / "test_config.yaml"
    config_path.write_text(f"""
project_name: "测试项目"
project_path: "{temp_dir}"
mode: serial
tasks:
  - id: task_1
    description: "任务1"
    prompt_template: "执行任务1"
    expected_output: "完成"
""")

    scheduler = Scheduler(
        base_path=str(temp_dir),
        config_path=str(config_path),
        dry_run=True
    )

    # 测试包含关键词的结果
    result1 = {
        'summary': '发现了一个重要问题',
        'next_hints': '建议下次注意这个'
    }
    knowledge1 = scheduler._extract_knowledge(result1)
    assert '发现' in knowledge1
    assert '建议' in knowledge1

    # 测试不包含关键词的结果
    result2 = {
        'summary': '正常执行',
        'next_hints': '继续'
    }
    knowledge2 = scheduler._extract_knowledge(result2)
    assert knowledge2 == ''


def test_run_until_complete(temp_dir, mock_claude_invoker):
    """测试执行直到完成"""
    config_path = temp_dir / "test_config.yaml"
    config_path.write_text(f"""
project_name: "测试项目"
project_path: "{temp_dir}"
mode: serial
tasks:
  - id: task_1
    description: "任务1"
    prompt_template: "执行任务1"
    expected_output: "完成"
  - id: task_2
    description: "任务2"
    depends_on: [task_1]
    prompt_template: "执行任务2"
    expected_output: "完成"
""")

    scheduler = Scheduler(
        base_path=str(temp_dir),
        config_path=str(config_path),
        dry_run=False
    )

    scheduler.claude_invoker = mock_claude_invoker
    scheduler.initialize()

    summary = scheduler.run_until_complete(max_rounds=10)

    assert summary['completed_tasks'] == 2
    assert summary['failed_tasks'] == 0
    assert scheduler.state.is_all_completed()


def test_loop_mode_with_first_task(temp_dir, mock_claude_invoker):
    """测试循环模式（带首轮任务）"""
    config_path = temp_dir / "test_config.yaml"
    config_path.write_text(f"""
project_name: "测试项目"
project_path: "{temp_dir}"
mode: loop
tasks:
  - id: task_plan
    description: "规划任务"
    prompt_template: "制定计划"
    expected_output: "完成规划"
  - id: task_execute
    description: "执行任务"
    prompt_template: "执行计划"
    expected_output: "完成执行"
loop_config:
  first_task_id: task_plan
  task_id: task_execute
  max_rounds: 3
  stop_condition: ""
""")

    scheduler = Scheduler(
        base_path=str(temp_dir),
        config_path=str(config_path),
        dry_run=False
    )

    scheduler.claude_invoker = mock_claude_invoker
    scheduler.initialize()

    summary = scheduler.run_loop_mode(max_rounds=3)

    # 第一轮执行 task_plan，后续轮次执行 task_execute
    assert scheduler.state.current_round >= 1
    assert scheduler.state.tasks["task_plan"].status == "completed"
