import discord
from discord.ext import tasks
import requests
import time
from playwright.sync_api import sync_playwright

# -------- CONFIG --------
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"
DISCORD_CHANNEL_ID = 123456789012345678  # your channel ID
ELDORADO_URL = "https://www.eldorado.gg/steam-accounts/a/42-0-0?pageSize=24&searchQuery=gorilla%20tag"
GORILLA_TAG_URL = "https://lzt.market/steam/gorilla-tag/?limit=yes&rt=nomatter&order_by=price_to_up"
CHECK_INTERVAL = 60  # seconds between checks

# -------- DISCORD SETUP --------
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
last_eldorado_ids = set()
last_gorilla_ids = set()

def fetch_eldorado():
    response = requests.get(ELDORADO_URL)
    data = response.json()  # assuming Eldorado returns JSON
    new_offers = []
    removed_offers = []

    global last_eldorado_ids
    current_ids = set(item["id"] for item in data["offers"])
    
    # new offers
    for item in data["offers"]:
        if item["id"] not in last_eldorado_ids:
            new_offers.append(item)

    # removed offers
    for old_id in last_eldorado_ids:
        if old_id not in current_ids:
            removed_offers.append(old_id)

    last_eldorado_ids = current_ids
    return new_offers, removed_offers

def fetch_gorilla_tag():
    response = requests.get(GORILLA_TAG_URL)
    data = response.json()
    new_offers = []

    global last_gorilla_ids
    current_ids = set(item["id"] for item in data["offers"])
    
    for item in data["offers"]:
        if item["id"] not in last_gorilla_ids:
            new_offers.append(item)

    last_gorilla_ids = current_ids
    return new_offers

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_offers():
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("Channel not found")
        return

    # Eldorado
    new_eldorado, removed_eldorado = fetch_eldorado()
    for offer in new_eldorado:
        await channel.send(f"🔥 NEW ELDORADO LISTING\n💰 {offer['price']}\n🔗 {offer['link']} @everyone")
    for offer_id in removed_eldorado:
        await channel.send(f"❌ ELDORADO LISTING REMOVED\nID: {offer_id} @everyone")

    # Gorilla Tag
    new_gorilla = fetch_gorilla_tag()
    for offer in new_gorilla:
        await channel.send(f"🐒 NEW GORILLA TAG ACCOUNT\n💰 {offer['price']}\n🔗 {offer['link']} @everyone")

# -------- RUN BOT --------
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    check_offers.start()

client.run(DISCORD_TOKEN)
