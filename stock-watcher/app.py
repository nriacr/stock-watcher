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
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
NO_ACTIVE_PRODUCTS_SLEEP_SECONDS = 5 * 60


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@dataclass
class Product:
    name: str
    enabled: bool
    url: str
    notify_once_in_24h: bool
    check_interval_minutes: int
    in_stock_keywords: list[str]
    out_of_stock_keywords: list[str]


@dataclass
class Settings:
    products: list[Product]
    pushover_user_key: str
    pushover_api_token: str
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
        request_timeout_seconds=int(raw.get("request_timeout_seconds", 20)),
        user_agent=raw.get("user_agent", DEFAULT_USER_AGENT).strip(),
    )
    validate_settings(settings)
    return settings


def load_products(raw: dict) -> list[Product]:
    products = []
    raw_products = raw.get("products", [])

    if isinstance(raw_products, list):
        for index, item in enumerate(raw_products, start=1):
            if not isinstance(item, dict):
                continue

            name = str(item.get("name") or f"Ürün {index}").strip()
            enabled = as_bool(item.get("enabled"), default=True)
            url = str(item.get("url") or "").strip()
            notify_once_in_24h = as_bool(item.get("notify_once_in_24h"), default=True)
            check_interval_minutes = as_int(item.get("check_interval_minutes"), default=60)
            in_stock_keywords = normalize_keywords(item.get("in_stock_keywords", []))
            out_of_stock_keywords = normalize_keywords(item.get("out_of_stock_keywords", []))
            products.append(
                Product(
                    name=name,
                    enabled=enabled,
                    url=url,
                    notify_once_in_24h=notify_once_in_24h,
                    check_interval_minutes=check_interval_minutes,
                    in_stock_keywords=in_stock_keywords,
                    out_of_stock_keywords=out_of_stock_keywords,
                )
            )

    return products


def as_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "on", "evet", "aktif"}

    return bool(value)


def as_int(value: object, default: int) -> int:
    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_keywords(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    return [str(item).strip().casefold() for item in value if str(item).strip()]


def validate_settings(settings: Settings) -> None:
    missing = []
    active_products = [product for product in settings.products if product.enabled and product.url]

    if not settings.products:
        missing.append("products")
    if active_products and not settings.pushover_user_key:
        missing.append("pushover_user_key")
    if active_products and not settings.pushover_api_token:
        missing.append("pushover_api_token")

    products_without_keywords = [
        product.name
        for product in active_products
        if not product.in_stock_keywords and not product.out_of_stock_keywords
    ]
    if products_without_keywords:
        missing.append("keywords for " + ", ".join(products_without_keywords))

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
            "priority": 0,
        },
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()


def main() -> None:
    last_notification_times: dict[str, float] = {}
    next_check_times: dict[str, float] = {}

    while True:
        try:
            settings = load_settings()
            now = time.monotonic()
            product_keys = {product_key_for(product) for product in settings.products}
            prune_product_state(product_keys, next_check_times, last_notification_times)

            active_products = [product for product in settings.products if product.enabled and product.url]
            if not active_products:
                next_check_times.clear()
                last_notification_times.clear()
                logging.info("Kontrol edilecek aktif ürün bulunamadı.")
                sleep_seconds = NO_ACTIVE_PRODUCTS_SLEEP_SECONDS
            else:
                for product in settings.products:
                    product_key = product_key_for(product)
                    if not product.enabled:
                        next_check_times.pop(product_key, None)
                        last_notification_times.pop(product_key, None)
                        continue

                    if not product.url:
                        logging.info("Linki olmayan ürün atlandı: %s", product.name)
                        continue

                    next_check_time = next_check_times.get(product_key, 0)
                    if now < next_check_time:
                        continue

                    logging.info("Ürün sayfası kontrol ediliyor: %s (%s)", product.name, product.url)
                    text = page_text(fetch_product_page(settings, product))
                    in_stock = detect_stock_state(text, product)

                    if in_stock:
                        logging.info("STOKTA: %s", product.name)
                        if should_send_notification(product, product_key, last_notification_times):
                            send_pushover(settings, product)
                            last_notification_times[product_key] = time.monotonic()
                    else:
                        logging.info("Stokta Değil: %s", product.name)
                        last_notification_times.pop(product_key, None)

                    next_check_times[product_key] = (
                        time.monotonic() + max(product.check_interval_minutes, 5) * 60
                    )

                sleep_seconds = next_sleep_seconds(settings.products, next_check_times)
        except Exception as exc:
            logging.exception("Kontrol sırasında hata oluştu: %s", exc)
            sleep_seconds = NO_ACTIVE_PRODUCTS_SLEEP_SECONDS

        time.sleep(sleep_seconds)


def next_sleep_seconds(products: list[Product], next_check_times: dict[str, float]) -> int:
    active_products = [product for product in products if product.enabled and product.url]
    if not active_products:
        return NO_ACTIVE_PRODUCTS_SLEEP_SECONDS

    pending_times = [
        next_check_times[product_key_for(product)]
        for product in active_products
        if product_key_for(product) in next_check_times
    ]

    if len(pending_times) < len(active_products):
        return 1

    return max(1, min(60, int(min(pending_times) - time.monotonic())))


def product_key_for(product: Product) -> str:
    return f"{product.name}|{product.url}"


def prune_product_state(
    product_keys: set[str],
    next_check_times: dict[str, float],
    last_notification_times: dict[str, float],
) -> None:
    for state in (next_check_times, last_notification_times):
        for product_key in list(state):
            if product_key not in product_keys:
                state.pop(product_key, None)


def should_send_notification(
    product: Product,
    product_key: str,
    last_notification_times: dict[str, float],
) -> bool:
    if not product.notify_once_in_24h:
        return True

    last_notification_time = last_notification_times.get(product_key)
    if last_notification_time is None:
        return True

    return time.monotonic() - last_notification_time >= 24 * 60 * 60


if __name__ == "__main__":
    main()
