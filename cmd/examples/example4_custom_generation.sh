#!/usr/bin/env bash
# Example 4: Simulate with custom generation profile
# Run: bash example4_custom_generation.sh

set -e

echo "=== Example 4: Custom Generation Profile ==="
echo ""

OUT_DIR="./example4_results"
mkdir -p "$OUT_DIR"

echo "Running simulate with manual generation expression..."
echo "Generation: phi * alpha * exp(-alpha * x)"
echo "Voltages: 0, 0.3, 0.6, 0.9 V"
echo ""

sesame-cli simulate \
  --nx 100 \
  --length 3e-4 \
  --use-manual-g \
  --gen-expr "1e17*2.3e4*np.exp(-2.3e4*x)" \
  --voltage-loop \
  --loop-values "0,0.3,0.6,0.9" \
  --left-contact Ohmic \
  --right-contact Ohmic \
  --periodic \
  --out-dir "$OUT_DIR" \
  --file-name "gen_sweep"

echo ""
echo "Results saved to: $OUT_DIR/gen_sweep_*.gzip"
echo ""
echo "Analyze and plot results:"
echo "  sesame-cli analyze $OUT_DIR/gen_sweep_0.gzip --current"
echo "  sesame-cli plot $OUT_DIR/gen_sweep_0.gzip --what v --out $OUT_DIR/potential_at_0V.png"
