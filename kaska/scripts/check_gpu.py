"""
GPU + CUDA + PyTorch diagnostikasi.
PyTorch GPU-ni ko'rmayotgan bo'lsa, sababini topadi va yechimni ko'rsatadi.
"""
import subprocess
import sys


def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True).strip()
    except subprocess.CalledProcessError as e:
        return f"[ERROR] {e.output.strip()}"
    except FileNotFoundError:
        return "[ERROR] komanda topilmadi"


def print_section(title):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    print("=" * 70)
    print("  Sergak AI - GPU + PyTorch diagnostikasi")
    print("=" * 70)

    # 1. NVIDIA drayveri
    print_section("1) NVIDIA GPU va drayver")
    nvidia_smi = run("nvidia-smi")
    if "[ERROR]" in nvidia_smi:
        print("  [X] nvidia-smi ishlamadi!")
        print("      => Sizda NVIDIA drayveri yo'q yoki GPU yo'q")
        print("      => Yechim: https://www.nvidia.com/download/index.aspx dan drayver yuklab oling")
        gpu_ok = False
    else:
        print(nvidia_smi[:1200])
        gpu_ok = True

    # 2. nvcc (CUDA toolkit) - ixtiyoriy
    print_section("2) NVCC (CUDA toolkit) - ixtiyoriy")
    nvcc = run("nvcc --version")
    if "[ERROR]" in nvcc:
        print("  [i] nvcc yo'q (lekin bu muammo emas - PyTorch o'zining CUDA-sini olib keladi)")
    else:
        print(nvcc)

    # 3. PyTorch
    print_section("3) PyTorch holati")
    try:
        import torch
        print(f"  PyTorch versiya:   {torch.__version__}")
        print(f"  CUDA support:      {torch.cuda.is_available()}")
        print(f"  CUDA versiya:      {torch.version.cuda or 'YO''Q (cpu-only build!)'}")
        print(f"  cuDNN versiya:     {torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else 'YO''Q'}")
        print(f"  GPU soni:          {torch.cuda.device_count()}")

        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                print(f"  GPU[{i}]:           {torch.cuda.get_device_name(i)}")
                props = torch.cuda.get_device_properties(i)
                print(f"  GPU xotira:        {props.total_memory/1e9:.2f} GB")
                print(f"  Compute capability: {props.major}.{props.minor}")
            print()
            print("  [OK] HAMMASI ISHLAYAPTI! Trainingni boshlash mumkin.")
            return 0
        else:
            print()
            if not gpu_ok:
                print("  [X] Sizda GPU yo'q yoki drayveri o'rnatilmagan")
                return 1
            print("  [X] PyTorch GPU-ni ko'rmayapti!")
            print()
            print("  SABAB: Sizda CPU-only PyTorch o'rnatilgan.")
            print()
            print("  YECHIM:")
            print("  1. Avval eski PyTorch ni o'chiring:")
            print("       pip uninstall torch torchvision torchaudio -y")
            print()
            print("  2. CUDA versiyali PyTorch o'rnating:")
            print("     (NVIDIA RTX 3060/4060/4070 uchun CUDA 12.1 tavsiya etiladi)")
            print()
            print("       pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
            print()
            print("     Yoki CUDA 11.8 uchun (eski GPU-larda):")
            print("       pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
            print()
            print("  3. Qayta tekshirish:")
            print("       python scripts/check_gpu.py")
            return 1
    except ImportError:
        print("  [X] PyTorch o'rnatilmagan!")
        print("      pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        return 1


if __name__ == "__main__":
    sys.exit(main())
