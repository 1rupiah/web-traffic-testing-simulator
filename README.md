# TrafficBot — SEO Click Simulator

Bot clicker berbasis Python + Selenium dengan dashboard web real-time.

---

## 🗂 Struktur Project

```
bot-clicker-portfolio/
├── app.py              ← Flask web dashboard
├── config.py           ← Konfigurasi bot (URL, jumlah visit, dll)
├── requirements.txt    ← Dependencies Python
├── src/
│   └── bot.py          ← Core Selenium bot logic
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── index.html
└── logs/               ← Auto-dibuat saat bot jalan
```

---

## ⚙️ Prerequisites

Pastikan sudah install:
- **Python 3.10+** → https://python.org/downloads
- **Google Chrome** → https://google.com/chrome
- **pip** (biasanya sudah include dengan Python)

---

## 🚀 Step-by-Step: Cara Jalankan

### 1. Clone / Download repo

```bash
# Kalau pakai git:
git clone <url-repo-lo>
cd bot-clicker-portfolio

# Atau ekstrak ZIP, lalu masuk foldernya:
cd bot-clicker-portfolio
```

### 2. Buat virtual environment (recommended)

```bash
python -m venv venv

# Activate — Windows:
venv\Scripts\activate

# Activate — Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> `webdriver-manager` akan otomatis download ChromeDriver yang sesuai versi Chrome lo — ga perlu install manual.

### 4. Set target URL (opsional)

Edit file `config.py`:

```python
TARGET_URL   = "https://website-lo.com"   # ← ganti ini
TOTAL_VISITS = 20                          # jumlah kunjungan default
```

Atau bisa langsung set dari dashboard web (lebih gampang).

### 5. Jalankan dashboard

```bash
python app.py
```

Buka browser → http://localhost:5000

---

## 🖥 Cara Pakai Dashboard

1. Isi **Target URL** (URL yang mau dikasih traffic)
2. Isi **Jumlah Kunjungan**
3. Klik **▶ Jalankan**
4. Pantau progress di tabel Session Log dan Live Log

---

## 🔧 Jalankan bot via terminal (tanpa dashboard)

```bash
python -c "
from src.bot import run_bot
results = run_bot('https://example.com', total_visits=10)
"
```

---

## ⚠️ Catatan

- Bot berjalan **headless** (tanpa jendela browser) secara default. Untuk debug, ubah `HEADLESS = False` di `config.py`
- Setiap sesi menggunakan **user-agent berbeda** secara acak
- Ada **jeda random** antar sesi (default 3–8 detik) untuk simulasi traffic organik
- Log disimpan otomatis di folder `logs/bot.log`
