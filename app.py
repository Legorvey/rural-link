import streamlit as st

from config import PROJECT_NAME, RESEARCH_TITLE, SCIENTIFIC_ENGINE_IMPLEMENTED

REQUIRED = ["numpy", "scipy", "pandas", "matplotlib", "plotly", "streamlit"]


def check_imports() -> dict[str, bool]:
    import importlib

    status = {}
    for name in REQUIRED:
        try:
            importlib.import_module(name)
            status[name] = True
        except ImportError:
            status[name] = False
    return status


st.set_page_config(page_title=PROJECT_NAME, page_icon="📡")
st.title(PROJECT_NAME)
st.subheader(RESEARCH_TITLE)

status = check_imports()
if all(status.values()):
    st.success("Environment ready: all required packages import successfully.")
else:
    st.error("Missing packages: " + ", ".join(k for k, v in status.items() if not v))

st.warning(
    "The scientific engine is not yet implemented"
    if not SCIENTIFIC_ENGINE_IMPLEMENTED
    else "Engine enabled."
)
st.caption("Phase 01 landing page: no simulation results are shown.")
