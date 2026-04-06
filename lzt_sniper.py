from playwright.sync_api import sync_playwright
import requests
import time
import os
import json

WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "YOUR_WEBHOOK_HERE"

URL = "https://lzt.market/steam/gorilla-tag/?limit=yes&rt=nomatter&order_by=price_to_up"

# 🔁 load seen items
try:
    with open("seen.json", "r") as f:
        seen = set(json.load(f))
except:
    seen = set()

def save_seen():
    with open("seen.json", "w") as f:
        json.dump(list(seen), f)

def send_webhook(title, price, link):
    data = {
        "content": "",  # change to "@everyone" if you want
        "embeds": [
            {
                "title": title,
                "description": f"💰 ${price}\n🔗 {link}",
                "color": 5814783
            }
        ]
    }
    try:
        requests.post(WEBHOOK_URL, json=data)
    except:
        print("Webhook failed")

def restart():
    try:
        token = os.getenv("GH_TOKEN")
        repo = os.getenv("GITHUB_REPOSITORY")

        if not token or not repo:
            return

        url = f"https://api.github.com/repos/{repo}/actions/workflows/bot.yml/dispatches"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        requests.post(url, headers=headers, json={"ref": "main"})
        print("♻️ Restart triggered")

    except Exception as e:
        print("Restart error:", e)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # False if running on PC
    page = browser.new_page()

    page.goto(URL)
    print("🔥 Gorilla Tag sniper started...")

    # ⏱️ ~5 hours runtime
    for _ in range(1800):
        try:
            print("🔄 Refreshing...")

            page.reload()
            page.wait_for_selector('[id^="marketItem--"]', timeout=10000)

            items = page.query_selector_all('[id^="marketItem--"]')
            print(f"📦 Found {len(items)} items")

            for item in items:
                try:
                    item_id = item.get_attribute("id")
                    if not item_id:
                        continue

                    item_id = item_id.replace("marketItem--", "")

                    if item_id in seen:
                        continue

                    # 🏷️ title
                    title = item.inner_text().strip().split("\n")[0]

                    # 💰 price
                    price_el = item.query_selector(".price")
                    if not price_el:
                        continue

                    price = float(price_el.inner_text().replace("$", "").strip())

                    # 🔥 FILTER (CHANGE THIS)
                    if price > 5:
                        continue

                    link = f"https://lzt.market/{item_id}"

                    seen.add(item_id)
                    save_seen()

                    send_webhook(title, price, link)

                    print(f"🔥 FOUND: {title} - ${price}")

                except Exception as e:
                    print("Item error:", e)

            time.sleep(10)

        except Exception as e:
            print("Loop error:", e)
            time.sleep(5)

    browser.close()

# 🔁 restart GitHub workflow
restart()
