import streamlit as st

from app.logic.shared import get_shared
from app.frontend.components.time_series_plot import time_series
from app.database.connection import SESSION
from app.database.models import Measurements
from app import EXPECTED_SERVICE_VERSION


st.set_page_config(layout="wide")
st.title("🌱 Plant Chamber Dashboard")


def get_latest_sensor_data(chamber_name: str, config):
    """Retrieves latest sensor measurements from memory or database."""
    with config.lock:
        if config.last_temperature is not None:
            return {
                "temperature": config.last_temperature,
                "humidity": config.last_humidity,
                "light_intensity": config.last_light_intensity,
                "date": config.last_sensor_reading_time,
            }
    
    # Fallback to database
    try:
        with SESSION() as session:
            latest = (
                session.query(Measurements)
                .where(Measurements.chamber_name == chamber_name)
                .order_by(Measurements.date.desc())
                .first()
            )
            if latest:
                return {
                    "temperature": latest.temperature,
                    "humidity": latest.humidity,
                    "light_intensity": latest.light_intensity,
                    "date": latest.date,
                }
    except Exception:
        pass
    return None


#---- Per Chamber ----
@st.fragment(run_every=10)
def chamber_status():
    configs = get_shared()
    cols = st.columns(len(configs))
    for col, (chamber_name, config) in zip(cols, configs.items()):
        with col:
            with st.container(border=True):
                st.subheader(f"📟 {chamber_name}")
                st.caption(f"Address: `{config.raspberry.url}`")

                health_data = config.raspberry.check_version()
                is_online = False
                if health_data is None:
                    #---- 🔴 Nie działa ----
                    st.error(
                        f"🔴 **Offline**\n\nCannot reach `{config.raspberry.url}`",
                        icon="🚨",
                    )
                elif health_data.get("version") != EXPECTED_SERVICE_VERSION:
                    #---- 🟡 Malina ma starą wersje ----
                    rpi_ver = health_data.get("version", "unknown")
                    st.warning(
                        f"🟡 **Outdated**\n\nRPi running `v{rpi_ver}`, expected `v{EXPECTED_SERVICE_VERSION}`",
                        icon="⚠️",
                    )
                elif not health_data.get("arduino_connected", False):
                    #---- 🟠 Malina działa, ale Arduino już nie ----
                    st.warning(
                        "🟠 **Arduino Disconnected**\n\nPi is online, but no micro-controller detected on USB.",
                        icon="🔌",
                    )
                else:
                    #---- 🟢 Malina i Arduino są połączone ----
                    is_online = True
                    port = health_data.get("port") or "/dev/ttyUSB0"
                    ver = health_data.get("version")
                    st.success(
                        f"🟢 **Connected**\n\nRPi `v{ver}`, Arduino `{port}` OK",
                        icon="✅",
                    )

                #---- LIVE SENSORS ----
                st.markdown("#### 🌡️ Live Sensors")
                sensor_data = get_latest_sensor_data(chamber_name, config)
                if sensor_data:
                    m_col1, m_col2, m_col3 = st.columns(3)
                    t_val = sensor_data["temperature"]
                    h_val = sensor_data["humidity"]
                    l_val = sensor_data["light_intensity"]
                    m_col1.metric("Temperature", f"{t_val:.1f} °C" if t_val is not None else "--")
                    m_col2.metric("Humidity", f"{h_val:.1f} %" if h_val is not None else "--")
                    m_col3.metric("Light", f"{l_val:.0f} lx" if l_val is not None else "--")
                    if sensor_data.get("date"):
                        time_str = sensor_data["date"].strftime("%H:%M:%S")
                        st.caption(f"Last reading: `{time_str}` (refreshes every 10s)")
                else:
                    st.info("No sensor readings received yet.")

                st.divider()

                #---- LIGHTING STATUS ----
                st.markdown("#### 💡 Lighting Status")
                is_magenta_on = getattr(config, "is_light_on", False) and is_online
                is_white_on = getattr(config, "is_camera_light_on", False) and is_online

                l_col1, l_col2 = st.columns(2)
                with l_col1:
                    if not is_online:
                        st.markdown("**🟣 Magenta (Grow):** :gray[Offline]")
                    elif is_magenta_on:
                        st.markdown("**🟣 Magenta (Grow):** :green[**● ON**]")
                    else:
                        st.markdown("**🟣 Magenta (Grow):** :gray[**○ OFF**]")

                with l_col2:
                    if not is_online:
                        st.markdown("**⚪ White (Camera):** :gray[Offline]")
                    elif is_white_on:
                        st.markdown("**⚪ White (Camera):** :green[**● ON**]")
                    else:
                        st.markdown("**⚪ White (Camera):** :gray[**○ OFF**]")

chamber_status()

#---- Sensory----
st.divider()
st.subheader("Jakiś wykres")
time_series()
