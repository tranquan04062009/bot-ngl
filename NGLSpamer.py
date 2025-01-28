import random
import string
import requests
import os
import time
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Thay thế bằng token bot của bạn
BOT_TOKEN = "7550168223:AAHswDYG8ozk1QnpKSnxFo9UuNhYgCh6mco"

def deviceId():
    characters = string.ascii_lowercase + string.digits

    part1 = ''.join(random.choices(characters, k=8))
    part2 = ''.join(random.choices(characters, k=4))
    part3 = ''.join(random.choices(characters, k=4))
    part4 = ''.join(random.choices(characters, k=4))
    part5 = ''.join(random.choices(characters, k=12))

    device_id = f"{part1}-{part2}-{part3}-{part4}-{part5}"

    return device_id

def UserAgent():
    with open('user-agents.txt', 'r') as file:
        user_agents = file.readlines()
        random_user_agent = random.choice(user_agents).strip()
        
        return random_user_agent
        
def Proxy():
    with open('proxies.txt', 'r') as file:
        proxies_list = file.readlines()
        if not proxies_list:
            return None
        random_proxy = random.choice(proxies_list).strip()

    proxies = {
        'http': random_proxy,
        'https': random_proxy
    }
    return proxies

def send_ngl_message(nglusername, message, count, delay, update, context):
    value = 0
    notsend = 0
    use_proxy = True
    proxies = Proxy()
    
    if proxies is None:
        use_proxy = False
        context.bot.send_message(chat_id=update.effective_chat.id, text="Không tìm thấy proxy. Chuyển sang chế độ không dùng proxy.")

    context.bot.send_message(chat_id=update.effective_chat.id, text="Bắt đầu gửi tin nhắn...")

    while value < count:
        headers = {
            'Host': 'ngl.link',
            'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'user-agent': f'{UserAgent()}',
            'sec-ch-ua-platform': '"Windows"',
            'origin': 'https://ngl.link',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': f'https://ngl.link/{nglusername}',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        data = {
            'username': f'{nglusername}',
            'question': f'{message}',
            'deviceId': f'{deviceId()}',
            'gameSlug': '',
            'referrer': '',
        }

        try:
            if use_proxy:
                response = requests.post('https://ngl.link/api/submit', headers=headers, data=data, proxies=proxies)
            else:
                response = requests.post('https://ngl.link/api/submit', headers=headers, data=data)
            
            if response.status_code == 200:
                notsend = 0
                value += 1
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"Đã gửi => {value}")
            else:
                notsend += 1
                context.bot.send_message(chat_id=update.effective_chat.id, text="Lỗi gửi tin nhắn")
                
            if notsend == 4:
                if use_proxy:
                    context.bot.send_message(chat_id=update.effective_chat.id, text="Đang thay đổi thông tin và proxy...")
                    proxies = Proxy()
                    if proxies is None:
                        use_proxy = False
                        context.bot.send_message(chat_id=update.effective_chat.id, text="Proxy lỗi. Chuyển sang chế độ không dùng proxy.")
                else:
                     context.bot.send_message(chat_id=update.effective_chat.id, text="Đang thay đổi thông tin...")

                deviceId()
                UserAgent()
                notsend = 0
           
            time.sleep(delay)

        except requests.exceptions.ProxyError as e:
            if use_proxy:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Lỗi Proxy!")
                proxies = Proxy()
                if proxies is None:
                    use_proxy = False
                    context.bot.send_message(chat_id=update.effective_chat.id, text="Proxy lỗi. Chuyển sang chế độ không dùng proxy.")
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Lỗi: không dùng proxy")

    context.bot.send_message(chat_id=update.effective_chat.id, text="Hoàn tất gửi tin nhắn!")

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! Hãy sử dụng lệnh /ngl để bắt đầu gửi tin nhắn.")

def ngl_command(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Vui lòng nhập thông tin theo định dạng: \n\n/ngl <username> <tin nhắn> <số lượng> <delay (giây)>")

def handle_message(update, context):
    text = update.message.text
    if text.startswith('/ngl '):
        try:
            parts = text.split(' ', 5)
            if len(parts) != 5:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Định dạng không đúng. Vui lòng nhập theo định dạng: \n\n/ngl <username> <tin nhắn> <số lượng> <delay (giây)>")
                return
            
            _, nglusername, message, count, delay = parts
            count = int(count)
            delay = float(delay)

            if count <= 0 or delay < 0:
               context.bot.send_message(chat_id=update.effective_chat.id, text="Số lượng phải lớn hơn 0 và delay phải lớn hơn hoặc bằng 0")
               return
            
            send_ngl_message(nglusername, message, count, delay, update, context)
        
        except ValueError:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Lỗi: Số lượng và delay phải là số.")
        
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Lỗi: {e}")

    else:
       context.bot.send_message(chat_id=update.effective_chat.id, text="Vui lòng sử dụng lệnh /ngl để bắt đầu.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ngl", ngl_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()