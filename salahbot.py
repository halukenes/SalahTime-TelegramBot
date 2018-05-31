import json
import requests
import time
import urllib

from datetime import datetime, timedelta
from dbhelper import DBHelper
from praytimes import PrayTimes
from googleplacesparser import GooglePlaceParser
from surahtmlparser import HTMLParser

db = DBHelper()
gpp = GooglePlaceParser()
pt = PrayTimes()
stage = 0
prelang = 0
prechoi = 0
predelloc = 0
presure = 0
prenoti = 0
prechoosesura = None
prechoosemean = None
prechooselang = None

TOKEN = "584920327:AAGKd2EDjQyIwyEwLalcMBnlMYZj6xF3K_s"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

praytimekeywords = ['ezan', 'ne', 'zaman', 'kaç dakika kaldı', 'okunmasına', 'ezana', 'ezanın', 'kaçta', 'pray', 'when',
                    'time', 'how many minutes', 'salah time', 'next', '/pray']
allpraytimekeywords = ['ezanları', 'ezan', 'ezanlar', 'hepsi', 'vakitlerinin', 'tüm', 'tümü', 'bugünki', 'vakitlerini',
                       'vakitleri', 'saatleri', 'pray',
                       'times',
                       'all', 'pray times'
                              'salah', 'salah times', 'hours', 'salah time', 'when']
firstkeywords = ['hi', 'hello', 'merhaba', '/start', '/yardim', '/help', 'menu', '/menu', 'menü']
settingskeywords = ['ayarlar', '/ayarlar', '/settings', 'settings', 'setting']
sendlocationkeywords = ['konumum', 'send my location', 'my location', 'konumumu gönder']
locationkeywords = ['/konum', '/location']
allsurakeywords = ['tüm', 'hepsi', 'tamamı', 'tümü', 'all', 'all of it', 'completely', 'complete']
suraarabicselec = ['arabic', 'arapça', 'arapça olarak', 'in arabic']
suralangselecti = ['meal', 'meaning', 'mealini', 'the meaning', 'meal olarak', 'meal şeklinde', 'in the meaning',
                   'türkçe', 'turkish']
