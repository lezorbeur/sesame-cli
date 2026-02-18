from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union, Dict, Literal

class MaterialProperties(BaseModel):
    name: Optional[str] = None
    Nc: float = Field(..., description="Effective DOS conduction band [cm^-3]")
    Nv: float = Field(..., description="Effective DOS valence band [cm^-3]")
    Eg: float = Field(..., description="Band gap [eV]")
    affinity: float = Field(..., description="Electron affinity [eV]")
    epsilon: float = Field(..., description="Relative permittivity")
    mu_e: float = Field(..., description="Electron mobility [cm^2/V/s]")
    mu_h: float = Field(..., description="Hole mobility [cm^2/V/s]")
    tau_e: float = Field(default=1e-9, description="Electron lifetime [s]")
    tau_h: float = Field(default=1e-9, description="Hole lifetime [s]")
    Et: float = Field(default=0, description="Trap energy level relative to intrinsic [eV]")
    location: Optional[str] = Field(default="", description="Spatial condition for this material (e.g. x < 1e-5)")

class DopingConfig(BaseModel):
    type: Literal["donor", "acceptor"]
    density: float = Field(..., gt=0, description="Doping density [cm^-3]")
    location: Optional[str] = Field(default="", description="Spatial condition for doping")

class DefectConfig(BaseModel):
    location: str = Field(..., description="Point or line location, e.g. 'point:1e-5'")
    density: float = Field(..., description="Defect density [cm^-2 or cm^-3]")
    sigma_e: float = Field(..., description="Electron capture cross-section [cm^2]")
    sigma_h: Optional[float] = None
    energy: Optional[float] = None

class ContactConfig(BaseModel):
    left: Literal["Ohmic", "Schottky", "Neutral"] = "Ohmic"
    right: Literal["Ohmic", "Schottky", "Neutral"] = "Ohmic"
    left_wf: Optional[float] = None
    right_wf: Optional[float] = None
    surface_recomb: List[float] = Field(default_factory=lambda: [1e7, 1e7, 1e7, 1e7], description="SnL, SpL, SnR, SpR")

class GenerationConfig(BaseModel):
    type: Literal["none", "exponential", "custom"] = "none"
    phi: float = Field(default=0, description="Photon flux [cm^-2s^-1]")
    alpha: float = Field(default=0, description="Absorption coefficient [cm^-1]")
    expr: Optional[str] = None

class SystemConfig(BaseModel):
    nx: int = Field(default=150, ge=10)
    ny: int = Field(default=1, ge=1)
    length: float = Field(default=3e-4, gt=0, description="Length [cm]")
    width: Optional[float] = Field(default=1e-4, description="Width [cm] for 2D")
    periodic: bool = True
    materials: List[MaterialProperties]
    doping: List[DopingConfig] = []
    defects: List[DefectConfig] = []
    contacts: ContactConfig = Field(default_factory=ContactConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)

class SimulationParams(BaseModel):
    voltages: List[float] = Field(default_factory=lambda: [0.0])
    tol: float = 1e-6
    maxiter: int = 300
    htpy: int = 1
    use_mumps: bool = False

class FullSimulationRequest(BaseModel):
    system: SystemConfig
    simulation: SimulationParams
    metadata: Dict[str, str] = {}
