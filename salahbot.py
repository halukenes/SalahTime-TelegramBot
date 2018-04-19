import json
import requests
import time
import urllib

from dbhelper import DBHelper

db = DBHelper()

pretext = None

TOKEN = "584920327:AAGKd2EDjQyIwyEwLalcMBnlMYZj6xF3K_s"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


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
    for update in updates["result"]:
        try:
            if "location" in update["message"]:
                print(update["message"]["location"]["latitude"])
                lang = "tur"
                db.add_user(update["message"]["from"]["id"],
                            update["message"]["location"]["latitude"],
                            update["message"]["location"]["longitude"],
                            "tur")
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
                elif text == "ayarlar":
                    textkeyboard = ["dil", "konum", "bildirim"]
                    keyboard = build_keyboard(textkeyboard)
                    send_message(
                        "Tercihlerini değiştirmek için aşağıdakilerden birisini seçebilirsin veya bir dahaki sefere "
                        "direk bunları bana yazabilirsin.", chat, keyboard)
                elif text == "konum":
                    keyboard = build_keyboard_for_location()
                    send_message(
                        "Aşağıdaki tuşa basarak konumunuzu gönderebilirsiniz.", chat, keyboard)
                elif pretext == "konum":
                    print("pretext1 kullanıldı")
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


def main():
    db.setup()
    last_update_id = None
    previous_update = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
