import streamlit as st

from frontend import render_sidebar, render_main_content

st.set_page_config(
    page_title="Wohnscore Zürich",
    page_icon="🏙️",
    layout="wide"
)

st.title("🏙️ Interaktiver Wohnscore-Planer")
st.markdown("Finde den perfekten Wohnort in Zürich basierend auf deinen persönlichen Gewichtungen.")

inputs = render_sidebar()

render_main_content(inputs)