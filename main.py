import speech_recognition as sr
import pyttsx3
import os
import google.generativeai as genai
from dotenv import load_dotenv
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


# Loop principale
print("Assistente vocale Gemini attivo! Di' 'esci' per terminare.")
parla("Come posso aiutarti?")

while True:
    domanda = ascolta()
    if domanda:
        if "esci" in domanda or "addio" in domanda or "ciao" in domanda:
            parla("Ciao! A presto.")
            break

        risposta = rispondi(domanda)
        print(f"AI: {risposta}")
        parla(risposta)