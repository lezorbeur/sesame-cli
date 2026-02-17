#!/usr/bin/env bash
# Example 5: Troubleshoot convergence with retries
# Run: bash example5_convergence_retry.sh

set -e

echo "=== Example 5: Convergence Troubleshooting ==="
echo ""

OUT_DIR="./example5_results"
mkdir -p "$OUT_DIR"

echo "If basic settings fail to converge, try increasing mesh and homotopy..."
echo ""

echo "Attempt 1: Small mesh, default homotopy (may fail)..."
sesame-cli simulate \
  --nx 50 \
  --length 1e-4 \
  --voltage-loop \
  --loop-values "0,0.1,0.2" \
  --out-dir "$OUT_DIR/attempt1" \
  --file-name "sim" \
  2>&1 | tail -20 || true

echo ""
echo "Attempt 2: Larger mesh, increased homotopy..."
sesame-cli simulate \
  --nx 150 \
  --length 1e-4 \
  --htpy 5 \
  --voltage-loop \
  --loop-values "0,0.1,0.2" \
  --out-dir "$OUT_DIR/attempt2" \
  --file-name "sim" \
  2>&1 | tail -5 || true

echo ""
echo "Attempt 3: Even larger homotopy + relaxed tolerance..."
sesame-cli simulate \
  --nx 150 \
  --length 1e-4 \
  --htpy 10 \
  --tol 1e-5 \
  --voltage-loop \
  --loop-values "0,0.1,0.2" \
  --out-dir "$OUT_DIR/attempt3" \
  --file-name "sim" \
  2>&1 | tail -5 || true

echo ""
echo "Note: If all attempts fail, check the system setup in the GUI first!"
