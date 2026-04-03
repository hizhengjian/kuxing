"""
Prompt模板 - 构造每轮输入提示词
"""
from typing import Optional
from state import SchedulerState, RoundState


class PromptBuilder:
    """Prompt构造器"""

    def __init__(self, project_name: str, project_path: str, mode: str):
        self.project_name = project_name
        self.project_path = project_path
        self.mode = mode

    def build_system_prompt(self) -> str:
        """构建系统提示词"""
        mode_desc = {
            "serial": "串行执行模式：按顺序一个一个任务执行，等待前一个完成后再执行下一个。",
            "parallel": "并行执行模式：同时执行多个独立任务。",
            "loop": "循环执行模式：反复执行同一个任务，直到满足停止条件。"
        }.get(self.mode, "")

        return f"""你是 Claude Code 多轮任务执行器。

## 基本信息
- 项目名称: {self.project_name}
- 项目路径: {self.project_path}
- 执行模式: {mode_desc}

## 执行原则
1. 专注完成本轮任务，不要超出范围
2. 完成后用 <result> 标签返回结构化结果
3. 包含 files_modified, summary, next_hints 字段
4. 如果任务失败，说明原因并提供错误信息

## 输出格式
完成任务后，输出以下格式的结果：

<result>
files_modified:
  - file1.md
  - file2.cpp
files_created:
  - new_file.h
summary: |
  本轮完成了什么工作，包括主要步骤和成果。
next_hints: |
  建议下一轮可以做什么，或者需要补充什么。
</result>

## 验收标准
每轮任务都会有明确的 expected_output，请确保达到验收标准后再提交结果。
"""

    def build_round_prompt(
        self,
        task_description: str,
        prompt_template: str,
        expected_output: str,
        context_summary: str,
        depends_on_completed: list,
        project_path: str,
        full_context: str = "",
        session_summary: str = ""
    ) -> str:
        """
        构建单轮任务的提示词

        Args:
            task_description: 任务描述
            prompt_template: 任务prompt模板
            expected_output: 预期输出
            context_summary: 历史上下文摘要
            depends_on_completed: 已完成的依赖任务列表
            project_path: 项目路径
            full_context: 完整上下文（全局+项目+知识沉淀）
            session_summary: 会话记忆摘要

        Returns:
            格式化后的完整提示词
        """
        # 先替换模板中的变量（除了 context_summary，它需要稍后插入）
        # 使用一个临时占位符
        prompt = prompt_template.replace("{context_summary}", "<<<CONTEXT_SUMMARY>>>")
        prompt = prompt.format(project_path=project_path)
        # 替换回真正的 context_summary
        prompt = prompt.replace("<<<CONTEXT_SUMMARY>>>", context_summary)

        # 构造依赖说明
        deps_note = ""
        if depends_on_completed:
            deps_note = f"\n\n### 依赖任务完成情况\n已完成的依赖任务: {', '.join(depends_on_completed)}\n"

        # 构造完整上下文说明
        context_note = ""
        if full_context:
            context_note = f"\n\n### 项目上下文（重要，请务必参考）\n{full_context}\n"

        # 构造会话记忆摘要
        session_note = ""
        if session_summary:
            session_note = f"\n\n{session_summary}\n"

        return f"""### 任务描述
{task_description}

{deps_note}{context_note}{session_note}
### 任务详情
{prompt}

### 预期输出
{expected_output}

## 执行要求
1. 按照 prompt 执行任务
2. 确保达到 expected_output 的验收标准
3. 完成后用 <result> 标签返回结构化结果
"""

    def build_resume_prompt(self, interrupted_summary: str, next_action: str) -> str:
        """
        构建恢复执行的提示词

        Args:
            interrupted_summary: 中断前的状态摘要
            next_action: 下一步应该做什么

        Returns:
            恢复执行的提示词
        """
        return f"""## 恢复执行

上一轮执行被中断，情况如下：
{interrupted_summary}

### 接下来应该
{next_action}

请继续执行，注意：
1. 不要重复已完成的工作
2. 状态已保存，可以安全地继续
3. 完成后用 <result> 标签返回结构化结果
"""

    def build_summary_prompt(self, all_rounds: list) -> str:
        """
        构建最终总结的提示词

        Args:
            all_rounds: 所有轮次的RoundState列表

        Returns:
            最终总结的提示词
        """
        rounds_summary = "\n\n".join([
            f"Round {r.round}: {r.task_description}\n"
            f"  结果: {r.result.get('summary', 'N/A') if r.result else 'N/A'}"
            for r in all_rounds
        ])

        return f"""## 任务全部完成

所有轮次已执行完毕，以下是执行总结：

{rounds_summary}

请生成一份完整的执行报告，包括：
1. 完成的所有工作
2. 创建/修改的文件列表
3. 遇到的问题和解决方法
4. 最终交付物
"""


