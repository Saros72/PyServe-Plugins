import sys
import os

sys.path.append(os.path.dirname(__file__))

import fp
import json
import logging
from bottle import response, request

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "freesexporn_error.log")

logger = logging.getLogger("freesexporn")
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
    @app.route("/freesexporn")
    def free_sex_porn():
        try:
            id = request.query.get("id")
            cat = request.query.get("cat")
            hash = request.query.get("hash")
            page = request.query.get("page") or "1"

            if id:
                return safe_json(fp.get_detail(id))

            if cat:
                return safe_json(fp.get_category(cat, page))

            if hash:
                return safe_json(fp.get_video(hash))

            return safe_json([])

        except Exception as e:
            logger.error(f"ERROR: {e}")
            return safe_json([])