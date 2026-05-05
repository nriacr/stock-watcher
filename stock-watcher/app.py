import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup


OPTIONS_PATH = Path("/data/options.json")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


@dataclass
class Settings:
    product_url: str
    check_interval_minutes: int
    in_stock_keywords: list[str]
    out_of_stock_keywords: list[str]
    pushover_user_key: str
    pushover_api_token: str
    notify_once: bool
    request_timeout_seconds: int
    user_agent: str


def load_settings() -> Settings:
    if not OPTIONS_PATH.exists():
        raise FileNotFoundError(f"Home Assistant options file was not found: {OPTIONS_PATH}")

    raw = json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))
    settings = Settings(
        product_url=raw.get("product_url", "").strip(),
        check_interval_minutes=int(raw.get("check_interval_minutes", 60)),
        in_stock_keywords=normalize_keywords(raw.get("in_stock_keywords", [])),
        out_of_stock_keywords=normalize_keywords(raw.get("out_of_stock_keywords", [])),
        pushover_user_key=raw.get("pushover_user_key", "").strip(),
        pushover_api_token=raw.get("pushover_api_token", "").strip(),
        notify_once=bool(raw.get("notify_once", True)),
        request_timeout_seconds=int(raw.get("request_timeout_seconds", 20)),
        user_agent=raw.get("user_agent", "Mozilla/5.0").strip(),
    )
    validate_settings(settings)
    return settings


def normalize_keywords(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    return [str(item).strip().casefold() for item in value if str(item).strip()]


def validate_settings(settings: Settings) -> None:
    missing = []
    if not settings.product_url:
        missing.append("product_url")
    if not settings.pushover_user_key:
        missing.append("pushover_user_key")
    if not settings.pushover_api_token:
        missing.append("pushover_api_token")
    if not settings.in_stock_keywords and not settings.out_of_stock_keywords:
        missing.append("in_stock_keywords or out_of_stock_keywords")

    if missing:
        raise ValueError("Missing required add-on options: " + ", ".join(missing))


def fetch_product_page(settings: Settings) -> str:
    response = requests.get(
        settings.product_url,
        headers={"User-Agent": settings.user_agent},
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()
    return response.text


def page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(" ")
    return re.sub(r"\s+", " ", text).strip().casefold()


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def detect_stock_state(text: str, settings: Settings) -> bool:
    has_out_of_stock = contains_any(text, settings.out_of_stock_keywords)
    has_in_stock = contains_any(text, settings.in_stock_keywords)

    if has_out_of_stock:
        return False

    return has_in_stock


def send_pushover(settings: Settings) -> None:
    response = requests.post(
        PUSHOVER_URL,
        data={
            "token": settings.pushover_api_token,
            "user": settings.pushover_user_key,
            "title": "Ürün stoğa geldi",
            "message": f"Takip ettiğiniz ürün stokta görünüyor: {settings.product_url}",
            "url": settings.product_url,
            "url_title": "Ürüne git",
            "priority": 1,
        },
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()


def main() -> None:
    notified = False

    while True:
        try:
            settings = load_settings()
            logging.info("Checking product page: %s", settings.product_url)
            text = page_text(fetch_product_page(settings))
            in_stock = detect_stock_state(text, settings)

            if in_stock:
                if settings.notify_once and notified:
                    logging.info("Product is still in stock; notification already sent.")
                else:
                    logging.info("Product appears to be in stock. Sending Pushover notification.")
                    send_pushover(settings)
                    notified = True
            else:
                logging.info("Product appears to be out of stock.")
                notified = False

            sleep_seconds = max(settings.check_interval_minutes, 5) * 60
        except Exception as exc:
            logging.exception("Check failed: %s", exc)
            sleep_seconds = 5 * 60

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
