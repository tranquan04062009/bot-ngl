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
        'referer': f'https://ngl.link/',
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

async def spamngl_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
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
    global spam_running, spam_task, progress_message
    spam_running = True
    spam_task = asyncio.create_task(spam_process(update, context))
    progress_message = await update.message.reply_text("Đang gửi tin nhắn: 0")

async def spam_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_running, progress_message
    nglusername = context.user_data.get("username")
    message = context.user_data.get("message")
    count = context.user_data.get("count")
    delay = context.user_data.get("delay")

    session = tao_session_retry()
    value = 0
    notsend = 0

    while value < count and spam_running:
        success, result = gui_ngl_tin_nhan(session, nglusername, message)
        if success:
            notsend = 0
            value += 1
            if progress_message:
                await progress_message.edit_text(f"Đang gửi tin nhắn: {value}")
        else:
            notsend += 1
            await update.message.reply_text(f"[-] Chưa gửi được, {result}")
        if notsend == 4:
            await update.message.reply_text("[!] Đang đổi thông tin...")
            notsend = 0
        if spam_running:
             await asyncio.sleep(delay + random.uniform(0,0.5))
    if progress_message:
            await progress_message.edit_text(f"Hoàn thành! Đã gửi tổng cộng {value} tin nhắn.")
    spam_running = False
    spam_task = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_running
    if spam_running:
        await update.message.reply_text("Đã có phiên đang chạy, hãy dùng lệnh /stop để dừng")
    else:
      await update.message.reply_text("Sẵn sàng để spam.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_running, spam_task
    if spam_running:
        spam_running = False
        if spam_task:
            spam_task.cancel()
            spam_task = None
        await update.message.reply_text("Đã dừng phiên spam.")
    else:
       await update.message.reply_text("Không có phiên spam nào đang chạy")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Hủy bỏ quá trình.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    TOKEN = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo"
    application = ApplicationBuilder().token(TOKEN).build()

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
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()