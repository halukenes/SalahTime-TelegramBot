import json
import requests
import time
import urllib

from datetime import datetime
from dbhelper import DBHelper
from praytimes import PrayTimes
from googleplacesparser import GooglePlaceParser
from surahtmlparser import HTMLParser

db = DBHelper()
gpp = GooglePlaceParser()
pt = PrayTimes()
now = datetime.now()

pretext = None
prechoi = 0
predelloc = 0

TOKEN = "584920327:AAGKd2EDjQyIwyEwLalcMBnlMYZj6xF3K_s"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

praytimekeywordsTR = ['ezan', 'ne', 'zaman', 'kaç dakika kaldı', 'okunmasına', 'ezana', 'ezanın', 'kaçta']
allpraytimekeywordsTR = ['ezanları', 'tüm', 'bugünki', 'vakitlerini', 'vakitleri', 'saatleri']


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
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def handle_updates(updates):
    global pretext
    global prechoi
    global predelloc
    for update in updates["result"]:
        try:
            chat = update["message"]["chat"]["id"]
            if "location" in update["message"]:
                user_lat = update["message"]["location"]["latitude"]
                user_lng = update["message"]["location"]["longitude"]
                if not db.get_user_lat(chat):
                    db.add_user(chat, user_lat, user_lng, "tur", gpp.get_gmt_location(user_lat, user_lng))
                else:
                    db.update_user_location(chat, user_lat, user_lng)
                prechoi = 0
                predelloc = 0
            else:
                text = update["message"]["text"]
                if text == "/start" or text.lower() == "merhaba" or text == "/yardim":
                    textkeyboard = ["/ezan", "/sure", "/ayarlar"]
                    keyboard = build_keyboard(textkeyboard)
                    send_message(
                        "Ezan vakti botuna hoşgeldin. Bana ezanın ne zaman okunacağı sorabilir veya sana göstermemi "
                        "istediğin bir ayet veya sure gösterebilirim. Komut olarak da /ezan yazarak ezan vaktine kaç "
                        "dakika kaldığını, /sure yazarak sureleri ve /ayarlar yazarak bot tercihlerini "
                        "değiştirebilirsin.", chat, keyboard)
                    prechoi = 0
                    predelloc = 0
                elif text.lower() == "ayarlar" or text == "/ayarlar":
                    textkeyboard = ["/dil", "/konum", "/bildirim"]
                    keyboard = build_keyboard(textkeyboard)
                    send_message(
                        "Tercihlerini değiştirmek için aşağıdakilerden birisini seçebilirsin veya bir dahaki sefere "
                        "direk bunları bana yazabilirsin.", chat, keyboard)
                    prechoi = 0
                    predelloc = 0
                elif text.lower() == "konumum":
                    keyboard = build_keyboard_for_location()
                    send_message(
                        "Aşağıdaki tuşa basarak konumunuzu gönderebilirsiniz.", chat, keyboard)
                    prechoi = 0
                    predelloc = 0
                elif text == "/konum":
                    if not db.get_user_lat(chat):
                        send_message(
                            "Önceden belirlediğin bir konum yok, benden ezan vakitlerini istediğin zaman konumunu da belirleyebilirsin.",
                            chat)
                        predelloc = 0
                    else:
                        if db.get_user_cityName(chat)[0] == None:
                            send_message(
                                "Konum tercihlerini önceden belirlemişsin, eğer değiştirmek veya silmek istiyorsan 'sil' yazabilirsin.",
                                chat)
                        else:
                            send_message("Konum tercihlerini önceden belirlemişsin: '" + str(
                                db.get_user_cityName(chat)[0]) + "', eğer bunu silmek istiyorsan 'sil' yazabilirsin.",
                                         chat)

                    predelloc = 1
                    prechoi = 0
                elif predelloc == 2:
                    if text.lower() == "evet":
                        db.delete_user(chat)
                        send_message(
                            "Konum tercihini artık bilmiyorum, benden ezan vakitlerini istediğin zaman konumunu da tekrardan belirleyebilirsin.",
                            chat)
                        predelloc = 0
                    else:
                        send_message(
                            "İsteğin üzerine konum tercihlerini değiştirmedim.",
                            chat)
                        predelloc = 0
                    prechoi = 0
                elif predelloc == 1:
                    if text.lower() == "sil":
                        send_message(
                            "Konum tercihini silmek istiyorsan 'evet' yaz.",
                            chat)
                        predelloc = 2
                    else:
                        send_message(
                            "Konum tercihlerinden çıktım.",
                            chat)
                        predelloc = 0
                    prechoi = 0
                elif len(set(text.split(" ")).intersection(
                        set(praytimekeywordsTR))) > 1 or text == 'ezan' or text.lower() == '/ezan' or prechoi == 10:
                    if not db.get_user_lat(chat) and prechoi != 10:
                        send_message(
                            "Konum tercihlerini bilmiyorum. O yüzden ezan vakti için istediğin şehirin ismini yazabilirsin veya 'konumum' yazarak konumunu gönderebilirsin.",
                            chat)
                        prechoi = 10
                        predelloc = 0
                    elif prechoi == 10:
                        if not gpp.get_location_ofcity(text)[2] == "OK":
                            send_message("Bu şehiri bulamadım, tekrar denemek ister misin?", chat)
                        else:
                            prechoi = 0;
                            userLON = gpp.get_location_ofcity(text)[1]
                            userLAT = gpp.get_location_ofcity(text)[0]
                            gmt = gpp.get_location_ofcity(text)[3]
                            if not db.get_user_lat(chat):
                                db.add_user_with_cityName(chat,
                                                          userLAT,
                                                          userLON, text,
                                                          "tur", gmt)
                            else:
                                db.update_user_location_with_cityName(chat,
                                                                      userLAT,
                                                                      userLON, text)
                            prayTime = \
                                get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), gmt)[
                                    'pray_time']
                            prayTimeName = \
                                get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), gmt)[
                                    'closest_time']
                            prayTimeRema = \
                                get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), gmt)[
                                    'remaining_time']
                            send_message(
                                text + " için " + prayTimeName + " ezanının vakti " + prayTime + ", " + prayTimeName + " ezanına " + prayTimeRema[
                                                                                                                                     :1] + " saat, " + prayTimeRema[
                                                                                                                                                       2:4] + " dakika kaldı.",
                                chat)
                    else:
                        userLON = db.get_user_long(chat)[0]
                        userLAT = db.get_user_lat(chat)[0]
                        gmt = db.get_gmt(chat)[0]
                        prayTime = \
                            get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), gmt)[
                                'pray_time']
                        prayTimeName = \
                            get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), gmt)[
                                'closest_time']
                        prayTimeRema = \
                            get_closest_praytime_with_time((now.year, now.month, now.day), (userLAT, userLON), gmt)[
                                'remaining_time']
                        send_message(
                            prayTimeName + " ezanının vakti " + prayTime + ", " + prayTimeName + " ezanına " + prayTimeRema[
                                                                                                               :1] + "saat, " + prayTimeRema[
                                                                                                                                2:4] + " dakika kaldı.",
                            chat)
                    predelloc = 0
                elif len(set(text.split(" ")).intersection(set(allpraytimekeywordsTR))) > 1 or prechoi == 11:
                    if not db.get_user_lat(chat) and prechoi != 11:
                        send_message(
                            "Konum tercihlerini bilmiyorum. O yüzden ezan vakti için istediğin şehirin ismini yazabilirsin veya 'konumum' yazarak konumunu gönderebilirsin.",
                            chat)
                        prechoi = 11
                        predelloc = 0
                    elif prechoi == 11:
                        if not gpp.get_location_ofcity(text)[2] == "OK":
                            send_message("Bu şehiri bulamadım, tekrar denemek ister misin?", chat)
                        else:
                            prechoi = 0;
                            userLON = gpp.get_location_ofcity(text)[1]
                            userLAT = gpp.get_location_ofcity(text)[0]
                            gmt = gpp.get_location_ofcity(text)[3]
                            if not db.get_user_lat(chat):
                                db.add_user_with_cityName(chat,
                                                          userLAT,
                                                          userLON, text,
                                                          "tur", gmt)
                            else:
                                db.update_user_location_with_cityName(chat,
                                                                      userLAT,
                                                                      userLON, text)
                            send_message(get_all_pray_times((now.year, now.month, now.day), (userLAT, userLON), gmt) ,chat)
                    else:
                        userLON = db.get_user_long(chat)[0]
                        userLAT = db.get_user_lat(chat)[0]
                        gmt = db.get_gmt(chat)[0]
                        send_message(get_all_pray_times((now.year, now.month, now.day), (userLAT, userLON), gmt), chat)
                    predelloc = 0
                else:
                    send_message("Ne demek istediğini anlayamadım, istersen /yardim yazabilirsin", chat)
                    prechoi = 0
                    predelloc = 0
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
    get_url(url)


