from sesame.api import SesameAPI
import numpy as np

config = {
    'nx': 100,
    'length': 3e-4,
    'materials': [{'Nc':8e17, 'Nv':1.8e19, 'Eg':1.5, 'affinity':3.9, 'epsilon':9.4,
            'mu_e':100, 'mu_h':100, 'tau_e':10e-9, 'tau_h':10e-9, 'Et':0}],
    'donors': [{'density': 1e17}],
    'acceptors': [{'density': 1e15}],
    'generation': {'type': 'exponential', 'phi': 1e17, 'alpha': 2.3e4}
}

api = SesameAPI()
sys = api.build_system(config)
print(f"System built: nx={sys.nx}, dimension={sys.dimension}")

eq = api.solve_equilibrium()
if eq:
    print("Equilibrium solved.")
else:
    print("Equilibrium failed.")
    exit(1)

sol = api.solve_at_voltage(0.5)
if sol:
    metrics = api.get_metrics()
    print(f"Solved at 0.5V. Current: {metrics['current']:.2e} A/cm^2")

api.save("api_test.gzip")
print("Saved api_test.gzip")
