from celery import Celery
import os

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

app = Celery('scipy_orchestrator',
             broker=REDIS_URL,
             backend=REDIS_URL,
             include=['scipy_orchestrator.orchestration.tasks'])

app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
