import requests
import time
import json
import discord
from discord import Webhook, RequestsWebhookAdapter

# === CONFIG ===
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"
ELDORADO_SEARCH_URL = "https://www.eldorado.gg/steam-accounts/a/42-0-0?pageSize=24&searchQuery=gorilla%20tag"
SCRAPE_INTERVAL = 20  # seconds between checks

# === SETUP DISCORD ===
webhook = Webhook.from_url(DISCORD_WEBHOOK_URL, adapter=RequestsWebhookAdapter())

# === TRACK LISTINGS ===
eldorado_seen = {}  # {pid: price}
steam_seen = {}     # {id: price}

# === FUNCTIONS ===

def fetch_eldorado_listings():
    """Returns a list of (pid, title, price, url)"""
    try:
        r = requests.get(ELDORADO_SEARCH_URL, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Eldorado fetch error: {e}")
        return []

    listings = []
    for item in data.get("items", []):
        pid = str(item.get("id"))
        title = item.get("title")
        price = float(item.get("price", 0))
        url = f"https://www.eldorado.gg/steam-accounts/{pid}"
        listings.append((pid, title, price, url))
    return listings

def send_discord(title, url, price, status):
    """Send message to Discord webhook"""
    if status == "NEW":
        emoji = "🔥"
    elif status == "EDITED":
        emoji = "✏️"
    elif status == "REMOVED":
        emoji = "❌"
    else:
        emoji = ""
    message = f"{emoji} **{status}**\n💰 {price}\n🔗 {url}\n**{title}**\n@everyone"
    try:
        webhook.send(message)
    except Exception as e:
        print(f"Discord send error: {e}")

# === MAIN LOOP ===
while True:
    # --- Eldorado ---
    listings = fetch_eldorado_listings()
    current_pids = set()

    for pid, title, price, url in listings:
        current_pids.add(pid)
        old_price = eldorado_seen.get(pid)
        if old_price is None:
            send_discord(title, url, price, "NEW")
            eldorado_seen[pid] = price
        elif old_price != price:
            send_discord(title, url, price, "EDITED")
            eldorado_seen[pid] = price

    # Detect removed listings
    for old_pid in list(eldorado_seen.keys()):
        if old_pid not in current_pids:
            send_discord(f"Listing {old_pid}", "", "", "REMOVED")
            del eldorado_seen[old_pid]

    # --- Wait before next check ---
    time.sleep(SCRAPE_INTERVAL)
