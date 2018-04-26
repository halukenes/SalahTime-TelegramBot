import json
import requests
import time

class GooglePlaceParser:

    def __init__(self):
        self.URL = "https://maps.googleapis.com/maps/api/place/textsearch/json?query="
        self.API_KEY = "AIzaSyBL7B08P-D0O_nOtyYdO8CB9uMnewAjDDo"
        self.TIMEZONE_URL = "https://maps.googleapis.com/maps/api/timezone/json?location="
        self.TIMEZONE_API_KEY = "AIzaSyAKkgVXPNKrutz80f6B6x82Wcv5qNOmja4"

    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_json(self, place):
        url = self.URL + place + "&key=" + self.API_KEY
        js = self.get_json_from_url(url)
        return js

    def get_json_timezone(self, lat, lng):
        ts = time.time()- 5400
        url = self.TIMEZONE_URL + str(lat) + "," + str(lng) + "&timestamp=" + str(ts)[:10] + "&key=" + self.TIMEZONE_API_KEY
        js = self.get_json_from_url(url)
        return js

    def get_gmt_location(self, lat, lng):
        timezoneplace = self.get_json_timezone(lat, lng)
        place_gmt = (int(timezoneplace["rawOffset"]) + int(timezoneplace["dstOffset"])) / 3600
        return int(place_gmt)

    def get_location_ofcity(self, placename):
        placejson = self.get_json(placename)
        if not placejson["status"] == "ZERO_RESULTS":
            lat_place = placejson["results"][0]["geometry"]["location"]["lat"]
            print(lat_place)
            lng_place = placejson["results"][0]["geometry"]["location"]["lng"]
            print(lng_place)
            jsonresult = placejson["status"]
            timezoneplace = self.get_json_timezone(lat_place, lng_place)
            place_gmt = (int(timezoneplace["rawOffset"]) + int(timezoneplace["dstOffset"]))/3600
            print(place_gmt)
        else:
            lat_place = None
            lng_place = None
            place_gmt = 0
            jsonresult = placejson["status"]
        return lat_place, lng_place, jsonresult, int(place_gmt)
