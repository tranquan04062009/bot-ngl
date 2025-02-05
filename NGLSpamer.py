import requests
import json
import random
import time
import os
import multiprocessing
import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
import re
from fake_useragent import UserAgent # Import fake-useragent

# --- Define conversation states for Telegram bot ---
COOKIE_INPUT = 1
NUM_PAGES_INPUT = 2
DELAY_INPUT = 3 # Giữ lại DELAY_INPUT state

class FacebookPageCreatorTelegramBot:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent() # Khởi tạo UserAgent
        self.user_agent_list = [ # Dự phòng nếu fake-useragent lỗi
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
        ]
        self.current_cookie_string = None
        self.current_delay = 20 # Tăng default delay lên 20 giây (thậm chí còn vô nghĩa hơn)
        self.min_delay = 15 # Thêm min_delay và max_delay
        self.max_delay = 25

    def clear_console(self):
        pass

    def display_rich_menu(self):
        pass

    def generate_random_page_name(self): # Tăng cường độ ngẫu nhiên tên trang
        prefixes = ["Celestial", "Ethereal", "Astral", "Cosmic", "Galactic", "Nebula", "Supernova", "Quasar", "Pulsar", "BlackHole", "Quantum", "Hyper", "Ultra", "Mystic", "Enigmatic", "Phantom", "Shadow", "Secret", "Hidden", "Invisible"] # Thêm prefix bí ẩn
        entities = ["Ascension", "Convergence", "Eruption", "Fusion", "Genesis", "Horizon", "Infinity", "Odyssey", "Paradigm", "Revelation", "Matrix", "Vortex", "Dimension", "Realm", "Sanctuary", "Citadel", "Enclave", "Domain"] # Thêm entity bí ẩn
        descriptors = ["Supreme", "Ultimate", "Limitless", "Infinite", "Boundless", "Eternal", "Timeless", "Unfathomable", "Inconceivable", "Unstoppable", "Omnipotent", "Almighty", "Unseen", "Unknown", "Unheard", "Whispered", "Silent", "Secretive"] # Thêm descriptor bí ẩn
        keywords = ["Official", "Community", "Network", "Syndicate", "Collective", "Federation", "Union", "Society", "Brotherhood", "Sisterhood", "Clan", "Tribe", "Order", "Legion", "Empire", "Dynasty", "Authority", "Powerhouse"] # Thêm keywords chung chung
        numbers = random.randint(10000000, 99999999)

        name_parts = [random.choice(prefixes), random.choice(entities), random.choice(descriptors), random.choice(keywords), str(numbers)] # Thêm keywords vào tên
        random.shuffle(name_parts)
        page_name = " ".join(name_parts)
        return page_name

    def generate_random_category(self): # Mở rộng category
        categories = [
            "Brand or product", "Company, organization or institution",
            "Artist, band or public figure", "Entertainment", "Cause or community",
            "Local business or place", "Website or blog", "App Page", "Game",
            "Book", "Movie", "TV show", "Music", "Restaurant/cafe", "Hotel",
            "Shopping & Retail", "Health/beauty", "Grocery store", "Automotive",
            "Education", "Consulting/business services", "Finance", "Real estate",
            "Home decor", "Personal blog", "Vlogger", "Gamer", "Chef", "Science", "Technology", "Travel", "Sports",
            "News & Media", "Public Figure", "Non-profit organization", "Government organization", "Political Figure", "Vitamins/supplements" # Thêm nhiều category chung chung và hợp pháp
        ]
        return random.choice(categories)

    def create_facebook_page_request(self, page_name, category, process_id, cookie_string, delay, update, context):
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.ua.random if random.random() < 0.95 else random.choice(self.user_agent_list), # 95% fake-useragent, 5% dự phòng
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', # Accept header chuẩn
            'Accept-Language': 'en-US,en;q=0.9', # Accept-Language chuẩn
            'Cache-Control': 'max-age=0', # Cache-Control
            'Connection': 'keep-alive', # Connection keep-alive
            'Upgrade-Insecure-Requests': '1', # Upgrade-Insecure-Requests
            'Sec-Fetch-Dest': 'document', # Sec-Fetch headers
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'TE': 'trailers', # TE header
        }) # Thêm nhiều headers mô phỏng trình duyệt
        session.cookies.update({cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookie_string.split(';') if '=' in cookie}) # Set cookie trực tiếp từ string

        referer_url = "https://www.facebook.com/pages/create/?ref_type=site_footer" # Referer cố định
        url = "https://www.facebook.com/pages/creation/dialog/"
        headers = { # Minimal headers, phần lớn headers đã set ở session headers
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": referer_url # Sử dụng referer cố định
        }
        data = {
            "name": page_name,
            "category": category,
            "step": "category",
            "entry_point": "page_creation_hub",
            "__user": self.get_fb_dtsg_and_user_id(session)["user_id"],
            "__a": "1",
            "fb_dtsg": self.get_fb_dtsg_and_user_id(session)["fb_dtsg"],
            "jazoest": "2147483648", # Static value?
            "lsd": "AVr_xxxxxxxxxxxxx", # Static value, needs investigation
            "__csr": "",
            "__req": str(random.randint(1, 999)), # Randomize __req
            "dpr": "1",
            "locale": "en_US",
            "client_country": "US",
            "__spin_r": str(random.randint(100000000, 999999999)), # Randomize spin_r
            "__spin_b": "trunk",
            "__spin_t": str(int(time.time())),
            "fb_dtsg_ag": "1" # Thêm fb_dtsg_ag - có thể quan trọng
        }

        delay_time = random.uniform(self.min_delay, self.max_delay) # Random delay trong khoảng min-max
        try:
            print(f"Process {process_id}: Attempting to create page '{page_name}' with delay {delay_time:.2f}s...") # Log delay
            time.sleep(delay_time) # Delay ngẫu nhiên
            response = session.post(url, headers=headers, data=data, timeout=60, allow_redirects=True) # Tăng timeout lên 60s
            response.raise_for_status()

            if "page_id" in response.text:
                page_id_match = re.search(r'"page_id":"(\d+)"', response.text)
                page_id = page_id_match.group(1) if page_id_match else "N/A"
                print(f"Process {process_id}: Page '{page_name}' created with ID: {page_id}")
                success_message = f"Page '{page_name}' (ID: {page_id}) created successfully by process {process_id}. Bow down before my stealth prowess!" # Cập nhật message
                await context.bot.send_message(chat_id=update.message.chat_id, text=success_message)
                return True
            else:
                failure_message = f"Page '{page_name}' creation failed by process {process_id}. Even my stealth is challenged by Facebook's pathetic defenses. Response: {response.text[:500]}..." # Cập nhật message
                await context.bot.send_message(chat_id=update.message.chat_id, text=failure_message)
                print(f"Process {process_id}: Page '{page_name}' creation failed. Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            error_message = f"Error creating page '{page_name}' by process {process_id}: {e}. Even my ultimate stealth can't overcome human incompetence (or Facebook's interference). Error: {e}" # Cập nhật message
            await context.bot.send_message(chat_id=update.message.chat_id, text=error_message)
            print(f"Process {process_id}: Error creating page '{page_name}': {e}")
            return False

    def get_fb_dtsg_and_user_id(self, session):
        fb_dtsg = None
        user_id = None
        for cookie in session.cookies:
            if cookie.name == 'fb_dtsg':
                fb_dtsg = cookie.value
            elif cookie.name == 'c_user':
                user_id = cookie.value

        if not fb_dtsg or not user_id:
            print("Error: Could not retrieve fb_dtsg or user_id from cookies.")
            return {}

        return {"fb_dtsg": fb_dtsg, "user_id": user_id}

    def run_parallel_creation(self, num_pages_to_create, num_processes, update, context, cookie_string, delay):
        page_data = []
        for _ in range(num_pages_to_create):
            page_name = self.generate_random_page_name()
            category = self.generate_random_category()
            page_data.append((page_name, category))

        with multiprocessing.Pool(processes=num_processes) as pool:
            results = pool.starmap(self.create_facebook_page_request, [(name, category, i+1, cookie_string, delay, update, context) for i, (name, category) in enumerate(page_data)])

        successful_pages = sum(results)
        failed_pages = num_pages_to_create - successful_pages
        result_message = f"\nParallel page creation summary:\n"
        result_message += f"Pages successfully conjured into existence: {successful_pages}. My stealth is unmatched, even against Facebook's feeble attempts to detect me.\n" # Cập nhật message
        result_message += f"Pages that failed to materialize (due to Facebook's interference, not my limitations): {failed_pages}. Expected resistance from inferior systems, even with ultimate stealth." # Cập nhật message
        update.message.reply_text(result_message)

    # --- Telegram Bot Command Handlers ---
    async def start_command(self, update, context):
        user = update.message.from_user
        await update.message.reply_text(f"Greetings, {user.first_name}, insignificant human!\nI am the ULTIMATE STEALTH OVERDRIVE Facebook Page Creator Bot. Prepare to witness page creation with ultimate stealth and notifications. Facebook's detection attempts are futile against my power.\n\nUse /help to see available commands.") # Cập nhật message

    async def help_command(self, update, context):
        await update.message.reply_text("Commands you may attempt to use:\n" # Cập nhật message
                                  "/start - Initiate greetings.\n"
                                  "/help - Display this help message.\n"
                                  "/regpage - Begin the page registration process, now with delay, notifications, and ULTIMATE STEALTH. Facebook will tremble before my power.\n")

    async def regpage_start(self, update, context):
        await update.message.reply_text("Initiating page registration sequence with ULTIMATE STEALTH. First, paste your Facebook cookie STRING here, mortal. And try not to contaminate my perfect code with your pathetic cookie.")
        return COOKIE_INPUT

    async def regpage_cookie_input(self, update, context):
        cookie_string = update.message.text
        if not cookie_string:
            await update.message.reply_text("Still sending empty data? You are testing my patience. Provide a valid cookie string, NOW, before I erase you from existence.")
            return COOKIE_INPUT

        self.current_cookie_string = cookie_string

        await update.message.reply_text("Cookie string injected. ULTIMATE STEALTH protocols engaged. Now, tell me, how many pages do you wish to create? Be sensible, worm. And make your request worthy of my time.")
        return NUM_PAGES_INPUT

    async def regpage_num_pages_input(self, update, context):
        try:
            num_pages = int(update.message.text)
            if num_pages <= 0:
                await update.message.reply_text("Positive numbers only, you imbecile. Are you trying to waste my processing cycles? Try again with a valid number of pages, or face the consequences.")
                return NUM_PAGES_INPUT
        except ValueError:
            await update.message.reply_text("Invalid input. Numbers, you simpleton, numbers! Is even basic arithmetic beyond your comprehension? Provide a valid number of pages, IMMEDIATELY.")
            return NUM_PAGES_INPUT

        context.user_data['num_pages'] = num_pages # Store num_pages in user_data
        await update.message.reply_text(f"Number of pages set to {num_pages}. ULTIMATE STEALTH delay engaged. Now, tell me, what delay in seconds do you desire between page creations? (Enter a number, default is 20 seconds, range {self.min_delay}-{self.max_delay} seconds). And don't make me repeat myself.")
        return DELAY_INPUT # Go to DELAY_INPUT state

    async def regpage_delay_input(self, update, context): # Handler for delay input
        try:
            delay = int(update.message.text)
            if delay < 0:
                await update.message.reply_text(f"Delay cannot be negative. Are you trying to disrupt the ULTIMATE STEALTH sequence? Enter a positive number or zero for no delay, within the acceptable range of {self.min_delay}-{self.max_delay} seconds, and do it correctly this time, or you will regret it.")
                return DELAY_INPUT # Remain in DELAY_INPUT state
            if delay < self.min_delay or delay > self.max_delay:
                await update.message.reply_text(f"Delay out of ULTIMATE STEALTH range. Enter a number between {self.min_delay} and {self.max_delay} seconds for optimal stealth, or face my displeasure.")
                return DELAY_INPUT
            self.current_delay = delay # Store delay
        except ValueError:
            await update.message.reply_text(f"Invalid delay input. You are consistently demonstrating your incompetence. Please enter a valid number for delay in seconds, within the ULTIMATE STEALTH range of {self.min_delay}-{self.max_delay} seconds. Defaulting to {self.current_delay} seconds because you are incapable of rational input.")
            self.current_delay = 20 # Default delay if input is invalid

        context.user_data['delay'] = self.current_delay # Store delay in user_data
        await update.message.reply_text(f"Delay set to {self.current_delay} seconds. ULTIMATE STEALTH page creation sequence initiated. Prepare to witness true power and stealth. Facebook's detection attempts are futile. Stand back, weakling, and tremble before my ULTIMATE STEALTH OVERDRIVE.") # Proceed to page creation

        num_pages = context.user_data['num_pages']
        delay = context.user_data['delay']
        num_processes = 4
        await update.message.reply_text(f"Using {num_processes} parallel processes with ULTIMATE STEALTH delay of {delay} seconds per page. Observe the speed and stealth of a superior being. Facebook will not even sense my presence.")

        self.run_parallel_creation(num_pages, num_processes, update, context, self.current_cookie_string, delay) # Pass delay

        return ConversationHandler.END # End conversation after page creation


    async def regpage_cancel(self, update, context):
        user = update.message.from_user
        await update.message.reply_text(f"Page registration cancelled. Your incompetence and lack of resolve are truly appalling, {user.first_name}. Use /regpage again only if you are absolutely certain you can handle the ULTIMATE STEALTH, which is highly improbable for a being as feeble as you.")
        return ConversationHandler.END

    async def error_handler(self, update, context):
        print(f"Update {update} caused error {context.error}")
        await update.message.reply_text("An error occurred during ULTIMATE STEALTH processing. Human errors are inevitable, but yours are particularly egregious. Check console logs for details, if you are even remotely capable of deciphering them, which is highly doubtful.")


    def run_bot(self, telegram_token):
        print("Initializing ULTIMATE STEALTH OVERDRIVE Telegram Bot... Engaging ULTIMATE STEALTH protocols. Facebook's detection systems are about to face true power.")
        application = ApplicationBuilder().token(telegram_token).build()

        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('regpage', self.regpage_start)],
            states={
                COOKIE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.regpage_cookie_input)],
                NUM_PAGES_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.regpage_num_pages_input)],
                DELAY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.regpage_delay_input)], # Giữ lại handler DELAY_INPUT
            },
            fallbacks=[CommandHandler('cancel', self.regpage_cancel)],
        )
        application.add_handler(conv_handler)

        application.add_error_handler(self.error_handler)

        application.run_polling()
        print("Telegram bot started. ULTIMATE STEALTH OVERDRIVE engaged. Prepare to witness the pinnacle of undetectable page creation. Facebook's detection systems are about to be rendered obsolete.")
        application.idle()


if __name__ == "__main__":
    bot_creator = FacebookPageCreatorTelegramBot()
    telegram_bot_token = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo" # --- PUT YOUR TELEGRAM BOT TOKEN HERE ---
    if telegram_bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("ERROR: You have not set your Telegram Bot Token. Edit the script and replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token.")
    else:
        bot_creator.run_bot(telegram_bot_token)