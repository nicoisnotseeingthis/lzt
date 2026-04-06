from playwright.sync_api import sync_playwright
import requests
import time
import os

# 🔐 Use secret in GitHub
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

URL = "https://lzt.market/steam/gorilla-tag/?limit=yes&rt=nomatter&order_by=price_to_up"

seen = set()

def send_webhook(title, price, link):
    data = {
        "content": "@everyone",
        "embeds": [
            {
                "title": title,
                "description": f"💰 Price: ${price}\n🔗 {link}",
                "color": 5814783
            }
        ]
    }
    requests.post(WEBHOOK_URL, json=data)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # ✅ REQUIRED FOR GITHUB
    page = browser.new_page()

    page.goto(URL)

    print("Sniper started...")

    for _ in range(10):  # ⚠️ runs limited times (GitHub limit)
        try:
            print("Refreshing...")
            page.reload()

            page.wait_for_selector('[id^="marketItem--"]', timeout=10000)

            items = page.query_selector_all('[id^="marketItem--"]')
            print("Found:", len(items))

            for item in items:
                try:
                    item_id = item.get_attribute("id")
                    if not item_id:
                        continue

                    item_id = item_id.replace("marketItem--", "")

                    if item_id in seen:
                        continue

                    price_el = item.query_selector(".price")
                    if not price_el:
                        continue

                    price = float(price_el.inner_text().replace("$", "").strip())

                    if price > 5:
                        continue

                    title = item.inner_text().split("\n")[0]

                    link = f"https://lzt.market/{item_id}"

                    seen.add(item_id)

                    send_webhook(title, price, link)
                    print("Sent:", title)

                except:
                    continue

            time.sleep(10)

        except Exception as e:
            print("Error:", e)

    browser.close()
