#!/usr/bin/env python3
"""
Test runner script for DANDI External Resources API
"""

import sys
import subprocess
import os

def run_tests():
    """Run all API tests"""
    print("🧪 Running DANDI External Resources API Tests")
    print("=" * 50)
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Install dev dependencies if needed
    print("📦 Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], 
                   capture_output=True)
    
    # Run unit tests
    print("\n🔬 Running Unit Tests...")
    unit_result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/test_api_endpoints.py", 
        "-v", "--tb=short"
    ])
    
    # Run integration tests
    print("\n🔗 Running Integration Tests...")
    integration_result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/test_api_integration.py", 
        "-v", "--tb=short"
    ])
    
    # Run all tests together for coverage
    print("\n📊 Running All Tests with Coverage...")
    all_result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", "--tb=short",
        "--durations=10"
    ])
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   Unit Tests: {'✅ PASSED' if unit_result.returncode == 0 else '❌ FAILED'}")
    print(f"   Integration Tests: {'✅ PASSED' if integration_result.returncode == 0 else '❌ FAILED'}")
    print(f"   Overall: {'✅ PASSED' if all_result.returncode == 0 else '❌ FAILED'}")
    
    if all_result.returncode == 0:
        print("\n🎉 All tests passed! Your API is ready to use.")
        print("\n📚 Next steps:")
        print("   1. Start the application: python -m src.dandiannotations.webapp.app")
        print("   2. Test API endpoints: curl http://localhost:5000/api/dandisets")
        print("   3. Read API documentation: API_DOCUMENTATION.md")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        return 1
    
    return all_result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
