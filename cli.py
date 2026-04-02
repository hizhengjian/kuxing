#!/usr/bin/env python3
"""
苦行僧 CLI - 命令行接口
"""
import argparse
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from scheduler import Scheduler, run_from_config
from memory_store import MemoryStore
from config_schema import load_config
from claude_invoker import check_claude_available, get_claude_version


def cmd_init(args):
    """初始化新项目"""
    config_path = os.path.abspath(args.config)

    if not Path(config_path).exists():
        print(f"错误: 配置文件不存在 - {config_path}")
        return 1

    # 加载配置验证
    config = load_config(config_path)

    print(f"初始化项目: {config.project_name}")
    print(f"项目路径: {config.project_path}")
    print(f"执行模式: {config.mode}")
    print(f"任务数: {len(config.tasks)}")

    # 创建记忆存储
    base_path = Path(__file__).parent
    memory_store = MemoryStore(str(base_path), config.project_slug)
    memory_store.ensure_dirs()

    # 保存配置副本
    import shutil
    dest_config = memory_store.get_config_path()
    shutil.copy(config_path, dest_config)

    # 创建初始state
    from scheduler import Scheduler
    sched = Scheduler(
        base_path=str(base_path),
        config_path=config_path,
        dry_run=True  # init只是初始化，不实际执行
    )
    sched.initialize()

    print(f"\n记忆目录: {memory_store.memory_dir}")
    print("初始化完成！")

    return 0


