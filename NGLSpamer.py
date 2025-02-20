import asyncio
import logging
import random
import re
import aiohttp
from typing import Dict, List, Tuple, Optional

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, constants
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    ApplicationBuilder
)
import threading

# --- Constants ---
GET_FILE, GET_ID, GET_DELAY, GET_LIMIT = range(4)
TOKEN = "7766543633:AAHZv7YVvjnTExyvRFy6xufeyc2AGYJTVlA"  # Replace with your bot token!

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- User Agents ---
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
running_threads = []  # Keep track of active sharing threads globally

def cleanup_threads():
    global running_threads
    running_threads = [t for t in running_threads if t.is_alive()]
# --- Helper Functions ---

async def get_token(cookie: str) -> Optional[str]:
    """Asynchronously gets the Facebook access token from a cookie, handling different response formats."""
    headers = {
        "authority": "business.facebook.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "cache-control": "max-age=0",
        "cookie": cookie,
        "referer": "https://www.facebook.com/",
        "sec-ch-ua": '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": random.choice(user_agents),
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://business.facebook.com/content_management",
                headers=headers,
                timeout=15,
            ) as response:
                response_text = await response.text()

                # More robust token extraction using regular expressions:
                match = re.search(r'"accessToken":"(EAAG[^"]+)"', response_text)
                if match:
                    return match.group(1)

                match = re.search(r'EAAG[a-zA-Z0-9]+', response_text)
                if match:
                    return match.group(0)

                # Look for tokens of the format EAAB....
                match = re.search(r'"token":"(EAAB[^"]+)"', response_text)
                if match:
                    return match.group(1)
                
                logger.warning(f"Could not get token from cookie: {cookie[:50]}...")
                return None

    except (aiohttp.ClientError, asyncio.TimeoutError, Exception) as e:
        logger.error(f"Error getting token for cookie: {cookie[:50]}... Error: {e}")
        return None

async def share_post(cookie_token: str, id_share: str) -> bool:
    """Asynchronously shares a post to Facebook."""
    cookie, token = cookie_token.split("|")
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate",
        "connection": "keep-alive",
        "content-length": "0",
        "cookie": cookie,
        "host": "graph.facebook.com",
        "user-agent": random.choice(user_agents),
        "referer": f"https://m.facebook.com/{id_share}",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://graph.facebook.com/me/feed?link=https://m.facebook.com/{id_share}&published=0&access_token={token}",
                headers=headers,
                timeout=10,
            ) as response:
                response_json = await response.json()
                if "id" in response_json:
                    return True
                else:
                    logger.warning(
                        f"Share failed: ID: {id_share} - Response: {response_json}"
                    )
                    return False
    except (aiohttp.ClientError, asyncio.TimeoutError, Exception) as e:
        logger.error(f"Error sharing post: ID: {id_share} - Error: {e}")
        return False

async def run_sharing_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs the sharing process with loaded cookies."""
    user_data = context.user_data
    total_share_limit = user_data['limit']
    shared_count = 0
    user_id = update.effective_user.id

    if not user_data.get('all_tokens'):  # Check if tokens are available.
        await update.message.reply_text("No valid tokens found. Please start over with /share.")
        return ConversationHandler.END
    async def share_single(cookie_token, id_share, update, user_id):
      """Helper function for sharing a single post."""
      if context.user_data.get('stop_requested', {}).get(user_id, False):
          return False

      success = await share_post(cookie_token, id_share)
      if success:
          await update.message.reply_text(
              f'[{cookie_token.split("|")[0][-8:]}] SHARE THÀNH CÔNG ID {id_share}',  # Display last 8 chars of cookie
              quote=False
          )
      return success

    continue_sharing = True
    while continue_sharing:

      if context.user_data.get('stop_requested', {}).get(user_id, False):
          break
      for cookie_token in user_data['all_tokens']:
            # Check stop request before each share
            if context.user_data.get('stop_requested', {}).get(user_id, False):
              continue_sharing = False
              break
          # Await share_single, not creating a separate task

            share_success = await share_single(cookie_token, user_data['id_share'], update,user_id)
            if share_success:
              shared_count +=1
            if total_share_limit > 0 and shared_count >= total_share_limit:
              continue_sharing = False  # Or = user_data['stop_requested']
              break

            if share_success:  # Only wait if the share was successful.
              await asyncio.sleep(user_data['delay'] + random.uniform(-1, 1))

    await update.message.reply_text(
        "Quá trình share hoàn tất." +
        (" Đạt giới hạn!" if total_share_limit > 0 and shared_count >= total_share_limit else ""),
         parse_mode=constants.ParseMode.HTML)



# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the bot and sends a welcome message."""
    await update.message.reply_text(
        "Chào mừng đến với Bot Share Facebook!\n"
        "Để bắt đầu, hãy dùng lệnh /share."
    )


