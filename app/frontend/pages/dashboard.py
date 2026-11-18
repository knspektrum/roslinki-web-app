import streamlit as st
from app.frontend.components import time_series

st.set_page_config(layout="wide")
st.title("Dashboard")

# TODO: Improve (redesign) dashboard
time_series()
