Interaktiver Wohnscore-Planer Zürich

Eine Streamlit-Webanwendung zur Bewertung von Wohnstandorten in Zürich basierend auf persönlichen Gewichtungen und der Nähe zu Points of Interest (POIs).
Funktionsweise
Die App berechnet einen personalisierten Wohn-Score (0-100) für einen beliebigen Punkt in Zürich. Der Score basiert darauf, wie nah der gewählte Standort an den wichtigsten Alltagszielen liegt, gewichtet nach den eigenen Bedürfnissen.

Ablauf der Anwendung:

Gewichtungen in der Sidebar einstellen
Wohnort auf der Karte anklicken
Auf "Distanz & Score berechnen" klicken
Score und die nächsten POIs pro Kategorie werden angezeigt

Features

Interaktive Karte: Wohnort per Klick setzen, POIs werden als Emoji-Marker eingeblendet
Top-3-Marker pro Kategorie: der nächste POI jeder Kategorie ist farbig hervorgehoben, die nächsten zwei werden ausgegraut dargestellt
Farbkodierung nach Score: grün (ab 80), orange (50-79), rot (unter 50)
Gewichtungssystem: jede Kategorie lässt sich von 0 bis 100 in 25er Schritten gewichten
Reisezeiten: Anzeige in Minuten zu Fuss, mit dem Velo oder mit dem Auto
Kartenebenen: wechselbar zwischen hellem Design und Swisstopo-Luftbild

POI-Kategorien

Schulen
Supermarkt
Grünfläche Parks und Grüanlagen
ÖV
RestaurantS
Spitäler

Scoring-Formel

Pro Kategorie wird die Distanz zum nächsten POI in einen Score (0-100) umgerechnet:
bis 200 m 100 Punkte
200 bis 2000 m linear abnehmend
ab 2000 m 0 Punkte
Der Gesamtscore ist der gewichtete Durchschnitt aller aktiven Kategorien.

Installation

git clone <https://github.com/Talahon93/Hackathooon.git>

Folgende Module müssen installiert sein:

import streamlit as st
import requests
import pandas as pd
import os
import time
from streamlit_folium import st_folium
from map_view import create_interactive_map
from logik import analysiere_standort
from geopy.distance import geodesic
import osmnx as ox
import networkx as nx
import streamlit as st
import folium
from folium.features import DivIcon

Im Terminal im Projektordner kann die Anwendung mit folgendem Befehl gestartet werden:
streamlit run app.py
