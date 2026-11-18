from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app import DATABASE_FILE
from app.database import models

Base = declarative_base()

DB = create_engine(f"sqlite:///{DATABASE_FILE}")
SESSION = sessionmaker(DB)

Base.metadata.create_all(DB)