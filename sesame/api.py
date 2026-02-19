"""
High-level API for Sesame.
This module provides a simplified interface for building, running, and analyzing simulations.
"""

import sesame
from .utils import save_sim, load_sim, make_safe_callable, export_to_csv
from .solvers import Solver
from .analyzer import Analyzer
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

class SesameAPI:
    def __init__(self, use_mumps=False):
        self.solver = Solver(use_mumps=use_mumps)
        self.system = None
        self.solution = None
        self.periodic = True

    def build_system(self, config):
        """
        Build a Sesame system from a configuration dictionary.

        Parameters
        ----------
        config : dict
            System configuration (grid, materials, donors, acceptors, defects, contacts, generation).
        """
        # grid
        if 'xpts' in config:
            xpts = np.array(config['xpts'])
        else:
            nx = config.get('nx', 150)
            length = config.get('length', 3e-4)
            xpts = np.linspace(0, length, nx)

        ypts = np.array([0])
        if 'ypts' in config:
            ypts = np.array(config['ypts'])
        elif 'ny' in config:
            ny = config['ny']
            width = config.get('width', 1e-4)
            ypts = np.linspace(0, width, ny)

        self.periodic = config.get('periodic', True)
        self.T = config.get('T', 300.0)
        self.system = sesame.Builder(xpts, ypts, T=self.T, periodic=self.periodic)

        # materials
        for mat in config.get('materials', []):
            loc_str = mat.get('location', '')
            if not loc_str:
                self.system.add_material(mat)
            else:
                # Basic spatial support: x_less, x_greater
                if 'x_less' in mat:
                    thresh = mat['x_less']
                    self.system.add_material(mat, location=lambda pos: pos < thresh)
                elif 'x_greater' in mat:
                    thresh = mat['x_greater']
                    self.system.add_material(mat, location=lambda pos: pos > thresh)
                else:
                    self.system.add_material(mat)

        # doping
        for d in config.get('donors', []):
            self.system.add_donor(d['density'], location=d.get('location', lambda pos: True))
        for a in config.get('acceptors', []):
            self.system.add_acceptor(a['density'], location=a.get('location', lambda pos: True))

        # defects
        for df in config.get('defects', []):
            loc = df['location']
            if isinstance(loc, str):
                if loc.startswith('point:'):
                    loc = float(loc.split(':')[1])
                elif loc.startswith('line:'):
                    pts = loc.split(':')[1].split(';')
                    p1 = tuple(float(x) for x in pts[0].split(','))
                    p2 = tuple(float(x) for x in pts[1].split(','))
                    loc = [p1, p2]

            self.system.add_defects(loc, df['density'], df['sigma_e'],
                                    sigma_h=df.get('sigma_h'), E=df.get('energy'))

        # contacts
        if 'contacts' in config:
            c = config['contacts']
            self.system.contact_type(c.get('left', 'Ohmic'), c.get('right', 'Ohmic'),
                                     left_wf=c.get('left_wf'), right_wf=c.get('right_wf'))
            if 'surface_recomb' in c:
                self.system.contact_S(*c['surface_recomb'])
        else:
            # Default Ohmic contacts
            self.system.contact_type('Ohmic', 'Ohmic')

        # default surface recombination if not set
        if not hasattr(self.system, 'Scn'):
            self.system.contact_S(1e7, 0, 0, 1e7) # Default as in examples

        # generation
        if 'generation' in config:
            g = config['generation']
            if g.get('type') == 'exponential':
                phi = g.get('phi', 1e17)
                alpha = g.get('alpha', 2.3e4)
                self.system.generation(lambda x, y=None: phi * alpha * np.exp(-alpha * x))
            elif g.get('type') == 'custom' and 'expr' in g:
                if self.system.dimension == 1:
                    f = make_safe_callable(g['expr'], ('x',))
                else:
                    f = make_safe_callable(g['expr'], ('x', 'y'))
                self.system.generation(f)

        return self.system

    def solve_equilibrium(self, tol=1e-6, maxiter=300, htpy=1):
        """Solve for thermal equilibrium."""
        if self.system is None:
            raise ValueError("System not built. Call build_system first.")

        guess = self.solver.make_guess(self.system)
        res = self.solver.solve(self.system, compute='Poisson', guess=guess,
                                tol=tol, maxiter=maxiter, htp=htpy, periodic_bcs=self.periodic)
        if res:
            self.solution = res
        return res

    def solve_at_voltage(self, voltage, tol=1e-6, maxiter=300, htpy=1):
        """Solve at a specific applied voltage."""
        if self.solver.equilibrium is None:
            self.solve_equilibrium(tol=tol, maxiter=maxiter, htpy=htpy)

        nx = self.system.nx
        s = [nx-1 + j*nx for j in range(self.system.ny)]
        q = 1 if self.system.rho[nx-1] < 0 else -1

        vapp = voltage / self.system.scaling.energy

        # Prepare guess from previous solution or equilibrium
        if self.solution is None:
            self.solution = {'efn': np.zeros_like(self.solver.equilibrium),
                             'efp': np.zeros_like(self.solver.equilibrium),
                             'v': np.copy(self.solver.equilibrium)}

        self.solution['v'][s] = self.solver.equilibrium[s] + q*vapp

        res = self.solver.solve(self.system, compute='all', guess=self.solution,
                                tol=tol, maxiter=maxiter, htp=htpy, periodic_bcs=self.periodic)
        if res:
            self.solution = res
        return res

    def run_iv_curve(self, voltages, tol=1e-6, maxiter=300, htpy=1):
        """Run an IV curve for the given voltages."""
        j_vals = []
        for v in voltages:
            logger.info(f"Solving at {v} V")
            res = self.solve_at_voltage(v, tol=tol, maxiter=maxiter, htpy=htpy)
            if res:
                metrics = self.get_metrics()
                j_vals.append(metrics['current'])
            else:
                logger.error(f"Solver failed at {v} V")
                j_vals.append(np.nan)
        return np.array(j_vals)

    def get_metrics(self):
        """Extract key metrics from the current solution."""
        if self.system is None or self.solution is None:
            return None

        az = Analyzer(self.system, self.solution)
        current = az.full_current() * self.system.scaling.current

        return {
            'current': current,
            'max_potential': np.max(self.solution['v']),
            'min_potential': np.min(self.solution['v'])
        }

    def get_profiles(self):
        """Extract full physical profiles along the x-direction."""
        if self.system is None or self.solution is None:
            return None

        az = Analyzer(self.system, self.solution)
        vt = self.system.scaling.energy

        # In 2D, we take a slice at y=0 or mid-width
        if self.system.ny > 1:
            y_idx = self.system.ny // 2
            sites = np.arange(y_idx * self.system.nx, (y_idx + 1) * self.system.nx)
        else:
            sites = np.arange(self.system.nx)

        x = self.system.xpts

        # Band diagram
        # Ec = -q(V + affinity) -> - (V + bl) in dimensionless energy units * vt
        ec = -vt * (self.solution['v'][sites] + self.system.bl[sites])
        ev = -vt * (self.solution['v'][sites] + self.system.bl[sites] + self.system.Eg[sites])
        efn = vt * self.solution['efn'][sites]
        efp = vt * self.solution['efp'][sites]

        # Carrier densities
        n = az.electron_density()[sites]
        p = az.hole_density()[sites]

        # Recombination rates
        r_srh = az.bulk_srh_rr()[sites] * self.system.scaling.generation
        r_aug = az.auger_rr()[sites] * self.system.scaling.generation
        r_rad = az.radiative_rr()[sites] * self.system.scaling.generation
        r_tot = az.total_rr()[sites] * self.system.scaling.generation

        return {
            'x': x.tolist(),
            'ec': ec.tolist(),
            'ev': ev.tolist(),
            'efn': efn.tolist(),
            'efp': efp.tolist(),
            'n': n.tolist(),
            'p': p.tolist(),
            'r_srh': r_srh.tolist(),
            'r_aug': r_aug.tolist(),
            'r_rad': r_rad.tolist(),
            'r_tot': r_tot.tolist()
        }

    def save(self, filename):
        """Save the system and current solution."""
        if self.system and self.solution:
            save_sim(self.system, self.solution, filename)
            logger.info(f"Saved simulation to {filename}")

    def export_csv(self, filename):
        """Export current solution to CSV."""
        if self.system and self.solution:
            export_to_csv(self.system, self.solution, filename)
            logger.info(f"Exported to CSV: {filename}")

    def load(self, filename):
        """Load a system and solution."""
        self.system, self.solution = load_sim(filename)
        # update solver equilibrium if available in the loaded solution
        if self.solution and 'v' in self.solution:
            # Note: This is a bit hacky as we don't know for sure if it's equilibrium
            # but usually we load a solved system.
            pass
        return self.system, self.solution
