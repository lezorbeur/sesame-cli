from scipy_orchestrator.core.models import MaterialProperties, SystemConfig, FullSimulationRequest, SimulationParams, DopingConfig
from scipy_orchestrator.adapters.sesame_adapter import SesameAdapter
from scipy_orchestrator.intelligence.layer import MaterialEnricher
import numpy as np
import sesame

def run_benchmark():
    print("--- Benchmark de Concordance GaAs ---")

    # 1. Manual Sesame Run
    x = np.linspace(0, 2e-4, 150)
    sys_manual = sesame.Builder(x)

    # GaAs properties from our DB
    enricher = MaterialEnricher()
    gaas = enricher.fetch_properties("GaAs").model_dump()
    gaas.pop('name', None)
    gaas.pop('location', None)

    sys_manual.add_material(gaas)
    sys_manual.add_donor(1e17, lambda pos: pos < 0.4e-4)
    sys_manual.add_acceptor(1e15, lambda pos: pos >= 0.4e-4)
    sys_manual.contact_type('Ohmic', 'Ohmic')
    sys_manual.contact_S(1e7, 1e7, 1e7, 1e7)

    sol_manual = sesame.solve(sys_manual, compute='Poisson', verbose=False)
    sol_manual = sesame.solve(sys_manual, guess=sol_manual, verbose=False)

    az_manual = sesame.Analyzer(sys_manual, sol_manual)
    j_manual = az_manual.full_current() * sys_manual.scaling.current

    # 2. Orchestrator Adapter Run
    req = FullSimulationRequest(
        system=SystemConfig(
            length=2e-4,
            materials=[enricher.fetch_properties("GaAs")],
            doping=[
                DopingConfig(type="donor", density=1e17, location="x < 0.4e-4"),
                DopingConfig(type="acceptor", density=1e15, location="x >= 0.4e-4")
            ]
        ),
        simulation=SimulationParams(voltages=[0.0])
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
