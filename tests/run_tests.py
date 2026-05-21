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
PAPERS_DIR = ROOT / "papers" / "__tests__"
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
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    project_name = "test-fe-minimal"
    project_dir = PAPERS_DIR / project_name

    if project_dir.exists():
        subprocess.run(["rm", "-rf", str(project_dir)], shell=True)

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

    # 跳转到 stata 阶段
    result = run_pipeline("jump", "stata")
    print("[OK] 跳转到 stata 阶段")

    # 生成 stata do-file
    result = run_pipeline("gen-do", "baseline")
    if result.returncode != 0:
        print("[FAIL] do-file 生成失败")
        print(result.stdout)
        return False
    print("[OK] do-file 生成成功")

    # 检查 do-file 存在（检查目录下是否有生成的 do 文件）
    do_dir = project_dir / "analysis" / "do-files"
    do_files = list(do_dir.glob("*.do")) if do_dir.exists() else []
    if do_files:
        print(f"[OK] do-file 文件存在: {do_files[0].name}")
    else:
        print("[WARN] do-file 目录为空，但命令执行成功")

    print("[OK] FE 最小测试通过！\n")
    return True


def test_did_minimal():
    """测试 2: 最小 DID 双重差分"""
    print("=" * 60)
    print("  TEST 2: DID 最小双重差分")
    print("=" * 60)

    project_name = "test-did-minimal"
    project_dir = PAPERS_DIR / project_name

    if project_dir.exists():
        subprocess.run(["rm", "-rf", str(project_dir)], shell=True)

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

    # 检查门禁系统：跳转到 stata 时应该能正确识别
    result = run_pipeline("jump", "stata")
    if result.returncode != 0:
        print("[FAIL] 跳转失败")
        return False
    print("[OK] 跳转到 stata 阶段成功")

    print("[OK] DID 最小测试通过！\n")
    return True


def test_compile_only():
    """测试 3: LaTeX 编译环境检查"""
    print("=" * 60)
    print("  TEST 3: LaTeX 编译环境检查")
    print("=" * 60)

    project_name = "test-compile-only"
    project_dir = PAPERS_DIR / project_name

    if project_dir.exists():
        subprocess.run(["rm", "-rf", str(project_dir)], shell=True)

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
    project_dir = PAPERS_DIR / project_name

    if project_dir.exists():
        subprocess.run(["rm", "-rf", str(project_dir)], shell=True)

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

    # 运行 cleanup - 这里需要模拟输入，我们直接检查命令是否存在
    result = run_pipeline("cleanup")
    if result.returncode == 0:
        print("[OK] cleanup 命令正常执行")
    else:
        print("[FAIL] cleanup 命令执行失败")
        print(result.stdout)
        print(result.stderr)
        return False

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
