
try:
    import torch
    print("✅ PyTorch imported successfully")
    print(f"Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
except OSError as e:
    print(f"❌ PyTorch DLL Error: {e}")
except ImportError as e:
    print(f"❌ PyTorch Import Error: {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
