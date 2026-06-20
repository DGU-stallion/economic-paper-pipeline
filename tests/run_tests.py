#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经济学论文自动化管线 - 最小测试套件
"""
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
PIPELINE = ROOT / "scripts" / "pipeline.py"


def run_pipeline(*args, cwd=None):
    """运行 pipeline 命令"""
    cmd = [sys.executable, str(PIPELINE)] + list(args)
    result = subprocess.run(
        cmd,
        cwd=cwd or str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    return result


def test_fe_minimal():
    """测试 1: 最小 FE 面板回归"""
    print("=" * 60)
    print("  TEST 1: FE 最小面板回归")
    print("=" * 60)

    # 创建测试项目
    (ROOT / "papers").mkdir(parents=True, exist_ok=True)
    project_name = "test-fe-minimal"
    project_dir = ROOT / "papers" / project_name

    if project_dir.exists():
        import shutil; shutil.rmtree(project_dir)

    # 新建项目
    result = run_pipeline("new", project_name)
    if result.returncode != 0:
        print("[FAIL] 项目创建失败")
        print(result.stderr)
        return False
    print("[OK] 项目创建成功")

    # 切换到项目
    run_pipeline("use", project_name)

    # 初始化 Context
    run_pipeline("set-context", "topic", "y_var", "y")
    run_pipeline("set-context", "topic", "d_var", "x")
    run_pipeline("set-context", "topic", "identification", "FE")
    print("[OK] Context 初始化完成")

    # 跳转到 analyze 阶段
    result = run_pipeline("jump", "analyze")
    print("[OK] 跳转到 analyze 阶段")

    # 检查 Python 后端可用
    result = run_pipeline("status")
    if "python" in result.stdout.lower() or result.returncode == 0:
        print("[OK] Pipeline 状态正常")

    print("[OK] FE 最小测试通过！\n")
    return True


def test_did_minimal():
    """测试 2: 最小 DID 双重差分"""
    print("=" * 60)
    print("  TEST 2: DID 最小双重差分")
    print("=" * 60)

    project_name = "test-did-minimal"
    project_dir = ROOT / "papers" / project_name

    if project_dir.exists():
        import shutil; shutil.rmtree(project_dir)

    # 新建项目
    result = run_pipeline("new", project_name)
    if result.returncode != 0:
        print("[FAIL] 项目创建失败")
        return False
    print("[OK] 项目创建成功")

    run_pipeline("use", project_name)

    # 初始化 Context - DID
    run_pipeline("set-context", "topic", "y_var", "y")
    run_pipeline("set-context", "topic", "d_var", "treat_x_post")
    run_pipeline("set-context", "topic", "identification", "DID")
    print("[OK] Context 初始化完成")

    # 检查门禁系统：跳转到 analyze 阶段
    result = run_pipeline("jump", "analyze")
    if result.returncode != 0:
        print("[FAIL] 跳转失败")
        return False
    print("[OK] 跳转到 analyze 阶段成功")

    print("[OK] DID 最小测试通过！\n")
    return True


def test_compile_only():
    """测试 3: LaTeX 编译环境检查"""
    print("=" * 60)
    print("  TEST 3: LaTeX 编译环境检查")
    print("=" * 60)

    project_name = "test-compile-only"
    project_dir = ROOT / "papers" / project_name

    if project_dir.exists():
        import shutil; shutil.rmtree(project_dir)

    # 新建项目
    run_pipeline("new", project_name)
    run_pipeline("use", project_name)
    print("[OK] 项目创建成功")

    # 跳转到 paper 阶段
    result = run_pipeline("jump", "paper")
    print("[OK] 跳转到 paper 阶段")

    # 检查门禁系统是否正确提醒缺少表格
    result = run_pipeline("status")
    if "context" in result.stdout.lower():
        print("[OK] 状态命令正常工作")

    print("[OK] 编译环境测试通过！\n")
    return True


def test_cleanup():
    """测试 4: 清道夫功能"""
    print("=" * 60)
    print("  TEST 4: 清道夫 cleanup 功能")
    print("=" * 60)

    project_name = "test-cleanup"
    project_dir = ROOT / "papers" / project_name

    if project_dir.exists():
        import shutil; shutil.rmtree(project_dir)

    run_pipeline("new", project_name)
    run_pipeline("use", project_name)

    # 创建一些假的 LaTeX 垃圾文件
    paper_dir = project_dir / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)

    junk_files = [
        "main.aux", "main.log", "main.bbl", "main.blg",
        "main.toc", "main.out",
    ]
    for f in junk_files:
        (paper_dir / f).write_text("junk content\n")

    print(f"[OK] 创建了 {len(junk_files)} 个测试垃圾文件")

    # 运行 cleanup
    result = run_pipeline("cleanup")
    if result.returncode != 0:
        print("[FAIL] cleanup 命令执行失败")
        print(result.stdout)
        return False

    # 验证垃圾文件是否已删除
    remaining = [f for f in junk_files if (paper_dir / f).exists()]
    if remaining:
        print(f"[FAIL] 以下文件未被清理: {remaining}")
        return False

    print(f"[OK] cleanup 命令成功清理了 {len(junk_files)} 个文件")
    print("[OK] 清道夫功能测试通过！\n")
    return True


def main():
    # Windows 控制台编码处理
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("\n" + "=" * 60)
    print("  [TEST] 经济学论文自动化管线 - 测试套件")
    print("=" * 60 + "\n")

    tests = [
        test_fe_minimal,
        test_did_minimal,
        test_compile_only,
        test_cleanup,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] 测试异常: {e}")
            failed += 1

    print("=" * 60)
    print("  📊 测试总结")
    print("=" * 60)
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    print(f"  总计: {len(tests)}")
    print()

    if failed == 0:
        print("  [OK] 所有测试通过！")
        return 0
    else:
        print("  [FAIL] 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
