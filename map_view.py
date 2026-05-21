import folium
from folium.features import DivIcon
import pandas as pd

def get_color_by_score(score):
    """Färbt die POIs basierend auf dem Wohn-Score."""
    if score >= 80:
        return "green"
    elif score >= 50:
        return "orange"
    else:
        return "red"

# Mapping der CSV-Kategorien (aus logik.py) zu Emojis
EMOJI_MAPPING = {
    "Schule": "🏫",
    "Supermarkt": "🛒",
    "Oeffentlicher Verkehr": "🚆",
    "Gruenflaeche": "🌳",
    "Restaurant": "🍽️", 
    "Spital": "🏥"       
}

# NEU: 'details' Parameter hinzugefügt, um die echten Scores aus logik.py zu erhalten
def create_interactive_map(wohnort_koordinaten=None, poi_df=None, details=None, karten_stil="CartoDB positron"):
    """
    Generiert die interaktive Karte mit Emojis.
    Zeigt jetzt NUR den nächsten POI pro Kategorie an.
    """
    if not wohnort_koordinaten:
        wohnort_koordinaten = (47.3769, 8.5417)

    # Karte initialisieren
    m = folium.Map(location=wohnort_koordinaten, zoom_start=14, tiles=karten_stil)

    # Marker für den ausgewählten Wohnort (Haus) hinzufügen
    folium.Marker(
        location=wohnort_koordinaten,
        popup="<b>Ausgewählter Wohnort</b>",
        tooltip="Dein Startpunkt",
        icon=folium.Icon(color="blue", icon="home", prefix="fa")
    ).add_to(m)

    # NEU: Extrahiere die echten Scores aus dem 'details' Dictionary von logik.py
    kategorie_scores = {}
    if details:
        for key, info in details.items():
            csv_kat = info.get("csv_kategorie")
            if csv_kat:
                kategorie_scores[csv_kat] = info.get("score", 0)

    # POIs einzeichnen
    if poi_df is not None and not poi_df.empty:
        
        # NEU: DataFrame filtern! Nur den nächsten POI pro Kategorie behalten.
        dist_col = 'distanz_m' if 'distanz_m' in poi_df.columns else 'luftlinie_m'
        if dist_col in poi_df.columns:
            # Gruppiert nach Kategorie und nimmt den Index der Zeile mit der kleinsten Distanz
            idx = poi_df.groupby('kategorie')[dist_col].idxmin()
            poi_df = poi_df.loc[idx]

        for _, row in poi_df.iterrows():
            kategorie = row.get('kategorie', 'Unbekannt')
            name = row.get('name', 'Unbekannter POI')
            distanz = row.get(dist_col, 0)
            
            # NEU: Den echten Score für die Farbe verwenden
            score = kategorie_scores.get(kategorie, 0)
            marker_farbe = get_color_by_score(score)
            
            emoji = EMOJI_MAPPING.get(kategorie, "📍") 
            
            # Popup anpassen, um Distanz und Score anzuzeigen
            popup_html = f"""
            <b>{name}</b><br>
            Kategorie: {kategorie}<br>
            Distanz: {int(distanz)} m<br>
            Kategorie-Score: {score:.1f}/100
            """
            
            # Icon mit weissem Hintergrund und farbigem Rand
            icon_html = f"""
            <div style="
                background-color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                border: 3px solid {marker_farbe};
                box-shadow: 2px 2px 5px rgba(0,0,0,0.4);
            ">{emoji}</div>
            """
            
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{name} ({emoji})",
                icon=DivIcon(html=icon_html, icon_anchor=(15, 15)) 
            ).add_to(m)

    return m