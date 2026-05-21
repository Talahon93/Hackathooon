import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from map_view import create_interactive_map
from logik import analysiere_standort

def render_sidebar():
    st.sidebar.header("Zieleingabe & Mobilität")
    
    # NEU: Text-Input entfernt. Wir fordern den User auf, die Karte zu nutzen.
    st.sidebar.info("👆 Klicke direkt auf die Karte, um deinen gewünschten Wohnort festzulegen!")

    transport_mode = st.sidebar.radio(
        "gewünschtes Fortbewegungsmittel",
        options=["Zu Fuss", "Fahrrad", "Auto"],
        help="Diese Auswahl beeinflusst, ob die Algorithmen Fusswege, Radwege oder Strassen nutzen."
    )
    
    st.sidebar.divider()
    
    # Gewichtungssystem gemäss Projektbeschrieb
    st.sidebar.header("⚖️ Gewichtungssystem")
    st.sidebar.write("Wie wichtig sind dir folgende Orte?")
    
    weight_schulen = st.sidebar.slider("Schulen", 0, 100, 50)
    weight_supermaerkte = st.sidebar.slider("Supermärkte", 0, 100, 50)
    weight_parks = st.sidebar.slider("Grünflächen", 0, 100, 50)
    weight_anbindung = st.sidebar.slider("ÖV-Anbindung", 0, 100, 50)
    weight_restaurants = st.sidebar.slider("Restaurants & Cafés", 0, 100, 50)
    weight_spitäler = st.sidebar.slider("Spitäler & Ärzte", 0, 100, 50)

    st.sidebar.divider()
    
    # Berechnen-Button
    calculate_btn = st.sidebar.button("Distanz & Score berechnen", type="primary", use_container_width=True)
    
    # Alle Daten gesammelt als Dictionary zurückgeben
    return {
        "transport_mode": transport_mode,
        "weights": {
            "schule": weight_schulen,
            "supermarkt": weight_supermaerkte,
            "park": weight_parks,
            "oev": weight_anbindung,
            "restaurant": weight_restaurants,
            "spital": weight_spitäler
        },
        "calculate_triggered": calculate_btn
    }

def render_main_content(user_inputs):
    """Rendert den Hauptbereich mit Karte und Resultaten."""
    
    # NEU: Session State initialisieren, um den Klick auf die Karte dauerhaft zu speichern
    if "wohnort_coords" not in st.session_state:
        st.session_state.wohnort_coords = (47.3769, 8.5417) # Zürich HB als Default

    # Layout aufteilen: 2/3 Breite für die Karte, 1/3 für Resultate
    col_map, col_results = st.columns([2, 1])
    
    with col_map:
        st.subheader("🗺️ Kartenansicht")
        st.caption("Klicke auf einen beliebigen Punkt auf der Karte, um den Wohnort dorthin zu verschieben.")
        
        pois_df = None
        gesamt_score = 0
        details = {}
        
        # Wenn der Benutzer auf "Berechnen" geklickt hat
        if user_inputs["calculate_triggered"]:
            # NEU: Wir nutzen die Koordinaten aus dem Session State
            pois_df, gesamt_score, details = analysiere_standort(
                lat=st.session_state.wohnort_coords[0],
                lon=st.session_state.wohnort_coords[1],
                radius=1000,
                gewichtung=user_inputs["weights"]   
            )
            
        # 1. Karte generieren (immer mit den Koordinaten aus dem Session State!)
        # NEU: Wir übergeben auch 'details', damit die Karte die echten Farben (Scores) berechnen kann
        karte = create_interactive_map(wohnort_koordinaten=st.session_state.wohnort_coords, poi_df=pois_df, details=details)   
        
        # 2. Die Leaflet-Karte in Streamlit rendern
        # NEU: returned_objects=["last_clicked"] fängt Klicks des Users ab
        st_data = st_folium(karte, width=700, height=500, returned_objects=["last_clicked"])
        
        # NEU: Klick-Logik – wenn der User klickt, updaten wir die Koordinaten und laden neu
        if st_data and st_data.get("last_clicked"):
            neue_lat = st_data["last_clicked"]["lat"]
            neue_lon = st_data["last_clicked"]["lng"]
            
            
            if (neue_lat, neue_lon) != st.session_state.wohnort_coords:
                st.session_state.wohnort_coords = (neue_lat, neue_lon)
                st.rerun() 
        
    with col_results:
        st.subheader("📊 Auswertung")
        
        if user_inputs["calculate_triggered"]:
            # Diese Zeile muss nach dem 'if' zwingend eingerückt sein!
            st.metric(label="Personalisierter Wohn-Score", value=f"{gesamt_score} / 100")
            
            for kat, info in details.items():
                if info["naechster_m"]:
                    st.write(f"**{kat.capitalize()}**: {info['naechster_name']} — {info['naechster_m']} m ({info['distanz_typ']})")
                    
                    auswahl = user_inputs["transport_mode"]
                    
                    if auswahl == "Zu Fuss":
                        st.write(f"Zeit zu Fuss: {info['zeit_fuss_min']} min")
                    elif auswahl == "Fahrrad":
                        st.write(f"Zeit mit dem Velo: {info['zeit_velo_min']} min")
                    elif auswahl == "Auto":
                        st.write(f"Zeit mit dem Auto: {info['zeit_auto_min']} min")
            
            st.divider()
            st.caption("Erweiterung (Geplant): Distanz entlang des Strassennetzes (Fuss, Fahrrad, Auto).")
        else:
            # Das 'else' muss auf der exakt gleichen Höhe sein wie das 'if'
            st.write("👈 Klicke auf die Karte, stelle deine Gewichte in der Sidebar ein und klicke auf Berechnen.")