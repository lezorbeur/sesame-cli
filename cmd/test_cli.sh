#!/usr/bin/env bash
# Quick smoke test of key CLI commands
# Run: bash test_cli.sh

set -e

echo "=== Sesame CLI Smoke Test ==="
echo ""

# Ensure we have the CLI
which sesame-cli > /dev/null || (echo "ERROR: sesame-cli not in PATH"; exit 1)

TEST_DIR="/tmp/sesame_cli_test"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

echo "✓ sesame-cli is available"
echo ""

# Test 1: build
echo "Test 1: sesame-cli build"
sesame-cli build --nx 100 --length 1e-4 --out "$TEST_DIR/test1.gzip" > /dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL"

# Test 2: load
echo "Test 2: sesame-cli load"
sesame-cli load "$TEST_DIR/test1.gzip" > /dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL"

# Test 3: add-donor
echo "Test 3: sesame-cli add-donor"
sesame-cli add-donor "$TEST_DIR/test1.gzip" 1e17 --out "$TEST_DIR/test3.gzip" > /dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL"

# Test 4: add-acceptor
echo "Test 4: sesame-cli add-acceptor"
sesame-cli add-acceptor "$TEST_DIR/test3.gzip" 1e15 --out "$TEST_DIR/test4.gzip" > /dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL"

# Test 5: solve
echo "Test 5: sesame-cli solve"
sesame-cli solve "$TEST_DIR/test4.gzip" --out "$TEST_DIR/test5.gzip" > /dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL"

# Test 6: analyze
echo "Test 6: sesame-cli analyze"
sesame-cli analyze "$TEST_DIR/test5.gzip" --current > /dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL"

# Test 7: plot
echo "Test 7: sesame-cli plot"
sesame-cli plot "$TEST_DIR/test5.gzip" --what v --out "$TEST_DIR/plot.png" > /dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL"

# Test 8: help
echo "Test 8: sesame-cli --help"
sesame-cli --help > /dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL"

# Test 9: subcommand help
echo "Test 9: sesame-cli simulate --help"
sesame-cli simulate --help > /dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL"

echo ""
echo "=== All basic tests completed ==="
echo ""
echo "Test files are in: $TEST_DIR"
echo "To run full IV example: sesame-cli ivcurve --npoints 3 --out $TEST_DIR/iv_test"
