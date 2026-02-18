import typer
import json
from pathlib import Path
from typing import Optional
from scipy_orchestrator.intelligence.layer import IntentExtractor, MaterialEnricher
from scipy_orchestrator.intelligence.material_cache import LocalMaterialCache
from scipy_orchestrator.core.models import FullSimulationRequest, MaterialProperties, SystemConfig, SimulationParams
from scipy_orchestrator.adapters.sesame_adapter import SesameAdapter
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="SCIPY-ORCHESTRATOR CLI")
console = Console()

@app.command()
def extract(text: str):
    """Extract structured data from a natural language prompt."""
    extractor = IntentExtractor()
    extracted = extractor.extract(text)
    console.print("[bold blue]Extracted data:[/bold blue]")
    console.print_json(data=extracted)

@app.command()
def run(config_file: Path):
    """Run a simulation from a JSON configuration file."""
    with open(config_file, 'r') as f:
        data = json.load(f)

    try:
        request = FullSimulationRequest.model_validate(data)
        adapter = SesameAdapter(request)
        console.print("[yellow]Running simulation...[/yellow]")
        results = adapter.run()

        if results['status'] == 'success':
            console.print("[bold green]Simulation complete![/bold green]")
            table = Table(title="IV Curve")
            table.add_column("Voltage (V)", justify="right")
            table.add_column("Current (A/cm^2)", justify="right")

            for point in results['iv_curve']:
                table.add_row(f"{point['v']:.2f}", f"{point['j']:.2e}" if point['j'] else "FAILED")

            console.print(table)
        else:
            console.print(f"[bold red]Simulation failed: {results['error']}[/bold red]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@app.command()
def quick_sim(material: str, thickness_nm: float = 200, voltage: float = 0.5):
    """Run a quick simulation for a given material and thickness."""
    cache = LocalMaterialCache()
    mat_props = cache.get(material)

    if not mat_props:
        console.print(f"[yellow]Material {material} not in cache. Fetching...[/yellow]")
        enricher = MaterialEnricher()
        mat_props = enricher.fetch_properties(material)
        if mat_props:
            cache.set(material, mat_props)

    if not mat_props:
        console.print(f"[red]Material {material} not found in database.[/red]")
        return

    # Build a simple request (PN junction for better convergence)
    request = FullSimulationRequest(
        system=SystemConfig(
            length=thickness_nm * 1e-7,
            materials=[mat_props],
            doping=[
                {"type": "donor", "density": 1e17, "location": f"x < {thickness_nm*0.2e-7}"},
                {"type": "acceptor", "density": 1e15, "location": f"x >= {thickness_nm*0.2e-7}"}
            ]
        ),
        simulation=SimulationParams(voltages=[0.0, voltage])
    )

    adapter = SesameAdapter(request)
    console.print(f"[yellow]Running quick sim for {material} at {thickness_nm}nm...[/yellow]")
    results = adapter.run()
    console.print_json(data=results)

if __name__ == "__main__":
    app()
