from brain import brain

print("🧠 Test DIONISIO Brain")
print("-" * 40)

test_inputs = [
    "Ciao, come ti chiami?",
    "Qual è la capitale d'Italia?",
    "Raccontami una barzelletta breve",
    "Grazie mille!",
]

for question in test_inputs:
    print(f"\n🧑 Tu: {question}")
    answer = brain(question)
    print(f"🤖 DIONISIO: {answer}")