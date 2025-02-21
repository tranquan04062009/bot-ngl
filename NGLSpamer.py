import sys
import os
import requests
import threading
import time
import json
import random
from time import strftime
import logging
import asyncio  # Import asyncio at the top

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- CONFIGURATION ---
ADMIN_ID = 6940071938  # Replace with the admin's Telegram ID (int)
BOT_TOKEN = "7766543633:AAHd5v0ILieeJdpnRTCdh2RvzV1M8jli4uc"  # Replace with your bot's token
GROUP_CHAT_ID = -1002370805497  # Replace with your group chat ID (int).  Negative for groups.
DAILY_SHARE_LIMIT = 5000
# --- END CONFIGURATION ---

user_states = {}  # Dictionary to track user's progress through the sharing process.  Keys: user_id, Values: State (e.g., "waiting_for_cookie_file", "waiting_for_id", etc.)
user_data = {}  # Stores the data the user enters. Keys: user_id, Values: Dict containing cookie_file_path, id_share, delay, target_share_count, successful_shares
daily_share_count = 0
share_count_lock = threading.Lock()  # Protects the daily_share_count variable
active_share_threads = {}  # Tracks active share threads per user: {user_id: thread}
continue_sharing_flags = {}  # Tracks whether a user wants to continue sharing: {user_id: bool}

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

gome_token = []


def get_token(input_file):
    global gome_token
    gome_token = []
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
            home_business = requests.get('https://business.facebook.com/content_management', headers=header_,
                                           timeout=15).text
            if 'EAAG' in home_business:
                token = home_business.split('EAAG')[1].split('","')[0]
                cookie_token = f'{cookie}|EAAG{token}'
                gome_token.append(cookie_token)
            else:
                logging.warning(f"Không thể lấy token từ cookie: {cookie[:50]}.... Cookie có thể không hợp lệ.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Lỗi khi lấy token cho cookie: {cookie[:50]}... {e}")
        except Exception as e:
            logging.exception(f"Lỗi không mong muốn khi lấy token cho cookie: {cookie[:50]}... {e}")
    return gome_token


async def share(tach, id_share, context: ContextTypes.DEFAULT_TYPE, user_id, successful_shares):
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
        res = requests.post(
            f'https://graph.facebook.com/me/feed?link=https://m.facebook.com/{id_share}&published=0&access_token={token}',
            headers=he, timeout=10).json()
        if 'id' in res:
            return True
        else:
            logging.warning(f"Share thất bại: ID: {id_share} - Phản hồi: {res}")
            # No longer send error messages per share. Only on completion or failure
            # await context.bot.send_message(chat_id=user_id, text=f"Share failed for ID {id_share}. Response: {res}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi request share: ID: {id_share} - {e}")
        # No longer send error messages per share. Only on completion or failure
        # await context.bot.send_message(chat_id=user_id, text=f"Request error during share for ID {id_share}: {e}")
        return False
    except Exception as e:
        logging.exception(f"Lỗi không mong muốn khi share: ID: {id_share} - {e}")
        # No longer send error messages per share. Only on completion or failure
        # await context.bot.send_message(chat_id=user_id, text=f"Unexpected error during share for ID {id_share}: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if chat_id != GROUP_CHAT_ID:
        await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, bot này chỉ hoạt động trong nhóm chat đã được chỉ định.")
        return
    await context.bot.send_message(chat_id=chat_id, text="Chào mừng! Sử dụng lệnh /share để bắt đầu.")


