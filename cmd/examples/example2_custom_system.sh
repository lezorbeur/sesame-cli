#!/usr/bin/env bash
# Example 2: Build custom system step-by-step
# Run: bash example2_custom_system.sh

set -e

echo "=== Example 2: Custom System Step-by-Step ==="
echo ""

OUT_DIR="./example2_results"
mkdir -p "$OUT_DIR"

echo "Step 1: Create base system (100 mesh points, 2e-4 cm length)..."
sesame-cli build \
  --nx 100 \
  --length 2e-4 \
  --out "$OUT_DIR/base_system.gzip"
echo "✓ Created base_system.gzip"

echo ""
echo "Step 2: Add donor doping (1e17 cm^-3)..."
sesame-cli add-donor \
  "$OUT_DIR/base_system.gzip" \
  1e17 \
  --out "$OUT_DIR/doped_system.gzip"
echo "✓ Added donor doping"

echo ""
echo "Step 3: Add acceptor doping (1e15 cm^-3)..."
sesame-cli add-acceptor \
  "$OUT_DIR/doped_system.gzip" \
  1e15 \
  --out "$OUT_DIR/final_system.gzip"
echo "✓ Added acceptor doping"

echo ""
echo "Step 4: Verify final system..."
sesame-cli load "$OUT_DIR/final_system.gzip"

echo ""
echo "Step 5: Solve and analyze..."
sesame-cli solve \
  "$OUT_DIR/final_system.gzip" \
  --tol 1e-6 \
  --maxiter 300 \
  --out "$OUT_DIR/final_solution.gzip"

sesame-cli analyze \
  "$OUT_DIR/final_solution.gzip" \
  --density both \
  --current

echo ""
echo "Results in: $OUT_DIR/"
