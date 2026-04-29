# -*- coding: utf-8 -*-

import requests
import json
import os
import uuid
import logging
from urllib.parse import quote

# -----------------------
# LOGIN DATA
# -----------------------
USERNAME = ""
PASSWORD = ""
PIN = ""

PRODUCT = "Samsung"
#DEVICE_TYPE = "androidportable"
DEVICE_TYPE = "samsungtv"
CODEC = "h265"

BASE_URL = "https://sledovanitv.cz"

# -----------------------
# PATH
# -----------------------
PATH = os.path.dirname(__file__)
DATA_FILE = os.path.join(PATH, "stv.json")
PLAYLIST_FILE = os.path.join(PATH, "playlist.m3u")

# -----------------------
# LOGGING
# -----------------------
logger = logging.getLogger("sledovanitv")

# -----------------------
# HEADERS
# -----------------------
HEADERS = {
    "User-Agent": "okhttp/3.12.12"
}

# -----------------------
# CACHE
# -----------------------
SESSION_CACHE = {"sessid": None}
QUALITY_CACHE = {"value": None}
CHANNEL_CACHE = {"data": None}


# -----------------------
# MAC
# -----------------------
def generate_mac():
    try:
        mac_num = hex(uuid.getnode()).replace('0x', '').upper()
        return ':'.join(mac_num[i:i+2] for i in range(0, 11, 2))
    except Exception as e:
        logger.error(f"MAC error: {e}")
        return "00:00:00:00:00:00"


# -----------------------
# LOAD / SAVE DEVICE
# -----------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Load failed: {e}")
        return None


def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Save failed: {e}")


# -----------------------
# REGISTER DEVICE
# -----------------------
def register_device():
    try:
        mac = generate_mac()

        url = (
            f"{BASE_URL}/api/create-pairing?"
            f"username={quote(USERNAME)}&"
            f"password={quote(PASSWORD)}&"
            f"type={DEVICE_TYPE}&"
            f"product={PRODUCT}&"
            f"serial={mac}"
        )

        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            logger.error(f"HTTP error {r.status_code}")
            return None

        data = r.json()

        if data.get("status") != 1:
            logger.error(f"API error {data}")
            return None

        save_data(data)
        logger.info(f"Device OK {data.get('deviceId')}")

        return data

    except Exception as e:
        logger.error(f"Register error {e}")
        return None


# -----------------------
# DEVICE
# -----------------------
def get_device():
    data = load_data()
    if data and data.get("deviceId") and data.get("password"):
        return data
    return register_device()


# -----------------------
# SESSION + PIN
# -----------------------
def get_session():
    try:
        if SESSION_CACHE["sessid"]:
            return SESSION_CACHE["sessid"]

        device = get_device()
        if not device:
            return None

        url = (
            f"{BASE_URL}/api/device-login?"
            f"deviceId={device['deviceId']}&"
            f"password={device['password']}&"
            f"version=2.44.16&lang=cs&unit=default"
        )

        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        if data.get("status") != 1:
            logger.error("Session failed")
            return None

        sessid = data.get("PHPSESSID")

        # PIN unlock
        if PIN:
            try:
                requests.get(
                    f"{BASE_URL}/api/pin-unlock?pin={PIN}&PHPSESSID={sessid}",
                    headers=HEADERS,
                    timeout=5
                )
            except:
                pass

        SESSION_CACHE["sessid"] = sessid
        return sessid

    except Exception as e:
        logger.error(f"Session error {e}")
        return None


# -----------------------
# QUALITY (ONLY ONCE)
# -----------------------
def get_best_quality(sessid):
    if QUALITY_CACHE["value"]:
        return QUALITY_CACHE["value"]

    try:
        r = requests.get(
            f"{BASE_URL}/api/get-stream-qualities?PHPSESSID={sessid}",
            timeout=10
        )

        data = r.json()

        qualities = [
            q["id"] for q in data.get("qualities", [])
            if q.get("allowed") == 1
        ]

        if not qualities:
            return "40"

        qualities.sort()
        QUALITY_CACHE["value"] = qualities[-1]

        return QUALITY_CACHE["value"]

    except Exception as e:
        logger.error(f"Quality error {e}")
        return "40"


# -----------------------
# CHANNELS
# -----------------------
def get_channels(sessid, quality):
    try:
        if CHANNEL_CACHE["data"]:
            return CHANNEL_CACHE["data"]

        params = {
            "quality": quality,
            "force": "true",
            "format": "m3u8",
            "logosize": "256",
            "whitelogo": "true",
            "capabilities": CODEC + ",vast,clientvast,adaptive2,webvtt",
            "subtitles": "1",
            "PHPSESSID": sessid
        }

        r = requests.get(
            f"{BASE_URL}/api/playlist",
            params=params,
            headers=HEADERS,
            timeout=10
        )

        data = r.json()

        if data.get("status") != 1:
            return []

        CHANNEL_CACHE["data"] = data.get("channels", [])
        return CHANNEL_CACHE["data"]

    except Exception as e:
        logger.error(f"Channels error {e}")
        return []


# -----------------------
# PLAYLIST
# -----------------------
def create_playlist():
    try:
        sessid = get_session()
        if not sessid:
            return False

        quality = get_best_quality(sessid)
        channels = get_channels(sessid, quality)

        lines = ["#EXTM3U"]

        for ch in channels:
            if ch.get("locked") != "none":
                continue

            lines.append(f'#EXTINF:-1 tvg-logo="{ch.get("logoUrl","")}",{ch["name"]}')
            lines.append(f"http://127.0.0.1:9666/sledovanitv/{ch['id']}.m3u8")

        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True

    except Exception as e:
        logger.error(f"Playlist error {e}")
        return False


# -----------------------
# STREAM (FIXED – FAST)
# -----------------------
def get_stream(channel_id):
    FALLBACK = "http://sledovanitv.sk/download/noAccess-cs.m3u8"

    try:
        sessid = get_session()
        if not sessid:
            return FALLBACK

        quality = get_best_quality(sessid)
        channels = get_channels(sessid, quality)

        for ch in channels:
            if ch["id"] == channel_id:
                return ch.get("url", FALLBACK)

        return FALLBACK

    except Exception as e:
        logger.error(f"Stream error {channel_id}: {e}")
        return FALLBACK