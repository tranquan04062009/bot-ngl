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

# Replace with your Telegram bot token
BOT_TOKEN = "7766543633:AAHd5v0ILieeJdpnRTCdh2RvzV1M8jli4uc"  # REPLACE
bot = telebot.TeleBot(BOT_TOKEN)

# Replace with your Telegram admin user ID.  Use an integer.
ADMIN_USER_ID = 6940071938  # Example: Replace with your actual admin ID

USER_SHARE_LIMIT_PER_DAY = 10000
user_share_counts = {}  # Keep track of shares per user per day

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
successful_shares = 0  # Global variable to track successful shares
token_status = {}  # Track status of each token
gome_token = []

# Proxy rotation (replace with your proxy list/source)
proxies = [
    None  # Direct connection. Leave this EVEN if using proxies!
    # "http://user:pass@proxy1.example.com:8080",
    # "http://user:pass@proxy2.example.com:8080",
    # ... Add your proxies here
]

# Session Management
token_sessions = {}  # Store requests.Session() objects for each token

# Rate limiting settings (adaptive)
BASE_REQUESTS_PER_MINUTE = 30  # Starting point.  Adjust!
REQUESTS_PER_MINUTE_VARIATION = 10  # Add some randomness
request_timestamps = {}  # per token rate limiting


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


def get_token(input_file, chat_id):
    global gome_token
    gome_token = []
    for cookie in input_file:
        cookie = cookie.strip()
        if not cookie:
            continue

        device_id = generate_device_id()
        headers = generate_headers(cookie, device_id)
        cookie_token = f'{cookie}|None|{device_id}'  # initial value.  None represents the absence of token.
        try:
            session = requests.Session()  # Create a new session for each token
            token_sessions[cookie_token] = session  # store session

            rate_limit(cookie_token)  # Rate limit token retrieval.
            response = session.get('https://business.facebook.com/content_management', headers=headers, timeout=15,
                                   proxies={'http': get_random_proxy(), 'https': get_random_proxy()})  # Use session
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            home_business = response.text
            if 'EAAG' in home_business:
                token = home_business.split('EAAG')[1].split('","')[0]
                cookie_token = f'{cookie}|EAAG{token}|{device_id}'
                gome_token.append(cookie_token)
                token_status[cookie_token] = "live"
            else:
                token_status[cookie_token] = "die"  # status die at token retrieval
                print(f"[!] Không thể lấy token từ cookie: {cookie[:50]}... Cookie có thể không hợp lệ.")

        except requests.exceptions.RequestException as e:
            token_status[cookie_token] = "die"
            print(f"[!] Lỗi khi lấy token cho cookie: {cookie[:50]}... {e}")
            bot.send_message(chat_id, f"Lỗi khi lấy token cho cookie: {cookie[:50]}... Dừng tool.")
            stop_sharing_flags[chat_id] = True
            #  Close session on error
            if cookie_token in token_sessions:
                token_sessions[cookie_token].close()
                del token_sessions[cookie_token]
            return []  # Stop immediately

        except Exception as e:
            token_status[cookie_token] = "die"
            print(f"[!] Lỗi không mong muốn khi lấy token cho cookie: {cookie[:50]}... {e}")
            bot.send_message(chat_id, f"Lỗi không mong muốn khi lấy token cho cookie: {cookie[:50]}... Dừng tool.")
            stop_sharing_flags[chat_id] = True
            # Close session on error
            if cookie_token in token_sessions:
                token_sessions[cookie_token].close()
                del token_sessions[cookie_token]
            return []  # Stop immediately

    return gome_token


