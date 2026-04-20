import requests
from bottle import redirect


FALLBACK_URL = "http://sledovanietv.sk/download/noAccess-cs.m3u8"


def get_stream(id):
    try:
        clean_id = id.split(".")[0]
        manifest = id.split(".")[1]
        if manifest == "m3u8":
            streamType = "hls"
        else:
            streamType = "dash"

        headers = {
           'User-Agent': "okhttp/4.12.0",
           'Accept-Encoding': "gzip"
        }

        url = (
            "https://api.ceskatelevize.cz/video/v1/playlist-live/v1/stream-data/"
            f"channel/CH_{clean_id}?canPlayDrm=false&streamType={streamType}&quality=1080p&maxQualityCount=1&client=iVysilaniAppAndroid&clientVersion=3.2.12"
        )

        req = requests.get(url, headers=headers, timeout=5).json()

        return req["streamUrls"]["main"]

    except requests.RequestException as e:
        print("Network error:", e)
        return FALLBACK_URL

    except (KeyError, ValueError, TypeError) as e:
        print("Parsing error:", e)
        return FALLBACK_URL


def register(app):
    @app.route("/ivysilani/<id>")
    def ivysilani_route(id):
        stream = get_stream(id)
        return redirect(stream)