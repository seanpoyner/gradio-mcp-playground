#!/usr/bin/env python3
"""Master Test Runner for Gradio MCP Playground

This script runs all test suites and provides a comprehensive test report.
Use this to validate the entire system before release.
"""

import sys
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List

def run_test_suite(script_path: Path, name: str) -> Dict[str, Any]:
    """Run a test suite and return results"""
    print(f"\n{'='*60}")
    print(f"🚀 Running {name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        return {
            "name": name,
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "success": False,
            "error": "Test suite timed out (5 minutes)",
            "duration": time.time() - start_time
        }
    except Exception as e:
        return {
            "name": name,
            "success": False,
            "error": f"Failed to run test suite: {str(e)}",
            "duration": time.time() - start_time
        }

def print_summary(results: List[Dict[str, Any]]):
    """Print a comprehensive test summary"""
    print(f"\n{'='*60}")
    print("🎯 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    
    total_duration = sum(r.get("duration", 0) for r in results)
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"  ✅ Passed: {passed_tests}/{total_tests}")
    print(f"  ❌ Failed: {failed_tests}/{total_tests}")
    print(f"  ⏱️ Total Duration: {total_duration:.1f}s")
    print(f"  📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        duration = result.get("duration", 0)
        print(f"  {status} {result['name']} ({duration:.1f}s)")
        
        if not result["success"]:
            error = result.get("error", "Unknown error")
            print(f"    💥 Error: {error}")
            
            if "stderr" in result and result["stderr"]:
                print(f"    📝 Error Details:")
                for line in result["stderr"].split('\n')[:5]:  # Show first 5 lines
                    if line.strip():
                        print(f"      {line.strip()}")
    
    if failed_tests > 0:
        print(f"\n🔍 DEBUGGING TIPS:")
        print(f"  1. Check individual test outputs above")
        print(f"  2. Run failed tests individually for detailed output")
        print(f"  3. Check the QA/QC checklist: QA_QC_CHECKLIST.md")
        print(f"  4. Use the test notebook for manual debugging: test_notebook.ipynb")
        print(f"  5. Ensure all dependencies are installed: pip install -e .[dev,all]")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! The system is ready for release.")
        print(f"\n📋 NEXT STEPS:")
        print(f"  1. Review QA/QC checklist manually")
        print(f"  2. Test deployment in staging environment")
        print(f"  3. Update documentation if needed")
        print(f"  4. Create release notes")
    else:
        print(f"\n⚠️ SOME TESTS FAILED. Please fix issues before release.")
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print(f"  1. Fix failing tests")
        print(f"  2. Run tests again to verify fixes")
        print(f"  3. Check code quality with: black . && ruff check . && mypy .")
        print(f"  4. Review error logs carefully")

def main():
    """Main test runner function"""
    print("🚀 GRADIO MCP PLAYGROUND - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("This will run all available test suites to validate the system.")
    print()
    
    # Define test suites
    test_dir = Path(__file__).parent / "tests"
    test_suites = [
        {
            "script": test_dir / "test_cli_comprehensive.py",
            "name": "CLI Comprehensive Tests"
        },
        {
            "script": test_dir / "test_mcp_functionality.py", 
            "name": "MCP Functionality Tests"
        },
        {
            "script": test_dir / "test_basic.py",
            "name": "Basic Unit Tests"
        }
    ]
    
    # Check if test files exist
    available_suites = []
    for suite in test_suites:
        if suite["script"].exists():
            available_suites.append(suite)
        else:
            print(f"⚠️ Test suite not found: {suite['script']}")
    
    if not available_suites:
        print("❌ No test suites found! Please ensure test files exist.")
        return 1
    
    print(f"📋 Found {len(available_suites)} test suites:")
    for suite in available_suites:
        print(f"  📄 {suite['name']}")
    
    print(f"\n⏱️ Starting test execution...")
    start_time = time.time()
    
    # Run all test suites
    results = []
    for suite in available_suites:
        result = run_test_suite(suite["script"], suite["name"])
        results.append(result)
        
        # Print immediate feedback
        if result["success"]:
            print(f"✅ {suite['name']} completed successfully")
        else:
            print(f"❌ {suite['name']} failed")
    
    total_duration = time.time() - start_time
    
    # Print comprehensive summary
    print_summary(results)
    
    print(f"\n⏱️ Total execution time: {total_duration:.1f}s")
    print(f"📅 Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return appropriate exit code
    failed_count = sum(1 for r in results if not r["success"])
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)