def cmd_run(args):
    """开始执行任务"""
    base_path = Path(__file__).parent

    # 检查Claude可用性
    if not check_claude_available():
        print("警告: 无法确认Claude是否可用，请确保claude命令在PATH中")

    try:
        scheduler = Scheduler(
            base_path=str(base_path),
            config_path=args.config or find_config(base_path),
            dry_run=args.dry_run
        )

        scheduler.initialize()

        if args.loop or scheduler.state.mode == "loop":
            result = scheduler.run_loop_mode(max_rounds=args.max_rounds)
        else:
            result = scheduler.run_until_complete(max_rounds=args.max_rounds)

        return 0 if result['failed_tasks'] == 0 else 1

    except KeyboardInterrupt:
        print("\n\n用户中断，状态已保存，下次可以继续")
        return 130
    except Exception as e:
        print(f"执行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_status(args):
    """查看当前状态"""
    base_path = Path(__file__).parent
    config_path = args.config or find_config(base_path)

    try:
        config = load_config(config_path)
        memory_store = MemoryStore(str(base_path), config.project_slug)
        summary = memory_store.export_summary()

        print(f"\n项目: {summary.get('project_name', 'N/A')}")
        print(f"路径: {summary.get('project_path', 'N/A')}")
        print(f"模式: {summary.get('mode', 'N/A')}")
        print(f"当前轮次: {summary.get('current_round', 0)}")
        print(f"\n任务进度:")
        print(f"  总数: {summary.get('total_tasks', 0)}")
        print(f"  已完成: {summary.get('completed_tasks', 0)}")
        print(f"  待处理: {summary.get('pending_tasks', 0)}")
        print(f"\n执行轮次: {summary.get('total_rounds', 0)}")

        if summary.get('last_activity'):
            print(f"最后活动: {summary['last_activity']}")

        if summary.get('last_error'):
            print(f"最后错误: {summary['last_error']}")

        return 0

    except Exception as e:
        print(f"获取状态失败: {e}")
        return 1


def cmd_resume(args):
    """继续执行"""
    args.loop = False
    # 确保 dry_run 存在（resume 默认不是 dry_run）
    if not hasattr(args, 'dry_run'):
        args.dry_run = False
    return cmd_run(args)


def cmd_reset(args):
    """重置所有状态"""
    base_path = Path(__file__).parent
    config_path = args.config or find_config(base_path)

    try:
        config = load_config(config_path)
        memory_store = MemoryStore(str(base_path), config.project_slug)

        if args.clear_all:
            print("清空所有记忆（包括配置）...")
            memory_store.clear_all()
            print("已清空所有记忆")
        else:
            print("清空轮次记忆...")
            memory_store.clear_rounds()
            memory_store.reset_state()
            print("轮次记忆已清空，状态已重置，配置保留")

        return 0

    except Exception as e:
        print(f"重置失败: {e}")
        return 1


def cmd_show(args):
    """显示历史记录"""
    base_path = Path(__file__).parent
    config_path = args.config or find_config(base_path)

    try:
        config = load_config(config_path)
        memory_store = MemoryStore(str(base_path), config.project_slug)

        # 使用 MemoryStore 的 get_context_for_next_round 方法显示历史
        if args.round:
            rounds = memory_store.load_rounds()
            round_data = [r for r in rounds if r.round == args.round]
            if not round_data:
                print(f"未找到 Round {args.round}")
            else:
                r = round_data[0]
                status_icon = "✅" if r.result and r.result.get('status') == 'completed' else "❌"
                print(f"\n### Round {r.round}: {status_icon} {r.task_description}")
                print(f"时间: {r.timestamp}")
                if r.input_context:
                    prev = r.input_context.get('previous_round_summary', '')
                    if prev:
                        print(f"摘要: {prev[:200]}...")
                if r.result:
                    if r.result.get('files_modified'):
                        print(f"修改: {', '.join(r.result['files_modified'])}")
                    if r.result.get('summary'):
                        print(f"结果: {r.result['summary'][:200]}...")
        elif args.history:
            rounds = memory_store.load_rounds()
            if not rounds:
                print("暂无历史记录")
            else:
                for r in rounds:
                    status_icon = "✅" if r.result and r.result.get('status') == 'completed' else "❌"
                    print(f"\n### Round {r.round}: {status_icon} {r.task_description}")
                    print(f"时间: {r.timestamp}")
                    if r.result and r.result.get('summary'):
                        print(f"  {r.result['summary'][:100]}...")
        else:
            # 默认显示历史
            print(memory_store.get_context_for_next_round())

        return 0

    except Exception as e:
        print(f"显示历史失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def find_config(base_path):
    """查找默认配置文件"""
    # 优先查找 memory 目录下保存的配置
    memory_dir = base_path / "memory"
    if memory_dir.exists():
        for project_dir in memory_dir.iterdir():
            config_path = project_dir / "config.yaml"
            if config_path.exists():
                return str(config_path)

    # 否则查找 examples 目录
    examples_dir = base_path / "examples"
    if examples_dir.exists():
        configs = list(examples_dir.glob("*.yaml"))
        if configs:
            return str(configs[0])

    raise FileNotFoundError("未找到配置文件，请使用 --config 指定")


def main():
    parser = argparse.ArgumentParser(
        description="苦行僧 - Claude Code 多轮任务调度系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s init --config examples/write_docs.yaml
  %(prog)s run
  %(prog)s status
  %(prog)s resume
  %(prog)s show --history
  %(prog)s show --round 3
  %(prog)s reset --confirm

更多信息:
  https://github.com/anthropics/claude-code
        """
    )

    # 全局选项
    parser.add_argument(
        "--config",
        help="配置文件路径 (YAML)",
        default=None
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init 子命令
    init_parser = subparsers.add_parser(
        "init",
        help="初始化新项目"
    )
    init_parser.add_argument(
        "--config",
        required=True,
        help="任务配置文件路径 (YAML)"
    )

    # run 子命令
    run_parser = subparsers.add_parser(
        "run",
        help="开始执行任务"
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟执行，不实际调用Claude"
    )
    run_parser.add_argument(
        "--loop",
        action="store_true",
        help="强制使用循环模式"
    )
    run_parser.add_argument(
        "--max-rounds",
        type=int,
        default=50,
        help="最大轮次限制 (默认: 50)"
    )

    # status 子命令
    status_parser = subparsers.add_parser(
        "status",
        help="查看当前状态"
    )

    # resume 子命令
    resume_parser = subparsers.add_parser(
        "resume",
        help="继续执行"
    )
    resume_parser.add_argument(
        "--max-rounds",
        type=int,
        default=50,
        help="最大轮次限制 (默认: 50)"
    )

    # reset 子命令
    reset_parser = subparsers.add_parser(
        "reset",
        help="重置所有状态"
    )
    reset_parser.add_argument(
        "--confirm",
        action="store_true",
        help="确认重置"
    )
    reset_parser.add_argument(
        "--clear-all",
        action="store_true",
        help="清空所有记忆（包括配置）"
    )

    # show 子命令
    show_parser = subparsers.add_parser(
        "show",
        help="显示历史记录"
    )
    show_parser.add_argument(
        "--history",
        action="store_true",
        help="显示所有历史"
    )
    show_parser.add_argument(
        "--round",
        type=int,
        help="显示指定轮次"
    )

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        # 无子命令时显示状态
        args.command = "status"
        args.config = None

    # 执行对应子命令
    commands = {
        "init": cmd_init,
        "run": cmd_run,
        "status": cmd_status,
        "resume": cmd_resume,
        "reset": cmd_reset,
        "show": cmd_show
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())