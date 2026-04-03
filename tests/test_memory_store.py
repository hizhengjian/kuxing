"""
测试 MemoryStore 模块
"""
import pytest
from pathlib import Path
import os

from memory_store import MemoryStore
from state import RoundState, SchedulerState, TaskState


def test_memory_store_init(temp_dir):
    """测试初始化"""
    store = MemoryStore(str(temp_dir), "test_project")

    assert store.base_path == temp_dir
    assert store.project_slug == "test_project"
    assert store.memory_dir == temp_dir / "memory" / "test_project"
    assert store.shared_context_dir == temp_dir / "shared_context"


def test_ensure_dirs(temp_dir):
    """测试目录创建"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()

    assert store.rounds_dir.exists()
    assert store.shared_context_dir.exists()


def test_save_and_load_state(temp_dir, sample_state):
    """测试状态保存和加载"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()

    # 保存
    store.save_state(sample_state)
    assert store.get_state_path().exists()

    # 加载
    loaded_state = store.load_state()
    assert loaded_state is not None
    assert loaded_state.project_name == sample_state.project_name
    assert loaded_state.current_round == sample_state.current_round
    assert len(loaded_state.tasks) == len(sample_state.tasks)


def test_save_and_load_rounds(temp_dir):
    """测试轮次保存和加载"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()

    # 保存轮次
    round1 = RoundState(
        round=1,
        timestamp="2026-04-03T10:00:00",
        task_id="task_1",
        task_description="测试任务",
        result={"status": "completed", "summary": "完成"}
    )
    store.save_round(round1)

    # 加载轮次
    rounds = store.load_rounds()
    assert len(rounds) == 1
    assert rounds[0].round == 1
    assert rounds[0].task_id == "task_1"


def test_resolve_env_vars(temp_dir):
    """测试环境变量替换"""
    store = MemoryStore(str(temp_dir), "test_project")

    # 设置测试环境变量
    os.environ["TEST_VAR"] = "test_value"

    content = "SDK路径: ${TEST_VAR}, 未定义: ${UNDEFINED_VAR}"
    result = store.resolve_env_vars(content)

    assert "test_value" in result
    assert "${UNDEFINED_VAR}" in result  # 未定义的保留原样

    # 清理
    del os.environ["TEST_VAR"]


def test_load_shared_context(temp_dir):
    """测试加载全局共享记忆"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()

    # 创建共享记忆文件
    store.shared_context_file.write_text("# 全局记忆\nSDK: /path/to/sdk")

    content = store.load_shared_context()
    assert "全局记忆" in content
    assert "SDK" in content


def test_load_project_context(temp_dir):
    """测试加载项目私有记忆"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()

    # 创建项目记忆文件
    store.context_file.write_text("# 项目记忆\n特性: xxx")

    content = store.load_project_context()
    assert "项目记忆" in content
    assert "特性" in content


def test_append_knowledge_base(temp_dir):
    """测试知识沉淀追加"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()

    # 第一次追加
    store.append_knowledge_base("发现1: 重要信息")
    assert store.knowledge_base_file.exists()

    content1 = store.knowledge_base_file.read_text()
    assert "发现1" in content1

    # 第二次追加
    store.append_knowledge_base("发现2: 更多信息")
    content2 = store.knowledge_base_file.read_text()
    assert "发现1" in content2
    assert "发现2" in content2


def test_get_full_context(temp_dir):
    """测试获取完整上下文"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()

    # 创建三层记忆
    store.shared_context_file.write_text("# 全局记忆")
    store.context_file.write_text("# 项目记忆")
    store.knowledge_base_file.write_text("# 知识沉淀")

    full_context = store.get_full_context()

    assert "全局记忆" in full_context
    assert "项目记忆" in full_context
    assert "知识沉淀" in full_context


def test_clear_rounds(temp_dir):
    """测试清空轮次"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()

    # 保存几个轮次
    for i in range(3):
        round_state = RoundState(
            round=i+1,
            timestamp="2026-04-03T10:00:00",
            task_id=f"task_{i+1}",
            task_description="测试"
        )
        store.save_round(round_state)

    assert len(store.load_rounds()) == 3

    # 清空
    store.clear_rounds()
    assert len(store.load_rounds()) == 0


def test_export_summary(temp_dir, sample_state):
    """测试导出摘要"""
    store = MemoryStore(str(temp_dir), "test_project")
    store.ensure_dirs()

    # 保存状态
    store.save_state(sample_state)

    # 导出摘要
    summary = store.export_summary()

    assert summary["project_name"] == "测试项目"
    assert summary["total_tasks"] == 2
    assert summary["current_round"] == 0
