from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class ChamberParameters(Base):
    __tablename__ = "chamber_parameters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)
    chamber_name: Mapped[str] = mapped_column(index=True)

    date: Mapped[datetime]
    
    rpi_address: Mapped[str] = mapped_column(default="127.0.0.1:5003")
    
    # --- NOWE KOLUMNY HARMONOGRAMU ---
    light_start_hour: Mapped[int]
    light_start_minute: Mapped[int]      # DODANE: minuty startu
    light_duration_hours: Mapped[int]
    light_duration_minutes: Mapped[int]  # DODANE: minuty trwania
    pump_start_hour: Mapped[int]
    pump_duration_seconds: Mapped[int]
    
    # --- POZOSTAWIONE KOLUMNY CZASOWE ---
    camera_frequency: Mapped[int]
    sensor_delay: Mapped[int]

    def __repr__(self) -> str:
        # Używamy formatowania :02d, żeby np. minuta 5 wyświetlała się jako "05"
        return (f"<{self.date} | {self.chamber_name} | "
                f"Światło: {self.light_start_hour:02d}:{self.light_start_minute:02d} przez {self.light_duration_hours}h i {self.light_duration_minutes}m | "
                f"Pompa: {self.pump_start_hour}:00 przez {self.pump_duration_seconds}s | "
                f"Kamera: co {self.camera_frequency}s | Czujniki: co {self.sensor_delay}s>")

class Measurements(Base):
    __tablename__ = "measurements"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)
    chamber_name: Mapped[str] = mapped_column(index=True)

    date: Mapped[datetime]
    temperature: Mapped[float]
    humidity: Mapped[float]
    light_intensity: Mapped[float]

    def __repr__(self) -> str:
        return f"<{self.date} | {self.chamber_name} | temperature: {self.temperature}, humidity={self.humidity}, light intensity={self.light_intensity}>"