async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if chat_id != GROUP_CHAT_ID:
        await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, bot này chỉ hoạt động trong nhóm chat đã được chỉ định.")
        return

    if user_id in active_share_threads:
        await context.bot.send_message(chat_id=chat_id,
                                       text="Bạn đang chạy một tiến trình share khác. Vui lòng dừng tiến trình hiện tại trước.")
        return

    # Create "Cancel" button.
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True, one_time_keyboard=True)

    user_states[user_id] = "waiting_for_cookie_file"
    user_data[user_id] = {}
    user_data[user_id]['successful_shares'] = 0  # Initialize the number of successful share

    await context.bot.send_message(chat_id=chat_id, text="Vui lòng gửi file chứa Cookies (cookies.txt).",
                                   reply_markup=cancel_keyboard)


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if chat_id != GROUP_CHAT_ID:
        await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, bot này chỉ hoạt động trong nhóm chat đã được chỉ định.")
        return

    if user_id in user_states and user_states[user_id] == "waiting_for_cookie_file":
        try:
            file_id = update.message.document.file_id
            new_file = await context.bot.get_file(file_id)
            file_path = await new_file.download_as_bytearray()

            decoded_file = bytearray(file_path).decode()
            input_file = decoded_file.split('\n')

            user_data[user_id]['input_file'] = input_file
            user_states[user_id] = "waiting_for_id"

            cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True,
                                                  one_time_keyboard=True)

            await context.bot.send_message(chat_id=chat_id, text="Tuyệt vời! Bây giờ, hãy nhập ID cần Share.",
                                           reply_markup=cancel_keyboard)
        except Exception as e:
            logging.exception(f"Error handling file: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"Có lỗi xảy ra khi xử lý file. Vui lòng thử lại. Error: {e}")
            cleanup_user_data(user_id)


async def handle_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    if chat_id != GROUP_CHAT_ID:
        await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, bot này chỉ hoạt động trong nhóm chat đã được chỉ định.")
        return
    if user_id in user_states and user_states[user_id] == "waiting_for_id":
        id_share = update.message.text
        user_data[user_id]['id_share'] = id_share
        user_states[user_id] = "waiting_for_target_count"

        cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True,
                                                  one_time_keyboard=True)

        await context.bot.send_message(chat_id=chat_id, text="OK. Nhập số lượng share bạn muốn.",
                                           reply_markup=cancel_keyboard)


async def handle_target_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    if chat_id != GROUP_CHAT_ID:
        await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, bot này chỉ hoạt động trong nhóm chat đã được chỉ định.")
        return
    if user_id in user_states and user_states[user_id] == "waiting_for_target_count":
        try:
            target_share_count = int(update.message.text)
            user_data[user_id]['target_share_count'] = target_share_count
            user_states[user_id] = "waiting_for_delay"

            cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True,
                                                  one_time_keyboard=True)

            await context.bot.send_message(chat_id=chat_id, text="Tuyệt vời! Nhập Delay giữa các lần share (giây, ví dụ: 10).",
                                           reply_markup=cancel_keyboard)
        except ValueError:
            await context.bot.send_message(chat_id=chat_id, text="Số lượng share phải là một số nguyên hợp lệ. Vui lòng thử lại.")
            user_states[user_id] = "waiting_for_target_count"
        except Exception as e:
            logging.exception(f"Error in handle_target_count: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"Đã có lỗi xảy ra. Vui lòng thử lại lệnh /share.")
            cleanup_user_data(user_id)


async def handle_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    if chat_id != GROUP_CHAT_ID:
        await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, bot này chỉ hoạt động trong nhóm chat đã được chỉ định.")
        return
    if user_id in user_states and user_states[user_id] == "waiting_for_delay":
        try:
            delay = int(update.message.text)
            user_data[user_id]['delay'] = delay
            user_states[user_id] = "ready_to_share"

            # Remove "Cancel" button and display "Stop Sharing"
            reply_markup = ReplyKeyboardMarkup([[KeyboardButton("Stop Sharing")]], resize_keyboard=True,
                                               one_time_keyboard=True)

            await context.bot.send_message(chat_id=chat_id, text="Tuyệt vời! Tất cả thông tin đã được thu thập.  Bắt đầu share...",
                                           reply_markup=reply_markup)
            await start_sharing(update, context)

        except ValueError:
            await context.bot.send_message(chat_id=chat_id, text="Delay phải là một số nguyên hợp lệ. Vui lòng thử lại.")
            user_states[user_id] = "waiting_for_delay"  # Go back to waiting for the delay
        except Exception as e:
            logging.exception(f"Error in handle_delay: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"Đã có lỗi xảy ra. Vui lòng thử lại lệnh /share.")
            cleanup_user_data(user_id)


async def start_sharing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    username = update.message.from_user.username  # Get the username, for tagging in the final message

    if user_id not in user_states or user_states[user_id] != "ready_to_share":
        await context.bot.send_message(chat_id=chat_id, text="Không thể bắt đầu share. Vui lòng chạy lại lệnh /share.")
        return

    input_file = user_data[user_id]['input_file']
    id_share = user_data[user_id]['id_share']
    delay = user_data[user_id]['delay']
    target_share_count = user_data[user_id]['target_share_count']
    successful_shares = 0  # Reset the successful shares count for this run.

    all_tokens = get_token(input_file)
    total_live = len(all_tokens)

    if total_live == 0:
        await context.bot.send_message(chat_id=chat_id, text="Không tìm thấy token hợp lệ nào.  Dừng lại.")
        cleanup_user_data(user_id)
        return

    await context.bot.send_message(chat_id=chat_id, text=f"Đã tìm thấy {total_live} token hợp lệ.")

    stt = 0
    shared_count = 0

    global daily_share_count
    global share_count_lock

    continue_sharing_flags[user_id] = True  # Initialize flag for this user

    def share_thread_target():
        nonlocal stt, shared_count, successful_shares

        for tach in all_tokens:
            if not continue_sharing_flags.get(user_id, False):  # Check the flag
                break

            with share_count_lock:
                if daily_share_count >= DAILY_SHARE_LIMIT:
                    asyncio.run(context.bot.send_message(chat_id=user_id, text="Đã đạt giới hạn share hàng ngày."))
                    continue_sharing_flags[user_id] = False  # Stop sharing for this user
                    break

            if successful_shares >= target_share_count:
                continue_sharing_flags[user_id] = False
                break

            stt += 1
            if not continue_sharing_flags.get(user_id, False):
                break  # Double-check before starting the share

            success = asyncio.run(share(tach, id_share, context, user_id,
                                        successful_shares))  # Pass the successful shares to the share function

            if success:
                with share_count_lock:
                    daily_share_count += 1
                successful_shares += 1  # Increment the successful share count

            shared_count += 1
            time.sleep(delay)  # Delay *inside* the thread function

        # Send final message.
        if successful_shares == target_share_count:
            message = f"@{username} Đã share thành công {successful_shares}/{target_share_count}."
        else:
            message = f"@{username} Đã dừng share. Đã share thành công {successful_shares}/{target_share_count}."

        asyncio.run(context.bot.send_message(chat_id=user_id, text=message))

        cleanup_user_data(user_id)
        del active_share_threads[user_id]

    share_thread = threading.Thread(target=share_thread_target)
    active_share_threads[user_id] = share_thread
    share_thread.start()


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    if chat_id != GROUP_CHAT_ID:
        await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, bot này chỉ hoạt động trong nhóm chat đã được chỉ định.")
        return

    if user_id in user_states:
        cleanup_user_data(user_id)
        await context.bot.send_message(chat_id=chat_id, text="Tiến trình đã bị huỷ.",
                                       reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True,
                                                                       one_time_keyboard=True))  # Remove keyboard
    else:
        await context.bot.send_message(chat_id=chat_id, text="Không có tiến trình nào đang chạy để hủy.")


async def handle_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if chat_id != GROUP_CHAT_ID:
        await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, bot này chỉ hoạt động trong nhóm chat đã được chỉ định.")
        return

    if user_id in active_share_threads:
        continue_sharing_flags[user_id] = False  # Set the flag to stop the thread
        await context.bot.send_message(chat_id=chat_id, text="Dừng chia sẻ...",
                                       reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True,
                                                                       one_time_keyboard=True))  # Remove Keyboard
    else:
        await context.bot.send_message(chat_id=chat_id, text="Không có tiến trình share nào đang chạy để dừng.")


