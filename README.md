Interaktiver Wohnscore-Planer Zürich

Eine Streamlit-Webanwendung zur Bewertung von Wohnstandorten in Zürich basierend auf persönlichen Gewichtungen und der Naehe zu Points of Interest (POIs).
Funktionsweise
Die App berechnet einen personalisierten Wohn-Score (0-100) fuer einen beliebigen Punkt in Zuerich. Der Score basiert darauf, wie nah der gewaehlte Standort an den wichtigsten Alltagszielen liegt, gewichtet nach den eigenen Beduerfnissen.

Ablauf:

Wohnort auf der Karte anklicken
Gewichtungen in der Sidebar einstellen
Auf "Distanz & Score berechnen" klicken
Score und die naechsten POIs pro Kategorie werden angezeigt

Features

Interaktive Karte: Wohnort per Klick setzen, POIs werden als Emoji-Marker eingeblendet
Top-3-Marker pro Kategorie: der naechste POI jeder Kategorie ist farbig hervorgehoben, die naechsten zwei werden ausgegraut dargestellt
Farbkodierung nach Score: gruen (ab 80), orange (50-79), rot (unter 50)
Gewichtungssystem: jede Kategorie laesst sich von 0 bis 100 gewichten
Reisezeiten: Anzeige in Minuten zu Fuss, mit dem Velo oder mit dem Auto
Strassennetz-Routing: Distanzen werden über das Fusswegnetz berechnet, Fallback auf Luftlinie
Kartenebenen: wechselbar zwischen hellem Design und Swisstopo-Luftbild

POI-Kategorien

Schule Primar- und Sekundarschulen
Supermarkt Lebensmittelgeschaefte
Grünflaeche Parks und Grünflächen
Oeffentl. Verkehr Bahnhoefe, Tram- und Bushaltestellen
Restaurant Restaurants und Cafes
Spital Spitäler und Ärzte

Scoring-Formel

Pro Kategorie wird die Distanz zum naechsten POI in einen Score (0-100) umgerechnet:
bis 200 m 100 Punkte
200 bis 2000 m linear abnehmend
ab 2000 m 0 Punkte
Der Gesamtscore ist der gewichtete Durchschnitt aller aktiven Kategorien.

Librarries

git clone <https://github.com/Talahon93/Hackathooon.git>
streamlit
streamlit-folium
folium
pandas
geopandas
geopy
osmnx
networkx
overpy
requests

Projektstruktur

app.py: Einstiegspunkt, Streamlit-Konfiguration
frontend.py: Sidebar, Hauptlayout, Session-State-Logik
logik.py: Distanz- und Score-Berechnung, OSMnx-Routing
map_view.py: Folium-Karte mit POI-Markern
data_sourcing.py: POI-Extraktion via OpenStreetMap Overpass API
data/poi_zuerich.csv: Lokal gespeicherte POI-Daten
README.md

Datenquellen

POI-Daten: OpenStreetMap via Overpass API (overpass-api.de)
Strassennetz: OSMnx, Fusswegnetz Stadt Zuerich
Kartenhintergrund: CartoDB Positron / Swisstopo Luftbild (swisstopo.admin.ch)
