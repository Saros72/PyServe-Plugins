import requests
import re
import html
import logging
import os
from urllib.parse import quote

# ----------------------------------------------------
# LOGOVÁNÍ – chyby do souboru ve stejné složce skriptu
# ----------------------------------------------------
if False:
    LOG_FILE = os.path.join(os.path.dirname(__file__), "eporner_error.log")

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

# ----------------------------------------------------
## KONSTANTY
# ----------------------------------------------------
E_BASE_URL = "https://www.eporner.com"
headers = {"User-Agent": "Mozilla/5.0"}


# ----------------------------------------------------
# Pomocné funkce
# ----------------------------------------------------
def encode_base_n(num, n, table=None):
    FULL_TABLE = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if not table:
        table = FULL_TABLE[:n]

    if n > len(table):
        raise ValueError('base %d exceeds table length %d' % (n, len(table)))

    if num == 0:
        return table[0]

    ret = ''
    while num:
        ret = table[num % n] + ret
        num = num // n
    return ret


def video_id_from_parts(q, id):
    q = (q or "").strip()
    id = (id or "").strip()

    if q.startswith("video-"):
        return q.split("video-", 1)[1] or None

    if q == "hd-porn":
        return id or None

    return None


# ----------------------------------------------------
# ZÍSKÁNÍ URL STREAMŮ
# ----------------------------------------------------
def get_url(q, id, slug=''):
    entry = []
    video_url = f"{E_BASE_URL}/{q}/{id}/{slug}".rstrip('/')

    try:
        r = requests.get(video_url, headers=headers).text

        match = re.compile(
            r"vid = '(.+?)'.+?hash = '(.+?)'",
            re.DOTALL | re.IGNORECASE
        ).findall(r)

        if not match:
            raise Exception("Embed data not found")

        vid, s = match[0]

        # hash výpočet
        hash_val = ''.join(
            encode_base_n(int(s[i:i + 8], 16), 36)
            for i in range(0, 32, 8)
        )

        json_url = (
            f"https://www.eporner.com/xhr/video/{vid}"
            f"?hash={hash_val}&domain=www.eporner.com"
            f"&fallback=false&embed=true&supportedFormats=dash,mp4"
        )

        data = requests.get(json_url, headers=headers).json()

        mp4_sources = data.get("sources", {}).get("mp4", {})

        # zachovat originální pořadí API + odstranit 240p a 360p
        for quality_name, info in mp4_sources.items():
            if any(x in quality_name for x in ["240", "360"]):
                continue
            entry.append({
                "name": quality_name.replace(" HD", "").strip(),
                "type": "mp4",
                "url": info.get("src")
            })

    except Exception as e:
        #logging.error(f"get_url ERROR for {video_url}: {e}")
        entry = []

    return entry


# ----------------------------------------------------
# DETAIL VIDEA
# ----------------------------------------------------
def get_detail(q, id, slug=''):
    entry = {}
    video_id = video_id_from_parts(q, id)

    if not video_id:
        return entry

    try:
        resp = requests.get(
            f"https://www.eporner.com/api/v2/video/id/?id={video_id}&thumbsize=big&format=json",
            headers=headers
        )
        data = resp.json()
    except Exception as e:
        #logging.error(f"get_detail API ERROR for id={video_id}: {e}")
        data = []
    if data == []:
        return entry
    # Release year
    added = data.get("added")
    release_year = added[:4] if isinstance(added, str) and len(added) >= 4 else None

    # Rating
    raw_rate = data.get("rate")
    try:
        rating = float(raw_rate) if raw_rate else None
    except:
        rating = None

    rating_percent = str(round((rating / 5) * 100)) if rating is not None else None

    # Keywords → overview
    keywords = data.get("keywords", "")
    if keywords:
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
        overview = ", ".join(kw_list[:3])
    else:
        overview = ""

    views = int(data.get("views", 0))

    poster = data.get("default_thumb", {}).get("src")
    thumbs = data.get("thumbs") or []
    backdrop = thumbs[0].get("src") if thumbs and isinstance(thumbs[0], dict) else None

    entry = {
        "id": f"{q}/{id}/{slug}" if slug else f"{q}/{id}",
        "title": data.get("title", ""),
        "overview": overview,
        "poster": poster,
        "backdrop": backdrop,
        "rating": rating_percent,
        "runtime": data.get("length_min"),
        "releaseDate": release_year,
        "views": views,
        "genres": ["Adult"]
    }

    return entry


# ----------------------------------------------------
# KATEGORIE
# ----------------------------------------------------
def get_category(cat, id, page):
    items = []
    if id == "{apiKey}":
        id = "Angel Wicky"
    
    url = f"{E_BASE_URL}/{cat}/{quote(id)}/{page}/"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            # Tag neexistuje → není chyba, jen vracíme prázdný seznam
            return items
        response.raise_for_status()  # ostatní chyby vyvolá výjimku
        html_data = response.text
    except requests.RequestException as e:
        #logging.error(f"get_category ERROR URL {url}: {e}")
        return items

    # Rozdělíme na jednotlivá videa
    videos = html_data.split('data-vp=')[1:]

    pattern = re.compile(
        r'href="([^"]+)"[^>]*>\s*<img[^>]*src="([^"]+)"[^>]*alt="([^"]+)"'
        r'.+?class="mbtim"[^>]*>([^<]+)'
        r'.+?class="mbrate"[^>]*>([^<]+)',
        re.DOTALL
    )

    for block in videos:
        match = pattern.search(block)
        if not match:
            continue

        video_url, poster, title, runtime, rating = match.groups()
        video_id = video_url.strip("/")
        title = html.unescape(title)
        rating = rating.replace("%", "").strip()
        poster = poster.replace("_240.jpg", "_360.jpg")

        items.append({
            "id": video_id,
            "title": title,
            "poster": poster,
            "rating": rating,
            "runtime": runtime.strip()
        })

    return items