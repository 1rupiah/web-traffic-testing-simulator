import json
import sys
import os
import re
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
import queue

sys.path.insert(0, os.path.dirname(__file__))
from src.bot import run_bot
from config import BotConfig

app = Flask(__name__, template_folder="templates", static_folder="static")

# In-memory store
session_results: list[dict] = []
all_sessions_history: list[dict] = []  # persistent across runs
bot_running = False
log_queue: queue.Queue = queue.Queue()


def bot_worker(url: str, visits: int):
    global bot_running, session_results
    bot_running = True
    session_results = []
    log_queue.put({"type": "start", "url": url, "visits": visits})

    import time
    import random
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    def build_driver():
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument(f"--user-agent={random.choice(BotConfig.USER_AGENTS)}")
        driver = uc.Chrome(headless=True, options=options, use_subprocess=True)
        return driver

    for i in range(1, visits + 1):
        result = {
            "session_id": i,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "duration_sec": 0,
            "page_title": "",
        }
        driver = None
        start = time.time()
        try:
            try:
                driver = build_driver()
            except Exception as e:
                error_msg = f"[Session {i}] Driver gagal launch: {e}"
                log_queue.put({"type": "error", "message": error_msg})
                result["error"] = error_msg
                raise

            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            result["page_title"] = driver.title
            time.sleep(random.uniform(2, 5))
            driver.execute_script("window.scrollBy(0, 400);")
            time.sleep(random.uniform(0.5, 1.5))
            result["status"] = "success"

        except Exception as e:
            if "error" not in result:
                result["error"] = str(e)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            result["duration_sec"] = round(time.time() - start, 2)

        session_results.append(result)
        all_sessions_history.append(result)
        log_queue.put({"type": "progress", "result": result, "done": i, "total": visits})

        if i < visits:
            gap = random.uniform(BotConfig.MIN_GAP_SEC, BotConfig.MAX_GAP_SEC)
            time.sleep(gap)

    log_queue.put({"type": "done"})
    bot_running = False


@app.route("/")
def index():
    return render_template("index.html", config=BotConfig)


# ── API: Bot Control ─────────────────────────────────────────
@app.route("/api/start", methods=["POST"])
def api_start():
    global bot_running
    if bot_running:
        return jsonify({"error": "Bot sudah berjalan"}), 400
    data = request.json or {}
    url = data.get("url", BotConfig.TARGET_URL)
    visits = int(data.get("visits", BotConfig.TOTAL_VISITS))
    t = threading.Thread(target=bot_worker, args=(url, visits), daemon=True)
    t.start()
    return jsonify({"status": "started", "url": url, "visits": visits})


@app.route("/api/results")
def api_results():
    success = sum(1 for r in session_results if r["status"] == "success")
    return jsonify({
        "results": session_results,
        "total": len(session_results),
        "success": success,
        "running": bot_running,
    })


@app.route("/api/stream")
def api_stream():
    def event_gen():
        while True:
            try:
                msg = log_queue.get(timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") == "done":
                    break
            except queue.Empty:
                yield "data: {\"type\":\"ping\"}\n\n"
    return Response(event_gen(), mimetype="text/event-stream")


# ── API: Sessions ────────────────────────────────────────────
@app.route("/api/sessions")
def api_sessions():
    return jsonify({
        "sessions": all_sessions_history,
        "total": len(all_sessions_history),
        "success": sum(1 for r in all_sessions_history if r["status"] == "success"),
        "failed": sum(1 for r in all_sessions_history if r["status"] != "success"),
    })


@app.route("/api/sessions/clear", methods=["POST"])
def api_sessions_clear():
    global all_sessions_history
    all_sessions_history = []
    return jsonify({"status": "cleared"})


# ── API: Config ──────────────────────────────────────────────
@app.route("/api/config", methods=["GET"])
def api_config_get():
    return jsonify({
        "TARGET_URL":   BotConfig.TARGET_URL,
        "TOTAL_VISITS": BotConfig.TOTAL_VISITS,
        "MIN_GAP_SEC":  BotConfig.MIN_GAP_SEC,
        "MAX_GAP_SEC":  BotConfig.MAX_GAP_SEC,
        "HEADLESS":     BotConfig.HEADLESS,
        "USER_AGENTS":  BotConfig.USER_AGENTS,
    })


@app.route("/api/config", methods=["POST"])
def api_config_set():
    data = request.json or {}
    if "TARGET_URL"   in data: BotConfig.TARGET_URL   = data["TARGET_URL"]
    if "TOTAL_VISITS" in data: BotConfig.TOTAL_VISITS = int(data["TOTAL_VISITS"])
    if "MIN_GAP_SEC"  in data: BotConfig.MIN_GAP_SEC  = float(data["MIN_GAP_SEC"])
    if "MAX_GAP_SEC"  in data: BotConfig.MAX_GAP_SEC  = float(data["MAX_GAP_SEC"])
    if "HEADLESS"     in data: BotConfig.HEADLESS     = bool(data["HEADLESS"])
    if "USER_AGENTS"  in data: BotConfig.USER_AGENTS  = data["USER_AGENTS"]
    return jsonify({"status": "saved"})


# ── API: Logs ────────────────────────────────────────────────
@app.route("/api/logs")
def api_logs():
    log_path = os.path.join(os.path.dirname(__file__), "logs", "bot.log")
    lines = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.readlines()
        # strip ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        lines = [ansi_escape.sub("", l).rstrip("\n\r") for l in raw[-500:]]
    return jsonify({"lines": lines, "total": len(lines)})


@app.route("/api/logs/clear", methods=["POST"])
def api_logs_clear():
    log_path = os.path.join(os.path.dirname(__file__), "logs", "bot.log")
    if os.path.exists(log_path):
        open(log_path, "w").close()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    app.run(debug=True, port=5001)
