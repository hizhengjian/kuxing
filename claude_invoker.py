"""
Claude调用层 - 通过subprocess调用Claude Code
"""
import subprocess
import os
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from state import ClaudeInvocation


@dataclass
class InvokeResult:
    """调用结果"""
    success: bool
    output: str = ""
    error: Optional[str] = None
    invocation: Optional[ClaudeInvocation] = None


class ClaudeInvoker:
    """Claude Code调用器"""

    def __init__(
        self,
        claude_path: str = "claude",
        model: str = "sonnet-4-20250514",
        timeout_seconds: int = 5400  # 90分钟，复杂文档生成任务需要较长时间
    ):
        """
        初始化调用器

        Args:
            claude_path: claude命令行路径
            model: 使用的模型
            timeout_seconds: 超时时间（秒）
        """
        self.claude_path = claude_path
        self.model = model
        self.timeout_seconds = timeout_seconds

    def invoke(
        self,
        prompt: str,
        project_path: Optional[str] = None,
        resume: bool = False,
        max_retries: int = 3
    ) -> InvokeResult:
        """
        调用Claude执行任务

        Args:
            prompt: 输入提示词
            project_path: 项目路径（用于设置cwd）
            resume: 是否使用--resume模式
            max_retries: 最大重试次数

        Returns:
            InvokeResult对象
        """
        # 构建命令
        cmd = [self.claude_path, "-p", prompt, "--dangerously-skip-permissions"]

        if resume:
            cmd.append("--resume")

        print(f"执行命令: {' '.join(cmd[:3])}...")
        print(f"Prompt长度: {len(prompt)} 字符")

        last_error = None

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # 第2次起尝试用 --resume 继续执行（之前的任务可能未完成）
                use_resume = resume or attempt > 0

                # 构建命令
                invoke_cmd = [self.claude_path, "-p", prompt, "--dangerously-skip-permissions"]
                if use_resume:
                    invoke_cmd.append("--resume")
                    print(f"使用 --resume 模式继续执行...")

                print(f"执行命令: {' '.join(invoke_cmd[:3])}...")
                print(f"Prompt长度: {len(prompt)} 字符, 超时: {self.timeout_seconds}秒")

                # 执行命令
                result = subprocess.run(
                    invoke_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=project_path or os.getcwd(),
                    env={**os.environ, "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")}
                )

                duration_ms = int((time.time() - start_time) * 1000)

                # 检查返回码
                if result.returncode != 0:
                    last_error = f"Claude返回错误码: {result.returncode}\nStderr: {result.stderr}"
                    print(f"调用失败 (尝试 {attempt + 1}/{max_retries}): {last_error}")
                    time.sleep(2 ** attempt)  # 指数退避
                    continue

                # 成功
                output = result.stdout

                # 解析token使用量（如果可用）
                input_tokens = 0
                output_tokens = 0

                # 构建调用记录
                invocation = ClaudeInvocation(
                    prompt=prompt[:500],  # 截断保存
                    model=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=duration_ms
                )

                print(f"调用成功，耗时: {duration_ms/1000:.1f}秒")

                return InvokeResult(
                    success=True,
                    output=output,
                    invocation=invocation
                )

            except subprocess.TimeoutExpired:
                last_error = f"调用超时 ({self.timeout_seconds}秒)"
                print(f"调用超时 (尝试 {attempt + 1}/{max_retries})，将使用 --resume 继续...")
                time.sleep(5)  # 等待5秒让Claude完成写入

            except Exception as e:
                last_error = f"调用异常: {str(e)}"
                print(f"调用异常 (尝试 {attempt + 1}/{max_retries}): {last_error}")
                time.sleep(2 ** attempt)

        # 所有重试都失败
        return InvokeResult(
            success=False,
            error=f"经过{max_retries}次重试后失败: {last_error}"
        )

    def invoke_simple(self, prompt: str) -> str:
        """
        简单调用，只返回输出字符串

        Args:
            prompt: 输入提示词

        Returns:
            Claude的输出字符串
        """
        result = self.invoke(prompt)
        if result.success:
            return result.output
        else:
            raise RuntimeError(f"Claude调用失败: {result.error}")


def check_claude_available() -> bool:
    """
    检查Claude是否可用

    Returns:
        True if claude命令可用
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_claude_version() -> str:
    """
    获取Claude版本

    Returns:
        版本字符串，未找到返回"unknown"
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    except:
        return "unknown"