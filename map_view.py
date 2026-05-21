import folium
import pandas as pd

def get_color_by_score(score):
    """Färbt die POIs basierend auf dem Wohn-Score."""
    if score >= 80:
        return "green"
    elif score >= 50:
        return "orange"
    else:
        return "red"

def create_interactive_map(wohnort_koordinaten=None, poi_df=None, karten_stil="CartoDB positron"):
    """
    Generiert die interaktive Karte.
    Nutzt 'CartoDB positron', um zum Light-Theme des Frontends zu passen.
    """
    # Falls keine Koordinaten übergeben wurden, Zürich (HB) als Standard verwenden
    if not wohnort_koordinaten:
        wohnort_koordinaten = (47.3769, 8.5417)

    # Karte initialisieren
    m = folium.Map(location=wohnort_koordinaten, zoom_start=14, tiles=karten_stil)

    # Marker für den ausgewählten Wohnort (Haus) hinzufügen
    folium.Marker(
        location=wohnort_koordinaten,
        popup="<b>Ausgewählter Wohnort</b>",
        tooltip="Zielort",
        icon=folium.Icon(color="blue", icon="home", prefix="fa")
    ).add_to(m)

    # POIs (Points of Interest) auf der Karte einzeichnen, falls das DataFrame existiert
    if poi_df is not None and not poi_df.empty:
        for _, row in poi_df.iterrows():
            score = row.get('score', 0)
            marker_farbe = get_color_by_score(score)
            
            # HTML für das Popup, das beim Klicken auf den Punkt erscheint
            popup_html = f"""
            <b>{row.get('name', 'Unbekannter POI')}</b><br>
            Kategorie: {row.get('category', 'Unbekannt')}<br>
            Score: {score:.1f}
            """
            
            # Kreis-Marker (CircleMarker) für die POIs verwenden
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=8,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{row.get('name', 'POI')}",
                color=marker_farbe,
                fill=True,
                fill_color=marker_farbe,
                fill_opacity=0.8
            ).add_to(m)

    return m