"""
任务队列引擎 - 支持串行、并行、循环三种模式
"""
from typing import List, Optional, Callable, Dict, Any
from abc import ABC, abstractmethod

from state import TaskState, SchedulerState
from prompts import build_task_prompt


class TaskQueue(ABC):
    """任务队列基类"""

    @abstractmethod
    def get_next_task(self, state: SchedulerState) -> Optional[str]:
        """获取下一个要执行的任务ID"""
        pass

    @abstractmethod
    def is_complete(self, state: SchedulerState) -> bool:
        """检查是否完成所有任务"""
        pass

    @abstractmethod
    def should_continue(self, state: SchedulerState) -> bool:
        """判断是否应该继续执行"""
        pass


class SerialQueue(TaskQueue):
    """串行任务队列 - 按顺序执行，支持依赖"""

    def get_next_task(self, state: SchedulerState) -> Optional[str]:
        """获取下一个可执行的任务（依赖都已完成）"""
        for task_id in state.pending_tasks:
            task = state.tasks.get(task_id)
            if not task or task.status != "pending":
                continue

            # 检查所有依赖是否已完成
            deps_completed = all(
                state.tasks.get(dep_id).status == "completed"
                for dep_id in task.depends_on
                if dep_id in state.tasks
            )

            if deps_completed:
                return task_id

        return None

    def is_complete(self, state: SchedulerState) -> bool:
        """所有任务完成或跳过"""
        return all(
            task.status in ("completed", "skipped", "failed")
            for task in state.tasks.values()
        )

    def should_continue(self, state: SchedulerState) -> bool:
        """还有待执行的任务"""
        return not self.is_complete(state) and self.get_next_task(state) is not None


class ParallelQueue(TaskQueue):
    """并行任务队列 - 同时执行多个独立任务"""

    def __init__(self, max_parallel: int = 3):
        self.max_parallel = max_parallel

    def get_next_task(self, state: SchedulerState) -> Optional[str]:
        """获取下一个可执行的独立任务"""
        # 统计当前运行中的任务数
        running_count = sum(
            1 for task in state.tasks.values()
            if task.status == "running"
        )

        if running_count >= self.max_parallel:
            return None

        # 找到下一个可执行的任务
        for task_id in state.pending_tasks:
            task = state.tasks.get(task_id)
            if not task or task.status != "pending":
                continue

            # 检查依赖（依赖的任务不能是running或pending）
            deps_ready = all(
                state.tasks.get(dep_id).status in ("completed", "skipped", "failed")
                for dep_id in task.depends_on
                if dep_id in state.tasks
            )

            if deps_ready:
                return task_id

        return None

    def is_complete(self, state: SchedulerState) -> bool:
        """所有任务完成"""
        return all(
            task.status in ("completed", "skipped", "failed")
            for task in state.tasks.values()
        )

    def should_continue(self, state: SchedulerState) -> bool:
        """还有可执行的任务"""
        return self.get_next_task(state) is not None


