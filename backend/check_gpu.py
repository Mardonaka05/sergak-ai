"""GPU/CUDA tekshirish skripti - Sergak AI uchun."""
import sys

print("=" * 64)
print("  Sergak AI - GPU / CUDA tekshiruv")
print("=" * 64)

# 1. Torch
try:
    import torch
    print(f"  [+] PyTorch versiyasi: {torch.__version__}")
    cuda_compiled = torch.version.cuda if torch.version.cuda else "YOQ"
    print(f"  [+] Compiled with CUDA: {cuda_compiled}")
except ImportError:
    print("  [X] PyTorch ornatilmagan!")
    sys.exit(1)

# 2. CUDA
print()
if torch.cuda.is_available():
    print(f"  [+] CUDA mavjud va ishlamoqda")
    print(f"  [+] Qurilmalar soni: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"      Qurilma {i}: {props.name}")
        print(f"        Xotira: {props.total_memory / (1024**3):.2f} GB")
        print(f"        Compute capability: {props.major}.{props.minor}")
        print(f"        Multiprocessors: {props.multi_processor_count}")
else:
    print("  [X] CUDA MAVJUD EMAS!")
    print()
    print("  Sabablari:")
    print("    1. PyTorch CUDA-siz ornatilgan (CPU-only)")
    print("    2. NVIDIA drayveri ornatilmagan")
    print("    3. GPU kompyuteringizda yoq")
    print()
    print("  Yechim - CUDA-PyTorch ornatish (Windows + NVIDIA GPU):")
    print()
    print('    & "D:\\sergak dasturi\\backend\\venv\\Scripts\\python.exe" -m pip uninstall torch torchvision -y')
    print('    & "D:\\sergak dasturi\\backend\\venv\\Scripts\\python.exe" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121')
    sys.exit(2)

# 3. Test inference
print()
print("  Test inference (CUDA tezligi)...")
try:
    import time
    x = torch.randn(1, 3, 640, 640).cuda()
    # Warm-up
    for _ in range(3):
        y = x * 2
    torch.cuda.synchronize()
    t0 = time.time()
    for _ in range(100):
        y = x * 2
    torch.cuda.synchronize()
    elapsed = (time.time() - t0) * 1000
    print(f"  [+] 100 ta operatsiya: {elapsed:.1f} ms ({elapsed/100:.2f} ms/iter)")
except Exception as e:
    print(f"  [X] Test xato: {e}")

# 4. ultralytics
print()
try:
    from ultralytics import YOLO
    print(f"  [+] ultralytics: ornatilgan")
except ImportError:
    print(f"  [X] ultralytics: yoq (pip install ultralytics)")

# 5. OpenCV
try:
    import cv2
    print(f"  [+] OpenCV versiyasi: {cv2.__version__}")
    # CUDA backend OpenCV uchun
    try:
        has_cuda_cv = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if has_cuda_cv:
            print(f"      OpenCV CUDA: BOR")
        else:
            print(f"      OpenCV CUDA: YOQ (lekin shart emas - YOLO ozi GPU ishlatadi)")
    except Exception:
        print(f"      OpenCV CUDA: YOQ (lekin shart emas)")
except Exception as e:
    print(f"  [X] OpenCV xato: {e}")

print()
print("  Xulosa:")
print("=" * 64)
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    print(f"  [OK] GPU TAYYOR - {gpu_name}")
    print(f"       Sergak AI GPU da ishlay oladi.")
    print(f"       Inference 5-20x tezroq boladi.")
else:
    print("  [X] GPU mavjud emas - CPU rejimida ishlaydi (sekin)")
print("=" * 64)
