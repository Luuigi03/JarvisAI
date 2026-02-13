import speech_recognition as sr #riconoscimento vocale
import pyttsx3 # TTS(text to speech)
import os #interazione con sistema operativo
import google.generativeai as genai #sdk per utilizzare gemini
import threading # concorrenza
from dotenv import load_dotenv #gestione variabili d'ambiente
import weather #api meteo 
import pygame as pg# libreria per ui
import threading #La ui sarà gestita su un thread separato da quello della logica di ascolto ecc..
import math #utilizzaremo sin e cos per la pulsazione della ui
import random # Serve per l'effetto glitch visivo

is_speaking = False #per animare la ui quando Jarvis parla

# Carica variabili d'ambiente che sono scritte nel file .env
load_dotenv()

# --- CONFIGURAZIONE API GEMINI ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Gestione errore soft per evitare crash se manca la chiave durante il test UI
    print("ATTENZIONE: Chiave API mancante. La logica AI potrebbe non funzionare.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")  # Usa Flash per maggiore velocità
    chat = model.start_chat()  # Mantiene la cronologia della conversazione della sessione attuale

# --- CONFIGURAZIONE VOCALE ---
recognizer = sr.Recognizer() # oggetto per la gestione del riconoscimento vocale STT
engine = pyttsx3.init() # oggetto per la gestione dello TTS
engine.setProperty('rate', 150)  # Velocità voce. Rate=parole al minuto
engine.setProperty('volume', 1.0) # 1.0 = volume al massimo

#Variabili globali
stop_speaking = False
NOME_PREFERITO = "Iron Man"

# --- SETUP INIZIALE MICROFONO ---
# Nota: Spostato dentro la logica per evitare blocchi all'avvio della UI, ma manteniamo il print
print("Inizializzazione sistema...")


def parla(testo):
    global stop_speaking, is_speaking
    stop_speaking = False

    # Debug visivo per essere sicuri che la funzione venga chiamata
    print(f"🔊 Tentativo di riproduzione audio: {testo}")

    is_speaking = True
    try:
        engine.say(testo)
        engine.runAndWait() # Questo blocca il thread 'logica_jarvis' finché non finisce di parlare
    except RuntimeError:
        # Gestisce il caso in cui il loop dell'engine sia già attivo (raro se non usi thread annidati)
        print("Errore: Engine loop già attivo")
        pass
    finally:
        is_speaking = False


def ascolta():
    # Definiamo mic qui per evitare conflitti di init
    mic = sr.Microphone()
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
        if not api_key: return "Chiave API non configurata."
        response = chat.send_message(domanda)
        return response.text
    except Exception as e:
        return f"Mi dispiace, c'è stato un errore nei miei circuiti: {str(e)}"

# --- CLASSI GRAFICHE (Aggiunte per l'effetto video) ---
class GlitchText:
    def __init__(self, text, font_size, center_pos):
        self.font = pg.font.Font(None, font_size) 
        self.base_surf = self.font.render(text, True, (100, 255, 255))
        self.rect = self.base_surf.get_rect(center=center_pos)
        self.glitch_intensity = 0.0

    def draw(self, surface, active):
        target = 1.0 if active else 0.0
        self.glitch_intensity += (target - self.glitch_intensity) * 0.1
        
        if self.glitch_intensity < 0.1:
            surface.blit(self.base_surf, self.rect)
            return

        slice_h = int(max(2, 15 * self.glitch_intensity))
        for y in range(0, self.rect.height, slice_h):
            slice_rect = pg.Rect(0, y, self.rect.width, slice_h)
            offset_x = random.randint(-5, 5) if random.random() < self.glitch_intensity else 0
            surface.blit(self.base_surf, (self.rect.x + offset_x, self.rect.y + y), slice_rect)

