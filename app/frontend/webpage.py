import streamlit as st
from pathlib import Path

from app.frontend import pages
from app import STATIC_FOLDER, PAGES_FOLDER, FRONTEND_FOLDER

#---- WHAT DOES THAT DO ----
# with open(static / "style.css") as f:
#     st.markdown(f"<style id='vapor-css'>{f.read()}</style>", unsafe_allow_html=True)
#---- END WHAT DOES THAT DO ----

def launch_webpage():
    st.logo(STATIC_FOLDER / "SpektrumLogoLight.svg")
    css_path = FRONTEND_FOLDER / "css" / "style.css"
    
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style id='vapor-css'>{f.read()}</style>", unsafe_allow_html=True)
    page_list = [
        st.Page(
            page=PAGES_FOLDER / filename,
            title=details[0],
            icon=details[1] if details[1] else None,
        )
        for filename, details in pages.pages.items()
    ]
    
    pg = st.navigation(pages=page_list, position="top")
    pg.run()
