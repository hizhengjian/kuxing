"""
测试 TaskQueue 模块
"""
import pytest

from task_queue import SerialQueue, ParallelQueue, LoopQueue, create_queue
from state import SchedulerState, TaskState


def test_serial_queue_get_next_task(sample_state):
    """测试串行队列获取下一个任务"""
    queue = SerialQueue()

    # 第一个任务没有依赖，应该返回
    next_task = queue.get_next_task(sample_state)
    assert next_task == "task_1"

    # 标记第一个任务完成
    sample_state.tasks["task_1"].status = "completed"

    # 现在应该返回第二个任务
    next_task = queue.get_next_task(sample_state)
    assert next_task == "task_2"


def test_serial_queue_should_continue(sample_state):
    """测试串行队列是否应该继续"""
    queue = SerialQueue()

    # 有待执行任务，应该继续
    assert queue.should_continue(sample_state) is True

    # 所有任务完成，不应该继续
    sample_state.tasks["task_1"].status = "completed"
    sample_state.tasks["task_2"].status = "completed"
    assert queue.should_continue(sample_state) is False


def test_parallel_queue_get_next_task(sample_state):
    """测试并行队列获取任务"""
    queue = ParallelQueue(max_parallel=2)

    # 第一个任务
    next_task = queue.get_next_task(sample_state)
    assert next_task == "task_1"

    # 标记为运行中
    sample_state.tasks["task_1"].status = "running"

    # 第二个任务依赖第一个，不应该返回
    next_task = queue.get_next_task(sample_state)
    assert next_task is None

    # 第一个任务完成后，应该返回第二个
    sample_state.tasks["task_1"].status = "completed"
    next_task = queue.get_next_task(sample_state)
    assert next_task == "task_2"


def test_loop_queue_basic(sample_state):
    """测试循环队列基本功能"""
    queue = LoopQueue(
        task_id="task_1",
        max_rounds=5,
        stop_condition=""
    )

    # 应该返回循环任务
    next_task = queue.get_next_task(sample_state)
    assert next_task == "task_1"

    # 未达到最大轮次，应该继续
    sample_state.current_round = 3
    assert queue.should_continue(sample_state) is True

    # 达到最大轮次，不应该继续
    sample_state.current_round = 5
    assert queue.should_continue(sample_state) is False


def test_loop_queue_with_first_task(sample_state):
    """测试循环队列带首轮任务"""
    queue = LoopQueue(
        task_id="task_2",
        max_rounds=5,
        stop_condition="",
        first_task_id="task_1"
    )

    # 第一轮应该返回 first_task
    next_task = queue.get_next_task(sample_state)
    assert next_task == "task_1"

    # 标记第一个任务完成
    sample_state.tasks["task_1"].status = "completed"

    # 后续应该返回循环任务
    next_task = queue.get_next_task(sample_state)
    assert next_task == "task_2"


def test_loop_queue_stop_condition(sample_state, memory_store):
    """测试循环队列停止条件"""
    from state import RoundState

    queue = LoopQueue(
        task_id="task_1",
        max_rounds=10,
        stop_condition="连续3次成功",
        memory_store=memory_store
    )

    # 保存3个成功的轮次
    for i in range(3):
        round_state = RoundState(
            round=i+1,
            timestamp="2026-04-03T10:00:00",
            task_id="task_1",
            task_description="测试",
            result={"status": "completed", "summary": "成功"}
        )
        memory_store.save_round(round_state)

    sample_state.current_round = 3

    # 应该检测到停止条件
    assert queue.check_stop_condition(sample_state, "") is True


def test_create_queue():
    """测试队列工厂函数"""
    # 串行队列
    queue1 = create_queue("serial", {})
    assert isinstance(queue1, SerialQueue)

    # 并行队列
    queue2 = create_queue("parallel", {"max_parallel": 5})
    assert isinstance(queue2, ParallelQueue)

    # 循环队列
    from config_schema import LoopConfig
    loop_config = LoopConfig(task_id="task_1", max_rounds=10)
    queue3 = create_queue("loop", {"loop_config": loop_config})
    assert isinstance(queue3, LoopQueue)
