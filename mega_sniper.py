from playwright.sync_api import sync_playwright
import requests
import time
import json
import os

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

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
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    print("🔥 MEGA SNIPER STARTED")

    # ~5 hours
    for _ in range(1800):
        try:
            # =====================
            # 🟢 LZT
            # =====================
            page.goto(LZT_URL)
            page.wait_for_selector('[id^="marketItem--"]')

            items = page.query_selector_all('[id^="marketItem--"]')

            for item in items:
                try:
                    item_id = item.get_attribute("id").replace("marketItem--", "")

                    if item_id in seen:
                        continue

                    price_el = item.query_selector(".price")
                    if not price_el:
                        continue

                    price = float(price_el.inner_text().replace("$", "").strip())

                    title = item.inner_text().split("\n")[0]
                    link = f"https://lzt.market/{item_id}"

                    seen.add(item_id)
                    save()

                    send("🟢 NEW LZT LISTING", title, price, link, ping=False)

                except:
                    continue

            # =====================
            # 🔴 ELDORADO
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

                    # NEW
                    if item_id not in seen:
                        seen.add(item_id)
                        prices[item_id] = price
                        save()

                        send("🔥 NEW ELDORADO LISTING", title, price, link, ping=True)
                        continue

                    # PRICE CHANGE
                    old_price = prices.get(item_id)

                    if old_price and price != old_price:
                        prices[item_id] = price
                        save()

                        send("🔥 PRICE CHANGED", title, price, link, ping=True)

                except:
                    continue

            # REMOVED
            removed = set(prices.keys()) - current_ids

            for item_id in removed:
                old_price = prices.get(item_id, "Unknown")

                send("❌ LISTING REMOVED", "Eldorado Listing Removed", old_price, item_id, ping=True)

                prices.pop(item_id, None)
                seen.discard(item_id)

            save()

            print("✅ cycle done")
            time.sleep(10)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)

    browser.close()

restart()
