import time
import random
import logging
import os
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import BotConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/bot.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


def build_driver(headless: bool = True) -> uc.Chrome:
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument(f"--user-agent={random.choice(BotConfig.USER_AGENTS)}")
    driver = uc.Chrome(headless=headless, options=options, use_subprocess=True)
    return driver


def human_delay(min_sec: float = 1.5, max_sec: float = 4.5) -> None:
    time.sleep(random.uniform(min_sec, max_sec))


def simulate_scroll(driver) -> None:
    scroll_pause = random.uniform(0.5, 1.5)
    total_height = driver.execute_script("return document.body.scrollHeight")
    current = 0
    step = random.randint(200, 500)
    while current < total_height:
        driver.execute_script(f"window.scrollBy(0, {step});")
        current += step
        time.sleep(scroll_pause)
    if random.random() > 0.5:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(scroll_pause)


def simulate_mouse_movement(driver) -> None:
    try:
        elements = driver.find_elements(By.TAG_NAME, "a")
        if elements:
            target = random.choice(elements[:10])
            ActionChains(driver).move_to_element(target).perform()
            time.sleep(random.uniform(0.3, 0.8))
    except Exception:
        pass


def visit_url(url: str, session_id: int, headless: bool = True) -> dict:
    result = {
        "session_id": session_id,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "status": "failed",
        "duration_sec": 0,
        "page_title": "",
    }
    driver = None
    start = time.time()
    try:
        driver = build_driver(headless=headless)
        logger.info(f"[Session {session_id}] Visiting: {url}")
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        result["page_title"] = driver.title

        human_delay(2, 5)
        simulate_scroll(driver)
        simulate_mouse_movement(driver)
        human_delay(1, 3)

        result["status"] = "success"
        logger.info(f"[Session {session_id}] Done ✓ | Title: {driver.title}")

    except Exception as e:
        logger.error(f"[Session {session_id}] Error: {e}")
        result["error"] = str(e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        result["duration_sec"] = round(time.time() - start, 2)

    return result


def run_bot(url: str, total_visits: int, headless: bool = True) -> list[dict]:
    os.makedirs("logs", exist_ok=True)
    results = []
    logger.info(f"Starting bot — Target: {url} | Visits: {total_visits}")

    for i in range(1, total_visits + 1):
        result = visit_url(url, session_id=i, headless=headless)
        results.append(result)

        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"Progress: {i}/{total_visits} | Success: {success_count}")

        if i < total_visits:
            gap = random.uniform(BotConfig.MIN_GAP_SEC, BotConfig.MAX_GAP_SEC)
            logger.info(f"Waiting {gap:.1f}s before next session...")
            time.sleep(gap)

    return results


if __name__ == "__main__":
    results = run_bot(
        url=BotConfig.TARGET_URL,
        total_visits=BotConfig.TOTAL_VISITS,
        headless=BotConfig.HEADLESS,
    )
    success = sum(1 for r in results if r["status"] == "success")
    print(f"\n✅ Done! {success}/{len(results)} visits succeeded.")