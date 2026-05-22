# logik.py
import pandas as pd
from geopy.distance import geodesic
import osmnx as ox
import networkx as nx
import streamlit as st
import os

# ── Mapping: Frontend-Keys -> CSV-Kategorien ──────────────────────────────────
KATEGORIE_MAPPING = {
    "schule":     "Schule",
    "supermarkt": "Supermarkt",
    "park":       "Gruenflaeche",
    "oev":        "Oeffentlicher Verkehr",
    "restaurant": "Restaurant",
    "spital":     "Spital",
}

CSV_PFAD = os.path.join(os.path.dirname(__file__), "data", "poi_zuerich.csv")


# ── 1. POIs aus lokalem CSV laden ─────────────────────────────────────────────
@st.cache_data
def lade_pois_csv() -> pd.DataFrame:
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

    df["luftlinie_m"] = df.apply(
        lambda row: geodesic((lat, lon), (row["lat"], row["lon"])).meters,
        axis=1
    )
    df = df[df["luftlinie_m"] <= radius * 2].copy()

    return df.reset_index(drop=True)


# ── 3. Strassennetz via OSMnx laden (gecacht) ─────────────────────────────────
@st.cache_resource
def lade_strassennetz_zuerich():
    try:
        G = ox.graph_from_place("Zürich, Switzerland", network_type="walk")
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
    if df.empty:
        return df

    df = df.copy()
    G = lade_strassennetz_zuerich()

    if G is None:
        st.warning("Strassennetz nicht verfuegbar - Luftlinie wird verwendet.")
        df["distanz_m"]   = df["luftlinie_m"].round(0).astype(int)
        df["distanz_typ"] = "Luftlinie"
        return df.sort_values("distanz_m").reset_index(drop=True)

    ursprung    = ox.distance.nearest_nodes(G, lon, lat)
    ziel_knoten = ox.distance.nearest_nodes(G, df["lon"].tolist(), df["lat"].tolist())
    alle_distanzen = nx.single_source_dijkstra_path_length(G, ursprung, weight="length")

    distanzen, typen = [], []
    for ziel, (_, row) in zip(ziel_knoten, df.iterrows()):
        if ziel in alle_distanzen:
            distanzen.append(round(alle_distanzen[ziel]))
            typen.append("Strasse")
        else:
            distanzen.append(round(row["luftlinie_m"]))
            typen.append("Luftlinie")

    df["distanz_m"]   = distanzen
    df["distanz_typ"] = typen
    return df.sort_values("distanz_m").reset_index(drop=True)


# ── 5. Reisezeiten berechnen ──────────────────────────────────────────────────
def berechne_reisezeiten(df: pd.DataFrame) -> pd.DataFrame:
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
    NEU: details[kat]["top3"] enthaelt die 3 naechsten POIs pro Kategorie.
    Diese Liste wird von map_view.py benoetigt um die Marker zu zeichnen.
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

        kat_df = df[df["kategorie"] == csv_kat].copy()

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
                "top3":           [],          # NEU: leere Liste als Fallback
            }
            continue

        # NEU: Top 3 naechste POIs dieser Kategorie
        top3_df = kat_df.nsmallest(3, "distanz_m")

        top3 = []
        for _, row in top3_df.iterrows():
            top3.append({
                "name":          row["name"],
                "lat":           row["lat"],
                "lon":           row["lon"],
                "distanz_m":     int(row["distanz_m"]),
                "distanz_typ":   row.get("distanz_typ", "-"),
                "zeit_fuss_min": row.get("zeit_fuss_min"),
                "zeit_velo_min": row.get("zeit_velo_min"),
                "zeit_auto_min": row.get("zeit_auto_min"),
                "csv_kategorie": csv_kat,
            })

        # Nächster POI (Platz 1) für Score und Auswertungstext
        beste = top3_df.iloc[0]
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
            "top3":           top3,            # NEU: wird von map_view.py gezeichnet
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