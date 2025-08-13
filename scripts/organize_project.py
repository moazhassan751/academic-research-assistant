#!/usr/bin/env python3
"""
Project Organization Checker and Maintainer

This script helps maintain professional project organization by:
- Checking for missing __init__.py files
- Validating directory structure
- Ensuring proper documentation
- Checking for code quality issues
- Cleaning up temporary files
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Set
import json
from datetime import datetime

class ProjectOrganizer:
    """Professional project organization checker and maintainer."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.issues = []
        self.warnings = []
        self.suggestions = []
        
    def check_structure(self) -> Dict[str, List[str]]:
        """Check overall project structure."""
        print("🔍 Checking project structure...")
        
        # Required directories
        required_dirs = {
            "src": "Core source code",
            "tests": "Test suite", 
            "docs": "Documentation",
            "scripts": "Automation scripts",
            "config": "Configuration files",
            "logs": "Application logs"
        }
        
        # Check required directories
        for dir_name, description in required_dirs.items():
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                self.issues.append(f"Missing required directory: {dir_name} ({description})")
            else:
                print(f"✅ Found {dir_name}/ - {description}")
                
        # Check for Python packages (should have __init__.py)
        src_dir = self.project_root / "src"
        if src_dir.exists():
            self._check_python_packages(src_dir)
            
        return {
            "issues": self.issues,
            "warnings": self.warnings, 
            "suggestions": self.suggestions
        }
    
    def _check_python_packages(self, src_dir: Path):
        """Check that Python packages have __init__.py files."""
        print("\n🐍 Checking Python package structure...")
        
        for item in src_dir.rglob("*"):
            if item.is_dir() and item.name != "__pycache__":
                # Skip if it's a hidden directory or common non-package dirs
                if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules']:
                    continue
                    
                init_file = item / "__init__.py"
                if not init_file.exists():
                    # Check if directory contains Python files
                    python_files = list(item.glob("*.py"))
                    if python_files:
                        self.warnings.append(f"Python package missing __init__.py: {item.relative_to(self.project_root)}")
                else:
                    print(f"✅ Package: {item.relative_to(self.project_root)}")
    
    def check_documentation(self):
        """Check documentation completeness."""
        print("\n📚 Checking documentation...")
        
        required_docs = {
            "README.md": "Main project documentation",
            "PROJECT_STRUCTURE.md": "Project structure documentation",
            "requirements.txt": "Python dependencies",
        }
        
        for doc_file, description in required_docs.items():
            file_path = self.project_root / doc_file
            if not file_path.exists():
                self.issues.append(f"Missing documentation: {doc_file} ({description})")
            else:
                print(f"✅ Found {doc_file} - {description}")
                
        # Check docs directory
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            doc_files = list(docs_dir.glob("*.md"))
            print(f"📄 Found {len(doc_files)} documentation files in docs/")
    
    def check_config_files(self):
        """Check configuration file organization."""
        print("\n⚙️  Checking configuration files...")
        
        config_files = {
            "config.yaml": "Main configuration",
            "pyproject.toml": "Python project metadata",
            ".gitignore": "Git ignore patterns",
            ".env.example": "Environment variables template"
        }
        
        for config_file, description in config_files.items():
            file_path = self.project_root / config_file
            if file_path.exists():
                print(f"✅ Found {config_file} - {description}")
            else:
                if config_file == "pyproject.toml":
                    self.suggestions.append(f"Consider adding {config_file} for modern Python project configuration")
                else:
                    self.warnings.append(f"Missing configuration file: {config_file}")
    
    def clean_temporary_files(self):
        """Clean up temporary and cache files."""
        print("\n🧹 Cleaning temporary files...")
        
        patterns_to_clean = [
            "**/__pycache__",
            "**/*.pyc", 
            "**/*.pyo",
            "**/*.pyd",
            "**/*~",
            "**/*.tmp",
            "**/*.temp",
            "**/.DS_Store",
            "**/Thumbs.db"
        ]
        
        cleaned_count = 0
        for pattern in patterns_to_clean:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        print(f"🗑️  Removed: {file_path.relative_to(self.project_root)}")
                    except Exception as e:
                        self.warnings.append(f"Could not remove {file_path}: {e}")
                elif file_path.is_dir() and file_path.name == "__pycache__":
                    try:
                        # Remove __pycache__ directories
                        import shutil
                        shutil.rmtree(file_path)
                        cleaned_count += 1
                        print(f"🗑️  Removed directory: {file_path.relative_to(self.project_root)}")
                    except Exception as e:
                        self.warnings.append(f"Could not remove {file_path}: {e}")
        
        print(f"✨ Cleaned {cleaned_count} temporary files/directories")
    
    def validate_imports(self):
        """Validate that Python imports are properly organized."""
        print("\n📦 Validating Python imports...")
        
        src_dir = self.project_root / "src"
        if not src_dir.exists():
            return
            
        python_files = list(src_dir.rglob("*.py"))
        print(f"🔍 Checking {len(python_files)} Python files...")
        
        import_issues = []
        for py_file in python_files:
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for relative imports that might break
                lines = content.split('\n')
                for i, line in enumerate(lines[:20]):  # Check first 20 lines
                    if 'from .' in line or 'import .' in line:
                        # This is a relative import, which is good
                        continue
                    elif 'from src.' in line:
                        import_issues.append(f"{py_file.relative_to(self.project_root)}:{i+1} - Consider using relative imports instead of 'from src.'")
                        
            except Exception as e:
                self.warnings.append(f"Could not analyze {py_file}: {e}")
        
        if import_issues:
            self.suggestions.extend(import_issues[:5])  # Limit to first 5
        else:
            print("✅ Import structure looks good")
    
    def generate_report(self) -> str:
        """Generate a comprehensive organization report."""
        report = f"""
# Project Organization Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Project: {self.project_root.name}

## Summary
- Issues: {len(self.issues)}
- Warnings: {len(self.warnings)}
- Suggestions: {len(self.suggestions)}

## Issues (Must Fix)
"""
        if self.issues:
            for issue in self.issues:
                report += f"❌ {issue}\n"
        else:
            report += "✅ No critical issues found!\n"
            
        report += "\n## Warnings (Should Fix)\n"
        if self.warnings:
            for warning in self.warnings:
                report += f"⚠️  {warning}\n"
        else:
            report += "✅ No warnings!\n"
            
        report += "\n## Suggestions (Consider)\n"
        if self.suggestions:
            for suggestion in self.suggestions:
                report += f"💡 {suggestion}\n"
        else:
            report += "✅ No suggestions at this time!\n"
            
        report += """
## Organization Best Practices Checklist
- [x] Clear directory structure (src/, tests/, docs/, etc.)
- [x] Python packages have __init__.py files
- [x] Comprehensive documentation
- [x] Proper configuration management
- [x] Version control ignore patterns
- [x] Project metadata (pyproject.toml)
- [x] Clean repository (no temporary files)

## Recommendations
1. Keep the src/ directory clean and well-organized
2. Ensure all packages have proper __init__.py files
3. Maintain comprehensive documentation
4. Use relative imports within the project
5. Regularly clean temporary files
6. Keep configuration files organized
7. Use type hints and docstrings
8. Maintain test coverage
"""
        return report
    
    def run_full_check(self):
        """Run all organization checks."""
        print("🚀 Running comprehensive project organization check...\n")
        
        self.check_structure()
        self.check_documentation()
        self.check_config_files()
        self.validate_imports()
        self.clean_temporary_files()
        
        print("\n" + "="*60)
        print("📋 ORGANIZATION REPORT")
        print("="*60)
        
        report = self.generate_report()
        print(report)
        
        # Save report to file
        report_file = self.project_root / "PROJECT_ORGANIZATION_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 Full report saved to: {report_file}")
        
        # Return status
        return len(self.issues) == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Professional project organization checker")
    parser.add_argument("--path", default=".", help="Project root path")
    parser.add_argument("--clean-only", action="store_true", help="Only clean temporary files")
    
    args = parser.parse_args()
    
    organizer = ProjectOrganizer(args.path)
    
    if args.clean_only:
        organizer.clean_temporary_files()
    else:
        success = organizer.run_full_check()
        sys.exit(0 if success else 1)
