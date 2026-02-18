import os, sys, redis, requests
import logging

# Ensure local modules are importable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scipy_orchestrator.core.models import MaterialProperties, SystemConfig, FullSimulationRequest

def check_system():
    print("--- Diagnostic Système SCIPY-ORCHESTRATOR ---")

    # 1. Vérification des clés API
    keys = ["OPENAI_API_KEY", "MP_API_KEY", "FIREBASE_CONFIG"]
    for key in keys:
        status = "OK" if os.getenv(key) else "MANQUANT"
        print(f"[API] {key}: {status}")

    # 2. Vérification Redis (File d'attente)
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url, socket_timeout=2)
        r.ping()
        print("[INFRA] Redis : CONNECTÉ")
    except Exception:
        print("[INFRA] Redis : ÉCHEC DE CONNEXION")

    # 3. Test de connectivité Materials Project
    try:
        url = "https://next-gen.materialsproject.org"
        res = requests.get(url, timeout=5)
        print(f"[DATA] Materials Project API : {'ALIVE' if res.status_code==200 else 'DOWN'}")
    except:
        print("[DATA] Materials Project API : INDISPONIBLE")

    # 4. Test d'intégrité du solveur Sesame
    try:
        import sesame
        from sesame.api import SesameAPI
        print(f"[PHYSICS] Sesame Engine OK")
    except ImportError:
        print("[PHYSICS] Sesame Engine : NON INSTALLÉ")

    # 5. Validation Pydantic
    try:
        # Rejet aberration : T < 0K
        SystemConfig(T=-10, materials=[])
        print("[MODEL] Validation Pydantic : ÉCHEC (Aberration non rejetée)")
    except Exception as e:
        print("[MODEL] Validation Pydantic : OK (Aberration rejetée)")

if __name__ == "__main__":
    check_system()
