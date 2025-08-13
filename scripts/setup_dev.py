#!/usr/bin/env python3
"""
Development Environment Setup Script

This script helps set up a development environment with proper tooling.
"""

import subprocess
import sys
from pathlib import Path

def run_command(command: str, description: str):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def setup_dev_environment():
    """Set up development environment."""
    print("🚀 Setting up development environment for Academic Research Assistant\n")
    
    # Install development dependencies
    dev_packages = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0", 
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
        "pre-commit>=3.0.0",
    ]
    
    print("📦 Installing development dependencies...")
    for package in dev_packages:
        run_command(f"pip install {package}", f"Installing {package}")
    
    # Set up pre-commit hooks
    if Path(".git").exists():
        print("\n🪝 Setting up pre-commit hooks...")
        
        # Create pre-commit config
        precommit_config = """repos:
-   repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
    -   id: black
        language_version: python3.12

-   repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
    -   id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
    -   id: mypy
        additional_dependencies: [types-all]

-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
"""
        
        with open(".pre-commit-config.yaml", "w") as f:
            f.write(precommit_config)
            
        run_command("pre-commit install", "Installing pre-commit hooks")
    
    # Create development scripts
    print("\n📜 Creating development scripts...")
    
    # Test runner script
    test_script = """#!/usr/bin/env python3
import subprocess
import sys

def run_tests():
    print("🧪 Running test suite...")
    result = subprocess.run(["python", "-m", "pytest", "tests/", "-v", "--cov=src"], 
                          capture_output=False)
    return result.returncode == 0

def run_linting():
    print("🔍 Running code quality checks...")
    
    # Black formatting check
    black_result = subprocess.run(["black", "--check", "src/", "tests/"], 
                                capture_output=True, text=True)
    if black_result.returncode != 0:
        print("❌ Code formatting issues found. Run 'black src/ tests/' to fix.")
        return False
    
    # Flake8 linting
    flake8_result = subprocess.run(["flake8", "src/", "tests/"], 
                                 capture_output=True, text=True)
    if flake8_result.returncode != 0:
        print(f"❌ Linting issues found:\\n{flake8_result.stdout}")
        return False
    
    print("✅ Code quality checks passed!")
    return True

if __name__ == "__main__":
    print("🚀 Running development checks...")
    
    tests_passed = run_tests()
    linting_passed = run_linting()
    
    if tests_passed and linting_passed:
        print("✅ All checks passed!")
        sys.exit(0)
    else:
        print("❌ Some checks failed!")
        sys.exit(1)
"""
    
    with open("scripts/dev_check.py", "w") as f:
        f.write(test_script)
    
    print("\n✅ Development environment setup complete!")
    print("\nUseful commands:")
    print("  python scripts/dev_check.py     - Run tests and linting")
    print("  python scripts/organize_project.py - Check project organization")
    print("  black src/ tests/               - Format code")
    print("  pytest tests/ -v                - Run tests")
    print("  pre-commit run --all-files      - Run pre-commit hooks")

if __name__ == "__main__":
    setup_dev_environment()
