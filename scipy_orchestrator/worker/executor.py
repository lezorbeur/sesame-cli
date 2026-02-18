import multiprocessing
import time
import os
import signal
from typing import Any, Callable, Dict
from scipy_orchestrator.core.models import FullSimulationRequest
from scipy_orchestrator.adapters.sesame_adapter import SesameAdapter
import logging

logger = logging.getLogger(__name__)

def _run_adapter(request_dict: dict, queue: multiprocessing.Queue):
    """Function to run in a separate process."""
    try:
        # Import inside to ensure fresh state if needed
        from scipy_orchestrator.core.models import FullSimulationRequest
        from scipy_orchestrator.adapters.sesame_adapter import SesameAdapter

        request = FullSimulationRequest.model_validate(request_dict)
        adapter = SesameAdapter(request)
        results = adapter.run()
        queue.put({"status": "success", "results": results})
    except Exception as e:
        queue.put({"status": "failed", "error": str(e)})

class IsolatedExecutor:
    def __init__(self, timeout_sec: int = 600, mem_limit_mb: int = 1024):
        self.timeout = timeout_sec
        self.mem_limit = mem_limit_mb

    def execute(self, request_dict: dict) -> Dict[str, Any]:
        """Runs the simulation in an isolated process with timeout."""
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=_run_adapter, args=(request_dict, queue))

        start_time = time.time()
        process.start()

        # Monitor loop
        while process.is_alive():
            if time.time() - start_time > self.timeout:
                logger.error(f"Simulation timed out after {self.timeout}s")
                process.terminate()
                process.join()
                return {"status": "failed", "error": "timeout"}

            # Simple polling
            time.sleep(1)

            if not queue.empty():
                break

        if not queue.empty():
            res = queue.get()
            process.join()
            return res

        process.join()
        return {"status": "failed", "error": "Unknown failure in isolated process"}
