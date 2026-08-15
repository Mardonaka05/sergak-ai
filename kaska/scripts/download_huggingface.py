"""
HuggingFace'dan helmet detection datasetlarini yuklash.
Login kerak emas - hammasi ochiq.
"""
import sys
from pathlib import Path

DATASETS_ROOT = Path(r"D:\sergak dasturi\kaska\datasets")

HF_DATASETS = [
    {
        "name": "hf_keremberke_hardhat",
        "id": "keremberke/hard-hat-detection",
        "config": "full",
        "desc": "Hard Hat Detection (~5300 rasm)",
    },
]


def yolo_export(dataset, out_dir, split_name):
    """HuggingFace datasetni YOLO formatga eksport qilish."""
    img_dir = out_dir / "images" / split_name
    lbl_dir = out_dir / "labels" / split_name
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    n = 0
    for i, item in enumerate(dataset):
        img = item.get("image")
        objects = item.get("objects", {})
        if img is None or not objects.get("bbox"):
            continue

        # Rasm saqlash
        img_path = img_dir / f"img_{i:06d}.jpg"
        img.save(img_path, "JPEG")
        w, h = img.size

        # Label yozish
        lbl_path = lbl_dir / f"img_{i:06d}.txt"
        lines = []
        bboxes = objects.get("bbox", [])
        categories = objects.get("category", [])
        for bbox, cat in zip(bboxes, categories):
            # bbox formati: [x_min, y_min, width, height]
            x_min, y_min, bw, bh = bbox
            xc = (x_min + bw / 2) / w
            yc = (y_min + bh / 2) / h
            wn = bw / w
            hn = bh / h
            # 0 = helmet, 1 = head (no_helmet uchun)
            cls = 0 if cat == 0 else 1
            lines.append(f"{cls} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}")
        if lines:
            lbl_path.write_text("\n".join(lines))
            n += 1

        if (i + 1) % 500 == 0:
            print(f"    {i+1} ta...")
    return n


def main():
    try:
        from datasets import load_dataset
    except ImportError:
        print("[!] HuggingFace datasets paketi yo'q. O'rnatish:")
        print(r'    & "D:\sergak dasturi\backend\venv\Scripts\python.exe" -m pip install datasets pillow')
        sys.exit(1)

    DATASETS_ROOT.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"  HuggingFace'dan {len(HF_DATASETS)} ta dataset yuklash")
    print("=" * 70)

    for ds_info in HF_DATASETS:
        print(f"\n[+] {ds_info['name']}")
        print(f"    {ds_info['desc']}")

        out_dir = DATASETS_ROOT / ds_info['name']
        if out_dir.exists() and any((out_dir / "labels").rglob("*.txt") if (out_dir / "labels").exists() else []):
            print(f"    [skip] allaqachon mavjud")
            continue

        try:
            print(f"    Yuklab olinmoqda (HuggingFace'dan)...")
            ds = load_dataset(ds_info['id'], ds_info.get('config'), trust_remote_code=True)

            # Train va test eksport qilish
            for split_key in ["train", "validation", "test"]:
                if split_key not in ds:
                    continue
                print(f"    [{split_key}] eksport qilinmoqda...")
                out_split = "valid" if split_key == "validation" else split_key
                n = yolo_export(ds[split_key], out_dir, out_split)
                print(f"    [OK] {split_key}: {n} ta rasm")

            # data.yaml
            yaml_path = out_dir / "data.yaml"
            yaml_path.write_text(
                f"path: {out_dir.as_posix()}\n"
                f"train: images/train\n"
                f"val: images/valid\n"
                f"test: images/test\n\n"
                f"nc: 2\n"
                f"names:\n"
                f"  0: helmet\n"
                f"  1: head\n",
                encoding="utf-8"
            )
        except Exception as e:
            print(f"    [X] xato: {str(e)[:200]}")

    print("\n" + "=" * 70)
    print("  TUGADI")
    print("=" * 70)


if __name__ == "__main__":
    main()
