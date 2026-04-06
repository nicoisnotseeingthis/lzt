from playwright.sync_api import sync_playwright
import requests
import time
import json
import os

WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "YOUR_WEBHOOK"

LZT_URL = "https://lzt.market/steam/gorilla-tag/?limit=yes&rt=nomatter&order_by=price_to_up"
ELDO_URL = "https://www.eldorado.gg/steam-accounts/a/42-0-0?pageSize=24&searchQuery=gorilla%20tag"

# load saved data
try:
    with open("data.json", "r") as f:
        data = json.load(f)
        seen = set(data.get("seen", []))
        prices = data.get("prices", {})
except:
    seen = set()
    prices = {}

def save():
    with open("data.json", "w") as f:
        json.dump({"seen": list(seen), "prices": prices}, f)

def send(msg, title=None, price=None, link=None, ping=False):
    data = {
        "content": "@everyone" if ping else "",
        "embeds": [
            {
                "title": title or msg,
                "description": f"{msg}\n💰 {price}\n🔗 {link}",
                "color": 16711680
            }
        ]
    }
    requests.post(WEBHOOK_URL, json=data)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    print("🔥 MEGA SNIPER STARTED")

    while True:
        try:
            # =====================
            # 🔴 ELDORADO CHECK
            # =====================
            page.goto(ELDO_URL)
            page.wait_for_timeout(5000)

            html = page.content()

            current_ids = set()

            blocks = html.split('href="/')

            for block in blocks:
                if "steam-accounts" not in block:
                    continue

                try:
                    link_part = block.split('"')[0]
                    link = "https://www.eldorado.gg/" + link_part

                    item_id = link
                    current_ids.add(item_id)

                    title = block.split(">")[1][:60]

                    if "$" not in block:
                        continue

                    price_text = block.split("$")[1].split("<")[0]
                    price = float(price_text)

                    # 🟢 NEW LISTING
                    if item_id not in seen:
                        seen.add(item_id)
                        prices[item_id] = price
                        save()

                        send("🔥 NEW ELDORADO LISTING", title, price, link, ping=True)
                        print("NEW:", title)
                        continue

                    # 🔥 PRICE CHANGE
                    old_price = prices.get(item_id)

                    if old_price and price != old_price:
                        prices[item_id] = price
                        save()

                        send("🔥 PRICE CHANGED", title, price, link, ping=True)
                        print("PRICE CHANGE:", title)

                except:
                    continue

            # ❌ REMOVED LISTINGS
            removed = set(prices.keys()) - current_ids

            for item_id in removed:
                old_price = prices.get(item_id, "Unknown")

                send("❌ LISTING REMOVED", "Eldorado Listing Removed", old_price, item_id, ping=True)
                print("REMOVED:", item_id)

                # remove from tracking
                prices.pop(item_id, None)
                seen.discard(item_id)

            save()

            print("✅ cycle done")
            time.sleep(10)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)
