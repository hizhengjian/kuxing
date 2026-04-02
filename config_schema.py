"""
配置加载和验证
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from state import TaskState, SchedulerMode


@dataclass
class LoopConfig:
    """循环模式配置"""
    task_id: str
    max_rounds: int = 10
    stop_condition: str = ""
    interval_seconds: int = 0
    first_task_id: Optional[str] = None  # 第一轮执行这个任务（如规划任务）


@dataclass
class TaskConfig:
    """任务配置"""
    id: str
    type: str = "agent"
    description: str = ""
    depends_on: List[str] = field(default_factory=list)
    prompt_template: str = ""
    expected_output: str = ""


@dataclass
class SchedulerConfig:
    """调度器配置"""
    project_name: str
    project_path: str
    mode: str = "serial"
    tasks: List[TaskConfig] = field(default_factory=list)
    loop_config: Optional[LoopConfig] = None
    description: str = ""

    @property
    def project_slug(self) -> str:
        """生成项目slug"""
        # slugify: 替换空格和特殊字符为下划线
        slug = self.project_name.lower().replace(" ", "_").replace("-", "_")
        slug = ''.join(c for c in slug if c.isalnum() or c == '_')
        return slug


def load_config(config_path: str) -> SchedulerConfig:
    """
    加载并验证配置文件

    Args:
        config_path: YAML配置文件路径

    Returns:
        SchedulerConfig对象

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置文件格式错误
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(path, 'r', encoding='utf-8') as f:
        raw_config = yaml.safe_load(f)

    if not raw_config:
        raise ValueError("配置文件为空")

    # 验证必需字段
    required_fields = ['project_name', 'project_path', 'tasks']
    for field_name in required_fields:
        if field_name not in raw_config:
            raise ValueError(f"缺少必需字段: {field_name}")

    # 解析任务列表
    tasks = []
    for task_data in raw_config.get('tasks', []):
        if 'id' not in task_data:
            raise ValueError(f"任务缺少ID字段: {task_data}")

        task_config = TaskConfig(
            id=task_data['id'],
            type=task_data.get('type', 'agent'),
            description=task_data.get('description', ''),
            depends_on=task_data.get('depends_on', []),
            prompt_template=task_data.get('prompt_template', ''),
            expected_output=task_data.get('expected_output', '')
        )
        tasks.append(task_config)

    # 解析循环配置
    loop_config = None
    if 'loop_config' in raw_config:
        lc = raw_config['loop_config']
        loop_config = LoopConfig(
            task_id=lc.get('task_id', ''),
            max_rounds=lc.get('max_rounds', 10),
            stop_condition=lc.get('stop_condition', ''),
            interval_seconds=lc.get('interval_seconds', 0),
            first_task_id=lc.get('first_task_id', None)
        )

    # 创建调度器配置
    config = SchedulerConfig(
        project_name=raw_config['project_name'],
        project_path=raw_config['project_path'],
        mode=raw_config.get('mode', 'serial'),
        tasks=tasks,
        loop_config=loop_config,
        description=raw_config.get('description', '')
    )

    return config


def create_tasks_state(config: SchedulerConfig) -> Dict[str, TaskState]:
    """
    从配置创建任务状态字典

    Args:
        config: SchedulerConfig对象

    Returns:
        task_id -> TaskState 的字典
    """
    tasks = {}
    pending = []

    for task_config in config.tasks:
        task_state = TaskState(
            id=task_config.id,
            type=task_config.type,
            description=task_config.description,
            status="pending",
            depends_on=task_config.depends_on,
            prompt_template=task_config.prompt_template,
            expected_output=task_config.expected_output
        )
        tasks[task_config.id] = task_state
        pending.append(task_config.id)

    return tasks, pending


def validate_config(config: SchedulerConfig) -> List[str]:
    """
    验证配置完整性

    Args:
        config: SchedulerConfig对象

    Returns:
        警告信息列表（空表示验证通过）
    """
    warnings = []

    # 检查项目路径是否存在
    if not Path(config.project_path).exists():
        warnings.append(f"警告: 项目路径不存在 - {config.project_path}")

    # 检查循环配置的task_id是否在任务列表中
    if config.loop_config and config.loop_config.task_id:
        task_ids = {t.id for t in config.tasks}
        if config.loop_config.task_id not in task_ids:
            warnings.append(f"警告: loop_config.task_id '{config.loop_config.task_id}' 不在任务列表中")

    # 检查循环配置中是否有未定义的依赖
    task_ids = {t.id for t in config.tasks}
    for task_config in config.tasks:
        for dep in task_config.depends_on:
            if dep not in task_ids:
                warnings.append(f"警告: 任务 '{task_config.id}' 依赖 '{dep}' 不存在")

    # 检查是否有循环依赖
    if has_circular_dependency(config.tasks):
        warnings.append("错误: 任务存在循环依赖")

    # 检查prompt_template是否为空
    for task_config in config.tasks:
        if not task_config.prompt_template:
            warnings.append(f"警告: 任务 '{task_config.id}' 的 prompt_template 为空")

    return warnings


def has_circular_dependency(tasks: List[TaskConfig]) -> bool:
    """
    检查是否存在循环依赖

    Args:
        tasks: 任务配置列表

    Returns:
        True if存在循环依赖
    """
    # 构建依赖图
    graph = {t.id: set(t.depends_on) for t in tasks}

    # DFS检测环
    visited = set()
    rec_stack = set()

    def has_cycle(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if has_cycle(node):
                return True

    return False