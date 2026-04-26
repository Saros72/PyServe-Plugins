import sys
import os

sys.path.append(os.path.dirname(__file__))

import ep
import json
import logging
from bottle import response, request

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "eporner_error.log")

logger = logging.getLogger("eporner")
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
    @app.route("/eporner/url/<id>")
    def eporner_url_invalid(id):
        return safe_json([])


    @app.route("/eporner/url/<q>/<id>/<slug:path>")
    @app.route("/eporner/url/<q>/<id>")
    def eporner_url(q, id, slug=''):
        try:
            return safe_json(ep.get_url(q, id, slug))
        except Exception as e:
            logger.error(f"ERROR: {e}")
            return safe_json([])


    @app.route('/eporner/detail/<q>/<id>/<slug:path>')
    @app.route("/eporner/detail/<q>/<id>")
    def eporner_detail(q, id, slug=''):
        try:
            return safe_json(ep.get_detail(q, id, slug))
        except Exception as e:
            logger.error(f"ERROR: {e}")
            return safe_json({})


    @app.route("/eporner/<cat>/<id>/<page>")
    def eporner_category(cat, id, page):
        try:
            if cat == "tag" and not id:
                id = "Angel Wicky"
            return safe_json(ep.get_category(cat, id, page))
        except Exception as e:
            logger.error(f"ERROR: {e}")
            return safe_json([])


    @app.route("/eporner/tag")
    def eporner_category_tag():
        try:
            query = request.query.get("query") or "Angel Wicky"
            page = request.query.get("page") or "1"
            return safe_json(ep.get_category("tag", query, page))
        except Exception as e:
            logger.error(f"ERROR: {e}")
            return safe_json([])