"""
pytest 配置和共享 fixtures
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

from state import SchedulerState, TaskState, RoundState
from memory_store import MemoryStore
from config_schema import SchedulerConfig, TaskConfig, LoopConfig


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def mock_claude_invoker():
    """Mock Claude 调用器"""
    mock = Mock()
    mock.invoke = Mock(return_value=MagicMock(
        success=True,
        output="""<result>
files_modified:
  - test.md
files_created:
  - new_file.md
summary: |
  测试执行成功
next_hints: |
  继续下一轮
</result>""",
        error=None,
        invocation=MagicMock(
            prompt="test prompt",
            model="sonnet-4",
            input_tokens=100,
            output_tokens=50,
            duration_ms=1000
        )
    ))
    return mock


@pytest.fixture
def sample_config(temp_dir):
    """示例配置"""
    return SchedulerConfig(
        project_name="测试项目",
        project_path=str(temp_dir),
        mode="serial",
        tasks=[
            TaskConfig(
                id="task_1",
                type="agent",
                description="第一个任务",
                prompt_template="执行任务1: {project_path}",
                expected_output="完成任务1"
            ),
            TaskConfig(
                id="task_2",
                type="agent",
                description="第二个任务",
                depends_on=["task_1"],
                prompt_template="执行任务2",
                expected_output="完成任务2"
            )
        ]
    )


@pytest.fixture
def sample_state(temp_dir):
    """示例状态"""
    tasks = {
        "task_1": TaskState(
            id="task_1",
            description="任务1",
            status="pending",
            prompt_template="执行任务1",
            expected_output="完成"
        ),
        "task_2": TaskState(
            id="task_2",
            description="任务2",
            status="pending",
            depends_on=["task_1"],
            prompt_template="执行任务2",
            expected_output="完成"
        )
    }

    return SchedulerState(
        project_slug="test_project",
        project_name="测试项目",
        project_path=str(temp_dir),
        config_file="test.yaml",
        mode="serial",
        tasks=tasks,
        pending_tasks=["task_1", "task_2"]
    )


@pytest.fixture
def memory_store(temp_dir):
    """内存存储实例"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()
    return store
