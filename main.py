import speech_recognition as sr #riconoscimento vocale
import pyttsx3 # TTS(text to speech)
import os #interazione con sistema operativo
import google.generativeai as genai #sdk per utilizzare gemini
import threading # concorrenza
from dotenv import load_dotenv #gestione variabili d'ambiente
import weather #api meteo 
import atexit
import subprocess
import pygame as pg# libreria per ui
import math #utilizzaremo sin e cos per la pulsazione della ui
#import random # Serve per l'effetto glitch visivo - rimosso perché non usato nell'animazione video

# --- VARIABILI GLOBALI ---
is_speaking = False #per animare la ui quando Jarvis parla
running = True # Variabile globale per chiudere tutto pulitamente

# Carica variabili d'ambiente che sono scritte nel file .env
load_dotenv()

# --- CONFIGURAZIONE API GEMINI ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Errore: imposta la variabile d'ambiente della chiave API")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")  # Usa Flash per maggiore velocità
chat = model.start_chat()  # Mantiene la cronologia della conversazione della sessione attuale

# --- CONFIGURAZIONE VOCALE (Versione Mac Stabile) ---
NOME_PREFERITO = "Iron Man"

 
def uccidi_voce_mac():
    try:
        # Silenzia eventuali errori se non c'è nessuna voce in riproduzione
        subprocess.run(["killall", "say"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except:
        pass

# Registriamo la funzione come "ultima azione da fare prima di morire"
atexit.register(uccidi_voce_mac)


# 2. Aggiorniamo la funzione parla usando subprocess al posto di os.system
def parla(testo):
    global is_speaking
    print(f"🔊 Jarvis: {testo}")

    # Ferma immediatamente qualsiasi voce precedente
    subprocess.run(["killall", "say"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    def esegui_voce():
        global is_speaking
        is_speaking = True
        try:
            testo_sicuro = testo.replace("'", "").replace('"', "")
            subprocess.run(["say", "-v", "Luca", testo_sicuro])
        except Exception as e:
            print(f"Errore voce: {e}")
        finally:
            is_speaking = False

    # Avvia la riproduzione in un thread indipendente
    threading.Thread(target=esegui_voce, daemon=True).start()


def ascolta(recognizer, mic):
    with mic as source:
        print("Listening...", end="\r", flush=True)
        try:
            # timeout: se non parlo entro 5s, smette di ascoltare
            # phrase_time_limit: IMPORTANTE per evitare che si blocchi se c'è rumore di fondo
            audio = recognizer.listen(source, timeout=4, phrase_time_limit=5)

            # Riconoscimento Google
            testo = recognizer.recognize_google(audio, language="it-IT") 
            print(f"\nTu: {testo}")
            return testo.lower()

        except sr.WaitTimeoutError: #Eccezione se l'utente non parla
            return None
        except sr.UnknownValueError: #Non capisce cosa è stato detto
            return None
        except sr.RequestError: #Richiesta a google fallita
            parla("C'è un problema di connessione.")
            return None
        except Exception as e: #Qualsiasi altra eccezione imprevista
            print(f"Errore ascolto: {e}")
            return None


#pone la domanda a gemini e ritorna la risposta
def rispondi_gemini(domanda):
    try:
        if not api_key: return "Chiave API non configurata."
        response = chat.send_message(domanda)
        return response.text
    except Exception as e:
        return f"Errore nei circuiti: {str(e)}"

# --- CLASSI E FUNZIONI GRAFICHE INTEGRATE ---

class imageHandler:
  """Gestore per il caricamento e il rendering sequenziale di immagini da 'JarvisGUIPart 11.txt'."""
  def __init__ ( self ):
    self.pics = dict()

  def loadFromFile ( self, filename, id=None ):
    if id == None: id = filename
    # pygame.image.load(filename).convert() da JarvisGUIPart 11.txt
    self.pics [ id ] = pg.image.load ( filename ).convert_alpha()

  def render ( self, surface, id, position = None, clear = False, size = None ):
    if clear == True:
      surface.fill ( (5,2,23) ) # background color from JarvisGUIPart 11.txt
    if position == None: picX = int ( surface.get_width() / 2 - self.pics [ id ].get_width() / 2 )
    else: picX, picY = position
    if size == None: surface.blit ( self.pics [ id ], ( picX, picY ) )
    else: surface.blit ( pg.transform.smoothscale ( self.pics [ id ], size ), ( picX, picY ) )


def main_ui():
    global running
    pg.init() 
    screen = pg.display.set_mode((600, 600)) 
    pg.display.set_caption("J.A.R.V.I.S.") 
    clock = pg.time.Clock()
    
    handler = imageHandler()
    center = (300, 300)
    
    # --- IMPOSTA IL NUMERO TOTALE DI FOTOGRAMMI QUI ---
    
    totale_fotogrammi = 148
    
    for i in range(1, totale_fotogrammi + 1):
        placeholder_path = f"jarvisface/{i}.jpg" 
        if os.path.exists(placeholder_path):
            handler.loadFromFile(placeholder_path, str(i))
        else:
            print(f"⚠️ Avviso: File non trovato in {placeholder_path}")

    frame_size = (500, 500) 
    frame_position = (center[0] - frame_size[0] // 2, center[1] - frame_size[1] // 2) 

    # Variabile per contare i frame in modo fluido (usiamo i decimali)
    current_frame_index = 1.0 
    
    # VELOCITÀ ANIMAZIONE: 0.5 significa che cambia immagine ogni 2 tick (circa 30 FPS effettivi)
    # Alzalo (es. 0.8) per farla andare più veloce, abbassalo (es. 0.2) per rallentarla
    velocita_base = 0.2 # Velocità fotogrammi quando è in silenzio
    
    # Variabili per l'analizzatore vocale simulato
    scala_corrente = 1.0
    scala_target = 1.0

    while running:
        for event in pg.event.get(): 
            if event.type == pg.QUIT: 
                os.system("killall say") 
                running = False 
                os._exit(0)

        screen.fill((5, 2, 23))

        indice_intero = int(current_frame_index)
        current_frame_index_str = str(indice_intero)
        
        if current_frame_index_str in handler.pics:
            
            # --- LOGICA SIMULAZIONE SPETTRO VOCALE ---
            if is_speaking:
                velocita_corrente = 0.6
                
                # Il 30% delle volte per ogni frame, genera un nuovo "picco" vocale (sillaba)
                # Questo crea l'effetto irregolare e scattante tipico di una voce reale
                import random
                if random.random() < 0.3: 
                    # Grandezza casuale tra il 100% e il 115% del normale
                    scala_target = random.uniform(1.0, 1.15) 
            else:
                velocita_corrente = velocita_base
                scala_target = 1.0 # Torna normale in silenzio

            # Interpolazione fluida: avvicina gradualmente la grandezza corrente a quella target
            # Questo ammorbidisce i picchi, rendendo l'impulso simile all'onda di Siri
            scala_corrente += (scala_target - scala_corrente) * 0.25 

            # Applica la scala calcolata
            dim_x = int(frame_size[0] * scala_corrente)
            dim_y = int(frame_size[1] * scala_corrente)
            dimensione_attuale = (dim_x, dim_y)

            # Ricalcola la posizione per tenerlo centrato
            pos_attuale = (center[0] - dimensione_attuale[0] // 2, center[1] - dimensione_attuale[1] // 2)

            handler.render(screen, current_frame_index_str, pos_attuale, clear=False, size=dimensione_attuale)
            
            # Avanzamento fotogrammi
            current_frame_index += velocita_corrente
            if current_frame_index >= totale_fotogrammi + 1:
                current_frame_index = 1.0 
                
        else:
            pg.draw.circle(screen, (0, 100, 150), center, 100, 2)

        pg.display.flip() 
        clock.tick(60) 
    
    pg.quit()
    subprocess.run(["killall", "say"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    os._exit(0)

def logica_jarvis():
    global running
    # --- CALIBRAZIONE SPOSTATA QUI PER NON BLOCCARE UI ---
    print("Calibrazione microfono in corso...")
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source: # apre lo stream audio
        recognizer.adjust_for_ambient_noise(source, duration=1) # calibra il riconoscimento in base al rumore ambientale
        recognizer.energy_threshold = 300  # Soglia base dalla quale il suono è considerato come voce
        recognizer.dynamic_energy_threshold = True  # Adatta leggermente il treshold
        recognizer.pause_threshold = 0.8  # Tempo di silenzio per considerare la frase finita
    
    # --- LOOP PRINCIPALE ---
    print("\n--- JARVIS ATTIVO ---")
    parla(f"Sistemi online. Ciao {NOME_PREFERITO}.")

    while running:
        # Passiamo mic e recognizer alla funzione
        testo_utente = ascolta(recognizer, mic)
        if not testo_utente:
            continue  # Se non sente nulla, ricomincia subito il ciclo

        # --- PREVENZIONE AUTO-ASCOLTO ED INTERRUZIONE ---
        # Se Jarvis sta parlando, accetta SOLO i comandi per zittirlo
        if is_speaking:
            if any(parola in testo_utente for parola in ["stop", "basta", "zitto", "fermati"]):
                subprocess.run(["killall", "say"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                print("🛑 Jarvis silenziato.")
            else:
                # Ignora le altre parole perché probabilemente è la sua stessa voce
                print("🗣️ Ignoro l'audio (Jarvis sta parlando)...")
            continue # Ricomincia il ciclo senza passare il testo a Gemini

        # 1. Comandi di Uscita totale
        if any(parola in testo_utente for parola in ["esci", "spegniti", "addio"]):
            parla("Disattivazione sistemi. A presto.")
            subprocess.run(["killall", "say"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            running = False
            os._exit(0)

        # 2. Rilevamento Parola Chiave "Jarvis" (o varianti)
        keyword_detected = any(k in testo_utente for k in ["jarvis", "giarvis", "ciarvis"])

        # Nota: nel tuo codice c'era "or True". Se vuoi che risponda SEMPRE
        # anche se non dici "Jarvis", lascialo. Altrimenti rimuovi "or True".
        if keyword_detected or True: 
            
            # Pulisce la frase togliendo la parola chiave
            comando_pulito = testo_utente.replace("jarvis", "").replace("giarvis", "").replace("ciarvis", "").strip()

            # Se ha detto SOLO "Jarvis", chiedi cosa vuole
            if not comando_pulito:
                parla("Dimmi pure.")
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
                    risposta = rispondi_gemini(comando_pulito)
                    parla(risposta)
                continue

            # 4. Risposta Generica (Gemini)
            print("🤖 Elaborazione risposta...")
            risposta = rispondi_gemini(comando_pulito)

            # Stampa e Parla
            print(f"Jarvis: {risposta}")
            parla(risposta)


if __name__ == "__main__":
    #Inizialmente avvio la logica di jarvis su un thread secondario
    #macos richiede che la ui venga eseguita sul thread principale
    thread_jarvis = threading.Thread(target = logica_jarvis, daemon = True)
    thread_jarvis.start()

    print("Avvio UI...")
    main_ui()