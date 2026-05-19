# gradio_ui.py
import gradio as gr
from your_main_module import speak  # importa la tua funzione speak()

def generate_and_play(text: str, engine: str, speed: float, pitch: int):
    """Callback per Gradio: genera e restituisce l'audio."""
    try:
        if engine == "coqui":
            audio_file = _speak_coqui(text, speed=speed, pitch=pitch)
        elif engine == "elevenlabs":
            audio_file = _speak_elevenlabs(text)
        else:
            audio_file = _speak_gtts(text)
        return audio_file
    except Exception as e:
        gr.Warning(f"Errore: {str(e)}")
        return None

with gr.Blocks(title="🎙️ DIONISIO TTS Studio", theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🎙️ DIONISIO - TTS Multi-Engine Studio")
    
    with gr.Row():
        with gr.Column(scale=2):
            text_input = gr.Textbox(
                label="📝 Testo da sintetizzare",
                placeholder="Scrivi qui il testo in italiano...",
                lines=4,
                value="Ciao! Sono DIONISIO, il tuo assistente vocale."
            )
            
            with gr.Row():
                engine_dropdown = gr.Dropdown(
                    choices=["gtts", "coqui", "elevenlabs"],
                    value="coqui",
                    label="🔧 Motore TTS"
                )
                speed_slider = gr.Slider(
                    minimum=0.5, maximum=2.0, value=1.0, step=0.1,
                    label="⚡ Velocità (solo Coqui)"
                )
                pitch_slider = gr.Slider(
                    minimum=-12, maximum=12, value=0, step=1,
                    label="🎵 Pitch (solo Coqui)"
                )
            
            generate_btn = gr.Button("🎧 Genera e Riproduci", variant="primary")
        
        with gr.Column(scale=1):
            audio_output = gr.Audio(label="🔊 Anteprima Audio", type="filepath")
            status_text = gr.Textbox(label="📊 Stato", interactive=False)
    
    # ✅ Collegamenti
    generate_btn.click(
        fn=generate_and_play,
        inputs=[text_input, engine_dropdown, speed_slider, pitch_slider],
        outputs=[audio_output]
    ).then(
        fn=lambda: "✅ Generazione completata!",
        outputs=[status_text]
    )
    
    # 🔁 Reset veloce con Invio
    text_input.submit(
        fn=generate_and_play,
        inputs=[text_input, engine_dropdown, speed_slider, pitch_slider],
        outputs=[audio_output]
    )

if __name__ == "__main__":
    print("🚀 Avvio interfaccia Gradio su http://localhost:7860")
    demo.launch(share=False)  # share=True per link pubblico temporaneo