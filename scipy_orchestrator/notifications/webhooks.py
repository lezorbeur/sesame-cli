import requests
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def dispatch_webhook(url: str, payload: Dict[str, Any]):
    """
    Sends a POST request to a given URL with simulation results.
    """
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Webhook dispatched to {url}")
    except Exception as e:
        logger.error(f"Failed to dispatch webhook to {url}: {e}")