def build_task_prompt(
    state: SchedulerState,
    task_id: str,
    context_summary: str,
    full_context: str = "",
    session_summary: str = ""
) -> str:
    """
    为指定任务构建完整的prompt

    Args:
        state: 调度器状态
        task_id: 任务ID
        context_summary: 历史上下文摘要
        full_context: 完整上下文（全局+项目+知识沉淀）
        session_summary: 会话记忆摘要

    Returns:
        完整的提示词字符串
    """
    task = state.tasks.get(task_id)
    if not task:
        raise ValueError(f"任务不存在: {task_id}")

    builder = PromptBuilder(
        project_name=state.project_name,
        project_path=state.project_path,
        mode=state.mode
    )

    # 获取已完成的依赖任务
    depends_on_completed = [
        dep_id for dep_id in task.depends_on
        if dep_id in state.tasks and state.tasks[dep_id].status == "completed"
    ]

    # 构建系统提示词
    system_prompt = builder.build_system_prompt()

    # 构建轮次提示词
    round_prompt = builder.build_round_prompt(
        task_description=task.description,
        prompt_template=task.prompt_template,
        expected_output=task.expected_output,
        context_summary=context_summary,
        depends_on_completed=depends_on_completed,
        project_path=state.project_path,
        full_context=full_context,
        session_summary=session_summary
    )

    return f"{system_prompt}\n\n{round_prompt}"


def extract_result_from_output(output: str) -> dict:
    """
    从Claude输出中提取结构化结果

    Args:
        output: Claude的原始输出

    Returns:
        包含 files_modified, files_created, summary, next_hints 的字典
    """
    import re

    result = {
        'files_modified': [],
        'files_created': [],
        'summary': '',
        'next_hints': '',
        'status': 'completed'
    }

    # 如果输出太短，直接返回空
    if not output or len(output.strip()) < 50:
        result['summary'] = output.strip() if output else 'No output'
        return result

    # 尝试多种方式提取 <result> 内容
    content = None

    # 方式1: 非贪婪匹配 <result>...</result>
    match = re.search(r'<result>\s*(.*?)\s*</result>', output, re.DOTALL)
    if match:
        content = match.group(1).strip()

    # 方式2: 贪婪匹配（最后一个 </result> 之前的内容）
    if not content:
        match = re.search(r'<result>(.*)', output, re.DOTALL)
        if match:
            partial = match.group(1)
            # 找到最后一个 </result>
            end_idx = partial.rfind('</result>')
            if end_idx > 0:
                content = partial[:end_idx].strip()

    # 方式3: 直接查找 files_modified 等关键词（不依赖 <result> 标签）
    if not content:
        # 作为 fallback，尝试在输出中直接搜索关键信息
        files_section = re.search(r'files_modified:\s*\n((?:.*\n)*?)(?=files_created:|summary:|next_hints:|$)', output, re.IGNORECASE)
        if files_section:
            content = files_section.group(0)

    # 方式4: 查找 <result 开头但没有闭合标签的情况
    if not content and '<result' in output:
        # 尝试找到 <result 后的内容到行尾
        match = re.search(r'<result[^>]*>(.*)', output, re.DOTALL)
        if match:
            content = match.group(1).strip()

    if not content:
        # 如果完全没有找到结构化内容，把整个输出作为 summary
        result['summary'] = output.strip()[:1000]  # 限制长度
        return result

    # 解析 files_modified（更宽松的匹配）
    files_patterns = [
        r'files_modified:\s*\n((?:- .+\n)*)',
        r'files_modified:\s*:\s*\n((?:- .+\n)*)',
        r'修改文件:\s*\n((?:- .+\n)*)',
        r'创建的文件:\s*\n((?:- .+\n)*)',
    ]
    for pattern in files_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            lines = match.group(1).strip().split('\n')
            for line in lines:
                if line.strip().startswith('-'):
                    result['files_modified'].append(line.strip()[1:].strip())
            if result['files_modified']:
                break

    # 解析 files_created
    for pattern in [
        r'files_created:\s*\n((?:- .+\n)*)',
        r'files_created:\s*:\s*\n((?:- .+\n)*)',
        r'创建的文件:\s*\n((?:- .+\n)*)',
    ]:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            lines = match.group(1).strip().split('\n')
            for line in lines:
                if line.strip().startswith('-'):
                    result['files_created'].append(line.strip()[1:].strip())
            if result['files_created']:
                break

    # 解析 summary（支持多种格式）
    for pattern in [
        r'summary:\s*\|\s*\n((?:(?!next_hints|files_created|files_modified).+\n)*)',
        r'summary:\s*\n((?:(?!next_hints|files_created|files_modified).+\n)*)',
        r'摘要:\s*\n((?:(?!next_hints|下一轮).+\n)*)',
    ]:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            summary_text = match.group(1).strip()
            if summary_text:
                result['summary'] = summary_text
                break

    # 如果 summary 还是空的，尝试从内容中提取前几行作为 summary
    if not result['summary']:
        lines = content.split('\n')
        meaningful_lines = [l for l in lines if l.strip() and not l.strip().startswith('-') and ':' not in l][:3]
        if meaningful_lines:
            result['summary'] = ' '.join(meaningful_lines)[:500]

    # 解析 next_hints
    for pattern in [
        r'next_hints:\s*\|\s*\n((?:(?!---|files|summary).+\n)*)',
        r'next_hints:\s*\n\s*(.+?)(?=\n\w+:|</result>|\Z)',
        r'下一轮:\s*\n((?:(?!---).+\n)*)',
    ]:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            next_text = match.group(1).strip()
            if next_text:
                result['next_hints'] = next_text
                break

    return result