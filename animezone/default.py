import sys
import os

sys.path.append(os.path.dirname(__file__))

import az
import json
import F16Px
import logging
from bottle import response, request


# LOGGING
# ----------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "animezone_error.log")

logger = logging.getLogger("animezone")
logger.setLevel(logging.ERROR)

if not logger.handlers:
    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ----------------------------------------------------
# JSON RESPONSE
# ----------------------------------------------------
def safe_json(data):
    response.content_type = "application/json; charset=utf-8"
    return json.dumps(data, ensure_ascii=False, indent=2)


# ----------------------------------------------------
# ROUTES
# ----------------------------------------------------
def register(app):
    @app.route('/animezone', method=['GET', 'POST'])
    def animezone():
        try:
            if request.method != 'POST':
                return safe_json([])

            data = request.json or {}

            playback = data.get('playback')
            hash_value = data.get('hash')

            if playback:
                stream = F16Px.filemoon(playback)
                subtitles = None
                if hash_value:
                    subtitles = az.get_subtitles_by_id(hash_value)

                return safe_json({
                    "link": stream,
                    "subtitles": subtitles
                })
        except Exception as e:
            logger.error(f"URL ERROR: {e}")
            return safe_json({})


    @app.route("/animezone/<id>/<se>/<ep>")
    def anime_zone(id, se, ep):
        try:
            result = az.get_stream(id, int(se), int(ep))
            return safe_json(result)
        except Exception as e:
            logger.error(e)
            return safe_json({})