# Sesame Automation & Workflow Guide

This guide describes the high-level automation tools developed for Sesame, enabling researchers to run complex parametric sweeps, manage data pipelines, and visualize results without direct source code modification.

---

## 1. High-Level API (`sesame.api`)

The `SesameAPI` class provides a simplified Python interface to the core Sesame engine.

### Usage Example

```python
from sesame.api import SesameAPI

# 1. Define configuration
config = {
    'nx': 150,
    'length': 3e-4,
    'materials': [{'Nc': 8e17, 'Eg': 1.5, ...}],
    'donors': [{'density': 1e17}],
    'generation': {'type': 'exponential', 'phi': 1e17, 'alpha': 2.3e4}
}

# 2. Initialize API and build system
api = SesameAPI()
api.build_system(config)

# 3. Solve equilibrium
api.solve_equilibrium()

# 4. Run voltage sweep
voltages = [0.0, 0.2, 0.4, 0.6, 0.8]
currents = api.run_iv_curve(voltages)

# 5. Export results
api.export_csv("results.csv")
```

---

## 2. Multi-Parameter Sweep Engine (`cmd/sweep.py`)

The sweep engine allows you to vary multiple parameters (e.g., thickness, bandgap, doping) across ranges defined in a JSON file.

### Configuration Format (`sweep_config.json`)

```json
{
  "base_config": {
    "nx": 100,
    "length": 3e-4,
    "materials": [{"Nc":8e17, "Eg":1.5, ...}],
    "donors": [{"density": 1e17}]
  },
  "sweep": [
    {
      "parameter": "materials.0.Eg",
      "range": {"start": 1.1, "stop": 1.8, "num": 5}
    },
    {
      "parameter": "donors.0.density",
      "values": [1e16, 1e17, 1e18]
    }
  ],
  "voltage_loop": [0.0, 0.5, 0.8],
  "out_dir": "my_sweep"
}
```

### Running a Sweep

```bash
python3 cmd/sweep.py sweep_config.json --export-csv
```

**Features:**
- **Robustness:** If one simulation fails to converge, the engine logs the error and proceeds to the next combination.
- **Centralized Data:** Results are saved in the `out_dir` with a `sweep_summary.json` and `sweep_summary.csv`.
- **Logs:** Detailed progress is saved in `sweep.log`.

---

## 3. Data Pipeline & I/O

Sesame now supports structured data export to CSV, facilitating integration with Excel, Origin, or other analysis tools.

- **`export_to_csv(sys, result, filename)`**: Utility function to export a full simulation mesh and results to CSV.
- **Summary Files**: The sweep engine automatically generates consolidated CSV summaries containing parameter values and corresponding currents.

---

## 4. Visualization Tool (`cmd/visualize_sweep.py`)

Quickly visualize the results of a parametric sweep without writing plotting code.

### Usage

```bash
python3 cmd/visualize_sweep.py sweep_results/sweep_summary.json \
  --x-param materials.0.Eg \
  --voltage 0.5 \
  --out trend_plot.png
```

This command generates a plot showing how the current density at 0.5V changes as the bandgap (`Eg`) of the first material is varied.

---

## 5. Security Best Practices

- **Pickle Security**: Sesame's `.gzip` files use Python's `pickle` module. Only load files from trusted sources.
- **Data Exchange**: For automated pipelines, prefer using the `.json` and `.csv` export features for safer data transfer between different stages of your workflow.
