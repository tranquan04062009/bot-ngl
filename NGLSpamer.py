import sys
import os
import requests
import threading
import time
import json
import random
from time import strftime
import telebot
from telebot import types
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Replace with your Telegram bot token
BOT_TOKEN = "7766543633:AAHd5v0ILieeJdpnRTCdh2RvzV1M8jli4uc"  # Replace with your actual bot token
bot = telebot.TeleBot(BOT_TOKEN)

# Replace with your Telegram admin user ID. Use an integer.
ADMIN_USER_ID = 6940071938  # Example: Replace with your actual admin ID
ALLOWED_CHAT_IDS = [-1002370805497]  # Replace with a list of allowed group chat IDs.  Negative numbers are for groups/channels
#ALLOWED_CHAT_IDS = [6940071938]  # Example: Single user id, remove comment to use

USER_SHARE_LIMIT_PER_DAY = 5000
user_share_counts = {}  # Keep track of shares per user per day
DATA_RETENTION_TIME = 3600  # 1 hour in seconds (adjust as needed)

# Improved User Agent Rotation (including mobile devices)
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.2210.144",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.259 Mobile Safari/537.36"
]

# Global stop flag for each chat
stop_sharing_flags = {}
successful_shares = {}  # Track successful shares per chat
token_status = {}  # Track status of each token
gome_token = []

# Proxy rotation (replace with your proxy list/source)
proxies = [
    None  # Direct connection. Leave this EVEN if using proxies!
]

# Session Management
token_sessions = {}  # Store requests.Session() objects for each token

# Rate limiting settings (adaptive)
BASE_REQUESTS_PER_MINUTE = 30  # Starting point. Adjust!
REQUESTS_PER_MINUTE_VARIATION = 10  # Add some randomness
request_timestamps = {}  # per token rate limiting

# Data timestamp for cleanup
data_timestamps = {}

# Tracking when to send the final report
report_sent = {}

# Constant for "Cancel" and "Stop Share" callback data
CANCEL_CALLBACK_DATA = "cancel_input"
STOP_SHARE_CALLBACK_DATA = "stop_share"

# Dictionary to store the initiator user ID per chat ID
initiator_user_ids = {}

# Dictionary to store message IDs for inline keyboards.
keyboard_message_ids = {}


def get_random_proxy():
    return random.choice(proxies)


def clear():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')


# Function to enforce rate limiting (adaptive per token)
def rate_limit(token):
    if token not in request_timestamps:
        request_timestamps[token] = []  # init list for that token

    current_time = time.time()
    while request_timestamps[token] and request_timestamps[token][0] <= current_time - 60:
        request_timestamps[token].pop(0)

    # Adaptive Rate Limiting: Adjust based on success
    if token_status.get(token, "live") == "live":
        requests_per_minute = BASE_REQUESTS_PER_MINUTE + random.randint(-REQUESTS_PER_MINUTE_VARIATION,
                                                                          REQUESTS_PER_MINUTE_VARIATION)
    else:  # slow down failing tokens.
        requests_per_minute = BASE_REQUESTS_PER_MINUTE // 2 + random.randint(-REQUESTS_PER_MINUTE_VARIATION // 2,
                                                                              REQUESTS_PER_MINUTE_VARIATION // 2)

    if len(request_timestamps[token]) >= requests_per_minute:
        sleep_time = 60 - (current_time - request_timestamps[token][0])
        time.sleep(max(0, sleep_time))  # Ensure sleep time is not negative

    request_timestamps[token].append(current_time)


# Generate a random device ID (UUID4)
def generate_device_id():
    return str(uuid.uuid4())


# Robust Header Generation Function
def generate_headers(cookie, device_id):
    user_agent = random.choice(user_agents)
    accept_language = random.choice([
        "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "en-US,en;q=0.9",
        "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
    ])  # Vary language preferences

    headers = {
        'authority': 'business.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': accept_language,
        'cache-control': 'max-age=0',
        'cookie': cookie,
        'referer': 'https://www.facebook.com/',
        'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
        'x-fb-device-group': '4481',  # Add realistic Facebook headers
        'x-fb-friendly-name': 'ViewerBookmarksListQuery',
        'x-fb-http-engine': 'Liger'
    }
    return headers


