import os
from pathlib import Path

import logging as log

#---- LOGGING ----

log.basicConfig(
    filemode= "a",
    filename= "main_log.log",
    level= log.DEBUG,
    # format= "",
)

#---- END LOGGING ----

#---- PATHS ----

ROOT_FOLDER = Path(__file__).resolve().parent.parent
STATIC_FOLDER = Path(ROOT_FOLDER / "app" / "frontend" / "static")
FRONTEND_FOLDER = Path(ROOT_FOLDER / "app" / "frontend")
PAGES_FOLDER = Path(ROOT_FOLDER / "app" / "frontend" / "pages")
DATABASE_FILE = Path(ROOT_FOLDER / "data" / "database.db")

#---- END PATHS ----

#---- CONSTANTS ----

CHAMBER_NAMES = ["Chamber-1", "Chamber-2"]
EXPECTED_SERVICE_VERSION = "0.1.0"
SERVICE_VERSION = ... # Znajduje się w pliku ./services/rpi_service.py ; 

#---- END CONSTANTS ----