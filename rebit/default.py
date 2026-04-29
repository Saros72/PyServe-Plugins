import sys
import os

sys.path.append(os.path.dirname(__file__))

import rbt
import json
import logging
from bottle import response, error, redirect

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "rebit.log")

logger = logging.getLogger("rebit")
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
    @app.route("/rebit")
    def rebit_playlist():
        p = rbt.create_playlist()
        if p:
            return "<h1 style='text-align:center;margin-top:20px;'>Playlist created ✅</h1>"
        else:
            return "<h1 style='text-align:center;margin-top:20px;'>Playlist not created ❌</h1>"

    @app.route("/rebit/<id>.m3u8")
    def rebit_stream(id):
        stream = rbt.get_stream(id)
        return redirect(stream)