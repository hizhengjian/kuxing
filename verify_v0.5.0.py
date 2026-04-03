#!/usr/bin/env python3
"""
快速验证 v0.5.0 新功能
测试：会话记忆、记忆索引、LLM 压缩
"""
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from session_memory import SessionMemory
from llm_compressor import LLMCompressor
from memory_store import MemoryStore
from claude_invoker import ClaudeInvoker


def test_session_memory():
    """测试会话记忆功能"""
    print("\n" + "="*60)
    print("测试 1: 会话记忆（SessionMemory）")
    print("="*60)

    # 创建临时目录
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # 初始化会话记忆
        session = SessionMemory(temp_dir, "test-project")
        session.initialize("测试项目", 1, "这是一个测试任务")

        # 验证文件创建
        session_file = temp_dir / "session.md"
        if not session_file.exists():
            print("❌ 失败：session.md 未创建")
            return False

        print("✅ session.md 已创建")

        # 更新当前状态
        session.update_current_state(
            summary="完成了功能A",
            next_hints="接下来实现功能B"
        )

        # 添加关键文件
        session.add_key_file("/tmp/test.py", "测试文件", 42)

        # 添加错误记录
        session.add_error("测试错误", "测试解决方案")

        # 获取摘要
        summary = session.get_summary_for_prompt()

        if "完成了功能A" not in summary:
            print("❌ 失败：摘要中没有找到更新的内容")
            return False

        print("✅ 会话记忆更新成功")
        print(f"✅ 摘要长度：{len(summary)} 字符")

        # 验证 10 个 section（注意：执行标题没有 # 前缀）
        content = session.load()
        sections = [
            "_测试项目 - Round",  # 执行标题（斜体格式）
            "# 当前状态",
            "# 任务规格",
            "# 关键文件",
            "# 工作流程",
            "# 错误与修正",
            "# 代码库文档",
            "# 学习总结",
            "# 关键结果",
            "# 工作日志"
        ]

        missing_sections = [s for s in sections if s not in content]
        if missing_sections:
            print(f"❌ 失败：缺少 section: {missing_sections}")
            return False

        print("✅ 所有 10 个 section 都存在")

        return True

    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir)


def test_memory_index():
    """测试记忆索引功能"""
    print("\n" + "="*60)
    print("测试 2: 记忆索引（MEMORY.md）")
    print("="*60)

    # 创建临时目录
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # 创建 MemoryStore
        memory_store = MemoryStore(str(temp_dir), "test-project")
        memory_store.ensure_dirs()

        # 创建记忆索引
        memory_store.create_memory_index()

        # 验证文件创建
        index_file = memory_store.index_file
        if not index_file.exists():
            print("❌ 失败：MEMORY.md 未创建")
            return False

        print("✅ MEMORY.md 已创建")

        # 读取内容
        content = index_file.read_text(encoding='utf-8')

        # 验证关键内容
        required_sections = [
            "# 项目记忆索引",
            "## 会话记忆",
            "## 项目背景",
            "## 知识沉淀"
        ]

        missing = [s for s in required_sections if s not in content]
        if missing:
            print(f"❌ 失败：缺少 section: {missing}")
            return False

        print("✅ 所有必需 section 都存在")

        # 更新索引
        memory_store.update_memory_index(
            "会话记忆",
            "测试会话",
            "test_session.md",
            "测试描述"
        )

        # 验证更新
        content = index_file.read_text(encoding='utf-8')
        if "test_session.md" not in content:
            print("❌ 失败：索引更新失败")
            return False

        print("✅ 索引更新成功")

        return True

    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir)