readsurakeyword = ['sure oku', 'read sura', '/sura', '/sure', 'sure', 'sura']


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
    global stage
    now = datetime.now()
    for update in updates["result"]:
        try:
            chat = update["message"]["chat"]["id"]
            if "location" in update["message"]:
                user_lat = update["message"]["location"]["latitude"]
                user_lng = update["message"]["location"]["longitude"]
                db.update_user_location_and_gmt(chat, user_lat, user_lng, None, +3)
            else:
                text = update["message"]["text"]
                if not db.get_user_language(chat):
                    db.add_user_with_language(chat, "en")
                if text in firstkeywords:
                    if db.get_user_language(chat) == "tur":
                        textkeyboard = ["/ezan", "/sure", "/ayarlar"]
                        keyboard = build_keyboard(textkeyboard)
                        send_message(
                            "Ezan vakti botuna hoşgeldin. Bana ezanın ne zaman okunacağı sorabilir veya sana göstermemi "
                            "istediğin bir ayet veya sure gösterebilirim. Komut olarak da /ezan yazarak ezan vaktine kaç "
                            "dakika kaldığını, 'tüm ezan vakitleri' ile bugünkü tüm vakitleri, /sure yazarak sureleri ve /ayarlar yazarak bot tercihlerini "
                            "değiştirebilirsin.", chat, keyboard)
                    elif db.get_user_language(chat) == "en":
                        textkeyboard = ["/salah", "/sura", "/settings"]
                        keyboard = build_keyboard(textkeyboard)
                        send_message(
                            "Welcome to Salah Time Bot. You can ask me when the pray time or I can show you a verse "
                            "that you want. As a command, you can learn how many minutes you have left by typing "
                            "/pray, you can see all the pray times of today with 'all pray times', you can see the verses by typing /sura, you can change the settings by typing "
                            "/settings.",
                            chat, keyboard)
                elif text.lower() in settingskeywords:
                    if db.get_user_language(chat) == "tur":
                        textkeyboard = ["/dil", "/konum", "/bildirim"]
                        keyboard = build_keyboard(textkeyboard)
                        send_message(
                            "Tercihlerini değiştirmek için aşağıdakilerden birisini seçebilirsin veya bir dahaki sefere "
                            "direk bunları bana yazabilirsin.", chat, keyboard)
                    elif db.get_user_language(chat) == "en":
                        textkeyboard = ["/language", "/location", "/notification"]
                        keyboard = build_keyboard(textkeyboard)
                        send_message(
                            "You can choose one of the following to change your preferences, or you can write them to "
                            "me at a later stage.", chat, keyboard)
                elif text in sendlocationkeywords:
                    if db.get_user_language(chat) == "tur":
                        keyboard = build_keyboard_for_location('tur')
                        send_message("Aşağıdaki tuşa basarak konumunuzu gönderebilirsiniz.", chat, keyboard)
                    elif db.get_user_language(chat) == "en":
                        keyboard = build_keyboard_for_location('en')
                        send_message("You can send your location by pressing the key below.", chat, keyboard)
                elif text in locationkeywords:
                    if db.get_user_language(chat) == "tur":
                        if (db.get_user_lat(chat) == 'on' or db.get_user_lat(chat) == ''):
                            send_message(
                                "Önceden belirlediğin bir konum yok, benden ezan vakitlerini istediğin zaman konumunu da belirleyebilirsin.(/ezan yazabilirsin.)",
                                chat)
                            db.update_user_stage(chat, 0)
                        else:
                            if db.get_user_cityName(chat) == None:
                                send_message(
                                    "Konum tercihlerini önceden belirlemişsin, eğer değiştirmek veya silmek istiyorsan 'sil' yazabilirsin.",
                                    chat)
                            else:
                                send_message("Konum tercihlerini önceden belirlemişsin: '" + str(
                                    db.get_user_cityName(chat)) + "', eğer bunu silmek istiyorsan 'sil' yazabilirsin.",
                                             chat)
                    elif db.get_user_language(chat) == "en":
                        if (db.get_user_lat(chat) == 'on' or db.get_user_lat(chat) == '') or db.get_user_lat(
                                chat) == '':
                            send_message(
                                "There is no location you set before, you can also set your location at any time when "
                                "you want me to show pray times. (You can type '/pray')",
                                chat)
                            db.update_user_stage(chat, 0)
                        else:
                            if db.get_user_cityName(chat) == None:
                                send_message(
                                    "You have preset location preferences. If you want to change or delete it, you can type 'delete'.",
                                    chat)
                            else:
                                send_message("You have preset location preferences: '" + str(
                                    db.get_user_cityName(
                                        chat)) + "'. If you want to change or delete it, you can type 'delete'.",
                                             chat)
                                db.update_user_stage(chat, 1)
                elif db.get_stage(chat) == 2:
                    if text.lower() == "evet" or text.lower() == "yes":
                        if db.get_user_language(chat) == "tur":
                            db.update_user_location(chat, None, None)
                            send_message(
                                "Konum tercihini artık bilmiyorum, benden ezan vakitlerini istediğin zaman konumunu da tekrardan belirleyebilirsin. ('/salah' yazabilirsin.)",
                                chat)
                        elif db.get_user_language(chat) == "en":
                            db.update_user_location(chat, None, None)
                            send_message(
                                "I don't know your location preference anymore, you can choose your location from pray times whenever you want. (You can type '/pray')",
                                chat)
                            db.update_user_stage(chat, 0)
                    else:
                        if db.get_user_language(chat) == "tur":
                            send_message(
                                "İsteğin üzerine konum tercihlerini değiştirmedim. ('/menu' yazabilirsin.)",
                                chat)
                            db.update_user_stage(chat, 0)
                        elif db.get_user_language(chat) == "en":
                            send_message(
                                "I have not changed your location preferences on your request. (You can type '/menu')",
                                chat)
                            db.update_user_stage(chat, 0)
                elif db.get_stage(chat) == 1:
                    if db.get_user_language(chat) == "tur":
                        if text.lower() == "sil" or text.lower() == "delete":
                            send_message(
                                "Konum tercihini silmek istiyorsan 'evet' yaz.",
                                chat)
                            db.update_user_stage(chat, 2)
                        else:
                            send_message(
                                "Konum tercihlerinden çıktım. ('/menu' yazabilirsin.)",
                                chat)
                            db.update_user_stage(chat, 0)
                    elif db.get_user_language(chat) == "en":
                        if text.lower() == "sil" or text.lower() == "delete":
                            send_message(
                                "If you want to delete the location preference, type 'yes'.",
                                chat)
                            db.update_user_stage(chat, 2)
                        else:
                            send_message(
                                "I'm out of location preferences. (You can type '/menu')",
                                chat)
                            db.update_user_stage(chat, 0)
                elif len(set(text.split(" ")).intersection(set(
                        praytimekeywords))) > 1 or text == 'ezan' or text.lower() == '/ezan' or text == 'salah' or text.lower() == '/salah' or text.lower() == '/pray' or db.get_stage(
                    chat) == 10:
                    if db.get_user_language(chat) == "tur":
                        if (db.get_user_lat(chat) == 'on' or db.get_user_lat(chat) == '') and db.get_stage(chat) != 10:
                            send_message(
                                "Konum tercihlerini bilmiyorum. O yüzden ezan vakti için istediğin şehirin ismini yazabilirsin veya 'konumum' yazarak konumunu gönderebilirsin. (Mesela 'Ankara' yaz.)",
                                chat)
                            db.update_user_stage(chat, 10)
                        elif db.get_stage(chat) == 10:
                            if not gpp.get_location_ofcity(text)[2] == "OK":
                                send_message("Bu şehiri bulamadım, tekrar denemek ister misin?", chat)
                            else:
                                db.update_user_stage(chat, 0)
                                cityResults = gpp.get_location_ofcity(text)
                                userLON = cityResults[1]
                                userLAT = cityResults[0]
                                gmt = cityResults[3]
                                lang = db.get_user_language(chat)
                                db.update_user_location_with_cityName(chat,
                                                                      userLAT,
                                                                      userLON, text, gmt)
                                prayTimeRow = get_closest_praytime_with_time((now.year, now.month, now.day),
                                                                             (float(userLAT), float(userLON)), gmt,
                                                                             lang)
                                prayTime = prayTimeRow['pray_time']
                                prayTimeName = prayTimeRow['closest_time']
                                prayTimeRema = prayTimeRow['remaining_time']
                                send_message(
                                    text + " için " + prayTimeName + " ezanının vakti " + prayTime + ", " + prayTimeName + " ezanına " + prayTimeRema[
                                                                                                                                         :1] + " saat, " + prayTimeRema[
                                                                                                                                                           2:4] + " dakika kaldı.",
                                    chat)
                        else:
                            userLON = db.get_user_long(chat)
                            userLAT = db.get_user_lat(chat)
                            gmt = db.get_gmt(chat)
                            lang = db.get_user_language(chat)
                            prayTimeRow = get_closest_praytime_with_time((now.year, now.month, now.day),
                                                                         (float(userLAT), float(userLON)), gmt, lang)
                            prayTime = prayTimeRow['pray_time']
                            prayTimeName = prayTimeRow['closest_time']
                            prayTimeRema = prayTimeRow['remaining_time']
                            send_message(
                                prayTimeName + " ezanının vakti " + prayTime + ", " + prayTimeName + " ezanına " + prayTimeRema[
                                                                                                                   :1] + " saat, " + prayTimeRema[
                                                                                                                                     2:4] + " dakika kaldı.",
                                chat)
                    elif db.get_user_language(chat) == "en":
                        if (db.get_user_lat(chat) == 'on' or db.get_user_lat(chat) == '') and db.get_stage(chat) != 10:
                            send_message(
                                "I do not know location preferences. So you can write the name of the city you want "
                                "for the time of the pray, or you can send the location by typing 'my location'. (For example, you can type 'New York')",
                                chat)
                            db.update_user_stage(chat, 10)
                        elif db.get_stage(chat) == 10:
                            if not gpp.get_location_ofcity(text)[2] == "OK":
                                send_message("I could not find this city, would you like to try again?", chat)
                            else:
                                db.update_user_stage(chat, 0)
                                cityResults = gpp.get_location_ofcity(text)
                                userLON = cityResults[1]
                                userLAT = cityResults[0]
                                gmt = cityResults[3]
                                lang = db.get_user_language(chat)
                                db.update_user_location_with_cityName(chat,
                                                                      userLAT,
                                                                      userLON, text, gmt)
                                prayTimeRow = get_closest_praytime_with_time((now.year, now.month, now.day),
                                                                             (float(userLAT), float(userLON)), gmt,
                                                                             lang)
                                prayTime = prayTimeRow['pray_time']
                                prayTimeName = prayTimeRow['closest_time']
                                prayTimeRema = prayTimeRow['remaining_time']
                                send_message(
                                    "For " + text + " " + prayTimeName.title() + " time is " + prayTime + ", remaining time is " + prayTimeRema[
                                                                                                                                   :1] + " hour, " + prayTimeRema[
                                                                                                                                                     2:4] + "minutes.",
                                    chat)
                        else:
                            userLON = db.get_user_long(chat)
                            userLAT = db.get_user_lat(chat)
                            gmt = db.get_gmt(chat)
                            lang = db.get_user_language(chat)
                            prayTimeRow = get_closest_praytime_with_time((now.year, now.month, now.day),
                                                                         (float(userLAT), float(userLON)), gmt, lang)
                            prayTime = prayTimeRow['pray_time']
                            prayTimeName = prayTimeRow['closest_time']
                            prayTimeRema = prayTimeRow['remaining_time']
                            send_message(prayTimeName.title() + " time is " +
                                         prayTime + ", remaining time is " +
                                         prayTimeRema[:1] + " hour, " +
                                         prayTimeRema[2:4] + "minutes.", chat)
                elif len(set(text.split(" ")).intersection(set(allpraytimekeywords))) > 1 or db.get_stage(chat) == 11:
                    if db.get_user_language(chat) == "tur":
                        if (db.get_user_lat(chat) == 'on' or db.get_user_lat(chat) == '') and db.get_stage(chat) != 11:
                            send_message(
                                "Konum tercihlerini bilmiyorum. O yüzden ezan vakti için istediğin şehirin ismini yazabilirsin veya 'konumum' yazarak konumunu gönderebilirsin. (Mesela 'Ankara' yaz.)",
                                chat)
                            db.update_user_stage(chat, 11)
                        elif db.get_stage(chat) == 11:
                            if not gpp.get_location_ofcity(text)[2] == "OK":
                                send_message("Bu şehiri bulamadım, tekrar denemek ister misin?", chat)
                            else:
                                db.update_user_stage(chat, 0)
                                cityResults = gpp.get_location_ofcity(text)
                                userLON = cityResults[1]
                                userLAT = cityResults[0]
                                gmt = cityResults[3]
                                db.update_user_location_with_cityName(chat,
                                                                      userLAT,
                                                                      userLON, text, gmt)
                                send_message(
                                    get_all_pray_times((now.year, now.month, now.day), (float(userLAT), float(userLON)),
                                                       gmt,
                                                       db.get_user_language(chat)),
                                    chat)
                        else:
                            userLON = db.get_user_long(chat)
                            userLAT = db.get_user_lat(chat)
                            gmt = db.get_gmt(chat)
                            send_message(
                                get_all_pray_times((now.year, now.month, now.day), (float(userLAT), float(userLON)),
                                                   gmt,
                                                   db.get_user_language(chat)),
                                chat)
                    elif db.get_user_language(chat) == "en":
                        if (db.get_user_lat(chat) == 'on' or db.get_user_lat(chat) == '') and db.get_stage(chat) != 11:
                            send_message(
                                "I do not know location preferences. So you can write the name of the city you want "
                                "for the time of the pray, or you can send the location by typing 'my location'. (For example, you can type 'New York')",
                                chat)
                            db.update_user_stage(chat, 11)
                        elif db.get_stage(chat) == 11:
                            if not gpp.get_location_ofcity(text)[2] == "OK":
                                send_message("I could not find this city, would you like to try again?", chat)
                            else:
                                db.update_user_stage(chat, 0)
                                cityResults = gpp.get_location_ofcity(text)
                                userLON = cityResults[1]
                                userLAT = cityResults[0]
                                gmt = cityResults[3]
                                db.update_user_location_with_cityName(chat,
                                                                      userLAT,
                                                                      userLON, text, gmt)
                                send_message(
                                    get_all_pray_times((now.year, now.month, now.day), (float(userLAT), float(userLON)),
                                                       gmt,
                                                       db.get_user_language(chat)),
                                    chat)
                        else:
                            userLON = db.get_user_long(chat)
                            userLAT = db.get_user_lat(chat)
                            gmt = db.get_gmt(chat)
                            send_message(
                                get_all_pray_times((now.year, now.month, now.day), (float(userLAT), float(userLON)),
                                                   gmt,
                                                   db.get_user_language(chat)),
                                chat)
                elif text.lower() in readsurakeyword:
                    if db.get_user_language(chat) == "tur":
                        send_message("Hangi sureyi istersin? (Mesela 'Yasin' yazabilirsin.)", chat)
                    elif db.get_user_language(chat) == "en":
                        send_message("Which sura do you want to look? (For example, you can type 'Yasin')", chat)
                    db.update_user_stage(chat, 15)
                elif db.get_stage(chat) == 15:
                    db.update_user_pS(chat, text.lower())
                    if db.get_user_language(chat) == "tur":
                        send_message(
                            "Tüm ayetler için 'tümü', belirli bir ayet için de ayet numarasını yaz? (Mesela '6' yada 'tümü' yazabilirsin.)",
                            chat)
                    elif db.get_user_language(chat) == "en":
                        send_message(
                            "For all the verses of the sura, write 'all'; or for a specific verse, write the verse number. (For example, '6' or 'all'.)",
                            chat)
                    db.update_user_stage(chat, 16)
                elif db.get_stage(chat) == 16:
                    db.update_user_pL(chat, text.lower())
                    if db.get_user_language(chat) == "tur":
                        send_message("Arapça olarak mı yoksa Türkçe mealini mi istersin? ('Türkçe' yazabilirsin.)",
                                     chat)
                    elif db.get_user_language(chat) == "en":
                        send_message("Do you want in Arabic or Turkish meaning? (You can type 'Arabic')", chat)
                    db.update_user_stage(chat, 17)
                elif db.get_stage(chat) == 17:
                    db.update_user_pM(chat, text.lower())
                    try:
                        if db.get_pL(chat) in allsurakeywords and db.get_pM(chat).lower() in suraarabicselec:
                            parser = HTMLParser("suras/" + db.get_pS(chat).lower() + ".html")
                            allsura = parser.get_all_sura_with_text()
                            for verse in allsura:
                                send_message(str(verse)[6:-7], chat)
                            db.update_sura(db.get_pS(chat).lower())
                            db.update_user_readsuraCount(chat)
                        elif db.get_pL(chat) in allsurakeywords and db.get_pM(chat).lower() in suralangselecti:
                            parser = HTMLParser("suras/" + db.get_pS(chat).lower() + ".html")
                            allsura = parser.get_all_sura_with_meaning()
                            for verse in allsura:
                                send_message(str(verse)[6:-7], chat)
                            db.update_sura(db.get_pS(chat).lower())
                            db.update_user_readsuraCount(chat)
                        elif representsInt(db.get_pL(chat)) and db.get_pM(chat).lower() in suraarabicselec:
                            parser = HTMLParser("suras/" + db.get_pS(chat).lower() + ".html")
                            send_message(str(parser.get_text(int(db.get_pL(chat)))), chat)
                            db.update_sura(db.get_pS(chat).lower())
                            db.update_user_readsuraCount(chat)
                        elif representsInt(db.get_pL(chat)) and db.get_pM(chat).lower() in suralangselecti:
                            parser = HTMLParser("suras/" + db.get_pS(chat).lower() + ".html")
                            send_message(str(parser.get_meaning(int(db.get_pL(chat)))), chat)
                            db.update_sura(db.get_pS(chat).lower())
                            db.update_user_readsuraCount(chat)
                        else:
                            send_message(
                                "Sanırım bir yerlerde hata yaptın, tekrar denemek ister misin? ('/sure' yazabilirsin.)",
                                chat)
                    except FileNotFoundError:
                        if db.get_user_language(chat) == "en":
                            send_message(
                                "I couldn't find the sura you wanted, would you like to try again? (You can type '/sura')",
                                chat)
                        elif db.get_user_language(chat) == "tur":
                            send_message(
                                "İstediğin sureyi bulamadım, tekrar denemek ister misin? ('/sure' yazabilirsin.)", chat)
                        pass
                    except IndexError:
                        if db.get_user_language(chat) == "en":
                            send_message("This sura doesn't include " + str(
                                db.get_pL(chat)) + ". verse, would you like to try again? (You can type '/sura')", chat)
                        elif db.get_user_language(chat) == "tur":
                            send_message(
                                "Bu sure " + str(
                                    db.get_pL(chat)) + ". ayeti içermiyor, tekrar denemek ister misin? ('/sure' yazabilirsin.)",
                                chat)
                        pass
                    db.update_user_stage(chat, 0)
                elif text == "/language" or text == "/dil":
                    if db.get_user_language(chat) == "tur":
                        send_message("Dil ayarın Türkçe olarak ayarlı, dil tercihini değiştirmek istiyorsan 'english' "
                                     "yaz.(If you want to change the language to English, write 'english')", chat)
                        db.update_user_stage(chat, 20)
                    elif db.get_user_language(chat) == "en":
                        send_message("Your language has been set to English. If you want to change this to Turkish, "
                                     "you can write 'turkish'. (Dil tercihini Türkçe olarak ayarlamak istiyorsan, "
                                     "'turkish' yaz.)", chat)
                        db.update_user_stage(chat, 21)
                elif db.get_stage(chat) == 20 and text.lower() == "english":
                    db.update_user_language(chat, "en")
                    send_message("Language has been changed to English. (You can type '/menu'.)", chat)
                    db.update_user_stage(chat, 0)
                elif db.get_stage(chat) == 21 and text.lower() == "turkish":
                    db.update_user_language(chat, "tur")
                    send_message("Dil Türkçe olarak değiştirildi.  ('/menu' yazabilirsin.)", chat)
                    db.update_user_stage(chat, 0)
                elif text == "/bildirim" or text == "/notification":
                    if db.get_user_notPeriod(chat) == None or db.get_user_notPeriod(chat) == 0:
                        if db.get_user_language(chat) == "tur":
                            send_message(
                                "Bildirim tercihlerini bilmiyorum; ezan vaktinden kaç dakika öncesinde bildirim "
                                "almak istiyorsun? (1-60 dakika arası) (Mesela '10' yaz.)", chat)
                        elif db.get_user_language(chat) == "en":
                            send_message(
                                "I do not know the notification preferences. How many minutes do you want to be notified before a salah time? (1-60 minutes) (For exmaple, type '10'.)",
                                chat)
                    else:
                        if db.get_user_language(chat) == "tur":
                            send_message("Bildirim tercihini " + str(db.get_user_notPeriod(chat)) + " dakika olarak "
                                                                                                    "ayarlamışsın, "
                                                                                                    "değiştirmek için "
                                                                                                    "1-60 dakika arası "
                                                                                                    "tercihini "
                                                                                                    "yazabilirsin. '0' yazarak da bildirimi kapatabilirsin. (Mesela '10' yaz.)",
                                         chat)
                        elif db.get_user_language(chat) == "en":
                            send_message("You set the notification preference to " + str(db.get_user_notPeriod(
                                chat)) + " minutes, you can write your choice between 1-60 minutes to change. You can write '0' to close notifications. (For exmaple, type '10'.)",
                                         chat)
                            db.update_user_stage(chat, 40)
                elif db.get_stage(chat) == 40:
                    if representsInt(text):
                        db.update_user_notification_rate(chat, int(text))
                        if db.get_user_language(chat) == "tur":
                            send_message(
                                "Bildirim tercihini " + text + " dakika olarak ayarlandı. Peki hangi vakitlerde bildirim almak istiyorsun? (Örneğin 'öğlen, akşam')",
                                chat)
                            db.update_user_stage(chat, 41)
                        elif db.get_user_language(chat) == "en":
                            send_message(
                                "Notification preference is set to " + text + " minutes. In which salah times do you want to be reminded? (e.g. 'dhuhr, maghrib')",
                                chat)
                            db.update_user_stage(chat, 41)
                        if text == "0":
                            db.update_user_nextnotTime(chat, ".")
                    else:
                        if db.get_user_language(chat) == "tur":
                            send_message("Bildirim tercihlerinden çıktım. ('/menu' yazabilirsin.)", chat)
                        elif db.get_user_language(chat) == "en":
                            send_message("I'm out of the notification preferences. (You can type '/menu')", chat)
                elif db.get_stage(chat) == 41:
                    userLON = db.get_user_long(chat)
                    userLAT = db.get_user_lat(chat)
                    gmt = db.get_gmt(chat)
                    prayTimeRow = get_closest_praytime_with_time((now.year, now.month, now.day),
                                                                 (float(userLAT), float(userLON)), gmt,
                                                                 (db.get_user_language(chat)))
                    prayTime = prayTimeRow['pray_time']
                    prayTimeCode = prayTimeRow['nextCoded']
                    db.update_user_remindCode(chat, transformtoReminderFormat(text))
                    if prayTimeCode == 0:
                        prayTimeCode = 7
                    if db.get_user_language(chat) == "tur":
                        if transformtoReminderFormat(text)[prayTimeCode - 1] == "1":
                            set_user_nextNotPeriod(chat, prayTime)
                        else:
                            set_user_nextNotPeriod(chat, "N")
                        send_message("Bildirim ayarlarının tamamlandı. ('/menu' yazabilirsin.)", chat)
                    elif db.get_user_language(chat) == "en":
                        if transformtoReminderFormat(text)[prayTimeCode - 1] == "1":
                            set_user_nextNotPeriod(chat, prayTime)
                        else:
                            set_user_nextNotPeriod(chat, "N")
                        send_message("Your notification settings is completed. (You can type '/menu'", chat)
                else:
                    if db.get_user_language(chat) == "tur":
                        send_message("Ne demek istediğini anlayamadım, istersen /yardim yazabilirsin", chat)
                    elif db.get_user_language(chat) == "en":
                        send_message("I don't understand what you mean, you can write '/help'.", chat)
                db.update_user_interaction(chat)
        except KeyError:
            pass


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def build_keyboard_for_location(lan):
    if lan == 'tur':
        getLocationJ = {"text": "Konumumu gönder", "request_location": True}
        keyboard = [[getLocationJ]]
        reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    elif lan == 'en':
        getLocationJ = {"text": "Send my location", "request_location": True}
        keyboard = [[getLocationJ]]
        reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


