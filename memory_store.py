"""
记忆存储层 - 管理每轮状态的持久化
"""
import json
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from state import RoundState, SchedulerState


class MemoryStore:
    """记忆存储管理器"""

    # 记忆文件大小限制（字符数）
    MAX_SESSION_SIZE = 20000      # session.md 最大 20KB
    MAX_CONTEXT_SIZE = 30000      # context.md 最大 30KB
    MAX_KNOWLEDGE_SIZE = 25000    # knowledge_base.md 最大 25KB

    def __init__(self, base_path: str, project_slug: str):
        """
        初始化记忆存储

        Args:
            base_path: 基础路径，如 ~/claudecode_projects/kuxing
            project_slug: 项目标识符，用于创建子目录
        """
        self.base_path = Path(base_path)
        self.project_slug = project_slug
        self.memory_dir = self.base_path / "memory" / project_slug
        self.rounds_dir = self.memory_dir / "rounds"
        self.context_file = self.memory_dir / "context.md"
        self.knowledge_base_file = self.memory_dir / "knowledge_base.md"
        # 全局共享记忆目录（改为项目内路径，便于迁移）
        self.shared_context_dir = self.base_path / "shared_context"
        self.shared_context_file = self.shared_context_dir / "context.md"
        # 新增：会话记忆和索引文件
        self.session_file = self.memory_dir / "session.md"
        self.index_file = self.memory_dir / "MEMORY.md"

    def ensure_dirs(self):
        """确保目录结构存在"""
        self.rounds_dir.mkdir(parents=True, exist_ok=True)
        # 确保全局共享目录存在
        self.shared_context_dir.mkdir(parents=True, exist_ok=True)

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

    # ==================== 记忆管理层 ====================

    def load_shared_context(self) -> str:
        """
        加载全局共享记忆（shared_context/context.md）

        Returns:
            全局共享记忆内容，如果不存在返回空字符串
        """
        if self.shared_context_file.exists():
            try:
                with open(self.shared_context_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                return self.resolve_env_vars(content)
            except Exception as e:
                print(f"警告: 读取全局共享记忆失败 {self.shared_context_file}: {e}")
                return ""
        return ""

    def load_project_context(self) -> str:
        """
        加载项目私有记忆（memory/{project}/context.md）

        Returns:
            项目私有记忆内容，如果不存在返回空字符串
        """
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                return self.resolve_env_vars(content)
            except Exception as e:
                print(f"警告: 读取项目记忆失败 {self.context_file}: {e}")
                return ""
        return ""

    def load_knowledge_base(self) -> str:
        """
        加载知识沉淀（memory/{project}/knowledge_base.md）

        Returns:
            知识沉淀内容，如果不存在返回空字符串
        """
        if self.knowledge_base_file.exists():
            try:
                with open(self.knowledge_base_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"警告: 读取知识沉淀失败 {self.knowledge_base_file}: {e}")
                return ""
        return ""

    def append_knowledge_base(self, new_content: str) -> None:
        """
        追加知识到沉淀文件

        Args:
            new_content: 新增的知识内容
        """
        if not new_content.strip():
            return

        self.ensure_dirs()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 如果文件不存在，创建头部
        header = f"# 知识沉淀\n\n最后更新: {timestamp}\n\n"
        separator = "\n" + "=" * 40 + "\n"

        new_entry = f"## 更新 {timestamp}\n{new_content.strip()}\n"

        if self.knowledge_base_file.exists():
            # 追加到现有文件
            with open(self.knowledge_base_file, 'a', encoding='utf-8') as f:
                f.write(separator + new_entry)
        else:
            # 创建新文件
            with open(self.knowledge_base_file, 'w', encoding='utf-8') as f:
                f.write(header + new_entry)

    def append_project_context(self, new_content: str) -> None:
        """
        追加内容到项目记忆文件

        Args:
            new_content: 新增的内容
        """
        if not new_content.strip():
            return

        self.ensure_dirs()

        # 追加到现有文件
        with open(self.context_file, 'a', encoding='utf-8') as f:
            f.write(new_content)

    def resolve_env_vars(self, content: str) -> str:
        """
        替换内容中的 ${VAR_NAME} 为环境变量值

        Args:
            content: 原始内容

        Returns:
            替换环境变量后的内容
        """
        if not content:
            return content

        # 匹配 ${VAR_NAME} 模式
        pattern = r'\$\{([^}]+)\}'
        undefined_vars = []

        def replace_var(match):
            var_name = match.group(1)
            value = os.environ.get(var_name)
            if value is not None:
                return value
            # 环境变量不存在，记录并保留原样
            undefined_vars.append(var_name)
            return f"${{{var_name}}}"

        result = re.sub(pattern, replace_var, content)

        # 警告未定义的变量
        if undefined_vars:
            unique_vars = sorted(set(undefined_vars))
            print(f"⚠️  警告: 以下环境变量未定义: {', '.join(unique_vars)}")

        return result

    def get_full_context(self) -> str:
        """
        获取完整的上下文记忆（按优先级合并）

        优先级（高到低）：
        1. 项目私有记忆 (context.md)
        2. 全局共享记忆 (shared/context.md)
        3. 知识沉淀 (knowledge_base.md)

        Returns:
            格式化后的完整上下文
        """
        parts = []

        # 知识沉淀（最低优先级，但每轮都应参考）
        kb = self.load_knowledge_base()
        if kb:
            parts.append("## 历史知识沉淀\n请参考以下历史发现：\n" + kb)

        # 全局共享记忆
        shared = self.load_shared_context()
        if shared:
            parts.append("## 全局公共记忆\n" + shared)

        # 项目私有记忆（最高优先级）
        project = self.load_project_context()
        if project:
            parts.append("## 项目私有记忆\n" + project)

        if not parts:
            return ""

        return "\n\n---\n\n".join(parts)

    def create_context_template(self) -> str:
        """
        创建项目 context.md 模板（如果不存在）

        Returns:
            模板文件路径
        """
        self.ensure_dirs()

        if not self.context_file.exists():
            template = """# 项目私有记忆

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
            with open(self.context_file, 'w', encoding='utf-8') as f:
                f.write(template)
            return str(self.context_file)
        return ""

    def create_shared_context_template(self) -> str:
        """
        创建全局 shared_context/context.md 模板（如果不存在）

        Returns:
            模板文件路径
        """
        self.shared_context_dir.mkdir(parents=True, exist_ok=True)

        if not self.shared_context_file.exists():
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
            with open(self.shared_context_file, 'w', encoding='utf-8') as f:
                f.write(template)
            return str(self.shared_context_file)
        return ""

    # ==================== 记忆索引管理 ====================

    def load_memory_index(self) -> Dict[str, List[Dict]]:
        """
        加载记忆索引

        Returns:
            索引字典，格式：{section: [{title, filename, description}]}
        """
        if not self.index_file.exists():
            return {}

        content = self.index_file.read_text(encoding='utf-8')
        index = {}
        current_section = None

        for line in content.split('\n'):
            if line.startswith('## '):
                current_section = line[3:].strip()
                index[current_section] = []
            elif line.startswith('- [') and current_section:
                # 解析：- [标题](文件名) — 描述
                match = re.match(r'- \[([^\]]+)\]\(([^\)]+)\) — (.+)', line)
                if match:
                    title, filename, description = match.groups()
                    index[current_section].append({
                        'title': title,
                        'filename': filename,
                        'description': description
                    })

        return index

    def update_memory_index(self, section: str, title: str,
                           filename: str, description: str):
        """
        更新记忆索引

        Args:
            section: section 名称（如"会话记忆"、"用户偏好"）
            title: 记忆标题
            filename: 文件名
            description: 简短描述
        """
        self.ensure_dirs()

        # 读取现有索引
        if self.index_file.exists():
            content = self.index_file.read_text(encoding='utf-8')
        else:
            content = f"# 项目记忆索引\n\n最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"

        # 确保 section 存在
        section_header = f"## {section}"
        if section_header not in content:
            content += f"\n{section_header}\n"

        # 添加新条目
        entry = f"- [{title}]({filename}) — {description}"

        # 检查是否已存在
        if entry in content:
            return

        # 插入到对应 section
        lines = content.split('\n')
        new_lines = []
        in_section = False
        inserted = False

        for line in lines:
            new_lines.append(line)
            if line == section_header:
                in_section = True
            elif in_section and not inserted:
                if line.startswith('## ') or (line == '' and len(new_lines) > 1):
                    # 到达下一个 section 或空行，插入条目
                    new_lines.insert(-1, entry)
                    inserted = True
                    in_section = False

        if in_section and not inserted:
            # section 是最后一个，直接追加
            new_lines.append(entry)

        # 更新时间戳
        content = '\n'.join(new_lines)
        content = re.sub(
            r'最后更新：.*',
            f'最后更新：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            content
        )

        self.index_file.write_text(content, encoding='utf-8')

    def create_memory_index(self):
        """创建初始记忆索引"""
        if self.index_file.exists():
            return

        self.ensure_dirs()

        template = f"""# 项目记忆索引

最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 会话记忆
- [当前会话](session.md) — 当前执行状态和下一步计划

## 项目背景
- [项目信息](context.md) — 代码路径、文档路径、账号信息

## 知识沉淀
- [历史经验](knowledge_base.md) — 最佳实践、避坑指南

---

**使用说明**：
- 每次执行前，先读取此索引文件
- 根据任务需要，按需加载相关记忆文件
- 新增记忆时，同步更新此索引
"""
        self.index_file.write_text(template, encoding='utf-8')

    # ==================== 记忆大小控制 ====================

    def check_and_compress_if_needed(self, compressor=None):
        """
        检查并压缩记忆文件（如果超出限制）

        Args:
            compressor: LLMCompressor 实例（可选）
        """
        files_to_check = [
            (self.session_file, self.MAX_SESSION_SIZE, "session"),
            (self.context_file, self.MAX_CONTEXT_SIZE, "context"),
            (self.knowledge_base_file, self.MAX_KNOWLEDGE_SIZE, "knowledge")
        ]

        for file_path, max_size, memory_type in files_to_check:
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding='utf-8')
            current_size = len(content)

            if current_size > max_size:
                print(f"⚠️  {file_path.name} 超出限制 ({current_size} > {max_size})，开始压缩...")

                if compressor:
                    # 使用 LLM 压缩
                    compressed = compressor.compress_memory(
                        content,
                        max_size,
                        memory_type
                    )
                else:
                    # 使用简单截断
                    compressed = self._simple_truncate(content, max_size)

                file_path.write_text(compressed, encoding='utf-8')
                new_size = len(compressed)
                reduction = (1 - new_size / current_size) * 100
                print(f"✅ 压缩完成：{current_size} → {new_size} ({reduction:.1f}% 减少)")

    def _simple_truncate(self, content: str, target_size: int) -> str:
        """
        简单截断（保留前面部分）

        Args:
            content: 原始内容
            target_size: 目标大小

        Returns:
            截断后的内容
        """
        if len(content) <= target_size:
            return content

        # 在 section 边界截断
        lines = content.split('\n')
        truncated_lines = []
        current_size = 0

        for line in lines:
            if current_size + len(line) + 1 > target_size:
                break
            truncated_lines.append(line)
            current_size += len(line) + 1

        truncated = '\n'.join(truncated_lines)
        truncated += '\n\n[... 内容已截断，已压缩到目标大小 ...]'

        return truncated
