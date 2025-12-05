import speech_recognition as sr
import pyttsx3
import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests
import re
load_dotenv()

# Utilizzo la api key di Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Errore: imposta la variabile d'ambiente della chiave API")

genai.configure(api_key = api_key)

model = genai.GenerativeModel("gemini-2.5-flash")
chat = model.start_chat() #chat con storico

recognizer = sr.Recognizer()
engine = pyttsx3.init()

coord_cache = {}

def ascolta():
    with sr.Microphone() as source:
        print("Sono in ascolto...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            testo = recognizer.recognize_google(audio, language="it-IT")
            print(f"Hai detto: {testo}")
            return testo.lower()
        except sr.UnknownValueError:
            print("Non ho capito, riprova!")
            return None
        except Exception as e:
            print(f"Errore riconoscimento: {e}")
            return None

def parla(testo):
    engine.say(testo)
    engine.runAndWait()

def rispondi(domanda):
    try:
        # Usa la chat con storico (molto meglio di una chiamata singola!)
        response = chat.send_message(domanda)
        return response.text
    except Exception as e:
        return f"Mi dispiace, c'è stato un errore: {str(e)}"

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

# Loop principale
print("Assistente vocale Gemini attivo! Di' 'esci' per terminare.")
parla("Ciao sono Jarvis. Come posso aiutarti?")

while True:
    domanda = ascolta()
    if domanda:
        if "esci" in domanda or "addio" in domanda or "ciao" in domanda:
            parla("Ciao! A presto signore.")
            break
        elif "jarvis" in domanda or "giarvis" in domanda or "gliarvis" in domanda: # parola di attivazione

            citta = trova_citta(domanda)
            if citta and any(parola in domanda for parola in ["meteo", "tempofa", "previsioni", "piove",  "fa caldo", "fa freddo"]):
                print(f"🔍 Cerco il meteo per {citta}...")
                risposta = previsione_meteo(citta)
                parla(risposta)
                continue

            risposta = rispondi(domanda)
            print(f"AI: {risposta}")
            parla(risposta)