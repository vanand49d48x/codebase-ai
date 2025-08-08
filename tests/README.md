# CodebaseAI Test Suite

This directory contains comprehensive tests for the CodebaseAI system.

## Test Files

- `test_system.py` - Main test suite that validates all system components
- `run_tests.sh` - Test runner script with pre-checks

## Running Tests

### Option 1: Using the test runner (Recommended)
```bash
./tests/run_tests.sh
```

### Option 2: Direct Python execution
```bash
python3 tests/test_system.py
```

### Option 3: Using the main start script
```bash
./start.sh test
```

## Test Coverage

The test suite validates:

### ✅ Service Health
- Backend API responsiveness
- All service dependencies (PostgreSQL, Qdrant, Ollama)
- Health endpoint functionality

### ✅ API Endpoints
- Project creation and listing
- Project processing pipeline
- Semantic search functionality
- Error handling for invalid requests

### ✅ Database Connectivity
- PostgreSQL connection and operations
- Vector store (Qdrant) connectivity
- Data persistence and retrieval

### ✅ Model Functionality
- LLM model availability and operation
- Code summarization capabilities
- Embedding generation

### ✅ Code Processing Pipeline
- Repository ingestion
- Code chunking
- Summary generation
- Vector embedding creation

## Test Results

The test suite provides:
- ✅/❌ Pass/Fail status for each test
- Execution time for each test
- Detailed error messages for failures
- Overall success rate
- Color-coded output for easy reading

## Prerequisites

Before running tests:
1. System must be running (`./start.sh start`)
2. Python 3 must be installed
3. `requests` module must be available (auto-installed if missing)

## Example Output

```
==================================================
CodebaseAI System Test Suite
==================================================

[14:30:15] ℹ Service Health Check: PASSED
[14:30:16] ℹ API Documentation: PASSED
[14:30:17] ℹ Database Connectivity: PASSED
[14:30:18] ℹ Vector Store Connectivity: PASSED
[14:30:19] ℹ Project Creation: PASSED
[14:30:45] ℹ Project Processing: PASSED
[14:30:46] ℹ Project Listing: PASSED
[14:30:47] ℹ Search Functionality: PASSED
[14:30:48] ℹ Search Without Project: PASSED
[14:30:49] ℹ Model Functionality: PASSED
[14:30:50] ℹ Error Handling: PASSED

==================================================
Test Results Summary
==================================================

Overall Results:
  Total Tests: 11
  Passed: 11
  Failed: 0
  Success Rate: 100.0%

✅ All tests passed!
```
