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

# Replace with your actual bot token
BOT_TOKEN = "7766543633:AAHd5v0ILieeJdpnRTCdh2RvzV1M8jli4uc"
ADMIN_ID = 6940071938  # Replace with your Telegram User ID
DAILY_SHARE_LIMIT = 5000

bot = telebot.TeleBot(BOT_TOKEN)

user_states = {} # Track user's progress in the share process.
user_share_counts = {}  # Track user's daily share counts.

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
            home_business = requests.get('https://business.facebook.com/content_management', headers=header_, timeout=15).text
            if 'EAAG' in home_business:
                token = home_business.split('EAAG')[1].split('","')[0]
                cookie_token = f'{cookie}|EAAG{token}'
                gome_token.append(cookie_token)
            else:
                bot.send_message(message.chat.id, f"[!] Không thể lấy token từ cookie: {cookie[:50]}... Cookie có thể không hợp lệ.")
        except requests.exceptions.RequestException as e:
             bot.send_message(message.chat.id, f"[!] Lỗi khi lấy token cho cookie: {cookie[:50]}... {e}")
        except Exception as e:
             bot.send_message(message.chat.id, f"[!] Lỗi không mong muốn khi lấy token cho cookie: {cookie[:50]}... {e}")
    return gome_token

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
            print(f"[!] Share thất bại: ID: {id_share} - Phản hồi: {res}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[!] Lỗi request share: ID: {id_share} - {e}")
        return False
    except Exception as e:
        print(f"[!] Lỗi không mong muốn khi share: ID: {id_share} - {e}")
        return False


def share_thread(user_id, tach, id_share, stt):
    if share(tach, id_share):
        bot.send_message(user_id, f'[{stt}] SHARE THÀNH CÔNG ID {id_share}')
        return True
    else:
        bot.send_message(user_id, f'[{stt}] SHARE THẤT BẠI ID {id_share}')
        return False

def reset_daily_share_counts():
    global user_share_counts
    user_share_counts = {}
    print("Daily share counts reset.")
    threading.Timer(86400, reset_daily_share_counts).start()  # Reset every 24 hours (86400 seconds)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Chào mừng bạn đến với tool share Facebook!\nSử dụng /share để bắt đầu.")

@bot.message_handler(commands=['share'])
def share_command(message):
    user_id = message.chat.id
    user_states[user_id] = {"step": "waiting_for_cookie_file"}
    bot.send_message(user_id, "Vui lòng gửi file chứa Cookies (cookies.txt).")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.chat.id

    if user_id not in user_states or user_states[user_id]["step"] != "waiting_for_cookie_file":
        bot.reply_to(message, "Vui lòng sử dụng lệnh /share trước khi gửi file.")
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        cookie_file = downloaded_file.decode('utf-8').splitlines()  # Split into lines
        user_states[user_id]["cookie_file"] = cookie_file
        bot.send_message(user_id, "Đã nhận file Cookies. Vui lòng nhập ID bài viết cần share:")
        user_states[user_id]["step"] = "waiting_for_post_id"

    except Exception as e:
        bot.reply_to(message, f"Lỗi khi xử lý file: {e}")
        del user_states[user_id]

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("step") == "waiting_for_post_id")
def handle_post_id(message):
    user_id = message.chat.id
    post_id = message.text.strip()

    if not post_id:
        bot.send_message(user_id, "ID bài viết không hợp lệ. Vui lòng nhập lại:")
        return

    user_states[user_id]["post_id"] = post_id
    bot.send_message(user_id, "Vui lòng nhập delay giữa các lần share (giây):")
    user_states[user_id]["step"] = "waiting_for_delay"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("step") == "waiting_for_delay")
def handle_delay(message):
    user_id = message.chat.id
    delay_str = message.text.strip()

    try:
        delay = int(delay_str)
        if delay < 0:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, "Delay không hợp lệ. Vui lòng nhập một số nguyên dương:")
        return

    user_states[user_id]["delay"] = delay
    bot.send_message(user_id, "Vui lòng nhập tổng số lượng share (0 để không giới hạn):")
    user_states[user_id]["step"] = "waiting_for_share_limit"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("step") == "waiting_for_share_limit")
def handle_share_limit(message):
    user_id = message.chat.id
    limit_str = message.text.strip()

    try:
        share_limit = int(limit_str)
        if share_limit < 0:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, "Số lượng share không hợp lệ. Vui lòng nhập một số nguyên dương hoặc 0:")
        return

    user_states[user_id]["share_limit"] = share_limit
    start_sharing(message)

def start_sharing(message):
    user_id = message.chat.id
    state = user_states.get(user_id)

    if not state or "cookie_file" not in state or "post_id" not in state or "delay" not in state or "share_limit" not in state:
        bot.send_message(user_id, "Có lỗi xảy ra. Vui lòng bắt đầu lại bằng lệnh /share.")
        del user_states[user_id]
        return

    cookie_file = state["cookie_file"]
    post_id = state["post_id"]
    delay = state["delay"]
    share_limit = state["share_limit"]

    all_tokens = get_token(cookie_file)
    total_live = len(all_tokens)

    if total_live == 0:
        bot.send_message(user_id, "Không tìm thấy token hợp lệ nào. Vui lòng kiểm tra lại file Cookies.")
        del user_states[user_id]
        return

    bot.send_message(user_id, f"Đã tìm thấy {total_live} token hợp lệ. Bắt đầu share...")

    # Check daily limit
    if user_id not in user_share_counts:
        user_share_counts[user_id] = 0

    if user_id != ADMIN_ID and user_share_counts[user_id] >= DAILY_SHARE_LIMIT:
        bot.send_message(user_id, f"Bạn đã đạt giới hạn {DAILY_SHARE_LIMIT} share mỗi ngày. Vui lòng thử lại sau.")
        del user_states[user_id]
        return

    stt = 0
    shared_count = 0
    continue_sharing = True

    for tach in all_tokens:
        if not continue_sharing:
            break

        stt += 1
        thread = threading.Thread(target=sharing_thread, args=(user_id, tach, post_id, stt, delay))
        thread.start()
        time.sleep(delay)
        shared_count += 1

        if user_id != ADMIN_ID:
            user_share_counts[user_id] += 1

        if share_limit > 0 and shared_count >= share_limit:
            continue_sharing = False
            bot.send_message(user_id, f"Đã đạt giới hạn share là {share_limit} shares.")
            break

        if user_id != ADMIN_ID and user_share_counts[user_id] >= DAILY_SHARE_LIMIT:
            continue_sharing = False
            bot.send_message(user_id, f"Bạn đã đạt giới hạn {DAILY_SHARE_LIMIT} share mỗi ngày. Vui lòng thử lại sau.")
            break

    del user_states[user_id]  # Clean up the user's state

def sharing_thread(user_id, tach, post_id, stt, delay):
        if share(tach, post_id):
            bot.send_message(user_id, f'[{stt}] SHARE THÀNH CÔNG ID {post_id}')
        else:
            bot.send_message(user_id, f'[{stt}] SHARE THẤT BẠI ID {post_id}')

if __name__ == '__main__':
    reset_daily_share_counts() # Start the daily reset timer.
    bot.infinity_polling()