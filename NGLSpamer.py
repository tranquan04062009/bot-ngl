import telebot
import requests
import os
import random
from time import sleep

# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
BOT_TOKEN = '7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo'
bot = telebot.TeleBot(BOT_TOKEN)

list_clone = []
list_img = []
dem = 0
stt = 0
stt2 = 0

# =========================== [ CLASS + FUNCTION TOOL ] ===========================
class API_PRO5_ByNgDucPhat:
    def __init__(self):
        pass

    def ndp_delay_tool(self, p):
        """
        Simple delay function.  Consider removing/replacing as it's blocking.
        """
        sleep(p) # Simplified delay

    def getthongtinfacebook(self, cookie: str):
        headers_get = {
            'authority': 'www.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'viewport-width': '1184',
            'cookie': cookie
        }
        try:
            url_profile = requests.get('https://www.facebook.com/me', headers=headers_get).url
            get_dulieu_profile = requests.get(url=url_profile, headers=headers_get).text
        except:
            return False
        try:
            uid_get = cookie.split('c_user=')[1].split(';')[0]
            fb_dtsg_get = get_dulieu_profile.split('{"name":"fb_dtsg","value":"')[1].split('"},')[0]
            jazoest_get = get_dulieu_profile.split('{"name":"jazoest","value":"')[1].split('"},')[0]
            name_get = get_dulieu_profile.split('<title>')[1].split('</title>')[0]
            return name_get, uid_get, fb_dtsg_get, jazoest_get
        except:
            try:
                uid_get = cookie.split('c_user=')[1].split(';')[0]
                fb_dtsg_get = get_dulieu_profile.split(',"f":"')[1].split('","l":null}')[0]
                jazoest_get = get_dulieu_profile.split('&jazoest=')[1].split('","e":"')[0]
                name_get = get_dulieu_profile.split('<title>')[1].split('</title>')[0]
                return name_get, uid_get, fb_dtsg_get, jazoest_get
            except:
                return False

    def UpAvt(self, cookie, id_page, link_anh):
        sleep(5)
        try:
            json_upavt =  requests.get(f'https://api-ndpcutevcl.000webhostapp.com/api/upavtpage.php?cookie={cookie}&id={id_page}&link_anh={link_anh}').json()
            if json_upavt['status'] == 'success':
                return json_upavt
            else:
                return False
        except:
            return False

    def RegPage(self, cookie, name, uid, fb_dtsg, jazoest):
        namepage = requests.get('https://story-shack-cdn-v2.glitch.me/generators/vietnamese-name-generator/male?count=2').json()['data'][0]['name']
        global dem
        headers_reg = {
            'authority': 'www.facebook.com',
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
            'origin': 'https://www.facebook.com',
            'referer': 'https://www.facebook.com/pages/creation?ref_type=launch_point',
            'sec-ch-prefers-color-scheme': 'dark',
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            'viewport-width': '979',
            'x-fb-friendly-name': 'AdditionalProfilePlusCreationMutation',
            'x-fb-lsd': 'ZM7FAk6cuRcUp3imwqvHTY',
            'cookie': cookie
        }
        data_reg = {
            'av': uid,
            '__user': uid,
            '__a': '1',
            '__dyn': '7AzHxq1mxu1syUbFuC0BVU98nwgU29zEdEc8co5S3O2S7o11Ue8hw6vwb-q7oc81xoswIwuo886C11xmfz81sbzoaEnxO0Bo7O2l2Utwwwi831wiEjwZwlo5qfK6E7e58jwGzE8FU5e7oqBwJK2W5olwuEjUlDw-wUws9ovUaU3qxWm2Sq2-azo2NwkQ0z8c84K2e3u362-2B0oobo',
            '__csr': 'gP4ZAN2d-hbbRmLObkZO8LvRcXWVvth9d9GGXKSiLCqqr9qEzGTozAXiCgyBhbHrRG8VkQm8GFAfy94bJ7xeufz8jK8yGVVEgx-7oiwxypqCwgF88rzKV8y2O4ocUak4UpDxu3x1K4opAUrwGx63J0Lw-wa90eG18wkE7y14w4hw6Bw2-o069W00CSE0PW06aU02Z3wjU6i0btw3TE1wE5u',
            '__req': 't',
            '__hs': '19296.HYP:comet_pkg.2.1.0.2.1',
            'dpr': '1',
            '__ccg': 'EXCELLENT',
            '__rev': '1006496476',
            '__s': '1gapab:y4xv3f:2hb4os',
            '__hsi': '7160573037096492689',
            '__comet_req': '15',
            'fb_dtsg': fb_dtsg,
            'jazoest': jazoest,
            'lsd': 'ZM7FAk6cuRcUp3imwqvHTY',
            '__aaid': '800444344545377',
            '__spin_r': '1006496476',
            '__spin_b': 'trunk',
            '__spin_t': '1667200829',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'AdditionalProfilePlusCreationMutation',
            'variables': '{"input":{"bio":"reg auto by duykhanh","categories":["181475575221097"],"creation_source":"comet","name":"'+namepage+'","page_referrer":"launch_point","actor_id":"'+uid+'","client_mutation_id":"1"}}',
            'server_timestamps': 'true',
            'doc_id': '5903223909690825',
        }
        try:
            idpage = requests.post('https://www.facebook.com/api/graphql/', headers=headers_reg, data=data_reg, timeout=20).json()['data']['additional_profile_plus_create']['additional_profile']['id']
            dem += 1
            return idpage
        except:
            return False


