import random
import string
import requests
import os
import time
import logging
from http.client import HTTPException
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import secrets
from fake_useragent import UserAgent, FakeUserAgentError
import telebot
from telebot import types
import threading

# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
BOT_TOKEN = '7766543633:AAHd5v0ILieeJdpnRTCdh2RvzV1M8jli4uc'
bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

nglusername = None
spam_message = None
Count = None
delay = None
spamming = False
chat_id = None
message_id_to_edit = None

def tao_device_id():
    characters = string.ascii_lowercase + string.digits
    parts = [
        ''.join(random.choices(characters, k=8)),
        ''.join(random.choices(characters, k=4)),
        ''.join(random.choices(characters, k=4)),
        ''.join(random.choices(characters, k=4)),
        ''.join(random.choices(characters, k=12)),
    ]
    return f"{'-'.join(parts)}"

def lay_user_agent():
    try:
        ua = UserAgent()
        return ua.random
    except FakeUserAgentError as e:
        logging.error(f"Lỗi khi lấy User Agent: {e}")
        if chat_id:
            bot.send_message(chat_id, "Lỗi: Không thể lấy User Agent. Vui lòng kiểm tra kết nối mạng và cài đặt fake-useragent.")
        return None

def tao_session_retry():
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1,
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def random_headers():
    return {
        'Host': 'ngl.link',
        'sec-ch-ua': f'"{random.choice(["Google Chrome", "Mozilla Firefox", "Microsoft Edge"]) }";v="{random.randint(100,120)}", "Chromium";v="{random.randint(100,120)}", "Not-A.Brand";v="24"',
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'sec-ch-ua-mobile': '?0',
        'user-agent': f'{lay_user_agent()}',
        'sec-ch-ua-platform': f'"{random.choice(["Windows", "macOS", "Linux"])}"',
        'origin': 'https://ngl.link',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': f'https://ngl.link/{nglusername}',
        'accept-language': f'{random.choice(["en-US,en;q=0.9","tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7","es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7"])}',
        'x-forwarded-for': f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}'
    }


def gui_ngl_tin_nhan(session, nglusername, message):
    data = {
        'username': f'{nglusername}',
        'question': f'{message}',
        'deviceId': f'{tao_device_id()}',
        'gameSlug': '',
        'referrer': '',
        't': str(int(time.time() * 1000)),
        'r': secrets.token_urlsafe(16),
    }

    try:
        response = session.post('https://ngl.link/api/submit', headers=random_headers(), data=data, timeout=10)
        response.raise_for_status()
        return True, response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi Request: {e}")
        return False, f"Lỗi Request: {e}"
    except HTTPException as e:
        logging.error(f"Lỗi HTTP: {e}")
        return False, f"Lỗi HTTP: {e}"

def spam_ngl(chat_id):
    global nglusername, spam_message, Count, delay, spamming, message_id_to_edit

    session = tao_session_retry()
    value = 0
    notsend = 0
    start_time = time.time()

    while value < Count and spamming:
        success, result = gui_ngl_tin_nhan(session, nglusername, spam_message)

        if success:
            notsend = 0
            value += 1
            status_message = f"[+] Đã gửi => {value}/{Count}\n"
            status_message += f"Lỗi: {notsend}\n"
            status_message += f"Độ trễ: {delay}\n"
            elapsed_time = time.time() - start_time
            status_message += f"Thời gian đã trôi qua: {elapsed_time:.2f} giây"
            print(status_message)

            try:
                 bot.edit_message_text(chat_id=chat_id, message_id=message_id_to_edit, text=status_message)
            except telebot.apihelper.ApiTelegramException as e:
                logging.error(f"Lỗi khi chỉnh sửa tin nhắn: {e}")

        else:
            notsend += 1
            status_message = f"[-] Chưa gửi được, {result}\n"
            status_message += f"Lỗi: {notsend}\n"
            status_message += f"Độ trễ: {delay}\n"
            elapsed_time = time.time() - start_time
            status_message += f"Thời gian đã trôi qua: {elapsed_time:.2f} giây"
            print(status_message)

            try:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id_to_edit, text=status_message)
            except telebot.apihelper.ApiTelegramException as e:
                logging.error(f"Lỗi khi chỉnh sửa tin nhắn: {e}")
        if notsend == 4:
            status_message = "[!] Đang đổi thông tin..."
            print(status_message)
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id_to_edit, text=status_message)
            except telebot.apihelper.ApiTelegramException as e:
                logging.error(f"Lỗi khi chỉnh sửa tin nhắn: {e}")
            notsend = 0

        time.sleep(delay + random.uniform(0,0.5))

    if spamming:
        bot.send_message(chat_id, "Hoàn thành spam!")
    spamming = False
    message_id_to_edit = None