def get_token(input_file, chat_id, user_id):
    global gome_token
    gome_token = []
    user_key = (chat_id, user_id)

    for cookie in input_file:
        cookie = cookie.strip()
        if not cookie:
            continue

        device_id = generate_device_id()
        headers = generate_headers(cookie, device_id)
        cookie_token = f'{cookie}|None|{device_id}'  # initial value. None represents the absence of token at this time
        try:
            session = requests.Session()  # Create a new session for each token
            token_sessions[cookie_token] = session  # store session in a dictionary indexed by "cookie|device_id"

            rate_limit(cookie_token)  # Rate limit token retrieval.
            response = session.get('https://business.facebook.com/content_management', headers=headers, timeout=15,
                                   proxies={'http': get_random_proxy(),
                                            'https': get_random_proxy()})  # Use session
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            home_business = response.text
            if 'EAAG' in home_business:
                token = home_business.split('EAAG')[1].split('","')[0]
                cookie_token = f'{cookie}|EAAG{token}|{device_id}'
                gome_token.append(cookie_token)
                token_status[cookie_token] = "live"
            else:
                token_status[cookie_token] = "die"  # status die at token retrieval
                logging.warning(
                    f"[!] User {user_id} - Không thể lấy token từ cookie: {cookie[:50]}... Cookie có thể không hợp lệ.")
                bot.send_message(chat_id, f"Không thể lấy token từ cookie: {cookie[:50]}... Cookie có thể không hợp lệ.")

        except requests.exceptions.RequestException as e:
            token_status[cookie_token] = "die"
            logging.error(f"[!] User {user_id} - Lỗi khi lấy token cho cookie: {cookie[:50]}... {e}")
            bot.send_message(chat_id, f"Lỗi khi lấy token cho cookie: {cookie[:50]}... Dừng tool.")
            stop_sharing_flags[user_key] = True
            if cookie_token in token_sessions:
                token_sessions[cookie_token].close()
                del token_sessions[cookie_token]
            cleanup_data(chat_id, user_id)  # Cleanup on error
            return []  # Stop immediately

        except Exception as e:
            token_status[cookie_token] = "die"
            logging.exception(
                f"[!] User {user_id} - Lỗi không mong muốn khi lấy token cho cookie: {cookie[:50]}... {e}")
            bot.send_message(chat_id, f"Lỗi không mong muốn khi lấy token cho cookie: {cookie[:50]}... Dừng tool.")
            stop_sharing_flags[user_key] = True
            if cookie_token in token_sessions:
                token_sessions[cookie_token].close()
                del token_sessions[cookie_token]
            cleanup_data(chat_id, user_id)  # Cleanup on error
            return []  # Stop immediately

    return gome_token


