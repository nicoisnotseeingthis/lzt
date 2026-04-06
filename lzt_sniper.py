from playwright.sync_api import sync_playwright
import requests
import time
import os
import json

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

URL = "https://lzt.market/telegram/?order_by=pdate_to_down"

# 🔁 Load seen items from file
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
        "content": "",
        "embeds": [
            {
                "title": title,
                "description": f"💰 {price}\n🔗 {link}",
                "color": 3447003
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
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL)
    print("🔥 Sniper started...")

    # ⏱️ ~5 hours runtime (1800 × 10 sec)
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

                    title = item.inner_text().strip().split("\n")[0]

                    price_el = item.query_selector(".price")
                    price = price_el.inner_text() if price_el else "No price"

                    link = f"https://lzt.market/{item_id}"

                    seen.add(item_id)
                    save_seen()

                    send_webhook(title, price, link)
                    print(f"🚀 SENT: {title}")

                except Exception as e:
                    print("Item error:", e)

            time.sleep(10)

        except Exception as e:
            print("Loop error:", e)
            time.sleep(5)

    browser.close()

# 🔁 Restart workflow after finishing
restart()
