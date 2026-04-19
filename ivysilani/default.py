import requestss
from bottle import redirect, response


FALLBACK_URL = "http://sledovanietv.sk/download/noAccess-cs.m3u8"


def get_stream(id):
    try:
        clean_id = id.split(".")[0]

        url = (
            "https://api.ceskatelevize.cz/video/v1/playlist-live/v1/stream-data/"
            f"channel/CH_{clean_id}?canPlayDrm=false&streamType=hls&quality=web&maxQualityCount=5"
        )

        req = requests.get(url, timeout=5).json()

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