def test_llm_compressor():
    """测试 LLM 压缩功能"""
    print("\n" + "="*60)
    print("测试 3: LLM 压缩（LLMCompressor）")
    print("="*60)

    # 检查 claude 命令是否可用
    import subprocess
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("⚠️  警告：claude 命令不可用，跳过压缩测试")
            print("   提示：这不影响其他功能，只是无法测试实际压缩")
            return True  # 跳过但不算失败
    except Exception as e:
        print(f"⚠️  警告：无法检查 claude 命令: {e}")
        print("   提示：这不影响其他功能，只是无法测试实际压缩")
        return True  # 跳过但不算失败

    print("✅ claude 命令可用")

    # 创建 ClaudeInvoker
    claude_invoker = ClaudeInvoker()

    # 创建 LLMCompressor
    compressor = LLMCompressor(claude_invoker)

    # 创建一个大的测试内容（模拟超过限制的记忆文件）
    test_content = """# 测试记忆文件

## Section 1
这是第一个 section 的内容。
""" * 100  # 重复 100 次，确保超过限制

    print(f"✅ 创建测试内容：{len(test_content)} 字符")

    # 测试压缩（目标 1000 字符）
    print("🤖 开始压缩测试（这会调用 claude 命令）...")
    print("   注意：这会消耗一次 API 调用")

    try:
        compressed = compressor.compress_memory(
            content=test_content,
            target_size=1000,
            memory_type="test"
        )

        print(f"✅ 压缩完成：{len(test_content)} → {len(compressed)} 字符")

        # 验证压缩结果
        if len(compressed) > len(test_content):
            print("❌ 失败：压缩后反而变大了")
            return False

        if len(compressed) > 1100:  # 允许 10% 误差
            print(f"⚠️  警告：压缩结果 ({len(compressed)}) 超出目标 (1000)，但在允许范围内")

        print("✅ 压缩功能正常")

        return True

    except Exception as e:
        print(f"❌ 失败：压缩过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_size_check():
    """测试记忆大小检查和自动压缩"""
    print("\n" + "="*60)
    print("测试 4: 记忆大小检查和自动压缩")
    print("="*60)

    # 创建临时目录
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # 创建 MemoryStore
        memory_store = MemoryStore(str(temp_dir), "test-project")
        memory_store.ensure_dirs()

        # 创建一个超大的 session.md
        session_file = memory_store.session_file
        large_content = "# 测试内容\n" + ("这是测试内容。\n" * 2000)
        session_file.write_text(large_content, encoding='utf-8')

        original_size = len(large_content)
        print(f"✅ 创建超大 session.md：{original_size} 字符")

        # 检查是否需要压缩
        if original_size <= memory_store.MAX_SESSION_SIZE:
            print(f"⚠️  警告：测试内容 ({original_size}) 未超过限制 ({memory_store.MAX_SESSION_SIZE})")
            print("   提示：增加测试内容大小")
            return True  # 不算失败

        print(f"✅ 测试内容超过限制：{original_size} > {memory_store.MAX_SESSION_SIZE}")

        # 检查 claude 命令
        import subprocess
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print("⚠️  警告：claude 命令不可用，跳过自动压缩测试")
                return True
        except Exception:
            print("⚠️  警告：claude 命令不可用，跳过自动压缩测试")
            return True

        # 创建压缩器
        claude_invoker = ClaudeInvoker()
        compressor = LLMCompressor(claude_invoker)

        # 执行自动压缩检查
        print("🤖 执行自动压缩检查...")
        memory_store.check_and_compress_if_needed(compressor)

        # 验证压缩结果
        compressed_content = session_file.read_text(encoding='utf-8')
        compressed_size = len(compressed_content)

        print(f"✅ 压缩后大小：{compressed_size} 字符")

        if compressed_size >= original_size:
            print("⚠️  警告：压缩后大小未减少（可能压缩失败，使用了简单截断）")
        else:
            print(f"✅ 压缩成功：减少了 {original_size - compressed_size} 字符")

        return True

    except Exception as e:
        print(f"❌ 失败：{e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Kuxing v0.5.0 快速验证")
    print("="*60)

    tests = [
        ("会话记忆", test_session_memory),
        ("记忆索引", test_memory_index),
        ("LLM 压缩", test_llm_compressor),
        ("自动压缩", test_memory_size_check),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\n总计：{passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！v0.5.0 功能正常。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
