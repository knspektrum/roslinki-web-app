from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import threading
import time
import requests
from typing import Any
from client.utils import get_logger
from logic import ChamberParameters, SESSION
from logic.database import Measurements
from .arduino import BaseArduinoController, create_arduino_controller
from .raspberry import RaspberryController

@dataclass
class Field:
    name: str
    fullname: str
    value: Any
    min_value: int | None = None  # Dodane: limit dolny
    max_value: int | None = None  # Dodane: limit górny


class ChamberConfig:
    def __init__(
        self,
        name: str,
        light_start_hour: int = 8,
        light_start_minute: int = 0,
        light_duration_hours: int = 12,
        light_duration_minutes: int = 0,
        pump_start_hour: int = 9,
        pump_duration_seconds: int = 5,
        sensor_delay: int = 60,
        camera_frequency: int = 3600,
    ):
        self.lock = threading.RLock()
        self.name = name
        
        # Nowe pola harmonogramu
        self.light_start_hour = light_start_hour
        self.light_start_minute = light_start_minute
        self.light_duration_hours = light_duration_hours
        self.light_duration_minutes = light_duration_minutes
        self.pump_start_hour = pump_start_hour
        self.pump_duration_seconds = pump_duration_seconds
        
        self.sensor_delay = sensor_delay
        self.camera_frequency = camera_frequency

        self.arduino = create_arduino_controller("None")
        self.raspberry = RaspberryController(img_dir=f"{name}-images")


    def reader(self) -> list[Field]:
        return [
            Field("light_start_hour", "Godzina włączenia (0-23)", self.light_start_hour, min_value=0, max_value=23),
            Field("light_start_minute", "Minuta włączenia (0-59)", self.light_start_minute, min_value=0, max_value=59),
            Field("light_duration_hours", "Czas świecenia (godziny)", self.light_duration_hours, min_value=0, max_value=24),
            Field("light_duration_minutes", "Czas świecenia (minuty)", self.light_duration_minutes, min_value=0, max_value=59),
            Field("pump_start_hour", "Godzina włączenia pompy (0-23)", self.pump_start_hour, min_value=0, max_value=23),
            Field("pump_duration_seconds", "Czas pompowania (w sekundach)", self.pump_duration_seconds, min_value=1),
            Field("sensor_delay", "Opóźnienie czujników (w sekundach)", self.sensor_delay, min_value=10),
            Field("camera_frequency", "Częstotliwość zdjęć (w sekundach)", self.camera_frequency, min_value=10),
        ]


    def set(
        self,
        light_start_hour: int | None = None,
        light_start_minute: int | None = None,       # DODANE
        light_duration_hours: int | None = None,
        light_duration_minutes: int | None = None,   # DODANE
        pump_start_hour: int | None = None,
        pump_duration_seconds: int | None = None,
        sensor_delay: int | None = None,
        camera_frequency: int | None = None,
    ) -> None:
        if light_start_hour is not None: self.light_start_hour = light_start_hour
        if light_start_minute is not None: self.light_start_minute = light_start_minute             # DODANE
        if light_duration_hours is not None: self.light_duration_hours = light_duration_hours
        if light_duration_minutes is not None: self.light_duration_minutes = light_duration_minutes # DODANE
        if pump_start_hour is not None: self.pump_start_hour = pump_start_hour
        if pump_duration_seconds is not None: self.pump_duration_seconds = pump_duration_seconds
        if sensor_delay is not None: self.sensor_delay = sensor_delay
        if camera_frequency is not None: self.camera_frequency = camera_frequency

    @classmethod
    def load(cls, name: str) -> "ChamberConfig":
        logger = get_logger(f"Config-{name}")
        with SESSION() as session:
            config: ChamberParameters | None = (
                session.query(ChamberParameters)
                .where(ChamberParameters.chamber_name == name)
                .order_by(ChamberParameters.date.desc())
                .first()
            )
        logger.debug(repr(config))
        if config is None:
            chamber_config = ChamberConfig(name)
            config = chamber_config.to_config_params()
            logger.debug("Config not found, submitting a new one")
            with SESSION() as session:
                session.add(config)
                session.commit()
            return cls.load(name)
        return cls.from_config_params(config)

    def save(self):
        logger = get_logger(f"Config-{self.name}")
        config = self.to_config_params()
        logger.debug(f"Saving configs\n{repr(config)}")
        with SESSION() as session:
            session.add(config)
            session.commit()

    @classmethod
    def from_config_params(cls, parameters: ChamberParameters) -> "ChamberConfig":
        return cls(
            name=parameters.chamber_name,
            light_start_hour=parameters.light_start_hour,
            light_start_minute=parameters.light_start_minute,
            light_duration_hours=parameters.light_duration_hours,
            light_duration_minutes=parameters.light_duration_minutes,
            pump_start_hour=parameters.pump_start_hour,
            pump_duration_seconds=parameters.pump_duration_seconds,
            sensor_delay=parameters.sensor_delay,
            camera_frequency=parameters.camera_frequency,
        )

    def to_config_params(self) -> ChamberParameters:
        return ChamberParameters(
            chamber_name=self.name,
            date=datetime.now(timezone.utc),
            light_start_hour=self.light_start_hour,
            light_start_minute=self.light_start_minute,         # POPRAWIONE (usunięte "s" na końcu)
            light_duration_hours=self.light_duration_hours,
            light_duration_minutes=self.light_duration_minutes,
            pump_start_hour=self.pump_start_hour,
            pump_duration_seconds=self.pump_duration_seconds,
            sensor_delay=self.sensor_delay,
            camera_frequency=self.camera_frequency,
        )

    @property
    def arduino(self):
        return self._arduino

    @arduino.setter
    def arduino(self, arduino_controller: BaseArduinoController):
        if "_arduino" in self.__dict__:
            self._arduino.logger.warning("Detached!")
        self._arduino = arduino_controller
        self._arduino.logger.info(
            f"Attached new arduino controller on: {arduino_controller.port}"
        )

    def __enter__(self):
        self.lock.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.lock.release()

