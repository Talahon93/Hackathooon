import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from map_view import create_interactive_map
from logik import analysiere_standort

def render_sidebar():
    st.sidebar.header("Zieleingabe & Mobilität")
    st.sidebar.info("👆 Klicke direkt auf die Karte, um deinen gewünschten Wohnort festzulegen!")

    transport_mode = st.sidebar.radio(
        "gewünschtes Fortbewegungsmittel",
        options=["Zu Fuss", "Fahrrad", "Auto"],
        help="Diese Auswahl beeinflusst, ob die Algorithmen Fusswege, Radwege oder Strassen nutzen."
    )

    st.sidebar.divider()
    st.sidebar.header("⚖️ Gewichtungssystem")
    st.sidebar.write("Wie wichtig sind dir folgende Orte?")

    weight_schulen      = st.sidebar.slider("Schulen",           0, 100, 50, step=25)
    weight_supermaerkte = st.sidebar.slider("Supermärkte",       0, 100, 50, step=25)
    weight_parks        = st.sidebar.slider("Grünflächen",       0, 100, 50, step=25)
    weight_anbindung    = st.sidebar.slider("ÖV-Anbindung",      0, 100, 50, step=25)
    weight_restaurants  = st.sidebar.slider("Restaurants & Cafés", 0, 100, 50, step=25)
    weight_spitaeler    = st.sidebar.slider("Spitäler & Ärzte",  0, 100, 50, step=25)

    st.sidebar.divider()
    calculate_btn = st.sidebar.button("Distanz & Score berechnen", type="primary", use_container_width=True)

    return {
        "transport_mode": transport_mode,
        "weights": {
            "schule":     weight_schulen,
            "supermarkt": weight_supermaerkte,
            "park":       weight_parks,
            "oev":        weight_anbindung,
            "restaurant": weight_restaurants,
            "spital":     weight_spitaeler,
        },
        "calculate_triggered": calculate_btn,
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

    col_map, col_results = st.columns([2, 1])

    with col_map:
        st.subheader("🗺️ Kartenansicht")
        st.caption("Klicke auf einen beliebigen Punkt auf der Karte, um den Wohnort dorthin zu verschieben.")

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
                        st.write(f"Zeit mit dem Velo: {info['zeit_velo_min']} min")
                    elif auswahl == "Auto":
                        st.write(f"Zeit mit dem Auto: {info['zeit_auto_min']} min")
        else:
            st.write("👈 Klicke auf die Karte, stelle deine Gewichte in der Sidebar ein und klicke auf Berechnen.")