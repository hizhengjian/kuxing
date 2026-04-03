"""
主调度器 - 协调所有组件执行任务
"""
import time
import logging
import sys
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from state import SchedulerState, RoundState, TaskState
from memory_store import MemoryStore
from config_schema import SchedulerConfig, load_config, create_tasks_state
from task_queue import create_queue, TaskQueue
from claude_invoker import ClaudeInvoker, InvokeResult
from prompts import build_task_prompt, PromptBuilder, extract_result_from_output


class Scheduler:
    """多轮任务调度器"""

    def __init__(
        self,
        base_path: str,
        config_path: str,
        claude_path: str = "claude",
        dry_run: bool = False
    ):
        """
        初始化调度器

        Args:
            base_path: 苦行僧项目根目录
            config_path: 任务配置文件路径
            claude_path: claude命令行路径
            dry_run: 是否只做模拟（不实际调用Claude）
        """
        self.base_path = Path(base_path)
        self.config_path = Path(config_path)
        self.dry_run = dry_run

        # 加载配置
        self.config = load_config(str(config_path))

        # 创建记忆存储
        self.memory_store = MemoryStore(
            str(self.base_path),
            self.config.project_slug
        )

        # 初始化日志系统
        self._setup_logger()

        # 创建Claude调用器
        self.claude_invoker = ClaudeInvoker(claude_path=claude_path)

        # 创建任务队列
        self.queue = create_queue(self.config.mode, {
            'loop_config': self.config.loop_config
        }, memory_store=self.memory_store)

        # 状态
        self.state: Optional[SchedulerState] = None

    def _setup_logger(self) -> None:
        """初始化日志系统"""
        # 创建日志目录
        log_dir = self.memory_store.memory_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # 生成日志文件名（带时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"run_{timestamp}.log"

        # 配置logger
        self.logger = logging.getLogger(f"kuxing_{self.config.project_slug}")
        self.logger.setLevel(logging.DEBUG)

        # 避免重复添加handler
        if not self.logger.handlers:
            # 文件handler - 写入完整日志
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)

            # 控制台handler - 简化输出
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(console_formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

        self.logger.info(f"日志文件: {log_file}")
        self.logger.info(f"项目: {self.config.project_name}")
        self.logger.info(f"模式: {self.config.mode}")

    def _log_round_start(self, round_num: int, task_desc: str) -> None:
        """记录轮次开始"""
        self.logger.info("=" * 60)
        self.logger.info(f"Round {round_num} 开始 | 任务: {task_desc}")
        self.logger.info("=" * 60)

    def _log_prompt(self, prompt: str, round_num: int) -> None:
        """记录发送的prompt（保存完整内容）"""
        self.logger.debug(f"[Round {round_num}] Prompt ({len(prompt)} 字符):")
        self.logger.debug("-" * 40)
        # 分割多行日志，每行单独记录
        for i, line in enumerate(prompt.split('\n')):
            self.logger.debug(line)
        self.logger.debug("-" * 40)

    def _log_result(self, result_dict: dict, round_num: int) -> None:
        """记录执行结果"""
        self.logger.info(f"[Round {round_num}] 结果:")
        self.logger.info(f"  status: {result_dict.get('status', 'unknown')}")
        self.logger.info(f"  files_modified: {result_dict.get('files_modified', [])}")
        self.logger.info(f"  files_created: {result_dict.get('files_created', [])}")
        summary = result_dict.get('summary', '')
        if summary:
            # summary可能很长，截断显示
            summary_preview = summary[:200] + '...' if len(summary) > 200 else summary
            self.logger.info(f"  summary: {summary_preview}")
        next_hints = result_dict.get('next_hints', '')
        if next_hints:
            hints_preview = next_hints[:200] + '...' if len(next_hints) > 200 else next_hints
            self.logger.info(f"  next_hints: {hints_preview}")

    def _log_error(self, error: str, round_num: int) -> None:
        """记录错误"""
        self.logger.error(f"[Round {round_num}] 错误: {error}")

    def _log_round_end(self, round_num: int, success: bool, elapsed: float) -> None:
        """记录轮次结束"""
        status = "成功" if success else "失败"
        self.logger.info(f"[Round {round_num}] 结束 | 状态: {status} | 耗时: {elapsed:.1f}秒")
        self.logger.info("-" * 40)

    def initialize(self) -> None:
        """初始化或加载状态"""
        # 检查是否已有保存的状态
        existing_state = self.memory_store.load_state()

        if existing_state:
            print(f"发现已有状态，加载中...")
            self.state = existing_state
            # 确保pending_tasks是最新的，且依赖都已满足
            self.state.pending_tasks = [
                task_id for task_id, task in self.state.tasks.items()
                if task.status == "pending"
                and all(
                    self.state.tasks.get(dep_id).status in ("completed", "skipped", "failed")
                    for dep_id in task.depends_on
                    if dep_id in self.state.tasks
                )
            ]
        else:
            print(f"创建新状态...")
            tasks, pending = create_tasks_state(self.config)

            self.state = SchedulerState(
                project_slug=self.config.project_slug,
                project_name=self.config.project_name,
                project_path=self.config.project_path,
                config_file=str(self.config_path),
                current_round=0,
                mode=self.config.mode,
                tasks=tasks,
                pending_tasks=pending
            )

            # 保存初始状态
            self.memory_store.save_state(self.state)

        print(f"项目: {self.state.project_name}")
        print(f"模式: {self.state.mode}")
        print(f"任务数: {len(self.state.tasks)}")
        print(f"当前轮次: {self.state.current_round}")

    def run_single_round(self) -> bool:
        """
        执行单轮任务

        Returns:
            True if执行成功，False if失败或无任务可执行
        """
        if not self.state:
            raise RuntimeError("调度器未初始化，请先调用initialize()")

        # 获取下一个任务
        task_id = self.queue.get_next_task(self.state)

        if not task_id:
            self.logger.warning("没有更多可执行的任务")
            return False

        task = self.state.tasks[task_id]

        # 更新任务状态
        task.status = "running"
        self.state.current_round += 1
        round_num = self.state.current_round

        # 记录轮次开始
        self._log_round_start(round_num, task.description)

        # 构建prompt
        context_summary = self.memory_store.get_context_for_next_round()
        prompt = build_task_prompt(self.state, task_id, context_summary)

        # 记录prompt
        self._log_prompt(prompt, round_num)

        # 执行（如果是dry_run则跳过）
        if self.dry_run:
            self.logger.info("[DRY RUN] 跳过实际执行")
            result_dict = {
                'status': 'completed',
                'files_modified': [],
                'files_created': [],
                'summary': '[Dry Run] 模拟执行',
                'next_hints': '无'
            }
            invocation_dict = None
            output = "[Dry Run] 模拟输出"
        else:
            start_time = time.time()
            # 调用Claude
            invoke_result = self.claude_invoker.invoke(
                prompt=prompt,
                project_path=self.state.project_path
            )
            elapsed = time.time() - start_time

            if invoke_result.success:
                output = invoke_result.output
                # 记录Claude原始输出（前1000字符到日志）
                self.logger.debug(f"[Round {round_num}] Claude输出 ({len(output)} 字符):")
                for i, line in enumerate(output[:1000].split('\n')):
                    self.logger.debug(line)
                if len(output) > 1000:
                    self.logger.debug("... (输出过长，已截断)")
                # 提取结果
                result_dict = extract_result_from_output(output)
                result_dict['status'] = 'completed'
                result_dict['raw_output'] = output  # 保存原始输出用于调试

                # 调用记录
                if invoke_result.invocation:
                    invocation_dict = {
                        'prompt': invoke_result.invocation.prompt[:500],
                        'model': invoke_result.invocation.model,
                        'input_tokens': invoke_result.invocation.input_tokens,
                        'output_tokens': invoke_result.invocation.output_tokens,
                        'duration_ms': invoke_result.invocation.duration_ms
                    }
                    self.logger.info(f"[Round {round_num}] Claude调用成功 | model: {invoke_result.invocation.model} | "
                                     f"input: {invoke_result.invocation.input_tokens} | output: {invoke_result.invocation.output_tokens} | "
                                     f"耗时: {invoke_result.invocation.duration_ms}ms")
            else:
                # 调用失败
                output = invoke_result.error or "Unknown error"
                result_dict = {
                    'status': 'failed',
                    'files_modified': [],
                    'files_created': [],
                    'summary': f'执行失败: {invoke_result.error}',
                    'next_hints': '请检查错误并重试'
                }
                invocation_dict = None
                self._log_error(invoke_result.error or "Unknown error", round_num)
                self.state.last_error = invoke_result.error

        # 更新任务状态
        task.status = result_dict.get('status', 'completed')
        task.round_completed = round_num

        if result_dict.get('status') == 'failed':
            task.error_message = result_dict.get('summary', 'Unknown error')

        # 从pending移除
        if task_id in self.state.pending_tasks:
            self.state.pending_tasks.remove(task_id)

        # 记录完成轮次
        if result_dict.get('status') == 'completed':
            self.state.completed_rounds.append(round_num)

        # 创建轮次记忆
        depends_on_completed = [
            dep_id for dep_id in task.depends_on
            if dep_id in self.state.tasks and self.state.tasks[dep_id].status == "completed"
        ]

        round_state = RoundState(
            round=round_num,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            task_description=task.description,
            input_context={
                'project_path': self.state.project_path,
                'previous_round_summary': result_dict.get('summary', ''),
                'depends_on_completed': depends_on_completed
            },
            claude_invocation=invocation_dict,
            result=result_dict
        )

        # 保存轮次记忆
        self.memory_store.save_round(round_state)
        self.logger.debug(f"[Round {round_num}] 轮次记忆已保存")

        # 保存状态
        self.memory_store.save_state(self.state)
        self.logger.debug(f"[Round {round_num}] 调度器状态已保存")

        # 记录结果
        self._log_result(result_dict, round_num)

        return result_dict.get('status') == 'completed'

    def run_until_complete(self, max_rounds: int = 50) -> dict:
        """
        持续执行直到所有任务完成

        Args:
            max_rounds: 最大轮次限制

        Returns:
            执行摘要字典
        """
        if not self.state:
            self.initialize()

        self.logger.info(f"\n开始执行，最多 {max_rounds} 轮...")

        start_time = time.time()
        completed = 0
        failed = 0

        while self.queue.should_continue(self.state):
            if self.state.current_round >= max_rounds:
                self.logger.info(f"\n达到最大轮次限制 ({max_rounds})，停止")
                break

            # 检查是否所有任务都完成
            if self.state.is_all_completed():
                self.logger.info("\n所有任务已完成")
                break

            # 执行一轮
            success = self.run_single_round()

            if success:
                completed += 1
            else:
                failed += 1
                # 如果失败的是串行队列中的任务，可能无法继续
                if self.state.mode == "serial":
                    self.logger.warning("串行任务失败，停止执行")
                    break

        elapsed = time.time() - start_time

        # 生成最终报告
        summary = {
            'total_rounds': self.state.current_round,
            'completed_tasks': completed,
            'failed_tasks': failed,
            'elapsed_seconds': elapsed,
            'final_state': self.state.to_dict()
        }

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"执行完成")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"总轮次: {summary['total_rounds']}")
        self.logger.info(f"成功: {completed}")
        self.logger.info(f"失败: {failed}")
        self.logger.info(f"耗时: {elapsed:.1f}秒")

        return summary

    def run_loop_mode(self, max_rounds: int = 100) -> dict:
        """
        循环模式执行

        Args:
            max_rounds: 最大轮次限制（不含first_task）

        Returns:
            执行摘要字典
        """
        if not self.state:
            self.initialize()

        if self.state.mode != "loop":
            raise RuntimeError("只能在loop模式下调用run_loop_mode()")

        self.logger.info(f"\n开始循环执行，最多 {max_rounds} 轮...")
        self.logger.info(f"停止条件: {self.config.loop_config.stop_condition or '无'}")

        start_time = time.time()
        consecutive_success = 0

        # 先执行 first_task（如果配置了且还没执行过）
        first_task_id = getattr(self.config.loop_config, 'first_task_id', None)
        if first_task_id and self.state.current_round == 0:
            self.logger.info(f"\n执行首轮任务: {first_task_id}")
            # 直接执行首轮任务，不通过队列
            task = self.state.tasks.get(first_task_id)
            if task:
                task.status = "running"
                self.state.current_round += 1
                round_num = self.state.current_round
                self._log_round_start(round_num, task.description)

                # 构建prompt（首轮任务不使用context_summary）
                prompt = self._build_first_task_prompt(task)
                self._log_prompt(prompt, round_num)

                # 执行
                invoke_result = self.claude_invoker.invoke(
                    prompt=prompt,
                    project_path=self.state.project_path
                )

                if invoke_result.success:
                    result_dict = extract_result_from_output(invoke_result.output)
                    result_dict['status'] = 'completed'
                    result_dict['raw_output'] = invoke_result.output
                    invocation_dict = None
                    if invoke_result.invocation:
                        invocation_dict = {
                            'prompt': invoke_result.invocation.prompt[:500],
                            'model': invoke_result.invocation.model,
                            'input_tokens': invoke_result.invocation.input_tokens,
                            'output_tokens': invoke_result.invocation.output_tokens,
                            'duration_ms': invoke_result.invocation.duration_ms
                        }
                    self.logger.info(f"[Round {round_num}] Claude调用成功 | model: {invoke_result.invocation.model}")
                else:
                    result_dict = {
                        'status': 'failed',
                        'files_modified': [],
                        'files_created': [],
                        'summary': f'执行失败: {invoke_result.error}',
                        'next_hints': '请检查错误并重试'
                    }
                    invocation_dict = None
                    self._log_error(invoke_result.error or "Unknown error", round_num)

                # 更新状态
                task.status = result_dict.get('status', 'completed')
                task.round_completed = round_num
                self.state.completed_rounds.append(round_num)

                # 保存轮次记忆
                round_state = RoundState(
                    round=round_num,
                    timestamp=datetime.now().isoformat(),
                    task_id=first_task_id,
                    task_description=task.description,
                    input_context={
                        'project_path': self.state.project_path,
                        'previous_round_summary': result_dict.get('summary', ''),
                        'depends_on_completed': []
                    },
                    claude_invocation=invocation_dict,
                    result=result_dict
                )
                self.memory_store.save_round(round_state)
                self._log_result(result_dict, round_num)

                if result_dict.get('status') == 'completed':
                    consecutive_success = 1

        # 解析停止条件中的数字
        stop_n = float('inf')  # 默认不停止（直到达到max_rounds）
        import re
        stop_cond = self.config.loop_config.stop_condition
        if stop_cond:  # 只有非空时才解析
            match = re.search(r'连续(\d+)次成功', stop_cond)
            if match:
                stop_n = int(match.group(1))

        # 主循环
        while self.queue.should_continue(self.state):
            if self.state.current_round >= max_rounds:
                self.logger.info(f"\n达到最大轮次限制 ({max_rounds})，停止")
                break

            # 执行一轮
            success = self.run_single_round()

            if success:
                consecutive_success += 1
            else:
                consecutive_success = 0

            # 检查停止条件
            if consecutive_success >= stop_n:
                self.logger.info(f"\n达成停止条件：连续{stop_n}次成功，停止循环")
                break

        elapsed = time.time() - start_time

        summary = {
            'total_rounds': self.state.current_round,
            'consecutive_success': consecutive_success,
            'elapsed_seconds': elapsed,
            'final_state': self.state.to_dict()
        }

        self.logger.info(f"\n循环执行结束，共 {self.state.current_round} 轮，耗时 {elapsed:.1f}秒")

        return summary

    def _build_first_task_prompt(self, task) -> str:
        """为首轮任务构建prompt（不使用context_summary）"""
        # 格式化prompt_template中的变量
        prompt = task.prompt_template.format(project_path=self.state.project_path)
        return f"""## 本轮任务

### 任务描述
{task.description}

### 预期输出
{task.expected_output}

### 执行 Prompt
{prompt}

## 执行要求
1. 按照 prompt 执行任务
2. 确保达到 expected_output 的验收标准
3. 完成后用 <result> 标签返回结构化结果
"""

    def get_status(self) -> dict:
        """获取当前状态摘要"""
        if not self.state:
            return {"error": "未初始化"}

        return self.memory_store.export_summary()

    def reset(self, confirm: bool = False) -> None:
        """
        重置所有状态

        Args:
            confirm: 必须为True才会执行
        """
        if not confirm:
            print("请提供 --confirm 参数以确认重置")
            return

        print(f"重置项目: {self.config.project_slug}")
        self.memory_store.clear_rounds()

        # 重新初始化
        self.initialize()

        print("重置完成")

    def show_history(self, round_num: Optional[int] = None) -> str:
        """
        显示历史记录

        Args:
            round_num: 指定轮次，None则显示所有

        Returns:
            格式化的历史记录字符串
        """
        if round_num:
            rounds = [r for r in self.memory_store.load_rounds() if r.round == round_num]
            if not rounds:
                return f"未找到 Round {round_num}"
        else:
            rounds = self.memory_store.load_rounds()

        if not rounds:
            return "暂无历史记录"

        lines = []
        for r in rounds:
            status_icon = "✅" if r.result and r.result.get('status') == 'completed' else "❌"
            lines.append(f"\n### Round {r.round}: {status_icon} {r.task_description}")
            lines.append(f"时间: {r.timestamp}")

            if r.input_context:
                prev = r.input_context.get('previous_round_summary', '')
                if prev:
                    lines.append(f"摘要: {prev[:150]}...")

            if r.result:
                if r.result.get('files_modified'):
                    lines.append(f"修改: {', '.join(r.result['files_modified'])}")
                if r.result.get('files_created'):
                    lines.append(f"创建: {', '.join(r.result['files_created'])}")
                if r.result.get('summary'):
                    lines.append(f"结果: {r.result['summary'][:200]}...")

        return "\n".join(lines)


def run_from_config(
    config_path: str,
    base_path: str,
    mode: str = "auto",
    max_rounds: int = 50,
    dry_run: bool = False
) -> dict:
    """
    从配置文件运行调度器

    Args:
        config_path: 配置文件路径
        base_path: 苦行僧项目根目录
        mode: 执行模式，auto则使用配置文件中的设置
        max_rounds: 最大轮次
        dry_run: 是否模拟执行

    Returns:
        执行摘要
    """
    scheduler = Scheduler(
        base_path=base_path,
        config_path=config_path,
        dry_run=dry_run
    )

    scheduler.initialize()

    if mode == "auto":
        mode = scheduler.state.mode

    if mode == "loop":
        return scheduler.run_loop_mode(max_rounds=max_rounds)
    else:
        return scheduler.run_until_complete(max_rounds=max_rounds)