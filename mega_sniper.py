from playwright.sync_api import sync_playwright
import requests
import time
import json
import os

# =========================
# 🔗 CONFIG
# =========================
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "YOUR_WEBHOOK_HERE"

LZT_URL = "https://lzt.market/steam/gorilla-tag/?limit=yes&rt=nomatter&order_by=price_to_up"
CHECK_DELAY = 10  # seconds

# =========================
# 💾 SAVE / LOAD
# =========================
try:
    with open("data.json", "r") as f:
        listings = json.load(f)
except:
    listings = {}

def save():
    with open("data.json", "w") as f:
        json.dump(listings, f)

# =========================
# 📡 CLEAN WEBHOOK
# =========================
def send(title, price, link, event, ping=False):
    data = {
        "content": "@everyone" if ping else "",
        "embeds": [
            {
                "title": title[:80],
                "url": link,
                "description": f"{event}\n💰 **${price}**",
                "color": 0x3498db,  # 🔵 clean blue
                "footer": {
                    "text": "Gorilla Tag Sniper"
                }
            }
        ]
    }

    try:
        requests.post(WEBHOOK_URL, json=data)
    except:
        print("Webhook failed")

# =========================
# 🧠 BOT
# =========================
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,  # 🔁 set True if using GitHub
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )

    page = browser.new_page()

    print("🔥 LZT SNIPER STARTED")

    while True:
        try:
            page.goto(LZT_URL)
            page.wait_for_selector('[id^="marketItem--"]')

            items = page.query_selector_all('[id^="marketItem--"]')
            print(f"📦 Found {len(items)} listings")

            for item in items:
                try:
                    item_id = item.get_attribute("id").replace("marketItem--", "")
                    key = f"lzt_{item_id}"

                    title = item.inner_text().split("\n")[0].strip()

                    price_el = item.query_selector(".price")
                    if not price_el:
                        continue

                    price = float(price_el.inner_text().replace("$", "").strip())
                    link = f"https://lzt.market/{item_id}"

                    old_price = listings.get(key)

                    # 🆕 NEW LISTING
                    if key not in listings:
                        listings[key] = price
                        save()
                        send(title, price, link, "🟢 New Listing", ping=False)
                        print(f"NEW: {title} - ${price}")

                    # 🔥 PRICE CHANGE
                    elif old_price != price:
                        listings[key] = price
                        save()
                        send(title, price, link, "🔥 Price Updated", ping=True)
                        print(f"UPDATED: {title} - ${price}")

                except Exception as e:
                    print("Item error:", e)

            time.sleep(CHECK_DELAY)

        except Exception as e:
            print("Loop error:", e)
            time.sleep(5)