class Chamber:
    def __init__(self, config: ChamberConfig):
        self.config: ChamberConfig = config
        self.logger = get_logger(self.config.name)

        self.is_light_on = False
        self.last_pump_date = None
        
        # TUTAJ MUSI BYĆ SAMO datetime.now()
        self.sensor_next_run = datetime.now()
        self.camera_next_run = datetime.now()

    def _send_to_rpi(self, cmd: str) -> dict | None:
        url = self.config.raspberry.url
        if not url.startswith("http"):
            url = f"http://{url}"
            
        try:
            # Zmienione: Teraz zwracamy odpowiedź w formacie JSON z Malinki
            res = requests.post(f"{url}/arduino", json={"cmd": cmd}, timeout=5)
            self.logger.info(f"Wysłano komendę '{cmd}' do RPi")
            return res.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Błąd wysyłania komendy '{cmd}' do RPi: {e}")
            return None

    def manage_lights(self, current_time: datetime):
        with self.config:
            start_h = self.config.light_start_hour
            start_m = self.config.light_start_minute
            duration_h = self.config.light_duration_hours
            duration_m = self.config.light_duration_minutes
            
        # Przeliczamy czasy na łączną liczbę minut od północy
        start_mins = start_h * 60 + start_m
        duration_mins = duration_h * 60 + duration_m
        current_mins = current_time.hour * 60 + current_time.minute
        
        # Minuta, w której światło ma zgasnąć
        end_mins = (start_mins + duration_mins) % (24 * 60)
        
        # Logika sprawdzania, czy obecnie jest "dzień"
        should_be_on = False
        if start_mins <= end_mins:
            if start_mins <= current_mins < end_mins:
                should_be_on = True
        else: 
            if current_mins >= start_mins or current_mins < end_mins:
                should_be_on = True

        # Jeśli stan faktyczny nie zgadza się ze statusem, przełączamy przekaźnik
        if should_be_on and not self.is_light_on:
            self.logger.info("Harmonogram: Włączam światło")
            self._send_to_rpi("L") 
            self.is_light_on = True
            
        elif not should_be_on and self.is_light_on:
            self.logger.info("Harmonogram: Wyłączam światło")
            self._send_to_rpi("D") 
            self.is_light_on = False

    def manage_pump(self, current_time: datetime):
        with self.config:
            start_hr = self.config.pump_start_hour
            duration_sec = self.config.pump_duration_seconds
            
        current_date = current_time.date()
        
        # Jeśli wybiła odpowiednia godzina, a dziś jeszcze nie podlewano
        if current_time.hour == start_hr and self.last_pump_date != current_date:
            self.logger.info(f"Harmonogram: Odpalam pompę na {duration_sec} sekund")
            self._send_to_rpi(f"P {duration_sec}")
            self.last_pump_date = current_date

    def read_from_sensors(self, add_to_database: bool = False) -> tuple[float, float, float]:
        temperature, humidity, light_intensity = 0.0, 0.0, 0.0
        
        # ODCZYT CZUJNIKÓW Z SIECI ZAMIAST Z KOMPUTERA
        res = self._send_to_rpi("R")
        
        if res and res.get("status") == "ok":
            try:
                # Malinka zwraca nam stringa "22.50,45.00,150.00" - musimy to rozdzielić
                data_string = res.get("response", "")
                parts = data_string.split(",")
                if len(parts) >= 3:
                    temperature = float(parts[0])
                    humidity = float(parts[1])
                    light_intensity = float(parts[2])
            except ValueError:
                self.logger.error("Błąd parsowania danych z czujników!")

        if add_to_database:
            measurement = Measurements(
                chamber_name=self.config.name,
                date=datetime.now(),
                temperature=temperature,
                humidity=humidity,
                light_intensity=light_intensity,
            )
            with SESSION() as session:
                session.add(measurement)
                session.commit()
        return temperature, humidity, light_intensity

    def take_photo(self):
        with self.config:
            self.config.raspberry.capture_photo()

class ChamberManager:
    def __init__(self, configs: dict[str, ChamberConfig]):
        self.chambers = {name: Chamber(config) for name, config in configs.items()}

    def scheduler_loop(self):
        while True:
            # TUTAJ TEŻ MUSI BYĆ SAMO datetime.now()
            current_time = datetime.now() 
            
            for chamber in self.chambers.values():
                # ...
                
                # Zależne od godziny
                chamber.manage_lights(current_time)
                chamber.manage_pump(current_time)
                
                # Zależne od interwału
                if current_time >= chamber.sensor_next_run:
                    chamber.read_from_sensors(add_to_database=True)
                    chamber.sensor_next_run = current_time + timedelta(seconds=chamber.config.sensor_delay)
                    
                if current_time >= chamber.camera_next_run:
                    chamber.take_photo()
                    chamber.camera_next_run = current_time + timedelta(seconds=chamber.config.camera_frequency)
            
            time.sleep(1) # Odpoczynek pętli