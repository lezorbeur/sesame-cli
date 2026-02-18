from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class SimulationHistory(Base):
    __tablename__ = 'simulation_history'

    id = Column(Integer, primary_key=True)
    task_id = Column(String, unique=True, index=True)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Input params
    material_name = Column(String)
    thickness_cm = Column(Float)
    config_json = Column(JSON)

    # Results path
    results_path = Column(String, nullable=True)
    summary_json = Column(JSON, nullable=True)

class MaterialCache(Base):
    __tablename__ = 'material_cache'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    properties = Column(JSON)
    last_updated = Column(DateTime, default=datetime.utcnow)

DB_PATH = os.environ.get('DATABASE_URL', 'sqlite:///./orchestrator.db')
if DB_PATH.startswith('sqlite:///./'):
    db_dir = os.path.dirname(DB_PATH.replace('sqlite:///./', ''))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
engine = create_engine(DB_PATH)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    except:
        db.close()
        raise