# =========================== [ TELEGRAM BOT HANDLERS ] ===========================
dpcutevcl = API_PRO5_ByNgDucPhat()
STATE = {}  # To keep track of user state


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    STATE[chat_id] = {'cookies': [], 'images': [], 'upload_avatar': False, 'page_limit': 0, 'delay': 0}
    bot.reply_to(message, "Welcome to the Facebook Page Registration Bot!\nUse /addcookie to add Facebook cookies.")

@bot.message_handler(commands=['addcookie'])
def add_cookie(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Please send me the Facebook cookie. Send each cookie separately.")
    STATE[chat_id]['awaiting_cookie'] = True

@bot.message_handler(func=lambda message: getattr(STATE.get(message.chat.id), 'awaiting_cookie', False) == True)
def handle_cookie(message):
    chat_id = message.chat.id
    cookie_fb = message.text
    checklive = dpcutevcl.getthongtinfacebook(cookie_fb)
    if checklive:
        STATE[chat_id]['cookies'].append(f'{cookie_fb}|{checklive[0]}|{checklive[1]}|{checklive[2]}|{checklive[3]}')
        bot.reply_to(message, f"Cookie added successfully.  User: {checklive[0]}.  Total cookies: {len(STATE[chat_id]['cookies'])}")
    else:
        bot.reply_to(message, "Invalid or expired cookie. Please check and try again.")
    STATE[chat_id]['awaiting_cookie'] = False


@bot.message_handler(commands=['addimage'])
def add_image(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Please send me the image link.  Send each link separately.")
    STATE[chat_id]['awaiting_image'] = True

@bot.message_handler(func=lambda message: getattr(STATE.get(message.chat.id), 'awaiting_image', False) == True)
def handle_image(message):
    chat_id = message.chat.id
    image_url = message.text
    STATE[chat_id]['images'].append(image_url)
    bot.reply_to(message, f"Image link added. Total images: {len(STATE[chat_id]['images'])}")
    STATE[chat_id]['awaiting_image'] = False


@bot.message_handler(commands=['setuploadavatar'])
def set_upload_avatar(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Do you want to upload an avatar after registering the page? (yes/no)")
    STATE[chat_id]['awaiting_upload_avatar_response'] = True

@bot.message_handler(func=lambda message: getattr(STATE.get(message.chat.id), 'awaiting_upload_avatar_response', False) == True)
def handle_upload_avatar_response(message):
    chat_id = message.chat.id
    response = message.text.lower()
    if response in ['yes', 'y']:
        STATE[chat_id]['upload_avatar'] = True
        bot.reply_to(message, "Avatar upload will be enabled after registration.")
    elif response in ['no', 'n']:
        STATE[chat_id]['upload_avatar'] = False
        bot.reply_to(message, "Avatar upload will be disabled.")
    else:
        bot.reply_to(message, "Invalid response. Please answer 'yes' or 'no'.")
    STATE[chat_id]['awaiting_upload_avatar_response'] = False


@bot.message_handler(commands=['setpagelimit'])
def set_page_limit(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Please enter the number of pages you want to create before the tool stops.")
    STATE[chat_id]['awaiting_page_limit'] = True

@bot.message_handler(func=lambda message: getattr(STATE.get(message.chat.id), 'awaiting_page_limit', False) == True)
def handle_page_limit(message):
    chat_id = message.chat.id
    try:
        page_limit = int(message.text)
        STATE[chat_id]['page_limit'] = page_limit
        bot.reply_to(message, f"Page creation limit set to: {page_limit}")
    except ValueError:
        bot.reply_to(message, "Invalid input. Please enter a number.")
    STATE[chat_id]['awaiting_page_limit'] = False

@bot.message_handler(commands=['setdelay'])
def set_delay(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Please enter the delay in seconds between page registrations.")
    STATE[chat_id]['awaiting_delay'] = True

@bot.message_handler(func=lambda message: getattr(STATE.get(message.chat.id), 'awaiting_delay', False) == True)
def handle_delay(message):
    chat_id = message.chat.id
    try:
        delay = int(message.text)
        STATE[chat_id]['delay'] = delay
        bot.reply_to(message, f"Delay set to: {delay} seconds.")
    except ValueError:
        bot.reply_to(message, "Invalid input. Please enter a number.")
    STATE[chat_id]['awaiting_delay'] = False


@bot.message_handler(commands=['run'])
def run_registration(message):
    chat_id = message.chat.id
    state = STATE.get(chat_id)

    if not state or not state['cookies']:
        bot.reply_to(message, "Please add at least one cookie first using /addcookie.")
        return

    if not state['page_limit'] > 0:
        bot.reply_to(message, "Please set a page limit using /setpagelimit.")
        return

    if not state['delay'] > 0:
        bot.reply_to(message, "Please set a delay using /setdelay.")
        return

    cookies = state['cookies']
    images = state['images']
    upload_avatar = state['upload_avatar']
    page_limit = state['page_limit']
    delay = state['delay']

    global dem
    dem = 0

    bot.reply_to(message, "Starting page registration...")

    while True:
        for dulieuclone in cookies:
            cookie, name, uid, fb_dtsg, jazoest = dulieuclone.split('|')
            idpage = dpcutevcl.RegPage(cookie, name, uid, fb_dtsg, jazoest)

            if idpage:
                dem += 1
                bot.send_message(chat_id, f"Page Created! ID: {idpage}")

                if upload_avatar:
                    if images:
                        link_anh = random.choice(images)
                        up_result = dpcutevcl.UpAvt(cookie, idpage, link_anh)
                        if up_result:
                            bot.send_message(chat_id, f"Avatar uploaded successfully to page {idpage}")
                        else:
                            bot.send_message(chat_id, f"Failed to upload avatar to page {idpage}")
                    else:
                         bot.send_message(chat_id, "No images available to upload as avatar. Please add images using /addimage command.")
                dpcutevcl.ndp_delay_tool(delay)

                if dem >= page_limit:
                    bot.send_message(chat_id, f"Reached page limit ({page_limit}). Stopping.")
                    return
            else:
                bot.send_message(chat_id, "Page registration failed.")

        # Consider adding a break condition if you want to stop after processing all cookies once
        # break

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
    Available commands:
    /start - Start the bot and initialize settings.
    /addcookie - Add a Facebook cookie.
    /addimage - Add an image link for avatar upload.
    /setuploadavatar - Enable or disable avatar upload after page registration (yes/no).
    /setpagelimit - Set the number of pages to create before stopping.
    /setdelay - Set the delay in seconds between page registrations.
    /run - Start the page registration process.
    /help - Display this help message.
    """
    bot.send_message(message.chat.id, help_text)



# =========================== [ START TOOL ] ===========================
if __name__ == '__main__':
    bot.infinity_polling()