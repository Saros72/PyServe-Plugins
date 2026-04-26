import sqlite3, os, requests, json


DB_PATH = os.path.join(os.path.dirname(__file__), "animezone.db")


def get_subtitles_by_id(episode_id):
    BASE_URL = "https://svetserialu.io"
    if not episode_id:
        return []

    headers = {"Referer": BASE_URL}
    subtitles_list = []

    try:
        r = requests.get(
            f"{BASE_URL}/jsonsubs/4/{episode_id}",
            headers=headers,
            timeout=(3, 8),
        )

        if r.status_code == 200:
            for s in r.json():
                label = s.get("label", "sub")
                subtitles_list.append(
                    {
                        "id": f"{episode_id}-{label}",
                        "title": label,
                        "language": label,
                        "url": s.get("file"),
                    }
                )
    except:
        pass

    return subtitles_list



def get_stream(tmdb_id, season, episode):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 🔹 vezmi epizodu
    cursor.execute("""
        SELECT iframe, subtitle_id, lang
        FROM episodes
        WHERE tmdb_id=? AND season=? AND episode=?
    """, (tmdb_id, season, episode))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return []

    # 🔹 vezmi název seriálu
    cursor.execute("""
        SELECT title
        FROM series
        WHERE tmdb_id=?
    """, (tmdb_id,))

    title_row = cursor.fetchone()
    conn.close()

    base_title = title_row[0] if title_row else "Unknown"

    # 🔹 formát S01E01
    ep_title = f"{base_title} S{int(season):02d}E{int(episode):02d}"

    lng = [row[2]]

    return [
        {
            "id": f"https://f16px.com/api/videos/{row[0]}/embed/playback",
            "title": ep_title,
            "hash": row[1],
            "type": "m3u8",
            "audioLanguages": lng
        }
    ]

print(get_stream("300054", 1, 1))