async def share(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to get sharing details."""
    # Reset stop request state
    if 'stop_requested' not in context.user_data:
        context.user_data['stop_requested'] = {}
    user_id = update.effective_user.id  # Initialize stop_requested for the user.
    context.user_data['stop_requested'][user_id] = False

    await update.message.reply_text(
        "Vui lòng gửi file cookies (mỗi cookie trên một dòng).",
    )
    return GET_FILE



async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the cookies file and extracts tokens."""
    user_data = context.user_data
    user_id = update.effective_user.id
    try:
        file = await update.message.document.get_file()
        file_content = await file.download_as_bytearray()
        cookies_list = file_content.decode().splitlines()
        user_data["cookies"] = cookies_list


        all_tokens_coros = [get_token(cookie.strip()) for cookie in cookies_list if cookie.strip()]
        all_tokens = await asyncio.gather(*all_tokens_coros) #gather all tokens
        user_data['all_tokens'] = [f"{c.strip()}|{t}" for c, t in zip(cookies_list, all_tokens) if t is not None]

        if not user_data['all_tokens']:
          await update.message.reply_text("Không tìm thấy token hợp lệ.  Hãy thử lại với file cookie khác hoặc kiểm tra cookie.")
          return GET_FILE  # Stay in the same state

        await update.message.reply_text(f"Đã nhận {len(user_data['all_tokens'])} token hợp lệ.")
        await update.message.reply_text("Vui lòng nhập ID bài viết cần share.")
        return GET_ID
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await update.message.reply_text("Có lỗi xảy ra khi xử lý file. Vui lòng gửi lại file.")
        return GET_FILE




async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the ID to be shared."""
    user_data = context.user_data
    id_share = update.message.text.strip()
    if not re.match(r"^\d+$", id_share):  # Basic validation for numeric ID.
      await update.message.reply_text("ID bài viết không hợp lệ. Vui lòng nhập lại.")
      return GET_ID
    user_data["id_share"] = id_share
    await update.message.reply_text("Vui lòng nhập thời gian delay giữa các lần share (giây).")
    return GET_DELAY



async def get_delay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the delay."""
    user_data = context.user_data
    try:
        delay = int(update.message.text.strip())
        if delay < 0:
          raise ValueError
        user_data["delay"] = delay
        await update.message.reply_text(
            "Vui lòng nhập tổng số share (nhập 0 nếu không giới hạn)."
        )
        return GET_LIMIT
    except ValueError:
        await update.message.reply_text("Delay không hợp lệ (phải là số nguyên không âm). Vui lòng nhập lại.")
        return GET_DELAY




async def get_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the share limit and starts sharing."""
    user_data = context.user_data

    try:
        limit = int(update.message.text.strip())
        if limit < 0:
          raise ValueError
        user_data["limit"] = limit
         # Run the sharing process in a separate thread
    except ValueError:
        await update.message.reply_text("Số lượng share không hợp lệ. Vui lòng nhập lại.")
        return GET_LIMIT
    cleanup_threads()
    thread = threading.Thread(target=lambda: asyncio.run(run_sharing_process(update, context)))

    user_id = update.effective_user.id  # Get user ID
    thread.start()

    return ConversationHandler.END

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the sharing process."""

    user_id = update.effective_user.id
    # Set the stop request flag in user_data, this part is thread-safe
    if 'stop_requested' not in context.user_data:
        context.user_data['stop_requested'] = {}

    context.user_data['stop_requested'][user_id] = True
    await update.message.reply_text("Đang dừng quá trình share...")




async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation."""
    await update.message.reply_text("Đã hủy.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END




# --- Main Function ---
def main() -> None:
    """Starts the bot."""

    application = ApplicationBuilder().token(TOKEN).build()  # Use ApplicationBuilder

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("share", share)],
        states={
            GET_FILE: [MessageHandler(filters.Document.ALL, get_file)],
            GET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_id)],
            GET_DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay)],
            GET_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_limit)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == "__main__":
    main()