def draw_reactor(screen, center, timer, active):
    # Colori
    cyan = (0, 200, 200)
    bright_cyan = (150, 255, 255)
    
    # Velocità rotazione
    speed = timer * 0.1 if active else timer * 0.02
    
    # Cerchio esterno (fisso con glow)
    pg.draw.circle(screen, (0, 50, 60), center, 220, 2)
    pg.draw.circle(screen, (0, 100, 100), center, 200, 5)

    # Anello rotante segmentato
    num_seg = 12
    for i in range(num_seg):
        angle = speed + (i * (2 * math.pi / num_seg))
        rect = pg.Rect(center[0]-180, center[1]-180, 360, 360)
        pg.draw.arc(screen, cyan, rect, angle, angle + 0.4, 4)

    # Nucleo Pulsante
    pulse = math.sin(timer * 0.2) * 10 if active else math.sin(timer * 0.05) * 5
    radius = int(80 + pulse)
    
    # Glow nucleo (trasparenza simulata disegnando cerchi multipli)
    pg.draw.circle(screen, (0, 30, 40), center, radius) 
    pg.draw.circle(screen, bright_cyan, center, radius, 3)
    pg.draw.circle(screen, (255, 255, 255), center, int(radius * 0.8), 1)


def main_ui():
    pg.init()
    # Aumentiamo leggermente la risoluzione per l'effetto grafico
    screen = pg.display.set_mode((600, 600)) 
    pg.display.set_caption("J.A.R.V.I.S.") #titolo finestra
    clock = pg.time.Clock()
    running = True

    #Variabili animazione
    base_radius = 100
    animation_timer = 0
    
    # Inizializza testo
    center = (300, 300)
    jarvis_text = GlitchText("JARVIS", 100, center)

    while running:
        for event in pg.event.get(): #recupera tutti gli eventi in coda
            if event.type == pg.QUIT: 
                running = False # Controlla se l'utente ha chiuso la finestra
                os._exit(0)

        screen.fill((5, 15, 25)) #Sfondo blu molto scuro (quasi nero)
   
        # Incremento timer continuo per fluidità
        animation_timer += 1

        #Logica animazione
        # Passiamo lo stato "is_speaking" alle funzioni di disegno
        
        # 1. Disegna il Reattore Arc
        draw_reactor(screen, center, animation_timer, is_speaking)

        # 2. Disegna il Testo Glitchato (sopra il reattore)
        jarvis_text.draw(screen, is_speaking)

        # Effetto particelle/disturbo se parla
        if is_speaking and random.random() > 0.8:
            rx = random.randint(0, 600)
            ry = random.randint(0, 600)
            pg.draw.circle(screen, (200, 255, 255), (rx, ry), 2)

        pg.display.flip() #mostra ciò che è stato disegnato
        clock.tick(60) #60fps
    
    pg.quit()


def logica_jarvis():
    # --- CALIBRAZIONE SPOSTATA QUI PER NON BLOCCARE UI ---
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1) 
        recognizer.energy_threshold = 300 
    
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
            stop_speaking = True
            os._exit(0)

        # 2. Rilevamento Parola Chiave "Jarvis" (o varianti)
        keyword_detected = any(k in testo_utente for k in ["jarvis", "giarvis", "ciarvis"])

        # Nota: Qui forziamo la risposta anche senza parola chiave se vuoi testare velocemente
        # Rimuovi "or True" se vuoi usare solo la parola chiave rigorosamente
        if keyword_detected or True: 
            
            # Pulisce la frase togliendo la parola chiave per mandarla pulita alle funzioni
            comando_pulito = testo_utente.replace("jarvis", "").replace("giarvis", "").strip()

            # Se ha detto SOLO "Jarvis", chiedi cosa vuole
            if not comando_pulito and keyword_detected:
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


if __name__ == "__main__":
    #Inizialmente avvio la logica di jarvis su un thread secondario
    #macos richiede che la ui venga eseguita sul thread principale
    thread_jarvis = threading.Thread(target = logica_jarvis, daemon = True)
    thread_jarvis.start()

    print("Avvio UI...")
    main_ui()