def get_all_pray_times(date, coordinates, timeZone, lan):
    allpraytimes = pt.getTimes(date, coordinates, int(timeZone))
    if lan == "tur":
        selectedpraytimes = "İmsak : " + allpraytimes['imsak'] + \
                            "\nGündoğumu : " + allpraytimes['sunrise'] + \
                            "\nÖğle : " + allpraytimes['dhuhr'] + \
                            "\nİkindi : " + allpraytimes['asr'] + \
                            "\nAkşam : " + allpraytimes['maghrib'] + \
                            "\nYatsı : " + allpraytimes['isha']
    else:
        selectedpraytimes = "Imsak : " + allpraytimes['imsak'] + \
                            "\nSunrise : " + allpraytimes['sunrise'] + \
                            "\nDhuhr : " + allpraytimes['dhuhr'] + \
                            "\nAsr : " + allpraytimes['asr'] + \
                            "\nMaghrib : " + allpraytimes['maghrib'] + \
                            "\nIsha : " + allpraytimes['isha']
    return selectedpraytimes


def get_closest_praytime_with_time(date, coordinates, timeZone, lan):
    allpraytimes = pt.getTimes(date, coordinates, int(timeZone))
    praytimearray = ['imsak', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha']
    now = datetime.strptime((datetime.now() + timedelta(hours=int(timeZone))).strftime('%H:%M'), "%H:%M")
    nextpray = None
    for i in range(len(praytimearray)):
        closesttime = praytimearray[i]
        if now.strftime('%H:%M') < allpraytimes[praytimearray[i]]:
            if i != len(praytimearray) - 1:
                nextpray = allpraytimes[praytimearray[i + 1]]
            else:
                nextpray = allpraytimes[praytimearray[0]]
            break
        if closesttime == 'isha' and now.strftime('%H:%M') > allpraytimes['isha']:
            closesttime = 'imsak'
    date_format = "%H:%M"
    timenow = datetime.strptime(now.strftime('%H:%M'), date_format)
    timepray = datetime.strptime(allpraytimes[closesttime], date_format)
    praytime = allpraytimes[closesttime]
    tremain = str((timepray - timenow))
    nextCoded = 0
    if lan == "tur":
        if (closesttime == "imsak"):
            closesttime = "İmsak"
            nextCoded = 1
        elif (closesttime == "fajr"):
            closesttime = "Sabah"
            nextCoded = 2
        elif (closesttime == "sunrise"):
            closesttime = "Gündoğumu"
            nextCoded = 3
        elif (closesttime == "dhuhr"):
            closesttime = "Öğle"
            nextCoded = 4
        elif (closesttime == "asr"):
            closesttime = "İkindi"
            nextCoded = 5
        elif (closesttime == "maghrib"):
            closesttime = "Akşam"
            nextCoded = 6
        elif (closesttime == "isha"):
            closesttime = "Yatsı"
            nextCoded = 0
    if tremain[0] == "-":
        tremain = tremain[8:12]
    if isTimewithSecondFormat(tremain):
        tremain = str(
            (datetime.strptime(str(tremain)[:-3], "%H:%M") - timedelta(hours=int(timeZone))).strftime('%H:%M'))[1:]

    return {'closest_time': closesttime, 'remaining_time': tremain, 'pray_time': praytime, 'next_time': nextpray,
            'nextCoded': nextCoded}


def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)


