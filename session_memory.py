"""
会话记忆管理 - 结构化跟踪每轮执行状态
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict


class SessionMemory:
    """结构化会话记忆管理"""

    # 会话记忆模板
    TEMPLATE = """# 执行标题
_{task_name} - Round {round_num}_

# 当前状态
_正在执行什么？待完成的任务？下一步计划？_


# 任务规格
_用户要求做什么？设计决策？关键约束？_


# 关键文件
_重要文件及其作用（文件路径:行号 格式）_


# 工作流程
_执行的命令及顺序，如何解释输出_


# 错误与修正
_遇到的错误及解决方法，失败的尝试_


# 代码库文档
_重要系统组件，如何协同工作_


# 学习总结
_什么有效？什么无效？应避免什么？_


# 关键结果
_如果用户要求特定输出，在此记录完整结果_


# 工作日志
_逐步执行摘要（时间戳 + 简短描述）_

"""

    SECTIONS = [
        "执行标题",
        "当前状态",
        "任务规格",
        "关键文件",
        "工作流程",
        "错误与修正",
        "代码库文档",
        "学习总结",
        "关键结果",
        "工作日志"
    ]

    def __init__(self, memory_dir: Path, project_name: str):
        """
        初始化会话记忆

        Args:
            memory_dir: 记忆目录
            project_name: 项目名称
        """
        self.memory_dir = memory_dir
        self.project_name = project_name
        self.session_file = memory_dir / 'session.md'

    def initialize(self, task_name: str, round_num: int, task_description: str = ""):
        """
        初始化会话记忆文件

        Args:
            task_name: 任务名称
            round_num: 当前轮次
            task_description: 任务描述
        """
        content = self.TEMPLATE.format(
            task_name=task_name,
            round_num=round_num
        )

        # 如果有任务描述，填充到"任务规格"
        if task_description:
            content = self._update_section_in_content(
                content,
                "任务规格",
                task_description
            )

        self.session_file.write_text(content, encoding='utf-8')

    def load(self) -> str:
        """加载会话记忆内容"""
        if not self.session_file.exists():
            return ""
        return self.session_file.read_text(encoding='utf-8')

    def update_current_state(self, summary: str, next_hints: str):
        """
        更新当前状态

        Args:
            summary: 上一轮完成的内容
            next_hints: 下一步计划
        """
        content = f"""
**上一轮完成**：
{summary}

**下一步计划**：
{next_hints}

