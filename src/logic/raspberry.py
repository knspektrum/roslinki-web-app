import logging
import requests
import os
from pathlib import Path

from datetime import datetime, timedelta
from client.utils import get_logger


class RaspberryController:
    logger: logging.Logger

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

    def bump(self) -> bool:
        try:
            r = requests.post(f"{self.url}/bump", timeout=30)
        except Exception:
            return False
        return r.status_code == 200


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    rpi_c = RaspberryController("127.0.0.1", 5003)
    print("Bumped" if rpi_c.bump() else "Bump failed :(")