def isTimewithSecondFormat(input):
    try:
        time.strptime(input, '%H:%M:%S')
        return True
    except ValueError:
        return False


def set_user_nextNotPeriod(userID, nextPrayTime):
    if nextPrayTime != "." and nextPrayTime != "N":
        nextNotTime = (datetime.strptime(nextPrayTime, "%H:%M") - timedelta(
            minutes=int(db.get_user_notPeriod(userID)))).strftime('%H:%M')
        db.update_user_nextnotTime(userID, str(nextNotTime))


def notify_users():
    now = datetime.now()
    if not db.get_users_to_notify(str(now.strftime('%H:%M'))) == "[]":
        users = db.get_users_to_notify(str(now.strftime('%H:%M')))
        for user in users:
            user = str(user)[2:-3]
            userLON = db.get_user_long(user)
            userLAT = db.get_user_lat(user)
            gmt = db.get_gmt(user)
            nextprayTimeRow = get_closest_praytime_with_time((now.year, now.month, now.day),
                                                             (float(userLAT), float(userLON)), gmt,
                                                             (db.get_user_language(user)))
            nextprayTime = nextprayTimeRow['next_time']
            prayTimeCode = nextprayTimeRow['nextCoded']
            tempprayTimeCode = prayTimeCode
            if tempprayTimeCode == 0:
                tempprayTimeCode = 7
            if transformtoReminderFormat(db.get_remindCode(user))[tempprayTimeCode - 1] == "1":
                if db.get_user_language(user) == "tur":
                    send_message("Sonraki ezan vaktine " + str(db.get_user_notPeriod(user)) + " dakika kaldı.", user)
                elif db.get_user_language(user) == "en":
                    send_message("There are " + str(db.get_user_notPeriod(user)) + " minutes to next salah time.", user)
            set_user_nextNotPeriod(user, nextprayTime)


