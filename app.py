import streamlit as st

# Komponenten importieren
from frontend import render_sidebar, render_main_content

# 1. Seitenkonfiguration (Muss immer die erste Streamlit-Anweisung sein!)
st.set_page_config(
    page_title="Stadtplaner Schweiz",
    page_icon="🏙️",
    layout="wide"
)

# 2. Header der App
st.title("🏙️ Interaktiver Stadtplaner")
st.markdown("Finde den perfekten Wohnort in der Schweiz basierend auf deinen persönlichen Gewichtungen.")

# 3. Sidebar rendern und Eingaben abfangen
inputs = render_sidebar()

# 4. Hauptbereich rendern und Eingaben übergeben
render_main_content(inputs)