"""
Multi-parameter sweep engine for Sesame.
Takes a JSON configuration defining parameters to sweep and runs the simulations.
"""

import json
import argparse
import os
import numpy as np
import logging
import itertools
import copy
from sesame.api import SesameAPI
from sesame.utils import save_sim

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_nested_val(data, path):
    """Access nested dictionary/list using a dot-separated path."""
    keys = path.split('.')
    for key in keys:
        if isinstance(data, list):
            data = data[int(key)]
        else:
            data = data[key]
    return data

def set_nested_val(data, path, value):
    """Set value in nested dictionary/list using a dot-separated path."""
    keys = path.split('.')
    for key in keys[:-1]:
        if isinstance(data, list):
            data = data[int(key)]
        else:
            data = data[key]

    last_key = keys[-1]
    if isinstance(data, list):
        data[int(last_key)] = value
    else:
        data[last_key] = value

def run_sweep(config_path, export_csv=False):
    with open(config_path, 'r') as f:
        config = json.load(f)

    out_dir = config.get('out_dir', 'sweep_results')
    os.makedirs(out_dir, exist_ok=True)

    # Configure file logging
    file_handler = logging.FileHandler(os.path.join(out_dir, 'sweep.log'))
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    base_config = config.get('base_config', {})
    sweep_params = config.get('sweep', [])
    voltage_loop = config.get('voltage_loop', [0.0])
    out_dir = config.get('out_dir', 'sweep_results')

    os.makedirs(out_dir, exist_ok=True)

    # Prepare parameter combinations
    param_names = []
    param_values = []

    for p in sweep_params:
        param_names.append(p['parameter'])
        if 'values' in p:
            param_values.append(p['values'])
        elif 'range' in p:
            r = p['range']
            vals = np.linspace(r['start'], r['stop'], r.get('num', 10))
            param_values.append(vals.tolist())
        else:
            logger.error(f"Missing values or range for parameter {p['parameter']}")
            return

    combinations = list(itertools.product(*param_values))
    logger.info(f"Starting sweep with {len(combinations)} combinations")

    results_summary = []

    for idx, combo in enumerate(combinations):
        logger.info(f"Combination {idx+1}/{len(combinations)}: {dict(zip(param_names, combo))}")

        # Create specific config
        current_config = copy.deepcopy(base_config)
        for name, val in zip(param_names, combo):
            set_nested_val(current_config, name, val)

        # Build and run
        api = SesameAPI(use_mumps=config.get('use_mumps', False))
        try:
            api.build_system(current_config)
            eq = api.solve_equilibrium(tol=config.get('tol', 1e-6))
            if not eq:
                logger.error(f"Equilibrium failed for combination {idx}")
                results_summary.append({'params': dict(zip(param_names, combo)), 'status': 'failed', 'error': 'equilibrium'})
                continue

            iv_results = []
            for v in voltage_loop:
                sol = api.solve_at_voltage(v, tol=config.get('tol', 1e-6))
                if sol:
                    metrics = api.get_metrics()
                    iv_results.append({'v': v, 'j': metrics['current']})
                    # Save individual simulation
                    # Name includes combination index and voltage index
                    filename = os.path.join(out_dir, f"sim_combo{idx}_v{v:.2f}.gzip")
                    api.save(filename)
                    if export_csv:
                        api.export_csv(filename.replace('.gzip', '.csv'))
                else:
                    logger.error(f"Solver failed for combination {idx} at {v} V")
                    iv_results.append({'v': v, 'j': None})

            results_summary.append({
                'combo_idx': idx,
                'params': dict(zip(param_names, combo)),
                'status': 'success',
                'iv': iv_results
            })

        except Exception as e:
            logger.exception(f"Unexpected error in combination {idx}")
            results_summary.append({'params': dict(zip(param_names, combo)), 'status': 'error', 'error': str(e)})

    # Save summary report
    summary_path = os.path.join(out_dir, 'sweep_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(results_summary, f, indent=2)

    # Save as CSV for easier spreadsheet integration
    csv_summary_path = os.path.join(out_dir, 'sweep_summary.csv')
    try:
        import csv
        with open(csv_summary_path, 'w', newline='') as csvfile:
            # Dynamically determine columns
            fieldnames = param_names + ['voltage', 'current', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for res in results_summary:
                if res['status'] == 'success':
                    for iv in res['iv']:
                        row = copy.deepcopy(res['params'])
                        row['voltage'] = iv['v']
                        row['current'] = iv['j']
                        row['status'] = 'success'
                        writer.writerow(row)
                else:
                    row = copy.deepcopy(res['params'])
                    row['status'] = res['status']
                    writer.writerow(row)
        logger.info(f"CSV summary saved to {csv_summary_path}")
    except Exception as e:
        logger.error(f"Could not save CSV summary: {e}")

    logger.info(f"Sweep complete. Summary saved to {summary_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sesame Parametric Sweep Engine")
    parser.add_argument('config', help="Path to sweep configuration JSON file")
    parser.add_argument('--export-csv', action='store_true', help="Export individual simulations to CSV")
    args = parser.parse_args()
    run_sweep(args.config, export_csv=args.export_csv)