def share(tach, id_share, chat_id, user_id):
    cookie = tach.split('|')[0]
    token = tach.split('|')[1]
    device_id = tach.split('|')[2]  # Get device ID from token
    headers = generate_headers(cookie, device_id)  # consistent headers
    user_key = (chat_id, user_id)

    session = token_sessions.get(tach)  # Get the session object.

    if not session:  # should never happen but just in case
        logging.warning(
            f"User {user_id} - No session found for token: {tach[:50]}. Creating new session (this is unexpected)")
        session = requests.Session()  # create ad hoc, but this should be fixed
        token_sessions[tach] = session  # save adhoc

    try:
        rate_limit(tach)  # Rate Limit per token

        data = {'link': f'https://m.facebook.com/{id_share}', 'published': '0', 'access_token': token,
                'device_id': device_id}
        response = session.post(f'https://graph.facebook.com/me/feed', headers=headers, data=data, timeout=10,
                                proxies={'http': get_random_proxy(), 'https': get_random_proxy()})
        response.raise_for_status()  # check for HTTP errors
        res = response.json()

        if 'id' in res:
            token_status[tach] = "live"  # Share was success. Keep it live.
            return True
        else:
            token_status[tach] = "die"  # Token is dead
            logging.warning(f"User {user_id} - [!] Share thất bại: ID: {id_share} - Token Die - Phản hồi: {res}")
            # bot.send_message(chat_id, f"[!] Share thất bại: ID: {id_share} - Token Die - Dừng tool.") # No longer send message on each failure
            stop_sharing_flags[user_key] = True
            return False

    except requests.exceptions.RequestException as e:
        token_status[tach] = "die"
        logging.error(f"User {user_id} - [!] Lỗi request share: ID: {id_share} - {e}")
        # bot.send_message(chat_id, f"[!] Lỗi request share: ID: {id_share} - {e} - Dừng tool.") # No longer send message on each failure
        stop_sharing_flags[user_key] = True
        return False

    except Exception as e:
        token_status[tach] = "die"
        logging.exception(f"User {user_id} - [!] Lỗi không mong muốn khi share: ID: {id_share} - {e}")
        # bot.send_message(chat_id, f"[!] Lỗi không mong muốn khi share: ID: {id_share} - {e} - Dừng tool.") # No longer send message on each failure
        stop_sharing_flags[user_key] = True
        return False


def share_thread_telegram(tach, id_share, stt, chat_id, user_id):  # Remove message_id as it is no longer used
    user_key = (chat_id, user_id)
    if stop_sharing_flags.get(user_key, False):
        return False  # Stop sharing
    if share(tach, id_share, chat_id, user_id):
        # Update successful share count
        successful_shares[user_key] = successful_shares.get(user_key, 0) + 1  # Increase share count for that chat
        return True
    else:
        return False


# Telegram Bot Handlers
share_data = {}  # Store user-specific data


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_key = (chat_id, user_id)

    if chat_id not in ALLOWED_CHAT_IDS and message.chat.type != 'private':
        bot.reply_to(message, "Xin lỗi, bot này chỉ hoạt động trong các nhóm được cho phép.")
        return

    if message.chat.type == 'private' and chat_id not in ALLOWED_CHAT_IDS:
        bot.reply_to(message, "Xin lỗi, bot này không hỗ trợ chat riêng. Hãy sử dụng nó trong nhóm được cho phép.")
        return

    bot.reply_to(message, "Chào mừng! Sử dụng /share để bắt đầu.")


@bot.message_handler(commands=['share'])
def share_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_key = (chat_id, user_id)

    # Check if the bot is used outside allowed chat IDs
    if chat_id not in ALLOWED_CHAT_IDS and message.chat.type != 'private':
        bot.reply_to(message, "Xin lỗi, bot này chỉ hoạt động trong các nhóm được cho phép.")
        return

    if message.chat.type == 'private' and chat_id not in ALLOWED_CHAT_IDS:
        bot.reply_to(message, "Xin lỗi, bot này không hỗ trợ chat riêng. Hãy sử dụng nó trong nhóm được cho phép.")
        return

    share_data[user_key] = {}  # Initialize data for the user
    successful_shares[user_key] = 0  # Initialize the share counter
    report_sent[user_key] = False  # Initialize report_sent flag

    # Update data timestamp
    update_data_timestamp(chat_id, user_id)

    # Check user's daily share count
    today = strftime("%Y-%m-%d")
    if user_id not in user_share_counts:
        user_share_counts[user_id] = {}
    if today not in user_share_counts[user_id]:
        user_share_counts[user_id][today] = 0

    if user_id != ADMIN_USER_ID and user_share_counts[user_id][today] >= USER_SHARE_LIMIT_PER_DAY:
        bot.send_message(chat_id,
                         f"Bạn đã đạt giới hạn {USER_SHARE_LIMIT_PER_DAY} share hôm nay. Vui lòng thử lại vào ngày mai.")
        return

    # Display link and other information
    bot.send_message(chat_id,
                     "Thông tin bot:\n- Bot này được phát triển bởi [Trần Quân/SecPhiPhai]\n- Hỗ trợ share bài viết trang cá nhân.\n- Liên hệ: [0376841471] \n- [https://linktr.ee/tranquan46]")

    # Create a stop button
    markup = types.InlineKeyboardMarkup()
    stop_button = types.InlineKeyboardButton("Dừng Share", callback_data=STOP_SHARE_CALLBACK_DATA)
    cancel_button = types.InlineKeyboardButton("Huỷ", callback_data=CANCEL_CALLBACK_DATA)  # Add cancel button
    markup.add(stop_button, cancel_button)  # Add both buttons in the same row

    # Store the message ID of the inline keyboard to allow editing later
    message_obj = bot.send_message(chat_id, "Vui lòng gửi file chứa cookie (cookies.txt).", reply_markup=markup)
    keyboard_message_ids[user_key] = message_obj.message_id

    # Store the user_id who started the /share command
    # Use the chat_id as the key
    initiator_user_ids[chat_id] = user_id

    bot.register_next_step_handler(message, process_cookie_file)


