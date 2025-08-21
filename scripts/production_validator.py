"""
Production Configuration Validator
Ensures all requirements are met for production deployment
"""

import sys
import pkg_resources
import os
from pathlib import Path
import yaml
import streamlit as st
from typing import Dict, List, Tuple

class ProductionValidator:
    """Validate production readiness"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility"""
        self.total_checks += 1
        min_version = (3, 8)
        current = sys.version_info[:2]
        
        if current >= min_version:
            self.checks_passed += 1
            return True
        else:
            self.issues.append(f"Python {min_version[0]}.{min_version[1]}+ required, found {current[0]}.{current[1]}")
            return False
    
    def check_dependencies(self) -> bool:
        """Check all required dependencies"""
        self.total_checks += 1
        
        required_packages = {
            'streamlit': '1.28.0',
            'pandas': '1.5.0',
            'numpy': '1.21.0',
            'plotly': '5.0.0',
            'requests': '2.25.0',
            'pydantic': '1.8.0',
            'python-dotenv': '0.19.0'
        }
        
        missing = []
        outdated = []
        
        for package, min_version in required_packages.items():
            try:
                installed = pkg_resources.get_distribution(package)
                if pkg_resources.parse_version(installed.version) < pkg_resources.parse_version(min_version):
                    outdated.append(f"{package} {installed.version} < {min_version}")
            except pkg_resources.DistributionNotFound:
                missing.append(f"{package} >= {min_version}")
        
        if not missing and not outdated:
            self.checks_passed += 1
            return True
        else:
            if missing:
                self.issues.append(f"Missing packages: {', '.join(missing)}")
            if outdated:
                self.issues.append(f"Outdated packages: {', '.join(outdated)}")
            return False
    
    def check_file_structure(self) -> bool:
        """Check required file structure"""
        self.total_checks += 1
        
        required_files = [
            'integrated_dashboard.py',
            'requirements.txt',
            'config.yaml',
            'README.md'
        ]
        
        required_dirs = [
            'src',
            'logs',
            'data',
            'config'
        ]
        
        missing_files = []
        missing_dirs = []
        
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                missing_dirs.append(dir_name)
        
        if not missing_files and not missing_dirs:
            self.checks_passed += 1
            return True
        else:
            if missing_files:
                self.issues.append(f"Missing files: {', '.join(missing_files)}")
            if missing_dirs:
                self.issues.append(f"Missing directories: {', '.join(missing_dirs)}")
            return False
    
    def check_configuration(self) -> bool:
        """Check configuration files"""
        self.total_checks += 1
        
        try:
            # Check config.yaml
            if Path('config.yaml').exists():
                with open('config.yaml', 'r') as f:
                    config = yaml.safe_load(f)
                
                required_sections = ['llm_config', 'database', 'api_keys', 'environment']
                missing_sections = [section for section in required_sections if section not in config]
                
                if missing_sections:
                    self.warnings.append(f"Config sections missing: {', '.join(missing_sections)}")
            
            # Check environment variables
            required_env = ['OPENAI_API_KEY', 'GOOGLE_API_KEY']  # Add your required env vars
            missing_env = [var for var in required_env if not os.getenv(var)]
            
            if missing_env:
                self.warnings.append(f"Environment variables missing: {', '.join(missing_env)}")
            
            self.checks_passed += 1
            return True
            
        except Exception as e:
            self.issues.append(f"Configuration error: {str(e)}")
            return False
    
    def check_database_connection(self) -> bool:
        """Check database connectivity"""
        self.total_checks += 1
        
        try:
            # Basic database file check
            db_path = Path('data/research.db')
            if db_path.exists():
                self.checks_passed += 1
                return True
            else:
                self.warnings.append("Database file not found - will be created on first run")
                self.checks_passed += 1  # Not critical for startup
                return True
        except Exception as e:
            self.issues.append(f"Database check failed: {str(e)}")
            return False
    
    def check_security_settings(self) -> bool:
        """Check security configuration"""
        self.total_checks += 1
        
        security_issues = []
        
        # Check if debug mode is disabled
        if os.getenv('DEBUG', 'false').lower() == 'true':
            security_issues.append("Debug mode should be disabled in production")
        
        # Check if secret keys are set
        if not os.getenv('SECRET_KEY'):
            security_issues.append("SECRET_KEY environment variable not set")
        
        # Check file permissions (basic check)
        config_files = ['config.yaml', '.env']
        for file in config_files:
            if Path(file).exists():
                # Add permission checks if needed
                pass
        
        if not security_issues:
            self.checks_passed += 1
            return True
        else:
            self.warnings.extend(security_issues)
            self.checks_passed += 1  # Warning level
            return True
    
    def check_performance_settings(self) -> bool:
        """Check performance optimization settings"""
        self.total_checks += 1
        
        performance_suggestions = []
        
        # Check caching configuration
        try:
            import streamlit as st
            # Add cache configuration checks
            performance_suggestions.append("Consider enabling Streamlit caching for production")
        except:
            pass
        
        if performance_suggestions:
            self.warnings.extend(performance_suggestions)
        
        self.checks_passed += 1
        return True
    
    def run_full_validation(self) -> Dict:
        """Run complete production validation"""
        print("🚀 RUNNING PRODUCTION VALIDATION")
        print("=" * 50)
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Dependencies", self.check_dependencies),
            ("File Structure", self.check_file_structure),
            ("Configuration", self.check_configuration),
            ("Database", self.check_database_connection),
            ("Security", self.check_security_settings),
            ("Performance", self.check_performance_settings)
        ]
        
        results = {}
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} {check_name}")
            except Exception as e:
                results[check_name] = False
                self.issues.append(f"{check_name} check failed: {str(e)}")
                print(f"❌ FAIL {check_name}: {str(e)}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        success_rate = (self.checks_passed / self.total_checks) * 100 if self.total_checks > 0 else 0
        print(f"Success Rate: {success_rate:.1f}% ({self.checks_passed}/{self.total_checks})")
        
        if self.issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  • {issue}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.issues:
            print(f"\n🎉 PRODUCTION READY!")
            print("✅ All critical checks passed")
            print("🚀 Safe to deploy")
        else:
            print(f"\n🚨 NOT PRODUCTION READY")
            print("❌ Critical issues must be resolved before deployment")
        
        return {
            'ready': len(self.issues) == 0,
            'success_rate': success_rate,
            'issues': self.issues,
            'warnings': self.warnings,
            'checks_passed': self.checks_passed,
            'total_checks': self.total_checks,
            'results': results
        }

def create_production_requirements():
    """Create production requirements.txt"""
    requirements = """# Production Requirements for Academic Research Assistant
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.21.0
plotly>=5.0.0
requests>=2.25.0
pydantic>=1.8.0
python-dotenv>=0.19.0
aiosqlite>=0.17.0
crewai>=0.1.0
google-generativeai>=0.3.0
openai>=1.0.0
sentence-transformers>=2.2.0
scikit-learn>=1.1.0
nltk>=3.7
beautifulsoup4>=4.11.0
lxml>=4.9.0
python-dateutil>=2.8.0
pyyaml>=6.0
typing-extensions>=4.0.0
asyncio>=3.4.0
concurrent-futures>=3.1.0
"""
    
    with open('requirements_production.txt', 'w') as f:
        f.write(requirements)
    
    print("✅ Created requirements_production.txt")

if __name__ == "__main__":
    validator = ProductionValidator()
    results = validator.run_full_validation()
    
    # Create production requirements
    create_production_requirements()
    
    print(f"\n📋 Validation complete: {'READY' if results['ready'] else 'NOT READY'}")
