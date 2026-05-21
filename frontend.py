import streamlit as st

def render_sidebar():
    st.sidebar.header("Zieleingabe")
    
    # Startpunkt/Wohnort
    target_location = st.sidebar.text_input(
        "Zieladresse oder Ort in Zürich eingeben", 
        placeholder="z.B. Bahnhofstrasse, Zürich"
    )
    
    st.sidebar.divider()
    
    # Gewichtungssystem gemäss Projektbeschrieb
    st.sidebar.header("⚖️ Gewichtungssystem")
    st.sidebar.write("Wie wichtig sind dir folgende Orte?")
    
    weight_schools = st.sidebar.slider("🏫 Schulen (für Familien)", 0, 100, 50)
    weight_shopping = st.sidebar.slider("🛒 Einkaufsmöglichkeiten", 0, 100, 50)
    weight_transit = st.sidebar.slider("🚆 ÖV-Anbindung", 0, 100, 50)
    weight_quiet = st.sidebar.slider("🌳 Ruhe & Natur (für Alleinstehende)", 0, 100, 50)
    
    st.sidebar.divider()
    
    # Berechnen-Button
    calculate_btn = st.sidebar.button("Distanz & Score berechnen", type="primary", use_container_width=True)
    
    # Alle Daten gesammelt als Dictionary zurückgeben
    return {
        "location": target_location,
        "weights": {
            "schule": weight_schools,
            "einkaufen": weight_shopping,
            "oev": weight_transit,
            "ruhe": weight_quiet
        },
        "calculate_triggered": calculate_btn
    }

def render_main_content(user_inputs):
    """Rendert den Hauptbereich mit Karte und Resultaten."""
    # Layout aufteilen: 2/3 Breite für die Karte, 1/3 für Resultate
    col_map, col_results = st.columns([2, 1])
    
    with col_map:
        st.subheader("🗺️ Kartenansicht")
        # Platzhalter für die Leaflet-Karte von Rolle 4
        st.info("Hier wird bald die interaktive Leaflet-Karte mit dem Strassennetz geladen.")
        # Später: render_map(user_inputs)
        
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