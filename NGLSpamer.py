import logging
import random
import string
import requests
import time
from http.client import HTTPException
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import secrets
from fake_useragent import UserAgent, FakeUserAgentError
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
import asyncio
import re

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Constants for conversation states
(
    USERNAME,
    MESSAGE,
    COUNT,
    DELAY,
) = map(chr, range(4))

# Global variable to control the spamming process
spam_running = False
spam_task = None
progress_message = None
error_message = None

# Common IP ranges for spoofing (Example - You may need more ranges from your target region)
VALID_IP_RANGES = [
    "103.252.0.0/22",
    "115.146.120.0/21",
    "115.165.160.0/21",
    "103.21.148.0/22",
    "124.158.0.0/20",
    "101.99.0.0/18",
    "103.216.72.0/22",
    "103.39.92.0/22",
    "113.22.0.0/16",
    "202.151.168.0/21",
    "125.253.112.0/20",
    "180.93.0.0/16",
    "103.141.176.0/23",
    "103.84.76.0/22",
    "117.103.192.0/18",
    "103.233.48.0/22",
    "221.132.30.0/23"
]

# Create a pool of sessions
SESSIONS = []

#Function to generate IP from a valid range
def generate_ip_from_range():
    range_str = random.choice(VALID_IP_RANGES)
    parts = range_str.split("/")
    ip_prefix = parts[0]
    cidr = int(parts[1])
    ip_parts = list(map(int, ip_prefix.split(".")))
    available_bits = 32 - cidr
    random_int = random.randint(0, (1 << available_bits) - 1)
    for i in range(4):
      if (cidr >= 8):
          cidr -= 8
          continue
      ip_parts[i] = (ip_parts[i] & (255 << (8-cidr))) | ((random_int >> (available_bits - (8 - cidr))) & ((1 << (8-cidr)) - 1))
      available_bits -= (8-cidr)
      cidr = 0

    return ".".join(map(str, ip_parts))

def generate_device_id(user_agent):
    android_id = ''.join(random.choices(string.hexdigits[:16], k=16)).lower()
    if "Android" in user_agent:
        return f"android-{android_id}"
    elif "iPhone" in user_agent or 'iPad' in user_agent or 'iOS' in user_agent:
        return f"ios-{secrets.token_hex(8)}"
    else:
      return f"web-{secrets.token_hex(8)}"


def lay_user_agent():
    try:
        ua = UserAgent()
        return ua.random
    except FakeUserAgentError as e:
        logging.error(f"Lỗi khi lấy User Agent: {e}")
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

def get_random_session():
    return random.choice(SESSIONS)

