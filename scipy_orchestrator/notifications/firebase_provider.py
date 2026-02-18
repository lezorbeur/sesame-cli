import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class FirebaseNotificationProvider:
    def __init__(self):
        self.enabled = False
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging

            cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self.enabled = True
                logger.info("Firebase Admin SDK initialized.")
            else:
                logger.warning("Firebase credentials not found. Notifications will be logged only.")
        except ImportError:
            logger.error("firebase-admin not installed.")

    def send_push(self, token: str, title: str, body: str, data: Optional[dict] = None):
        if not self.enabled:
            logger.info(f"[MOCK PUSH] To: {token} | {title}: {body}")
            return

        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data,
            token=token,
        )
        try:
            response = messaging.send(message)
            logger.info(f"Successfully sent message: {response}")
        except Exception as e:
            logger.error(f"Error sending Firebase message: {e}")
