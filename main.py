import speech_recognition as sr
import pyttsx3
import os
import google.generativeai as genai
import threading
from dotenv import load_dotenv
load_dotenv()

#My libs
import weather

# Utilizzo la api key di Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Errore: imposta la variabile d'ambiente della chiave API")

genai.configure(api_key = api_key)

model = genai.GenerativeModel("gemini-2.5-flash")
chat = model.start_chat() #chat con storico

recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 150)
stop_speaking = False
NOME_PREFERITO = "Signor Cocc"


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



def rispondi_con_nome(domanda):
    """Invia la domanda a Gemini e fa rispondere sempre chiamandoti con il tuo nome"""
    try:
        risposta_cruda = chat.send_message(domanda).text


        prompt = f"Riscrivi esattamente questa risposta rivolgendoti sempre a me chiamandomi '{NOME_PREFERITO}'. "
        prompt += "Non aggiungere spiegazioni, usa solo la risposta riscritta:\n\n" + risposta_cruda

        risposta_finale = chat.send_message(prompt).text

        return risposta_finale.strip()

    except Exception as e:
        return f"Mi dispiace {NOME_PREFERITO}, c'è stato un errore."


def parla(testo):
    global stop_speaking
    stop_speaking = False  # resetta ogni volta che inizia a parlare

    def _speak():
        if stop_speaking:
            return
        engine.say(testo)
        engine.runAndWait()

    # Avvia la sintesi vocale in un thread separato
    thread = threading.Thread(target=_speak, daemon=True)
    thread.start()
    thread.join(timeout=15)  # massimo 15 secondi di attesa (per sicurezza)

def rispondi(domanda):
    try:
        # Usa la chat con storico (molto meglio di una chiamata singola!)
        response = chat.send_message(domanda)
        return response.text
    except Exception as e:
        return f"Mi dispiace, c'è stato un errore: {str(e)}"

# Loop principale
print("Assistente vocale Gemini attivo! Di' 'esci' per terminare.")
parla("Ciao sono Jarvis. Come posso aiutarti?")

while True:
    domanda = ascolta()
    if not domanda:
        continue

    if "esci" in domanda or "addio" in domanda or "ciao" in domanda:
        parla("Ciao! A presto signore.")
        break

    if any(x in domanda for x in ["zitto", "silenzio", "sta zitto", "sh", "basta", "taci", "stop"]):
        stop_speaking = True
        engine.stop()  # forza lo stop immediato
        print("🔇 Silenzio attivato.")
        continue  # torna subito in ascolto senza rispondere

    elif "jarvis" in domanda or "giarvis" in domanda or "gliarvis" in domanda:  # parola di attivazione

        citta = weather.trova_citta(domanda)
        if citta and any(
                parola in domanda for parola in ["meteo", "tempofa", "previsioni", "piove", "fa caldo", "fa freddo"]):
            print(f"🔍 Cerco il meteo per {citta}...")
            risposta = weather.previsione_meteo(citta)
            parla(risposta)
            continue

        if "sono io" in domanda:
            risposta = rispondi_con_nome(domanda)
            parla(risposta)



        risposta = rispondi(domanda)
        print(f"AI: {risposta}")
        parla(risposta)