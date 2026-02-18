from .celery_app import app
from scipy_orchestrator.core.models import FullSimulationRequest
from scipy_orchestrator.adapters.sesame_adapter import SesameAdapter
import logging

logger = logging.getLogger(__name__)

@app.task(bind=True)
def run_simulation_task(self, request_dict: dict):
    """
    Asynchronous task to run a simulation.
    Takes a serialized FullSimulationRequest.
    """
    try:
        request = FullSimulationRequest.model_validate(request_dict)
        adapter = SesameAdapter(request)

        logger.info(f"Starting simulation task {self.request.id}")
        results = adapter.run()

        # In a real app, notify user via Firebase here
        # send_push_notification(request.metadata.get('user_id'), "Simulation complete!")

        return results
    except Exception as e:
        logger.exception(f"Simulation task {self.request.id} failed")
        return {"status": "failed", "error": str(e)}
