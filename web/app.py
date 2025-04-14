from flask import Flask, redirect, request, session, url_for
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = 'http://localhost:5000/callback'
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

DISCORD_API_BASE = "https://discord.com/api"
OAUTH_SCOPE = "identify connections"

@app.route("/")
def index():
    return "Go to your bot and use `!linksteam` to start."

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "No code provided."

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "scope": OAUTH_SCOPE
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Get access token
    token_res = requests.post(f"{DISCORD_API_BASE}/oauth2/token", data=data, headers=headers)
    token_res.raise_for_status()
    access_token = token_res.json()['access_token']

    # After getting access_token from Discord
    user_res = requests.get("https://discord.com/api/users/@me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    user_res.raise_for_status()
    user = user_res.json()

    discord_id = user['id']
    
    # Get connections (Steam, Xbox, etc.)
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    conn_res = requests.get(f"{DISCORD_API_BASE}/users/@me/connections", headers=headers)
    conn_res.raise_for_status()
    connections = conn_res.json()

    # Find Steam
    steams = [c for c in connections if c['type'] == 'steam']
    
    if not steams:
        return "No Steam account linked."

    steam = sorted(steams, key=lambda x: get_steam_level(x['id']))[-1]
    
    steam_id = steam['id']
    steam_name = steam['name']

    # Fetch Steam level
    steam_level = get_steam_level(steam_id)
    
    save_user(discord_id, steam_id, steam_name, steam_level)
    return f"✅ {steam_name}'s Steam level is {steam_level} (SteamID: {steam_id})"

def get_steam_level(steam_id):
    url = "https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/"
    params = {
        "key": STEAM_API_KEY,
        "steamid": steam_id
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json().get("response", {}).get("player_level", "Unknown")

def save_user(discord_id, steam_id, steam_name, steam_level):
    conn = sqlite3.connect('/home/deepforce/DuobotBot/db/db.sqlite')
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO users (discord_id, steam_id, steam_name, steam_level, last_updated)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        discord_id,
        steam_id,
        steam_name,
        steam_level,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True)
