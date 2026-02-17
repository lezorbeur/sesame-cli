#!/usr/bin/env bash
# Example 1: Simple IV Curve with default system
# Run: bash example1_simple_iv.sh

set -e

echo "=== Example 1: Simple IV Curve ==="
echo ""

OUT_DIR="./example1_results"
mkdir -p "$OUT_DIR"

echo "Building default system and computing IV curve..."
sesame-cli ivcurve \
  --nx 150 \
  --length 3e-4 \
  --npoints 10 \
  --vmin 0 \
  --vmax 0.95 \
  --out "$OUT_DIR/iv_default"

echo ""
echo "Results saved to: $OUT_DIR/iv_default_IV_summary.npz"
echo "Individual voltage solutions: $OUT_DIR/iv_default_*.gzip"
echo ""
echo "To analyze, run:"
echo "  sesame-cli analyze $OUT_DIR/iv_default_0.gzip --current --density electron"
