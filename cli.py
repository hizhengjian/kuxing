#!/usr/bin/env python3
"""
苦行僧 CLI - 命令行接口
"""
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def robust_input(prompt: str = "") -> str:
    """安全的输入函数，处理终端编码问题"""
    try:
        return input(prompt)
    except UnicodeDecodeError:
        # 从缓冲区读取原始字节并忽略编码错误
        sys.stdout.write(prompt)
        sys.stdout.flush()
        return sys.stdin.buffer.readline().decode("utf-8", errors="ignore").strip()


def check_dependencies():
    """检查依赖是否满足"""
    errors = []

    # 检查 Python 版本
    if sys.version_info < (3, 8):
        errors.append(f"Python 版本过低: {sys.version_info.major}.{sys.version_info.minor}，需要 Python 3.8+")

    # 检查 pyyaml
    try:
        import yaml
    except ImportError:
        errors.append("缺少 pyyaml 库，请运行: pip install pyyaml")

    if errors:
        print("错误: 依赖检查失败")
        for err in errors:
            print(f"  - {err}")
        print()
        print("安装依赖:")
        print("  pip install -r requirements.txt")
        sys.exit(1)


# 启动时检查依赖
check_dependencies()

from scheduler import Scheduler, run_from_config
from memory_store import MemoryStore
from config_schema import load_config
from claude_invoker import check_claude_available, get_claude_version
import yaml


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


def cmd_init_context(args):
    """初始化记忆模板"""
    base_path = Path(__file__).parent

    # 获取全局共享记忆模板
    if args.global_context:
        memory_store = MemoryStore(str(base_path), "temp")
        shared_path = memory_store.shared_context_file

        if shared_path.exists():
            print(f"全局共享记忆已存在: {shared_path}")
            if not args.force:
                print("使用 --force 覆盖")
                return 1

        template = """# 全局公共记忆

## SDK 路径
- Android SDK: ${ANDROID_SDK_HOME}
- NDK: ${ANDROID_NDK_HOME}
- Python: /usr/bin/python3

## 常用参考文档
- API规范: /docs/api-spec.yaml
- 设计文档: /docs/design.md

## 账号配置（使用 ${VAR_NAME} 引用环境变量）
- Harbor: ${HARBOR_USERNAME}
- GitLab: ${GITLAB_TOKEN}

"""
        memory_store.shared_context_dir.mkdir(parents=True, exist_ok=True)
        with open(shared_path, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"已创建全局共享记忆: {shared_path}")
        print("提示: 编辑此文件添加你的 SDK 路径、参考文件、账号配置等")
        print("      使用 ${VAR_NAME} 语法引用环境变量")

    # 获取项目记忆模板
    if args.project_context or not args.global_context:
        config_path = args.config or find_config(base_path)
        try:
            config = load_config(config_path)
        except Exception as e:
            print(f"错误: 无法加载配置 - {e}")
            return 1

        memory_store = MemoryStore(str(base_path), config.project_slug)
        memory_store.ensure_dirs()

        context_file = memory_store.context_file
        if context_file.exists():
            print(f"项目记忆已存在: {context_file}")
            if not args.force:
                print("使用 --force 覆盖")
                return 1

        template = f"""# 项目私有记忆

## 项目: {config.project_name}

## SDK 路径
- SDK路径: ${SDK_PATH}

## 参考文件
- 参考文档: /path/to/doc.md

## 账号配置（使用 ${VAR_NAME} 引用环境变量）
- 服务地址: ${SERVICE_URL}

## 项目特定信息
- 项目特性1: xxx
- 项目特性2: xxx

## 已知问题
- 模块A有bug，需要特殊处理

"""
        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"已创建项目记忆: {context_file}")
        print("提示: 编辑此文件添加你的项目特定信息")

    return 0


