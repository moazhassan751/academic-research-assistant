# Test Files

This folder contains all test files for the Academic Research Assistant project.

## Test Files Overview

### Core Component Tests
- `test_database.py` - Database functionality tests
- `test_async_api_manager.py` - API manager tests
- `test_literature_survey.py` - Literature survey agent tests
- `test_validators.py` - Input validation tests
- `test_error_handler.py` - Error handling tests
- `test_enhanced_config.py` - Configuration tests

### Q&A Feature Tests
- `test_qa_feature.py` - Main Q&A functionality tests
- `test_validator_errors.py` - Q&A validation error tests
- `test_fixes.py` - Bug fix verification tests

### Integration & Workflow Tests
- `complete_workflow_test.py` - End-to-end workflow tests
- `comprehensive_test.py` - Comprehensive system tests

### Debug & Development Tools
- `debug_test.py` - Debug utilities and tests
- `debug_qa.py` - Q&A debugging tools
- `demo_qa_feature.py` - Q&A feature demonstrations

### API & External Service Tests  
- `Open_Alex_test.py` - OpenAlex API integration tests
- `quick_test.py` - Quick functionality tests

### Configuration
- `conftest.py` - pytest configuration and fixtures

## Running Tests

To run all tests:
```bash
pytest tests/
```

To run specific test files:
```bash
pytest tests/test_qa_feature.py
pytest tests/complete_workflow_test.py
```

To run tests with verbose output:
```bash
pytest tests/ -v
```
