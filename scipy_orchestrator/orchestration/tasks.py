from .celery_app import app
from scipy_orchestrator.core.models import FullSimulationRequest
from scipy_orchestrator.worker.executor import IsolatedExecutor
from scipy_orchestrator.notifications.firebase_provider import FirebaseNotificationProvider
from scipy_orchestrator.storage.database import SessionLocal, SimulationHistory, init_db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize database
init_db()

@app.task(bind=True)
def run_simulation_task(self, request_dict: dict):
    """
    Asynchronous task to run a simulation with isolation and persistence.
    """
    db = SessionLocal()
    history_entry = db.query(SimulationHistory).filter(SimulationHistory.task_id == self.request.id).first()

    if not history_entry:
        # Create history entry if it doesn't exist (though usually created by caller)
        history_entry = SimulationHistory(task_id=self.request.id, status='running')
        db.add(history_entry)
        db.commit()
    else:
        history_entry.status = 'running'
        db.commit()

    try:
        executor = IsolatedExecutor(timeout_sec=1200) # 20 min
        logger.info(f"Starting isolated simulation task {self.request.id}")

        exec_res = executor.execute(request_dict)

        if exec_res['status'] == 'success':
            results = exec_res['results']
            history_entry.status = 'completed'
            history_entry.summary_json = results
        else:
            history_entry.status = 'failed'
            history_entry.summary_json = {"error": exec_res.get('error')}

        history_entry.completed_at = datetime.utcnow()
        db.commit()

        # Notifications
        notify = FirebaseNotificationProvider()
        token = request_dict.get('metadata', {}).get('push_token')
        if token:
            notify.send_push(token, "Simulation Complete", f"Task {self.request.id} finished with status {history_entry.status}")

        return history_entry.summary_json
    except Exception as e:
        logger.exception(f"Simulation task {self.request.id} critical failure")
        history_entry.status = 'error'
        db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