**更新时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self._update_section("当前状态", content)

    def update_task_spec(self, spec: str):
        """更新任务规格"""
        self._update_section("任务规格", spec)

    def add_key_file(self, file_path: str, description: str, line_number: Optional[int] = None):
        """
        添加关键文件

        Args:
            file_path: 文件路径
            description: 文件说明
            line_number: 行号（可选）
        """
        if line_number:
            entry = f"- `{file_path}:{line_number}` - {description}"
        else:
            entry = f"- `{file_path}` - {description}"

        self._append_to_section("关键文件", entry)

    def add_workflow_step(self, command: str, description: str = ""):
        """
        添加工作流程步骤

        Args:
            command: 执行的命令
            description: 命令说明
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        if description:
            entry = f"[{timestamp}] `{command}` - {description}"
        else:
            entry = f"[{timestamp}] `{command}`"

        self._append_to_section("工作流程", entry)

    def add_error(self, error: str, solution: str = "", failed_attempts: List[str] = None):
        """
        添加错误与修正

        Args:
            error: 错误描述
            solution: 解决方法
            failed_attempts: 失败的尝试
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"\n**[{timestamp}] 错误**：{error}\n"

        if failed_attempts:
            entry += "\n**失败的尝试**：\n"
            for attempt in failed_attempts:
                entry += f"- {attempt}\n"

        if solution:
            entry += f"\n**解决方法**：{solution}\n"
        else:
            entry += "\n**状态**：未解决\n"

        self._append_to_section("错误与修正", entry)

    def add_learning(self, learning: str, category: str = "general"):
        """
        添加学习总结

        Args:
            learning: 学习内容
            category: 分类（general/effective/ineffective/avoid）
        """
        category_map = {
            "general": "一般经验",
            "effective": "✅ 有效方法",
            "ineffective": "❌ 无效方法",
            "avoid": "⚠️ 应避免"
        }

        prefix = category_map.get(category, "一般经验")
        entry = f"- **{prefix}**：{learning}"

        self._append_to_section("学习总结", entry)

    def add_key_result(self, result: str):
        """添加关键结果"""
        self._update_section("关键结果", result)

    def add_worklog(self, description: str):
        """
        添加工作日志

        Args:
            description: 简短描述
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"- [{timestamp}] {description}"

        self._append_to_section("工作日志", entry)

    def update_round_number(self, round_num: int):
        """更新轮次号"""
        content = self.load()
        # 更新执行标题中的 Round 号
        content = re.sub(
            r'(# 执行标题\n_.*? - Round )\d+(_)',
            f'\\g<1>{round_num}\\g<2>',
            content
        )
        self.session_file.write_text(content, encoding='utf-8')

    def _update_section(self, section_name: str, new_content: str):
        """
        更新指定 section 的内容（替换）

        Args:
            section_name: section 名称
            new_content: 新内容
        """
        content = self.load()
        updated = self._update_section_in_content(content, section_name, new_content)
        self.session_file.write_text(updated, encoding='utf-8')

    def _update_section_in_content(self, content: str, section_name: str, new_content: str) -> str:
        """在内容中更新 section"""
        # 匹配 section：# Section\n_description_\n\n<content>\n\n# NextSection
        # 注意：模板中 section 之间只有一个空行，不是两个
        pattern = f'(# {re.escape(section_name)}\\n_[^_]*_\\n)(.*?)(\\n# |\\n\\n# |$)'

        def replacer(match):
            # 如果有内容，添加两个换行符
            if new_content.strip():
                return f'{match.group(1)}\n{new_content.strip()}\n{match.group(3)}'
            else:
                return f'{match.group(1)}{match.group(3)}'

        updated = re.sub(pattern, replacer, content, flags=re.DOTALL)

        return updated

    def _append_to_section(self, section_name: str, new_entry: str):
        """
        追加内容到指定 section

        Args:
            section_name: section 名称
            new_entry: 新条目
        """
        content = self.load()

        # 匹配 section 并在末尾追加
        pattern = f'(# {re.escape(section_name)}\\n_[^_]*_\\n)(.*?)(\\n# |\\n\\n# |$)'

        def replacer(match):
            existing = match.group(2).strip()
            if existing:
                return f'{match.group(1)}\n{existing}\n{new_entry}\n{match.group(3)}'
            else:
                return f'{match.group(1)}\n{new_entry}\n{match.group(3)}'

        updated = re.sub(pattern, replacer, content, flags=re.DOTALL)

        # 保存更新后的内容
        self.session_file.write_text(updated, encoding='utf-8')

        def replacer(match):
            existing_content = match.group(2).strip()
            if existing_content:
                combined = f"{existing_content}\n{new_entry}"
            else:
                combined = new_entry
            return f'{match.group(1)}{combined}{match.group(3)}'

        updated = re.sub(pattern, replacer, content, flags=re.DOTALL)

        # 如果没有匹配到，尝试简化模式
        if updated == content:
            pattern = f'(# {re.escape(section_name)}\\n_[^_]*_\\n)(.*?)(\\n# |$)'
            updated = re.sub(pattern, replacer, content, flags=re.DOTALL)

        self.session_file.write_text(updated, encoding='utf-8')

    def get_section_content(self, section_name: str) -> str:
        """
        获取指定 section 的内容

        Args:
            section_name: section 名称

        Returns:
            section 内容
        """
        content = self.load()

        # 匹配 section 内容
        pattern = f'# {re.escape(section_name)}\\n_[^_]*_\\n\\n(.*?)(\\n\\n# |$)'
        match = re.search(pattern, content, flags=re.DOTALL)

        if match:
            return match.group(1).strip()

        # 尝试简化模式
        pattern = f'# {re.escape(section_name)}\\n_[^_]*_\\n(.*?)(\\n# |$)'
        match = re.search(pattern, content, flags=re.DOTALL)

        if match:
            return match.group(1).strip()

        return ""

    def extract_from_result(self, result: dict, round_num: int):
        """
        从执行结果中自动提取信息并更新会话记忆

        Args:
            result: 执行结果字典
            round_num: 当前轮次
        """
        # 更新轮次号
        self.update_round_number(round_num)

        # 更新当前状态
        summary = result.get('summary', '')
        next_hints = result.get('next_hints', '')
        if summary or next_hints:
            self.update_current_state(summary, next_hints)

        # 添加修改的文件
        files_modified = result.get('files_modified', [])
        files_created = result.get('files_created', [])

        for file_path in files_modified:
            self.add_key_file(file_path, "已修改")

        for file_path in files_created:
            self.add_key_file(file_path, "新创建")

        # 添加工作日志
        if summary:
            self.add_worklog(summary[:100])  # 截断到 100 字符

        # 如果有错误，记录
        if 'error' in summary.lower() or '失败' in summary or '错误' in summary:
            self.add_error(summary)

    def get_summary_for_prompt(self) -> str:
        """
        获取用于 prompt 的摘要

        Returns:
            格式化的摘要文本
        """
        current_state = self.get_section_content("当前状态")
        task_spec = self.get_section_content("任务规格")
        key_files = self.get_section_content("关键文件")
        errors = self.get_section_content("错误与修正")

        summary = "## 会话记忆摘要\n\n"

        if current_state:
            summary += f"### 当前状态\n{current_state}\n\n"

        if task_spec:
            summary += f"### 任务规格\n{task_spec}\n\n"

        if key_files:
            summary += f"### 关键文件\n{key_files}\n\n"

        if errors:
            # 只显示最近的错误（最后20行）
            error_lines = errors.split('\n')
            recent_errors = '\n'.join(error_lines[-20:])  # 最近 20 行
            summary += f"### 最近的错误\n{recent_errors}\n\n"

        return summary
