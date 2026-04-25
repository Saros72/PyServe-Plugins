import requests, json, html, re
from bs4 import BeautifulSoup


headers = {
  'User-Agent': "Mozilla/5.0 (Linux; Android 16; Mi A3 Build/BP2A.250805.005) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.109 Mobile Safari/537.36"
}


def get_video(videoHash):
    payload = {
        'videoHash': videoHash
    }
    r = requests.post("https://www.freepornsex.net/tools/api/hls.php", data=payload, headers=headers)
    if r.status_code == 200:
        return [{
           "url": r.text.strip()
        }]

    return []


def get_detail(video_id):
    result = {}
    r = requests.get(f"https://www.freepornsex.net/wp-json/wp/v2/posts/{video_id}", headers=headers)
    if r.status_code == 200:
        d =  r.json()
        title = html.unescape(d.get("title", {}).get("rendered", ""))
        content = d.get("content", {}).get("rendered", "")
        soup = BeautifulSoup(content, "html.parser")
        p = soup.find("p")
        description = p.get_text(strip=True) if p else None
        match1 = re.search(r'videoHash\s*=\s*"([^"]+)"', content)
        id = match1.group(1) if match1 else None
        match2 = re.search(r'image:\s*"([^"]+)"', content)
        backdrop = match2.group(1).replace("\\/", "/") if match2 else None
        poster = None
        if backdrop:
            poster = backdrop.replace(".jpg", "-768x432.jpg")
            backdrop = backdrop.replace(".jpg", "-768x432.jpg")
        return {
            "id": id,
            "title": title,
            "description": description,
            "backdrop": backdrop,
            "poster": poster,
            "genres": ["Adult"]
        }
    return {}


def get_category(cat, page):
    result = []
    r = requests.get(f"https://www.freepornsex.net/wp-json/wp/v2/posts?categories={cat}&per_page=20&page={page}", headers=headers)
    if r.status_code == 200:
        for d in r.json():
            id = d.get("id")
            title = html.unescape(d.get("title", {}).get("rendered", ""))
            content = d.get("content", {}).get("rendered", "")
            match = re.search(r'image:\s*"([^"]+)"', content)
            if match:
                poster = match.group(1).replace("\\/", "/").replace(".jpg", "-768x432.jpg")
            else:
                poster = None
            result.append({
                "id": id,
                "title": title,
                "poster": poster
            })
    return result