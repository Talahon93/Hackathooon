# logik.py
import pandas as pd
from geopy.distance import geodesic
import osmnx as ox
import networkx as nx
import streamlit as st
import os

# ── Mapping: Frontend-Keys -> CSV-Kategorien ──────────────────────────────────
# frontend.py gibt diese Keys zurueck: "schule", "einkaufen", "oev", "ruhe"
# Das CSV hat diese Kategorien:        "Schule", "Supermarkt", "Oeffentlicher Verkehr", "Gruenflaeche"
KATEGORIE_MAPPING = {
    "schule":    "Schule",
    "einkaufen": "Supermarkt",
    "oev":       "Oeffentlicher Verkehr",
    "ruhe":      "Gruenflaeche",
}

# Pfad zur CSV-Datei (relativ zu logik.py)
CSV_PFAD = os.path.join(os.path.dirname(__file__), "data", "poi_zuerich.csv")


# ── 1. POIs aus lokalem CSV laden ─────────────────────────────────────────────
@st.cache_data
def lade_pois_csv() -> pd.DataFrame:
    """
    Laedt alle POIs aus data/poi_zuerich.csv.
    Gibt DataFrame zurueck mit Spalten: kategorie, name, lat, lon
    """
    if not os.path.exists(CSV_PFAD):
        st.error(f"CSV nicht gefunden: {CSV_PFAD}")
        return pd.DataFrame()

    df = pd.read_csv(CSV_PFAD, encoding="utf-8")

    df = df.rename(columns={
        "Name":        "name",
        "Kategorie":   "kategorie",
        "Breitengrad": "lat",
        "Laengengrad": "lon",
    })

    df = df.dropna(subset=["lat", "lon"])
    df = df[(df["lat"] != 0) & (df["lon"] != 0)]

    return df.reset_index(drop=True)


# ── 2. POIs auf Radius und aktive Kategorien filtern ──────────────────────────
def filtere_pois_nach_radius(
    alle_pois: pd.DataFrame,
    lat: float,
    lon: float,
    radius: int,
    gewichtung: dict
) -> pd.DataFrame:
    """
    Behaelt nur POIs:
    - deren Kategorie in der Gewichtung aktiv ist (Wert > 0)
    - die per Luftlinie innerhalb von 2x Radius liegen (schneller Vorfilter)
    """
    if alle_pois.empty:
        return pd.DataFrame()

    relevante_kategorien = [
        KATEGORIE_MAPPING[k]
        for k, v in gewichtung.items()
        if v > 0 and k in KATEGORIE_MAPPING
    ]

    df = alle_pois[alle_pois["kategorie"].isin(relevante_kategorien)].copy()

    if df.empty:
        return pd.DataFrame()

    # Luftlinien-Vorfilter: 2x Radius, damit Strassenrouten vollstaendig erfasst werden
    df["luftlinie_m"] = df.apply(
        lambda row: geodesic((lat, lon), (row["lat"], row["lon"])).meters,
        axis=1
    )
    df = df[df["luftlinie_m"] <= radius * 2].copy()

    return df.reset_index(drop=True)


# ── 3. Strassennetz via OSMnx API laden (gecacht) ─────────────────────────────
@st.cache_resource
def lade_strassennetz(lat: float, lon: float, radius: int):
    """
    Laedt das Fussgaenger-Strassennetz von OpenStreetMap via OSMnx.
    Nur beim ersten Aufruf langsam (ca. 10-30s), danach gecacht.
    Gibt NetworkX-Graph zurueck, oder None bei Fehler.
    """
    try:
        G = ox.graph_from_point(
            (lat, lon),
            dist=radius + 500,
            network_type="walk"
        )
        return G
    except Exception as e:
        print(f"[logik] Strassennetz konnte nicht geladen werden: {e}")
        return None


# ── 4. Strassendistanzen berechnen ────────────────────────────────────────────
def berechne_distanzen(
    df: pd.DataFrame,
    lat: float,
    lon: float,
    radius: int
) -> pd.DataFrame:
    """
    Berechnet Distanz entlang des Strassennetzes (zu Fuss) fuer jeden POI.
    Fallback auf Luftlinie wenn ein POI nicht erreichbar ist.
    Neue Spalten: distanz_m, distanz_typ
    """
    if df.empty:
        return df

    df = df.copy()
    G  = lade_strassennetz(lat, lon, radius)

    if G is None:
        st.warning("Strassennetz nicht verfuegbar - Luftlinie wird verwendet.")
        df["distanz_m"]   = df["luftlinie_m"].round(0).astype(int)
        df["distanz_typ"] = "Luftlinie"
        return df.sort_values("distanz_m").reset_index(drop=True)

    ursprung = ox.distance.nearest_nodes(G, lon, lat)

    distanzen = []
    typen     = []

    for _, row in df.iterrows():
        try:
            ziel = ox.distance.nearest_nodes(G, row["lon"], row["lat"])
            dist = nx.shortest_path_length(G, ursprung, ziel, weight="length")
            distanzen.append(round(dist))
            typen.append("Strasse")

        except nx.NetworkXNoPath:
            distanzen.append(round(row["luftlinie_m"]))
            typen.append("Luftlinie")

        except Exception as e:
            print(f"[logik] Fehler bei '{row['name']}': {e}")
            distanzen.append(round(row["luftlinie_m"]))
            typen.append("Luftlinie")

    df["distanz_m"]   = distanzen
    df["distanz_typ"] = typen

    return df.sort_values("distanz_m").reset_index(drop=True)


