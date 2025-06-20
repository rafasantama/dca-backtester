"""Comprehensive test runner for the DCA Backtester with CDP AgentKit integration."""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run tests with various options."""
    
    test_commands = {
        "unit": ["python", "-m", "pytest", "tests/services/", "tests/ui/", "-v" if verbose else ""],
        "integration": ["python", "-m", "pytest", "tests/integration/", "-v" if verbose else ""],
        "all": ["python", "-m", "pytest", "tests/", "-v" if verbose else ""],
        "quick": ["python", "-m", "pytest", "tests/", "-x", "--tb=short"]
    }
    
    if coverage:
        test_commands[test_type].extend([
            "--cov=dca_backtester",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Filter out empty strings
    cmd = [arg for arg in test_commands[test_type] if arg]
    
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {test_type.title()} tests passed!")
        else:
            print(f"❌ {test_type.title()} tests failed!")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def check_dependencies():
    """Check if all required test dependencies are installed."""
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Missing test dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run DCA Backtester tests")
    parser.add_argument(
        "test_type", 
        choices=["unit", "integration", "all", "quick"],
        default="all",
        nargs="?",
        help="Type of tests to run"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--check-deps", action="store_true", help="Check test dependencies")
    
    args = parser.parse_args()
    
    if args.check_deps:
        if check_dependencies():
            print("✅ All test dependencies are installed")
        sys.exit(0)
    
    if not check_dependencies():
        print("❌ Missing test dependencies. Use --check-deps to see what's needed.")
        sys.exit(1)
    
    success = run_tests(args.test_type, args.verbose, args.coverage)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()