def transformtoReminderFormat(input):
    reminderFormat = ""
    if 'imsak' in input.lower():
        reminderFormat = reminderFormat + "1"
    else:
        reminderFormat = reminderFormat + "0"
    if 'fajr' in input.lower() or 'sabah' in input.lower():
        reminderFormat = reminderFormat + "1"
    else:
        reminderFormat = reminderFormat + "0"
    if 'sunrise' in input.lower() or 'gündoğumu' in input.lower():
        reminderFormat = reminderFormat + "1"
    else:
        reminderFormat = reminderFormat + "0"
    if 'dhuhr' in input.lower() or 'öğle' in input.lower():
        reminderFormat = reminderFormat + "1"
    else:
        reminderFormat = reminderFormat + "0"
    if 'asr' in input.lower() or 'ikindi' in input.lower():
        reminderFormat = reminderFormat + "1"
    else:
        reminderFormat = reminderFormat + "0"
    if 'maghrib' in input.lower() or 'akşam' in input.lower():
        reminderFormat = reminderFormat + "1"
    else:
        reminderFormat = reminderFormat + "0"
    if 'isha' in input.lower() or 'yatsı' in input.lower():
        reminderFormat = reminderFormat + "1"
    else:
        reminderFormat = reminderFormat + "0"
    return reminderFormat


def main():
    db.setup()
    print(db.get_pL(465066877))
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        notify_users()
        time.sleep(0.5)


if __name__ == '__main__':
    main()