def share(tach, id_share, chat_id):
    cookie = tach.split('|')[0]
    token = tach.split('|')[1]
    device_id = tach.split('|')[2]  # Get device ID from token
    headers = generate_headers(cookie, device_id)  # consistent headers

    session = token_sessions.get(tach)  # Get the session object.

    if not session:  # should never happen but just in case
        print(f"No session found for token: {tach[:50]}.  Creating new session (this is unexpected)")
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
            bot.send_message(chat_id, f"[!] Share thất bại: ID: {id_share} - Token Die - Dừng tool.")
            stop_sharing_flags[chat_id] = True
            print(f"[!] Share thất bại: ID: {id_share} - Phản hồi: {res}")
            return False

    except requests.exceptions.RequestException as e:
        token_status[tach] = "die"
        bot.send_message(chat_id, f"[!] Lỗi request share: ID: {id_share} - {e} - Dừng tool.")
        stop_sharing_flags[chat_id] = True
        print(f"[!] Lỗi request share: ID: {id_share} - {e}")
        return False

    except Exception as e:
        token_status[tach] = "die"
        bot.send_message(chat_id, f"[!] Lỗi không mong muốn khi share: ID: {id_share} - {e} - Dừng tool.")
        stop_sharing_flags[chat_id] = True
        print(f"[!] Lỗi không mong muốn khi share: ID: {id_share} - {e}")
        return False


def share_thread_telegram(tach, id_share, stt, chat_id):
    if stop_sharing_flags.get(chat_id, False):
        return False  # Stop sharing
    if share(tach, id_share, chat_id):
        return True
    else:
        return False


# Telegram Bot Handlers
share_data = {}  # Store user-specific data


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Chào mừng! Sử dụng /share để bắt đầu.")


@bot.message_handler(commands=['share'])
def share_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    share_data[chat_id] = {}  # Initialize data for the user

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
                     "Thông tin bot:\n- Bot này được phát triển bởi [Your Name/Organization]\n- Hỗ trợ share bài viết lên trang cá nhân.\n- Liên hệ: [Your Contact Information/Link]")

    # Create a stop button
    markup = types.InlineKeyboardMarkup()
    stop_button = types.InlineKeyboardButton("Dừng Share", callback_data="stop_share")
    markup.add(stop_button)
    bot.send_message(chat_id, "Vui lòng gửi file chứa cookie (cookies.txt).", reply_markup=markup)
    bot.register_next_step_handler(message, process_cookie_file)


@bot.callback_query_handler(func=lambda call: call.data == "stop_share")
def stop_share_callback(call):
    chat_id = call.message.chat.id
    stop_sharing_flags[chat_id] = True  # Set the stop flag
    bot.send_message(chat_id, "Đã nhận lệnh dừng share. Vui lòng chờ quá trình hoàn tất.")
    global gome_token
    gome_token.clear()

    # close sessions (cleanup resources)
    global token_sessions
    for session in token_sessions.values():
        session.close()
    token_sessions = {}  # reset


def process_cookie_file(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    try:
        if message.document is None:
            bot.reply_to(message, "Vui lòng gửi file chứa cookie (cookies.txt).")
            return

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_content = downloaded_file.decode('utf-8').splitlines()
        share_data[chat_id]['cookie_file'] = file_content
        bot.send_message(chat_id, "Đã nhận file cookie. Vui lòng nhập ID bài viết cần share.")
        bot.register_next_step_handler(message, process_id)
    except Exception as e:
        print(f"Error processing file: {e}")  # Log error for debugging
        bot.reply_to(message, "Vui lòng gửi file chứa cookie (cookies.txt).")  # User-friendly message
        del share_data[chat_id]  # Clear data


def process_id(message):
    chat_id = message.chat.id
    id_share = message.text.strip()
    if not id_share.isdigit():
        bot.reply_to(message, "ID không hợp lệ. Vui lòng nhập lại ID bài viết cần share.")
        bot.register_next_step_handler(message, process_id)
        return

    share_data[chat_id]['id_share'] = id_share
    bot.send_message(chat_id, "Vui lòng nhập delay giữa các lần share (giây).")
    bot.register_next_step_handler(message, process_delay)


def process_delay(message):
    chat_id = message.chat.id
    delay_str = message.text.strip()
    try:
        delay = int(delay_str)
        if delay < 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message, "Delay không hợp lệ. Vui lòng nhập lại delay (giây) là một số dương.")
        bot.register_next_step_handler(message, process_delay)
        return

    share_data[chat_id]['delay'] = delay
    bot.send_message(chat_id, "Vui lòng nhập tổng số lượng share (0 để không giới hạn).")
    bot.register_next_step_handler(message, process_total_shares)