def cmd_run(args):
    """开始执行任务"""
    base_path = Path(__file__).parent
    config_path = os.path.abspath(args.config) if args.config else find_config(base_path)

    # 重新拷贝配置文件到 memory 目录（每次运行都用最新的配置）
    config = load_config(config_path)
    memory_store = MemoryStore(str(base_path), config.project_slug)
    memory_store.ensure_dirs()
    import shutil
    shutil.copy(config_path, memory_store.get_config_path())
    print(f"已更新配置: {memory_store.get_config_path()}")

    # 检查Claude可用性
    if not check_claude_available():
        print("警告: 无法确认Claude是否可用，请确保claude命令在PATH中")

    try:
        scheduler = Scheduler(
            base_path=str(base_path),
            config_path=config_path,
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


def cmd_parallel(args):
    """并行执行多个项目"""
    import subprocess
    import threading
    import time

    base_path = Path(__file__).parent

    if not args.configs:
        # 如果没指定配置，查找 examples 目录下所有配置
        examples_dir = base_path / "examples"
        if examples_dir.exists():
            configs = list(examples_dir.glob("*.yaml"))
        else:
            print("错误: 未找到配置文件，请使用 --config 指定")
            return 1
    else:
        configs = [Path(c) for c in args.configs]

    if len(configs) == 0:
        print("错误: 未找到任何配置文件")
        return 1

    print(f"=" * 60)
    print(f"并行执行 {len(configs)} 个项目")
    print(f"=" * 60)

    processes = []
    for cfg in configs:
        if not cfg.exists():
            print(f"警告: 配置文件不存在 - {cfg}")
            continue

        # 加载配置获取项目名
        try:
            config = load_config(str(cfg))
            project_name = config.project_name
        except Exception as e:
            project_name = cfg.stem
            print(f"警告: 无法加载配置 {cfg}: {e}")

        print(f"  [{len(processes)+1}] {project_name} ({cfg})")

    print(f"\n每个项目使用独立的记忆空间，互不干扰。")
    print(f"按 Ctrl+C 停止所有项目。")
    print(f"=" * 60)

    # 启动每个项目的run进程
    for cfg in configs:
        if not cfg.exists():
            continue

        config_path = str(cfg.absolute())

        # 使用 subprocess 启动独立进程
        # --loop 标志让任务持续运行
        cmd = [
            sys.executable,
            str(base_path / "cli.py"),
            "run",
            "--config", config_path
        ]
        if args.loop:
            cmd.append("--loop")

        print(f"\n启动进程: {Path(cfg).stem}")
        print(f"  命令: {' '.join(cmd)}")

        # 启动进程，重定向输出到文件
        log_dir = base_path / "parallel_logs"
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{Path(cfg).stem}_{timestamp}.log"

        with open(log_file, 'w') as f:
            proc = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=str(base_path)
            )

        processes.append({
            'config': str(cfg),
            'process': proc,
            'log': str(log_file),
            'name': Path(cfg).stem
        })

        print(f"  日志: {log_file}")
        print(f"  PID: {proc.pid}")

    if not processes:
        print("错误: 没有成功启动任何项目")
        return 1

    print(f"\n{'=' * 60}")
    print(f"已启动 {len(processes)} 个项目")
    print(f"查看日志: tail -f {log_dir}/<项目名>_*.log")
    print(f"{'=' * 60}")

    # 监控进程状态
    try:
        while True:
            time.sleep(30)  # 每30秒检查一次

            all_stopped = True
            for p in processes:
                if p['process'].poll() is None:
                    all_stopped = False
                else:
                    exit_code = p['process'].poll()
                    print(f"\n[!] 项目 {p['name']} 已结束 (退出码: {exit_code})")
                    print(f"    日志: {p['log']}")

            if all_stopped:
                print("\n所有项目已结束")
                break

            # 显示状态
            running = sum(1 for p in processes if p['process'].poll() is None)
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 运行中: {running}/{len(processes)}", end='\r')

    except KeyboardInterrupt:
        print("\n\n检测到 Ctrl+C，停止所有项目...")
        for p in processes:
            if p['process'].poll() is None:
                print(f"  停止 {p['name']} (PID: {p['process'].pid})...")
                p['process'].terminate()
                try:
                    p['process'].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p['process'].kill()

        print("所有项目已停止")
        return 130

    return 0


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


