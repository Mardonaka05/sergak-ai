"""
Sergak AI - Kaska aniqlash GUI Test Application

Tkinter asosida sodda dastur:
  - Web kamera ochish (1 ta tugma)
  - Video fayl tanlash (file dialog)
  - Rasm fayl tanlash (file dialog)
  - Rasmlar papkasi tanlash (folder dialog)

Real-time:
  - Bbox'lar bilan video oqim
  - FPS, helmet/no_helmet hisoblagichlar
  - Confidence slider (0.1 - 0.95)
  - Pauza/davom, Snapshot tugmalari
  - Model weight tanlash (best.pt yoki istalgan .pt fayl)
"""
import threading
import time
import sys
from pathlib import Path
from queue import Queue, Empty

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Lazy imports — secondary heavy libs
cv2 = None
Image = None
ImageTk = None
YOLO = None


# ===== Konfiguratsiya =====
PROJECT_ROOT = Path(r"D:\sergak dasturi\kaska")
DEFAULT_WEIGHTS_CANDIDATES = [
    PROJECT_ROOT / "runs" / "helmet_v8l_640" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "helmet_v8l_640" / "weights" / "last.pt",
]
SNAPSHOT_DIR = PROJECT_ROOT / "runs" / "live_snapshots"
DEFAULT_CONF = 0.40
DEFAULT_DEVICE = "0"        # GPU (RTX 4060) — TEZ
DEFAULT_IMGSZ = 480         # 640 dan kichikroq — VRAM tejaydi, training ga xalal bermaydi
DEFAULT_HALF = True         # FP16 (yarim aniqlik) — 2x tezroq, 50% kam VRAM
CLASS_COLORS = {0: (0, 200, 0), 1: (0, 0, 255)}  # BGR
CLASS_NAMES = {0: "helmet", 1: "no_helmet"}

# Display o'lcham
DISPLAY_W = 900
DISPLAY_H = 540


def lazy_import_cv():
    global cv2, Image, ImageTk
    if cv2 is None:
        import cv2 as _cv2
        from PIL import Image as _Image, ImageTk as _ImageTk
        cv2 = _cv2
        Image = _Image
        ImageTk = _ImageTk


def lazy_import_yolo():
    global YOLO
    if YOLO is None:
        from ultralytics import YOLO as _YOLO
        YOLO = _YOLO


def find_default_weights():
    for p in DEFAULT_WEIGHTS_CANDIDATES:
        if p.exists():
            return str(p)
    return ""


def draw_boxes(frame, results, conf_thresh):
    """Bbox larni rasmga chizish (cv2 frame)."""
    h_count = 0
    nh_count = 0
    if results.boxes is None or len(results.boxes) == 0:
        return frame, 0, 0
    boxes = results.boxes.xyxy.cpu().numpy()
    confs = results.boxes.conf.cpu().numpy()
    clss = results.boxes.cls.cpu().numpy().astype(int)
    for box, conf, cls in zip(boxes, confs, clss):
        if conf < conf_thresh:
            continue
        x1, y1, x2, y2 = map(int, box)
        color = CLASS_COLORS.get(cls, (255, 255, 255))
        label = f"{CLASS_NAMES.get(cls, str(cls))} {conf:.2f}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        if cls == 0:
            h_count += 1
        else:
            nh_count += 1
    return frame, h_count, nh_count


class SergakApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sergak AI - Kaska Aniqlash Test")
        self.root.geometry("1100x780")
        self.root.minsize(900, 700)
        self.root.configure(bg="#1e1e2e")

        # State
        self.weights_path = tk.StringVar(value=find_default_weights())
        self.conf_var = tk.DoubleVar(value=DEFAULT_CONF)
        self.device_var = tk.StringVar(value=DEFAULT_DEVICE)
        self.imgsz_var = tk.IntVar(value=DEFAULT_IMGSZ)
        self.half_var = tk.BooleanVar(value=DEFAULT_HALF)
        self.status_var = tk.StringVar(value="Tayyor")
        self.fps_var = tk.StringVar(value="FPS: 0.0")
        self.helmet_var = tk.StringVar(value="helmet: 0")
        self.no_helmet_var = tk.StringVar(value="no_helmet: 0")
        self.source_label_var = tk.StringVar(value="Manba: (tanlanmagan)")

        # Model & thread
        self.model = None
        self.thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()  # set = pauza
        self.frame_queue = Queue(maxsize=2)  # latest frame for display
        self.snapshot_request = threading.Event()
        self.current_frame_for_save = None

        # Folder mode state
        self.folder_files = []
        self.folder_index = 0

        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

        self._build_ui()
        self._tick_display()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("Accent.TButton", foreground="white", background="#3b82f6")
        style.configure("Stop.TButton", foreground="white", background="#dc2626")

        # ===== TOP: Title bar =====
        top = tk.Frame(self.root, bg="#1e1e2e", pady=10)
        top.pack(fill="x", padx=12, pady=(8, 0))
        tk.Label(top, text="Sergak AI - Kaska Aniqlash",
                 font=("Segoe UI", 18, "bold"), bg="#1e1e2e", fg="#fef08a").pack(side="left")
        tk.Label(top, text="  Real-time Test Application",
                 font=("Segoe UI", 11), bg="#1e1e2e", fg="#94a3b8").pack(side="left")

        # ===== Model row =====
        model_row = tk.Frame(self.root, bg="#1e1e2e")
        model_row.pack(fill="x", padx=12, pady=4)
        tk.Label(model_row, text="Model:", bg="#1e1e2e", fg="#e2e8f0",
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        self.weights_entry = ttk.Entry(model_row, textvariable=self.weights_path, width=80)
        self.weights_entry.pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(model_row, text="Tanlash",
                   command=self.choose_weights).pack(side="left", padx=4)

        # ===== Source buttons row =====
        source_row = tk.Frame(self.root, bg="#1e1e2e")
        source_row.pack(fill="x", padx=12, pady=8)
        tk.Label(source_row, text="Manba:", bg="#1e1e2e", fg="#e2e8f0",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
        ttk.Button(source_row, text="📷 Web Kamera", style="Accent.TButton",
                   command=lambda: self.start_source("webcam")).pack(side="left", padx=4)
        ttk.Button(source_row, text="🎬 Video Fayl",
                   command=lambda: self.start_source("video")).pack(side="left", padx=4)
        ttk.Button(source_row, text="🖼️ Rasm Fayl",
                   command=lambda: self.start_source("image")).pack(side="left", padx=4)
        ttk.Button(source_row, text="📁 Rasmlar Papkasi",
                   command=lambda: self.start_source("folder")).pack(side="left", padx=4)
        ttk.Button(source_row, text="⏹ To'xtatish", style="Stop.TButton",
                   command=self.stop_stream).pack(side="left", padx=12)

        # ===== Display canvas =====
        canvas_frame = tk.Frame(self.root, bg="#0f172a", relief="solid", bd=1)
        canvas_frame.pack(fill="both", expand=True, padx=12, pady=8)
        self.canvas = tk.Canvas(canvas_frame, bg="#0f172a",
                                width=DISPLAY_W, height=DISPLAY_H,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._show_welcome()

        # ===== Stats row =====
        stats = tk.Frame(self.root, bg="#1e1e2e")
        stats.pack(fill="x", padx=12, pady=4)
        tk.Label(stats, textvariable=self.source_label_var, bg="#1e1e2e", fg="#cbd5e1",
                 font=("Segoe UI", 10)).pack(side="left", padx=8)
        tk.Label(stats, textvariable=self.fps_var, bg="#1e1e2e", fg="#fde047",
                 font=("Consolas", 11, "bold")).pack(side="left", padx=20)
        tk.Label(stats, textvariable=self.helmet_var, bg="#1e1e2e", fg="#22c55e",
                 font=("Consolas", 11, "bold")).pack(side="left", padx=12)
        tk.Label(stats, textvariable=self.no_helmet_var, bg="#1e1e2e", fg="#ef4444",
                 font=("Consolas", 11, "bold")).pack(side="left", padx=12)

        # ===== Controls row =====
        ctrl = tk.Frame(self.root, bg="#1e1e2e")
        ctrl.pack(fill="x", padx=12, pady=6)

        tk.Label(ctrl, text="Confidence:", bg="#1e1e2e", fg="#e2e8f0",
                 font=("Segoe UI", 10)).pack(side="left", padx=(4, 4))
        self.conf_label = tk.Label(ctrl, text=f"{DEFAULT_CONF:.2f}",
                                    bg="#1e1e2e", fg="#fde047",
                                    font=("Consolas", 10, "bold"), width=5)
        self.conf_label.pack(side="left", padx=(0, 6))
        conf_slider = ttk.Scale(ctrl, from_=0.05, to=0.95,
                                 variable=self.conf_var,
                                 orient="horizontal", length=300,
                                 command=lambda v: self.conf_label.configure(
                                     text=f"{float(v):.2f}"))
        conf_slider.pack(side="left", padx=4)

        tk.Label(ctrl, text="  Device:", bg="#1e1e2e", fg="#e2e8f0",
                 font=("Segoe UI", 10)).pack(side="left", padx=(12, 4))
        device_combo = ttk.Combobox(ctrl, textvariable=self.device_var, width=6,
                                     values=["0", "cpu"], state="readonly")
        device_combo.pack(side="left")

        tk.Label(ctrl, text=" ImgSz:", bg="#1e1e2e", fg="#e2e8f0",
                 font=("Segoe UI", 10)).pack(side="left", padx=(8, 2))
        imgsz_combo = ttk.Combobox(ctrl, textvariable=self.imgsz_var, width=5,
                                    values=[320, 416, 480, 640, 800],
                                    state="readonly")
        imgsz_combo.pack(side="left")

        half_check = ttk.Checkbutton(ctrl, text="FP16",
                                      variable=self.half_var)
        half_check.pack(side="left", padx=(8, 0))

        ttk.Button(ctrl, text="⏸ Pauza/Davom",
                   command=self.toggle_pause).pack(side="left", padx=12)
        ttk.Button(ctrl, text="📸 Snapshot",
                   command=self.request_snapshot).pack(side="left", padx=4)
        ttk.Button(ctrl, text="➡ Keyingi (papka rejim)",
                   command=self.next_folder_frame).pack(side="left", padx=4)

        # ===== Status bar =====
        status = tk.Frame(self.root, bg="#0f172a", height=24)
        status.pack(fill="x", side="bottom")
        tk.Label(status, textvariable=self.status_var,
                 bg="#0f172a", fg="#cbd5e1",
                 font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=10, pady=3)

    def _show_welcome(self):
        self.canvas.delete("all")
        w, h = DISPLAY_W, DISPLAY_H
        self.canvas.create_text(w//2, h//2 - 40,
                                text="Sergak AI", fill="#fde047",
                                font=("Segoe UI", 36, "bold"))
        self.canvas.create_text(w//2, h//2 + 10,
                                text="Yuqoridagi tugmalardan birini tanlang:\n📷 Kamera   🎬 Video   🖼️ Rasm   📁 Papka",
                                fill="#94a3b8", font=("Segoe UI", 14),
                                justify="center")
        self.canvas.create_text(w//2, h//2 + 80,
                                text="DIQQAT: Training davom etyapti - 'cpu' device tavsiya etiladi",
                                fill="#f87171", font=("Segoe UI", 10, "italic"))

    # ============ Source handlers ============
    def choose_weights(self):
        path = filedialog.askopenfilename(
            title="Model vazn faylini tanlang",
            initialdir=str(PROJECT_ROOT / "runs"),
            filetypes=[("PyTorch weights", "*.pt"), ("Barchasi", "*.*")],
        )
        if path:
            self.weights_path.set(path)

    def _ensure_model(self):
        if self.model is not None:
            return True
        wp = self.weights_path.get().strip()
        if not wp or not Path(wp).exists():
            messagebox.showerror("Xato", f"Model fayli topilmadi:\n{wp}")
            return False
        try:
            lazy_import_yolo()
            self.status_var.set("Model yuklanmoqda...")
            self.root.update_idletasks()
            self.model = YOLO(wp)
            self.status_var.set(f"Model yuklandi: {Path(wp).name}")
            return True
        except Exception as e:
            messagebox.showerror("Xato", f"Model yuklashda xato:\n{e}")
            return False

    def start_source(self, kind):
        try:
            lazy_import_cv()
        except ImportError as e:
            messagebox.showerror("Xato", f"OpenCV yoki Pillow yo'q:\n{e}")
            return

        if not self._ensure_model():
            return

        self.stop_stream()
        time.sleep(0.15)  # avvalgi thread tugashini kutamiz

        if kind == "webcam":
            self.source_label_var.set("Manba: Web kamera #0")
            self._launch_thread(self._stream_loop, args=(0,))
        elif kind == "video":
            path = filedialog.askopenfilename(
                title="Video faylni tanlang",
                filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                           ("Barchasi", "*.*")],
            )
            if not path:
                return
            self.source_label_var.set(f"Manba: {Path(path).name}")
            self._launch_thread(self._stream_loop, args=(path,))
        elif kind == "image":
            path = filedialog.askopenfilename(
                title="Rasm faylni tanlang",
                filetypes=[("Rasmlar", "*.jpg *.jpeg *.png *.bmp *.webp"),
                           ("Barchasi", "*.*")],
            )
            if not path:
                return
            self.source_label_var.set(f"Manba: {Path(path).name}")
            self._show_image(path)
        elif kind == "folder":
            path = filedialog.askdirectory(title="Rasmlar papkasini tanlang")
            if not path:
                return
            self.folder_files = sorted([
                str(p) for p in Path(path).iterdir()
                if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp")
            ])
            if not self.folder_files:
                messagebox.showinfo("Papka", "Papkada rasm topilmadi.")
                return
            self.folder_index = 0
            self.source_label_var.set(
                f"Manba: papka ({len(self.folder_files)} ta) — 'Keyingi' tugmasi")
            self._show_image(self.folder_files[0],
                              extra=f"[1/{len(self.folder_files)}] ")

    def _launch_thread(self, target, args=()):
        self.stop_event.clear()
        self.pause_event.clear()
        self.thread = threading.Thread(target=target, args=args, daemon=True)
        self.thread.start()

    def stop_stream(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.thread = None
        # Folder mode reset
        self.folder_files = []
        self.folder_index = 0

    def toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.status_var.set("Davom etmoqda...")
        else:
            self.pause_event.set()
            self.status_var.set("Pauza")

    def request_snapshot(self):
        self.snapshot_request.set()
        self.status_var.set("Snapshot so'raldi...")

    def next_folder_frame(self):
        if not self.folder_files:
            self.status_var.set("Papka rejimi faol emas")
            return
        self.folder_index = (self.folder_index + 1) % len(self.folder_files)
        path = self.folder_files[self.folder_index]
        prefix = f"[{self.folder_index+1}/{len(self.folder_files)}] "
        self._show_image(path, extra=prefix)

    # ============ Inference loops ============
    def _stream_loop(self, source):
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            self.status_var.set(f"Manba ochilmadi: {source}")
            return
        self.status_var.set("Inference boshlandi...")
        fps_smooth = 0.0
        snap_count = 0
        while not self.stop_event.is_set():
            if self.pause_event.is_set():
                time.sleep(0.05)
                continue
            ret, frame = cap.read()
            if not ret:
                self.status_var.set("Manba tugadi")
                break
            t0 = time.time()
            try:
                results = self._predict(frame)
            except Exception as e:
                self.status_var.set(f"Inference xatosi: {e}")
                break
            dt = time.time() - t0
            inst_fps = 1.0 / max(dt, 1e-6)
            fps_smooth = (0.9 * fps_smooth + 0.1 * inst_fps) if fps_smooth > 0 else inst_fps
            frame, h, nh = draw_boxes(frame, results, self.conf_var.get())
            self.current_frame_for_save = frame.copy()
            self._push_display(frame)
            self.helmet_var.set(f"helmet: {h}")
            self.no_helmet_var.set(f"no_helmet: {nh}")
            self.fps_var.set(f"FPS: {fps_smooth:.1f}")

            if self.snapshot_request.is_set():
                self.snapshot_request.clear()
                snap_count += 1
                ts = time.strftime("%Y%m%d_%H%M%S")
                out = SNAPSHOT_DIR / f"snap_{ts}_{snap_count:03d}.jpg"
                cv2.imwrite(str(out), frame)
                self.status_var.set(f"Snapshot saqlandi: {out.name}")
        cap.release()
        self.status_var.set("Tugadi")

    def _predict(self, frame):
        """Inference - OOM bo'lsa avtomatik CPU ga o'tadi."""
        device = self.device_var.get()
        imgsz = int(self.imgsz_var.get())
        use_half = self.half_var.get() and device != "cpu"
        try:
            return self.model(frame, conf=self.conf_var.get(),
                              imgsz=imgsz, device=device,
                              half=use_half, verbose=False)[0]
        except Exception as e:
            err = str(e).lower()
            if "out of memory" in err or "cuda" in err or "cublas" in err:
                # GPU xotira yo'q - CPU ga o'tamiz
                self.status_var.set("[!] GPU xotira yo'q - CPU ga o'tildi (training tugasin)")
                self.device_var.set("cpu")
                import torch
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
                return self.model(frame, conf=self.conf_var.get(),
                                  imgsz=imgsz, device="cpu",
                                  half=False, verbose=False)[0]
            raise

    def _show_image(self, path, extra=""):
        frame = cv2.imread(path)
        if frame is None:
            self.status_var.set(f"O'qib bo'lmadi: {path}")
            return
        try:
            results = self._predict(frame)
        except Exception as e:
            messagebox.showerror("Inference xatosi", str(e))
            return
        frame, h, nh = draw_boxes(frame, results, self.conf_var.get())
        self.current_frame_for_save = frame.copy()
        self._push_display(frame)
        self.helmet_var.set(f"helmet: {h}")
        self.no_helmet_var.set(f"no_helmet: {nh}")
        self.fps_var.set("FPS: -")
        self.status_var.set(f"{extra}{Path(path).name}  helmet={h}  no_helmet={nh}")

    # ============ Display pipeline ============
    def _push_display(self, frame):
        # Convert BGR -> RGB -> PIL -> Tkinter
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            # Resize to fit display while keeping aspect
            scale = min(DISPLAY_W / w, DISPLAY_H / h, 1.0) if (w > DISPLAY_W or h > DISPLAY_H) else 1.0
            if scale < 1.0:
                nw, nh = int(w * scale), int(h * scale)
                rgb = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)
            pil_img = Image.fromarray(rgb)
            # Non-blocking: replace pending frame
            try:
                while True:
                    self.frame_queue.get_nowait()
            except Empty:
                pass
            self.frame_queue.put(pil_img)
        except Exception:
            pass

    def _tick_display(self):
        # 30 FPS UI refresh
        try:
            pil_img = self.frame_queue.get_nowait()
            tk_img = ImageTk.PhotoImage(pil_img)
            self.canvas.delete("all")
            w = tk_img.width()
            h = tk_img.height()
            cw = self.canvas.winfo_width() or DISPLAY_W
            ch = self.canvas.winfo_height() or DISPLAY_H
            x = (cw - w) // 2
            y = (ch - h) // 2
            self.canvas.create_image(x, y, image=tk_img, anchor="nw")
            self.canvas.image = tk_img  # GC dan saqlash
        except Empty:
            pass
        self.root.after(33, self._tick_display)


def main():
    if not find_default_weights():
        # Hech qanday model topilmagan bo'lsa, ogohlantirish ber
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Model topilmadi",
            f"Default model topilmadi:\n"
            f"  {DEFAULT_WEIGHTS_CANDIDATES[0]}\n"
            f"  {DEFAULT_WEIGHTS_CANDIDATES[1]}\n\n"
            f"Dasturda 'Model -> Tanlash' bilan qo'lda tanlang.",
        )
        root.destroy()

    root = tk.Tk()
    app = SergakApp(root)

    def on_close():
        app.stop_event.set()
        time.sleep(0.2)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
