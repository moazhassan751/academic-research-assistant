# Test Suite

This directory contains the essential test files for the Academic Research Assistant project.

## Core Test Files

### Configuration & Setup
- `conftest.py` - PyTest configuration and fixtures for all tests

### API Integration Tests  
- `Open_Alex_test.py` - OpenAlex API integration tests and validation

### Performance & Benchmarking
- `performance_test.py` - Comprehensive performance testing and benchmarking

## Test Structure

### Integration Tests (`integration/`)
- End-to-end workflow tests
- Component integration tests

### Unit Tests (`unit/`)
- Individual component tests
- Function-level testing

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/Open_Alex_test.py

# Run performance tests
python tests/performance_test.py

# Run with verbose output
pytest -v
```

## Test Quality Standards

This test suite maintains high quality by:
- ✅ **Focused scope** - Each test has a clear purpose
- ✅ **Proper fixtures** - Reusable test data and mocks
- ✅ **Performance validation** - Tests include speed benchmarks
- ✅ **Integration coverage** - Tests real API interactions
- ✅ **Documentation** - Clear test descriptions and usage
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
