import requests
import pandas as pd
import os
import time

def poi_zuerich_extrahieren(osm_schluessel, osm_wert, kategorie_name):
    url_overpass = "http://overpass-api.de/api/interpreter"
    
    # MODIFIKATION: Timeout auf 90 Sekunden erhöht, um dem Server mehr Zeit zu geben
    abfrage = f"""
    [out:json][timeout:90];
    area["name"="Zürich"]["admin_level"="8"]->.suchGebiet;
    (
      node["{osm_schluessel}"="{osm_wert}"](area.suchGebiet);
      way["{osm_schluessel}"="{osm_wert}"](area.suchGebiet);
      relation["{osm_schluessel}"="{osm_wert}"](area.suchGebiet);
    );
    out center;
    """
    
    print(f"Lade Daten herunter für die Kategorie: {kategorie_name}...")
    
    headers = {
        'User-Agent': 'Stadtplaner_FHNW_Hackathon/1.1 (Akademisches Projekt)'
    }
    
    antwort = requests.post(url_overpass, data={'data': abfrage}, headers=headers)
    
    if antwort.status_code == 200:
        daten_json = antwort.json()
        elemente = daten_json.get('elements', [])
        poi_liste = []
        
        for element in elemente:
            name = element.get('tags', {}).get('name', 'Unbekannt')
            
            if element['type'] == 'node':
                breitengrad = element.get('lat')
                laengengrad = element.get('lon')
            else:
                breitengrad = element.get('center', {}).get('lat')
                laengengrad = element.get('center', {}).get('lon')
            
            if breitengrad and laengengrad:
                poi_liste.append({
                    'Name': name,
                    'Kategorie': kategorie_name,
                    'Breitengrad': breitengrad,
                    'Laengengrad': laengengrad
                })
                
        return pd.DataFrame(poi_liste)
    elif antwort.status_code == 429:
        print(f"Fehler 429: Der Server ist immer noch überlastet. Überspringe {kategorie_name}.")
        return pd.DataFrame()
    else:
        print(f"Fehler {antwort.status_code} beim Herunterladen von {kategorie_name}.")
        return pd.DataFrame()

# ==========================================
# HAUPTAUSFÜHRUNG DES SKRIPTS (MAIN)
# ==========================================
if __name__ == "__main__":
    
    if not os.path.exists('data'):
        os.makedirs('data')
    
    kategorien_liste = [
        {'osm_key': 'amenity', 'osm_wert': 'school', 'name_de': 'Schule'},
        {'osm_key': 'shop', 'osm_wert': 'supermarket', 'name_de': 'Supermarkt'},
        {'osm_key': 'leisure', 'osm_wert': 'park', 'name_de': 'Gruenflaeche'},
        {'osm_key': 'public_transport', 'osm_wert': 'station', 'name_de': 'Oeffentlicher Verkehr'}, # Bahnhöfe
        {'osm_key': 'highway', 'osm_wert': 'bus_stop', 'name_de': 'Oeffentlicher Verkehr'},         # Bushaltestellen
        {'osm_key': 'railway', 'osm_wert': 'tram_stop', 'name_de': 'Oeffentlicher Verkehr'},        # Tramhaltestellen
        {'osm_key': 'amenity', 'osm_wert': 'restaurant', 'name_de': 'Restaurant'},
        {'osm_key': 'amenity', 'osm_wert': 'hospital', 'name_de': 'Spital'}
    ]
    
    alle_datenframes = []
    
    for kat in kategorien_liste:
        df_temp = poi_zuerich_extrahieren(kat['osm_key'], kat['osm_wert'], kat['name_de'])
        
        if not df_temp.empty:
            alle_datenframes.append(df_temp)
            print(f" -> {len(df_temp)} Punkte für '{kat['name_de']}' gefunden.")
        
        # MODIFIKATION: Pause auf 8 Sekunden erhöht, um Blockaden zu vermeiden
        print(" -> 8 Sekunden Pause, um den Server zu schonen...")
        time.sleep(8) 
    
    if alle_datenframes:
        df_gesamt = pd.concat(alle_datenframes, ignore_index=True)
        datei_pfad_poi = 'data/poi_zuerich.csv'
        df_gesamt.to_csv(datei_pfad_poi, index=False, encoding='utf-8')
        
        print("\n--- ZUSAMMENFASSUNG ---")
        print(f"POI-Datenextraktion erfolgreich abgeschlossen!")
        print(f"Insgesamt {len(df_gesamt)} POIs gefunden.")
        print(f"Gespeichert in: {datei_pfad_poi}")
    
    # STRASSENNETZ TEMPORÄR DEAKTIVIERT:
    # Um das MVP (Minimum Viable Product) zu sichern, berechnen wir zuerst nur 
    # die Luftliniendistanz (wie im Projektbeschrieb gefordert). 
    # Das Strassennetz kann später reaktiviert werden, falls noch Zeit bleibt.
    #
    # strassennetz_extrahieren() 
    
    print("\nDas Skript ist vollständig durchgelaufen. Die Daten sind bereit für Jascha!")