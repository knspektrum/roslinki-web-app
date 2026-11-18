import sys
from streamlit.web import cli as stcli

from app.logic.shared import start_chamber_manager, get_shared
from app.frontend.webpage import launch_webpage


def run():
    start_chamber_manager(get_shared())
    launch_webpage()
    
if __name__ == "__main__":
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        in_streamlit = get_script_run_ctx() is not None
        
    except Exception:
        in_streamlit = False
        
    if in_streamlit:
        run()
    else:
        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())