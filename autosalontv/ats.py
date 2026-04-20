import requests, os, re, json, logging
from bs4 import BeautifulSoup

logger = logging.getLogger("autosalontv")

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; 2109119DG Build/UKQ1.231108.001)",
    "referer": "https://www.autosalon.tv/",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip"
}


# ----------------------------------------------------
# GET URL
# ----------------------------------------------------
def get_url(year, id):
    lst = []
    base = f"https://autosalon.tv/epizody/{year}/{id}"

    try:
        html = requests.get(base, headers=headers, timeout=10).text

        sid_match = re.search(r'sid=(.*?)"', html)
        if not sid_match:
            logger.error(f"get_url: sid not found for URL {base}")
            return lst

        sid = sid_match.group(1)

        html = requests.get(f"https://video.onnetwork.tv/embed.php?sid={sid}",
                            headers=headers, timeout=10).text

        ver_match = re.search(r'version":"(.*?)"', html)
        mid_match = re.search(r'mid":"(.*?)"', html)

        if not ver_match or not mid_match:
            logger.error(f"get_url: version or mid missing for sid={sid}")
            return lst

        ver = ver_match.group(1)
        mid = mid_match.group(1)

        html = requests.get(f"https://video.onnetwork.tv/frame{ver}.php?mid={mid}",
                            headers=headers, timeout=10).text

        urls_match = re.search(r'playerVideos = (.*?);', html, re.DOTALL)
        if not urls_match:
            logger.error(f"get_url: playerVideos not found for mid={mid}")
            return lst

        data = json.loads(urls_match.group(1))
        url = data[0].get("url")

        if not url:
            logger.error(f"get_url: No URL inside JSON for mid={mid}")
            return lst

        stream = url.replace("\\", "")
        lst.append({"url": stream})

    except Exception as e:
        logger.error(f"get_url ERROR {year}/{id}: {e}")

    return lst


# ----------------------------------------------------
# GET DETAIL
# ----------------------------------------------------
def get_detail(year, ep):
    items = {}
    url = f"https://autosalon.tv/epizody/{year}/{ep}"

    try:
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        title = None
        if soup.title:
            raw = soup.title.get_text(strip=True)
            title = raw.split(",")[0].strip()

        description = None
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            txt = desc_tag["content"]
            description = txt.split(":", 1)[1].strip() if ":" in txt else txt

        image = None
        img_tag = soup.find("meta", property="og:image")
        if img_tag:
            image = img_tag.get("content")

        rating_match = re.search(r"\((\d+)%\)", html)
        rating = rating_match.group(1) if rating_match else None

        items = {
            "id": f"{year}/{ep}",
            "name": title,
            "description": description,
            "backdrop": (image or "").replace("small", "original").replace("medium", "original").replace("large", "original"),
            "poster": "https://ant-6482.rostiapp.cz/streamlet/autosalontv.png",
            "release_date": year,
            "runtime": "50",
            "rating": rating,
            "genres": ["Publicistický", "Sportovní"]
        }

    except Exception as e:
        logger.error(f"get_detail ERROR {year}/{ep}: {e}")

    return items


# ----------------------------------------------------
# GET CATEGORY
# ----------------------------------------------------
def get_category(year):
    link = f"https://autosalon.tv/epizody/{year}"
    lst = []

    try:
        html = requests.get(link, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        items = soup.find_all("div", {"class": "container-fluid cards-container cards-container-episodes"}, True)
        if not items:
            return lst

        for item in items:
            titles = item.find_all('div', {'class': 'title'})
            links = item.find_all('a')
            posters = item.find_all('img')

            for i in range(min(len(titles), len(links), len(posters))):
                try:
                    name = titles[i].get_text(strip=True)[-10:]
                    href = links[i].get("href", "")
                    poster = posters[i].get("src", "").replace("small", "large").replace("medium", "large")

                    cleaned = "/".join(href.split("/")[2:])

                    lst.append({
                        "id": cleaned,
                        "name": name,
                        "poster": poster
                    })

                except Exception as inner:
                    logger.error(f"get_category ITEM ERROR {year}: {inner}")

    except Exception as e:
        logger.error(f"get_category ERROR year={year}: {e}")

    return lst