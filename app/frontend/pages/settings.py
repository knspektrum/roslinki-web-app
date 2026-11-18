import streamlit as st

from app.config import CHAMBER_NAMES
from app.frontend.components import config_form
from app.frontend.components.authorization import after_login


st.set_page_config(layout="centered")
st.title("Chamber settings")


def settings():
    for name, tab in zip(CHAMBER_NAMES, st.tabs(CHAMBER_NAMES)):
        with tab:
            config_form(name)


roles = after_login(settings, required_role="maintainer")
