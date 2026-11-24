from pathlib import Path
from datetime import datetime

import os
import requests
import logging as log

from app.frontend.utils import get_logger


class RaspberryController:
    logger: log.Logger

    def __init__(
        self,
        url: str = "127.0.0.1",
        port: int = 5003,
        img_dir: str = "Photos",
    ):
        self._url = url
        self.port = port
        self.logger = get_logger(f"RPI-{url}")
        self.img_dir = Path(img_dir)
        os.makedirs(img_dir, exist_ok=True)

    @property
    def url(self) -> str:
        return f"{self._url}:{self.port}"

    @url.setter
    def url(self, address: str):
        self._url, self.port = address.split(":")

    def capture_photo(self, filename: str | None = None) -> Path | None:
        try:
            r = requests.post(f"http://{self.url}/capture", timeout=30)
        except Exception as e:
            self.logger.error(f"Sygnał nie dotarł do Malinki! Przyczyna: {e}")
            return None
        if r.status_code != 200:
            self.logger.error("Unexpected error")
            return None

        if filename is None:
            filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        path = self.img_dir / filename
        with open(path, "wb") as f:
            f.write(r.content)
        return path

    def health_check(self) -> bool:
        try:
            r = requests.get(f"http://{self.url}/health", timeout=10)
            return r.status_code == 200
        except Exception:
            return False
    
    def check_version(self) -> dict | None:
        try:
            res = requests.get(f"http://{self.url}/health", timeout=15)
            if res.status_code == 200:
                return res.json()
            
        except Exception:
            pass
        return None


#---- Do testowania ----
if __name__ == "__main__":
    log.basicConfig(level=log.DEBUG)
    rpi_c = RaspberryController("127.0.0.1", 5003)
    print("Bumped" if rpi_c.health_check() else "Bump failed :(")
