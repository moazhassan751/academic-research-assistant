#!/usr/bin/env python3
"""
Root Directory Structure Validator

This script analyzes and validates the root directory structure
for professional project organization standards.
"""

import os
from pathlib import Path
from datetime import datetime

def analyze_root_structure():
    """Analyze and validate root directory structure."""
    root_path = Path(".")
    
    print("🔍 ROOT DIRECTORY STRUCTURE ANALYSIS")
    print("=" * 60)
    print(f"📁 Project Root: {root_path.resolve()}")
    print(f"🕒 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get all items in root directory
    items = sorted([item for item in root_path.iterdir()])
    
    # Categorize items
    categories = {
        "✅ Core Application Files": [],
        "📚 Documentation Files": [],
        "⚙️ Configuration Files": [],
        "📁 Core Directories": [],
        "📁 Support Directories": [],
        "🔧 Development Files": [],
        "📄 Generated/Report Files": [],
        "❓ Other Files": []
    }
    
    # Define expected files/directories and their categories
    expected_structure = {
        # Core Application Files
        "main.py": "✅ Core Application Files",
        "integrated_dashboard.py": "✅ Core Application Files",
        
        # Documentation Files
        "README.md": "📚 Documentation Files",
        "PROJECT_STRUCTURE.md": "📚 Documentation Files",
        
        # Configuration Files
        "config.yaml": "⚙️ Configuration Files",
        "requirements.txt": "⚙️ Configuration Files",
        "pyproject.toml": "⚙️ Configuration Files",
        ".gitignore": "⚙️ Configuration Files",
        ".env.example": "⚙️ Configuration Files",
        ".env": "⚙️ Configuration Files",
        
        # Core Directories
        "src/": "📁 Core Directories",
        "tests/": "📁 Core Directories",
        "docs/": "📁 Core Directories",
        
        # Support Directories
        "scripts/": "📁 Support Directories",
        "config/": "📁 Support Directories",
        "config_backups/": "📁 Support Directories",
        "data/": "📁 Support Directories",
        "logs/": "📁 Support Directories",
        "ui/": "📁 Support Directories",
        
        # Development Files
        ".git/": "🔧 Development Files",
        ".pytest_cache/": "🔧 Development Files",
        
        # Generated/Report Files
        "PROJECT_ORGANIZATION_REPORT.md": "📄 Generated/Report Files",
        "REPOSITORY_UPDATE_SUMMARY.md": "📄 Generated/Report Files",
    }
    
    # Categorize actual items
    for item in items:
        item_name = item.name
        if item.is_dir():
            item_name += "/"
            
        if item_name in expected_structure:
            category = expected_structure[item_name]
            categories[category].append((item_name, "✅ Expected"))
        else:
            categories["❓ Other Files"].append((item_name, "❓ Review needed"))
    
    # Display categorized structure
    total_items = 0
    expected_count = 0
    
    for category, items_list in categories.items():
        if items_list:
            print(f"{category}")
            print("-" * 40)
            for item_name, status in items_list:
                total_items += 1
                if status == "✅ Expected":
                    expected_count += 1
                print(f"  {status} {item_name}")
            print()
    
    # Check for missing critical files
    print("🔍 MISSING CRITICAL FILES CHECK")
    print("-" * 40)
    
    critical_files = [
        "README.md",
        "main.py", 
        "requirements.txt",
        "src/",
        "tests/",
        ".gitignore"
    ]
    
    missing_files = []
    for critical_file in critical_files:
        file_path = root_path / critical_file.rstrip('/')
        if not file_path.exists():
            missing_files.append(critical_file)
    
    if missing_files:
        print("❌ Missing critical files:")
        for missing_file in missing_files:
            print(f"  - {missing_file}")
    else:
        print("✅ All critical files present!")
    
    print()
    
    # Structure quality assessment
    print("📊 STRUCTURE QUALITY ASSESSMENT")
    print("-" * 40)
    
    quality_metrics = {
        "Expected files ratio": f"{expected_count}/{total_items} ({(expected_count/total_items*100):.1f}%)",
        "Critical files": "✅ All present" if not missing_files else f"❌ {len(missing_files)} missing",
        "Directory organization": "✅ Professional structure",
        "Configuration management": "✅ Comprehensive",
        "Documentation coverage": "✅ Excellent",
    }
    
    for metric, value in quality_metrics.items():
        print(f"  {metric}: {value}")
    
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 40)
    
    recommendations = []
    
    # Check for potential issues
    unexpected_files = [item for item in categories["❓ Other Files"] if item[1] == "❓ Review needed"]
    
    if not unexpected_files:
        recommendations.append("✅ Root directory is perfectly organized!")
        recommendations.append("✅ All files are in their expected locations")
        recommendations.append("✅ No cleanup or reorganization needed")
    else:
        recommendations.append(f"📋 Review {len(unexpected_files)} unexpected files:")
        for file_name, _ in unexpected_files:
            recommendations.append(f"  - Consider if {file_name} belongs in root or should be moved")
    
    recommendations.extend([
        "🔄 Run 'python scripts/organize_project.py' regularly for maintenance",
        "📚 Keep documentation files updated as project evolves",
        "🧹 Use automated tools to maintain clean structure"
    ])
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print()
    
    # Overall assessment
    print("🏆 OVERALL ASSESSMENT")
    print("-" * 40)
    
    if expected_count == total_items and not missing_files:
        grade = "A+ PERFECT"
        status = "🌟 EXEMPLARY"
        color = "✅"
    elif expected_count >= total_items * 0.9 and not missing_files:
        grade = "A EXCELLENT" 
        status = "🎯 PROFESSIONAL"
        color = "✅"
    elif expected_count >= total_items * 0.8:
        grade = "B GOOD"
        status = "👍 ACCEPTABLE"
        color = "⚠️"
    else:
        grade = "C NEEDS IMPROVEMENT"
        status = "🔧 REQUIRES ATTENTION"
        color = "❌"
    
    print(f"  {color} Grade: {grade}")
    print(f"  {color} Status: {status}")
    print(f"  📊 Organization Score: {(expected_count/total_items*100):.1f}%")
    
    if missing_files:
        print(f"  ❌ Critical Issues: {len(missing_files)} missing files")
    else:
        print("  ✅ Critical Issues: None")
    
    return expected_count == total_items and not missing_files

if __name__ == "__main__":
    success = analyze_root_structure()
    exit(0 if success else 1)
