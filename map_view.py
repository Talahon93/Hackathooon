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

EMOJI_MAPPING = {
    "Schule":               "🏫",
    "Supermarkt":           "🛒",
    "Oeffentlicher Verkehr":"🚆",
    "Gruenflaeche":         "🌳",
    "Restaurant":           "🍽️",
    "Spital":               "🏥",
}

def create_interactive_map(wohnort_koordinaten=None, poi_df=None, details=None, karten_zoom=14):
    if not wohnort_koordinaten:
        wohnort_koordinaten = (47.3769, 8.5417)

    m = folium.Map(location=wohnort_koordinaten, zoom_start=karten_zoom, tiles=None)

    cartodb_attr = '<span style="display: inline-block; margin-right: 60px;">&copy; OpenStreetMap, CartoDB</span>'

    folium.TileLayer(
        'CartoDB positron', 
        name='Helles Design (Standard)', 
        attr=cartodb_attr,
        control=True
    ).add_to(m)

    swisstopo_attr = '<span style="display: inline-block; margin-right: 60px;">&copy; swisstopo</span>'

    swisstopo_ortho_url = 'https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.swissimage-product/default/current/3857/{z}/{x}/{y}.jpeg'
    folium.TileLayer(
        tiles=swisstopo_ortho_url,
        attr=swisstopo_attr,
        name='Swisstopo Luftbild',
        control=True,
        show=False
    ).add_to(m)

    folium.Marker(
        location=wohnort_koordinaten,
        popup="<b>Ausgewählter Wohnort</b>",
        tooltip="Dein Startpunkt",
        icon=folium.Icon(color="blue", icon="home", prefix="fa")
    ).add_to(m)

    if details:
        for frontend_key, info in details.items():
            csv_kat      = info.get("csv_kategorie", "")
            score        = info.get("score", 0)
            emoji        = EMOJI_MAPPING.get(csv_kat, "📍")
            marker_farbe = get_color_by_score(score)
            top3         = info.get("top3", [])

            for i, poi in enumerate(top3):
                if i == 0:
                    rand_farbe   = marker_farbe
                    hintergrund  = "white"
                    opacity      = 1.0
                else:
                    rand_farbe   = "#888888"
                    hintergrund  = "#dddddd"
                    opacity      = 0.55

                popup_html = (
                    f"<b>{poi['name']}</b><br>"
                    f"Kategorie: {csv_kat}<br>"
                    f"Distanz: {poi['distanz_m']} m ({poi['distanz_typ']})<br>"
                    f"Kategorie-Score: {score:.1f}/100"
                )

                icon_html = f"""
                <div style="
                    background-color: {hintergrund};
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    border: 3px solid {rand_farbe};
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.4);
                    opacity: {opacity};
                ">{emoji}</div>
                """

                tooltip_text = f"{'(nächster) ' if i == 0 else ''}{poi['name']} ({emoji})"

                folium.Marker(
                    location=[poi["lat"], poi["lon"]],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=tooltip_text,
                    icon=DivIcon(html=icon_html, icon_anchor=(15, 15))
                ).add_to(m)

    folium.LayerControl(position='bottomleft').add_to(m)
    return m