# Telegram Bot Handlers
@bot.message_handler(commands=['startngl'])
def start_command(message):
    global chat_id
    chat_id = message.chat.id
    bot.send_message(chat_id, "Chào mừng! Sử dụng /ngl để bắt đầu spam NGL hoặc /stop để dừng.")


@bot.message_handler(commands=['ngl'])
def ngl_command(message):
    global chat_id
    chat_id = message.chat.id

    if message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, "Lệnh /ngl không được hỗ trợ trong nhóm. Vui lòng chat riêng với bot để sử dụng.")
        return

    bot.send_message(chat_id, "Hãy nhập tên người dùng NGL:")
    bot.register_next_step_handler(message, get_username)

def get_username(message):
    global nglusername, chat_id
    chat_id = message.chat.id
    nglusername = message.text
    bot.send_message(chat_id, "Nhập nội dung tin nhắn:")
    bot.register_next_step_handler(message, get_message)

def get_message(message):
    global nglusername, spam_message, chat_id
    chat_id = message.chat.id
    spam_message = message.text
    bot.send_message(chat_id, "Nhập số lượng tin nhắn:")
    bot.register_next_step_handler(message, get_count)

def get_count(message):
    global nglusername, spam_message, Count, chat_id
    chat_id = message.chat.id
    try:
        Count = int(message.text)
        bot.send_message(chat_id, "Nhập độ trễ giữa các tin nhắn (0 để nhanh nhất):")
        bot.register_next_step_handler(message, get_delay)
    except ValueError:
        bot.send_message(chat_id, "Lỗi: Số lượng tin nhắn không hợp lệ. Vui lòng nhập một số.")
        bot.register_next_step_handler(message, get_count)

def get_delay(message):
    global nglusername, spam_message, Count, delay, chat_id
    chat_id = message.chat.id
    try:
        delay = float(message.text)
        if delay < 0:
            bot.send_message(chat_id, "Lỗi: Độ trễ không hợp lệ. Vui lòng nhập một số dương.")
            bot.register_next_step_handler(message, get_delay)
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        itembtn1 = types.KeyboardButton('Bắt đầu spam')
        itembtn2 = types.KeyboardButton('Hủy bỏ')
        markup.add(itembtn1, itembtn2)
        bot.send_message(chat_id, "Bạn có muốn bắt đầu spam không?", reply_markup=markup)
        bot.register_next_step_handler(message, confirm_spam)

    except ValueError:
        bot.send_message(chat_id, "Lỗi: Độ trễ không hợp lệ. Vui lòng nhập một số.")
        bot.register_next_step_handler(message, get_delay)

def confirm_spam(message):
    global spamming, chat_id, nglusername, spam_message, Count, delay, message_id_to_edit
    chat_id = message.chat.id
    if message.text == 'Bắt đầu spam':
        if not all([nglusername, spam_message, Count, delay is not None]):
            bot.send_message(chat_id, "Lỗi: Vui lòng sử dụng lệnh /ngl theo đúng cú pháp để cung cấp đủ thông tin.")
            spamming = False
            return

        spamming = True
        initial_message = bot.send_message(chat_id, "Bắt đầu spam...", reply_markup=types.ReplyKeyboardRemove())
        message_id_to_edit = initial_message.message_id

        spam_thread = threading.Thread(target=spam_ngl, args=(chat_id,))
        spam_thread.start()

    else:
        spamming = False
        bot.send_message(chat_id, "Đã hủy bỏ.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(commands=['stop'])
def stop_command(message):
    global spamming, chat_id
    chat_id = message.chat.id
    if spamming:
        spamming = False
        bot.send_message(chat_id, "Đã dừng spam.")
    else:
        bot.send_message(chat_id, "Không có tiến trình spam nào đang chạy.")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def default_command(message):
    global chat_id
    chat_id = message.chat.id

    # Only send the "invalid command" message in private chats
    if message.chat.type == 'private':
        bot.reply_to(message, "Lệnh không hợp lệ. Vui lòng sử dụng /ngl để bắt đầu hoặc /stop để dừng. Gõ /startngl để biết thêm thông tin.")

print("Bot NGL Spammer Telegram đã chạy")
bot.infinity_polling()