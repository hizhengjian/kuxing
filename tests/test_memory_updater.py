"""
测试 MemoryUpdater 模块
"""
import pytest
from pathlib import Path
from memory_updater import MemoryUpdater
from memory_store import MemoryStore


@pytest.fixture
def temp_memory_store(tmp_path):
    """创建临时记忆存储"""
    memory_store = MemoryStore(str(tmp_path), "test-project")
    memory_store.ensure_dirs()

    # 创建初始的项目记忆文件
    memory_store.context_file.write_text("# 测试项目记忆\n\n", encoding='utf-8')

    return memory_store


@pytest.fixture
def memory_updater(temp_memory_store):
    """创建记忆更新器"""
    return MemoryUpdater(temp_memory_store)


def test_memory_updater_init(memory_updater):
    """测试 MemoryUpdater 初始化"""
    assert memory_updater.memory_store is not None
    assert memory_updater.discovered_paths == set()
    assert memory_updater.discovered_commands == set()
    assert memory_updater.discovered_errors == set()


def test_extract_paths_unix(memory_updater):
    """测试提取 Unix 路径"""
    text = "分析了 /home/user/project/src/main.cpp 和 /usr/local/include/utils.h"
    paths = memory_updater._extract_paths(text)

    assert '/home/user/project/src/main.cpp' in paths
    assert '/usr/local/include/utils.h' in paths


def test_extract_paths_windows(memory_updater):
    """测试提取 Windows 路径"""
    text = "分析了 C:\\Users\\user\\project\\src\\main.cpp"
    paths = memory_updater._extract_paths(text)

    assert 'C:\\Users\\user\\project\\src\\main.cpp' in paths


def test_extract_paths_filter_short(memory_updater):
    """测试过滤太短的路径"""
    text = "路径 /a /ab /abc /abcd 和 /home/user/file.txt"
    paths = memory_updater._extract_paths(text)

    # 太短的路径应该被过滤（<5个字符）
    assert '/a' not in paths
    assert '/ab' not in paths
    assert '/abc' not in paths
    # /abcd 是5个字符，会被包含
    assert '/abcd' in paths
    assert '/home/user/file.txt' in paths


def test_extract_commands(memory_updater):
    """测试提取命令"""
    text = """
    执行: gcc -o test test.c
    运行: make clean
    使用命令: `python setup.py install`
    """
    commands = memory_updater._extract_commands(text)

    assert 'gcc -o test test.c' in commands
    assert 'make clean' in commands
    assert 'python setup.py install' in commands


def test_extract_error_english(memory_updater):
    """测试提取英文错误信息"""
    text = "执行成功。Error: file not found。继续执行。"
    error = memory_updater._extract_error(text)

    assert 'Error: file not found' in error


def test_extract_error_chinese(memory_updater):
    """测试提取中文错误信息"""
    text = "执行成功。编译失败，缺少头文件。继续执行。"
    error = memory_updater._extract_error(text)

    assert '编译失败' in error or '缺少头文件' in error


def test_update_from_result_paths(memory_updater, temp_memory_store):
    """测试从结果中更新路径"""
    result = {
        'status': 'completed',
        'summary': '分析了 /home/user/project/src/main.cpp',
        'files_modified': ['/home/user/project/src/utils.cpp']
    }

    memory_updater.update_from_result(result)

    # 检查路径是否被记录
    assert '/home/user/project/src/main.cpp' in memory_updater.discovered_paths
    assert '/home/user/project/src/utils.cpp' in memory_updater.discovered_paths

    # 检查是否写入到项目记忆
    context = temp_memory_store.load_project_context()
    assert '/home/user/project/src/main.cpp' in context
    assert '/home/user/project/src/utils.cpp' in context


def test_update_from_result_commands(memory_updater, temp_memory_store):
    """测试从结果中更新命令"""
    result = {
        'status': 'completed',
        'summary': '执行: gcc -o test test.c 和运行: make clean',
        'files_modified': []
    }

    memory_updater.update_from_result(result)

    # 检查命令是否被记录
    assert 'gcc -o test test.c' in memory_updater.discovered_commands
    assert 'make clean' in memory_updater.discovered_commands

    # 检查是否写入到项目记忆
    context = temp_memory_store.load_project_context()
    assert 'gcc -o test test.c' in context
    assert 'make clean' in context


def test_update_from_result_errors(memory_updater, temp_memory_store):
    """测试从结果中更新错误信息"""
    result = {
        'status': 'completed',
        'summary': '编译失败，缺少头文件 stdio.h',
        'files_modified': []
    }

    memory_updater.update_from_result(result)

    # 检查错误是否被记录
    assert len(memory_updater.discovered_errors) > 0

    # 检查是否写入到项目记忆
    context = temp_memory_store.load_project_context()
    assert '编译失败' in context or '缺少头文件' in context


def test_update_from_result_no_duplicates(memory_updater, temp_memory_store):
    """测试不重复记录相同信息"""
    result = {
        'status': 'completed',
        'summary': '分析了 /home/user/project/src/main.cpp',
        'files_modified': []
    }

    # 第一次更新
    memory_updater.update_from_result(result)
    context1 = temp_memory_store.load_project_context()

    # 第二次更新相同信息
    memory_updater.update_from_result(result)
    context2 = temp_memory_store.load_project_context()

    # 内容应该相同（不重复添加）
    assert context1 == context2


def test_update_from_result_failed_status(memory_updater, temp_memory_store):
    """测试处理失败状态"""
    result = {
        'status': 'failed',
        'summary': 'Error: compilation failed',
        'files_modified': []
    }

    memory_updater.update_from_result(result)

    # 失败状态也应该记录错误
    context = temp_memory_store.load_project_context()
    assert 'compilation failed' in context or 'Error' in context


def test_append_paths_empty(memory_updater, temp_memory_store):
    """测试追加空路径集合"""
    # 追加空集合不应该修改文件
    original_context = temp_memory_store.load_project_context()
    memory_updater._append_paths(set())
    new_context = temp_memory_store.load_project_context()

    assert original_context == new_context


def test_append_commands_empty(memory_updater, temp_memory_store):
    """测试追加空命令集合"""
    # 追加空集合不应该修改文件
    original_context = temp_memory_store.load_project_context()
    memory_updater._append_commands(set())
    new_context = temp_memory_store.load_project_context()

    assert original_context == new_context


def test_multiple_updates(memory_updater, temp_memory_store):
    """测试多次更新累积效果"""
    # 第一次更新
    result1 = {
        'status': 'completed',
        'summary': '分析了 /path/to/file1.cpp',
        'files_modified': []
    }
    memory_updater.update_from_result(result1)

    # 第二次更新
    result2 = {
        'status': 'completed',
        'summary': '分析了 /path/to/file2.cpp，执行: make test',
        'files_modified': []
    }
    memory_updater.update_from_result(result2)

    # 检查两次更新的内容都在
    context = temp_memory_store.load_project_context()
    assert '/path/to/file1.cpp' in context
    assert '/path/to/file2.cpp' in context
    assert 'make test' in context
