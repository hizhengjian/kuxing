"""
测试会话记忆模块
"""
import pytest
from pathlib import Path
from session_memory import SessionMemory


@pytest.fixture
def temp_session_memory(tmp_path):
    """创建临时会话记忆"""
    return SessionMemory(tmp_path, "test-project")


def test_session_memory_init(temp_session_memory):
    """测试会话记忆初始化"""
    assert temp_session_memory.project_name == "test-project"
    assert temp_session_memory.session_file.name == "session.md"


def test_initialize_session(temp_session_memory):
    """测试初始化会话记忆文件"""
    temp_session_memory.initialize("测试任务", 1, "这是一个测试任务")

    assert temp_session_memory.session_file.exists()
    content = temp_session_memory.load()

    assert "测试任务 - Round 1" in content
    assert "这是一个测试任务" in content
    assert "# 当前状态" in content
    assert "# 任务规格" in content


def test_update_current_state(temp_session_memory):
    """测试更新当前状态"""
    temp_session_memory.initialize("测试任务", 1)

    temp_session_memory.update_current_state(
        summary="完成了功能A",
        next_hints="接下来实现功能B"
    )

    content = temp_session_memory.load()
    assert "完成了功能A" in content
    assert "接下来实现功能B" in content


def test_add_key_file(temp_session_memory):
    """测试添加关键文件"""
    temp_session_memory.initialize("测试任务", 1)

    temp_session_memory.add_key_file(
        "/path/to/file.py",
        "主要逻辑文件",
        line_number=42
    )

    content = temp_session_memory.load()
    assert "`/path/to/file.py:42`" in content
    assert "主要逻辑文件" in content


def test_add_workflow_step(temp_session_memory):
    """测试添加工作流程"""
    temp_session_memory.initialize("测试任务", 1)

    temp_session_memory.add_workflow_step(
        "pytest tests/",
        "运行测试"
    )

    content = temp_session_memory.load()
    assert "`pytest tests/`" in content
    assert "运行测试" in content


def test_add_error(temp_session_memory):
    """测试添加错误"""
    temp_session_memory.initialize("测试任务", 1)

    temp_session_memory.add_error(
        error="导入失败",
        solution="安装缺失的依赖",
        failed_attempts=["尝试1: 重启", "尝试2: 清理缓存"]
    )

    content = temp_session_memory.load()
    assert "导入失败" in content
    assert "安装缺失的依赖" in content
    assert "尝试1: 重启" in content


def test_add_learning(temp_session_memory):
    """测试添加学习总结"""
    temp_session_memory.initialize("测试任务", 1)

    temp_session_memory.add_learning(
        "使用 mock 可以避免 API 调用",
        category="effective"
    )

    content = temp_session_memory.load()
    assert "✅ 有效方法" in content
    assert "使用 mock 可以避免 API 调用" in content


def test_add_worklog(temp_session_memory):
    """测试添加工作日志"""
    temp_session_memory.initialize("测试任务", 1)

    temp_session_memory.add_worklog("完成了模块A的实现")

    content = temp_session_memory.load()
    assert "完成了模块A的实现" in content


def test_update_round_number(temp_session_memory):
    """测试更新轮次号"""
    temp_session_memory.initialize("测试任务", 1)

    temp_session_memory.update_round_number(5)

    content = temp_session_memory.load()
    assert "Round 5" in content


def test_extract_from_result(temp_session_memory):
    """测试从执行结果中提取信息"""
    temp_session_memory.initialize("测试任务", 1)

    result = {
        'status': 'completed',
        'summary': '完成了功能实现',
        'next_hints': '下一步需要添加测试',
        'files_modified': ['/path/to/file1.py', '/path/to/file2.py'],
        'files_created': ['/path/to/new_file.py']
    }

    temp_session_memory.extract_from_result(result, 2)

    content = temp_session_memory.load()
    assert "Round 2" in content
    assert "完成了功能实现" in content
    assert "下一步需要添加测试" in content
    assert "/path/to/file1.py" in content
    assert "/path/to/new_file.py" in content


def test_get_summary_for_prompt(temp_session_memory):
    """测试获取用于 prompt 的摘要"""
    temp_session_memory.initialize("测试任务", 1, "实现功能A")

    temp_session_memory.update_current_state(
        summary="完成了基础框架",
        next_hints="接下来实现核心逻辑"
    )

    summary = temp_session_memory.get_summary_for_prompt()

    # 验证摘要包含关键信息
    assert "## 会话记忆摘要" in summary
    assert "### 当前状态" in summary
    assert "完成了基础框架" in summary
    assert "接下来实现核心逻辑" in summary


def test_get_section_content(temp_session_memory):
    """测试获取指定 section 的内容"""
    temp_session_memory.initialize("测试任务", 1)

    temp_session_memory.update_current_state(
        summary="测试内容",
        next_hints="测试提示"
    )

    current_state = temp_session_memory.get_section_content("当前状态")
    assert "测试内容" in current_state
    assert "测试提示" in current_state


def test_multiple_updates(temp_session_memory):
    """测试多次更新累积效果"""
    temp_session_memory.initialize("测试任务", 1)

    # 第一次更新
    temp_session_memory.add_workflow_step("step1", "第一步")

    # 第二次更新
    temp_session_memory.add_workflow_step("step2", "第二步")

    # 第三次更新
    temp_session_memory.add_workflow_step("step3", "第三步")

    content = temp_session_memory.load()
    assert "step1" in content
    assert "step2" in content
    assert "step3" in content
