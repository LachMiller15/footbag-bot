#!/usr/bin/env python3
"""Watch a whole Shopify store and alert when ANY product comes back in stock.

Uses the store's public products.json (reliable 'available' flag per variant).
Only alerts on the transition out-of-stock -> in-stock, so you aren't spammed on
every scheduled run. State is kept in state.json, which the GitHub Actions
workflow commits back to the repo between runs.
"""

import json
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

import requests

ROOT = Path(__file__).parent
CONFIG_FILE = ROOT / "config.json"
STATE_FILE = ROOT / "state.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def fetch_all_products(store):
    """Return every product in a Shopify store (handles pagination)."""
    base = store.rstrip("/")
    products = []
    page = 1
    while True:
        url = f"{base}/products.json?limit=250&page={page}"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        batch = resp.json().get("products", [])
        if not batch:
            break
        products.extend(batch)
        page += 1
    return products


def is_in_stock(product):
    return any(v.get("available") for v in product.get("variants", []))


def send_alert(store, newly_in_stock):
    user = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipients = [r.strip() for r in os.environ["ALERT_TO"].split(",") if r.strip()]

    base = store.rstrip("/")
    lines = []
    for p in newly_in_stock:
        lines.append(f"{p['title']}\n{base}/products/{p['handle']}")
    body = "Back in stock:\n\n" + "\n\n".join(lines)

    names = ", ".join(p["title"] for p in newly_in_stock)
    msg = EmailMessage()
    msg["Subject"] = f"IN STOCK: {names}"[:120]
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    print(f"  -> alerted ({names}) to {', '.join(recipients)}")


def main():
    config = load_json(CONFIG_FILE, {})
    store = config.get("store")
    if not store:
        print("No 'store' set in config.json")
        return 1

    state = load_json(STATE_FILE, {})  # { handle: bool_in_stock }
    first_run = not STATE_FILE.exists()

    try:
        products = fetch_all_products(store)
    except Exception as e:
        print(f"!! failed to fetch store: {e}")
        return 0

    print(f"Checked {len(products)} products in {store}")

    newly_in_stock = []
    new_state = {}
    for p in products:
        handle = p["handle"]
        in_stock = is_in_stock(p)
        new_state[handle] = in_stock
        was = state.get(handle, False)
        if in_stock and not was:
            newly_in_stock.append(p)

    # On the very first run, just record the baseline — don't alert on everything
    # that already happens to be in stock.
    if newly_in_stock and not first_run:
        try:
            send_alert(store, newly_in_stock)
        except Exception as e:
            print(f"!! failed to send alert: {e}")
            return 0  # keep old state so we retry next run
    elif first_run:
        print("First run: recording baseline, no alerts sent.")
    else:
        print("Nothing newly in stock.")

    if new_state != state:
        STATE_FILE.write_text(json.dumps(new_state, indent=2, sort_keys=True))
        print("State updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