def cmd_create_task(args):
    """创建新任务（包含配置和记忆）"""
    base_path = Path(__file__).parent
    project_name = args.project_name

    print(f"🤖 创建任务: {project_name}")
    print("=" * 60)

    # ========== 第1步：项目路径 ==========
    print("\n" + "=" * 60)
    print("📂 第1步：项目路径")
    print("=" * 60)
    print("输入项目根目录路径（用于代码分析）:")
    project_path = robust_input("  路径: ").strip()

    # ========== 第2步：项目私有记忆 ==========
    print("\n" + "=" * 60)
    print("📝 第2步：项目私有记忆")
    print("=" * 60)
    print("直接输入任意内容，写入到【项目记忆】")
    print("可以写：网址、账号、备注、项目结构等任何内容")
    print("输入空行结束输入：")
    print("-" * 40)

    project_notes = []
    while True:
        line = robust_input("")
        if not line.strip():
            break
        project_notes.append(line)

    # ========== 第3步：全局共享记忆 ==========
    print("\n" + "=" * 60)
    print("🌐 第3步：全局共享记忆")
    print("=" * 60)
    print("直接输入任意内容，写入到【全局共享记忆】")
    print("所有项目共享，可写：通用账号、Token、服务器地址等")
    print("输入空行结束输入：")
    print("-" * 40)

    global_notes = []
    while True:
        line = robust_input("")
        if not line.strip():
            break
        global_notes.append(line)

    # ========== 第4步：任务配置 ==========
    print("\n" + "=" * 60)
    print("⚙️  第4步：任务配置")
    print("=" * 60)
    max_rounds_input = robust_input("最大轮次（默认50）: ").strip()
    max_rounds = int(max_rounds_input) if max_rounds_input else 50

    # ========== 生成文件 ==========
    print("\n" + "=" * 60)
    print("🔄 正在生成配置和记忆文件...")
    print("=" * 60)

    project_slug = project_name.lower().replace(' ', '-').replace('_', '-')

    # 生成配置文件
    config = {
        'project_name': project_name,
        'project_path': project_path or '.',
        'mode': 'loop',
        'tasks': [
            {
                'id': 'task_analyze',
                'description': f'分析 {project_name}',
                'prompt_template': '{context_summary}\n\n分析代码结构，生成文档。',
                'expected_output': '生成分析文档'
            }
        ],
        'loop_config': {
            'task_id': 'task_analyze',
            'max_rounds': max_rounds
        }
    }

    config_file = base_path / 'examples' / f'{project_slug}.yaml'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    memory_store = MemoryStore(str(base_path), project_slug)
    memory_store.ensure_dirs()

    # 保存项目记忆
    project_context_file = memory_store.memory_dir / "context.md"
    project_context_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    project_context = f"""# {project_name} 项目记忆

## 创建时间
{timestamp}

## 项目路径
{project_path or '(未指定)'}

## 自由笔记
"""
    if project_notes:
        project_context += "\n".join(f"- {note}" for note in project_notes)
    else:
        project_context += "- （暂无）"

    project_context_file.write_text(project_context, encoding='utf-8')

    # 保存全局共享记忆
    shared_context_file = memory_store.shared_context_file
    shared_context_file.parent.mkdir(parents=True, exist_ok=True)

    if global_notes:
        # 如果文件已存在，追加
        if shared_context_file.exists():
            existing = shared_context_file.read_text(encoding='utf-8')
            header = f"\n\n---\n\n# 全局共享记忆 - {project_name}\n\n## 创建时间\n{timestamp}\n\n## 自由笔记\n"
            content = header + "\n".join(f"- {note}" for note in global_notes)
            shared_context = existing + content
        else:
            shared_context = f"""# 全局共享记忆

## 创建时间
{timestamp}

## 自由笔记
"""
            shared_context += "\n".join(f"- {note}" for note in global_notes)
        shared_context_file.write_text(shared_context, encoding='utf-8')

    # 初始化其他记忆文件
    try:
        init_args = type('obj', (object,), {'config': str(config_file)})()
        cmd_init(init_args)
    except Exception as e:
        print(f"⚠️  初始化记忆失败: {e}")

    # ========== 输出报告 ==========
    print("\n" + "=" * 60)
    print("📋 创建完成报告")
    print("=" * 60)

    print(f"""
✅ 任务创建成功！

📁 配置文件：
   {config_file}

📝 项目记忆（仅本项目使用）：
   {project_context_file}
   内容预览：
{project_context[:300]}...

🌐 全局共享记忆（所有项目共享）：
   {shared_context_file}
   本次追加内容：
{chr(10).join(f'  - {n}' for n in global_notes) if global_notes else '  （本次未输入）'}

📚 其他记忆文件（自动创建）：
   {memory_store.memory_dir / 'MEMORY.md'}  - 记忆索引
   {memory_store.memory_dir / 'session.md'} - 会话记忆
   {memory_store.memory_dir / 'state.json'}  - 调度器状态

🚀 运行命令：
   python cli.py --config {config_file} run

💡 后续追加信息：
   • 编辑项目记忆：
     vim {project_context_file}
   • 编辑全局共享记忆：
     vim {shared_context_file}
   • 查看记忆目录：
     ls {memory_store.memory_dir}
""")

    return 0


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
        version="%(prog)s 0.5.1"
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

    # init-context 子命令
    init_context_parser = subparsers.add_parser(
        "init-context",
        help="初始化记忆模板（全局共享记忆/项目私有记忆）"
    )
    init_context_parser.add_argument(
        "--global",
        dest="global_context",
        action="store_true",
        help="初始化全局共享记忆 (~/.kuxing/shared/context.md)"
    )
    init_context_parser.add_argument(
        "--project",
        dest="project_context",
        action="store_true",
        help="初始化项目私有记忆"
    )
    init_context_parser.add_argument(
        "--config",
        help="配置文件路径（用于确定项目）"
    )
    init_context_parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已有文件"
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
        default=None,
        help="最大轮次限制 (默认: 使用配置文件中的值)"
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
        default=None,
        help="最大轮次限制 (默认: 使用配置文件中的值)"
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

    # parallel 子命令
    parallel_parser = subparsers.add_parser(
        "parallel",
        help="并行执行多个项目（每个项目独立记忆空间）"
    )
    parallel_parser.add_argument(
        "--config",
        nargs="+",
        dest="configs",
        help="配置文件路径列表（默认使用 examples/ 下所有配置）"
    )
    parallel_parser.add_argument(
        "--loop",
        action="store_true",
        help="使用循环模式持续执行"
    )

    # create-task 子命令
    create_task_parser = subparsers.add_parser(
        "create-task",
        help="创建新任务（交互式生成配置和记忆）"
    )
    create_task_parser.add_argument(
        "--project-name",
        "-p",
        required=True,
        help="项目名称"
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
        "init-context": cmd_init_context,
        "run": cmd_run,
        "parallel": cmd_parallel,
        "status": cmd_status,
        "resume": cmd_resume,
        "reset": cmd_reset,
        "show": cmd_show,
        "create-task": cmd_create_task
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())