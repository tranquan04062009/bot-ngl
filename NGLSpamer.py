import os
import sys
import requests
import threading
import time
import random
import asyncio
from telegram import Update, ForceReply, constants
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackContext,
)

# --- Constants and Configuration ---
TOKEN = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo"  # Replace with your bot token
__Copyright__ = "Trần Quân✔️"
__version__ = "v2_telegram"

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
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.259 Mobile Safari/537.36",
]


# --- Global Variables ---
active_shares = {}  # Dictionary to store active sharing processes {chat_id: {"stop_event": threading.Event(), ...}}
lock = asyncio.Lock() # Lock for thread safety

# --- Helper Functions ---
def get_token_from_cookie(cookie: str) -> str | None:
    """Extracts a Facebook access token from a cookie."""
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
        response = requests.get(
            "https://business.facebook.com/content_management",
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        home_business = response.text
        if "EAAG" in home_business:
            token = home_business.split("EAAG")[1].split('","')[0]
            return f"EAAG{token}"
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}")  # Log the error
        return None
    except Exception as e:
        print(f"An unexpected error occurred during token retrieval: {e}")
        return None

def share_post(cookie: str, token: str, id_share: str) -> bool:
    """Shares a Facebook post using a cookie and token."""
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
        response = requests.post(
            f"https://graph.facebook.com/me/feed?link=https://m.facebook.com/{id_share}&published=0&access_token={token}",
            headers=headers,
            timeout=15,  # Increased timeout
        )
        response.raise_for_status()
        return "id" in response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error during share: {e}")  # Log the error
        return False
    except Exception as e:
        print(f"Unexpected error during share: {e}")
        return False

async def process_share(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    cookies: list[str],
    id_share: str,
    delay: int,
    total_share_limit: int,
):
    """Handles the core sharing logic."""
    chat_id = update.effective_chat.id
    stop_event = threading.Event()

    async with lock:
        active_shares[chat_id] = {
            "stop_event": stop_event,
            "shared_count": 0,
            "total_live": 0, # Initialize total_live
        }
    
    tokens = []
    for cookie in cookies:
        token = get_token_from_cookie(cookie)
        if token:
            tokens.append((cookie, token))
            async with lock:
                active_shares[chat_id]["total_live"] += 1  # Increment total_live for each valid token

    if not tokens:
        await update.message.reply_text("No valid tokens found.")
        async with lock:
            del active_shares[chat_id]  # Clean up if no tokens
        return

    await update.message.reply_text(f"Found {active_shares[chat_id]['total_live']} valid tokens. Starting sharing...")
    
    shared_count = 0
    
    for cookie, token in tokens:
        if stop_event.is_set():
            break

        success = share_post(cookie, token, id_share)
        if success:
            shared_count += 1
            async with lock:
                active_shares[chat_id]["shared_count"] = shared_count  # Update shared_count
            await update.message.reply_text(
                f"Share successful! (Count: {shared_count}, Cookie: ...{cookie[-10:]})"  # Show last 10 chars of cookie
                , parse_mode=constants.ParseMode.MARKDOWN_V2
            )
        else:
            await update.message.reply_text(
                f"Share failed! (Cookie: ...{cookie[-10:]})", parse_mode=constants.ParseMode.MARKDOWN_V2
            )

        if total_share_limit > 0 and shared_count >= total_share_limit:
            break

        if not stop_event.is_set():
            await asyncio.sleep(delay)  # Use asyncio.sleep for non-blocking delay

    async with lock:
        if chat_id in active_shares: # Check if it still exist
             del active_shares[chat_id]

    await update.message.reply_text(f"Sharing process completed. Total shares: {shared_count}")



# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!  Send /share to start sharing.",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message."""
    help_text = """
    *Commands:*
    /start - Start the bot
    /help - Show this help message
    /share - Start the sharing process. The bot will ask for:
        1.  A `.txt` file containing cookies (one cookie per line).
        2.  The Facebook post ID to share.
        3.  The delay between shares (in seconds).
        4.  The total number of shares (0 for unlimited).
    /stop - Stop the current sharing process.

    *Example Usage (Important):*
    1. Send /share
    2. Send the cookies file.
    3. Send the post ID.
    4. Send the delay (e.g., 10).
    5. Send the total shares (e.g., 0).
    """
    await update.message.reply_text(help_text, parse_mode=constants.ParseMode.MARKDOWN_V2)



async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initiates the sharing process."""
    chat_id = update.effective_chat.id
    if chat_id in active_shares:
        await update.message.reply_text("A sharing process is already running. Use /stop to stop it.")
        return

    context.user_data["state"] = "awaiting_file"
    await update.message.reply_text("Please send me the .txt file containing your cookies (one cookie per line).")



async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages based on the current state."""
    chat_id = update.effective_chat.id
    state = context.user_data.get("state")

    if state == "awaiting_id":
        context.user_data["id_share"] = update.message.text
        context.user_data["state"] = "awaiting_delay"
        await update.message.reply_text("Enter the delay between shares (in seconds):")

    elif state == "awaiting_delay":
        try:
            delay = int(update.message.text)
            if delay < 0:
                raise ValueError("Delay must be non-negative")
            context.user_data["delay"] = delay
            context.user_data["state"] = "awaiting_total_shares"
            await update.message.reply_text("Enter the total number of shares (0 for unlimited):")
        except ValueError:
            await update.message.reply_text("Invalid delay value. Please enter a non-negative integer.")

    elif state == "awaiting_total_shares":
        try:
            total_shares = int(update.message.text)
            if total_shares < 0:
                raise ValueError("Total shares must be non-negative")
            context.user_data["total_shares"] = total_shares

            cookies = context.user_data.get("cookies", [])
            id_share = context.user_data.get("id_share")
            delay = context.user_data.get("delay")

            if not all([cookies, id_share, delay is not None, total_shares is not None]): #check for valid data
                await update.message.reply_text("Missing required information. Start again with /share")
                context.user_data.clear() # clean up user data.
                return

            await process_share(
                update, context, cookies, id_share, delay, total_shares
            )
            context.user_data.clear()  # Clear user data after processing

        except ValueError:
            await update.message.reply_text("Invalid total shares value.  Please enter a non-negative integer.")



async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles file uploads (specifically, the cookies file)."""
    chat_id = update.effective_chat.id
    state = context.user_data.get("state")
    if state != "awaiting_file":
        return  # Ignore if not waiting for a file

    file = await update.message.document.get_file()
    file_path = f"{file.file_id}.txt"  # Use file ID for unique filename
    await file.download_to_drive(file_path)

    try:
        with open(file_path, "r") as f:
            cookies = [line.strip() for line in f if line.strip()]  # Read and clean cookies
        if not cookies:
            await update.message.reply_text("The file is empty. Please provide a file with cookies.")
            return
        context.user_data["cookies"] = cookies
        context.user_data["state"] = "awaiting_id"
        await update.message.reply_text("Now, send me the Facebook post ID you want to share.")
    except Exception as e:
        await update.message.reply_text(f"Error reading the file: {e}")
        context.user_data.clear()  # Reset on error
    finally:
        try:  # Ensure file deletion
            os.remove(file_path)
        except FileNotFoundError:
            pass


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the currently active sharing process."""
    chat_id = update.effective_chat.id
    async with lock:
        if chat_id in active_shares:
            active_shares[chat_id]["stop_event"].set()
            await update.message.reply_text("Stopping the sharing process...")
            # No need to delete from dictionary here. The thread will handle it.
        else:
            await update.message.reply_text("No sharing process is currently running.")



# --- Main Application Setup ---
def main() -> None:
    """Starts the Telegram bot."""
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("share", share_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.TEXT, handle_file))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bot stopped by user.")
        sys.exit(0)