from scipy_orchestrator.core.models import MaterialProperties, SystemConfig, FullSimulationRequest, SimulationParams, DopingConfig
from scipy_orchestrator.adapters.sesame_adapter import SesameAdapter
from scipy_orchestrator.intelligence.layer import MaterialEnricher
from sesame.api import SesameAPI
import numpy as np
import sesame

def run_benchmark():
    print("--- Benchmark de Concordance GaAs (0.5V) ---")

    enricher = MaterialEnricher()
    gaas_props = enricher.fetch_properties("GaAs")

    # 1. Manual API Run
    api_manual = SesameAPI()
    cfg_manual = {
        'nx': 150,
        'length': 2e-4,
        'materials': [gaas_props.model_dump()],
        'donors': [{'density': 1e17, 'location': lambda pos: pos < 0.4e-4}],
        'acceptors': [{'density': 1e15, 'location': lambda pos: pos >= 0.4e-4}],
        'contacts': {'left': 'Ohmic', 'right': 'Ohmic', 'surface_recomb': [1e7, 1e7, 1e7, 1e7]}
    }
    api_manual.build_system(cfg_manual)
    api_manual.solve_equilibrium()
    api_manual.solve_at_voltage(0.5)
    j_manual = api_manual.get_metrics()['current']

    # 2. Orchestrator Adapter Run
    req = FullSimulationRequest(
        system=SystemConfig(
            length=2e-4,
            materials=[gaas_props],
            doping=[
                DopingConfig(type="donor", density=1e17, location="x < 0.4e-4"),
                DopingConfig(type="acceptor", density=1e15, location="x >= 0.4e-4")
            ],
            contacts={'left': 'Ohmic', 'right': 'Ohmic', 'surface_recomb': [1e7, 1e7, 1e7, 1e7]}
        ),
        simulation=SimulationParams(voltages=[0.5])
    )

    adapter = SesameAdapter(req)
    res_adapter = adapter.run()
    j_adapter = res_adapter['iv_curve'][0]['j']

    # 3. Comparison
    error = abs(j_manual - j_adapter)
    print(f"[BENCHMARK] J_manual: {j_manual:.6e} A/cm^2")
    print(f"[BENCHMARK] J_adapter: {j_adapter:.6e} A/cm^2")
    print(f"[BENCHMARK] Écart: {error:.6e}")

    if error < 1e-10:
        print("[BENCHMARK] RÉSULTAT : SUCCÈS")
        return True
    else:
        print("[BENCHMARK] RÉSULTAT : ÉCHEC")
        return False

if __name__ == "__main__":
    run_benchmark()
