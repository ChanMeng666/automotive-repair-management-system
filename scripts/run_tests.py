#!/usr/bin/env python3
"""
测试运行脚本
用于运行各种类型的测试
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行单元测试...")
    cmd = "python -m pytest tests/unit -v --tb=short"
    returncode, stdout, stderr = run_command(cmd)
    
    print(f"返回码: {returncode}")
    if stdout:
        print("输出:")
        print(stdout)
    if stderr and returncode != 0:
        print("错误:")
        print(stderr)
    
    return returncode == 0


def run_integration_tests():
    """运行集成测试"""
    print("🔗 运行集成测试...")
    cmd = "python -m pytest tests/integration -v --tb=short"
    returncode, stdout, stderr = run_command(cmd)
    
    print(f"返回码: {returncode}")
    if stdout:
        print("输出:")
        print(stdout)
    if stderr and returncode != 0:
        print("错误:")
        print(stderr)
    
    return returncode == 0


def run_security_tests():
    """运行安全相关测试"""
    print("🔒 运行安全测试...")
    cmd = "python -m pytest tests/ -m security -v --tb=short"
    returncode, stdout, stderr = run_command(cmd)
    
    print(f"返回码: {returncode}")
    if stdout:
        print("输出:")
        print(stdout)
    if stderr and returncode != 0:
        print("错误:")
        print(stderr)
    
    return returncode == 0


def run_coverage_tests():
    """运行测试覆盖率检查"""
    print("📊 运行测试覆盖率检查...")
    cmd = "python -m pytest tests/ --cov=app --cov-report=html --cov-report=term"
    returncode, stdout, stderr = run_command(cmd)
    
    print(f"返回码: {returncode}")
    if stdout:
        print("输出:")
        print(stdout)
    if stderr and returncode != 0:
        print("错误:")
        print(stderr)
    
    return returncode == 0


def run_all_tests():
    """运行所有测试"""
    print("🚀 运行所有测试...")
    cmd = "python -m pytest tests/ -v --tb=short"
    returncode, stdout, stderr = run_command(cmd)
    
    print(f"返回码: {returncode}")
    if stdout:
        print("输出:")
        print(stdout)
    if stderr and returncode != 0:
        print("错误:")
        print(stderr)
    
    return returncode == 0


def check_test_structure():
    """检查测试结构"""
    print("📁 检查测试结构...")
    
    required_dirs = [
        "tests",
        "tests/unit", 
        "tests/integration",
        "tests/fixtures"
    ]
    
    required_files = [
        "tests/__init__.py",
        "tests/conftest.py",
        "pytest.ini"
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_dirs:
        print("❌ 缺少目录:")
        for dir_path in missing_dirs:
            print(f"  - {dir_path}")
    
    if missing_files:
        print("❌ 缺少文件:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    if not missing_dirs and not missing_files:
        print("✅ 测试结构完整")
        return True
    
    return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="汽车维修管理系统测试运行器")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--security", action="store_true", help="只运行安全测试")
    parser.add_argument("--coverage", action="store_true", help="运行覆盖率测试")
    parser.add_argument("--check", action="store_true", help="检查测试结构")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    
    args = parser.parse_args()
    
    # 如果没有指定任何参数，默认运行结构检查
    if not any([args.unit, args.integration, args.security, args.coverage, args.check, args.all]):
        args.check = True
    
    success = True
    
    if args.check:
        success &= check_test_structure()
    
    if args.unit:
        success &= run_unit_tests()
    
    if args.integration:
        success &= run_integration_tests()
    
    if args.security:
        success &= run_security_tests()
    
    if args.coverage:
        success &= run_coverage_tests()
    
    if args.all:
        success &= run_all_tests()
    
    print("\n" + "="*50)
    if success:
        print("✅ 所有测试任务完成")
        sys.exit(0)
    else:
        print("❌ 部分测试任务失败")
        sys.exit(1)


if __name__ == "__main__":
    main() 