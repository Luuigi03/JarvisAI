Questo progetto implementa un assistente vocale avanzato basato su un'architettura multi-threaded, integrando modelli di linguaggio di grandi dimensioni (LLM), elaborazione del segnale vocale e un'interfaccia grafica dinamica.

Key Features
Core AI Engine: Integrazione con Google Gemini 1.5 Flash per risposte a bassa latenza e alta capacità di ragionamento.

Multithreading Architecture: Gestione separata del loop grafico (Main Thread) e della logica di elaborazione IA/Audio (Background Thread) per evitare il blocco della UI durante le chiamate API.

Dynamic UI Rendering: Animazione basata su frame con simulazione di spettro vocale (interpolazione fluida della scala dei fotogrammi) tramite Pygame.

Contextual Commands: Sistema di filtraggio dei comandi per query meteorologiche via API esterne e gestione della cronologia della chat.

Speech System: * STT: Speech-to-Text tramite Google Web Speech API.

TTS: Text-to-Speech nativo macOS (say) ottimizzato con gestione dei segnali di sistema (killall) per l'interruzione immediata del parlato.

Tech Stack
Language: Python 3.x

AI: Google Generative AI (Gemini SDK)

Graphics: Pygame (Frame management & Image transformation)

Audio: SpeechRecognition, PyAudio, Subprocess (CLI interaction)

Environment: Dotenv (Secrets management)

System Architecture
L'applicazione è progettata per massimizzare la reattività:

Main Thread (UI): Gestisce il rendering a 60 FPS, calcola la pulsazione "vocal-driven" dei frame e intercetta gli eventi di chiusura.

Logic Thread: Gestisce il ciclo Listen -> Process -> Respond. Utilizza una variabile globale atomica is_speaking per sincronizzare lo stato dell'animazione con l'output audio.

Signal Handling: Utilizzo di atexit e subprocess per garantire che i processi audio pendenti vengano terminati correttamente alla chiusura del software.

Prerequisites
macOS (per il supporto nativo del comando say)

Chiave API di Google Gemini

Cartella jarvisface/ contenente i frame dell'animazione (formato .jpg, 1-148)

Installation & Setup:
Clone & Install Dependencies:
pip install speech_recognition google-generativeai pygame python-dotenv

Environment Configuration:
Crea un file .env nella root del progetto:
GOOGLE_API_KEY=tuo_codice_api
OPENWEATHER_API_KEY=tua_chiave_meteo  # Se prevista nel modulo weather

Run:
python main.py

Logic Flow
Interruzione Attiva: Il sistema monitora costantemente l'input anche mentre Jarvis parla. Se viene rilevata una keyword di interruzione (es. "stop"), il processo say viene terminato istantaneamente tramite segnale di sistema.

Prevenzione Eco: Implementato un delay di sicurezza di 0.5s post-riproduzione per evitare che il microfono catturi il riverbero della voce dell'assistente come nuovo input.

Prossimi Step Evolutivi:
- Implementazione di Vosk per il riconoscimento della "Wake Word" totalmente offline.