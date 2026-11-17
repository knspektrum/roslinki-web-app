from pathlib import Path

import streamlit as st

from app import STATIC_FOLDER, PAGES_FOLDER
from app.frontend import pages

#---- WHAT DOES THAT DO ----
# with open(static / "style.css") as f:
#     st.markdown(f"<style id='vapor-css'>{f.read()}</style>", unsafe_allow_html=True)
#---- END WHAT DOES THAT DO ----

def launch_webpage():
    
    st.logo(STATIC_FOLDER / "SpektrumLogoLight.svg")
    
    for name, content in pages.pages:
        title, icon = content
        
        st.Page(
            page = PAGES_FOLDER / name,
            title= title,
            icon= icon
        )
    pg = st.navigation(
        pages= pages.pages,
        position= "top"
    )
    pg.run()