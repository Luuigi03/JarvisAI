import speech_recognition as sr
import pyttsx3
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Utilizzo la api kaey di openaui
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Errore: imposta la variabile d'ambiente OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


recognizer = sr.Recognizer()
engine = pyttsx3.init()

def ascolta():
    with sr.Microphone() as source:
        print("Sono in ascolto...")

        audio = recognizer.listen(source)
        try:
            testo = recognizer.recognize_google(audio, language="it-IT")
            print(f"Hai detto: {testo}")
            return testo
        except:
            print("Non ho capito, riprova!")
            return None

def parla(testo):
    engine.say(testo)
    engine.runAndWait()

def rispondi(domanda):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": domanda}]
    )
    return response.choices[0].message.content


while True:
    domanda = ascolta()
    if domanda:
        if "esci" in domanda.lower():
            parla("Ciao! A presto.")
            break
        risposta = rispondi(domanda)
        print(f"AI: {risposta}")
        parla(risposta)