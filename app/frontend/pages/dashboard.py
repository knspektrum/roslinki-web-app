import streamlit as st

from app.logic.shared import get_shared
from app.frontend.components.time_series_plot import time_series
from app import EXPECTED_SERVICE_VERSION


st.set_page_config(layout="wide")
st.title("🌱 Plant Chamber Dashboard")

#---- Per Chamber ----
configs = get_shared()
cols = st.columns(len(configs))
for col, (chamber_name, config) in zip(cols, configs.items()):
    with col:
        with st.container(border=True):
            st.subheader(f"📟 {chamber_name}")
            st.caption(f"Address: `{config.raspberry.url}`")

            health_data = config.raspberry.check_version()
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
                port = health_data.get("port") or "/dev/ttyUSB0"
                ver = health_data.get("version")
                st.success(
                    f"🟢 **Connected**\n\nRPi `v{ver}`, Arduino `{port}` OK",
                    icon="✅",
                )

#---- Sensory----
st.divider()
st.subheader("Jakiś wykres")
time_series()