import speech_recognition as sr #riconoscimento vocale
import pyttsx3 # TTS(text to speech)
import os #interazione con sistema operativo
import google.generativeai as genai #sdk per utilizzare gemini
import threading # concorrenza
from dotenv import load_dotenv #gestione variabili d'ambiente
import weather #api meteo

# Carica variabili d'ambiente che sono scritte nel file .env
load_dotenv()

# --- CONFIGURAZIONE API GEMINI ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Errore: imposta la variabile d'ambiente della chiave API")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")  # Usa Flash per maggiore velocità
chat = model.start_chat()  # Mantiene la cronologia della conversazione della sessione attuale

# --- CONFIGURAZIONE VOCALE ---
recognizer = sr.Recognizer() # oggetto per la gestione del riconoscimento vocale STT
engine = pyttsx3.init() # oggetto per la gestione dello TTS
engine.setProperty('rate', 150)  # Velocità voce. Rate=parole al minuto
engine.setProperty('volume', 1.0) # 1.0 = volume al massimo

# Variabili globali
stop_speaking = False
NOME_PREFERITO = "Iron Man"

# --- SETUP INIZIALE MICROFONO ---
print("Calibrazione microfono in corso... (Resta in silenzio per 1 secondo)")
mic = sr.Microphone()
with mic as source: # apre lo stream audio
    recognizer.adjust_for_ambient_noise(source, duration=1) # calibra il riconoscimento in base al rumore ambientale
    recognizer.energy_threshold = 300  # Soglia base dalla quale il suono è considerato come voce
    recognizer.dynamic_energy_threshold = True  # Adatta leggermente il treshold
    recognizer.pause_threshold = 0.8  # Tempo di silenzio per considerare la frase finita
print("Calibrazione completata. Jarvis è pronto.")


def parla(testo):
    global stop_speaking
    stop_speaking = False

    def _speak():
        if stop_speaking: return
        try:
            engine.say(testo)
            engine.runAndWait() #multithreading
        except RuntimeError:
            # Gestisce il caso in cui il loop dell'engine sia già attivo
            pass

    # Thread per non bloccare l'ascolto mentre parla, multithreading
    thread = threading.Thread(target=_speak, daemon=True)
    thread.start()


def ascolta():

    with mic as source:
        print("Listening...", end="\r", flush=True)
        try:
            # timeout: se non parlo entro 5s, smette di ascoltare
            # phrase_time_limit: a 10s smette di ascoltare considerando la frase terminata
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            # Riconoscimento Google
            testo = recognizer.recognize_google(audio, language="it-IT") #invia l'audio a google ed ottiene il testo
            print(f"\nTu: {testo}")
            return testo.lower()

        except sr.WaitTimeoutError: #Eccezione se l'utente non parla o ha fatto troppo silenzio
            return None
        except sr.UnknownValueError: #Non capisce cosa è stato detto
            return None
        except sr.RequestError: #Richiesta a google fallita
            parla("C'è un problema di connessione.")
            return None
        except Exception as e: #Qualsiasi altra eccezione imprevista
            print(f"Errore: {e}")
            return None


#pone la domanda a gemini e ritorna la risposta
def rispondi_gemini(domanda):

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