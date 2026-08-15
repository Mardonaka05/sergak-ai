"""
Sergak AI - Real-time Kaska Aniqlash Test Skript.

Quvvatlaydi:
  1. Web kamera (real-time)
  2. Video fayl (.mp4, .avi, .mov, ...)
  3. Rasm fayl (.jpg, .png, ...)
  4. Rasmlar papkasi (batch)

Ishlash:
  python scripts/live_test.py
  python scripts/live_test.py --source 0        # web kamera
  python scripts/live_test.py --source video.mp4
  python scripts/live_test.py --source image.jpg
  python scripts/live_test.py --weights runs/helmet_v8l_640/weights/last.pt
  python scripts/live_test.py --conf 0.5 --device cpu

Tugmalar (live oyna):
  Q yoki ESC  - chiqish
  S           - hozirgi kadrni snapshot saqlash
  P           - pauza/davom etish
  + / -       - confidence chegarani oshirish/kamaytirish
"""
import argparse
import sys
import time
from pathlib import Path

# ---- Konfiguratsiya ----
PROJECT_ROOT = Path(r"D:\sergak dasturi\kaska")
DEFAULT_WEIGHTS_CANDIDATES = [
    PROJECT_ROOT / "runs" / "helmet_v8l_640" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "helmet_v8l_640" / "weights" / "last.pt",
]
DEFAULT_CONF = 0.40
DEFAULT_IMGSZ = 640
SNAPSHOT_DIR = PROJECT_ROOT / "runs" / "live_snapshots"

# Klass nomlari va ranglar (BGR — OpenCV)
CLASS_NAMES = {0: "helmet", 1: "no_helmet"}
CLASS_COLORS = {
    0: (0, 200, 0),       # yashil - helmet
    1: (0, 0, 255),       # qizil  - no_helmet
}


def find_default_weights():
    """Mavjud weights faylini topish."""
    for p in DEFAULT_WEIGHTS_CANDIDATES:
        if p.exists():
            return str(p)
    return None


def get_input_choice():
    """Interaktiv menyu."""
    print()
    print("=" * 60)
    print("  Sergak AI - Real-time Test")
    print("=" * 60)
    print("  Manba tanlang:")
    print("    1) Web kamera (real-time)")
    print("    2) Video fayl")
    print("    3) Rasm fayl")
    print("    4) Rasmlar papkasi")
    print("    0) Chiqish")
    print("=" * 60)
    choice = input("  Tanlov [1-4, 0=chiqish]: ").strip()
    if choice == "0":
        sys.exit(0)
    if choice == "1":
        idx = input("  Kamera indeksi [0]: ").strip() or "0"
        return int(idx), "webcam"
    if choice == "2":
        path = input("  Video fayl yo'li: ").strip().strip('"').strip("'")
        if not path or not Path(path).exists():
            print(f"  [X] Topilmadi: {path}")
            sys.exit(1)
        return path, "video"
    if choice == "3":
        path = input("  Rasm fayl yo'li: ").strip().strip('"').strip("'")
        if not path or not Path(path).exists():
            print(f"  [X] Topilmadi: {path}")
            sys.exit(1)
        return path, "image"
    if choice == "4":
        path = input("  Rasmlar papkasi yo'li: ").strip().strip('"').strip("'")
        if not path or not Path(path).is_dir():
            print(f"  [X] Papka topilmadi: {path}")
            sys.exit(1)
        return path, "folder"
    print("  [X] Noto'g'ri tanlov")
    sys.exit(1)


def draw_boxes(frame, results, conf_thresh):
    """Bbox larni rasmga chizish."""
    import cv2
    if results.boxes is None or len(results.boxes) == 0:
        return frame, 0, 0

    h_count = 0
    nh_count = 0
    boxes = results.boxes.xyxy.cpu().numpy()
    confs = results.boxes.conf.cpu().numpy()
    clss = results.boxes.cls.cpu().numpy().astype(int)

    for box, conf, cls in zip(boxes, confs, clss):
        if conf < conf_thresh:
            continue
        x1, y1, x2, y2 = map(int, box)
        color = CLASS_COLORS.get(cls, (255, 255, 255))
        label = f"{CLASS_NAMES.get(cls, str(cls))} {conf:.2f}"
        # Bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        # Label fon (chiroyli ko'rinish uchun)
        (tw, th), bl = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        if cls == 0:
            h_count += 1
        else:
            nh_count += 1
    return frame, h_count, nh_count


