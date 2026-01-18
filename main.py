import speech_recognition as sr
import pyttsx3
import os
import google.generativeai as genai
import threading
from dotenv import load_dotenv

# I tuoi moduli
import weather

# Carica variabili d'ambiente
load_dotenv()

# --- CONFIGURAZIONE API GEMINI ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Errore: imposta la variabile d'ambiente della chiave API")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")  # Usa Flash per maggiore velocità
chat = model.start_chat()  # Mantiene la memoria della conversazione

# --- CONFIGURAZIONE VOCALE (Ottimizzata) ---
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Velocità voce
engine.setProperty('volume', 1.0)

# Variabili globali
stop_speaking = False
NOME_PREFERITO = "Signore"  # O "Signor Cocc"

# --- SETUP INIZIALE MICROFONO (Fatto una sola volta per velocità) ---
print("Calibrazione microfono in corso... (Resta in silenzio per 1 secondo)")
mic = sr.Microphone()
with mic as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
    recognizer.energy_threshold = 300  # Soglia base (puoi alzarla se c'è rumore di fondo)
    recognizer.dynamic_energy_threshold = True  # Si adatta leggermente
    recognizer.pause_threshold = 0.8  # Tempo di silenzio per considerare la frase finita
print("Calibrazione completata. Jarvis è pronto.")


def parla(testo):
    global stop_speaking
    stop_speaking = False

    def _speak():
        if stop_speaking: return
        try:
            engine.say(testo)
            engine.runAndWait()
        except RuntimeError:
            # Gestisce il caso in cui il loop dell'engine sia già attivo
            pass

    # Thread per non bloccare l'ascolto mentre parla
    thread = threading.Thread(target=_speak, daemon=True)
    thread.start()


def ascolta():
    """Ascolta il microfono con impostazioni ottimizzate per la velocità"""
    with mic as source:
        print("Listening...", end="\r", flush=True)  # Feedback visivo minimo
        try:
            # timeout: se non parli entro 5s, smette di ascoltare
            # phrase_time_limit: taglia la registrazione a 10s per velocizzare l'invio a Google
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            # Riconoscimento Google
            testo = recognizer.recognize_google(audio, language="it-IT")
            print(f"\nTu: {testo}")
            return testo.lower()

        except sr.WaitTimeoutError:
            return None  # Silenzio, riprova subito
        except sr.UnknownValueError:
            return None  # Rumore non capito, riprova
        except sr.RequestError:
            parla("C'è un problema di connessione.")
            return None
        except Exception as e:
            print(f"Errore: {e}")
            return None


def rispondi_gemini(domanda):
    """Gestisce la risposta AI"""
    try:
        response = chat.send_message(domanda)
        return response.text
    except Exception as e:
        return f"Mi dispiace, c'è stato un errore nei miei circuiti: {str(e)}"


# --- LOOP PRINCIPALE ---
print("\n--- JARVIS ATTIVO ---")
parla(f"Sistemi online. Ciao {NOME_PREFERITO}.")

while True:
    testo_utente = ascolta()

    if not testo_utente:
        continue  # Se non sente nulla, ricomincia subito il ciclo (reattività)

    # 1. Comandi di Uscita
    if any(parola in testo_utente for parola in ["esci", "spegniti", "addio", "stop"]):
        parla("Disattivazione sistemi. A presto.")
        break

    # 2. Rilevamento Parola Chiave "Jarvis" (o varianti)
    keyword_detected = any(k in testo_utente for k in ["jarvis", "giarvis", "ciarvis"])

    if keyword_detected:
        # Pulisce la frase togliendo la parola chiave per mandarla pulita alle funzioni
        comando_pulito = testo_utente.replace("jarvis", "").replace("giarvis", "").strip()

        # Se ha detto SOLO "Jarvis", chiedi cosa vuole
        if not comando_pulito:
            parla("Dimmi pure?")
            continue

        # 3. Controllo Meteo
        keywords_meteo = ["meteo", "tempo", "previsioni", "piove", "gradi"]
        if any(w in comando_pulito for w in keywords_meteo):
            citta = weather.trova_citta(comando_pulito)
            if citta:
                print(f"🔍 Controllo meteo per: {citta}")
                dati_meteo = weather.previsione_meteo(citta)
                parla(dati_meteo)
            else:
                # Se non trova la città, lo chiede a Gemini
                risposta = rispondi_gemini(comando_pulito)
                parla(risposta)
            continue

        # 4. Risposta Generica (Gemini)
        print("🤖 Elaborazione risposta...")
        risposta = rispondi_gemini(comando_pulito)

        # Stampa e Parla
        print(f"Jarvis: {risposta}")
        parla(risposta)