def get_all_pray_times(date, coordinates, timeZone):
    allpraytimes = pt.getTimes(date, coordinates, timeZone)
    selectedpraytimes = "İmsak : " + allpraytimes['imsak'] + \
                        "\nSabah : " + allpraytimes['fajr'] + \
                        "\nGündoğumu : " + allpraytimes['sunrise'] + \
                        "\nÖğle : " + allpraytimes['dhuhr'] + \
                        "\nİkindi : " + allpraytimes['asr'] + \
                        "\nAkşam : " + allpraytimes['maghrib'] + \
                        "\nYatsı : " + allpraytimes['isha']
    return selectedpraytimes


def get_closest_praytime_with_time(date, coordinates, timeZone):
    allpraytimes = pt.getTimes(date, coordinates, timeZone)
    praytimearray = ['imsak', 'fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha']
    for temptimename in praytimearray:
        closesttime = temptimename
        if now.strftime('%H:%M') < allpraytimes[temptimename]:
            break
    date_format = "%H:%M"
    timenow = datetime.strptime(now.strftime('%H:%M'), date_format)
    timepray = datetime.strptime(allpraytimes[closesttime], date_format)
    praytime = allpraytimes[closesttime]
    tremain = str((timepray - timenow))
    print(tremain)
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
    elif (closesttime == "maghrib"):
        closesttime = "Akşam"
    elif (closesttime == "isha"):
        closesttime = "Yatsı"
    return {'closest_time': closesttime, 'remaining_time': tremain, 'pray_time': praytime}


def main():
    db.setup()
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