@bot.callback_query_handler(func=lambda call: call.data == STOP_SHARE_CALLBACK_DATA)
def stop_share_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_key = (chat_id, user_id)

    # Only allow the admin or the user who initiated the /share command to stop the sharing
    if user_id == ADMIN_USER_ID or (chat_id in initiator_user_ids and initiator_user_ids[chat_id] == user_id):
        stop_sharing_flags[user_key] = True  # Set the stop flag
        bot.send_message(chat_id, "Đã nhận lệnh dừng share. Vui lòng chờ quá trình hoàn tất.")
        global gome_token
        gome_token.clear()

        # close sessions (cleanup resources)
        global token_sessions
        for session in token_sessions.values():
            session.close()
        token_sessions = {}  # reset

        cleanup_data(chat_id, user_id)  # Cleanup when stopped
        remove_inline_keyboard(chat_id, user_id) # Remove the inline keyboard
    else:
        bot.answer_callback_query(call.id, "Bạn không có quyền dừng quá trình này.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == CANCEL_CALLBACK_DATA)
def cancel_input_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_key = (chat_id, user_id)

    # Check if the user who pressed the button is the same user who initiated the /share command.
    if chat_id in initiator_user_ids and initiator_user_ids[chat_id] == user_id:
        bot.send_message(chat_id, "Đã huỷ. Bạn có thể bắt đầu lại bằng lệnh /share.")
        cleanup_data(chat_id, user_id)

        # Remove the inline keyboard
        remove_inline_keyboard(chat_id, user_id)

        # Remove the initiator user ID for this chat
        if chat_id in initiator_user_ids:
            del initiator_user_ids[chat_id]
    else:
        bot.answer_callback_query(call.id, "Bạn không có quyền huỷ quá trình này.", show_alert=True)


def process_cookie_file(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_key = (chat_id, user_id)

    # Check if the user sent a callback query (from the inline keyboard) instead of a file.
    if message.content_type == 'text' and message.text == "/share":
        # User restarted the process. Clean up the data.
        cleanup_data(chat_id, user_id)
        return  # stop processing this request

    try:
        if message.document is None:
            # Check for a "cancel" message
            if message.text and message.text.lower() == "cancel":
                # Check the initiator
                if chat_id in initiator_user_ids and initiator_user_ids[chat_id] == user_id:
                    bot.send_message(chat_id, "Đã huỷ. Bạn có thể bắt đầu lại bằng lệnh /share.")
                    cleanup_data(chat_id, user_id)
                    # Remove the initiator user ID for this chat
                    if chat_id in initiator_user_ids:
                        del initiator_user_ids[chat_id]
                    return
                else:
                    bot.send_message(chat_id, "Bạn không có quyền huỷ quá trình này.")
                    return

            bot.reply_to(message, "Vui lòng gửi file chứa cookie (cookies.txt).")
            return

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_content = downloaded_file.decode('utf-8').splitlines()
        share_data[user_key]['cookie_file'] = file_content
        update_data_timestamp(chat_id, user_id)

        # Delete the message containing the cookie file
        bot.delete_message(chat_id, message.message_id)

        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("Huỷ", callback_data=CANCEL_CALLBACK_DATA)  # Add cancel button
        markup.add(cancel_button)

        # Store the message ID of the inline keyboard to allow editing later
        message_obj = bot.send_message(chat_id, "Đã nhận file cookie. Vui lòng nhập ID bài viết cần share.", reply_markup=markup)
        keyboard_message_ids[user_key] = message_obj.message_id

        bot.register_next_step_handler(message, process_id)
    except Exception as e:
        logging.exception(f"User {user_id} - Error processing file for chat_id {chat_id}: {e}")
        bot.reply_to(message, "Lỗi xử lý file cookie. Vui lòng thử lại.")  # User-friendly message
        cleanup_data(chat_id, user_id)  # Clear data
        remove_inline_keyboard(chat_id, user_id)  # Remove the inline keyboard


def process_id(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_key = (chat_id, user_id)

    # Check if the user sent a callback query (from the inline keyboard) instead of a file.
    if message.content_type == 'text' and message.text == "/share":
        # User restarted the process. Clean up the data.
        cleanup_data(chat_id, user_id)
        return  # stop processing this request

    try:
        id_share = message.text.strip()
        if not id_share.isdigit():
            # Check for a "cancel" message
            if message.text and message.text.lower() == "cancel":
                if chat_id in initiator_user_ids and initiator_user_ids[chat_id] == user_id:
                    bot.send_message(chat_id, "Đã huỷ. Bạn có thể bắt đầu lại bằng lệnh /share.")
                    cleanup_data(chat_id, user_id)
                    # Remove the initiator user ID for this chat
                    if chat_id in initiator_user_ids:
                        del initiator_user_ids[chat_id]
                    return
                else:
                    bot.send_message(chat_id, "Bạn không có quyền huỷ quá trình này.")
                    return

            bot.reply_to(message, "ID không hợp lệ. Vui lòng nhập lại ID bài viết cần share.")
            bot.register_next_step_handler(message, process_id)
            return

        share_data[user_key]['id_share'] = id_share
        update_data_timestamp(chat_id, user_id)
        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("Huỷ", callback_data=CANCEL_CALLBACK_DATA)  # Add cancel button
        markup.add(cancel_button)

        # Store the message ID of the inline keyboard to allow editing later
        message_obj = bot.send_message(chat_id, "Vui lòng nhập delay giữa các lần share (giây).", reply_markup=markup)
        keyboard_message_ids[user_key] = message_obj.message_id
        bot.register_next_step_handler(message, process_delay)
    except Exception as e:
        logging.exception(f"User {user_id} - Error processing ID for chat_id {chat_id}: {e}")
        bot.reply_to(message, "Lỗi xử lý ID. Vui lòng thử lại.")  # User-friendly message
        cleanup_data(chat_id, user_id)  # Clear data
        remove_inline_keyboard(chat_id, user_id)  # Remove the inline keyboard


def process_delay(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_key = (chat_id, user_id)
    # Check if the user sent a callback query (from the inline keyboard) instead of a file.
    if message.content_type == 'text' and message.text == "/share":
        # User restarted the process. Clean up the data.
        cleanup_data(chat_id, user_id)
        return  # stop processing this request
    try:
        delay_str = message.text.strip()
        try:
            delay = int(delay_str)
            if delay < 0:
                raise ValueError
        except ValueError:
            # Check for a "cancel" message
            if message.text and message.text.lower() == "cancel":
                if chat_id in initiator_user_ids and initiator_user_ids[chat_id] == user_id:
                    bot.send_message(chat_id, "Đã huỷ. Bạn có thể bắt đầu lại bằng lệnh /share.")
                    cleanup_data(chat_id, user_id)
                    # Remove the initiator user ID for this chat
                    if chat_id in initiator_user_ids:
                        del initiator_user_ids[chat_id]
                    return
                else:
                    bot.send_message(chat_id, "Bạn không có quyền huỷ quá trình này.")
                    return
            bot.reply_to(message, "Delay không hợp lệ. Vui lòng nhập lại delay (giây) là một số dương.")
            bot.register_next_step_handler(message, process_delay)
            return

        share_data[user_key]['delay'] = delay
        update_data_timestamp(chat_id, user_id)
        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("Huỷ", callback_data=CANCEL_CALLBACK_DATA)  # Add cancel button
        markup.add(cancel_button)

        # Store the message ID of the inline keyboard to allow editing later
        message_obj = bot.send_message(chat_id, "Vui lòng nhập tổng số lượng share (0 để không giới hạn).", reply_markup=markup)
        keyboard_message_ids[user_key] = message_obj.message_id
        bot.register_next_step_handler(message, process_total_shares)

    except Exception as e:
        logging.exception(f"User {user_id} - Error processing delay for chat_id {chat_id}: {e}")
        bot.reply_to(message, "Lỗi xử lý delay. Vui lòng thử lại.")  # User-friendly message
        cleanup_data(chat_id, user_id)  # Clear data
        remove_inline_keyboard(chat_id, user_id)  # Remove the inline keyboard


def process_total_shares(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_key = (chat_id, user_id)
    # Check if the user sent a callback query (from the inline keyboard) instead of a file.
    if message.content_type == 'text' and message.text == "/share":
        # User restarted the process. Clean up the data.
        cleanup_data(chat_id, user_id)
        return  # stop processing this request

    try:
        total_share_limit_str = message.text.strip()
        try:
            total_share_limit = int(total_share_limit_str)
            if total_share_limit < 0:
                raise ValueError
        except ValueError:
            # Check for a "cancel" message
            if message.text and message.text.lower() == "cancel":
                if chat_id in initiator_user_ids and initiator_user_ids[chat_id] == user_id:
                    bot.send_message(chat_id, "Đã huỷ. Bạn có thể bắt đầu lại bằng lệnh /share.")
                    cleanup_data(chat_id, user_id)
                    # Remove the initiator user ID for this chat
                    if chat_id in initiator_user_ids:
                        del initiator_user_ids[chat_id]
                    return
                else:
                    bot.send_message(chat_id, "Bạn không có quyền huỷ quá trình này.")
                    return
            bot.reply_to(message,
                         "Số lượng share không hợp lệ. Vui lòng nhập lại tổng số lượng share (0 để không giới hạn) là một số dương.")
            bot.register_next_step_handler(message, process_total_shares)
            return

        share_data[user_key]['total_share_limit'] = total_share_limit
        update_data_timestamp(chat_id, user_id)

        # Limit total shares based on user role
        if user_id != ADMIN_USER_ID and total_share_limit > USER_SHARE_LIMIT_PER_DAY:
            total_share_limit = USER_SHARE_LIMIT_PER_DAY
            bot.send_message(chat_id,
                             f"Bạn không phải là admin. Số lượng share sẽ bị giới hạn ở mức {USER_SHARE_LIMIT_PER_DAY}.")
            share_data[user_key]['total_share_limit'] = total_share_limit

        start_sharing(chat_id, user_id,
                      message.from_user.username)  # Pass user_id and username to start_sharing
    except Exception as e:
        logging.exception(f"User {user_id} - Error processing total shares for chat_id {chat_id}: {e}")
        bot.reply_to(message, "Lỗi xử lý số lượng share. Vui lòng thử lại.")  # User-friendly message
        cleanup_data(chat_id, user_id)  # Clear data
        remove_inline_keyboard(chat_id, user_id)  # Remove the inline keyboard


def start_sharing(chat_id, user_id, username):
    user_key = (chat_id, user_id)
    data = share_data.get(user_key)

    if not data:
        bot.send_message(chat_id, "Dữ liệu không đầy đủ. Vui lòng bắt đầu lại bằng lệnh /share.")
        return

    input_file = data['cookie_file']
    id_share = data['id_share']
    delay = data['delay']
    total_share_limit = data['total_share_limit']

        # Get tokens, stop if fails
    all_tokens = get_token(input_file, chat_id, user_id)
    if not all_tokens:
        # get_token already sent a message to the user
        cleanup_data(chat_id, user_id)
        return

    total_live = len(all_tokens)

    if total_live == 0:
        bot.send_message(chat_id, "Không tìm thấy token hợp lệ nào.")
        cleanup_data(chat_id, user_id)
        return

    bot.send_message(chat_id, f"Tìm thấy {total_live} token hợp lệ.")

    # Send initial message with share success count and store its ID
    markup = types.InlineKeyboardMarkup()
    stop_button = types.InlineKeyboardButton("Dừng Share", callback_data=STOP_SHARE_CALLBACK_DATA)
    markup.add(stop_button)
    message_obj = bot.send_message(chat_id, "Bắt đầu share...", reply_markup=markup)  # Simplified starting message.  Removed the counter update
    keyboard_message_ids[user_key] = message_obj.message_id

    stt = 0
    shared_count = 0
    # global successful_shares #No longer global. Use the one defined per chat_id
    successful_shares[user_key] = 0  # Reset successful shares count for this chat_id
    continue_sharing = True
    stop_sharing_flags[user_key] = False  # Reset stop flag at start
    report_sent[user_key] = False  # Ensure the report will be sent if total_share_limit is reached.

    while continue_sharing:
        for tach in all_tokens:
            if stop_sharing_flags.get(user_key, False):
                continue_sharing = False
                break  # Exit inner loop

            # Daily Limit Check inside the loop
            today = strftime("%Y-%m-%d")
            if user_id != ADMIN_USER_ID and user_share_counts[user_id][today] >= USER_SHARE_LIMIT_PER_DAY:
                bot.send_message(chat_id,
                                 f"Bạn đã đạt giới hạn {USER_SHARE_LIMIT_PER_DAY} share hôm nay. Vui lòng thử lại vào ngày mai.")
                continue_sharing = False
                break

            if token_status.get(tach, "live") == "die":  # Skip dead tokens
                continue

            stt += 1
            thread = threading.Thread(target=process_share,
                                      args=(tach, id_share, stt, chat_id, user_id, username))  # Removed message_id
            thread.start()
            time.sleep(delay)
            shared_count += 1

            if total_share_limit > 0 and shared_count >= total_share_limit:
                continue_sharing = False
                break

            if stop_sharing_flags.get(user_key, False):
                continue_sharing = False
                break

    for thread in threading.enumerate():
        if thread != threading.current_thread():
            thread.join()

    # Send final report if not already sent
    if not report_sent.get(user_key, False):
        send_final_report(chat_id, user_id, username)

    cleanup_data(chat_id, user_id)
    global gome_token
    gome_token.clear()
    stop_sharing_flags[user_key] = False  # Reset

    # Cleanup sessions
    global token_sessions
    for session in token_sessions.values():
        try:
            session.close()
        except Exception as e:
            logging.exception(f"User {user_id} - Error closing session: {e}")
    token_sessions = {}  # Reset
    remove_inline_keyboard(chat_id, user_id) # Remove the inline keyboard after finished or stopped


def process_share(tach, id_share, stt, chat_id, user_id, username):  # Removed message_id argument
    user_key = (chat_id, user_id)
    # global successful_shares #No longer global, each chat_id has it's counter
    global user_share_counts  # access global variable

    if stop_sharing_flags.get(user_key, False):
        return  # Stop immediately

    success = share_thread_telegram(tach, id_share, stt, chat_id, user_id)  # Removed message_id argument
    if not success:
        # share() function handles stopping when share fails
        return

    # Update daily share count
    today = strftime("%Y-%m-%d")
    if user_id not in user_share_counts:
        user_share_counts[user_id] = {}
    if today not in user_share_counts[user_id]:
        user_share_counts[user_id][today] = 0
    user_share_counts[user_id][today] += 1

    # Check if total_share_limit is reached, and if it is, send the final report and set the flag
    if share_data[user_key]['total_share_limit'] > 0 and successful_shares[user_key] >= share_data[user_key][
        'total_share_limit'] and not report_sent.get(user_key, False):
        send_final_report(chat_id, user_id, username)


def send_final_report(chat_id, user_id, username):
    user_key = (chat_id, user_id)
    bot.send_message(chat_id, "Quá trình share hoàn tất.")
    if share_data[user_key]['total_share_limit'] > 0 and successful_shares[user_key] >= share_data[user_key][
        'total_share_limit']:
        bot.send_message(chat_id, f"Đạt giới hạn share là {share_data[user_key]['total_share_limit']} shares.")
    bot.send_message(chat_id, f"@{username}, Tổng cộng {successful_shares[user_key]} share thành công.")  # Final count message.  Use username instead of first_name + last_name
    report_sent[user_key] = True  # Set the flag to prevent duplicate reports


def update_data_timestamp(chat_id, user_id):
    user_key = (chat_id, user_id)
    data_timestamps[user_key] = time.time()

# Function to remove the inline keyboard
def remove_inline_keyboard(chat_id, user_id):
    user_key = (chat_id, user_id)
    if user_key in keyboard_message_ids:
        try:
            bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=keyboard_message_ids[user_key],
                reply_markup=None  # Remove the keyboard
            )
            del keyboard_message_ids[user_key]  # Clean up the stored message ID
        except Exception as e:
            logging.exception(f"User {user_id} - Error removing inline keyboard: {e}")

def cleanup_data(chat_id, user_id):
    user_key = (chat_id, user_id)
    global share_data, user_share_counts, request_timestamps, token_sessions, successful_shares, report_sent, initiator_user_ids

    logging.info(f"User {user_id} - Cleaning up data for chat_id: {chat_id}")

    # Clear data specific to the user_key
    if user_key in share_data:
        del share_data[user_key]
    if user_key in stop_sharing_flags:
        del stop_sharing_flags[user_key]
    if user_key in successful_shares:
        del successful_shares[user_key]  # Delete successful share counter
    if user_key in report_sent:
        del report_sent[user_key]

    # Clean up token related data. This part needs extra attention to avoid unintended consequences.
    # Iterate through token_sessions and check if the token is associated with the user.
    tokens_to_remove = [token for token in token_sessions if token.startswith(f'{user_key}')]  # Safer check
    for token in tokens_to_remove:
        if token in token_sessions:
            try:
                token_sessions[token].close()
            except Exception as e:
                logging.exception(f"User {user_id} - Error closing session for token {token}: {e}")
            del token_sessions[token]
        if token in request_timestamps:
            del request_timestamps[token]
        if token in token_status:
            del token_status[token]

    # Remove timestamp
    if user_key in data_timestamps:
        del data_timestamps[user_key]

     # Remove the initiator user ID for this chat
    if chat_id in initiator_user_ids:
        del initiator_user_ids[chat_id]

    # Remove message id for inline keyboard
    if user_key in keyboard_message_ids:
        del keyboard_message_ids[user_key]


def periodic_cleanup():
    while True:
        current_time = time.time()
        keys_to_cleanup = [
            user_key for user_key, timestamp in data_timestamps.items()
            if current_time - timestamp > DATA_RETENTION_TIME
        ]

        for user_key in keys_to_cleanup:
            chat_id, user_id = user_key  # unpack
            logging.info(f"User {user_id} - Data retention time exceeded for chat_id: {chat_id}. Cleaning up.")
            cleanup_data(chat_id, user_id)

        time.sleep(150)  # Check every 5 minutes


if __name__ == "__main__":
    try:
        # Start the periodic cleanup thread
        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()

        print("Bot is running...")
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Bot stopped.")
        sys.exit()