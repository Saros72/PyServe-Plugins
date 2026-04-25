# -*- coding: utf-8 -*-
import sys
import os
import json
import time 
import uuid
import gzip
import ssl
import requests
from bottle import redirect, response
from websocket import create_connection
from urllib.request import urlopen, Request
from urllib.error import HTTPError


PATH = os.path.join(os.path.dirname(__file__), "oneplay_session.txt")


SETTINGS = {
    "username":"",
    "password":"",
    "deviceid":"",
    "profile":"",
    "pin":"",
    "profile_pin":""
}

def get_config():
    return SETTINGS


config = get_config()


def call_api(url, data, token = None):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept-Encoding': 'gzip',
        'Accept': '*/*',
        'Content-type': 'application/json;charset=UTF-8'
    }

    if token is not None:
        headers['Authorization'] = 'Bearer ' + token

    try:
        requestId = str(uuid.uuid4())
        clientId = str(uuid.uuid4())

#        ws = create_connection('wss://ws.cms.jyxo.cz/websocket/' + clientId)
        ws = create_connection('wss://ws.cms.jyxo.cz/websocket/' + clientId, sslopt={"cert_reqs": ssl.CERT_NONE})
        ws_data = json.loads(ws.recv())

        post = {
            "deviceInfo":{
                "deviceType":"web",
                "appVersion":"1.0.10",
                "deviceManufacturer":"Unknown",
                "deviceOs":"Linux"
            },
            "capabilities":{"async":"websockets"},
            "context":{
                "requestId":requestId,
                "clientId":clientId,
                "sessionId":ws_data['data']['serverId'],
                "serverId":ws_data['data']['serverId']
            }
        }

        if data is not None:
            post = {**data, **post}

        post = json.dumps(post).encode("utf-8")

        request = Request(url=url, data=post, headers=headers)
#        response = urlopen(request, timeout=20)
        ssl_context = ssl._create_unverified_context()

        response = urlopen(request, timeout=20, context=ssl_context)

        if response.getheader("Content-Encoding") == 'gzip':
            gzipFile = gzip.GzipFile(fileobj=response)
            data = gzipFile.read()
        else:
            data = response.read()

        if len(data) > 0:
            data = json.loads(data)

        if 'result' not in data or data['result']['status'] not in ['OkAsync', 'Ok']:
            print('Chyba při volání ' + str(url))
            ws.close()
            return {'err': 'Chyba při volání API'}

        if data['result']['status'] == 'OkAsync':
            response = ws.recv()
            if response:
                data = json.loads(response)
                ws.close()
                if 'data' in data['response']:
                    return data['response']['data']
                return []
            else:
                ws.close()
                return []

        elif data['result']['status'] == 'Ok':
            ws.close()
            if 'data' in data:
                return data['data']
            return []

    except HTTPError as e:
        print('Chyba při volání ' + str(url) + ': ' + e.reason)
        ws.close()
        return {'err': e.reason}


def get_token():
    post = {
        "payload":{
            "command":{
                "schema":"LoginWithCredentialsCommand",
                "email":config['username'],
                "password":config['password']
            }
        }
    }

    data = call_api('https://http.cms.jyxo.cz/api/v1.8/user.login.step', post)

    if 'err' in data or 'step' not in data:
        print('Problém při přihlášení')
        sys.exit()

    token = data['step']['bearerToken']
    return token


def load_session(reset=False):
    if reset:
        token = get_token()
        save_session(token)
        return token

    data = load_json_data()

    if data is not None:
        data = json.loads(data)

        if 'valid_to' in data and 'token' in data:
            token = data['token']
            if int(data['valid_to']) < int(time.time()):
                token = get_token()
                save_session(token)
        else:
            token = get_token()
            save_session(token)
    else:
        token = get_token()
        save_session(token)

    return token


def save_session(token):
    data = json.dumps({
        'token': token,
        'valid_to': int(time.time() + 60*60*4)
    })
    save_json_data(data)


def save_json_data(data):
    try:
        with open(PATH, "w") as f:
            f.write('%s\n' % data)
    except IOError:
        print('Oneplay > Chyba při uložení session')
        sys.exit()


def load_json_data():
    data = None
    try:
        with open(PATH, "r") as f:
            for row in f:
                data = row.strip()
    except IOError as error:
        if error.errno != 2:
            print('Oneplay > Chyba při načtení session')
    return data



config = get_config()


# adult ids
adult = ["180", "181", "182", "183", "184", "185", "186", "187", "188"]


def get_stream(id):
  try:
    id = id.split(".")[0]
    url = None
    token = load_session()
    pin = config["pin"]
    if id in adult:
        post = {"authorization":[{"schema":"PinRequestAuthorization","pin":pin,"type":"parental"}],"payload":{"criteria":{"schema":"ContentCriteria","contentId":"channel." + id},"startMode":"live"},"playbackCapabilities":{"protocols":["dash","hls"],"drm":["widevine","fairplay"],"altTransfer":"Unicast","subtitle":{"formats":["vtt"],"locations":["InstreamTrackLocation","ExternalTrackLocation"]},"liveSpecificCapabilities":{"protocols":["dash","hls"],"drm":["widevine","fairplay"],"altTransfer":"Unicast","multipleAudio":False}}}
    else:
        post = {"payload":{"criteria":{"schema":"ContentCriteria","contentId":"channel." + id},"startMode":"live"},"playbackCapabilities":{"protocols":["dash","hls"],"drm":["widevine","fairplay"],"altTransfer":"Unicast","subtitle":{"formats":["vtt"],"locations":["InstreamTrackLocation","ExternalTrackLocation"]},"liveSpecificCapabilities":{"protocols":["dash","hls"],"drm":["widevine","fairplay"],"altTransfer":"Unicast","multipleAudio":False}}}
    data = call_api(url = 'https://http.cms.jyxo.cz/api/v1.8/content.play', data = post, token = token)
    url = 'http://sledovanietv.sk/download/noAccess-cs.m3u8'
    for asset in data['media']['stream']['assets']:
        if asset['protocol'] == 'hls':
            if 'drm' not in asset:
                if 'clear' not in asset['src']:
                    url = asset['src']
                elif url == 'http://sledovanietv.sk/download/noAccess-cs.m3u8':
                    url = asset['src']
  except:
    url = 'http://sledovanietv.sk/download/noAccess-cs.m3u8'
  return url


def register(app):
    @app.route("/oneplay/<id>")
    def oneplay_route(id):
        stream = get_stream(id)
        return redirect(stream)

