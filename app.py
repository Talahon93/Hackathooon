import streamlit as st

# Komponenten importieren
from frontend import render_sidebar, render_main_content

st.set_page_config(
    page_title="Wohnscore Zürich",
    page_icon="🏙️",
    layout="wide"
)

# 2. Header der App
st.title("🏙️ Interaktiver Wohnscore-Planer")
st.markdown("Finde den perfekten Wohnort in Zürich basierend auf deinen persönlichen Gewichtungen.")

# 3. Sidebar rendern und Eingaben abfangen
inputs = render_sidebar()

# 4. Hauptbereich rendern und Eingaben übergeben
render_main_content(inputs)