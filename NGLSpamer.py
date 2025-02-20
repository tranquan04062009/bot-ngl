import logging
import os
import requests
import threading
import time
import json
import random

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Constants
__version__ = 'v2-telegram'
__Copyright__ = 'Trần Quân✔️'

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# User Agents
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

# Global variables
sharing_active = False
all_tokens = []
id_share = None
delay = 10
total_share_limit = 0
shared_count = 0
cookie_file_path = None

# --- Helper Functions ---
def get_token(input_file):
    tokens = []
    for cookie in input_file:
        cookie = cookie.strip()
        if not cookie:
            continue
        header_ = {
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
            'user-agent': random.choice(user_agents)
        }
        try:
            home_business = requests.get('https://business.facebook.com/content_management', headers=header_, timeout=15).text
            if 'EAAG' in home_business:
                token = home_business.split('EAAG')[1].split('","')[0]
                cookie_token = f'{cookie}|EAAG{token}'
                tokens.append(cookie_token)
            else:
                logging.warning(f"Could not get token from cookie: {cookie[:50]}... Cookie may be invalid.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error getting token for cookie: {cookie[:50]}... {e}")
        except Exception as e:
            logging.exception(f"Unexpected error getting token for cookie: {cookie[:50]}... {e}")
    return tokens

def share(tach, id_share):
    cookie = tach.split('|')[0]
    token = tach.split('|')[1]
    he = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'connection': 'keep-alive',
        'content-length': '0',
        'cookie': cookie,
        'host': 'graph.facebook.com',
        'user-agent': random.choice(user_agents),
        'referer': f'https://m.facebook.com/{id_share}'
    }
    try:
        res = requests.post(f'https://graph.facebook.com/me/feed?link=https://m.facebook.com/{id_share}&published=0&access_token={token}', headers=he, timeout=10).json()
        if 'id' in res:
            return True
        else:
            logging.error(f"Share failed: ID: {id_share} - Response: {res}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error sharing: ID: {id_share} - {e}")
        return False
    except Exception as e:
        logging.exception(f"Unexpected error sharing: ID: {id_share} - {e}")
        return False

def share_thread(tach, id_share, stt, context: CallbackContext):
    global shared_count
    if share(tach, id_share):
        logger.info(f'[{stt}] SHARE SUCCESSFUL ID {id_share}')
        context.bot.send_message(chat_id=context.job.chat_id, text=f'[{stt}] SHARE SUCCESSFUL ID {id_share}')
    else:
          context.bot.send_message(chat_id=context.job.chat_id, text=f'[{stt}] SHARE FAILED ID {id_share}')
    shared_count +=1

# --- Telegram Bot Handlers ---

async def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    text = (
        f"Chào mừng bạn đến với Telegram Bot Share Facebook!\n\n"
        f"Sử dụng lệnh /share để bắt đầu chia sẻ bài viết.\n"
        f"Gửi file cookies, ID bài viết, delay và tổng số lượng share theo yêu cầu.\n"
        f"Sử dụng lệnh /stop để dừng quá trình chia sẻ."
    )
    await update.message.reply_text(text)

async def share_command(update: Update, context: CallbackContext):
    """Starts the sharing process."""
    global sharing_active, all_tokens, id_share, delay, total_share_limit, shared_count, cookie_file_path
    if sharing_active:
        await update.message.reply_text("Một tiến trình share đang chạy. Vui lòng dừng nó trước khi bắt đầu tiến trình mới.")
        return

    sharing_active = True
    all_tokens = []
    id_share = None
    delay = 10
    total_share_limit = 0
    shared_count = 0
    cookie_file_path = None

    await update.message.reply_text("Vui lòng gửi file chứa cookies.")
    return

async def process_file(update: Update, context: CallbackContext):
    """Processes the cookie file."""
    global cookie_file_path
    try:
        file = await context.bot.get_file(update.message.document.file_id)
        cookie_file_path = f"cookies_{update.message.chat_id}.txt"
        await file.download_to_drive(cookie_file_path)
        await update.message.reply_text("File cookies đã được nhận. Vui lòng nhập ID bài viết cần share.")
    except Exception as e:
        await update.message.reply_text(f"Lỗi khi xử lý file: {e}")
        sharing_active = False
        return