class LoopQueue(TaskQueue):
    """循环任务队列 - 反复执行同一个任务"""

    def __init__(
        self,
        task_id: str,
        max_rounds: int = 10,
        stop_condition: str = "",
        memory_store=None,
        first_task_id: Optional[str] = None  # 第一轮执行的任务
    ):
        self.task_id = task_id
        self.max_rounds = max_rounds
        self.stop_condition = stop_condition
        self.memory_store = memory_store
        self.first_task_id = first_task_id  # 第一轮执行这个任务
        self.first_round_done = False  # 标记第一轮是否完成

    def set_max_rounds(self, max_rounds: int):
        """运行时更新最大轮次限制（用于命令行参数覆盖配置文件）"""
        self.max_rounds = max_rounds

    def get_next_task(self, state: SchedulerState) -> Optional[str]:
        """每次都返回循环任务ID"""
        # 第一轮：如果还没有执行过first_task_id，返回它
        if not self.first_round_done and self.first_task_id:
            # 检查first_task_id是否在state中
            if self.first_task_id in state.tasks:
                first_task = state.tasks[self.first_task_id]
                if first_task.status == "pending":
                    return self.first_task_id
                # 如果first_task已完成，标记并继续主循环
                if first_task.status == "completed":
                    self.first_round_done = True
        return self.task_id

    def is_complete(self, state: SchedulerState) -> bool:
        """检查是否达到循环终止条件"""
        # 检查轮次是否达到上限
        if state.current_round >= self.max_rounds:
            return True

        # 检查停止条件（需要Claude判断）
        # 这里简单处理，实际需要根据state中的信息判断
        return False

    def should_continue(self, state: SchedulerState) -> bool:
        """判断是否应该继续循环"""
        if state.current_round >= self.max_rounds:
            return False

        # 获取循环任务的当前状态
        task = state.tasks.get(self.task_id)
        if not task:
            return False

        # 如果任务失败，不继续
        if task.status == "failed":
            return False

        # 如果任务是 completed 状态，说明之前执行过了
        # 在循环模式下，completed 状态意味着本次循环可能完成了，继续循环
        # 但如果 current_round 已经是 max_rounds，就停止
        if task.status == "completed":
            # 检查是否所有轮次都执行完了
            # completed_rounds 包含了所有完成的轮次
            if len(state.completed_rounds) >= self.max_rounds:
                return False
            # 否则继续循环（因为loop模式就是要重复执行）
            return True

        # 如果first_task还没执行，第一轮还没完成
        if not self.first_round_done and self.first_task_id:
            first_task = state.tasks.get(self.first_task_id)
            if first_task and first_task.status != "completed":
                return True  # 继续等待first_task完成

        # 检查停止条件
        context = ""
        if self.memory_store:
            try:
                context = self.memory_store.get_context_for_next_round()
            except Exception:
                context = ""
        if self.check_stop_condition(state, context):
            return False

        return True

    def check_stop_condition(self, state: SchedulerState, context: str) -> bool:
        """
        检查是否满足停止条件

        Args:
            state: 调度器状态
            context: 包含历史信息的上下文

        Returns:
            True if 应该停止
        """
        if not self.stop_condition:
            return False

        # 解析"连续N次成功"的停止条件
        import re
        match = re.search(r'连续(\d+)次成功', self.stop_condition)
        if match:
            n = int(match.group(1))
            # 加载最近N轮的历史
            if self.memory_store:
                try:
                    rounds = self.memory_store.load_rounds()
                    if len(rounds) >= n:
                        # 检查最近N轮是否都成功
                        recent_rounds = rounds[-n:]
                        all_success = all(
                            r.result and r.result.get('status') == 'completed'
                            for r in recent_rounds
                        )
                        if all_success:
                            print(f"\n达成停止条件：连续{n}次成功，停止循环")
                            return True
                except Exception:
                    pass
            return False

        # 其他停止条件暂不处理
        return False


def create_queue(mode: str, config: Dict[str, Any], memory_store=None) -> TaskQueue:
    """
    根据模式和配置创建任务队列

    Args:
        mode: 执行模式 (serial, parallel, loop)
        config: 模式相关配置
        memory_store: 记忆存储实例（用于LoopQueue检查停止条件）

    Returns:
        对应的TaskQueue实现
    """
    if mode == "serial":
        return SerialQueue()

    elif mode == "parallel":
        max_parallel = config.get("max_parallel", 3)
        return ParallelQueue(max_parallel=max_parallel)

    elif mode == "loop":
        loop_config = config.get("loop_config")
        # 支持LoopConfig对象或dict
        if hasattr(loop_config, 'task_id'):
            # LoopConfig对象
            task_id = loop_config.task_id
            max_rounds = getattr(loop_config, 'max_rounds', 10)
            stop_condition = getattr(loop_config, 'stop_condition', '')
            first_task_id = getattr(loop_config, 'first_task_id', None)
        else:
            # dict
            task_id = loop_config.get("task_id", "")
            max_rounds = loop_config.get("max_rounds", 10)
            stop_condition = loop_config.get("stop_condition", "")
            first_task_id = loop_config.get("first_task_id", None)
        return LoopQueue(
            task_id=task_id,
            max_rounds=max_rounds,
            stop_condition=stop_condition,
            memory_store=memory_store,
            first_task_id=first_task_id
        )

    else:
        raise ValueError(f"不支持的模式: {mode}")