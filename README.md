# Web Traffic Testing Simulator

A Python-based web traffic simulation tool built with Selenium and a real-time Flask dashboard.

---

## 📸 Dashboard Screenshots

### Dashboard Overview

![Dashboard Overview](images/Menu%20-%20Dashboard.png)

Real-time dashboard displaying traffic simulation statistics, active sessions, visit counts, and execution status.

### Session Monitoring

![Session Monitoring](images/Menu%20-%20Sessions.png)

Session management interface showing running visits, completed sessions, timestamps, and execution progress.

### Configuration Panel

![Configuration Panel](images/Menu%20-%20Config.png)

Configuration page for managing target URLs, visit counts, delays, browser settings, and simulation parameters.

### Live Logs

![Live Logs](images/Menu%20-%20Logs.png)

Real-time logging console displaying browser activity, traffic generation events, session updates, and diagnostic information.

---

## 🗂 Structure Project

```
web-traffic-testing-simulator/
├── app.py              ← Flask web dashboard
├── config.py           ← Bot configuration (URL, visit count, etc.)
├── requirements.txt    ← Python dependencies
├── src/
│   └── bot.py          ← Core Selenium bot logic
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── index.html
└── logs/               ← Automatically created during execution
```

---

## ⚙️ Prerequisites

Make sure the following software is installed:

- **Python 3.10+** → https://python.org/downloads
- **Google Chrome** → https://google.com/chrome
- **pip** (usually included with Python)

---

## 🚀 Step-by-Step: Getting Started

### 1. Clone / Download Repository

```bash
# Using Git:
git clone https://github.com/1rupiah/web-traffic-testing-simulator.git
cd web-traffic-testing-simulator

# Or extract the ZIP file and enter the project folder:
cd web-traffic-testing-simulator
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> `webdriver-manager` automatically downloads the correct ChromeDriver version for your installed Chrome browser. No manual installation is required.

### 4. Configure Target URL (Optional)

Edit `config.py`:

```python
TARGET_URL   = "https://your-website.com"
TOTAL_VISITS = 20
```

Or configure it directly from the web dashboard.

### 5. Start the Dashboard

```bash
python app.py
```

Open your browser:

```text
http://localhost:5001
```

---

## 🖥 Dashboard Usage

1. Enter the **Target URL**
2. Specify the **Number of Visits**
3. Click **▶ Start**
4. Monitor progress through the Session Log and Live Log tables

---

## 🔧 Run from Terminal (Without Dashboard)

```bash
python -c "
from src.bot import run_bot
results = run_bot('https://example.com', total_visits=10)
"
```

---

## ⚠️ Notes

- The bot runs in **headless mode** by default. For debugging purposes, set `HEADLESS = False` in `config.py`
- Each session uses a randomized **user-agent**
- Random delays between sessions (default 3 to 8 seconds) help simulate realistic browsing behavior
- Logs are automatically stored in `logs/bot.log`
