"""
Visualization tool for Sesame sweep results.
Generates comparative plots from a sweep summary.
"""

import json
import argparse
import os
import matplotlib.pyplot as plt
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def visualize_sweep(summary_path, x_param=None, voltage=None, out_file='sweep_plot.png'):
    with open(summary_path, 'r') as f:
        results = json.load(f)

    # Filter for successful simulations
    successful = [r for r in results if r['status'] == 'success']
    if not successful:
        logger.error("No successful simulations found in summary.")
        return

    # If x_param not specified, use the first swept parameter
    if x_param is None:
        x_param = list(successful[0]['params'].keys())[0]

    # If voltage not specified, use the first one available
    if voltage is None:
        voltage = successful[0]['iv'][0]['v']

    logger.info(f"Plotting current vs {x_param} at {voltage} V")

    x_vals = []
    y_vals = []

    for res in successful:
        x_vals.append(res['params'][x_param])
        # Find current at specified voltage
        current = None
        for iv in res['iv']:
            if abs(iv['v'] - voltage) < 1e-6:
                current = iv['j']
                break
        y_vals.append(current)

    # Sort by x_vals
    sorted_indices = np.argsort(x_vals)
    x_vals = np.array(x_vals)[sorted_indices]
    y_vals = np.array(y_vals)[sorted_indices]

    plt.figure(figsize=(10, 6))
    plt.plot(x_vals, y_vals, 'o-', linewidth=2)
    plt.xlabel(x_param)
    plt.ylabel('Current Density [A/cm^2]')
    plt.title(f'Sweep Results: Current vs {x_param} at {voltage} V')
    plt.grid(True)

    plt.savefig(out_file)
    logger.info(f"Plot saved to {out_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Visualize Sesame sweep results")
    parser.add_argument('summary', help="Path to sweep_summary.json")
    parser.add_argument('--x-param', help="Parameter to use for X axis")
    parser.add_argument('--voltage', type=float, help="Voltage at which to compare currents")
    parser.add_argument('--out', default='sweep_plot.png', help="Output plot filename")

    args = parser.parse_args()
    visualize_sweep(args.summary, args.x_param, args.voltage, args.out)