def draw_info(frame, fps, h, nh, conf_thresh, source_label, paused=False):
    """Top-left ma'lumot panelidagi yozuvlar."""
    import cv2
    H, W = frame.shape[:2]
    # Yarim shaffof panel
    overlay = frame.copy()
    cv2.rectangle(overlay, (5, 5), (310, 130), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    lines = [
        f"Sergak AI - Kaska aniqlash",
        f"Manba: {source_label}",
        f"FPS:   {fps:.1f}",
        f"Conf:  {conf_thresh:.2f}  (+/- bilan)",
        f"helmet:    {h}",
        f"no_helmet: {nh}",
    ]
    if paused:
        cv2.putText(frame, "PAUSED", (W // 2 - 80, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)

    y = 25
    for line in lines:
        cv2.putText(frame, line, (12, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        y += 18
    return frame


def process_image(weights, image_path, conf, imgsz, device):
    """Bitta rasmga inference."""
    import cv2
    from ultralytics import YOLO

    print(f"\n[+] Model yuklanmoqda: {weights}")
    model = YOLO(weights)

    frame = cv2.imread(str(image_path))
    if frame is None:
        print(f"[X] Rasm o'qib bo'lmadi: {image_path}")
        return

    t0 = time.time()
    results = model(frame, conf=conf, imgsz=imgsz, device=device, verbose=False)[0]
    dt = time.time() - t0

    frame, h, nh = draw_boxes(frame, results, conf)
    print(f"  helmet={h}  no_helmet={nh}  vaqt={dt*1000:.0f} ms")

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SNAPSHOT_DIR / f"result_{Path(image_path).stem}.jpg"
    cv2.imwrite(str(out_path), frame)
    print(f"  Natija saqlandi: {out_path}")

    # Ko'rsatish
    cv2.imshow("Sergak AI - Result (q=chiqish)", frame)
    while True:
        if cv2.waitKey(50) & 0xFF in (ord('q'), 27):
            break
    cv2.destroyAllWindows()


def process_folder(weights, folder_path, conf, imgsz, device):
    """Papkadagi barcha rasmlarga inference."""
    import cv2
    from ultralytics import YOLO

    folder = Path(folder_path)
    imgs = sorted([p for p in folder.iterdir()
                   if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")])
    if not imgs:
        print("[X] Papkada rasm topilmadi")
        return

    print(f"\n[+] Model yuklanmoqda: {weights}")
    model = YOLO(weights)
    print(f"[+] {len(imgs)} ta rasm topildi")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    cv2.namedWindow("Sergak AI - Folder (q=chiqish, space=keyingisi)", cv2.WINDOW_NORMAL)
    i = 0
    while i < len(imgs):
        img_path = imgs[i]
        frame = cv2.imread(str(img_path))
        if frame is None:
            i += 1
            continue
        results = model(frame, conf=conf, imgsz=imgsz, device=device, verbose=False)[0]
        frame, h, nh = draw_boxes(frame, results, conf)
        info = f"[{i+1}/{len(imgs)}] {img_path.name}  H={h} NH={nh}"
        cv2.putText(frame, info, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow("Sergak AI - Folder (q=chiqish, space=keyingisi)", frame)

        out_path = SNAPSHOT_DIR / f"folder_{img_path.stem}.jpg"
        cv2.imwrite(str(out_path), frame)
        print(f"  {info}")

        k = cv2.waitKey(0) & 0xFF
        if k in (ord('q'), 27):
            break
        elif k == ord('s'):  # snapshot
            pass  # allaqachon saqlangan
        i += 1
    cv2.destroyAllWindows()
    print(f"\n[+] Hammasi: {SNAPSHOT_DIR}")


def process_stream(weights, source, conf, imgsz, device, source_label):
    """Web kamera yoki video oqim uchun."""
    import cv2
    from ultralytics import YOLO

    print(f"\n[+] Model yuklanmoqda: {weights}")
    model = YOLO(weights)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[X] Manba ochilmadi: {source}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_src = cap.get(cv2.CAP_PROP_FPS) or 30
    print(f"[+] {source_label} ochildi: {width}x{height} @ {fps_src:.0f} FPS")

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    cv2.namedWindow("Sergak AI - Live", cv2.WINDOW_NORMAL)

    paused = False
    last_frame = None
    fps_smooth = 0.0
    snap_count = 0
    conf_thresh = conf
    last_time = time.time()

    print()
    print("  Tugmalar:")
    print("    Q yoki ESC  - chiqish")
    print("    S           - snapshot saqlash")
    print("    P           - pauza/davom")
    print("    + / -       - confidence o'zgartirish")
    print()

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("[+] Manba tugadi")
                break
            last_frame = frame.copy()
        else:
            if last_frame is None:
                continue
            frame = last_frame.copy()

        t0 = time.time()
        results = model(frame, conf=conf_thresh, imgsz=imgsz, device=device, verbose=False)[0]
        dt = time.time() - t0
        inst_fps = 1.0 / max(dt, 1e-6)
        fps_smooth = 0.9 * fps_smooth + 0.1 * inst_fps if fps_smooth > 0 else inst_fps

        frame, h, nh = draw_boxes(frame, results, conf_thresh)
        frame = draw_info(frame, fps_smooth, h, nh, conf_thresh, source_label, paused)

        cv2.imshow("Sergak AI - Live", frame)
        k = cv2.waitKey(1) & 0xFF
        if k in (ord('q'), 27):
            break
        elif k == ord('p'):
            paused = not paused
            print(f"  [{'pauza' if paused else 'davom'}]")
        elif k == ord('s'):
            snap_count += 1
            ts = time.strftime("%Y%m%d_%H%M%S")
            out = SNAPSHOT_DIR / f"snap_{ts}_{snap_count:03d}.jpg"
            cv2.imwrite(str(out), frame)
            print(f"  [snapshot] {out}")
        elif k == ord('+') or k == ord('='):
            conf_thresh = min(0.95, conf_thresh + 0.05)
        elif k == ord('-') or k == ord('_'):
            conf_thresh = max(0.05, conf_thresh - 0.05)

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[+] Snapshotlar: {SNAPSHOT_DIR}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=None,
                        help="0 = webcam, 'video.mp4', 'image.jpg', 'folder/'")
    parser.add_argument("--weights", default=None, help="best.pt yoki last.pt")
    parser.add_argument("--conf", type=float, default=DEFAULT_CONF)
    parser.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ)
    parser.add_argument("--device", default="0",
                        help="'0' = GPU, 'cpu' = CPU. Training vaqtida 'cpu' tavsiya etiladi.")
    args = parser.parse_args()

    # Weights ni tanlash
    weights = args.weights or find_default_weights()
    if not weights or not Path(weights).exists():
        print(f"[X] Model vazn fayli topilmadi!")
        print(f"    Kutilgan joy: {DEFAULT_WEIGHTS_CANDIDATES[0]}")
        print(f"    yoki:          {DEFAULT_WEIGHTS_CANDIDATES[1]}")
        sys.exit(1)
    print(f"[+] Weights: {weights}")
    print(f"[+] Device:  {args.device}")
    print(f"[+] Conf:    {args.conf}")

    # Manba aniqlash
    if args.source is None:
        source, kind = get_input_choice()
    else:
        s = args.source
        if s.isdigit():
            source, kind = int(s), "webcam"
        elif Path(s).is_dir():
            source, kind = s, "folder"
        else:
            sp = Path(s)
            if not sp.exists():
                print(f"[X] Topilmadi: {s}")
                sys.exit(1)
            ext = sp.suffix.lower()
            if ext in (".jpg", ".jpeg", ".png", ".bmp"):
                source, kind = str(sp), "image"
            else:
                source, kind = str(sp), "video"

    # Ishga tushirish
    if kind == "image":
        process_image(weights, source, args.conf, args.imgsz, args.device)
    elif kind == "folder":
        process_folder(weights, source, args.conf, args.imgsz, args.device)
    elif kind == "webcam":
        label = f"Web kamera #{source}"
        process_stream(weights, source, args.conf, args.imgsz, args.device, label)
    elif kind == "video":
        label = f"Video: {Path(source).name}"
        process_stream(weights, source, args.conf, args.imgsz, args.device, label)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] To'xtatildi")
