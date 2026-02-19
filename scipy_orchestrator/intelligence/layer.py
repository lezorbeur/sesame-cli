from typing import Dict, Any, Optional
import re
from scipy_orchestrator.core.models import MaterialProperties

class MaterialEnricher:
    """
    Mock implementation of Materials Project / AFLOW integration.
    In a real scenario, this would call external APIs.
    """
    DATABASE = {
        "Si": {
            "Nc": 2.8e19, "Nv": 1.04e19, "Eg": 1.12, "affinity": 4.05,
            "epsilon": 11.7, "mu_e": 1400, "mu_h": 450, "tau_e": 1e-6, "tau_h": 1e-6,
            "B": 4.73e-15, "Cn": 2.8e-31, "Cp": 9.9e-32, "mass_e": 1.08, "mass_h": 0.81
        },
        "GaAs": {
            "Nc": 4.4e17, "Nv": 8.1e18, "Eg": 1.42, "affinity": 4.07,
            "epsilon": 12.9, "mu_e": 8500, "mu_h": 400, "tau_e": 1e-8, "tau_h": 1e-8,
            "B": 7.2e-10, "Cn": 1e-30, "Cp": 1e-30, "mass_e": 0.067, "mass_h": 0.45
        },
        "CdTe": {
            "Nc": 8e17, "Nv": 1.8e19, "Eg": 1.5, "affinity": 3.9,
            "epsilon": 9.4, "mu_e": 320, "mu_h": 40, "tau_e": 1e-9, "tau_h": 1e-9,
            "B": 2e-10, "Cn": 1e-30, "Cp": 1e-30, "mass_e": 0.11, "mass_h": 0.4
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
    Enhanced with regex to capture physical parameters like gap, thickness, etc.
    """
    def extract(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        extracted = {}

        # Material detection using word boundaries
        if re.search(r"\bsi\b|\bsilicon\b", text_lower):
            extracted["material"] = "Si"
        elif re.search(r"\bgaas\b", text_lower):
            extracted["material"] = "GaAs"
        elif re.search(r"\bcdte\b", text_lower):
            extracted["material"] = "CdTe"
        elif re.search(r"\bsemiconductor\b|\bmaterial\b", text_lower):
            extracted["material"] = "Generic"

        # Thickness detection (nm, um, micron, cm)
        thickness_match = re.search(r"(\d+\.?\d*)\s*(nm|um|µm|micron|cm)", text_lower)
        if thickness_match:
            val = float(thickness_match.group(1))
            unit = thickness_match.group(2)
            if unit == "nm":
                extracted["thickness"] = val * 1e-7
            elif unit in ["um", "µm", "micron"]:
                extracted["thickness"] = val * 1e-4
            elif unit == "cm":
                extracted["thickness"] = val

        # Band gap detection (eV)
        gap_match = re.search(r"(\d+\.?\d*)\s*ev", text_lower)
        if gap_match:
            extracted["Eg"] = float(gap_match.group(1))

        # Doping detection (cm^-3 or cm-3)
        doping_match = re.search(r"(\d+\.?\d*[eE]?[-+]?\d*)\s*cm", text_lower)
        if doping_match:
            extracted["doping_density"] = float(doping_match.group(1))

        return extracted