def random_headers(user_agent):
    fetch_sites = ['same-origin', 'same-site', 'none']
    fetch_modes = ['cors', 'navigate', 'no-cors']
    fetch_dests = ['empty', 'document', 'nested-document', 'object', 'embed', 'image', 'audio', 'video', 'script', 'style', 'font', 'report']
    languages = [
        "en-US,en;q=0.9",
        "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
        "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    ]
    return {
        'Host': 'ngl.link',
        'sec-ch-ua': f'"{random.choice(["Google Chrome", "Mozilla Firefox", "Microsoft Edge"]) }";v="{random.randint(100,120)}", "Chromium";v="{random.randint(100,120)}", "Not-A.Brand";v="24"',
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'sec-ch-ua-mobile': '?0',
        'user-agent': user_agent,
        'sec-ch-ua-platform': f'"{random.choice(["Windows", "macOS", "Linux"])}"',
        'origin': 'https://ngl.link',
        'sec-fetch-site': random.choice(fetch_sites),
        'sec-fetch-mode': random.choice(fetch_modes),
        'sec-fetch-dest': random.choice(fetch_dests),
        'referer': f'https://ngl.link/',
        'accept-language': random.choice(languages),
        'x-forwarded-for': generate_ip_from_range()
    }


def gui_ngl_tin_nhan(nglusername, message):
    user_agent = lay_user_agent()
    headers = random_headers(user_agent)
    data = {
        'username': f'{nglusername}',
        'question': f'{message}',
        'deviceId': generate_device_id(user_agent),
        'gameSlug': '',
        'referrer': '',
        't': str(int(time.time() * 1000)),
        'r': secrets.token_urlsafe(16),
    }
    try:
        session = get_random_session()
        response = session.post('https://ngl.link/api/submit', headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return True, response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi Request: {e}")
        return False, f"Lỗi Request: {e}"
    except HTTPException as e:
        logging.error(f"Lỗi HTTP: {e}")
        return False, f"Lỗi HTTP: {e}"


async def spamngl_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    context.user_data.clear()
    await update.message.reply_text("Nhập tên người dùng NGL:")
    return USERNAME


async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    username = update.message.text
    context.user_data["username"] = username
    await update.message.reply_text("Nhập nội dung tin nhắn:")
    return MESSAGE


async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.message.text
    context.user_data["message"] = message
    await update.message.reply_text("Nhập số lượng tin nhắn:")
    return COUNT


async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        count = int(update.message.text)
        context.user_data["count"] = count
        await update.message.reply_text("Nhập độ trễ giữa các tin nhắn (0 để nhanh nhất):")
        return DELAY
    except ValueError:
        await update.message.reply_text("Lỗi: Số lượng tin nhắn phải là một số. Hãy nhập lại:")
        return COUNT


async def get_delay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        delay = float(update.message.text)
        context.user_data["delay"] = delay
        await update.message.reply_text("Bắt đầu gửi tin nhắn...")
        await start_spam_process(update, context)
        return ConversationHandler.END
    except ValueError:
       await update.message.reply_text("Lỗi: Độ trễ phải là một số. Hãy nhập lại:")
       return DELAY


async def start_spam_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_running, spam_task, progress_message, error_message
    spam_running = True
    spam_task = asyncio.create_task(spam_process(update, context))
    progress_message = await update.message.reply_text("Đang gửi tin nhắn: 0")
    error_message = await update.message.reply_text("")


async def spam_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_running, progress_message, error_message
    nglusername = context.user_data.get("username")
    message = context.user_data.get("message")
    count = context.user_data.get("count")
    delay = context.user_data.get("delay")

    value = 0
    notsend = 0

    while value < count and spam_running:
        success, result = gui_ngl_tin_nhan(nglusername, message)
        if success:
            notsend = 0
            value += 1
            if progress_message:
                await progress_message.edit_text(f"Đang gửi tin nhắn: {value}")
        else:
            notsend += 1
            if error_message:
                await error_message.edit_text(f"[-] Lỗi: {result}")
        if notsend == 4:
            if error_message:
                await error_message.edit_text("[!] Đang đổi thông tin...")
            notsend = 0
        if spam_running:
            await asyncio.sleep(delay + random.uniform(0, 0.5))
    if progress_message:
        await progress_message.edit_text(f"Hoàn thành! Đã gửi tổng cộng {value} tin nhắn.")
    if error_message:
       await error_message.edit_text("")
    spam_running = False
    spam_task = None
    context.user_data.clear()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_running
    if spam_running:
        await update.message.reply_text("Đã có phiên đang chạy, hãy dùng lệnh /stop để dừng")
    else:
      await update.message.reply_text("Sẵn sàng để spam dùng lệnh /help để xem hướng dân.")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_running, spam_task, error_message
    if spam_running:
        spam_running = False
        if spam_task:
            spam_task.cancel()
            spam_task = None
        if error_message:
            await error_message.edit_text("")
        await update.message.reply_text("Đã dừng phiên spam.")
    else:
       await update.message.reply_text("Không có phiên spam nào đang chạy")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    Sử dụng các lệnh sau:
    /start - Kiểm tra trạng thái hoạt động của bot.
    /spamngl - Bắt đầu một phiên spam tin nhắn NGL.
    /stop - Dừng phiên spam đang chạy.
    /help - Hiển thị hướng dẫn này.
    """
    await update.message.reply_text(help_text)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Hủy bỏ quá trình.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main() -> None:
    TOKEN = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo"
    application = ApplicationBuilder().token(TOKEN).build()

    # Create sessions
    global SESSIONS
    SESSIONS = [tao_session_retry() for _ in range(5)]


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("spamngl", spamngl_start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)],
            DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()