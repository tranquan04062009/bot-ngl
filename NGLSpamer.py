import random
import string
import requests
import os
import time
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.ext import ConversationHandler

# Thay thế bằng token bot của bạn
BOT_TOKEN = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo"


# Các trạng thái cho conversation
(
    USERNAME,
    MESSAGE_TEXT,
    COUNT,
    DELAY,
) = range(4)

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


async def send_ngl_message(nglusername, message, count, delay, update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = 0
    notsend = 0
    use_proxy = True
    proxies = Proxy()
    
    if proxies is None:
        use_proxy = False
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Không tìm thấy proxy. Chuyển sang chế độ không dùng proxy.")

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Bắt đầu gửi tin nhắn...")

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
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Đã gửi => {value}")
            else:
                notsend += 1
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Lỗi gửi tin nhắn")
                
            if notsend == 4:
                if use_proxy:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="Đang thay đổi thông tin và proxy...")
                    proxies = Proxy()
                    if proxies is None:
                        use_proxy = False
                        await context.bot.send_message(chat_id=update.effective_chat.id, text="Proxy lỗi. Chuyển sang chế độ không dùng proxy.")
                else:
                     await context.bot.send_message(chat_id=update.effective_chat.id, text="Đang thay đổi thông tin...")

                deviceId()
                UserAgent()
                notsend = 0
           
            time.sleep(delay)

        except requests.exceptions.ProxyError as e:
            if use_proxy:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Lỗi Proxy!")
                proxies = Proxy()
                if proxies is None:
                    use_proxy = False
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="Proxy lỗi. Chuyển sang chế độ không dùng proxy.")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Lỗi: không dùng proxy")

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hoàn tất gửi tin nhắn!")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Chào bạn! Hãy sử dụng lệnh /ngl để bắt đầu gửi tin nhắn.")

async def ngl_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Nhập tên người dùng NGL:")
    return USERNAME

async def ngl_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    context.user_data['username'] = username
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Nhập tin nhắn muốn gửi:")
    return MESSAGE_TEXT

async def ngl_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    context.user_data['message'] = message
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Nhập số lượng tin nhắn muốn gửi:")
    return COUNT

async def ngl_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count <= 0:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Số lượng phải lớn hơn 0, nhập lại:")
            return COUNT

        context.user_data['count'] = count
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Nhập delay giữa các tin nhắn (giây):")
        return DELAY
    except ValueError:
       await context.bot.send_message(chat_id=update.effective_chat.id, text="Số lượng phải là số, vui lòng nhập lại:")
       return COUNT

async def ngl_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        delay = float(update.message.text)
        if delay < 0:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Delay phải lớn hơn hoặc bằng 0, nhập lại:")
            return DELAY
        
        context.user_data['delay'] = delay
        
        nglusername = context.user_data['username']
        message = context.user_data['message']
        count = context.user_data['count']
        delay = context.user_data['delay']

        await send_ngl_message(nglusername, message, count, delay, update, context)
        return ConversationHandler.END
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Delay phải là số, vui lòng nhập lại:")
        return DELAY

async def ngl_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Đã hủy gửi tin nhắn.")
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("ngl", ngl_start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ngl_username)],
            MESSAGE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ngl_message)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ngl_count)],
            DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ngl_delay)],
        },
        fallbacks=[CommandHandler("cancel", ngl_cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))

    application.run_polling()

if __name__ == '__main__':
    main()