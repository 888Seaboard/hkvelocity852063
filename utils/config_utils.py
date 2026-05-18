import json
import re
import logging
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "config.json"

DEFAULT_CONFIG = {
    "default_date": "2026/05/17",
    "default_course": "ST",
    "auto_schedule": True,
    "schedule": []
}

def load_config():
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            config.setdefault(k, v)
        return config
    except Exception as e:
        logger.exception("load_config failed: %s", e)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info("✅ Config saved to %s", CONFIG_PATH)
        return True
    except Exception as e:
        logger.exception("save_config failed: %s", e)
        return False

def generate_race_links(config):
    links = []
    default_date = config.get("default_date", DEFAULT_CONFIG["default_date"])
    default_course = config.get("default_course", DEFAULT_CONFIG["default_course"])

    for i in range(1, 12):
        link = (
            "https://racing.hkjc.com/zh-hk/local/information/racecard"
            f"?racedate={default_date}&Racecourse={default_course}&RaceNo={i}"
        )
        links.append({
            "race_no": i,
            "url": link,
            "title": f"R{i} - {default_date} {default_course}"
        })
    return links

def get_next_race_day():
    config = load_config()
    schedule = config.get("schedule", [])
    today = datetime.now().strftime("%Y/%m/%d")

    for day in schedule:
        date_str = day.get("date", "")
        course = day.get("course", "ST")
        if date_str >= today:
            return date_str, course

    if schedule:
        day = schedule[0]
        return day.get("date", today), day.get("course", "ST")

    return today, "ST"

def auto_update_schedule():
    config = load_config()
    if not config.get("auto_schedule", False):
        return config

    try:
        resp = requests.get(
            "https://racing.hkjc.com/zh-hk/local/information/fixture",
            timeout=10
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()

        dates = []
        date_patterns = [
            r"(\d{1,2})[月\/\-\s]+(\w+)[日賽]",
            r"(\d{1,2})[月\/\-\s]+(\d{1,2})[日賽]"
        ]

        for pattern in date_patterns:
            for match in re.finditer(pattern, text):
                day = match.group(1)
                dates.append({
                    "date": f"2026/05/{day.zfill(2)}",
                    "course": "ST" if "沙田" in text else "HV",
                    "name": f"5/{day} 賽事"
                })

        if dates:
            config["schedule"] = dates[:5]
            save_config(config)
            logger.info("✅ 自動更新賽期：%d 場", len(config["schedule"]))

        return config

    except Exception as e:
        logger.warning("自動賽期失敗：%s", e)
        return config