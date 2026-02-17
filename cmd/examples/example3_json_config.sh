#!/usr/bin/env bash
# Example 3: Simulate with JSON configuration
# Run: bash example3_json_config.sh

set -e

echo "=== Example 3: Simulate with JSON Config ==="
echo ""

OUT_DIR="./example3_results"
CONFIG_FILE="$OUT_DIR/system_config.json"
mkdir -p "$OUT_DIR"

# Create a JSON config
cat > "$CONFIG_FILE" << 'EOF'
{
  "nx": 120,
  "length": 3e-4,
  "materials": [
    {
      "Nc": 8e17,
      "Nv": 1.8e19,
      "Eg": 1.5,
      "affinity": 3.9,
      "epsilon": 9.4,
      "mu_e": 100,
      "mu_h": 100,
      "tau_e": 1e-9,
      "tau_h": 1e-9,
      "Et": 0,
      "B": 0,
      "Cn": 0,
      "Cp": 0,
      "mass_e": 1,
      "mass_h": 1
    }
  ],
  "donors": [
    { "density": 1e17 }
  ],
  "acceptors": [
    { "density": 1e15 }
  ],
  "contacts": {
    "left": "Ohmic",
    "right": "Ohmic"
  },
  "generation": {
    "type": "exponential",
    "phi": 1e17,
    "alpha": 2.3e4
  }
}
EOF

echo "Created config: $CONFIG_FILE"
echo ""

echo "Running simulate with config..."
sesame-cli simulate \
  --config-json "$CONFIG_FILE" \
  --voltage-loop \
  --loop-values "0,0.2,0.5,0.8" \
  --out-dir "$OUT_DIR" \
  --file-name "sim"

echo ""
echo "Results saved to: $OUT_DIR/"
echo ""
echo "To analyze first voltage:"
echo "  sesame-cli analyze $OUT_DIR/sim_0.gzip --current --density electron"
