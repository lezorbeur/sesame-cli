from scipy_orchestrator.core.models import SystemConfig
import sesame
import numpy as np

def generate_mesh_preview(config: SystemConfig):
    """
    Instantiates a sesame.Builder and returns mesh nodes for visualization.
    """
    # Simplified system build for preview
    xpts = np.linspace(0, config.length, config.nx)
    ypts = np.array([0])
    if config.ny > 1:
        ypts = np.linspace(0, config.width or 1e-4, config.ny)

    # We can also return doping info or material regions by evaluating them at nodes
    # For now, let's just return coordinates

    return {
        "x": xpts.tolist(),
        "y": ypts.tolist(),
        "dimension": 2 if config.ny > 1 else 1,
        "nodes_count": len(xpts) * len(ypts)
    }

def get_doping_preview(config: SystemConfig):
    """Evaluates doping at each node for visualization."""
    # This would be more intensive but useful
    pass
