# START HERE — 5-Minute Quick Start

Welcome to Sesame CLI! Get your first simulation running in **5 minutes**.

---

## Step 1: Install (1 minute)

```bash
cd /path/to/sesame
pip install -e .
```

Verify:
```bash
sesame-cli --help
```

You should see a list of 14 commands.

---

## Step 2: Run Your First Simulation (2 minutes)

### Option A: Simple IV Curve (Recommended)

```bash
sesame-cli ivcurve --npoints 5 --out my_iv
```

**What happens:**
- Creates a default system (150 grid points, 3e-4 cm long)
- Sweeps voltage from 0 to 0.95V (5 points)
- Solves at each voltage
- Saves results

**When done, you get:**
- `my_iv_IV_summary.npz` ← voltage and current arrays

### Option B: Custom System

```bash
sesame-cli build --nx 100 --out sys.gzip
sesame-cli ivcurve --mesh-file sys.gzip --npoints 10 --out results
```

---

## Step 3: Load and Analyze Results (2 minutes)

```python
import numpy as np
import matplotlib.pyplot as plt

# Load results
data = np.load('my_iv_IV_summary.npz')
V = data['voltage']
J = data['current']

# Plot
plt.figure(figsize=(8, 6))
plt.plot(V, J, 'o-', linewidth=2, markersize=8)
plt.xlabel('Voltage (V)', fontsize=12)
plt.ylabel('Current Density (A/cm²)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.title('IV Characteristic from Sesame CLI', fontsize=14)
plt.tight_layout()
plt.savefig('my_iv_curve.png', dpi=150)
plt.show()

# Print numbers
print(f"Voc (approx): {V[np.argmin(np.abs(J))]:.3f} V")
print(f"Jsc: {J[0]:.3e} A/cm²")
print(f"Max power: {np.max(V*J):.3e} W/cm²")
```

**Output:**
- `my_iv_curve.png` ← Your first plot!
- Console output with key parameters

---

## 🎯 That's It!

You've just:
✅ Built a semiconductor device  
✅ Computed I-V characteristics  
✅ Analyzed results in Python  

---

## Next Steps

### Want More Examples?

See [`examples/`](./examples/) directory:
- `example1_simple_iv.sh` — Repeat above in shell
- `example2_custom_system.sh` — Build custom structures
- `example3_json_config.sh` — Use JSON configurations
- `example4_custom_generation.sh` — Add light generation
- `example5_convergence_retry.sh` — Handle solver issues

### Need Help?

**Quick questions:**
- `sesame-cli ivcurve --help` — Help for specific command
- [`README.md`](./README.md) — Overview with examples (5 min read)
- [`QUICKSTART.md`](./QUICKSTART.md) — Common workflows (10 min read)

**Complete reference:**
- [`CLI_COMPLETE_GUIDE.md`](./CLI_COMPLETE_GUIDE.md) — Everything (1,462 lines, bookmark it!)

**Troubleshooting:**
- Solver divergence? → See [Troubleshooting](./CLI_COMPLETE_GUIDE.md#troubleshooting--diagnostics)
- Strange results? → See [FAQ](./CLI_COMPLETE_GUIDE.md#faq)

### Advanced Features

**Run batch simulations:**
```bash
# Parameter sweep: vary donor density
for N_D in 1e16 1e17 1e18; do
  sesame-cli simulate --donor-density $N_D \
    --voltage-loop --loop-npoints 10 --out-dir results_ND${N_D}
done
```

**Use JSON configuration:**
```bash
# Create config.json, then:
sesame-cli simulate --config-json config.json --voltage-loop --loop-npoints 10 --out-dir results
```

**Run on HPC (Slurm):**
```bash
#!/bin/bash
#SBATCH --job-name=sesame
#SBATCH --time=02:00:00
sesame-cli simulate --nx 200 --voltage-loop --loop-npoints 20 --out-dir results
```

---

## Command Summary

```bash
# Create system
sesame-cli build --out sys.gzip

# IV curve (main use case)
sesame-cli ivcurve --npoints 10 --out results

# Full simulation with voltage loop
sesame-cli simulate --voltage-loop --loop-npoints 10 --out-dir results

# Inspect saved system
sesame-cli load sys.gzip

# Add materials/doping
sesame-cli add-material sys.gzip --mat '{"Eg": 1.5}' --out sys2.gzip
sesame-cli add-donor sys.gzip 1e17 --out sys2.gzip

# Analyze results
sesame-cli analyze solution.gzip --current --density electron

# Plot results
sesame-cli plot solution.gzip --what v --out potential.png
```

**All 14 commands:** See [`CLI_COMPLETE_GUIDE.md`](./CLI_COMPLETE_GUIDE.md#complete-command-reference)

---

## Where to Go From Here

1. **Tried the examples above?**  
   → Copy/modify for your own research

2. **Want to learn all commands?**  
   → Read [`README.md`](./README.md) then [`CLI_COMPLETE_GUIDE.md`](./CLI_COMPLETE_GUIDE.md)

3. **Need to run batch jobs?**  
   → See [Advanced Usage](./CLI_COMPLETE_GUIDE.md#advanced-usage) and [Integration Guide](./CLI_COMPLETE_GUIDE.md#integration-guide)

4. **Build complex workflows?**  
   → Check [`examples/`](./examples/) and create your own scripts

5. **Stuck?**  
   → Try the [Troubleshooting](./CLI_COMPLETE_GUIDE.md#troubleshooting--diagnostics) section first

---

## Key Things to Remember

✅ **Default system works out of the box** — no config needed  
✅ **Everything is based on flags, JSON, or GUI configs** — choose what suits you  
✅ **Works headless** — perfect for servers, Docker, HPC  
✅ **Results are portable** — `.npz` files load anywhere with NumPy  
✅ **Help is a flag away** — `sesame-cli COMMAND --help`  

---

## File Locations

```
cmd/
├── CLI_COMPLETE_GUIDE.md      ← The Bible (1,462 lines)
├── README.md                  ← Overview + key features
├── QUICKSTART.md              ← Workflows (this file + more)
├── IMPLEMENTATION_SUMMARY.md  ← Architecture details
├── DELIVERY_SUMMARY.md        ← Project summary
├── cli.py                     ← The code (923 lines)
├── examples/                  ← 5 working scripts
└── validate_py.py             ← Test suite
```

---

**Ready?** Run: `sesame-cli ivcurve --npoints 5 --out test`  
**Questions?** Check [`CLI_COMPLETE_GUIDE.md`](./CLI_COMPLETE_GUIDE.md)  
**Need more help?** See [Troubleshooting](./CLI_COMPLETE_GUIDE.md#troubleshooting--diagnostics)  

**Happy simulating!** 🚀
