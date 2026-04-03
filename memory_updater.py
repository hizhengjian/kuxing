"""
记忆自动更新器 - 从执行结果中提取信息并更新项目记忆
"""
import re
from datetime import datetime
from typing import Set
from memory_store import MemoryStore


class MemoryUpdater:
    """自动更新记忆"""

    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self.discovered_paths: Set[str] = set()
        self.discovered_commands: Set[str] = set()
        self.discovered_errors: Set[str] = set()

    def update_from_result(self, result: dict):
        """从执行结果中更新记忆"""
        summary = result.get('summary', '')
        files_modified = result.get('files_modified', [])

        # 1. 提取新路径
        new_paths = self._extract_paths(summary)
        new_paths.update(files_modified)

        paths_to_add = new_paths - self.discovered_paths
        if paths_to_add:
            self.discovered_paths.update(paths_to_add)
            self._append_paths(paths_to_add)

        # 2. 提取新命令
        new_commands = self._extract_commands(summary)
        commands_to_add = new_commands - self.discovered_commands
        if commands_to_add:
            self.discovered_commands.update(commands_to_add)
            self._append_commands(commands_to_add)

        # 3. 提取错误信息
        if 'error' in summary.lower() or 'failed' in summary.lower() or '错误' in summary or '失败' in summary:
            error_info = self._extract_error(summary)
            if error_info and error_info not in self.discovered_errors:
                self.discovered_errors.add(error_info)
                self._append_error(error_info)

    def _extract_paths(self, text: str) -> Set[str]:
        """提取路径"""
        paths = set()
        # Unix 路径 - 至少5个字符
        unix_paths = re.findall(r'/[\w/\-\.]+', text)
        paths.update(p for p in unix_paths if len(p) >= 5)  # 过滤太短的路径

        # Windows 路径
        win_paths = re.findall(r'[A-Z]:\\[\w\\\-\.]+', text)
        paths.update(win_paths)

        return paths

    def _extract_commands(self, text: str) -> Set[str]:
        """提取命令"""
        commands = set()
        # 常见命令模式
        patterns = [
            r'`([^`]+)`',  # 反引号包裹的命令
            r'执行[：:]\s*([^，。\n和]+)',  # "执行: xxx"，到逗号、句号、换行或"和"为止
            r'运行[：:]\s*([^，。\n和]+)',  # "运行: xxx"
            r'命令[：:]\s*([^，。\n和]+)',  # "命令: xxx"
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            commands.update(m.strip() for m in matches if m.strip())

        return commands

    def _extract_error(self, text: str) -> str:
        """提取错误信息"""
        # 提取错误相关的句子
        sentences = re.split(r'[。\n]', text)
        for sent in sentences:
            if any(kw in sent.lower() for kw in ['error', 'failed', '错误', '失败']):
                return sent.strip()
        return ""

    def _append_paths(self, paths: Set[str]):
        """追加路径到项目记忆"""
        if not paths:
            return

        content = f"\n\n## 新发现的路径 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
        content += "\n".join(f"- {p}" for p in sorted(paths))

        self.memory_store.append_project_context(content)

    def _append_commands(self, commands: Set[str]):
        """追加命令到项目记忆"""
        if not commands:
            return

        content = f"\n\n## 新发现的命令 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
        content += "\n".join(f"- `{c}`" for c in sorted(commands))

        self.memory_store.append_project_context(content)

    def _append_error(self, error: str):
        """追加错误到项目记忆"""
        content = f"\n\n## 遇到的问题 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
        content += f"- {error}\n"

        self.memory_store.append_project_context(content)
