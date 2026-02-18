from typing import Dict, Any, Optional
from scipy_orchestrator.core.models import MaterialProperties

class MaterialEnricher:
    """
    Mock implementation of Materials Project / AFLOW integration.
    In a real scenario, this would call external APIs.
    """
    DATABASE = {
        "Si": {
            "Nc": 2.8e19, "Nv": 1.04e19, "Eg": 1.12, "affinity": 4.05,
            "epsilon": 11.7, "mu_e": 1400, "mu_h": 450, "tau_e": 1e-6, "tau_h": 1e-6
        },
        "GaAs": {
            "Nc": 4.4e17, "Nv": 8.1e18, "Eg": 1.42, "affinity": 4.07,
            "epsilon": 12.9, "mu_e": 8500, "mu_h": 400, "tau_e": 1e-8, "tau_h": 1e-8
        },
        "CdTe": {
            "Nc": 8e17, "Nv": 1.8e19, "Eg": 1.5, "affinity": 3.9,
            "epsilon": 9.4, "mu_e": 320, "mu_h": 40, "tau_e": 1e-9, "tau_h": 1e-9
        }
    }

    def fetch_properties(self, material_name: str) -> Optional[MaterialProperties]:
        data = self.DATABASE.get(material_name)
        if data:
            return MaterialProperties(name=material_name, **data)
        return None

class IntentExtractor:
    """
    Translates user natural language into structured data.
    Uses a mock rule-based system for the sandbox, architected for LangChain.
    """
    def extract(self, text: str) -> Dict[str, Any]:
        # Mocking extraction logic
        # Real version would use: langchain.chains.create_extraction_chain
        text = text.lower()
        extracted = {}

        if "si" in text or "silicon" in text:
            extracted["material"] = "Si"
        elif "gaas" in text:
            extracted["material"] = "GaAs"
        elif "cdte" in text:
            extracted["material"] = "CdTe"

        if "200nm" in text:
            extracted["thickness"] = 200e-7 # nm to cm
        elif "500nm" in text:
            extracted["thickness"] = 500e-7

        return extracted