def process_total_shares(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    total_share_limit_str = message.text.strip()
    try:
        total_share_limit = int(total_share_limit_str)
        if total_share_limit < 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message,
                     "Số lượng share không hợp lệ. Vui lòng nhập lại tổng số lượng share (0 để không giới hạn) là một số dương.")
        bot.register_next_step_handler(message, process_total_shares)
        return

    share_data[chat_id]['total_share_limit'] = total_share_limit

    # Limit total shares based on user role
    if user_id != ADMIN_USER_ID and total_share_limit > USER_SHARE_LIMIT_PER_DAY:
        total_share_limit = USER_SHARE_LIMIT_PER_DAY
        bot.send_message(chat_id, f"Bạn không phải là admin. Số lượng share sẽ bị giới hạn ở mức {USER_SHARE_LIMIT_PER_DAY}.")
        share_data[chat_id]['total_share_limit'] = total_share_limit

    start_sharing(chat_id)


def start_sharing(chat_id):
    data = share_data.get(chat_id)
    user_id = bot.get_chat(chat_id).id  # Get user ID safely

    if not data:
        bot.send_message(chat_id, "Dữ liệu không đầy đủ. Vui lòng bắt đầu lại bằng lệnh /share.")
        return

    input_file = data['cookie_file']
    id_share = data['id_share']
    delay = data['delay']
    total_share_limit = data['total_share_limit']

    # Get tokens, stop if fails
    all_tokens = get_token(input_file, chat_id)
    if not all_tokens:
        # get_token already sent a message to the user and handled stopping
        del share_data[chat_id]
        return

    total_live = len(all_tokens)

    if total_live == 0:
        bot.send_message(chat_id, "Không tìm thấy token hợp lệ nào.")
        del share_data[chat_id]  # Clean up
        return

    bot.send_message(chat_id, f"Tìm thấy {total_live} token hợp lệ.")

    # Send initial message with share success count and store its ID
    markup = types.InlineKeyboardMarkup()
    stop_button = types.InlineKeyboardButton("Dừng Share", callback_data="stop_share")
    markup.add(stop_button)
    bot.send_message(chat_id, "Đang share, khi nào xong bot sẽ báo lại...", reply_markup=markup)


    stt = 0
    shared_count = 0
    global successful_shares
    successful_shares = 0  # Reset successful shares count
    continue_sharing = True
    stop_sharing_flags[chat_id] = False  # Reset stop flag at start

    while continue_sharing:
        for tach in all_tokens:
            if stop_sharing_flags.get(chat_id, False):
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
            thread = threading.Thread(target=process_share, args=(tach, id_share, stt, chat_id, user_id))
            thread.start()
            time.sleep(delay)
            shared_count += 1

            if total_share_limit > 0 and shared_count >= total_share_limit:
                continue_sharing = False
                break

            if stop_sharing_flags.get(chat_id, False):
                continue_sharing = False
                break
    # Wait for all threads to complete.  Important for accurate count.
    for thread in threading.enumerate():
        if thread != threading.current_thread():
            thread.join()

    bot.send_message(chat_id, "Quá trình share hoàn tất.")
    if total_share_limit > 0 and shared_count >= total_share_limit:
        bot.send_message(chat_id, f"Đạt giới hạn share là {total_share_limit} shares.")
    bot.send_message(chat_id, f"Tổng cộng {successful_shares} share thành công.")  # Final count

    del share_data[chat_id]  # Clean up
    global gome_token
    gome_token.clear()
    stop_sharing_flags[chat_id] = False  # Reset

    # Cleanup sessions
    global token_sessions
    for session in token_sessions.values():
        session.close()
    token_sessions = {}  # Reset


def process_share(tach, id_share, stt, chat_id, user_id):
    global successful_shares
    global user_share_counts  # access global variable
    if stop_sharing_flags.get(chat_id, False):
        return  # Stop immediately

    success = share_thread_telegram(tach, id_share, stt, chat_id)
    if not success:
        # share() function handles stopping when share fails
        return

    # If share was successful:
    successful_shares += 1

    # Update daily share count
    today = strftime("%Y-%m-%d")
    if user_id not in user_share_counts:
        user_share_counts[user_id] = {}
    if today not in user_share_counts[user_id]:
        user_share_counts[user_id][today] = 0
    user_share_counts[user_id][today] += 1



if __name__ == "__main__":
    try:
        print("Bot is running...")
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Bot stopped.")
        sys.exit()