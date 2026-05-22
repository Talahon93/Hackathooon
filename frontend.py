import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from map_view import create_interactive_map
from logik import analysiere_standort

def render_sidebar():
    st.sidebar.header("Zieleingabe & Mobilität")

    # NEU: Reset-Button direkt unter der Info-Box
    reset_btn = st.sidebar.button("Ansicht zurücksetzen", use_container_width=True)

    transport_mode = st.sidebar.radio(
        "gewünschtes Fortbewegungsmittel",
        options=["Zu Fuss", "Fahrrad", "Auto"],
        help="Diese Auswahl beeinflusst, ob die Algorithmen Fusswege, Radwege oder Strassen nutzen."
    )

    st.sidebar.divider()
    st.sidebar.header("⚖️ Gewichtungssystem")
    persona = st.sidebar.selectbox(
        "Wähle dein Profil (Persona):",
        options=[
            "Junge Familie mit kleinen Kindern",
            "Studenten WG",
            "Rentnerpaar",
            "Manuell (Eigene Gewichtung)"
        ]
    )
    
    # Dictionary für die Gewichte initialisieren
    weights = {}
    
    # NEU: Logik für die einzelnen Personas
    if persona == "Junge Familie mit kleinen Kindern":
        st.sidebar.markdown("**Voreingestellte Prioritäten für Familien:**")
        st.sidebar.caption("🏫 Schulen: **100** | 🌳 Grünflächen: **100**")
        st.sidebar.caption("🛒 Supermärkte: **75** | 🚆 ÖV & 🏥 Spitäler: **50**")
        st.sidebar.caption("🍽️ Restaurants: **0**")
        
        # Fest definierte Gewichte übergeben
        weights = {"schule": 100, "supermarkt": 75, "park": 100, "oev": 50, "restaurant": 0, "spital": 50}
        
    elif persona == "Studenten WG":
        st.sidebar.markdown("**Voreingestellte Prioritäten für Studenten:**")
        st.sidebar.caption("🚆 ÖV-Anbindung: **100**")
        st.sidebar.caption("🛒 Supermärkte: **50** | 🏫 Schulen & 🌳 Grünflächen: **25**")
        st.sidebar.caption("🍽️ Restaurants: **25** | 🏥 Spitäler: **0**")
        
        weights = {"schule": 25, "supermarkt": 50, "park": 25, "oev": 100, "restaurant": 25, "spital": 0}
        
    elif persona == "Rentnerpaar":
        st.sidebar.markdown("**Voreingestellte Prioritäten für Senioren:**")
        st.sidebar.caption("🚆 ÖV: **100** | 🛒 Supermärkte, 🍽️ Restaurants & 🏥 Spitäler: **75**")
        st.sidebar.caption("🌳 Grünflächen: **50** | 🏫 Schulen: **0**")
        
        weights = {"schule": 0, "supermarkt": 75, "park": 50, "oev": 100, "restaurant": 75, "spital": 75}
        
    elif persona == "Manuell (Eigene Gewichtung)":
        st.sidebar.write("Stelle deine Gewichte individuell ein (0-100):")
        # Die bewährten Slider mit den 25er-Schritten erscheinen NUR hier
        weight_schulen = st.sidebar.slider("Schulen", 0, 100, 50, step=25)
        weight_supermaerkte = st.sidebar.slider("Supermärkte", 0, 100, 50, step=25)
        weight_parks = st.sidebar.slider("Grünflächen", 0, 100, 50, step=25)
        weight_anbindung = st.sidebar.slider("ÖV-Anbindung", 0, 100, 50, step=25)
        weight_restaurants = st.sidebar.slider("Restaurants & Cafés", 0, 100, 50, step=25)
        weight_spitäler = st.sidebar.slider("Spitäler & Ärzte", 0, 100, 50, step=25)
        
        weights = {
            "schule": weight_schulen,
            "supermarkt": weight_supermaerkte,
            "park": weight_parks,
            "oev": weight_anbindung,
            "restaurant": weight_restaurants,
            "spital": weight_spitäler
        }

    st.sidebar.divider()
    
    # Berechnen-Button
    calculate_btn = st.sidebar.button("Distanz & Score berechnen", type="primary", use_container_width=True)
    
    # Alle Daten gesammelt als Dictionary zurückgeben
    return {
        "transport_mode": transport_mode,
        "weights": weights,
        "calculate_triggered": calculate_btn,
        "reset_triggered": reset_btn # NEU: Reset-Status übergeben
    }