def cleanup_user_data(user_id):
    """Cleans up user-specific data after sharing is complete or cancelled."""
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_data:
        del user_data[user_id]
    if user_id in continue_sharing_flags:
        del continue_sharing_flags[user_id]
    if user_id in active_share_threads:
        del active_share_threads[user_id]


async def reset_daily_limit(context: ContextTypes.DEFAULT_TYPE):
    global daily_share_count
    global share_count_lock
    with share_count_lock:
        daily_share_count = 0
    await context.bot.send_message(chat_id=ADMIN_ID, text="Daily share limit reset.")  # Notify admin


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, lệnh này không hợp lệ.")


if __name__ == '__main__':
    import datetime

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Get the job queue
    job_queue: JobQueue = application.job_queue

    # Command handlers
    start_handler = CommandHandler('start', start)
    share_handler = CommandHandler('share', share_command)
    application.add_handler(start_handler)
    application.add_handler(share_handler)

    # Message Handlers
    file_handler = MessageHandler(filters.Document.ALL, handle_file)
    id_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_id)
    target_count_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_target_count)  # Added handler
    delay_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delay)
    cancel_handler = MessageHandler(filters.TEXT & filters.Regex(pattern="^Cancel$"), handle_cancel)
    stop_handler = MessageHandler(filters.TEXT & filters.Regex(pattern="^Stop Sharing$"), handle_stop)

    application.add_handler(file_handler)
    application.add_handler(id_handler)
    application.add_handler(target_count_handler)  # Added handler
    application.add_handler(delay_handler)
    application.add_handler(cancel_handler)
    application.add_handler(stop_handler)

    # Unknown command handler
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    # Job to reset the daily limit (Run at midnight)
    job_daily_reset = job_queue.run_daily(reset_daily_limit, time=datetime.time(0, 0))  # Midnight

    application.run_polling()