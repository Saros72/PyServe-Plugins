import sys
import os

sys.path.append(os.path.dirname(__file__))

import ats
import json
import logging
from bottle import response

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "autosalontv_error.log")

logger = logging.getLogger("autosalontv")
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

    @app.route("/autosalontv/url/<id>")
    def autosalontv_url_invalid(id):
        return safe_json([])

    @app.route("/autosalontv/url/<year>/<id>")
    def autosalontv_url(year, id):
        try:
            return safe_json(ats.get_url(year, id))
        except Exception as e:
            logger.error(f"URL ERROR {year}/{id}: {e}")
            return safe_json({})

    @app.route("/autosalontv/detail/<year>/<ep>")
    def autosalon_detail(year, ep):
        try:
            return safe_json(ats.get_detail(year, ep))
        except Exception as e:
            logger.error(f"DETAIL ERROR {year}/{ep}: {e}")
            return safe_json([])

    @app.route("/autosalontv/<year>")
    def autosalontv(year):
        try:
            return safe_json(ats.get_category(year))
        except Exception as e:
            logger.error(f"CATEGORY ERROR {year}: {e}")
            return safe_json({})