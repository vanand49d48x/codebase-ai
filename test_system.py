#!/usr/bin/env python3
"""
Test script for the Codebase Ingestion System
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Services: {data['services']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_create_project():
    """Test project creation"""
    print("\n🔍 Testing project creation...")
    try:
        # Create a test project
        data = {
            "name": "test-project",
            "description": "Test project for system verification",
            "repo_url": "https://github.com/octocat/Hello-World.git",
            "language": "python"
        }
        
        response = requests.post(f"{BASE_URL}/projects/", data=data)
        if response.status_code == 200:
            project = response.json()
            print(f"✅ Project created: {project['name']} (ID: {project['project_id']})")
            return project['project_id']
        else:
            print(f"❌ Project creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Project creation error: {str(e)}")
        return None

def test_process_project(project_id):
    """Test project processing"""
    print(f"\n🔍 Testing project processing for {project_id}...")
    try:
        response = requests.post(f"{BASE_URL}/projects/{project_id}/process")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Project processed successfully:")
            print(f"   Total chunks: {result['total_chunks']}")
            print(f"   Processed chunks: {result['processed_chunks']}")
            return True
        else:
            print(f"❌ Project processing failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Project processing error: {str(e)}")
        return False

def test_search(project_id):
    """Test code search"""
    print(f"\n🔍 Testing code search...")
    try:
        data = {
            "query": "hello world function",
            "project_id": project_id,
            "limit": 5
        }
        
        response = requests.post(f"{BASE_URL}/search", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search completed:")
            print(f"   Query: {result['query']}")
            print(f"   Results found: {result['total']}")
            
            if result['results']:
                print("   Top result:")
                top_result = result['results'][0]
                print(f"     Score: {top_result['score']:.3f}")
                print(f"     File: {top_result['payload']['file_path']}")
                print(f"     Function: {top_result['payload'].get('function_name', 'N/A')}")
            
            return True
        else:
            print(f"❌ Search failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return False

def test_list_projects():
    """Test listing projects"""
    print("\n🔍 Testing project listing...")
    try:
        response = requests.get(f"{BASE_URL}/projects/")
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Found {len(projects)} projects:")
            for project in projects:
                print(f"   - {project['name']} ({project['project_id']})")
            return True
        else:
            print(f"❌ Project listing failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Project listing error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Codebase Ingestion System Tests")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ System is not healthy. Please check if all services are running.")
        print("   Run: docker-compose up -d")
        sys.exit(1)
    
    # Test 2: Create project
    project_id = test_create_project()
    if not project_id:
        print("\n❌ Failed to create project. Exiting.")
        sys.exit(1)
    
    # Test 3: Process project (this may take a while)
    print("\n⏳ Processing project (this may take 5-10 minutes)...")
    if not test_process_project(project_id):
        print("\n❌ Failed to process project. Exiting.")
        sys.exit(1)
    
    # Test 4: Search
    if not test_search(project_id):
        print("\n❌ Search test failed.")
    
    # Test 5: List projects
    test_list_projects()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print(f"📊 Project ID: {project_id}")
    print("🌐 API available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
