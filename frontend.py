import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from map_view import create_interactive_map

def render_sidebar():
    st.sidebar.header("Zieleingabe & Mobilität")
    
    # Startpunkt/Wohnort
    target_location = st.sidebar.text_input(
        "Zieladresse oder Ort in Zürich eingeben", 
        placeholder="z.B. Bahnhofstrasse, Zürich"
    )

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
        "location": target_location,
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
    # Layout aufteilen: 2/3 Breite für die Karte, 1/3 für Resultate
    col_map, col_results = st.columns([2, 1])
    
    with col_map:
        st.subheader("🗺️ Kartenansicht")
        
        # Standardkoordinaten (Zürich)
        wohnort_koordinaten = (47.3769, 8.5417)
        poi_daten = None
        
        # Wenn der Benutzer auf "Berechnen" geklickt und ein Ort eingegeben hat, Dummy-Daten generieren
        if user_inputs["calculate_triggered"] and user_inputs["location"]:
            # Dummy-Daten zur Simulation der Arbeit von Rolle 1 (Data) und Rolle 2 (Algorithmus)
            poi_daten = pd.DataFrame({
                'name': ['Schule Zentrum', 'Migros', 'Park am See'],
                'category': ['Schule', 'Einkaufen', 'Natur'],
                'lat': [47.3780, 47.3750, 47.3800],
                'lon': [8.5400, 8.5450, 8.5350],
                'score': [90, 60, 30] # Grün, Orange, Rot
            })
            
        # 1. Deine Funktion aufrufen, um die Karte zu generieren
        karte = create_interactive_map(wohnort_koordinaten=wohnort_koordinaten, poi_df=poi_daten)
        
        # 2. Die Leaflet-Karte in Streamlit rendern
        st_folium(karte, width=700, height=500, returned_objects=[])
        
    with col_results:
        st.subheader("📊 Auswertung")
        
        # Logik, wenn der Button gedrückt wurde
        if user_inputs["calculate_triggered"]:
            if not user_inputs["location"]:
                st.warning("Bitte gib zuerst einen Zielort in der Sidebar ein.")
            else:
                st.success("Berechnung läuft...")
                
                # Dummy-Resultate (bis die Logik von Rolle 2 steht)
                st.metric(label="🏆 Personalisierter Wohn-Score", value="82 / 100", delta="+12")
                
                st.write("**Luftlinien-Distanzen zu POIs:**")
                st.write("🏫 Nächste Schule: **450 m**")
                st.write("🌳 Nächster Park: **1.2 km**")
                
                # Hinweis für die geplante Erweiterung
                st.divider()
                st.caption("Erweiterung (Geplant): Distanz entlang des Strassennetzes (Fuss, Fahrrad, Auto).")
        else:
            st.write("👈 Stelle deine Gewichte in der Sidebar ein und klicke auf Berechnen.")