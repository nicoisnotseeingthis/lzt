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
ELDO_URL = "https://www.eldorado.gg/steam-accounts/a/42-0-0?pageSize=24&searchQuery=gorilla%20tag"

CHECK_DELAY = 15  # seconds

# =========================
# 💾 SAVE / LOAD DATA
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
        headless=True,  # ✅ required for GitHub
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )

    page = browser.new_page()

    print("🔥 SNIPER STARTED")

    while True:
        try:
            # =========================
            # 🟢 LZT
            # =========================
            page.goto(LZT_URL)
            page.wait_for_selector('[id^="marketItem--"]')

            items = page.query_selector_all('[id^="marketItem--"]')

            for item in items:
                try:
                    item_id = item.get_attribute("id").replace("marketItem--", "")

                    title = item.inner_text().split("\n")[0].strip()

                    price_el = item.query_selector(".price")
                    if not price_el:
                        continue

                    price = float(price_el.inner_text().replace("$", "").strip())
                    link = f"https://lzt.market/{item_id}"

                    key = f"lzt_{item_id}"
                    old_price = listings.get(key)

                    # 🆕 NEW
                    if key not in listings:
                        listings[key] = price
                        save()
                        send(title, price, link, "🟢 New LZT Listing", ping=False)

                    # 🔥 PRICE CHANGE
                    elif old_price != price:
                        listings[key] = price
                        save()
                        send(title, price, link, "🔥 LZT Price Changed", ping=True)

                except:
                    continue

            # =========================
            # 🔴 ELDORADO
            # =========================
            page.goto(ELDO_URL)
            page.wait_for_timeout(5000)

            cards = page.query_selector_all('a[href*="steam-accounts"]')

            current_ids = set()

            for card in cards:
                try:
                    link = card.get_attribute("href")
                    if not link:
                        continue

                    link = "https://www.eldorado.gg" + link
                    key = f"eldo_{link}"
                    current_ids.add(key)

                    text = card.inner_text().replace("\n", " ").strip()

                    if "$" not in text:
                        continue

                    price = float(text.split("$")[1].split(" ")[0])
                    title = text.split("$")[0][:60].strip()

                    old_price = listings.get(key)

                    # 🆕 NEW
                    if key not in listings:
                        listings[key] = price
                        save()
                        send(title, price, link, "🔥 New Eldorado Listing", ping=True)

                    # 🔥 PRICE CHANGE
                    elif old_price != price:
                        listings[key] = price
                        save()
                        send(title, price, link, "🔥 Price Updated", ping=True)

                except:
                    continue

            # ❌ REMOVED (ELDORADO ONLY)
            for key in list(listings.keys()):
                if key.startswith("eldo_") and key not in current_ids:
                    link = key.replace("eldo_", "")
                    old_price = listings[key]

                    send("Listing Removed", old_price, link, "❌ Eldorado Removed", ping=True)

                    del listings[key]
                    save()

            print("✅ cycle complete")
            time.sleep(CHECK_DELAY)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)
