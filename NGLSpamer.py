import requests
import time
import random
import telebot
from telebot import types

# --- Cấu hình và Hằng số ---
TOKEN = "7766543633:AAHd5v0ILieeJdpnRTCdh2RvzV1M8jli4uc"  # Thay thế bằng token của bot bạn
ADMIN_ID = 6940071938  # Thay thế bằng ID Telegram của bạn (admin)
ALLOWED_GROUP_IDS = [-1002370805497]  # Thay thế bằng ID nhóm của bạn

DAILY_SHARE_LIMIT = 5000  # Giới hạn chia sẻ hàng ngày (cho người dùng thường)
USER_DATA = {}

# --- Khởi tạo Bot ---
bot = telebot.TeleBot(TOKEN)

# --- User Agents (Danh sách các User-Agent) ---
USER_AGENTS = [
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

# --- Hàm Hỗ Trợ ---

def get_token(cookies):
    tokens = []
    for cookie in cookies:
        cookie = cookie.strip()
        if not cookie:
            continue
        headers = {
            'authority': 'business.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
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
            'user-agent': random.choice(USER_AGENTS)
        }
        try:
            response = requests.get('https://business.facebook.com/content_management', headers=headers, timeout=15)
            response.raise_for_status()
            home_business = response.text
            if 'EAAG' in home_business:
                token = home_business.split('EAAG')[1].split('","')[0]
                tokens.append(f'{cookie}|EAAG{token}')
        except requests.exceptions.RequestException as e:
            print(f"Lỗi lấy token cho cookie {cookie[:50]}...: {e}")
        except Exception as e:
            print(f"Lỗi không xác định khi lấy token cho cookie {cookie[:50]}...: {e}")

    return tokens


def perform_share(token_data, post_id):
    cookie = token_data.split('|')[0]
    token = token_data.split('|')[1]
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'connection': 'keep-alive',
        'content-length': '0',
        'cookie': cookie,
        'host': 'graph.facebook.com',
        'user-agent': random.choice(USER_AGENTS),
        'referer': f'https://m.facebook.com/{post_id}'
    }
    try:
        response = requests.post(f'https://graph.facebook.com/me/feed?link=https://m.facebook.com/{post_id}&published=0&access_token={token}', headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return 'id' in data
    except requests.exceptions.RequestException as e:
        print(f"Lỗi request khi chia sẻ: {e}")
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi chia sẻ: {e}")
        return False


def reset_daily_counts():
    today = time.strftime("%Y-%m-%d")
    for chat_id, data in USER_DATA.items():
        if data['last_share_date'] != today:
            data['shares_today'] = 0
            data['last_share_date'] = today


def check_daily_limit(chat_id, user_id):
    reset_daily_counts()
    if chat_id not in USER_DATA:
        USER_DATA[chat_id] = {'shares_today': 0, 'last_share_date': time.strftime("%Y-%m-%d"), 'running': False, 'user_id': None}
    if user_id == ADMIN_ID or chat_id in ALLOWED_GROUP_IDS:
        return True  # Admin và nhóm được phép không giới hạn
    return USER_DATA[chat_id]['shares_today'] < DAILY_SHARE_LIMIT

def check_running(chat_id, user_id):
    if chat_id not in USER_DATA:
      USER_DATA[chat_id] = {'shares_today': 0, 'last_share_date': time.strftime("%Y-%m-%d"), 'running': False, 'user_id': None}

    if USER_DATA[chat_id]['running'] == True and USER_DATA[chat_id]['user_id'] != user_id:
        return True
    elif USER_DATA[chat_id]['running'] == True and USER_DATA[chat_id]['user_id'] == user_id:
        return False
    else:
        return False

def increment_share_count(chat_id):
    USER_DATA[chat_id]['shares_today'] += 1


# --- Trình xử lý của Bot ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        bot.reply_to(message, "Bot này chỉ hoạt động trong nhóm chat.")
        return
    # Kiểm tra xem tin nhắn có đến từ nhóm được phép không
    if message.chat.id not in ALLOWED_GROUP_IDS:
        bot.reply_to(message, "Bot này không được phép hoạt động trong nhóm này.")
        return

    help_text = """
Bot này giúp bạn chia sẻ bài viết Facebook.

**Lệnh:**
/share - Bắt đầu quá trình chia sẻ.
/help  - Hiển thị tin nhắn trợ giúp này.
    """
    bot.reply_to(message, help_text, parse_mode="Markdown")


@bot.message_handler(commands=['share'])
def start_share(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.username

    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        bot.reply_to(message, "Bot này chỉ hoạt động trong nhóm chat.")
        return

    # Kiểm tra xem tin nhắn có đến từ nhóm được phép không
    if message.chat.id not in ALLOWED_GROUP_IDS:
        bot.reply_to(message, "Bot này không được phép hoạt động trong nhóm này.")
        return

    if not check_daily_limit(chat_id, user_id):
        bot.reply_to(message, "Đã đạt giới hạn chia sẻ hàng ngày cho nhóm này.")
        return
    if check_running(chat_id, user_id):
        bot.reply_to(message, "Có người trong nhóm này đang sử dụng lệnh chia sẻ. Vui lòng đợi.")
        return


    USER_DATA[chat_id]['running'] = True
    USER_DATA[chat_id]['user_id'] = user_id
    USER_DATA[chat_id]['user_name'] = user_name
    USER_DATA[chat_id]['stop_requested'] = False


    markup = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Hủy", callback_data="cancel")
    markup.add(cancel_button)

    msg = bot.reply_to(message, "Vui lòng gửi cho tôi tệp cookie (dưới dạng tài liệu).", reply_markup=markup)
    bot.register_next_step_handler(msg, process_cookie_file, user_id)


def process_cookie_file(message, user_id):
    chat_id = message.chat.id

    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        bot.reply_to(message, "Bot này chỉ hoạt động trong nhóm chat.")
        return
     # Kiểm tra xem tin nhắn có đến từ nhóm được phép không
    if message.chat.id not in ALLOWED_GROUP_IDS:
        bot.reply_to(message, "Bot này không được phép hoạt động trong nhóm này.")
        return

    # Kiểm tra xem người dùng có hủy không
    if message.text == '/cancel' or (hasattr(message, 'data') and  message.data == 'cancel'):
            USER_DATA[chat_id]['running'] = False
            USER_DATA[chat_id]['user_id'] = None
            bot.reply_to(message, "Đã hủy thao tác.")
            return

    if not message.document:
        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("Hủy", callback_data="cancel")
        markup.add(cancel_button)
        bot.reply_to(message, "Vui lòng gửi cookie dưới dạng tệp đính kèm (tài liệu).", reply_markup=markup)

        bot.register_next_step_handler(message, process_cookie_file, user_id) # Đăng ký lại
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        cookies = downloaded_file.decode('utf-8').splitlines()
        tokens = get_token(cookies)

        if not tokens:
            USER_DATA[chat_id]['running'] = False
            USER_DATA[chat_id]['user_id'] = None
            bot.reply_to(message, "Không tìm thấy token hợp lệ trong tệp cookie.")
            return

        USER_DATA[chat_id]['tokens'] = tokens

        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("Hủy", callback_data="cancel")
        markup.add(cancel_button)

        msg = bot.reply_to(message, "Nhập ID bài viết Facebook:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_post_id, user_id, tokens)

    except Exception as e:
        USER_DATA[chat_id]['running'] = False
        USER_DATA[chat_id]['user_id'] = None
        bot.reply_to(message, f"Lỗi xử lý tệp cookie: {e}")



def process_post_id(message, user_id, tokens):
    chat_id = message.chat.id

    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        bot.reply_to(message, "Bot này chỉ hoạt động trong nhóm chat.")
        return
    # Kiểm tra xem tin nhắn có đến từ nhóm được phép không
    if message.chat.id not in ALLOWED_GROUP_IDS:
        bot.reply_to(message, "Bot này không được phép hoạt động trong nhóm này.")
        return

    if message.text == '/cancel' or (hasattr(message, 'data') and message.data == "cancel"):
        USER_DATA[chat_id]['running'] = False
        USER_DATA[chat_id]['user_id'] = None
        bot.reply_to(message, "Đã hủy thao tác.")
        return

    post_id = message.text.strip()
    if not post_id.isdigit():
        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("Hủy", callback_data="cancel")
        markup.add(cancel_button)
        bot.reply_to(message, "ID bài viết không hợp lệ. Vui lòng nhập ID là số.", reply_markup=markup)
        bot.register_next_step_handler(message, process_post_id, user_id, tokens)
        return

    USER_DATA[chat_id]['post_id'] = post_id

    markup = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Hủy", callback_data="cancel")
    markup.add(cancel_button)

    msg = bot.reply_to(message, "Nhập độ trễ giữa các lần chia sẻ (tính bằng giây):", reply_markup=markup)
    bot.register_next_step_handler(msg, process_delay, user_id, tokens, post_id)


def process_delay(message, user_id, tokens, post_id):
    chat_id = message.chat.id

    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        bot.reply_to(message, "Bot này chỉ hoạt động trong nhóm chat.")
        return

    # Kiểm tra xem tin nhắn có đến từ nhóm được phép không
    if message.chat.id not in ALLOWED_GROUP_IDS:
        bot.reply_to(message, "Bot này không được phép hoạt động trong nhóm này.")
        return

    if message.text == '/cancel' or (hasattr(message, 'data') and message.data == "cancel"):
        USER_DATA[chat_id]['running'] = False
        USER_DATA[chat_id]['user_id'] = None

        bot.reply_to(message, "Đã hủy thao tác.")
        return
    try:
        delay = int(message.text.strip())
        if delay < 0:
            raise ValueError("Độ trễ phải là số không âm")
    except ValueError:
        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("Hủy", callback_data="cancel")
        markup.add(cancel_button)
        bot.reply_to(message, "Độ trễ không hợp lệ. Vui lòng nhập một số nguyên không âm.", reply_markup=markup)
        bot.register_next_step_handler(msg, process_delay, user_id, tokens, post_id)
        return

    USER_DATA[chat_id]['delay'] = delay

    markup = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Hủy", callback_data="cancel")
    markup.add(cancel_button)

    msg = bot.reply_to(message, "Nhập tổng số lượt chia sẻ (0 để không giới hạn):", reply_markup=markup)
    bot.register_next_step_handler(msg, process_share_count, user_id, tokens, post_id, delay)


def process_share_count(message, user_id, tokens, post_id, delay):
    chat_id = message.chat.id
    user_name =  USER_DATA[chat_id]['user_name']

    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        bot.reply_to(message, "Bot này chỉ hoạt động trong nhóm chat.")
        return
    # Kiểm tra xem tin nhắn có đến từ nhóm được phép không
    if message.chat.id not in ALLOWED_GROUP_IDS:
        bot.reply_to(message, "Bot này không được phép hoạt động trong nhóm này.")
        return

    if message.text == '/cancel' or (hasattr(message,'data') and message.data == "cancel"):
        USER_DATA[chat_id]['running'] = False
        USER_DATA[chat_id]['user_id'] = None
        bot.reply_to(message, "Đã hủy thao tác.")
        return

    try:
        share_count = int(message.text.strip())
        if share_count < 0:
            raise ValueError("Số lượt chia sẻ phải là số không âm")
    except ValueError:
        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("Hủy", callback_data="cancel")
        markup.add(cancel_button)
        bot.reply_to(message, "Số lượt chia sẻ không hợp lệ. Vui lòng nhập một số nguyên không âm.", reply_markup = markup)
        bot.register_next_step_handler(msg, process_share_count, user_id, tokens, post_id, delay)
        return

    USER_DATA[chat_id]['share_count'] = share_count

    if not check_daily_limit(chat_id, user_id):
        bot.reply_to(message, "Đã đạt giới hạn chia sẻ hàng ngày cho nhóm này.")
        return
    #Xác nhận và Nút dừng
    markup = types.InlineKeyboardMarkup()
    stop_button = types.InlineKeyboardButton("Dừng Chia sẻ", callback_data="stop_sharing")
    markup.add(stop_button)
    bot.send_message(chat_id, "Đang bắt đầu chia sẻ. Nhấn 'Dừng Chia sẻ' để gián đoạn.", reply_markup=markup)

    success_count = 0
    for i, token_data in enumerate(tokens):
        if share_count > 0 and success_count >= share_count: #Dừng lại khi success_count >= share_count
            break

        if not check_daily_limit(chat_id, user_id):
            bot.send_message(chat_id, f"Đã đạt giới hạn chia sẻ hàng ngày trong quá trình hoạt động. Đã chia sẻ {success_count} lần.")
            break
        #Yêu cầu dừng
        if USER_DATA[chat_id]['stop_requested']:
            bot.send_message(chat_id, f"Quá trình chia sẻ bị dừng bởi người dùng. Đã chia sẻ {success_count} lần.")
            break

        if perform_share(token_data, post_id):
            success_count += 1
            increment_share_count(chat_id)
            #Không gửi thông báo thành công sau mỗi lượt share
        else:
            #Không gửi thông báo khi thất bại
            pass

        if i < len(tokens) - 1:
            time.sleep(delay)

    #Chỉ thông báo khi đã hoàn tất (hoặc bị dừng)
    if success_count == share_count or (share_count == 0 and i == len(tokens) -1 ):
        bot.send_message(chat_id, f"@{user_name} Quá trình chia sẻ đã hoàn tất. Đã chia sẻ thành công {success_count} lần.")
    elif USER_DATA[chat_id]['stop_requested']:
      pass
    else:
      bot.send_message(chat_id, f"@{user_name} Quá trình chia sẻ đã dừng lại. Đã chia sẻ thành công {success_count} lần.")


    USER_DATA[chat_id]['running'] = False
    USER_DATA[chat_id]['user_id'] = None
    if 'tokens' in USER_DATA[message.chat.id]:
        del USER_DATA[message.chat.id]['tokens']

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if call.data == "cancel":
      if chat_id in USER_DATA and USER_DATA[chat_id]['user_id'] == user_id:
        #Hủy handler bước tiếp theo
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)

        bot.edit_message_text("Đã hủy thao tác.", chat_id=chat_id, message_id=call.message.message_id)
        USER_DATA[chat_id]['running'] = False
        USER_DATA[chat_id]['user_id'] = None
      else:
        bot.answer_callback_query(call.id, "Bạn không thể hủy thao tác này.")

    elif call.data == "stop_sharing":

        if chat_id in USER_DATA and USER_DATA[chat_id]['user_id'] == user_id:

            USER_DATA[chat_id]['stop_requested'] = True
            bot.edit_message_text("Đang dừng quá trình chia sẻ...", chat_id=chat_id, message_id=call.message.message_id)
        else:

            bot.answer_callback_query(call.id, "Bạn không thể dừng thao tác này.")


# --- Khởi động Bot ---
bot.infinity_polling()