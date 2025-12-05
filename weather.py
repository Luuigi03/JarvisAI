import requests
import re



coord_cache = {}
def trova_citta(testo):
    """Estrae il nome della città dalla frase usando regex semplice"""
    match = re.search(r"(?:meteo|tempofa|previsione) (?:a|di|per|in) (.+)", testo, re.IGNORECASE)
    if match:
        citta = match.group(1).strip()
        # Pulizia veloce di parole inutili
        citta = re.sub(r"\b(oggi|domani|ora)\b", "", citta, flags=re.IGNORECASE).strip()
        return citta.capitalize()
    return None

def previsione_meteo(citta):
    coords = ottieni_coordinate(citta)
    if not coords:
        return f"Mi dispiace, non riesco a trovare la città {citta}."

    lat, lon, nome_citta = coords
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "temperature_2m,weathercode",
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "timezone": "Europe/Rome",
        "forecast_days": 1
    }
    try:
        r = requests.get(url, params=params, timeout=10) # api call
        data = r.json()

        current = data["current_weather"]
        temp = current["temperature"]
        vento = current["windspeed"]
        codice = current["weathercode"]

        # Traduzione semplicissima del codice WMO (i più comuni)
        descrizione = {
            0: "sereno", 1: "poco nuvoloso", 2: "parzialmente nuvoloso", 3: "nuvoloso",
            45: "nebbia", 51: "pioggerella", 61: "pioggia", 63: "pioggia moderata", 65: "pioggia forte",
            71: "neve", 95: "temporale"
        }.get(codice, "condizioni variabili")

        risposta = f"A {nome_citta} in questo momento ci sono {temp} gradi, " \
                   f"{descrizione}, con vento a {vento} km/h."
        return risposta

    except Exception as e:
        return "Non riesco a prendere i dati meteo al momento."

def ottieni_coordinate(citta):
    """Usa l’API gratuita di Open-Meteo per trovare lat/lon della città"""
    if citta in coord_cache:
        return coord_cache[citta]

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={citta}&count=1&language=it"
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("results"):
            loc = data["results"][0]
            coord_cache[citta] = (loc["latitude"], loc["longitude"], loc["name"])
            return coord_cache[citta]
    except:
        pass
    return None
