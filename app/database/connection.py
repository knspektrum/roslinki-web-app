from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app import DATABASE_FILE

Base = declarative_base()

from app.database import models


DB = create_engine(f"sqlite:///{DATABASE_FILE}")
SESSION = sessionmaker(DB)

Base.metadata.create_all(DB)