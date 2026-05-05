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
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@dataclass
class Product:
    name: str
    url: str
    check_interval_minutes: int
    in_stock_keywords: list[str]
    out_of_stock_keywords: list[str]


@dataclass
class Settings:
    products: list[Product]
    pushover_user_key: str
    pushover_api_token: str
    notify_once: bool
    request_timeout_seconds: int
    user_agent: str


def load_settings() -> Settings:
    if not OPTIONS_PATH.exists():
        raise FileNotFoundError(f"Home Assistant ayar dosyası bulunamadı: {OPTIONS_PATH}")

    raw = json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))
    settings = Settings(
        products=load_products(raw),
        pushover_user_key=raw.get("pushover_user_key", "").strip(),
        pushover_api_token=raw.get("pushover_api_token", "").strip(),
        notify_once=bool(raw.get("notify_once", True)),
        request_timeout_seconds=int(raw.get("request_timeout_seconds", 20)),
        user_agent=raw.get(
            "user_agent",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ).strip(),
    )
    validate_settings(settings)
    return settings


def load_products(raw: dict) -> list[Product]:
    products = []
    raw_products = raw.get("products", [])
    legacy_check_interval_minutes = int(raw.get("check_interval_minutes", 60))
    legacy_in_stock_keywords = normalize_keywords(raw.get("in_stock_keywords", []))
    legacy_out_of_stock_keywords = normalize_keywords(raw.get("out_of_stock_keywords", []))

    if isinstance(raw_products, list):
        for index, item in enumerate(raw_products, start=1):
            if not isinstance(item, dict):
                continue

            name = str(item.get("name") or f"Ürün {index}").strip()
            url = str(item.get("url") or "").strip()
            check_interval_minutes = int(
                item.get("check_interval_minutes", legacy_check_interval_minutes)
            )
            in_stock_keywords = normalize_keywords(item.get("in_stock_keywords", []))
            out_of_stock_keywords = normalize_keywords(item.get("out_of_stock_keywords", []))
            products.append(
                Product(
                    name=name,
                    url=url,
                    check_interval_minutes=check_interval_minutes,
                    in_stock_keywords=in_stock_keywords or legacy_in_stock_keywords,
                    out_of_stock_keywords=out_of_stock_keywords or legacy_out_of_stock_keywords,
                )
            )

    legacy_url = str(raw.get("product_url") or "").strip()
    if not products and legacy_url:
        products.append(
            Product(
                name="Ürün 1",
                url=legacy_url,
                check_interval_minutes=legacy_check_interval_minutes,
                in_stock_keywords=legacy_in_stock_keywords,
                out_of_stock_keywords=legacy_out_of_stock_keywords,
            )
        )

    return products


def normalize_keywords(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    return [str(item).strip().casefold() for item in value if str(item).strip()]


def validate_settings(settings: Settings) -> None:
    missing = []
    if not settings.products or not any(product.url for product in settings.products):
        missing.append("products")
    if not settings.pushover_user_key:
        missing.append("pushover_user_key")
    if not settings.pushover_api_token:
        missing.append("pushover_api_token")
    if not any(product.in_stock_keywords or product.out_of_stock_keywords for product in settings.products):
        missing.append("in_stock_keywords or out_of_stock_keywords")

    if missing:
        raise ValueError("Zorunlu eklenti ayarları eksik: " + ", ".join(missing))


def fetch_product_page(settings: Settings, product: Product) -> str:
    response = requests.get(
        product.url,
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


def detect_stock_state(text: str, product: Product) -> bool:
    has_out_of_stock = contains_any(text, product.out_of_stock_keywords)
    has_in_stock = contains_any(text, product.in_stock_keywords)

    if has_out_of_stock:
        return False

    return has_in_stock


def send_pushover(settings: Settings, product: Product) -> None:
    response = requests.post(
        PUSHOVER_URL,
        data={
            "token": settings.pushover_api_token,
            "user": settings.pushover_user_key,
            "title": f"{product.name} stoğa geldi",
            "message": f"Takip ettiğiniz ürün stokta görünüyor: {product.url}",
            "url": product.url,
            "url_title": "Ürüne git",
            "priority": 1,
        },
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()


def main() -> None:
    notified_products: set[str] = set()
    next_check_times: dict[str, float] = {}

    while True:
        try:
            settings = load_settings()
            now = time.monotonic()
            for product in settings.products:
                if not product.url:
                    logging.info("Linki olmayan ürün atlandı: %s", product.name)
                    continue

                product_key = product.url
                next_check_time = next_check_times.get(product_key, 0)
                if now < next_check_time:
                    continue

                logging.info("Ürün sayfası kontrol ediliyor: %s (%s)", product.name, product.url)
                text = page_text(fetch_product_page(settings, product))
                in_stock = detect_stock_state(text, product)

                if in_stock:
                    if settings.notify_once and product_key in notified_products:
                        logging.info("%s hâlâ stokta görünüyor; bildirim daha önce gönderildi.", product.name)
                    else:
                        logging.info("%s stokta görünüyor. Pushover bildirimi gönderiliyor.", product.name)
                        send_pushover(settings, product)
                        notified_products.add(product_key)
                else:
                    logging.info("%s stokta değil görünüyor.", product.name)
                    notified_products.discard(product_key)

                next_check_times[product_key] = (
                    time.monotonic() + max(product.check_interval_minutes, 5) * 60
                )

            sleep_seconds = next_sleep_seconds(settings.products, next_check_times)
        except Exception as exc:
            logging.exception("Kontrol sırasında hata oluştu: %s", exc)
            sleep_seconds = 5 * 60

        time.sleep(sleep_seconds)


def next_sleep_seconds(products: list[Product], next_check_times: dict[str, float]) -> int:
    active_products = [product for product in products if product.url]
    pending_times = [
        next_check_times[product.url]
        for product in active_products
        if product.url in next_check_times
    ]

    if len(pending_times) < len(active_products):
        return 1

    return max(1, min(60, int(min(pending_times) - time.monotonic())))


if __name__ == "__main__":
    main()
