from scipy_orchestrator.core.models import FullSimulationRequest, SystemConfig
from sesame.api import SesameAPI
from sesame.utils import make_safe_callable
import numpy as np

class SesameAdapter:
    """
    Adapter class for Sesame 2.0 simulation engine.

    Translates engine-agnostic FullSimulationRequest objects into
    Sesame-specific API calls.
    """
    def __init__(self, request: FullSimulationRequest):
        """
        Initializes the adapter with a simulation request.

        Args:
            request (FullSimulationRequest): The validated simulation parameters.
        """
        self.request = request
        self.api = SesameAPI(use_mumps=request.simulation.use_mumps)

    def _prepare_sesame_config(self) -> dict:
        """
        Translate FullSimulationRequest to the dict expected by SesameAPI.

        Returns:
            dict: Configuration dictionary for Sesame Builder.
        """
        s = self.request.system

        sesame_config = {
            'nx': s.nx,
            'length': s.length,
            'periodic': s.periodic,
            'T': s.T,
            'materials': [],
            'donors': [],
            'acceptors': [],
            'defects': [],
            'contacts': {
                'left': s.contacts.left,
                'right': s.contacts.right,
                'left_wf': s.contacts.left_wf,
                'right_wf': s.contacts.right_wf,
                'surface_recomb': s.contacts.surface_recomb
            },
            'generation': {}
        }

        if s.ny > 1:
            sesame_config['ny'] = s.ny
            sesame_config['width'] = s.width

        # Materials
        for m in s.materials:
            m_dict = m.model_dump()
            if m.location:
                # Need to translate string location to lambda
                # In build_system of API, it handles x_less/x_greater if passed in dict
                # Let's ensure the API can handle general string locations if we improve it
                # For now we use the existing logic in build_system
                pass
            sesame_config['materials'].append(m_dict)

        # Doping
        for d in s.doping:
            # Handle location string
            loc_func = lambda pos: True
            if d.location:
                # Use x, y directly as variables for the user
                if s.ny == 1:
                    # In 1D, builder passes pos as a single array of x
                    loc_func = make_safe_callable(d.location, ('x',))
                else:
                    # In 2D, builder passes pos as (x_array, y_array)
                    loc_func = make_safe_callable(d.location, ('x', 'y'))

            d_entry = {'density': d.density, 'location': loc_func}
            if d.type == 'donor':
                sesame_config['donors'].append(d_entry)
            else:
                sesame_config['acceptors'].append(d_entry)

        # Defects
        for df in s.defects:
            sesame_config['defects'].append(df.model_dump())

        # Generation
        g = s.generation
        if g.type == 'exponential':
            sesame_config['generation'] = {'type': 'exponential', 'phi': g.phi, 'alpha': g.alpha}
        elif g.type == 'custom':
            sesame_config['generation'] = {'type': 'custom', 'expr': g.expr}

        return sesame_config

    def run(self) -> dict:
        """
        Execute the simulation and return results summary.

        This method performs the following steps:
        1. Build the physical system.
        2. Solve for thermal equilibrium.
        3. Sweep through the requested bias voltages.

        Returns:
            dict: A summary of simulation results (J-V points, status).
        """
        cfg = self._prepare_sesame_config()
        self.api.build_system(cfg)

        p = self.request.simulation
        eq = self.api.solve_equilibrium(tol=p.tol, maxiter=p.maxiter, htpy=p.htpy)

        if not eq:
            return {"status": "failed", "error": "Equilibrium convergence failed"}

        iv_data = []
        last_profiles = None
        for v in p.voltages:
            sol = self.api.solve_at_voltage(v, tol=p.tol, maxiter=p.maxiter, htpy=p.htpy)
            if sol:
                m = self.api.get_metrics()
                profiles = self.api.get_profiles()
                iv_data.append({"v": v, "j": m['current']})
                last_profiles = profiles
            else:
                iv_data.append({"v": v, "j": None, "error": "Convergence failed"})

        return {
            "status": "success",
            "iv_curve": iv_data,
            "profiles": last_profiles,
            "system_summary": {
                "nx": self.api.system.nx,
                "dimension": self.api.system.dimension
            }
        }
