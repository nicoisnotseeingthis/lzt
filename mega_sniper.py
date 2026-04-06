from playwright.sync_api import sync_playwright
import requests
import time
import json
import os

# 🔗 PUT YOUR WEBHOOK HERE OR USE GITHUB SECRET
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "YOUR_WEBHOOK_HERE"

LZT_URL = "https://lzt.market/steam/gorilla-tag/?limit=yes&rt=nomatter&order_by=price_to_up"
ELDO_URL = "https://www.eldorado.gg/steam-accounts/a/42-0-0?pageSize=24&searchQuery=gorilla%20tag"

# =========================
# LOAD DATA
# =========================
try:
    with open("data.json", "r") as f:
        data = json.load(f)
        listings = data.get("listings", {})
except:
    listings = {}

def save():
    with open("data.json", "w") as f:
        json.dump({"listings": listings}, f)

# =========================
# DISCORD WEBHOOK
# =========================
def send(event, title, price, link, ping=False):
    data = {
        "content": "@everyone" if ping else "",
        "embeds": [
            {
                "title": title,
                "description": f"{event}\n💰 ${price}\n🔗 {link}",
                "color": 16711680
            }
        ]
    }

    try:
        requests.post(WEBHOOK_URL, json=data)
    except:
        print("Webhook failed")

# =========================
# MAIN BOT
# =========================
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,  # ✅ REQUIRED FOR GITHUB
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )

    page = browser.new_page()

    print("🔥 SNIPER STARTED")

    while True:
        try:
            # =====================
            # 🟢 LZT (GORILLA TAG)
            # =====================
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

                    old = listings.get(item_id)

                    # 🆕 NEW
                    if not old:
                        listings[item_id] = price
                        save()
                        send("🟢 NEW LZT LISTING", title, price, link, ping=False)

                    # 🔥 PRICE CHANGE
                    elif old != price:
                        listings[item_id] = price
                        save()
                        send("🔥 LZT PRICE CHANGED", title, price, link, ping=True)

                except:
                    continue

            # =====================
            # 🔴 ELDORADO
            # =====================
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
                    item_id = link
                    current_ids.add(item_id)

                    text = card.inner_text().replace("\n", " ").strip()

                    if "$" not in text:
                        continue

                    price_text = text.split("$")[1].split(" ")[0]
                    price = float(price_text)

                    title = text.split("$")[0][:60].strip()

                    old = listings.get(item_id)

                    # 🆕 NEW
                    if not old:
                        listings[item_id] = price
                        save()
                        send("🔥 NEW ELDORADO LISTING", title, price, link, ping=True)

                    # 🔥 PRICE CHANGE / EDIT
                    elif old != price:
                        listings[item_id] = price
                        save()
                        send("🔥 ELDORADO PRICE CHANGED", title, price, link, ping=True)

                except:
                    continue

            # ❌ REMOVED (ELDORADO ONLY)
            removed = set(listings.keys()) - current_ids

            for item_id in list(removed):
                if "eldorado.gg" in item_id:
                    old_price = listings.get(item_id, "Unknown")

                    send("❌ LISTING REMOVED", "Eldorado Listing Removed", old_price, item_id, ping=True)

                    del listings[item_id]
                    save()

            print("✅ cycle done")
            time.sleep(15)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)
