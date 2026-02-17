# Sesame CLI — Complete Comprehensive Guide

*A production-ready command-line interface to Sesame, enabling full workflow automation, HPC integration, and headless operation.*

---

## Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Installation & Setup](#installation--setup)
3. [Quick Start (5 minutes)](#quick-start-5-minutes)
4. [Complete Command Reference](#complete-command-reference)
5. [Configuration Formats](#configuration-formats)
6. [Workflow Examples](#workflow-examples)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting & Diagnostics](#troubleshooting--diagnostics)
9. [Integration Guide](#integration-guide)
10. [FAQ](#faq)

---

## Overview & Architecture

### What is Sesame CLI?

Sesame CLI is a **headless, full-featured command-line interface** to the Sesame semiconductor device simulator. It provides:

- **14 subcommands** for system building, solving, analysis, and visualization
- **Complete feature parity** with the GUI (no GUI → no loss of functionality)
- **Flexible configuration** via CLI flags, JSON files, or GUI `.ini` configurations
- **Production-ready error handling** with automatic retries and detailed diagnostics
- **HPC & CI/CD ready** — runs on headless servers, Docker, slurm clusters, GitHub Actions

### Architecture

```
Command-Line Input
       ↓
    CLI Parser (argparse)
       ↓
Command Handlers (cmd_build, cmd_solve, etc.)
       ↓
Sesame Library (unmodified)
       ↓
Results (gzip files, PNG plots, console output)
```

**Key Design Principles:**
- Zero modifications to core Sesame library
- All CLI functionality lives in `cmd/cli.py`
- Configuration-driven (JSON for portability, CLI flags for convenience)
- Robust error handling with actionable messages

---

## Installation & Setup

### Prerequisites

- Python 3.8+
- NumPy, SciPy, Matplotlib (installed with Sesame)
- Sesame source code (this repo)

### Step 1: Install Sesame with CLI support

```bash
cd /path/to/sesame
pip install -e .
```

This installs Sesame in development mode and registers the `sesame-cli` command.

### Step 2: Verify installation

```bash
sesame-cli --help
```

**Expected output:** Lists all 14 subcommands with descriptions.

### Step 3: Test basic operation

```bash
sesame-cli build --out test_system.gzip
sesame-cli load test_system.gzip
sesame-cli ivcurve --out test_iv --npoints 3
```

All three commands should complete successfully.

### Optional: Enable MUMPS (sparse solver)

If your Sesame installation includes MUMPS for faster solving:

```bash
sesame-cli simulate --use-mumps --out-dir ./results ...
```

---

## Quick Start (5 minutes)

### Scenario 1: Compute an IV curve with defaults

```bash
# Generate and solve across 5 voltages (0 → 0.8V)
sesame-cli ivcurve --npoints 5 --vmax 0.8 --out iv_results

# Outputs:
# - iv_results_IV_summary.npz  (voltage and current arrays)
```

### Scenario 2: Custom system with custom doping

```bash
# Create system, add donors and acceptors
sesame-cli build --nx 120 --length 2.5e-4 --out sys.gzip
sesame-cli add-donor sys.gzip 5e16 --out sys.gzip
sesame-cli add-acceptor sys.gzip 5e15 --out sys.gzip

# Run IV curve
sesame-cli ivcurve --mesh-file sys.gzip --npoints 10 --out myiv
```

### Scenario 3: Load a GUI configuration and run headless

1. **In the GUI:** File → Save Configuration → `my_config.ini`
2. **On command line:**
   ```bash
   sesame-cli run-config my_config.ini --out-dir ./headless_results
   # CLI runs the exact same simulation as the GUI
   ```

### Scenario 4: Define system in JSON and run full simulation

```bash
# Create config file
cat > system.json << 'EOF'
{
  "nx": 100,
  "length": 3e-4,
  "donors": [{"density": 1e17}],
  "acceptors": [{"density": 1e15}],
  "generation": {"type": "exponential", "phi": 1e17, "alpha": 2.3e4}
}
EOF

# Run simulation
sesame-cli simulate --config-json system.json \
  --voltage-loop --loop-values "0,0.3,0.6,0.9" \
  --out-dir ./results
```

---

## Complete Command Reference

### Universal Options

All commands accept:

```bash
-h, --help              Show command-specific help
--debug                 Enable debug logging (verbose output to stderr)
```

---

### 1. `build` — Create a system

**Purpose:** Build a semiconductor system from scratch.

**Usage:**

```bash
sesame-cli build [OPTIONS] --out OUTPUT_FILE
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--out` | str | - | **Required.** Output `.gzip` filename |
| `--nx` | int | 150 | Number of grid points (1D) |
| `--ny` | int | 1 | Number of grid points y-direction (2D) |
| `--length` | float | 3e-4 | Device length [cm] |
| `--width` | float | 1e-4 | Device width [cm] (2D systems) |
| `--config` | str | - | JSON config file (overrides --nx, --length, etc.) |
| `--periodic` | - | False | Use periodic boundary conditions |

**Examples:**

```bash
# Simple 1D with 100 grid points
sesame-cli build --nx 100 --out sys.gzip

# 2D system 200×50 points
sesame-cli build --nx 200 --ny 50 --length 5e-4 --width 1e-4 --out sys2d.gzip

# From JSON configuration
sesame-cli build --config system_config.json --out sys.gzip
```

**Output:** `sys.gzip` — serialized Sesame system object

---

### 2. `ivcurve` — Compute I-V characteristics

**Purpose:** Run a voltage sweep and compute current at each voltage.

**Usage:**

```bash
sesame-cli ivcurve [OPTIONS] --out OUTPUT_PREFIX
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--out` | str | - | **Required.** Output prefix (no extension) |
| `--mesh-file` | str | - | Load system from `.gzip` (if empty, use defaults) |
| `--nx` | int | 150 | Grid points (only if no `--mesh-file`) |
| `--length` | float | 3e-4 | Device length [cm] (only if no `--mesh-file`) |
| `--npoints` | int | 10 | Number of voltages to sweep |
| `--vmin` | float | 0 | Minimum voltage [V] |
| `--vmax` | float | 0.95 | Maximum voltage [V] |
| `--voltages` | str | - | Explicit voltage list, e.g., `"0,0.2,0.5,0.8"` (overrides npoints/vmin/vmax) |
| `--tol` | float | 1e-6 | Solver tolerance |
| `--maxiter` | int | 300 | Max solver iterations per voltage |

**Examples:**

```bash
# Simple IV: 10 voltages, 0→0.95 V
sesame-cli ivcurve --out iv1

# Custom voltage range and density
sesame-cli ivcurve --npoints 20 --vmin 0 --vmax 1.2 --out iv2

# Explicit voltages
sesame-cli ivcurve --voltages "0,0.1,0.2,0.3,0.5,0.7,0.9" --out iv3

# Load custom system and sweep
sesame-cli ivcurve --mesh-file mysys.gzip --npoints 15 --vmax 1.0 --out iv4

# Fine tolerance
sesame-cli ivcurve --npoints 10 --tol 1e-7 --maxiter 500 --out iv5
```

**Output:**
- `iv1_IV_summary.npz` — NumPy archive with `voltage` and `current` arrays
- `iv1_0.gzip`, `iv1_1.gzip`, ... — Full solution at each voltage

**Loading results in Python:**

```python
import numpy as np
data = np.load('iv1_IV_summary.npz')
voltages = data['voltage']
currents = data['current']
# Plot, analyze, etc.
```

---

### 3. `solve` — Equilibrium/drift-diffusion solver

**Purpose:** Solve a system at equilibrium or under applied voltage.

**Usage:**

```bash
sesame-cli solve INPUT_FILE [OPTIONS] --out OUTPUT_FILE
```

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `INPUT_FILE` | str | Input `.gzip` system file |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--out` | str | - | **Required.** Output `.gzip` filename |
| `--voltage` | float | 0 | Applied voltage [V] |
| `--tol` | float | 1e-6 | Solver tolerance |
| `--maxiter` | int | 300 | Max iterations |
| `--htpy` | int | 1 | Homotopy steps (higher = more robust, slower) |

**Examples:**

```bash
# Equilibrium solve
sesame-cli solve sys.gzip --out sys_eq.gzip

# At 0.5 V with stricter tolerance
sesame-cli solve sys.gzip --voltage 0.5 --tol 1e-7 --out sys_0p5V.gzip

# High homotopy for difficult cases
sesame-cli solve sys.gzip --voltage 0.8 --htpy 5 --out sys_0p8V.gzip
```

**Output:** `sys_eq.gzip` — solved system with potential, electron/hole densities

---

### 4. `save` — Save a default system

**Purpose:** Create a default system and save immediately.

**Usage:**

```bash
sesame-cli save OUTPUT_FILE
```

**Examples:**

```bash
sesame-cli save default_sys.gzip
```

---

### 5. `load` — Load and inspect a system

**Purpose:** Load a `.gzip` system file and display summary info.

**Usage:**

```bash
sesame-cli load INPUT_FILE
```

**Output Example:**

```
System: 150×1 grid (1D)
Length: 3.00e-04 cm
Defects: 0
Donors: 1 (density = 1.00e+17 cm⁻³)
Acceptors: 1 (density = 1.00e+15 cm⁻³)
```

---

### 6. `analyze` — Extract and display observables

**Purpose:** Compute current densities, carrier densities, recombination rates from solved systems.

**Usage:**

```bash
sesame-cli analyze INPUT_FILE [OPTIONS]
```

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `INPUT_FILE` | str | Solved `.gzip` system file |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--current` | - | Print current [A/cm²] at both contacts |
| `--density <type>` | str | `electron`, `hole`, or `both` |
| `--recomb <type>` | str | `total`, `srh`, or `bimolecular` |

**Examples:**

```bash
sesame-cli analyze sys_0p5V.gzip --current
sesame-cli analyze sys_0p5V.gzip --density electron
sesame-cli analyze sys_0p5V.gzip --recomb srh
sesame-cli analyze sys_0p5V.gzip --density both --current
```

**Output:** Formatted arrays printed to stdout; save to file with `> output.txt`

---

### 7. `plot` — Generate headless visualizations

**Purpose:** Create PNG plots from solved systems (no GUI needed).

**Usage:**

```bash
sesame-cli plot INPUT_FILE [OPTIONS] --what QUANTITY --out OUTPUT_PNG
```

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `INPUT_FILE` | str | Input `.gzip` system file |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--what` | str | - | **Required.** Quantity to plot: `v` (potential), `n` (electron density), `p` (hole density), `Eg` (bandgap), `grid`, `generation`, `recombination` |
| `--out` | str | - | **Required.** Output PNG filename |
| `--vmin` | float | auto | Min value for colorbar |
| `--vmax` | float | auto | Max value for colorbar |

**Examples:**

```bash
sesame-cli plot sys_0p5V.gzip --what v --out potential.png
sesame-cli plot sys_0p5V.gzip --what n --out electron_density.png
sesame-cli plot sys_0p5V.gzip --what "Eg" --out bandgap.png
```

**Output:** PNG image file suitable for embedding in reports, presentations, etc.

---

### 8. `add-material` — Modify material properties

**Purpose:** Change material parameters (Eg, Nc, mu, etc.) in a system.

**Usage:**

```bash
sesame-cli add-material INPUT_FILE [OPTIONS] --out OUTPUT_FILE
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--mat-file` | str | JSON file with material properties |
| `--mat` | str | Inline JSON: `'{"Nc": 1e19, "Eg": 1.4}'` |
| `--x-less` | float | Apply to region x < value [cm] |
| `--x-greater` | float | Apply to region x > value [cm] |
| `--out` | str | **Required.** Output `.gzip` file |

**Examples:**

```bash
# From file
sesame-cli add-material sys.gzip --mat-file CdTe.json --out sys_cdTe.gzip

# Inline
sesame-cli add-material sys.gzip --mat '{"Eg": 1.6, "Nc": 5e18}' --out sys_mod.gzip

# Spatial variation (heterostructure)
sesame-cli add-material sys.gzip --x-less 1.5e-4 --mat '{"Eg": 1.4}' --out sys_het.gzip
```

---

### 9. `add-donor` & `add-acceptor` — Add doping

**Purpose:** Add shallow donor or acceptor doping to a system.

**Usage:**

```bash
sesame-cli add-donor INPUT_FILE DENSITY [OPTIONS] --out OUTPUT_FILE
sesame-cli add-acceptor INPUT_FILE DENSITY [OPTIONS] --out OUTPUT_FILE
```

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `DENSITY` | float | Doping density [cm⁻³] |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--x-less` | float | Apply to region x < value [cm] |
| `--x-greater` | float | Apply to region x > value [cm] |
| `--out` | str | **Required.** Output `.gzip` file |

**Examples:**

```bash
# Uniform n-doping
sesame-cli add-donor sys.gzip 1e17 --out sys_n.gzip

# p-doped region
sesame-cli add-acceptor sys.gzip 1e15 --out sys_p.gzip

# Graded doping (heterojunction)
sesame-cli add-donor sys.gzip 1e18 --x-less 1.5e-4 --out sys_nside.gzip
sesame-cli add-acceptor sys_nside.gzip 1e16 --x-greater 1.5e-4 --out sys_het.gzip
```

---

### 10. `add-defect` — Add recombination centers

**Purpose:** Add point or line defects (traps) with specific capture cross-sections.

**Usage:**

```bash
sesame-cli add-defect INPUT_FILE LOCATION DENSITY SIGMA_E [OPTIONS] --out OUTPUT_FILE
```

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `LOCATION` | str | `point:x` or `line:x1,y1;x2,y2` in [cm] |
| `DENSITY` | float | Defect density [cm⁻³] or [cm⁻²] |
| `SIGMA_E` | float | Electron capture cross-section [cm²] |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--sigma_h` | float | `SIGMA_E` | Hole capture cross-section [cm²] |
| `--E` | float | 0.5 | Energy level relative to bandgap midpoint |
| `--out` | str | - | **Required.** Output `.gzip` file |

**Examples:**

```bash
# Point defect at x = 1e-5 cm
sesame-cli add-defect sys.gzip point:1e-5 1e12 1e-14 --sigma_h 1e-14 --E 0.5 --out sys_defect.gzip

# Line defect (grain boundary in 2D)
sesame-cli add-defect sys2d.gzip line:1.5e-4,0;1.5e-4,1e-4 5e11 1e-13 --out sys_gb.gzip
```

---

### 11. `set-contacts` — Configure contact boundary conditions

**Purpose:** Set contact types and surface recombination velocities.

**Usage:**

```bash
sesame-cli set-contacts INPUT_FILE [OPTIONS] --out OUTPUT_FILE
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--left` | str | Contact type: `Ohmic`, `Neutral`, `Schottky` |
| `--right` | str | Contact type: `Ohmic`, `Neutral`, `Schottky` |
| `--contact-S` | str | Surface recomb. velocities: `S_e_left,S_e_right,S_h_left,S_h_right` [cm/s] |
| `--out` | str | **Required.** Output `.gzip` file |

**Examples:**

```bash
# Ohmic contacts (default)
sesame-cli set-contacts sys.gzip --left Ohmic --right Ohmic --out sys2.gzip

# Mixed contacts
sesame-cli set-contacts sys.gzip --left Ohmic --right Schottky --out sys2.gzip

# With surface recombination (1e6 cm/s for electrons and holes)
sesame-cli set-contacts sys.gzip --contact-S "1e6,1e6,1e6,1e6" --out sys2.gzip
```

---

### 12. `set-generation` — Configure light generation profile

**Purpose:** Set illumination or generation profile.

**Usage:**

```bash
sesame-cli set-generation INPUT_FILE [OPTIONS] --out OUTPUT_FILE
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--type` | str | `none`, `exponential`, `uniform`, `custom` |
| `--phi` | float | Light flux [cm⁻²s⁻¹] (for exponential/uniform) |
| `--alpha` | float | Absorption coefficient [cm⁻¹] (for exponential) |
| `--expr` | str | Custom generation expression in x: `"5e17*np.exp(-x*1e4)"` |
| `--out` | str | **Required.** Output `.gzip` file |

**Examples:**

```bash
# No generation (dark)
sesame-cli set-generation sys.gzip --type none --out sys_dark.gzip

# Exponential (typical for solar cells)
sesame-cli set-generation sys.gzip --type exponential --phi 1e17 --alpha 2.3e4 --out sys_light.gzip

# Custom expression
sesame-cli set-generation sys.gzip --type custom --expr "5e17*np.exp(-np.abs(x-1.5e-4)*1e4)" --out sys_custom.gzip
```

---

### 13. `run-config` — Execute GUI `.ini` configurations headless

**Purpose:** Load a configuration saved from the GUI and run the full simulation headless.

**Usage:**

```bash
sesame-cli run-config CONFIG_FILE [OPTIONS]
```

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `CONFIG_FILE` | str | `.ini` file saved from Sesame GUI |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--out-dir` | str | Output directory for results |

**Workflow:**

1. **In GUI:** File → Save Configuration → `my_config.ini`
2. **Command line:** `sesame-cli run-config my_config.ini --out-dir ./results`

**Example:**

```bash
sesame-cli run-config solar_cell.ini --out-dir ./pv_results
# Runs: system build + voltage loop + solver at each voltage
# Outputs: results in ./pv_results/
```

**Note:** The `.ini` file contains all GUI settings (mesh, doping, generation, solver params, etc.). No additional parameters needed.

---

### 14. `simulate` — Full-featured end-to-end simulation

**Purpose:** Build system → solve series of voltages → save results in one command.

**Usage:**

```bash
sesame-cli simulate [OPTIONS] --out-dir OUTPUT_DIR
```

**System Definition (choose one):**

| Option | Type | Description |
|--------|------|-------------|
| `--config-json` | str | JSON system config file |
| `--nx` | int | Grid points (default = 150) |
| `--ny` | int | Grid points y (default = 1, use >1 for 2D) |
| `--length` | float | Device length [cm] (default = 3e-4) |
| `--width` | float | Device width [cm] (2D only) |

**Doping:**

| Option | Type | Description |
|--------|------|-------------|
| `--donor-density` | float | Uniform n-doping [cm⁻³] |
| `--acceptor-density` | float | Uniform p-doping [cm⁻³] |

**Generation:**

| Option | Type | Description |
|--------|------|-------------|
| `--use-manual-g` | - | Enable custom generation |
| `--gen-type` | str | `exponential`, `uniform`, `custom` |
| `--gen-phi` | float | Light flux [cm⁻²s⁻¹] |
| `--gen-alpha` | float | Absorption coeff [cm⁻¹] |
| `--gen-expr` | str | Custom expression in x |

**Voltage Loop:**

| Option | Type | Description |
|--------|------|-------------|
| `--voltage-loop` | - | Enable voltage sweep |
| `--loop-values` | str | Voltage list: `"0,0.2,0.5,0.8"` |
| `--loop-npoints` | int | Generate npoints voltages |
| `--loop-min` | float | Min voltage [V] |
| `--loop-max` | float | Max voltage [V] |

**Solver:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--tol` | float | 1e-6 | Solver tolerance |
| `--maxiter` | int | 300 | Max iterations |
| `--htpy` | int | 1 | Homotopy steps |

**Output:**

| Option | Type | Description |
|--------|------|-------------|
| `--out-dir` | str | **Required.** Output directory |

**Examples:**

```bash
# Simple 1D IV curve
sesame-cli simulate \
  --nx 100 --length 2e-4 \
  --voltage-loop --loop-values "0,0.2,0.5,0.8" \
  --out-dir ./results1

# 2D system with generation
sesame-cli simulate \
  --nx 120 --ny 80 --length 3e-4 --width 1e-4 \
  --donor-density 1e17 --acceptor-density 1e15 \
  --use-manual-g --gen-type exponential --gen-phi 1e17 --gen-alpha 2.3e4 \
  --voltage-loop --loop-npoints 10 --loop-max 1.0 \
  --out-dir ./results2d

# From JSON with tight tolerance
sesame-cli simulate \
  --config-json device.json \
  --voltage-loop --loop-values "0,0.25,0.5,0.75,1.0" \
  --tol 1e-7 --maxiter 500 \
  --out-dir ./accurate_results

# Custom generation expression
sesame-cli simulate \
  --nx 150 --length 3e-4 \
  --donor-density 1e17 \
  --use-manual-g --gen-type custom \
  --gen-expr "1e17 * 2.3e4 * np.exp(-2.3e4*x)" \
  --voltage-loop --loop-npoints 8 --loop-max 0.9 \
  --out-dir ./custom_gen
```

**Output:** 
- `sim_0.gzip`, `sim_1.gzip`, ... — Solved systems at each voltage
- `sim_IV_summary.npz` — Voltage and current arrays
- Console output with timing and diagnostics

---

## Configuration Formats

### JSON System Configuration

Complete JSON schema for `--config-json`:

```json
{
  "nx": 100,
  "ny": 1,
  "length": 3e-4,
  "width": 1e-4,
  "periodic": false,
  
  "materials": [
    {
      "Nc": 8e17,
      "Nv": 1.8e19,
      "Eg": 1.5,
      "affinity": 3.9,
      "epsilon": 9.4,
      "mu_e": 100,
      "mu_h": 100,
      "tau_e": 1e-8,
      "tau_h": 1e-8,
      "Et": 0,
      "B": 1e-10,
      "Cn": 0,
      "Cp": 0,
      "mass_e": 1,
      "mass_h": 1
    }
  ],
  
  "donors": [
    {
      "density": 1e17,
      "x_less": null,
      "x_greater": null
    }
  ],
  
  "acceptors": [
    {
      "density": 1e15,
      "x_less": null,
      "x_greater": null
    }
  ],
  
  "defects": [
    {
      "location": "point:1e-5",
      "density": 1e12,
      "sigma_e": 1e-14,
      "sigma_h": 1e-14,
      "energy": 0.5
    }
  ],
  
  "contacts": {
    "left": "Ohmic",
    "right": "Ohmic",
    "surface_recomb": [1e6, 1e6, 1e6, 1e6]
  },
  
  "generation": {
    "type": "exponential",
    "phi": 1e17,
    "alpha": 2.3e4,
    "expr": null
  }
}
```

**Minimal JSON (everything else uses defaults):**

```json
{
  "donors": [{"density": 1e17}],
  "acceptors": [{"density": 1e15}]
}
```

### Material Property File (material.json)

```json
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
  "B": 1e-10,
  "Cn": 0,
  "Cp": 0,
  "mass_e": 1,
  "mass_h": 1
}
```

**Common materials:**

**Silicon (Si):**
```json
{"Nc": 2.86e19, "Nv": 3.1e19, "Eg": 1.12, "affinity": 4.05, "epsilon": 11.7, "mu_e": 1350, "mu_h": 480, "tau_e": 1e-7, "tau_h": 1e-7}
```

**GaAs:**
```json
{"Nc": 4.4e17, "Nv": 7.0e18, "Eg": 1.43, "affinity": 4.07, "epsilon": 13.1, "mu_e": 8500, "mu_h": 400, "tau_e": 1e-8, "tau_h": 1e-8}
```

**CdTe:**
```json
{"Nc": 8e17, "Nv": 1.8e19, "Eg": 1.5, "affinity": 3.9, "epsilon": 9.4, "mu_e": 100, "mu_h": 100, "tau_e": 1e-9, "tau_h": 1e-9}
```

### Defects File (defects.json)

```json
[
  {
    "location": "point:1e-5",
    "density": 1e12,
    "sigma_e": 1e-14,
    "sigma_h": 1e-14,
    "energy": 0.5
  },
  {
    "location": "line:1.5e-4,0;1.5e-4,1e-4",
    "density": 5e11,
    "sigma_e": 2e-13,
    "sigma_h": 2e-13,
    "energy": 0.3
  }
]
```

---

## Workflow Examples

### Example 1: Simple Solar Cell IV Curve

```bash
#!/bin/bash
# Compute I-V curve for a simple homojunction

sesame-cli ivcurve \
  --nx 150 \
  --length 3e-4 \
  --npoints 15 \
  --vmax 1.0 \
  --out solar_cell_iv

# Extract and plot with Python
python3 << 'PYEOF'
import numpy as np
import matplotlib.pyplot as plt

data = np.load('solar_cell_iv_IV_summary.npz')
V = data['voltage']
J = data['current']

plt.figure(figsize=(8,6))
plt.plot(V, J, 'o-', linewidth=2)
plt.xlabel('Voltage (V)')
plt.ylabel('Current Density (A/cm²)')
plt.grid(True)
plt.savefig('iv_curve.png', dpi=150)
print(f"Max power point: V={V[np.argmax(V*J)]:.2f}V, J={J[np.argmax(V*J)]:.2e}A/cm²")
PYEOF
```

### Example 2: Heterojunction with Custom Materials

```bash
#!/bin/bash
# Create an n-type/p-type heterojunction with different materials

# Create base system
sesame-cli build --nx 120 --length 2.5e-4 --out het.gzip

# n-side: GaAs (0 to 1.25e-4 cm)
sesame-cli add-material het.gzip \
  --x-less 1.25e-4 \
  --mat '{"Nc": 4.4e17, "Nv": 7.0e18, "Eg": 1.43, "affinity": 4.07, "mu_e": 8500, "mu_h": 400}' \
  --out het.gzip

# p-side: CdTe (1.25e-4 to 2.5e-4 cm)
sesame-cli add-material het.gzip \
  --x-greater 1.25e-4 \
  --mat '{"Nc": 8e17, "Nv": 1.8e19, "Eg": 1.5, "affinity": 3.9, "mu_e": 100, "mu_h": 100}' \
  --out het.gzip

# Add doping
sesame-cli add-donor het.gzip 1e17 --x-less 1.25e-4 --out het.gzip
sesame-cli add-acceptor het.gzip 1e15 --x-greater 1.25e-4 --out het.gzip

# Simulate
sesame-cli simulate --mesh-file het.gzip \
  --voltage-loop --loop-npoints 12 --loop-max 1.1 \
  --out-dir ./het_results
```

### Example 3: GUI Configuration → Headless Batch

```bash
#!/bin/bash
# Save configuration in GUI, then run multiple times with different parameters

# Original config from GUI
CONFIG="my_device.ini"

# Run headless (uses all GUI settings)
sesame-cli run-config "$CONFIG" --out-dir ./baseline_results

# For parametric studies, create JSON variants
for T in 250 300 350; do
  cat > config_${T}K.json << EOF
{
  "nx": 150,
  "length": 3e-4,
  "temperature": $T,
  "donors": [{"density": 1e17}],
  "acceptors": [{"density": 1e15}],
  "generation": {"type": "exponential", "phi": 1e17, "alpha": 2.3e4}
}
EOF
  
  sesame-cli simulate --config-json config_${T}K.json \
    --voltage-loop --loop-npoints 10 --loop-max 1.0 \
    --out-dir ./results_${T}K
done
```

### Example 4: Grain Boundary Defect Study

```bash
#!/bin/bash
# Create 2D system with grain boundary and sweep defect density

BASE="gb_system.gzip"

# Create 2D base system
sesame-cli build --nx 120 --ny 60 --length 3e-4 --width 1.5e-4 --out "$BASE"

# Add uniform doping
sesame-cli add-donor "$BASE" 1e17 --out "$BASE"
sesame-cli add-acceptor "$BASE" 1e15 --out "$BASE"

# Study effect of GB defect density
for DEFECT_DENS in 1e10 1e11 1e12 1e13; do
  LABEL=$(printf "%.0e" "$DEFECT_DENS")
  OUT="gb_${LABEL}.gzip"
  
  sesame-cli add-defect "$BASE" \
    --location "line:1.5e-4,0;1.5e-4,1.5e-4" \
    "$DEFECT_DENS" 1e-13 \
    --sigma_h 1e-13 --E 0.5 \
    --out "$OUT"
  
  # Solve at one voltage
  sesame-cli solve "$OUT" --voltage 0.5 --out "${OUT%.gzip}_solved.gzip"
  
  # Extract current
  CURRENT=$(sesame-cli analyze "${OUT%.gzip}_solved.gzip" --current 2>/dev/null | grep -oE "[0-9.e+-]+" | head -1)
  echo "GB defect density=$DEFECT_DENS, J=$CURRENT A/cm²"
done
```

---

## Advanced Usage

### Performance Optimization

**Use MUMPS for faster solving:**

```bash
sesame-cli simulate --use-mumps \
  --nx 200 --ny 100 \
  --voltage-loop --loop-npoints 20 \
  --out-dir ./fast_results
```

(Requires MUMPS compiled in your Sesame installation.)

**Coarser mesh for parameter exploration:**

```bash
sesame-cli ivcurve --nx 80 --out quick_iv  # Fast, lower accuracy
# Then use finer mesh for final results:
sesame-cli ivcurve --nx 250 --out final_iv  # Slower, higher accuracy
```

**Parallel batch processing (GNU Parallel or xargs):**

```bash
# Create multiple configs
for V in 0.0 0.1 0.2 0.3 0.4 0.5; do
  cat > config_v${V}.json <<< '{"donors":[{"density":1e17}],"acceptors":[{"density":1e15}]}'
done

# Run in parallel (using GNU Parallel)
parallel "sesame-cli simulate --config-json {} --voltage 0.5 --out-dir results_{/.}" ::: config_v*.json

# Or with xargs (8 processes):
ls config_v*.json | xargs -P 8 -I {} bash -c 'sesame-cli simulate --config-json {} --voltage 0.5 --out-dir results_$(basename {} .json)'
```

### Custom Python Scripts Using Save/Load

```python
#!/usr/bin/env python3
# Post-process CLI results

import numpy as np
import gzip
import pickle
import matplotlib.pyplot as plt

# Load IV curve result
data = np.load('results/ivcurve_IV_summary.npz')
V = data['voltage']
J = data['current']

# Calculate power density
P = V * J

# Plot IV and power
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.plot(V, J, 'b-o')
ax1.set_xlabel('Voltage (V)')
ax1.set_ylabel('Current Density (A/cm²)')
ax1.grid()
ax1.set_title('I-V Characteristic')

ax2.plot(V, P, 'r-o')
ax2.set_xlabel('Voltage (V)')
ax2.set_ylabel('Power Density (W/cm²)')
ax2.grid()
ax2.set_title('Power Output')

plt.tight_layout()
plt.savefig('analysis.png', dpi=150)

# Extract MPP
mpp_idx = np.argmax(P)
print(f"MPP: V={V[mpp_idx]:.3f} V, J={J[mpp_idx]:.3e} A/cm², P={P[mpp_idx]:.3e} W/cm²")
print(f"Voc: {V[np.argmin(np.abs(J))]:.3f} V")
print(f"Jsc: {J[0]:.3e} A/cm²")
```

### Sensitivity Analysis

```bash
#!/bin/bash
# Parameter sweep: vary Eg and measure Voc

for EG in 1.0 1.2 1.4 1.6 1.8; do
  # Create config with specific Eg
  cat > config_Eg${EG}.json << EOF
{
  "nx": 150,
  "length": 3e-4,
  "materials": [{"Eg": $EG, "Nc": 1e19, "Nv": 1e19, "affinity": 4.0, "epsilon": 10}],
  "donors": [{"density": 1e17}],
  "acceptors": [{"density": 1e15}]
}
EOF
  
  # Run IV curve
  sesame-cli ivcurve --config config_Eg${EG}.json --npoints 20 --out iv_Eg${EG}
  
  # Extract Voc (voltage where current crosses zero)
  python3 << PYEOF
import numpy as np
data = np.load('iv_Eg${EG}_IV_summary.npz')
V = data['voltage']
J = data['current']
# Find zero-crossing (simplified)
idx = np.argmin(np.abs(J))
voc = V[idx]
print(f"Eg=$EG: Voc={voc:.3f}V")
PYEOF
done
```

---

## Troubleshooting & Diagnostics

### Equilibrium Solver Divergence

**Error:** `ERROR: Equilibrium could not be found after retries`

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Mesh too fine | Use coarser mesh: `--nx 100` instead of `--nx 200` |
| Unrealistic doping | Check donor/acceptor densities (should be positive, <1e20 cm⁻³) |
| Poor initial guess | Increase homotopy: `--htpy 5` or `--htpy 10` |
| Solver too strict | Relax tolerance: `--tol 1e-5` instead of `1e-6` |
| Material parameters | Verify Nc, Nv, Eg, mu, tau are physically reasonable |
| Contact type mismatch | Ensure contact BCs match doping (Ohmic for n-doped, etc.) |

**Diagnostic workflow:**

```bash
# 1. Test with simple system
sesame-cli ivcurve --nx 100 --out test_simple

# 2. If that works, try coarser version of your system
sesame-cli ivcurve --nx 80 --out test_coarse

# 3. Gradually increase nx
sesame-cli ivcurve --nx 120 --out test_120
sesame-cli ivcurve --nx 150 --out test_150

# 4. If still failing, inspect system
sesame-cli simulate --config-json my_config.json --htpy 5 --tol 1e-5 --out-dir debug
```

### Solver Fails at Specific Application voltage

**Symptom:** Successfully solves at V=0, 0.2V, then diverges at V=0.5V

**Likely Cause:** Physical limitation at that voltage (e.g., high injection, avalanche)

**Actions:**

1. **Try high homotopy:**
   ```bash
   sesame-cli simulate --htpy 10 --voltage-loop --loop-values "0,0.2,0.5" --out-dir results
   ```

2. **Reduce voltage step:**
   ```bash
   sesame-cli simulate \
     --voltage-loop --loop-values "0,0.1,0.2,0.3,0.4,0.45,0.5" \
     --out-dir results
   ```

3. **Check material/doping validity** at that voltage (inspect with GUI first).

### Memory Issues on Coarse/2D Meshes

**Symptom:** `MemoryError` or excessive memory consumption

**Solution:**

1. **Reduce mesh size:**
   ```bash
   sesame-cli simulate --nx 100 --ny 50 --out-dir results  # instead of 250×150
   ```

2. **If using MUMPS, disable it:**
   ```bash
   sesame-cli simulate --out-dir results  # (remove --use-mumps)
   ```

3. **Run on machine with more RAM** or reduce problem size.

### Plotting Issues on Headless Server

**Symptom:** Missing plots or blank PNG files

**Causes & Solutions:**

```bash
# 1. Ensure Agg backend is set
export MPLBACKEND=Agg
sesame-cli plot sys.gzip --what v --out potential.png

# 2. Check file was created
ls -lh potential.png

# 3. Verify image is valid (not corrupted)
file potential.png  # should show: PNG image data, ...

# 4. Debug with verbose logging
sesame-cli plot sys.gzip --what v --out potential.png --debug 2>debug.log
```

### Files Not Saving

**Symptom:** No output files created, but no error

**Debug:**

```bash
# 1. Check directory exists
mkdir -p ./results

# 2. Verify write permissions
touch ./results/test.txt && rm ./results/test.txt

# 3. Run with full paths
sesame-cli ivcurve --out /full/path/to/results/iv --debug

# 4. Capture error output
sesame-cli ivcurve --out results/iv 2>error.log
cat error.log
```

### Slow Performance

**Issue:** CLI commands take unexpectedly long

**Optimizations:**

```bash
# Fastest (coarse mesh, loose tolerance)
sesame-cli ivcurve --nx 80 --tol 1e-4 --out results_fast

# Balanced (default options)
sesame-cli ivcurve --out results

# Accurate (fine mesh, strict tolerance)
sesame-cli ivcurve --nx 250 --tol 1e-7 --maxiter 500 --out results_accurate
```

---

## Integration Guide

### GitHub Actions CI/CD

```yaml
name: Sesame Simulations

on: [push, pull_request]

jobs:
  simulate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install Sesame
      run: |
        cd sesame
        pip install -e .
        pip install numpy scipy matplotlib
    
    - name: Run simulations
      run: |
        # Parametric study
        for V_MAX in 0.8 1.0 1.2; do
          sesame-cli ivcurve --npoints 10 --vmax $V_MAX \
            --out results_vmax${V_MAX}
        done
    
    - name: Upload results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: simulation-results
        path: results_*.npz
```

### Docker Integration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y gcc gfortran libopenblas-dev

# Clone and install Sesame
RUN git clone https://github.com/usnistgov/sesame.git
WORKDIR /app/sesame
RUN pip install -e .

# Default command
ENTRYPOINT ["sesame-cli"]
CMD ["--help"]
```

**Usage:**

```bash
docker build -t sesame-cli .
docker run sesame-cli ivcurve --npoints 5 --out results
docker run -v $(pwd):/data sesame-cli ivcurve --out /data/results
```

### Slurm Batch Job

```bash
#!/bin/bash
#SBATCH --job-name=sesame_sims
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G

cd /path/to/sesame

# Export backend for headless operation
export MPLBACKEND=Agg

# Run parameter sweep
for T in 250 300 350 400; do
  sesame-cli simulate \
    --nx 150 --length 3e-4 \
    --donor-density 1e17 --acceptor-density 1e15 \
    --voltage-loop --loop-npoints 15 --loop-max 1.0 \
    --out-dir results_T${T}K &
done

wait
```

Submit with: `sbatch job.sh`

---

## FAQ

### Q: Do I need the GUI to use the CLI?

**A:** No. The CLI is completely independent. However, the GUI is useful for:
  - Visualizing systems interactively
  - Testing parameters before running batch simulations
  - Saving `.ini` configs for use with `run-config`

### Q: Can I use the CLI on a headless server (no GUI, no display)?

**A:** Yes, completely. All plotting is headless (PNG output). Set `export MPLBACKEND=Agg` if needed.

### Q: How do I run 100 simulations in parallel?

**A:** Use GNU Parallel or xargs:
  ```bash
  seq 1 100 | xargs -P 8 -I {} sesame-cli simulate --out-dir result_{} ...
  ```
  This runs 8 parallel jobs. Adjust `-P` for your hardware.

### Q: What's the difference between `simulate` and the individual `build`, `solve`, and `analyze` commands?

**A:** 
- Use **individual commands** for step-by-step workflows (inspect between steps, modify system, etc.)
- Use **`simulate`** for end-to-end automation (build + voltage loop in one call)

### Q: How do I handle convergence problems?

**A:** See [Troubleshooting & Diagnostics](#troubleshooting--diagnostics) section. Start with:
  ```bash
  sesame-cli simulate --htpy 5 --tol 1e-5 --maxiter 500 ...
  ```

### Q: Can I do 2D simulations?

**A:** Yes. Use `--ny > 1`:
  ```bash
  sesame-cli simulate --nx 150 --ny 100 --length 3e-4 --width 1e-4 ...
  ```

### Q: How do I extract numerical data programmatically?

**A:** Use NumPy to load `.npz` files:
  ```python
  import numpy as np
  data = np.load('iv_results_IV_summary.npz')
  voltages = data['voltage']
  currents = data['current']
  ```

### Q: What file formats are supported?

**A:**
- `.gzip` — Sesame system objects (serialized with pickle)
- `.npz` — NumPy archives (IV curves, analysis results)
- `.json` — Configuration files
- `.ini` — GUI configuration files (from `run-config`)
- `.png` — Plot output

### Q: How do I cite Sesame in publications?

**A:** See the main [Sesame repository](https://github.com/usnistgov/sesame) for citation information.

---

## Closing Notes

The Sesame CLI brings the full power of the Sesame simulator to command-line and batch workflows. Combine with:

- **Python scripts** for analysis and visualization
- **Shell scripts** for automation and parametric studies
- **CI/CD pipelines** for continuous validation
- **HPC systems** for large-scale simulations
- **Jupyter notebooks** for interactive exploration

For detailed physics questions, see the [Sesame documentation](https://sesame.readthedocs.io).

Happy simulating! 🚀
