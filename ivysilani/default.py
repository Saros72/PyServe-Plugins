from bottle import response, redirect
import time, json, requests


# -----------------------
# FALLBACK
# -----------------------
FALLBACK_URL = "http://sledovanietv.sk/download/noAccess-cs.m3u8"


# -----------------------
# STREAMS (TV)
# -----------------------
STREAMS = {
    "1": {"title": "ČT1", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ct1.png"},
    "2": {"title": "ČT2", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ct2.png"},
    "24": {"title": "ČT24", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ct24.png"},
    "4": {"title": "ČT Sport", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ctsport.png"},
    "5": {"title": "ČT :D", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ctdecko.png"},
    "6": {"title": "ČT art", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ctart.png"},
    "28": {"title": "ČT Sport Plus 1", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ctsport.png"},
    "29": {"title": "ČT Sport Plus 2", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ctsport.png"},
    "31": {"title": "ČT Sport Plus 3", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ctsport.png"},
    "32": {"title": "ČT Sport Plus 4", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ctsport.png"},
    "27": {"title": "ČT Sport Plus 5", "logo": "https://raw.githubusercontent.com/Saros72/PyServe-Plugins/refs/heads/main/ivysilani/logos/ctsport.png"}
}


# -----------------------
# STREAM RESOLVER
# -----------------------
def get_stream(id):
    try:
        clean_id = id.split(".")[0]

        headers = {
            "User-Agent": "okhttp/4.12.0",
            "Accept-Encoding": "gzip"
        }

        url = (
            "https://api.ceskatelevize.cz/video/v1/playlist-live/v1/stream-data/"
            f"channel/CH_{clean_id}?canPlayDrm=false&streamType=hls"
            "&quality=1080p&maxQualityCount=5"
            "&client=iVysilaniAppAndroid&clientVersion=3.2.12"
        )

        req = requests.get(url, headers=headers, timeout=5).json()
        return req["streamUrls"]["main"]

    except Exception:
        return FALLBACK_URL


# -----------------------
# REGISTER
# -----------------------
def register(app):

    @app.route("/ivysilani")
    def page():

        first = list(STREAMS.keys())[0]

        items_html = ""

        for k, v in STREAMS.items():
            items_html += f"""
            <div class="item" onclick="play('{k}')">
                <img class="thumb" src="{v['logo']}"/>
                <div class="info">
                    <div class="title">{v['title']}</div>
                    <div class="meta">iVysílání • LIVE</div>
                    <div class="btn">▶ Play</div>
                </div>
            </div>
            """

        return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">

<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>

<style>
body {{
    margin:0;
    background:#0b0f1a;
    color:#fff;
    font-family:Arial;
    height:100dvh;
    display:flex;
    flex-direction:column;
}}

html, body {{
    overscroll-behavior: none;
}}

/* HEADER */
.header {{
    background:#1565C0;
    padding:10px 14px;
    font-size:16px;
    font-weight:bold;
    display:flex;
    justify-content:space-between;
    align-items:center;
    flex-shrink:0;
}}

/* CLEAN SELECT */
.quality {{
    background:transparent;
    border:none;
    color:#E3F2FD;
    font-size:13px;
    font-weight:500;
    outline:none;
    cursor:pointer;
}}

/* PLAYER */
.player {{
    flex-shrink:0;
    background:black;
}}

video {{
    width:100%;
    height:200px;
    background:black;
    display:block;
}}

/* LIST */
.list {{
    flex:1;
    overflow-y:auto;
    padding:12px;
}}

.item {{
    display:flex;
    background:#111827;
    margin-bottom:10px;
    border-radius:12px;
    overflow:hidden;
}}

.thumb {{
    width:120px;
    height:80px;
    object-fit:cover;
}}

.info {{
    padding:10px;
    flex:1;
}}

.title {{
    font-weight:bold;
}}

.meta {{
    font-size:12px;
    color:#aaa;
    margin-top:4px;
}}

.btn {{
    margin-top:6px;
    background:#1e88e5;
    padding:6px;
    border-radius:6px;
    width:80px;
    text-align:center;
}}

/* FOOTER */
.footer {{
    flex-shrink:0;
    padding:12px;
    background:#0b0f1a;
}}

.api {{
    display:block;
    background:#1f2937;
    padding:12px;
    border-radius:10px;
    text-align:center;
    color:white;
    text-decoration:none;
    font-weight:bold;
}}
</style>
</head>

<body>

<div class="header">
    <div>iVysílání</div>

    <select id="quality" class="quality" onchange="setQuality(this.value)">
        <option value="-1">Auto</option>
    </select>
</div>

<div class="player">
    <video id="video" controls playsinline></video>
</div>

<div class="list">
    {items_html}
</div>

<div class="footer">
    <a class="api" href="/ivysilani/api">📡 API</a>
</div>

<script>
let hls;
const video = document.getElementById("video");
const qualitySelect = document.getElementById("quality");

window.onload = function() {{
    play('{first}');
}};

function play(id) {{
    fetch("/ivysilani/stream/" + id)
        .then(r => r.text())
        .then(url => {{

            if (hls) {{
                hls.destroy();
                hls = null;
            }}

            if (Hls.isSupported()) {{
                hls = new Hls();
                hls.loadSource(url);
                hls.attachMedia(video);

                hls.on(Hls.Events.MANIFEST_PARSED, function (event, data) {{

                    qualitySelect.innerHTML = '<option value="-1">Auto</option>';

                    data.levels.forEach((level, i) => {{
                        const opt = document.createElement("option");
                        opt.value = i;
                        opt.text = level.height ? level.height + "p" : Math.round(level.bitrate/1000) + " kbps";
                        qualitySelect.appendChild(opt);
                    }});

                    video.play().catch(()=>{{}});
                }});

            }} else {{
                video.src = url;
                video.load();
                video.play().catch(()=>{{}});
            }}
        }});
}}

function setQuality(level) {{
    if (!hls) return;

    if (level == -1) {{
        hls.currentLevel = -1;
    }} else {{
        hls.currentLevel = parseInt(level);
    }}
}}
</script>

</body>
</html>
"""

    @app.route("/ivysilani/api")
    def api():
        response.content_type = "application/json; charset=utf-8"

        data = {
            "status": "ok",
            "time": time.time(),
            "streams": {}
        }

        for k, v in STREAMS.items():
            data["streams"][k] = {
                "title": v["title"],
                "logo": v["logo"],
                "url": f"http://127.0.0.1:9666/ivysilani/play/{k}.m3u8"
            }

        return json.dumps(data, indent=4, ensure_ascii=False)

    @app.route("/ivysilani/stream/<id>")
    def stream(id):
        return get_stream(id)

    @app.route("/ivysilani/play/<id>")
    def play(id):
        return redirect(get_stream(id))