def render_main_content(user_inputs):
    """Rendert den Hauptbereich mit Karte und Resultaten."""

    # Session State initialisieren
    if "wohnort_coords" not in st.session_state:
        st.session_state.wohnort_coords = (47.3769, 8.5417)  # Zürich HB als Default
    if "details" not in st.session_state:
        st.session_state.details = {}
    if "gesamt_score" not in st.session_state:
        st.session_state.gesamt_score = None   # NEU: Score bleibt nach Map-Klick erhalten

    # NEU: Logik für den Reset-Button (alles leeren und neu laden)
    if user_inputs.get("reset_triggered"):
        st.session_state.wohnort_coords = (47.3769, 8.5417)
        st.session_state.details = {}
        st.session_state.gesamt_score = None
        st.rerun() # Lädt die App sofort neu

    col_map, col_results = st.columns([2, 1])

    with col_map:
        st.subheader("🗺️ Kartenansicht")

        # Berechnung nur wenn Button gedrückt
        if user_inputs["calculate_triggered"]:
            pois_df, gesamt_score, details = analysiere_standort(
                lat=st.session_state.wohnort_coords[0],
                lon=st.session_state.wohnort_coords[1],
                radius=1000,
                gewichtung=user_inputs["weights"],
            )
            # NEU: Ergebnisse im Session State speichern, damit sie nach st.rerun() erhalten bleiben
            st.session_state.details      = details
            st.session_state.gesamt_score = gesamt_score

        # Karte immer mit den aktuellen Session-State-Werten rendern
        karte = create_interactive_map(
            wohnort_koordinaten=st.session_state.wohnort_coords,
            details=st.session_state.details,
        )

        st_data = st_folium(karte, width=700, height=500, returned_objects=["last_clicked"])

        # Kartenklick verarbeiten
        if st_data and st_data.get("last_clicked"):
            neue_lat = st_data["last_clicked"]["lat"]
            neue_lon = st_data["last_clicked"]["lng"]
            if (neue_lat, neue_lon) != st.session_state.wohnort_coords:
                st.session_state.wohnort_coords = (neue_lat, neue_lon)
                st.rerun()

    with col_results:
        st.subheader("📊 Auswertung")

        # NEU: Ergebnisse aus Session State lesen (nicht aus lokalen Variablen)
        if st.session_state.gesamt_score is not None:
            st.metric(
                label="Personalisierter Wohn-Score",
                value=f"{st.session_state.gesamt_score} / 100",
            )

            for kat, info in st.session_state.details.items():
                if info["naechster_m"]:
                    st.write(
                        f"**{kat.capitalize()}**: {info['naechster_name']} "
                        f"— {info['naechster_m']} m ({info['distanz_typ']})"
                    )
                    auswahl = user_inputs["transport_mode"]
                    if auswahl == "Zu Fuss":
                        st.write(f"Zeit zu Fuss: {info['zeit_fuss_min']} min")
                    elif auswahl == "Fahrrad":
                        st.write(f"Zeit mit dem Fahrrad: {info['zeit_velo_min']} min")
                    elif auswahl == "Auto":
                        st.write(f"Zeit mit dem Auto: {info['zeit_auto_min']} min")
        else:
            st.write("Klicke auf die Karte, stelle deine Gewichte in der Sidebar ein und klicke auf Berechnen.")