from collections.abc import Callable
import streamlit as st


import requests  # DODANE: Import biblioteki do komunikacji sieciowej

from client.utils import get_logger
from logic import get_shared
from logic.chamber import Field

def callback_generator(chamber: str, reader: list[Field]) -> Callable:
    logger = get_logger(chamber)
    config = get_shared()[chamber]

    def callback():
        form_values = {
            field.name: st.session_state[f"{chamber}-{field.name}"] for field in reader
        }
        rpi_address = st.session_state[f"{chamber}-rpi-address"]
        
        with config:
            config.set(**form_values)
            config.raspberry.url = rpi_address
            config.save()
            
        logger.info(
            "Parameters has been changed to:\n\t"
            + "\n\t".join(
                f"{field.fullname}: {form_values[field.name]}" for field in reader
            )
        )


    return callback


def config_form(chamber: str):
    
    
    
    
    config = get_shared()[chamber]
    
    with st.form(f"{chamber}-settings"):
        with config:
            reader = config.reader()
            
            rpi_address = config.raspberry.url

        n = (len(reader) + 1) // 2
        cols = st.columns([1, 1])
        with cols[0]:
            for field in reader[:n]:
                st.number_input(
                    field.fullname,
                    value=field.value,
                    placeholder="Type a number...",
                    key=f"{chamber}-{field.name}",
                )
            st.text_input(
                "Raspberry PI address",
                value=rpi_address,
                placeholder="10.28.146.80:5003",
                key=f"{chamber}-rpi-address",
            )
        with cols[1]:
            for field in reader[n:]:
                st.number_input(
                    field.fullname,
                    value=field.value,
                    placeholder="Type a number...",
                    key=f"{chamber}-{field.name}",
                )
            
        submitted = st.form_submit_button(
            "Save", on_click=callback_generator(chamber, reader)
        )
        
        if submitted:
            st.success("Settings saved and sent to device successfully!", icon="✅")