# ── 5. Reisezeiten berechnen ──────────────────────────────────────────────────
def berechne_reisezeiten(df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet Reisezeit in Minuten basierend auf distanz_m.
    Geschwindigkeiten: Fuss 5 km/h, Velo 15 km/h, Auto 30 km/h (Stadtverkehr)
    Neue Spalten: zeit_fuss_min, zeit_velo_min, zeit_auto_min
    """
    if df.empty or "distanz_m" not in df.columns:
        return df

    df = df.copy()
    df["zeit_fuss_min"] = (df["distanz_m"] / 1000 / 5  * 60).round(1)
    df["zeit_velo_min"] = (df["distanz_m"] / 1000 / 15 * 60).round(1)
    df["zeit_auto_min"] = (df["distanz_m"] / 1000 / 30 * 60).round(1)

    return df


# ── 6. Score berechnen ────────────────────────────────────────────────────────
def berechne_score(df: pd.DataFrame, gewichtung: dict) -> tuple[float, dict]:
    """
    Berechnet Gesamt-Score (0-100) basierend auf Strassendistanz und Gewichtung.

    Scoring-Formel pro Kategorie:
      <= 200m   -> 100 Punkte
      200-2000m -> linear abnehmend
      >= 2000m  -> 0 Punkte

    Gesamtscore = gewichteter Durchschnitt aller Kategorie-Scores.
    """
    DIST_BEST = 200
    DIST_MAX  = 2000

    details       = {}
    total_gewicht = sum(gewichtung.values())

    if total_gewicht == 0:
        return 0.0, {}

    for frontend_key, gewicht in gewichtung.items():
        csv_kat = KATEGORIE_MAPPING.get(frontend_key)
        if not csv_kat:
            continue

        kat_df = df[df["kategorie"] == csv_kat]

        if kat_df.empty or gewicht == 0:
            details[frontend_key] = {
                "score":          0.0,
                "naechster_m":    None,
                "naechster_name": "-",
                "distanz_typ":    "-",
                "zeit_fuss_min":  None,
                "zeit_velo_min":  None,
                "zeit_auto_min":  None,
                "csv_kategorie":  csv_kat,
            }
            continue

        beste = kat_df.loc[kat_df["distanz_m"].idxmin()]
        dist  = beste["distanz_m"]

        if dist <= DIST_BEST:
            raw_score = 100.0
        elif dist >= DIST_MAX:
            raw_score = 0.0
        else:
            raw_score = 100.0 * (DIST_MAX - dist) / (DIST_MAX - DIST_BEST)

        details[frontend_key] = {
            "score":          round(raw_score, 1),
            "naechster_m":    int(dist),
            "naechster_name": beste["name"],
            "distanz_typ":    beste.get("distanz_typ", "-"),
            "zeit_fuss_min":  beste.get("zeit_fuss_min"),
            "zeit_velo_min":  beste.get("zeit_velo_min"),
            "zeit_auto_min":  beste.get("zeit_auto_min"),
            "csv_kategorie":  csv_kat,
        }

    gesamt = sum(
        details[k]["score"] * gewichtung[k] / total_gewicht
        for k in gewichtung
        if k in details
    )

    return round(gesamt, 1), details


# ── 7. Haupt-Funktion ─────────────────────────────────────────────────────────
def analysiere_standort(
    lat: float,
    lon: float,
    radius: int,
    gewichtung: dict
) -> tuple[pd.DataFrame, float, dict]:
    """
    Einziger Aufruf fuer app.py / frontend.py.

    Parameter:
        lat, lon   : Koordinaten des Wohnorts
        radius     : Suchradius in Metern
        gewichtung : {"schule": 80, "einkaufen": 50, "oev": 70, "ruhe": 30}

    Rueckgabe:
        pois_df      : DataFrame mit allen POIs inkl. Distanzen und Zeiten
        gesamt_score : Gewichteter Gesamtscore (0-100)
        details      : Pro Kategorie: score, naechster_m, naechster_name,
                       distanz_typ, zeit_fuss_min, zeit_velo_min, zeit_auto_min

    Beispiel details-Eintrag:
        "schule": {
            "score": 85.0,
            "naechster_m": 320,
            "naechster_name": "Primarschule Zuerich",
            "distanz_typ": "Strasse",
            "zeit_fuss_min": 3.8,
            "zeit_velo_min": 1.3,
            "zeit_auto_min": 0.6,
            "csv_kategorie": "Schule",
        }
    """
    alle_pois = lade_pois_csv()

    if alle_pois.empty:
        return pd.DataFrame(), 0.0, {}

    pois_df = filtere_pois_nach_radius(alle_pois, lat, lon, radius, gewichtung)

    if pois_df.empty:
        return pd.DataFrame(), 0.0, {}

    pois_df = berechne_distanzen(pois_df, lat, lon, radius)
    pois_df = berechne_reisezeiten(pois_df)
    gesamt_score, details = berechne_score(pois_df, gewichtung)

    return pois_df, gesamt_score, details