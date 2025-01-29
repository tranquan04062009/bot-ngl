import telebot
import requests
import json
import time
import threading
from collections import defaultdict

# ================= CONFIGURATION =================
BOT_TOKEN = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo"  # Replace with your actual bot token
API_URL = "https://freefireinfoapiv2lk-team.vercel.app/send_like?uid={UID}&server={region}"
MAX_THREADS = 10  # Maximum number of threads for processing requests
REQUEST_DELAY = 1  # Delay between API requests in seconds
COOLDOWN_TIME = 30  # Cooldown time for users in seconds
ADMIN_USER_ID = 123456789  # Replace with your Telegram user ID
# ================================================


bot = telebot.TeleBot(BOT_TOKEN)
user_cooldowns = defaultdict(float)
request_queue = []
queue_lock = threading.Lock()
thread_pool = []


def send_like(uid, region):
    url = API_URL.format(UID=uid, region=region)
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data and data.get("status") == "success":
            return True, data.get("message")
        else:
             return False, data.get("message", "Unknown Error")
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"


def process_queue():
    global request_queue
    while True:
        with queue_lock:
            if not request_queue:
                time.sleep(0.1)
                continue
            chat_id, uid, region = request_queue.pop(0)

        result, message = send_like(uid, region)
        if result:
            bot.send_message(
                chat_id, f"Đã gửi like thành công cho UID {uid}, Server {region}. Message: {message}"
            )
        else:
            bot.send_message(
                 chat_id, f"Lỗi khi gửi like cho UID {uid}, Server {region}. Message: {message}"
             )
        time.sleep(REQUEST_DELAY)


def is_admin(user_id):
    return user_id == ADMIN_USER_ID

@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(
        message.chat.id,
        "Chào mừng bạn đến với bot tăng like Free Fire! Sử dụng /like [UID] [Server] để bắt đầu.",
    )

@bot.message_handler(commands=["help"])
def handle_help(message):
    bot.send_message(
        message.chat.id,
         "Để sử dụng bot, hãy gửi lệnh /like [UID] [Server]. Ví dụ: /like 123456789 vn.\n"
         "Bot sẽ xử lý yêu cầu và thông báo kết quả. Mỗi người dùng sẽ có thời gian chờ giữa các lần sử dụng."
    )

@bot.message_handler(commands=["admin"])
def handle_admin(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.send_message(message.chat.id, "Bạn không có quyền admin.")
        return
    bot.send_message(message.chat.id, "Admin commands here soon...")


@bot.message_handler(commands=["like"])
def handle_like(message):
    user_id = message.from_user.id
    if user_id not in user_cooldowns or (time.time() - user_cooldowns[user_id] >= COOLDOWN_TIME):
        try:
            parts = message.text.split()
            if len(parts) != 3:
               bot.send_message(message.chat.id, "Lệnh không hợp lệ. Vui lòng sử dụng /like [UID] [Server]")
               return
            uid = parts[1]
            region = parts[2]

            if not uid.isdigit():
                bot.send_message(message.chat.id, "UID phải là một số.")
                return

            if region not in ["vn", "sg", "th", "id", "br", "na", "eu", "latam","me", "in"]:
               bot.send_message(message.chat.id, "Server không hợp lệ. Vui lòng chọn một trong các server: vn, sg, th, id, br, na, eu, latam, me, in.")
               return

            with queue_lock:
                request_queue.append((message.chat.id, uid, region))
            user_cooldowns[user_id] = time.time()
            bot.send_message(message.chat.id, "Yêu cầu của bạn đã được đưa vào hàng đợi.")
        except Exception as e:
              bot.send_message(message.chat.id, f"Lỗi xử lý lệnh: {str(e)}")
    else:
        remaining = int(COOLDOWN_TIME - (time.time() - user_cooldowns[user_id]))
        bot.send_message(
            message.chat.id, f"Vui lòng đợi {remaining} giây trước khi thực hiện lại."
        )

if __name__ == "__main__":
    for _ in range(MAX_THREADS):
        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start()
        thread_pool.append(thread)
    bot.polling(non_stop=True)