#!/usr/bin/env python3
"""
Test runner script for Namaskah.App
Provides comprehensive testing with different test suites and reporting
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    print("-" * 50)
    
    result = subprocess.run(command, shell=True, capture_output=False)
    success = result.returncode == 0
    
    if success:
        print(f"✅ {description} - PASSED")
    else:
        print(f"❌ {description} - FAILED")
    
    return success


def main():
    parser = argparse.ArgumentParser(description="Run Namaskah.App tests")
    parser.add_argument("--suite", choices=["all", "unit", "integration", "performance", "security"], 
                       default="all", help="Test suite to run")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    
    args = parser.parse_args()
    
    # Ensure we're in the project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 Namaskah.App Test Runner")
    print("=" * 50)
    print(f"Project root: {project_root}")
    print(f"Test suite: {args.suite}")
    print(f"Coverage: {args.coverage}")
    print(f"Verbose: {args.verbose}")
    
    # Base pytest command
    pytest_cmd = ["pytest"]
    
    # Add verbosity
    if args.verbose:
        pytest_cmd.append("-v")
    else:
        pytest_cmd.append("-q")
    
    # Add parallel execution
    if args.parallel:
        pytest_cmd.extend(["-n", "auto"])
    
    # Add coverage
    if args.coverage:
        pytest_cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
        
        if args.html_report:
            pytest_cmd.extend(["--cov-report=html:htmlcov"])
    
    # Add JUnit XML report
    pytest_cmd.extend(["--junit-xml=test-results/junit.xml"])
    
    # Test suite selection
    if args.suite == "unit":
        pytest_cmd.extend(["-m", "unit"])
    elif args.suite == "integration":
        pytest_cmd.extend(["-m", "integration"])
    elif args.suite == "performance":
        pytest_cmd.extend(["-m", "performance"])
    elif args.suite == "security":
        pytest_cmd.extend(["-m", "security"])
    elif args.suite == "all":
        # Run all tests
        pass
    
    # Skip slow tests if requested
    if args.fast:
        pytest_cmd.extend(["-m", "not slow"])
    
    # Create test results directory
    os.makedirs("test-results", exist_ok=True)
    
    # Run the tests
    success = True
    
    # 1. Code quality checks
    if args.suite in ["all"]:
        print("\n📋 Running Code Quality Checks")
        print("=" * 50)
        
        # Black formatting check
        if not run_command("black --check .", "Black formatting check"):
            success = False
        
        # isort import sorting check
        if not run_command("isort --check-only .", "Import sorting check"):
            success = False
        
        # flake8 linting
        if not run_command("flake8 . --max-line-length=88 --extend-ignore=E203,W503", "Flake8 linting"):
            success = False
        
        # Bandit security check
        if not run_command("bandit -r . -x tests/ -f json -o test-results/bandit-report.json", "Security scan"):
            print("⚠️  Security scan completed with warnings")
    
    # 2. Run pytest
    pytest_command = " ".join(pytest_cmd)
    if not run_command(pytest_command, f"Running {args.suite} tests"):
        success = False
    
    # 3. Generate reports
    print("\n📊 Generating Reports")
    print("=" * 50)
    
    if args.coverage and args.html_report:
        print("📄 Coverage report: htmlcov/index.html")
    
    print("📄 JUnit report: test-results/junit.xml")
    
    if os.path.exists("test-results/bandit-report.json"):
        print("📄 Security report: test-results/bandit-report.json")
    
    # 4. Summary
    print("\n📋 Test Summary")
    print("=" * 50)
    
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()