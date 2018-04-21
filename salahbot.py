import json
import requests
import time
import urllib

from datetime import datetime
from dbhelper import DBHelper
from praytimes import PrayTimes

db = DBHelper()
pt = PrayTimes()
now = datetime.now()

pretext = None
prechoi = 0

TOKEN = "584920327:AAGKd2EDjQyIwyEwLalcMBnlMYZj6xF3K_s"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

praytimekeywordsTR = ['ezan', 'ne', 'zaman', 'kaç dakika kaldı', 'okunmasına', 'ezana', 'ezanın', 'kaçta']


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates"
    if offset:
        url += "?offset={}".format(offset)
    js = get_json_from_url(url)
    print(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def handle_updates(updates):
    global pretext
    global prechoi
    for update in updates["result"]:
        try:
            if "location" in update["message"]:
                print(update["message"]["location"]["latitude"])
                if not db.get_user_lat(update["message"]["from"]["id"]):
                    db.add_user(update["message"]["from"]["id"],
                                update["message"]["location"]["latitude"],
                                update["message"]["location"]["longitude"],
                                "tur")
                else:
                    db.update_user_location(update["message"]["from"]["id"],
                                update["message"]["location"]["latitude"],
                                update["message"]["location"]["longitude"])
            else:
                text = update["message"]["text"]
                chat = update["message"]["chat"]["id"]
                if text == "/start" or text == "merhaba":
                    textkeyboard = ["/ezan", "/sure", "/ayarlar"]
                    keyboard = build_keyboard(textkeyboard)
                    send_message(
                        "Ezan vakti botuna hoşgeldin. Bana ezanın ne zaman okunacağı sorabilir veya sana göstermemi "
                        "istediğin bir ayet veya sure gösterebilirim. Komut olarak da /ezan yazarak ezan vaktine kaç "
                        "dakika kaldığını, /sure yazarak sureleri ve /ayarlar yazarak bot tercihlerini "
                        "değiştirebilirsin.", chat, keyboard)
                elif text == "ayarlar" or text == "/ayarlar":
                    textkeyboard = ["dil", "konum", "bildirim"]
                    keyboard = build_keyboard(textkeyboard)
                    send_message(
                        "Tercihlerini değiştirmek için aşağıdakilerden birisini seçebilirsin veya bir dahaki sefere "
                        "direk bunları bana yazabilirsin.", chat, keyboard)
                elif text == "konum" or text == "/konum":
                    keyboard = build_keyboard_for_location()
                    send_message(
                        "Aşağıdaki tuşa basarak konumunuzu gönderebilirsiniz.", chat, keyboard)
                elif len(set(text.split(" ")).intersection(set(praytimekeywordsTR))) > 1 or text == 'ezan' or text == '/ezan' or prechoi == 1:
                    if not db.get_user_lat(update["message"]["from"]["id"]) and prechoi != 1:
                        send_message("Ezan için istediğin şehirin ismini yazabilirsin veya 'konumum' yazarak konumunu gönderebilirsin.", chat)
                        prechoi = 1;
                    elif prechoi == 1:
                        prechoi = 0;
                        userLON = db.get_city_lng(text)[0]
                        userLAT = db.get_city_lat(text)[0]
                        prayTime = \
                            get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), +3)[
                                'pray_time']
                        prayTimeName = \
                            get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), +3)[
                                'closest_time']
                        prayTimeRema = \
                            get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), +3)[
                                'remaining_time']
                        send_message(
                            text + " için " + prayTimeName + " ezanının vakti " + prayTime + ", " + prayTimeName + " ezanına " + prayTimeRema[
                                                                                                                                 :1] + " saat, " + prayTimeRema[
                                                                                                                                                   2:4] + " dakika kaldı.",
                            chat)
                    else:
                        userLON = db.get_user_long(update["message"]["from"]["id"])[0]
                        userLAT = db.get_user_lat(update["message"]["from"]["id"])[0]
                        prayTime = \
                        get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), +3)[
                            'pray_time']
                        prayTimeName = \
                        get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), +3)[
                            'closest_time']
                        prayTimeRema = \
                        get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), +3)[
                            'remaining_time']
                        send_message(
                            prayTimeName + " ezanının vakti " + prayTime + ", " + prayTimeName + " ezanına " + prayTimeRema[
                                                                                                               :1] + " saat, " + prayTimeRema[
                                                                                                                                 2:4] + " dakika kaldı.",
                            chat)
                else:
                    send_message("Ne demek istediğini anlayamadım, tekrar denemek ister misin?", chat)
                pretext = text
        except KeyError:
            pass


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def build_keyboard_for_location():
    getLocationJ = {"text": "Konumumu gönder", "request_location": True}
    keyboard = [[getLocationJ]]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
        print(url)
    get_url(url)
    print(url)


def get_closest_praytime_with_time(date, coordinates, timeZone):
    allpraytimes = pt.getTimes(date, coordinates, timeZone)
    praytimearray = ['imsak', 'fajr', 'sunrise', 'dhuhr', 'asr', 'sunset', 'maghrib', 'isha', 'midnight']
    for temptimename in praytimearray:
        closesttime = temptimename
        if now.strftime('%H:%M') < allpraytimes[temptimename]:
            break
    date_format = "%H:%M"
    timenow = datetime.strptime(now.strftime('%H:%M'), date_format)
    timepray = datetime.strptime(allpraytimes[closesttime], date_format)
    praytime = allpraytimes[closesttime]
    tremain = str((timepray - timenow))
    if (closesttime == "imsak"):
        closesttime = "İmsak"
    elif (closesttime == "fajr"):
        closesttime = "Sabah"
    elif (closesttime == "sunrise"):
        closesttime = "Gündoğumu"
    elif (closesttime == "dhuhr"):
        closesttime = "Öğle"
    elif (closesttime == "asr"):
        closesttime = "İkindi"
    elif (closesttime == "sunset"):
        closesttime = "Günbatımı"
    elif (closesttime == "maghrib"):
        closesttime = "Akşam"
    elif (closesttime == "isha"):
        closesttime = "Yatsı"
    elif (closesttime == "midnight"):
        closesttime = "Gece yarısı"
    return {'closest_time': closesttime, 'remaining_time': tremain, 'pray_time': praytime}


def main():
    db.setup()
    last_update_id = None
    print(str(db.get_city_lat("Ankara")[0]) + " " + str(db.get_city_lng("Ankara")[0]))
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
