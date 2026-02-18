# SCIPY-ORCHESTRATOR 🔬

Production-grade simulation orchestrator for semiconductor physics labs.

## Architecture 🏛️
1. **Interface Layer**: Streamlit web app + Typer CLI.
2. **Intelligence Layer**: LangChain extraction + Pydantic validation + Material Cache.
3. **Orchestration Layer**: Celery worker + Redis queue.
4. **Simulation Layer**: Sesame 2.0 Adapter.

## Quickstart (Dockerized) 🚀

1.  **Clone the repo**
2.  **Configure environment**
    Create a `.env` file:
    ```env
    OPENAI_API_KEY=your_key
    MP_API_KEY=your_key
    REDIS_URL=redis://redis:6379/0
    DATABASE_URL=sqlite:///./data/orchestrator.db
    ```
3.  **Build and Run**
    ```bash
    docker-compose up --build
    ```
4.  **Smoke Test**
    Open `http://localhost:8501`.
    Type in Chatbot: `"Simulate a GaAs homojunction of 2µm at 300K"`.
    Observe: Material props loaded -> Mesh Preview -> Run Simulation -> Result Plotly.

## Development Setup (Local) 💻

```bash
pip install -r requirements.txt
pip install -e .
python check_system.py
```

## Scientific Validation ✅

- **Benchmark**: Run `python benchmark_gaas.py`. Success criteria: Error < 10^-10 vs manual Sesame scripts.
- **Robustness**: Pydantic models in `scipy_orchestrator/core/models.py` enforce physical limits (T > 0K, etc.).
- **Isolation**: Simulations run in subprocesses with timeouts and resource monitoring via `IsolatedExecutor`.

## Directory Map 🗺️

- `scipy_orchestrator/storage/`: SQLite DB models and Material Cache.
- `scipy_orchestrator/core/preview_mesh.py`: Plotly-compatible mesh extraction.
- `scipy_orchestrator/worker/executor.py`: Process isolation logic.
- `scipy_orchestrator/notifications/`: Firebase push engine.
