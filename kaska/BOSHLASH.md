# TEZKOR BOSHLASH - DATASET YIG'ISH

## Bugun nima qilamiz

3 ta asosiy datasetni yuklab olamiz va birlashtiramiz. Bu **2-3 soat** vaqt oladi (asosan internetdan yuklash).

---

## 1-QADAM: Roboflow Hard Hat (eng oson, 5 daqiqa)

Eng tez yo'l - YOLOv8 formatida tayyor.

1. Brauzerda oching: **https://public.roboflow.com/object-detection/hard-hat-workers**
2. Pastga aylantirib **"Download Dataset"** tugmasiga bosing
3. Bepul ro'yxatdan o'ting (email + parol, 30 soniya)
4. Format tanlash oynasida: **"YOLOv8"** ni tanlang
5. **"Download zip to computer"** bosing
6. ZIP'ni `D:\sergak dasturi\kaska\datasets\roboflow_hardhat\` ga oching

Ichida quyidagicha bo'lishi kerak:
```
datasets/roboflow_hardhat/
├── data.yaml
├── train/
│   ├── images/  (~5000 ta .jpg)
│   └── labels/  (~5000 ta .txt)
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

---

## 2-QADAM: Kaggle Hard Hat Detection (10 daqiqa)

1. Kaggle akkaunti yo'q bo'lsa, **https://www.kaggle.com** da ro'yxatdan o'ting (1 daqiqa)
2. Brauzerda oching: **https://www.kaggle.com/datasets/andrewmvd/hard-hat-detection**
3. O'ng yuqori burchakda **"Download"** tugmasi (~370 MB)
4. ZIP'ni `D:\sergak dasturi\kaska\datasets\kaggle_hardhat\` ga oching

Bu dataset **VOC formatda** (XML), keyin konvertatsiya qilamiz.

---

## 3-QADAM: SHWD - Safety Helmet Wearing Dataset (15 daqiqa)

Bu eng katta va sifatli dataset.

1. GitHub: **https://github.com/njvisionpower/Safety-Helmet-Wearing-Dataset**
2. README ichida **Google Drive havolasi** bor (yoki Baidu — tezroq, lekin xitoy uchun)
3. Google Drive'dan yuklab oling (~650 MB)
4. `D:\sergak dasturi\kaska\datasets\shwd\` ga oching

Bu ham VOC formatda.

---

## 4-QADAM: VOC -> YOLO konvertatsiya

Kaggle va SHWD datasetlarini YOLO formatiga aylantiramiz.

PowerShell'da:

```powershell
cd "D:\sergak dasturi\kaska\scripts"

# Kaggle uchun
py convert_voc_to_yolo.py --voc-dir "D:\sergak dasturi\kaska\datasets\kaggle_hardhat" --output "D:\sergak dasturi\kaska\datasets\kaggle_hardhat_yolo"

# SHWD uchun
py convert_voc_to_yolo.py --voc-dir "D:\sergak dasturi\kaska\datasets\shwd" --output "D:\sergak dasturi\kaska\datasets\shwd_yolo"
```

---

## 5-QADAM: Birlashtirish

```powershell
cd "D:\sergak dasturi\kaska\scripts"
py merge_datasets.py
```

Bu skript:
- Barcha YOLO datasetlarni topadi
- Train/val/test ga bo'ladi (80/15/5%)
- `D:\sergak dasturi\kaska\merged\` ga yozadi
- YOLOv8 uchun `data.yaml` yaratadi

---

## 6-QADAM: Statistika

```powershell
py stats.py "D:\sergak dasturi\kaska\merged"
```

Quyidagicha natijani ko'rasiz:
```
[TRAIN]
  Rasmlar:        18,500
  Labellar:       18,500
  Jami bbox:      45,200
  Klass 0 (helmet):    28,000 (62%)
  Klass 1 (no_helmet): 17,200 (38%)

[VAL]
  Rasmlar:        3,500
  ...
```

**Yaxshi balans:** har klass 30-70% oralig'ida.

---

## 7-QADAM: Ko'z bilan tekshirish

Bir nechta rasmni bbox bilan birga ko'ring:

```powershell
py visualize.py "D:\sergak dasturi\kaska\merged" train 20
```

`D:\sergak dasturi\kaska\merged\visualized\train\` papkasini oching va rasmlarni ko'ring. Yashil = helmet, qizil = no_helmet.

Agar bbox'lar noto'g'ri joyda bo'lsa — annotatsiyada xato bor.

---

## KEYINGI BOSQICH: TRENING

Dataset tayyor bo'lganidan keyin (taxminan 25,000 rasm) treningga o'tamiz:

1. Sizning RTX 4060 da CUDA PyTorch o'rnatish (Python 3.13 bilan)
2. Yoki Google Colab da bepul T4 GPU bilan
3. Yoki Kaggle Kernels da bepul P100 bilan

Trening buyrug'i:
```bash
yolo train data=merged/data.yaml model=yolov8s.pt epochs=100 imgsz=640 batch=16 device=0
```

Natija: `runs/detect/train/weights/best.pt` — sizning yangi modelingiz.

Buni Sergak AI ga yuklasangiz, eski `helmet_best.pt` o'rniga ishlay boshlaydi.

---

## SAVOLLAR / MUAMMOLAR

- **Internet sekin?** → Faqat Roboflow datasetini olsangiz ham yetadi (7000 rasm)
- **Disk to'lib qoldi?** → SHWD ni o'tkazib yuboring (eng katta)
- **Roboflow akkaunti ochilmayapti?** → Kaggle bilan davom eting
- **Konversiya skripti xato beradi?** → Menga xato matnini yuboring

**Hozir 1-3 qadamlarni boshlang** — uchta datasetdan kamida bittasini yuklab olsangiz, davom etish mumkin.
