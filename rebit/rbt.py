# -*- coding: utf-8 -*-

import requests
import json
import os
import time
import logging


# -----------------------
# LOGIN DATA
# -----------------------
USERNAME = ""
PASSWORD = ""


# -----------------------
# PATH
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOKEN_FILE = os.path.join(BASE_DIR, "rebit_token.json")
PLAYLIST_FILE = os.path.join(BASE_DIR, "playlist.m3u")


BASE_URL = "https://bbxnet.api.iptv.rebit.sk"

# -----------------------
# LOGGING
# -----------------------
logger = logging.getLogger("rebit")


# -----------------------
# LOAD / SAVE TOKEN
# -----------------------
def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Load token failed: {e}")
        return None


def save_token(data):
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Save token failed: {e}")


# -----------------------
# LOGIN
# -----------------------
def login():
    try:
        logger.info("Login...")

        headers = {"Content-Type": "application/json"}
        data = {"username": USERNAME, "password": PASSWORD}

        r = requests.post(f"{BASE_URL}/auth/auth", json=data, headers=headers)

        if r.status_code not in (200, 201):
            logger.error(f"Login failed: {r.text}")
            return None

        d = r.json()["data"]

        token_data = {
            "access_token": d["access_token"],
            "refresh_token": d["refresh_token"],
            "expires": int(time.time()) + d["expire_in"] - 5,
            "device_id": ""
        }

        save_token(token_data)
        logger.info("Login OK")

        return token_data

    except Exception as e:
        logger.error(f"Login error: {e}")
        return None


# -----------------------
# REFRESH TOKEN
# -----------------------
def refresh(token_data):
    try:
        logger.info("Refreshing token...")

        headers = {
            "Authorization": f"Bearer {token_data['refresh_token']}"
        }

        r = requests.post(f"{BASE_URL}/auth/auth", headers=headers)

        if r.status_code not in (200, 201):
            logger.warning("Refresh failed → login")
            return login()

        d = r.json()["data"]

        new_token = {
            "access_token": d["access_token"],
            "refresh_token": d["refresh_token"],
            "expires": int(time.time()) + d["expire_in"] - 5,
            "device_id": token_data.get("device_id", "")
        }

        save_token(new_token)
        logger.info("Refresh OK")

        return new_token

    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return login()


# -----------------------
# GET VALID TOKEN
# -----------------------
def get_valid_token():
    token = load_token()

    if not token:
        return login()

    if token["expires"] < time.time():
        return refresh(token)

    return token


# -----------------------
# REGISTER DEVICE
# -----------------------
def register_device(access_token):
    try:
        logger.info("Register device...")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "title": "PyServe",
            "type": "computer",
            "child_lock_code": "0000"
        }

        r = requests.post(f"{BASE_URL}/television/client", json=data, headers=headers)

        if r.status_code not in (200, 201):
            logger.error(f"Device register failed: {r.text}")
            return None

        device_id = r.json()["data"]["id"]

        logger.info(f"Device OK: {device_id}")
        return device_id

    except Exception as e:
        logger.error(f"Device error: {e}")
        return None


# -----------------------
# GET DEVICE ID
# -----------------------
def get_device_id(token_data):
    if token_data.get("device_id"):
        return token_data["device_id"]

    device_id = register_device(token_data["access_token"])

    if device_id:
        token_data["device_id"] = device_id
        save_token(token_data)

    return device_id


# -----------------------
# CREATE PLAYLIST
# -----------------------
def create_playlist():
    try:
        logger.info("Creating playlist...")

        token_data = get_valid_token()
        if not token_data:
            return False

        token = token_data["access_token"]

        device_id = get_device_id(token_data)
        if not device_id:
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "x-television-client-id": device_id
        }

        r = requests.get(f"{BASE_URL}/television/channels", headers=headers)

        if r.status_code != 200:
            logger.error(f"Channels error: {r.text}")
            return False

        channels = r.json()["data"]

        # SORT
        channels_sorted = sorted(channels, key=lambda x: x["channel"])

        lines = ["#EXTM3U"]

        for ch in channels_sorted:
            name = ch["title"].replace(" HD", "")
            logo = ch["icon"]
            cid = ch["id"]

            lines.append(f'#EXTINF:-1 tvg-logo="{logo}",{name}')
            lines.append(f"http://127.0.0.1:9666/rebit/{cid}.m3u8")

        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("Playlist OK")
        return True

    except Exception as e:
        logger.error(f"Playlist error: {e}")
        return False


# -----------------------
# STREAM
# -----------------------
def get_stream(channel_id):
    FALLBACK = "http://sledovanietv.sk/download/noAccess-cs.m3u8"

    try:
        logger.info(f"Stream {channel_id}")

        token_data = get_valid_token()
        if not token_data:
            return FALLBACK

        device_id = get_device_id(token_data)
        if not device_id:
            return FALLBACK

        headers = {
            "Authorization": f"Bearer {token_data['access_token']}",
            "x-television-client-id": device_id
        }

        url = f"{BASE_URL}/television/channels/{channel_id}/play"

        r = requests.get(url, headers=headers, timeout=5)

        if r.status_code != 200:
            logger.error(r.text)
            return FALLBACK

        data = r.json()

        return data["data"]["link"]

    except Exception as e:
        logger.error(f"Stream error: {e}")
        return FALLBACK