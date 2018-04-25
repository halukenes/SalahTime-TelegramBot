import json
import requests

URL = "https://maps.googleapis.com/maps/api/place/textsearch/json?query="
API_KEY = "AIzaSyBL7B08P-D0O_nOtyYdO8CB9uMnewAjDDo"


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(placename):
    url = URL + placename + "&key=" + API_KEY
    js = get_json_from_url(url)
    return js
