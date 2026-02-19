#!/usr/bin/env bash
# Quick validation that all CLI commands work
# This test can be run from anywhere after `pip install -e .`

set -e

PYTHON="/usr/bin/python3"
WORKDIR="/tmp/sesame_cli_validation"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

echo "=== Sesame CLI Validation Test ==="
echo "Working directory: $WORKDIR"
echo ""

# Ensure we can import the CLI
export PYTHONPATH="/app:$PYTHONPATH"

test_cmd() {
    local name="$1"
    shift
    echo -n "  Testing: $name ... "
    if python3 << PYEOF > /dev/null 2>&1
import sys
sys.path.insert(0, '/app')
from cmd.cli import main
sys.exit(main($@) or 0)
PYEOF
    then
        echo "✓ PASS"
        return 0
    else
        echo "✗ FAIL"
        return 1
    fi
}

echo "Test 1: build"
test_cmd "build" "['build', '--nx', '150', '--out', 'sys.gzip']"

echo "Test 2: load"
test_cmd "load" "['load', 'sys.gzip']"

echo "Test 3: add-donor"
test_cmd "add-donor" "['add-donor', 'sys.gzip', '1e17', '--out', 'sys2.gzip']"

echo "Test 4: add-acceptor"
test_cmd "add-acceptor" "['add-acceptor', 'sys2.gzip', '1e15', '--out', 'sys3.gzip']"

echo "Test 5: solve"
test_cmd "solve" "['solve', 'sys3.gzip', '--out', 'solved.gzip']"

echo "Test 6: analyze"
test_cmd "analyze" "['analyze', 'solved.gzip', '--current']"

echo ""
echo "✓ All core commands validated successfully!"
echo ""
echo "For full documentation, see: /workspaces/sesame/cmd/README.md"
echo "For examples, see: /workspaces/sesame/cmd/examples/"
