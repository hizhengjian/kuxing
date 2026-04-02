"""
状态数据结构和类型定义
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskType(Enum):
    """任务类型"""
    AGENT = "agent"
    BASH = "bash"
    LOOP = "loop"


class SchedulerMode(Enum):
    """调度模式"""
    SERIAL = "serial"
    PARALLEL = "parallel"
    LOOP = "loop"


@dataclass
class TaskState:
    """单个任务的状态"""
    id: str
    type: str = "agent"
    description: str = ""
    status: str = "pending"
    depends_on: List[str] = field(default_factory=list)
    prompt_template: str = ""
    expected_output: str = ""
    round_completed: Optional[int] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskState':
        return cls(**data)


@dataclass
class ClaudeInvocation:
    """Claude调用记录"""
    prompt: str
    model: str = "sonnet-4-20250514"
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    error: Optional[str] = None


@dataclass
class RoundResult:
    """单轮执行结果"""
    status: str  # completed, failed, partial
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    summary: str = ""
    next_hints: str = ""
    artifacts: Dict[str, str] = field(default_factory=dict)


@dataclass
class RoundState:
    """单轮记忆状态"""
    round: int
    timestamp: str
    task_id: str
    task_description: str
    input_context: Dict[str, Any] = field(default_factory=dict)
    claude_invocation: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoundState':
        return cls(
            round=data['round'],
            timestamp=data['timestamp'],
            task_id=data['task_id'],
            task_description=data['task_description'],
            input_context=data.get('input_context', {}),
            claude_invocation=data.get('claude_invocation'),
            result=data.get('result')
        )


@dataclass
class SchedulerState:
    """调度器全局状态"""
    project_slug: str
    project_name: str
    project_path: str
    config_file: str
    current_round: int = 0
    mode: str = "serial"
    tasks: Dict[str, TaskState] = field(default_factory=dict)
    completed_rounds: List[int] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    last_error: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """序列化时将TaskState转为dict"""
        return {
            'project_slug': self.project_slug,
            'project_name': self.project_name,
            'project_path': self.project_path,
            'config_file': self.config_file,
            'current_round': self.current_round,
            'mode': self.mode,
            'tasks': {k: v.to_dict() for k, v in self.tasks.items()},
            'completed_rounds': self.completed_rounds,
            'pending_tasks': self.pending_tasks,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_error': self.last_error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchedulerState':
        """反序列化时将dict转为TaskState"""
        tasks = {k: TaskState.from_dict(v) for k, v in data.get('tasks', {}).items()}
        state = cls(
            project_slug=data['project_slug'],
            project_name=data['project_name'],
            project_path=data['project_path'],
            config_file=data.get('config_file', ''),
            current_round=data.get('current_round', 0),
            mode=data.get('mode', 'serial'),
            tasks=tasks,
            completed_rounds=data.get('completed_rounds', []),
            pending_tasks=data.get('pending_tasks', []),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            last_error=data.get('last_error')
        )
        return state

    def update_timestamp(self):
        """更新最后修改时间"""
        self.updated_at = datetime.now().isoformat()

    def get_next_task(self) -> Optional[str]:
        """获取下一个待执行的任务"""
        for task_id in self.pending_tasks:
            task = self.tasks.get(task_id)
            if task and task.status == "pending":
                # 检查依赖是否都完成
                deps_completed = all(
                    self.tasks.get(dep_id).status == "completed"
                    for dep_id in task.depends_on
                    if dep_id in self.tasks
                )
                if deps_completed:
                    return task_id
        return None

    def is_all_completed(self) -> bool:
        """检查所有任务是否完成"""
        return all(
            task.status in ("completed", "skipped", "failed")
            for task in self.tasks.values()
        )