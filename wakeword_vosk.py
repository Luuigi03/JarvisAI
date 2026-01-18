import json
import pyaudio
from vosk import Model, KaldiRecognizer

MODEL_PATH = "/Users/luigicocco/PycharmProjects/JarvisAI/models/vosk-it"
WAKE_WORD = "ehi jarvis"  # La nuova wake word

def attendi_wakeword():

    print("🎙 In attesa della parola di attivazione 'ehi mela'...")

    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(False)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8000
    )

    #stream.start_stream()

    try:
        while True:
            try:
                data = stream.read(4000, exception_on_overflow=False)
            except IOError:
                continue

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                testo = result.get("text", "").lower().strip()

                if testo == "ehi mela":
                    print("🔥 Wake word 'ehi mela' rilevata!")
                    return
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
