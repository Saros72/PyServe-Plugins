import sys
import os

sys.path.append(os.path.dirname(__file__))

import stv
import json
import logging
from bottle import response, error, redirect

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "sledovanitv.log")

logger = logging.getLogger("sledovanitv")
logger.setLevel(logging.ERROR)

if not logger.handlers:
    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ----------------------------------------------------
# ROUTES
# ----------------------------------------------------
def register(app):
    @app.route("/sledovanitv")
    def sledovanitv_playlist():
        p = stv.create_playlist()
        if p:
            return "<h1 style='text-align:center;margin-top:20px;'>Playlist created ✅</h1>"
        else:
            return "<h1 style='text-align:center;margin-top:20px;'>Playlist not created ❌</h1>"

    @app.route("/sledovanitv/<id>.m3u8")
    def sledovanitv_stream(id):
        stream = stv.get_stream(id)
        return redirect(stream)