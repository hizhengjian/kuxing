"""
LLM 记忆压缩器 - 使用 LLM API 智能压缩记忆文件
支持 Claude API 和其他兼容 API（如 MiniMax）
"""
import re
from datetime import datetime
from typing import Optional
from pathlib import Path


class LLMCompressor:
    """使用 LLM 智能压缩记忆文件"""

    def __init__(self, claude_invoker):
        """
        初始化压缩器

        Args:
            claude_invoker: ClaudeInvoker 实例（支持任何兼容的 LLM API）
        """
        self.claude_invoker = claude_invoker

    def compress_memory(self, content: str, target_size: int,
                       memory_type: str = "context") -> str:
        """
        使用 LLM 压缩记忆内容

        Args:
            content: 原始记忆内容
            target_size: 目标大小（字符数）
            memory_type: 记忆类型（context/session/knowledge）

        Returns:
            压缩后的内容
        """
        current_size = len(content)

        if current_size <= target_size:
            return content

        # 计算压缩比例
        compression_ratio = target_size / current_size

        # 构建压缩 prompt
        prompt = self._build_compression_prompt(
            content,
            current_size,
            target_size,
            compression_ratio,
            memory_type
        )

        # 调用 LLM 进行压缩（使用配置的 API，如 MiniMax）
        print(f"🤖 使用 LLM 压缩记忆文件（{current_size} → {target_size} 字符）...")
        result = self.claude_invoker.invoke(
            prompt=prompt,
            max_retries=2
        )

        if not result.success:
            print(f"⚠️  LLM 压缩失败，使用简单截断: {result.error}")
            # 压缩失败，使用简单截断
            return self._simple_truncate(content, target_size)

        # 提取压缩后的内容
        compressed = self._extract_compressed_content(result.output)

        # 验证压缩结果
        if len(compressed) > target_size * 1.1:  # 允许 10% 误差
            print(f"⚠️  压缩结果仍超出目标 ({len(compressed)} > {target_size * 1.1})，再次截断")
            # 压缩不够，再次截断
            compressed = self._simple_truncate(compressed, target_size)

        return compressed

    def _build_compression_prompt(self, content: str, current_size: int,
                                  target_size: int, compression_ratio: float,
                                  memory_type: str) -> str:
        """构建压缩 prompt"""

        if memory_type == "context":
            strategy = """
压缩策略（项目记忆）：
1. 合并相同类型的 section（如多个"新发现的路径"合并为一个）
2. 去重：相同的路径、命令只保留一次
3. 时间优先：保留最近的信息，删除旧的重复信息
4. 保留关键信息：路径、命令、账号信息必须保留
5. 删除冗余描述：只保留核心信息
"""
        elif memory_type == "session":
            strategy = """
压缩策略（会话记忆）：
1. 保留"当前状态"和"下一步计划"（最重要）
2. 压缩"工作日志"：只保留最近 10 条
3. 压缩"错误与修正"：只保留未解决的和最近的
4. 合并"关键文件"：去重，只保留文件路径和简短说明
5. 删除过时的"学习总结"
"""
        else:  # knowledge
            strategy = """
压缩策略（知识沉淀）：
1. 保留最佳实践和避坑指南
2. 删除已过时的经验
3. 合并相似的经验
4. 保留关键发现和优化建议
5. 删除冗余的详细说明
"""

        prompt = f"""你是一个记忆压缩专家。请将以下记忆内容从 {current_size} 字符压缩到约 {target_size} 字符（压缩比例：{compression_ratio:.1%}）。

{strategy}

**重要规则**：
1. 保持 Markdown 格式和 section 结构
2. 不要改变 section 标题（以 ## 开头的行）
3. 优先保留最新的信息
4. 删除重复和冗余的内容
5. 保留所有关键信息（路径、命令、账号、错误）
6. 压缩描述性文字，保留事实性信息

**原始内容**：

{content}

**请输出压缩后的内容**（直接输出 Markdown，不要添加任何解释）：
"""
        return prompt

    def _extract_compressed_content(self, output: str) -> str:
        """从 Claude 输出中提取压缩后的内容"""
        # Claude 可能会添加一些说明，尝试提取 Markdown 内容

        # 如果输出包含代码块，提取代码块内容
        code_block_match = re.search(r'```(?:markdown)?\n(.*?)\n```', output, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # 如果没有代码块，查找第一个 ## 开始的内容
        lines = output.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('##') or line.startswith('#'):
                start_idx = i
                break

        if start_idx > 0:
            return '\n'.join(lines[start_idx:]).strip()

        # 否则返回全部内容
        return output.strip()

    def _simple_truncate(self, content: str, target_size: int) -> str:
        """简单截断（保留前面部分）"""
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
        truncated += '\n\n[... 内容已截断 ...]'

        return truncated

    def analyze_memory_structure(self, content: str) -> dict:
        """
        分析记忆文件结构

        Returns:
            {
                'total_size': int,
                'sections': [
                    {
                        'name': str,
                        'size': int,
                        'timestamp': datetime or None,
                        'line_start': int,
                        'line_end': int
                    }
                ]
            }
        """
        lines = content.split('\n')
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            if line.startswith('##'):
                # 保存上一个 section
                if current_section:
                    current_section['line_end'] = i - 1
                    current_section['size'] = sum(
                        len(lines[j]) + 1
                        for j in range(current_section['line_start'],
                                      current_section['line_end'] + 1)
                    )
                    sections.append(current_section)

                # 开始新 section
                section_name = line[2:].strip()

                # 尝试提取时间戳
                timestamp = None
                timestamp_match = re.search(
                    r'\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)',
                    section_name
                )
                if timestamp_match:
                    try:
                        timestamp = datetime.strptime(
                            timestamp_match.group(1),
                            '%Y-%m-%d %H:%M:%S'
                        )
                    except:
                        pass

                current_section = {
                    'name': section_name,
                    'timestamp': timestamp,
                    'line_start': i,
                    'line_end': None,
                    'size': 0
                }

        # 保存最后一个 section
        if current_section:
            current_section['line_end'] = len(lines) - 1
            current_section['size'] = sum(
                len(lines[j]) + 1
                for j in range(current_section['line_start'],
                              current_section['line_end'] + 1)
            )
            sections.append(current_section)

        return {
            'total_size': len(content),
            'sections': sections
        }

    def smart_compress_by_sections(self, content: str, target_size: int) -> str:
        """
        按 section 智能压缩（混合策略）

        策略：
        1. 分析每个 section 的大小和时间戳
        2. 对于旧的、大的 section，使用 LLM 压缩
        3. 对于新的、小的 section，保持不变
        4. 合并相同类型的 section
        """
        analysis = self.analyze_memory_structure(content)

        if analysis['total_size'] <= target_size:
            return content

        sections = analysis['sections']
        lines = content.split('\n')

        # 计算需要压缩的比例
        compression_ratio = target_size / analysis['total_size']

        # 按时间和大小排序 section
        now = datetime.now()
        for section in sections:
            # 计算年龄（小时）
            if section['timestamp']:
                age_hours = (now - section['timestamp']).total_seconds() / 3600
            else:
                age_hours = 999  # 无时间戳的视为很旧

            section['age_hours'] = age_hours

            # 计算优先级（年龄越大、体积越大，优先级越高 = 越需要压缩）
            section['compress_priority'] = age_hours * section['size']

        # 按优先级排序（优先压缩旧的、大的）
        sections.sort(key=lambda s: s['compress_priority'], reverse=True)

        # 逐个压缩 section，直到达到目标大小
        compressed_sections = {}
        current_total_size = analysis['total_size']

        for section in sections:
            if current_total_size <= target_size:
                break

            # 提取 section 内容
            section_lines = lines[section['line_start']:section['line_end']+1]
            section_content = '\n'.join(section_lines)

            # 计算该 section 需要压缩到的大小
            section_target = int(section['size'] * compression_ratio * 0.8)

            if section['size'] > 1000 and section['age_hours'] > 1:
                # 大且旧的 section，使用 LLM 压缩
                compressed = self.compress_memory(
                    section_content,
                    section_target,
                    memory_type="context"
                )
                compressed_sections[section['line_start']] = compressed

                # 更新总大小
                size_reduction = section['size'] - len(compressed)
                current_total_size -= size_reduction
            else:
                # 小或新的 section，保持不变
                compressed_sections[section['line_start']] = section_content

        # 重新组装内容
        result_lines = []
        for i, line in enumerate(lines):
            if i in compressed_sections:
                # 使用压缩后的 section
                result_lines.append(compressed_sections[i])
                # 跳过原 section 的其他行
                section = next(s for s in sections if s['line_start'] == i)
                i = section['line_end']
            elif not any(s['line_start'] < i <= s['line_end'] for s in sections):
                # 不在任何 section 内的行（如文件头）
                result_lines.append(line)

        return '\n'.join(result_lines)
