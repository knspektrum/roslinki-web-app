import os
import streamlit as st

from app.frontend.components.label_image import image_labeler
from app.frontend.components.authorization import after_login

st.title("Labelling")
st.set_page_config(layout="wide")


def main():
    image_labeler(os.path.join("data", "example"))


after_login(main, "maintainer")