async def process_id(update: Update, context: CallbackContext):
    """Processes the share ID."""
    global id_share
    id_share = update.message.text
    await update.message.reply_text("Đã nhận ID. Vui lòng nhập delay giữa các lần share (giây).")

async def process_delay(update: Update, context: CallbackContext):
    """Processes the delay."""
    global delay
    try:
        delay = int(update.message.text)
        if delay < 0:
            raise ValueError
        await update.message.reply_text("Đã nhận delay. Vui lòng nhập tổng số lượng share (0 để không giới hạn).")
    except ValueError:
        await update.message.reply_text("Delay phải là một số nguyên dương hợp lệ.")
        sharing_active = False

async def process_total_shares(update: Update, context: CallbackContext):
     """Processes the total number of shares and starts sharing."""
     global total_share_limit, sharing_active, all_tokens, id_share, delay, shared_count, cookie_file_path
     try:
        total_share_limit = int(update.message.text)
        if total_share_limit < 0:
            raise ValueError

        # Load cookies and get tokens
        try:
            with open(cookie_file_path, 'r') as f:
                input_file = f.read().split('\n')
            all_tokens = get_token(input_file)
            if not all_tokens:
                await update.message.reply_text("Không tìm thấy token hợp lệ nào trong file cookie.")
                sharing_active = False
                return
        except FileNotFoundError:
            await update.message.reply_text("Không tìm thấy file cookies.")
            sharing_active = False
            return
        except Exception as e:
            await update.message.reply_text(f"Lỗi khi đọc file cookies: {e}")
            sharing_active = False
            return

        await update.message.reply_text(f"Tìm thấy {len(all_tokens)} token hợp lệ. Bắt đầu share...")
        shared_count = 0
        stt = 0

        # Start sharing in a separate thread
        context.job_queue.run_repeating(
            callback=start_sharing,
            interval=delay,
            first=1,
            context={'chat_id': update.message.chat_id, 'stt': stt}
        )

     except ValueError:
        await update.message.reply_text("Tổng số lượng share phải là một số nguyên không âm hợp lệ.")
        sharing_active = False

async def start_sharing(context: CallbackContext):
    """Shares posts using available tokens."""
    global sharing_active, all_tokens, id_share, total_share_limit, shared_count
    job = context.job
    stt = context.job.context['stt']
    if not sharing_active:
        await context.bot.send_message(job.chat_id, text="Tiến trình share đã dừng.")
        job.schedule_removal()  # Remove the job from the queue
        return

    if total_share_limit > 0 and shared_count >= total_share_limit:
        await context.bot.send_message(job.chat_id, text=f"Đã đạt giới hạn share là {total_share_limit} shares.")
        sharing_active = False
        job.schedule_removal()
        return
    try:
        tach = all_tokens[stt % len(all_tokens)]  # Cycle through tokens
        thread = threading.Thread(target=share_thread, args=(tach, id_share, stt, context))
        thread.start()
        stt+=1
        context.job.context['stt'] = stt

    except Exception as e:
        await context.bot.send_message(job.chat_id, text=f"Lỗi trong quá trình share: {e}")
        sharing_active = False
        job.schedule_removal()

async def stop(update: Update, context: CallbackContext):
    """Stops the sharing process."""
    global sharing_active
    sharing_active = False
    await update.message.reply_text("Đã dừng tiến trình share.")
    context.job_queue.stop()

def main():
    """Starts the bot."""

    TOKEN = os.environ.get("7766543633:AAHZv7YVvjnTExyvRFy6xufeyc2AGYJTVlA") # Replace with your bot token
    if not TOKEN:
        print("Please set the TELEGRAM_BOT_TOKEN environment variable.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("share", share_command))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.Document.ALL, process_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           lambda update, context: (
                                               process_id(update, context) if id_share is None else (
                                                   process_delay(update, context) if delay == 10 else process_total_shares(update, context)
                                               )
                                           )))

    application.run_polling()

if __name__ == '__main__':
    main()