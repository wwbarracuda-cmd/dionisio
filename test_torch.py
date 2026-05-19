# test_torch.py
try:
    import torch
    print(f"✅ torch versione: {torch.__version__}")
    print(f"✅ CUDA disponibile: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()