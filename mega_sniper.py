# mega_sniper.py
import time
import json
import requests
from playwright.sync_api import sync_playwright

# ---------------- CONFIG ----------------
DISCORD_WEBHOOK = "YOUR_DISCORD_WEBHOOK"
HEADLESS = True  # True for GitHub Actions, False for PC debugging
SLEEP_INTERVAL = 60  # seconds between checks

# Eldorado / Gorilla Tag sources
ELDORADO_URL = "https://www.eldorado.gg/steam-accounts/a/42-0-0?pageSize=24&searchQuery=gorilla%20tag"
GORILLA_TAG_URL = "https://lzt.market/steam/gorilla-tag/?limit=yes&rt=nomatter&order_by=price_to_up"

# Store seen listings to detect new/edited/deleted
seen_listings = set()
# ----------------------------------------

def send_discord(title, url, price, status="NEW"):
    data = {
        "content": f"@everyone",
        "embeds": [{
            "title": f"{status} - {title}",
            "url": url,
            "description": f"💰 Price: {price}",
            "color": 16711680 if status=="REMOVED" else 65280
        }]
    }
    requests.post(DISCORD_WEBHOOK, json=data)

def fetch_eldorado_listings():
    try:
        resp = requests.get(ELDORADO_URL, headers={"User-Agent": "Mozilla/5.0"})
        listings = resp.json().get("data", [])
        results = []
        for l in listings:
            pid = l["id"]
            title = l["name"]
            price = l.get("price", "Unknown")
            url = f"https://www.eldorado.gg/steam-accounts/{pid}"
            results.append((pid, title, price, url))
        return results
    except Exception as e:
        print("Eldorado fetch error:", e)
        return []

def fetch_gorilla_tag():
    try:
        resp = requests.get(GORILLA_TAG_URL, headers={"User-Agent": "Mozilla/5.0"})
        listings = resp.json().get("items", [])
        results = []
        for l in listings:
            pid = l["id"]
            title = l["title"]
            price = l.get("price", "Unknown")
            url = f"https://lzt.market/steam/gorilla-tag/{pid}"
            results.append((pid, title, price, url))
        return results
    except Exception as e:
        print("Gorilla Tag fetch error:", e)
        return []

# ---------------- MAIN LOOP ----------------
with sync_playwright() as p:
    browser = p.chromium.launch(headless=HEADLESS, args=["--no-sandbox", "--disable-dev-shm-usage"])
    context = browser.new_context()
    page = context.new_page()

    while True:
        try:
            # Eldorado
            for pid, title, price, url in fetch_eldorado_listings():
                if pid not in seen_listings:
                    send_discord(title, url, price, "NEW")
                    seen_listings.add(pid)

            # Detect removed listings
            for old_pid in list(seen_listings):
                current_pids = {pid for pid, _, _, _ in fetch_eldorado_listings()}
                if old_pid not in current_pids:
                    send_discord(f"Listing {old_pid}", "", "", "REMOVED")
                    seen_listings.remove(old_pid)

            # Gorilla Tag
            for pid, title, price, url in fetch_gorilla_tag():
                if pid not in seen_listings:
                    send_discord(title, url, price, "NEW")
                    seen_listings.add(pid)

            time.sleep(SLEEP_INTERVAL)

        except Exception as e:
            print("Main loop error:", e)
            time.sleep(30)
