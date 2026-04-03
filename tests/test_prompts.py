"""
测试 Prompts 模块
"""
import pytest

from prompts import PromptBuilder, build_task_prompt, extract_result_from_output
from state import SchedulerState, TaskState


def test_prompt_builder_init():
    """测试 PromptBuilder 初始化"""
    builder = PromptBuilder(
        project_name="测试项目",
        project_path="/path/to/project",
        mode="serial"
    )

    assert builder.project_name == "测试项目"
    assert builder.project_path == "/path/to/project"
    assert builder.mode == "serial"


def test_build_system_prompt():
    """测试构建系统提示词"""
    builder = PromptBuilder(
        project_name="测试项目",
        project_path="/path/to/project",
        mode="serial"
    )

    prompt = builder.build_system_prompt()

    assert "测试项目" in prompt
    assert "/path/to/project" in prompt
    assert "串行执行模式" in prompt
    assert "<result>" in prompt


def test_build_round_prompt():
    """测试构建轮次提示词"""
    builder = PromptBuilder(
        project_name="测试项目",
        project_path="/path/to/project",
        mode="serial"
    )

    prompt = builder.build_round_prompt(
        task_description="执行任务1",
        prompt_template="请执行: {project_path}\n\n{context_summary}",
        expected_output="完成任务",
        context_summary="## 历史\n上一轮完成了xxx",
        depends_on_completed=["task_0"],
        project_path="/path/to/project",
        full_context="## 全局记忆\nSDK路径: /sdk"
    )

    assert "执行任务1" in prompt
    assert "/path/to/project" in prompt
    assert "完成任务" in prompt
    assert "历史" in prompt or "上一轮完成了xxx" in prompt  # context_summary 被注入到 prompt_template 中
    assert "全局记忆" in prompt


def test_build_task_prompt(sample_state):
    """测试构建任务提示词"""
    prompt = build_task_prompt(
        state=sample_state,
        task_id="task_1",
        context_summary="## 历史\n无",
        full_context="## 全局记忆\n无"
    )

    assert "任务1" in prompt
    assert "执行任务1" in prompt


def test_extract_result_from_output_success():
    """测试从输出中提取结果（成功）"""
    output = """
执行完成

<result>
files_modified:
- file1.md
- file2.py
files_created:
- new_file.txt
summary: |
  本轮完成了文档编写和代码修改
next_hints:
  下一轮可以继续优化性能
</result>
"""

    result = extract_result_from_output(output)

    assert result['status'] == 'completed'
    assert 'file1.md' in result['files_modified']
    assert 'file2.py' in result['files_modified']
    assert 'new_file.txt' in result['files_created']
    assert '文档编写' in result['summary']
    assert '优化性能' in result['next_hints']


def test_extract_result_from_output_no_tags():
    """测试提取结果（无标签）"""
    output = "这是一段普通输出，没有 result 标签"

    result = extract_result_from_output(output)

    assert result['status'] == 'completed'
    assert result['summary'] == output.strip()
    assert result['files_modified'] == []


def test_extract_result_from_output_partial():
    """测试提取结果（部分字段）"""
    output = """
<result>
files_modified:
- test.md
summary: |
  只有部分字段
</result>
"""

    result = extract_result_from_output(output)

    assert 'test.md' in result['files_modified']
    assert '部分字段' in result['summary']
    assert result['files_created'] == []
    assert result['next_hints'] == ''


def test_extract_result_from_output_empty():
    """测试提取结果（空输出）"""
    result = extract_result_from_output("")

    assert result['summary'] == 'No output'
    assert result['files_modified'] == []


def test_extract_result_from_output_malformed():
    """测试提取结果（格式错误）"""
    output = """
<result>
这是一段没有正确格式的内容
随便写的
</result>
"""

    result = extract_result_from_output(output)

    # 应该能容错处理
    assert result['status'] == 'completed'
    assert len(result['summary']) > 0
