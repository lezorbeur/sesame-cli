# Sesame CLI — Quick Start

A complete **headless CLI** for Sesame—use all the computational power without needing the GUI.

## Installation

```bash
cd /workspaces/sesame
pip install -e .
```

## Run Your First IV Curve

```bash
python3 -c "import sys; sys.path.insert(0, '/workspaces/sesame'); from cmd.cli import main; main(['ivcurve', '--nx', '150', '--npoints', '10', '--out', 'iv_results'])"
```

This creates:
- `iv_results_0.gzip` ... `iv_results_9.gzip` — Solutions at each voltage
- `iv_results_IV_summary.npz` — Summary with voltages and currents

## Common Workflows

### 1. Build & Solve a System

```bash
python3 -c "
import sys
sys.path.insert(0, '/workspaces/sesame')
from cmd.cli import main

# Build
main(['build', '--nx', '150', '--out', 'mysys.gzip'])

# Add doping
main(['add-donor', 'mysys.gzip', '1e17', '--out', 'mysys_doped.gzip'])

# Solve
main(['solve', 'mysys_doped.gzip', '--out', 'solution.gzip'])

# Analyze
main(['analyze', 'solution.gzip', '--current', '--density', 'both'])
"
```

### 2. Full IV Loop

```bash
python3 -c "
import sys
sys.path.insert(0, '/workspaces/sesame')
from cmd.cli import main
main(['ivcurve', '--npoints', '20', '--vmax', '1.0', '--out', 'iv_scan'])
"
```

### 3. Custom System from JSON

Create `system.json`:
```json
{
  "nx": 200,
  "length": 3e-4,
  "materials": [{"Nc": 8e17, "Nv": 1.8e19, "Eg": 1.5}],
  "donors": [{"density": 1e17}],
  "acceptors": [{"density": 1e15}]
}
```

Run:
```bash
python3 -c "
import sys
sys.path.insert(0, '/workspaces/sesame')
from cmd.cli import main
main(['simulate', '--config-json', 'system.json', '--voltage-loop', '--loop-values', '0,0.1,0.2,0.5', '--out-dir', './results'])
"
```

## All Commands

| Command | Purpose |
|---------|---------|
| `build` | Create a system |
| `ivcurve` | Compute I-V curve |
| `save` | Save default system |
| `load` | Load & inspect system |
| `solve` | Solve equilibrium |
| `analyze` | Extract data (current, density, recomb) |
| `plot` | Visualize results (PNG) |
| `add-donor` | Add n-type doping |
| `add-acceptor` | Add p-type doping |
| `add-defect` | Add recombination centers |
| `set-contacts` | Configure contacts |
| `set-generation` | Set generation profile |
| `run-config` | Execute GUI `.ini` headless |
| `simulate` | Full simulation with CLI flags |

## Documentation

- **Full CLI Docs:** [README.md](./README.md)
- **Examples:** [examples/](./examples/)
  - `example1_simple_iv.sh` — Basic IV
  - `example2_custom_system.sh` — Step-by-step build
  - `example3_json_config.sh` — JSON config
  - `example4_custom_generation.sh` — Custom profiles
  - `example5_convergence_retry.sh` — Troubleshooting

## Validation

Run the validation test:
```bash
python3 /workspaces/sesame/cmd/validate_py.py
```

Expected output:
```
✓ build
✓ load
✓ ivcurve
✓ analyze
✓ plot

✓ All tests passed!
```

## Tips & Tricks

### Headless Matplotlib

All plots work headless (no display needed):
```bash
export MPLBACKEND=Agg
# ... run CLI commands ...
```

### Adjust Solver for Convergence Issues

If equilibrium diverges, try:
```python
main([
  'simulate',
  '--nx', '200',        # Finer mesh
  '--htpy', '5',        # More homotopy steps
  '--tol', '1e-5',      # Relax tolerance
  '--maxiter', '500',   # More iterations
  '--voltage-loop',
  '--loop-values', '0,0.5'
])
```

### Batch Processing

Process many voltages:
```python
from cmd.cli import main
voltages = ','.join(str(v/100) for v in range(0, 100, 5))
main(['ivcurve', '--voltages', voltages, '--out', 'sweep'])
```

### CI/CD Integration

Example GitHub Actions:
```yaml
- run: python3 -c "import sys; sys.path.insert(0, '.'); from cmd.cli import main; main(['ivcurve', '--npoints', '5', '--out', 'iv_ci'])"
- uses: actions/upload-artifact@v2
  with:
    name: iv-results
    path: iv_ci_IV_summary.npz
```

## Troubleshooting

**Q: Entry point `sesame-cli` not found?**  
A: Use `python3 -c "import sys; sys.path.insert(0, '/workspaces/sesame'); from cmd.cli import main; main([...])"` or run `python3 /workspaces/sesame/cmd/cli.py [...]` directly.

**Q: Equilibrium solver diverges?**  
A: Try coarser mesh (`--nx 100`), increase homotopy (`--htpy 5`), or relax tolerance (`--tol 1e-5`). See [README.md](./README.md#troubleshooting) for details.

**Q: How do I run the GUI `.ini` configurations?**  
A: Save config from GUI, then: `main(['run-config', 'my_config.ini', '--out-dir', './results'])`

## Next Steps

- Create your own configurations (JSON or GUI `.ini`)
- Run parametric sweeps (voltages, generation profiles, doping levels)
- Integrate into scripts or HPC workflows
- Generate plots for papers/reports

For detailed documentation, see [README.md](./README.md).
