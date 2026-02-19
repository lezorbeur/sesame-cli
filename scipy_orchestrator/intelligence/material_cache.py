from typing import Optional, Any, Dict
from scipy_orchestrator.storage.database import SessionLocal, MaterialCache
from scipy_orchestrator.core.models import MaterialProperties
import logging

logger = logging.getLogger(__name__)

class LocalMaterialCache:
    def get(self, name: str) -> Optional[MaterialProperties]:
        db = SessionLocal()
        try:
            cached = db.query(MaterialCache).filter(MaterialCache.name == name).first()
            if cached:
                logger.info(f"Cache hit for material: {name}")
                return MaterialProperties(**cached.properties)
            return None
        finally:
            db.close()

    def set(self, name: str, properties: MaterialProperties):
        db = SessionLocal()
        try:
            cached = db.query(MaterialCache).filter(MaterialCache.name == name).first()
            if cached:
                cached.properties = properties.model_dump()
            else:
                new_entry = MaterialCache(name=name, properties=properties.model_dump())
                db.add(new_entry)
            db.commit()
            logger.info(f"Cached material: {name}")
        finally:
            db.close()
