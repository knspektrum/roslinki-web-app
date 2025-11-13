import logging
import requests
import os
from pathlib import Path

from client.utils import get_logger


class RaspberryController:
    logger: logging.Logger

    def __init__(
        self,
        url: str = "127.0.0.1",
        port: int = 5003,
        img_dir: str | Path | None = None,
    ):
        self._url = url
        self.port = port
        self.logger = get_logger(f"RPI-{url}")
        if img_dir is None:
            img_dir = Path("data", "photos")
        self.img_dir = Path(img_dir)
        os.makedirs(img_dir, exist_ok=True)

    @property
    def url(self) -> str:
        return f"{self._url}:{self.port}"

    @url.setter
    def url(self, address: str):
        if ":" in address:
            self._url, self.port = address.split(":")
        else:
            self._url = address

    def capture_photo(self, filename: str | None = None) -> Path | None:
        try:
            r = requests.post(f"http://{self.url}/capture", timeout=30)
        except Exception:
            return None
        if r.status_code != 200:
            self.logger.error("Unexpected error")
            return None

        if filename is None:
            # TODO: auto generation using current datetime
            filename = "test.jpg"

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
