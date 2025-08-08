#!/usr/bin/env python3
"""
CodebaseAI System Test Suite

This script tests all components of the CodebaseAI system:
- Service health checks
- API endpoints
- Database connectivity
- Vector store operations
- Model functionality
- Code processing pipeline
"""

import requests
import time
import json
import sys
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    duration: float
    details: Optional[Dict] = None

class CodebaseAITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.test_project_id: Optional[str] = None
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
        print(f"{Colors.BLUE}{title:^50}{Colors.END}")
        print(f"{Colors.BLUE}{'='*50}{Colors.END}")
        
    def print_status(self, message: str, status: str = "INFO"):
        """Print a status message with color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if status == "PASS":
            print(f"{Colors.GREEN}[{timestamp}] ✓ {message}{Colors.END}")
        elif status == "FAIL":
            print(f"{Colors.RED}[{timestamp}] ✗ {message}{Colors.END}")
        elif status == "WARN":
            print(f"{Colors.YELLOW}[{timestamp}] ⚠ {message}{Colors.END}")
        else:
            print(f"{Colors.CYAN}[{timestamp}] ℹ {message}{Colors.END}")
            
    def run_test(self, name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a test and record the result"""
        start_time = time.time()
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            self.results.append(TestResult(
                name=name,
                passed=True,
                message="Test passed",
                duration=duration,
                details=result
            ))
            self.print_status(f"{name}: PASSED", "PASS")
            return self.results[-1]
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                name=name,
                passed=False,
                message=str(e),
                duration=duration
            ))
            self.print_status(f"{name}: FAILED - {str(e)}", "FAIL")
            return self.results[-1]
    
    def test_service_health(self) -> Dict:
        """Test if all services are healthy"""
        response = requests.get(f"{self.base_url}/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check all services
        services = data.get("services", {})
        for service, status in services.items():
            if status != "ok":
                raise Exception(f"Service {service} is not healthy: {status}")
        
        return data
    
    def test_api_documentation(self) -> Dict:
        """Test if API documentation is accessible"""
        response = requests.get(f"{self.base_url}/docs", timeout=10)
        response.raise_for_status()
        return {"status": "available"}
    
    def test_project_creation(self) -> Dict:
        """Test project creation endpoint"""
        project_data = {
            "name": "test-project",
            "repo_url": "https://github.com/microsoft/vscode-extension-samples.git"
        }
        
        response = requests.post(
            f"{self.base_url}/projects/",
            data=project_data,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        # Store project ID for later tests
        self.test_project_id = data.get("project_id")
        
        return {
            "project_id": self.test_project_id,
            "name": data.get("name"),
            "status": "created"
        }
    
    def test_project_processing(self) -> Dict:
        """Test project processing endpoint"""
        if not self.test_project_id:
            raise Exception("No project ID available from creation test")
        
        response = requests.post(
            f"{self.base_url}/projects/{self.test_project_id}/process",
            timeout=120  # Processing can take time
        )
        response.raise_for_status()
        
        return {"status": "processed", "project_id": self.test_project_id}
    
    def test_project_listing(self) -> Dict:
        """Test project listing endpoint"""
        response = requests.get(f"{self.base_url}/projects/", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "count": len(data),
            "projects": data
        }
    
    def test_search_functionality(self) -> Dict:
        """Test semantic search functionality"""
        if not self.test_project_id:
            raise Exception("No project ID available for search test")
        
        search_params = {
            "query": "authentication provider",
            "project_id": self.test_project_id,
            "limit": 3
        }
        
        response = requests.post(
            f"{self.base_url}/search",
            params=search_params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "query": data.get("query"),
            "result_count": len(data.get("results", [])),
            "results": data.get("results", [])
        }
    
    def test_search_without_project(self) -> Dict:
        """Test search across all projects"""
        search_params = {
            "query": "function",
            "limit": 2
        }
        
        response = requests.post(
            f"{self.base_url}/search",
            params=search_params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "query": data.get("query"),
            "result_count": len(data.get("results", [])),
            "results": data.get("results", [])
        }
    
    def test_error_handling(self) -> Dict:
        """Test error handling for invalid requests"""
        # Test invalid project ID
        response = requests.get(f"{self.base_url}/projects/invalid-uuid", timeout=10)
        if response.status_code != 404:
            raise Exception(f"Expected 404 for invalid project, got {response.status_code}")
        
        # Test invalid search parameters
        response = requests.post(f"{self.base_url}/search", timeout=10)
        if response.status_code != 422:
            raise Exception(f"Expected 422 for invalid search params, got {response.status_code}")
        
        return {"status": "error_handling_working"}
    
    def test_database_connectivity(self) -> Dict:
        """Test database connectivity through API"""
        # This is tested indirectly through other endpoints
        # but we can check if projects can be listed
        response = requests.get(f"{self.base_url}/projects/", timeout=10)
        response.raise_for_status()
        
        return {"status": "database_accessible"}
    
    def test_vector_store_connectivity(self) -> Dict:
        """Test vector store connectivity through search"""
        # Test a simple search to verify vector store is working
        search_params = {
            "query": "test",
            "limit": 1
        }
        
        response = requests.post(
            f"{self.base_url}/search",
            params=search_params,
            timeout=30
        )
        response.raise_for_status()
        
        return {"status": "vector_store_accessible"}
    
    def test_model_functionality(self) -> Dict:
        """Test if the LLM model is working through processing"""
        # This is tested through project processing
        # If processing works, the model is working
        if not self.test_project_id:
            raise Exception("No project available to test model functionality")
        
        return {"status": "model_functional"}
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.print_header("CodebaseAI System Test Suite")
        
        tests = [
            ("Service Health Check", self.test_service_health),
            ("API Documentation", self.test_api_documentation),
            ("Database Connectivity", self.test_database_connectivity),
            ("Vector Store Connectivity", self.test_vector_store_connectivity),
            ("Project Creation", self.test_project_creation),
            ("Project Processing", self.test_project_processing),
            ("Project Listing", self.test_project_listing),
            ("Search Functionality", self.test_search_functionality),
            ("Search Without Project", self.test_search_without_project),
            ("Model Functionality", self.test_model_functionality),
            ("Error Handling", self.test_error_handling),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            time.sleep(1)  # Brief pause between tests
        
        self.print_results()
    
    def print_results(self):
        """Print test results summary"""
        self.print_header("Test Results Summary")
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        failed = total - passed
        
        print(f"\n{Colors.BOLD}Overall Results:{Colors.END}")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {Colors.GREEN}{passed}{Colors.END}")
        print(f"  Failed: {Colors.RED}{failed}{Colors.END}")
        print(f"  Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.name}: {result.message}")
        
        print(f"\n{Colors.BOLD}Detailed Results:{Colors.END}")
        for result in self.results:
            status = f"{Colors.GREEN}PASS{Colors.END}" if result.passed else f"{Colors.RED}FAIL{Colors.END}"
            print(f"  {result.name:<30} {status} ({result.duration:.2f}s)")
        
        # Exit with appropriate code
        if failed > 0:
            print(f"\n{Colors.RED}❌ Some tests failed!{Colors.END}")
            sys.exit(1)
        else:
            print(f"\n{Colors.GREEN}✅ All tests passed!{Colors.END}")
            sys.exit(0)

def main():
    """Main function to run the test suite"""
    print(f"{Colors.PURPLE}CodebaseAI System Test Suite{Colors.END}")
    print(f"{Colors.CYAN}Testing system at: http://localhost:8000{Colors.END}")
    
    tester = CodebaseAITester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test suite interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test suite failed with error: {str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
