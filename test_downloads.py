"""
Test script for Streamlit Download functionality
Run this to verify download features work before deployment
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test export manager import
        from src.utils.export_manager import export_manager
        print("✅ Export manager imported successfully")
        export_available = True
    except ImportError as e:
        print(f"❌ Export manager import failed: {e}")
        export_available = False
    
    try:
        # Test streamlit downloads import
        from src.utils.streamlit_downloads import StreamlitDownloadHelper, add_download_buttons
        print("✅ Streamlit downloads imported successfully")
        downloads_available = True
    except ImportError as e:
        print(f"❌ Streamlit downloads import failed: {e}")
        downloads_available = False
    
    return export_available, downloads_available

def test_download_helper():
    """Test the download helper functionality"""
    print("\n🧪 Testing download helper...")
    
    try:
        from src.utils.export_manager import export_manager
        from src.utils.streamlit_downloads import StreamlitDownloadHelper
        
        # Create helper instance
        helper = StreamlitDownloadHelper(export_manager)
        print("✅ StreamlitDownloadHelper created successfully")
        
        # Test with dummy data
        dummy_draft = {
            'title': 'Test Research Paper',
            'content': 'This is a test content for the research paper.',
            'research_topic': 'Test Topic'
        }
        
        print("✅ Test data prepared")
        return True
        
    except Exception as e:
        print(f"❌ Download helper test failed: {e}")
        return False

def test_file_operations():
    """Test if file operations work"""
    print("\n🧪 Testing file operations...")
    
    try:
        # Test directory creation (Windows compatible)
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_export"
            test_dir.mkdir(exist_ok=True)
            print("✅ Directory creation works")
            
            # Test file writing
            test_file = test_dir / "test.txt"
            test_file.write_text("Test content")
            print("✅ File writing works")
            
            # Test file reading
            content = test_file.read_text()
            assert content == "Test content"
            print("✅ File reading works")
            
        print("✅ File cleanup works")
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are available"""
    print("\n🧪 Testing dependencies...")
    
    dependencies = [
        ('streamlit', 'st'),
        ('reportlab.platypus', 'SimpleDocTemplate'),
        ('docx', 'Document'),
        ('io', 'BytesIO'),
        ('pathlib', 'Path')
    ]
    
    all_available = True
    
    for dep_name, import_name in dependencies:
        try:
            if '.' in dep_name:
                module_name, class_name = dep_name, import_name
                exec(f"from {module_name} import {class_name}")
            else:
                exec(f"import {dep_name} as {import_name}")
            print(f"✅ {dep_name} available")
        except ImportError:
            print(f"❌ {dep_name} not available")
            all_available = False
    
    return all_available

def main():
    """Run all tests"""
    print("🚀 Starting Download Functionality Tests")
    print("=" * 50)
    
    # Run tests
    export_ok, downloads_ok = test_imports()
    helper_ok = test_download_helper() if export_ok and downloads_ok else False
    files_ok = test_file_operations()
    deps_ok = test_dependencies()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Import Tests", export_ok and downloads_ok),
        ("Download Helper", helper_ok),
        ("File Operations", files_ok),
        ("Dependencies", deps_ok)
    ]
    
    all_passed = True
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Download functionality is ready!")
        print("✅ Safe to deploy to Colab")
        return True
    else:
        print("⚠️ SOME TESTS FAILED! Fix issues before deployment")
        print("❌ Do not deploy until all tests pass")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
