# HELMET DETECTION DATASETLARI

Bu hujjat — internetdagi eng yaxshi helmet detection datasetlarining ro'yxati va yuklab olish ko'rsatmalari.

**Maqsad:** Bularning hammasini yuklab olib, YOLOv8 formatiga aylantirib, bitta katta dataset qilamiz.

---

## 1. ROBOFLOW HARD HAT WORKERS ⭐ (TAVSIYA)

**Eng yaxshi va eng oson** — to'g'ridan-to'g'ri YOLOv8 formatida yuklab olish mumkin.

| Parametr | Qiymat |
|---|---|
| Rasm soni | 7,036 |
| Klasslar | head, helmet, person (3 ta) |
| Format | YOLOv8 / COCO / VOC (tanlash mumkin) |
| Hajm | ~250 MB |
| Litsenziya | CC BY 4.0 (bepul, kommersiyaga ham) |
| Saytda | https://public.roboflow.com/object-detection/hard-hat-workers |

**Yuklab olish:**
1. Yuqoridagi havolaga o'ting
2. "Download Dataset" tugmasini bosing
3. Format: **YOLOv8** ni tanlang
4. Bepul roʻyxatdan oʻting (email kerak)
5. ZIP fayl yuklanadi → `D:\sergak dasturi\kaska\datasets\roboflow_hardhat\` ga ochib qo'ying

**Klassni qayta xaritalash kerak:** `head` va `person` → `no_helmet` (chunki bu kaska yo'q odam), `helmet` → `helmet`

---

## 2. SAFETY HELMET WEARING DATASET (SHWD) ⭐

Xitoyning eng katta helmet datasetlaridan biri. Asiyo zavod ishchilari.

| Parametr | Qiymat |
|---|---|
| Rasm soni | 7,581 |
| Klasslar | hat (helmet), person (no helmet) |
| Format | PASCAL VOC (XML) — konversiya kerak |
| Hajm | ~650 MB |
| Litsenziya | Erkin foydalanish |
| GitHub | https://github.com/njvisionpower/Safety-Helmet-Wearing-Dataset |

**Yuklab olish:**
1. GitHub sahifasiga o'ting
2. README'da Google Drive yoki Baidu havolasi bor
3. Yuklab olib `D:\sergak dasturi\kaska\datasets\shwd\` ga oching
4. `scripts/convert_voc_to_yolo.py` bilan YOLO formatiga aylantiring

---

## 3. KAGGLE HARD HAT DETECTION

| Parametr | Qiymat |
|---|---|
| Rasm soni | 5,000 |
| Klasslar | helmet, head, person |
| Format | PASCAL VOC (XML) |
| Hajm | ~370 MB |
| Litsenziya | CC0 (toʻliq bepul) |
| Sayt | https://www.kaggle.com/datasets/andrewmvd/hard-hat-detection |

**Yuklab olish:**
1. Kaggle akkaunti yarating (bepul)
2. Yuqoridagi havola → "Download" tugmasi
3. `D:\sergak dasturi\kaska\datasets\kaggle_hardhat\` ga oching

---

## 4. PICTOR-V3 (CONSTRUCTION WORKERS)

Qurilish ishchilari uchun maxsus dataset.

| Parametr | Qiymat |
|---|---|
| Rasm soni | 774 (kichik, lekin sifatli) |
| Klasslar | helmet, no_helmet, person |
| Format | YOLO |
| Hajm | ~150 MB |
| Litsenziya | MIT |
| GitHub | https://github.com/ciber-lab/pictor-ppe |

**Yuklab olish:**
```powershell
cd "D:\sergak dasturi\kaska\datasets"
git clone https://github.com/ciber-lab/pictor-ppe.git pictor_v3
```

---

## 5. CHV — CONSTRUCTION HELMET VISION

Yangi tadqiqot dataseti — 2023 yil.

| Parametr | Qiymat |
|---|---|
| Rasm soni | 12,000+ |
| Klasslar | helmet (rangli ranglar bilan), no_helmet |
| Format | YOLO |
| Hajm | ~1.5 GB |
| Litsenziya | Akademik foydalanish |
| Sayt | https://github.com/RUB-Bochum/CHV |

---

## 6. ROBOFLOW UNIVERSE — qo'shimcha datasetlar

Roboflow Universe'da **100+ ta** helmet detection dataset bor. Eng yaxshilari:

- **Safety Helmet Detection v3** — 3,500 rasm, https://universe.roboflow.com/joseph-nelson/hard-hat-workers
- **PPE Detection** — 8,000+ rasm, https://universe.roboflow.com/search?q=helmet
- **Hard Hat Universe** — 15,000+ rasm
- **Industrial Safety** — sanoat sharoiti

Hammasini "Combine + Re-train" tugmasi orqali avtomatik birlashtirish mumkin.

---

## 7. KAGGLE HELMET DETECTION (qoʻshimcha)

| Dataset | Rasm | Link |
|---|---|---|
| Helmet Detection Dataset | 5,000 | https://www.kaggle.com/datasets/snehilsanyal/construction-site-safety-image-dataset-roboflow |
| PPE Detection | 7,000 | https://www.kaggle.com/datasets/snehilsanyal/personal-protective-equipment-detection |
| Hardhat Workers | 5,000 | https://www.kaggle.com/datasets/vodan37/yolo-helmethead |

---

## 8. HUGGINGFACE DATASETS

| Dataset | Rasm | Link |
|---|---|---|
| keremberke/hard-hat-detection | 5,300 | https://huggingface.co/datasets/keremberke/hard-hat-detection |
| construction-helmet | 3,000 | https://huggingface.co/datasets/laaq/construction-helmet |

**Yuklab olish:**
```python
from datasets import load_dataset
ds = load_dataset("keremberke/hard-hat-detection", "full")
```

---

## 9. SIZNING DEHQONOBOD KAMERALARINGIZDAN (ENG MUHIM!)

Eng yaxshi natija uchun **o'z kameralaringizdan** ham rasm yig'ing:

1. Sergak AI'da kameralar ishlamoqda → har soatda **snapshot** olinadi
2. `D:\sergak dasturi\backend\snapshots\` papkasidan rasmlarni `D:\sergak dasturi\kaska\datasets\our_factory\images\` ga ko'chiring
3. **CVAT** yoki **Roboflow** orqali qo'lda annotatsiya qiling (kaska bor/yo'q deb belgilash)

Bu bilan sizning korxonangiz sharoitiga (yorug'lik, masofa, kamera burchagi) maxsus moslashgan model bo'ladi.

---

## DATASETLARNI BIRLASHTIRISH REJASI

| Manba | Rasm soni | Hissa |
|---|---|---|
| Roboflow Hard Hat | 7,036 | 30% |
| SHWD | 7,581 | 30% |
| Kaggle Hard Hat | 5,000 | 20% |
| Pictor-v3 | 774 | 3% |
| CHV | 5,000 (sampling) | 15% |
| Sizning korxona | 500-2000 | 2-10% |
| **JAMI** | **~25,000-27,000 rasm** | **100%** |

**Trening + Validation + Test taqsimoti:**
- Train: 80% (~20,000 rasm)
- Validation: 15% (~3,750 rasm)
- Test: 5% (~1,250 rasm)

---

## KEYINGI QADAMLAR

1. ✅ Papka yaratildi
2. ⏳ Yuqoridagi datasetlardan **2-3 tasini** yuklab oling (har qaysi 5-10 daqiqalik ish)
3. ⏳ `scripts/convert_voc_to_yolo.py` bilan formatlarni YOLO'ga aylantiring
4. ⏳ `scripts/merge_datasets.py` bilan birlashtiring
5. ⏳ `scripts/stats.py` bilan tekshiring (kaska/no_helmet balansi qancha?)
6. ⏳ Trening — `D:\sergak dasturi\kaska\TRAINING.md` da batafsil

---

## SAVOLLAR

Agar dataset yuklab olishda muammo bo'lsa, menga ayting:
- Kaggle akkaunti yo'q? — yangi yaratish 1 daqiqa
- Roboflow akkaunti yo'q? — ham 1 daqiqa, bepul
- GitHub'dan git clone qila olmayapsizmi? — buyruqni ko'rsataman
- Internet sekinmi? — kichikroq datasetdan boshlaymiz (Pictor-v3 — 150 MB)
