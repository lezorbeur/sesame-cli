#!/usr/bin/env python3
"""
Sesame CLI validation script — run all tests in one process
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, '/workspaces/sesame')

from cmd.cli import main

def run_test(name, cmd_args):
    """Run a single CLI command and return success status"""
    try:
        result = main(cmd_args)
        if result == 0:
            print(f"  ✓ {name}")
            return True
        else:
            print(f"  ✗ {name} (exit code: {result})")
            return False
    except Exception as e:
        print(f"  ✗ {name} ({e})")
        return False

def main_test():
    """Run all validation tests"""
    print("=== Sesame CLI Validation ===\n")
    
    # Create temp dir for test files
    tmpdir = tempfile.mkdtemp(prefix='sesame_validation_')
    os.chdir(tmpdir)
    print(f"Working directory: {tmpdir}\n")
    
    passed = 0
    failed = 0
    
    # Test 1: build
    if run_test("build", ["build", "--nx", "100", "--out", "sys.gzip"]):
        passed += 1
    else:
        failed += 1
        print("Build failed; aborting tests")
        shutil.rmtree(tmpdir)
        return False
    
    # Test 2: load
    if run_test("load", ["load", "sys.gzip"]):
        passed += 1
    else:
        failed += 1
    
    # Test 3: ivcurve (main workflow)
    if run_test("ivcurve", ["ivcurve", "--nx", "100", "--npoints", "3", "--out", "iv_test"]):
        passed += 1
    else:
        failed += 1
    
    # Test 4: analyze
    if run_test("analyze", ["analyze", "iv_test_0.gzip", "--current"]):
        passed += 1
    else:
        failed += 1
    
    # Test 5: plot
    if run_test("plot", ["plot", "iv_test_0.gzip", "--what", "v", "--out", "plot.png"]):
        passed += 1
    else:
        failed += 1
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    # Cleanup
    os.chdir("/")
    shutil.rmtree(tmpdir)
    
    if failed == 0:
        print("\n✓ All tests passed!")
        return True
    else:
        print(f"\n✗ {failed} test(s) failed")
        return False

if __name__ == '__main__':
    success = main_test()
    sys.exit(0 if success else 1)
