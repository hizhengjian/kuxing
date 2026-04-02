"""
记忆存储层 - 管理每轮状态的持久化
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from state import RoundState, SchedulerState


class MemoryStore:
    """记忆存储管理器"""

    def __init__(self, base_path: str, project_slug: str):
        """
        初始化记忆存储

        Args:
            base_path: 基础路径，如 ~/claudecode_projects/kuxing僧
            project_slug: 项目标识符，用于创建子目录
        """
        self.base_path = Path(base_path)
        self.project_slug = project_slug
        self.memory_dir = self.base_path / "memory" / project_slug
        self.rounds_dir = self.memory_dir / "rounds"

    def ensure_dirs(self):
        """确保目录结构存在"""
        self.rounds_dir.mkdir(parents=True, exist_ok=True)

    def get_config_path(self) -> Path:
        """获取配置文件路径"""
        return self.memory_dir / "config.yaml"

    def get_state_path(self) -> Path:
        """获取状态文件路径"""
        return self.memory_dir / "state.json"

    def save_state(self, state: SchedulerState) -> None:
        """
        保存调度器状态

        Args:
            state: SchedulerState对象
        """
        self.ensure_dirs()
        state.update_timestamp()

        with open(self.get_state_path(), 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)

    def load_state(self) -> Optional[SchedulerState]:
        """
        加载调度器状态

        Returns:
            SchedulerState对象，如果不存在返回None
        """
        state_path = self.get_state_path()
        if not state_path.exists():
            return None

        with open(state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return SchedulerState.from_dict(data)

    def save_round(self, round_state: RoundState) -> None:
        """
        保存单轮记忆

        Args:
            round_state: RoundState对象
        """
        self.ensure_dirs()

        round_file = self.rounds_dir / f"round_{round_state.round:04d}.json"

        with open(round_file, 'w', encoding='utf-8') as f:
            json.dump(round_state.to_dict(), f, ensure_ascii=False, indent=2)

    def load_rounds(self) -> List[RoundState]:
        """
        加载所有轮次记忆

        Returns:
            按轮次排序的RoundState列表
        """
        if not self.rounds_dir.exists():
            return []

        rounds = []
        for round_file in sorted(self.rounds_dir.glob("round_*.json")):
            try:
                with open(round_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                rounds.append(RoundState.from_dict(data))
            except (json.JSONDecodeError, KeyError) as e:
                print(f"警告: 损坏的轮次文件 {round_file}: {e}")
                continue

        return rounds

    def get_latest_round(self) -> Optional[RoundState]:
        """
        获取最新一轮的记忆

        Returns:
            最新的RoundState对象，如果不存在返回None
        """
        rounds = self.load_rounds()
        return rounds[-1] if rounds else None

    def get_context_for_next_round(self) -> str:
        """
        构造下一轮输入的历史上下文摘要

        Returns:
            格式化的历史上下文字符串
        """
        rounds = self.load_rounds()

        if not rounds:
            return "## 历史上下文\n\n这是第一轮执行，无历史记录。"

        context_parts = ["## 历史上下文\n"]

        for round_state in rounds:
            status_icon = "✅" if round_state.result and round_state.result.get('status') == 'completed' else "❌"

            context_parts.append(f"### Round {round_state.round}: {status_icon} {round_state.task_description}\n")

            if round_state.input_context:
                prev_summary = round_state.input_context.get('previous_round_summary', '')
                if prev_summary:
                    context_parts.append(f"  - 概述: {prev_summary}")

            if round_state.result:
                result = round_state.result
                if result.get('files_modified'):
                    context_parts.append(f"  - 修改文件: {', '.join(result.get('files_modified', []))}")
                if result.get('files_created'):
                    context_parts.append(f"  - 创建文件: {', '.join(result.get('files_created', []))}")
                if result.get('summary'):
                    context_parts.append(f"  - 结果: {result.get('summary')}")
                if result.get('next_hints'):
                    context_parts.append(f"  - 下轮建议: {result.get('next_hints')}")

            context_parts.append("")

        return "\n".join(context_parts)

    def clear_rounds(self) -> None:
        """清空所有轮次记忆（保留config和state）"""
        if self.rounds_dir.exists():
            for round_file in self.rounds_dir.glob("round_*.json"):
                round_file.unlink()

    def reset_state(self) -> None:
        """重置调度器状态（轮次归零，任务重置为pending）"""
        state = self.load_state()
        if state:
            state.current_round = 0
            for task in state.tasks.values():
                task.status = "pending"
            self.save_state(state)

    def clear_all(self) -> None:
        """清空整个项目记忆目录"""
        import shutil
        if self.memory_dir.exists():
            shutil.rmtree(self.memory_dir)

    def get_round_count(self) -> int:
        """获取已完成的轮次数量"""
        return len(self.load_rounds())

    def export_summary(self) -> Dict[str, Any]:
        """
        导出会话摘要

        Returns:
            包含所有关键信息的字典
        """
        state = self.load_state()
        rounds = self.load_rounds()

        if not state:
            return {"error": "No state found"}

        return {
            "project_name": state.project_name,
            "project_path": state.project_path,
            "current_round": state.current_round,
            "mode": state.mode,
            "total_tasks": len(state.tasks),
            "completed_tasks": sum(1 for t in state.tasks.values() if t.status == "completed"),
            "pending_tasks": len(state.pending_tasks),
            "total_rounds": len(rounds),
            "completed_rounds": state.completed_rounds,
            "last_activity": rounds[-1].timestamp if rounds else None,
            "last_error": state.last_error
        }