from brain import brain
from voice import speak
from utils import clean
from memory import load_memory, save_memory

memory = load_memory()

print("🤖 JARVIS MODULARE AVVIATO")

speak("Jarvis attivo")

while True:

    user = input("\n🧑 Tu: ")
    user = clean(user)

    if user in ["stop", "esci"]:
        speak("Sistema spento")
        break

    response = brain(user)

    memory["log"].append({
        "input": user,
        "output": response
    })

    save_memory(memory)

    speak(response)