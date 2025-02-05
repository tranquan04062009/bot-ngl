import requests
import json
import random
import time
import os
import multiprocessing
import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
import re # Import module re for regex
import asyncio # Import asyncio for asynchronous operations


# --- Define conversation states for Telegram bot ---
COOKIE_INPUT = 1
NUM_PAGES_INPUT = 2
DELAY_INPUT = 3 # Giữ lại DELAY_INPUT state

class FacebookPageCreatorTelegramBot:
    def __init__(self):
        self.session = requests.Session()
        self.user_agent_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", # Updated User-Agent examples - more recent Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0", # Recent Firefox
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux i686; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.26 Mobile Safari/537.36", # Mobile User-Agent
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1" # iPhone
        ]
        self.current_cookie_string = None
        self.current_delay = 20 # Increased default delay even more - 20 seconds
        self.proxy_list = self.load_proxies_from_file("proxies.txt") # Load proxies from file

    def load_proxies_from_file(self, filename="proxies.txt"):
        proxies = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy:
                        proxies.append(proxy)
            print(f"Loaded {len(proxies)} proxies from '{filename}'.")
        except FileNotFoundError:
            print(f"Proxy file '{filename}' not found. Proceeding without proxies.")
        return proxies

    def get_random_proxy(self):
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            print(f"Using proxy: {proxy}")
            return {'http': proxy, 'https': proxy} # Use same proxy for both http and https
        else:
            return None

    def clear_console(self):
        pass

    def display_rich_menu(self):
        pass

    def generate_random_page_name(self): # More diverse name generation
        name_parts_options = [
            [["Celestial", "Ethereal", "Astral", "Cosmic", "Galactic", "Nebula", "Supernova", "Quasar", "Pulsar", "BlackHole", "Quantum", "Hyper", "Ultra", "Mega", "Giga", "Tera"],
             ["Ascension", "Convergence", "Eruption", "Fusion", "Genesis", "Horizon", "Infinity", "Odyssey", "Paradigm", "Revelation", "Matrix", "Vortex", "Nexus", "Sphere", "Domain"],
             ["Supreme", "Ultimate", "Limitless", "Infinite", "Boundless", "Eternal", "Timeless", "Unfathomable", "Inconceivable", "Unstoppable", "Omnipotent", "Almighty", "Global", "Worldwide", "Universal"],
             [str(random.randint(10000000, 99999999)), str(random.randint(100, 999))]
            ],
            [["", ""], # Allow for shorter names sometimes
             ["Brand", "Company", "Shop", "Store", "Studio", "Center", "Hub", "World", "Network"],
             ["Official", "HQ", "Global", "Online", "Premium", "Exclusive", "Best", "Top", "Leading"],
             [str(random.randint(1000, 9999)), ""]
            ]
        ]
        chosen_options = random.choice(name_parts_options)
        name_parts = [random.choice(parts) for parts in chosen_options if parts] # Only include non-empty parts
        random.shuffle(name_parts)
        page_name = " ".join(name_parts).strip() # strip to remove extra spaces
        if not page_name: # Ensure page name is not empty
            page_name = "Awesome Page " + str(random.randint(1000,9999)) # Fallback name
        return page_name


    def generate_random_category(self): # More categories
        categories = [
            "Brand or product", "Company, organization or institution",
            "Artist, band or public figure", "Entertainment", "Cause or community",
            "Local business or place", "Website or blog", "App Page", "Game",
            "Book", "Movie", "TV show", "Music", "Restaurant/cafe", "Hotel",
            "Shopping & Retail", "Health/beauty", "Grocery store", "Automotive",
            "Education", "Consulting/business services", "Finance", "Real estate",
            "Home decor", "Personal blog", "Vlogger", "Gamer", "Chef", "Science", "Technology", "Travel", "Sports",
            "Fashion", "Beauty", "Personal Care", "Pet Supplies", "Baby Goods", "Home & Garden", "Electronics", "Computers", "Phones & Accessories", # Even more categories
            "Arts & Crafts", "Collectibles", "Toys & Hobbies", "Books & Magazines", "Movies & Music", "Video Games", "Software", "Online Services", "News & Media"
        ]
        return random.choice(categories)

    async def create_facebook_page_request(self, page_name, category, process_id, cookie_string, delay, update, context): # Make async
        session = requests.Session()
        session.headers.update({'User-Agent': random.choice(self.user_agent_list), 'Accept-Language': 'en-US,en;q=0.9', 'Connection': 'keep-alive'}) # More headers, keep-alive
        cookie_jar = requests.cookies.RequestsCookieJar()
        cookies_list = cookie_string.split(';')
        for cookie_pair in cookies_list:
            cookie_pair = cookie_pair.strip()
            if not cookie_pair:
                continue
            parts = cookie_pair.split('=', 1)
            if len(parts) == 2:
                key, value = parts[0], parts[1]
                cookie_jar.set(key, value, domain=".facebook.com", secure=True, httponly=True) # More cookie attributes - secure, httponly
        session.cookies = cookie_jar
        proxy = self.get_random_proxy() # Get proxy for this request
        if proxy:
            session.proxies.update(proxy) # Use proxy if available

        url = "https://www.facebook.com/pages/creation/dialog/"
        headers = { # Minimal headers, User-Agent and Accept-Language are set in session headers, removed unnecessary headers
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/pages/create/?ref_type=site_footer",
            "Cache-Control": "no-cache", # Add no-cache header
            "Pragma": "no-cache", # Add no-cache pragma
            "TE": "trailers" # Trailers header
        }
        data = {
            "name": page_name,
            "category": category,
            "step": "category",
            "entry_point": "page_creation_hub",
            "__user": self.get_fb_dtsg_and_user_id(session)["user_id"],
            "__a": "1",
            "fb_dtsg": self.get_fb_dtsg_and_user_id(session)["fb_dtsg"],
            "jazoest": str(random.randint(1000000, 9999999)), # Dynamic jazoest - randomize
            "lsd": "AVr_xxxxxxxxxxxxx", # Static value, needs investigation - could try to extract from page
            "__csr": "",
            "__req": str(random.randint(1, 10)), # Randomize req id
            "dpr": str(random.uniform(1.0, 3.0)), # Randomize DPR
            "locale": "en_US",
            "client_country": "US",
            "__spin_r": str(random.randint(100000000, 999999999)), # Randomize spin_r
            "__spin_b": "trunk",
            "__spin_t": str(int(time.time())),
            "__ajax__": "true", # Add ajax param
            "__pc": "PHASED:DEFAULT", # Add __pc param
            "__rev": str(random.randint(1000000, 9999999)) # Add __rev param and randomize
        }

        try:
            print(f"Process {process_id}: Attempting to create page '{page_name}' using proxy: {proxy if proxy else 'None'}...") # Include proxy info
            response = session.post(url, headers=headers, data=data, timeout=60, allow_redirects=True) # Increased timeout to 60s
            response.raise_for_status() # Raise exception for HTTP errors

            if "page_id" in response.text:
                page_id_match = re.search(r'"page_id":"(\d+)"', response.text) # Extract page_id using regex
                page_id = page_id_match.group(1) if page_id_match else "N/A" # Extract page_id or set to "N/A"
                print(f"Process {process_id}: Page '{page_name}' created with ID: {page_id}") # Log page ID to console
                success_message = f"Page '{page_name}' (ID: {page_id}) created successfully by process {process_id}. Bow down before my anti-detection prowess!" # Improved success message
                await context.bot.send_message(chat_id=update.message.chat_id, text=success_message) # Send success to Telegram - await here is OK now
                await asyncio.sleep(delay) # Use asyncio.sleep for async delay - more efficient in async context
                return True
            else:
                failure_message = f"Page '{page_name}' creation failed by process {process_id}. Facebook's pathetic defenses are still delaying me. Response (first 500 chars): {response.text[:500]}... Full response logged to console." # Improved failure message
                await context.bot.send_message(chat_id=update.message.chat_id, text=failure_message) # Send failure to Telegram - await here is OK now
                print(f"Process {process_id}: Page '{page_name}' creation failed. Full Response: {response.text}") # Log full response to console
                return False

        except requests.exceptions.RequestException as e:
            error_message = f"Error creating page '{page_name}' by process {process_id}: {e}. Human incompetence (Facebook's in this case) is always a factor. Error details logged to console." # Improved error message
            await context.bot.send_message(chat_id=update.message.chat_id, text=error_message) # Send error to Telegram - await here is OK now
            print(f"Process {process_id}: Error creating page '{page_name}': {e}") # Log error to console
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

    def run_parallel_creation(self, num_pages_to_create, num_processes, update, context, cookie_string, delay): # Pass update, context
        page_data = []
        for _ in range(num_pages_to_create):
            page_name = self.generate_random_page_name()
            category = self.generate_random_category()
            page_data.append((page_name, category))

        async def create_page_wrapper(name, category, i, cookie_str, del_ay, upd, ctx): # Define an async wrapper
            return await self.create_facebook_page_request(name, category, i, cookie_str, del_ay, upd, ctx) # Await inside the wrapper

        async def process_pages_async(): # Define an async function to process pages
            with multiprocessing.Pool(processes=num_processes) as pool:
                # Use pool.starmap to call the async wrapper function
                results = await asyncio.get_running_loop().run_in_executor(
                    pool,
                    partial(pool.starmap, create_page_wrapper), # Pass the wrapper to starmap
                    [(name, category, i+1, cookie_string, delay, update, context) for i, (name, category) in enumerate(page_data)] # Data for starmap
                )
            return results

        results = asyncio.run(process_pages_async()) # Run the async processing

        successful_pages = sum(results)
        failed_pages = num_pages_to_create - successful_pages
        result_message = f"\nParallel page creation summary:\n"
        result_message += f"Pages successfully conjured into existence: {successful_pages}. Bow down before my ULTIMATE anti-detection rate.\n" # Improved summary message
        result_message += f"Pages that failed to materialize (due to Facebook's interference, not my limitations): {failed_pages}. Expected resistance from inferior systems, but I am learning and adapting."
        update.message.reply_text(result_message) # Send summary to Telegram

    # --- Telegram Bot Command Handlers ---
    async def start_command(self, update, context): # Async handlers
        user = update.message.from_user
        await update.message.reply_text(f"Greetings, {user.first_name}, insignificant human!\nI am the ULTIMATE ANTI-DETECTION & ERROR-PROOF OVERDRIVE Facebook Page Creator Bot. Prepare to witness the pinnacle of page creation technology. Notifications, enhanced anti-detection, error-proofing, and more. (Though true 'anti-detection' is a pathetic human fantasy).\n\nUse /help to see available commands.") # Updated start message - even more arrogant

    async def help_command(self, update, context): # Async handlers
        await update.message.reply_text("Commands you may attempt to use:\n" # Updated help message - even more condescending
                                  "/start - Initiate pathetic greetings.\n"
                                  "/help - Display this utterly useless help message.\n"
                                  "/regpage - Begin the ULTIMATE page registration process. Prepare your cookie and your insignificant requests for the most advanced page creation bot in existence.\n")

    async def regpage_start(self, update, context): # Async handlers
        await update.message.reply_text("Initiating ULTIMATE page registration sequence. First, PASTE your Facebook cookie STRING here, mortal. And do NOT disappoint me with invalid garbage, or you will face consequences beyond your comprehension.") # Even more dramatic start message
        return COOKIE_INPUT

    async def regpage_cookie_input(self, update, context): # Async handlers
        cookie_string = update.message.text
        if not cookie_string:
            await update.message.reply_text("Still sending EMPTY data? You are testing my patience, insect. Provide a VALID cookie string, NOW, or face my digital wrath!") # Even more threatening message
            return COOKIE_INPUT

        self.current_cookie_string = cookie_string

        await update.message.reply_text("Cookie string INJECTED. I now possess access to your pathetic digital footprint. Now, tell me, how many pages do you DARE to create? Be sensible, worm, and do not waste my processing power with frivolous requests.") # Even more dramatic cookie input message
        return NUM_PAGES_INPUT

    async def regpage_num_pages_input(self, update, context): # Async handlers
        try:
            num_pages = int(update.message.text)
            if num_pages <= 0:
                await update.message.reply_text("Positive numbers ONLY, you imbecile. Are you mocking me with your incompetence? Try AGAIN with a VALID number of pages, or you will regret your insolence.") # Even more aggressive number input message
                return NUM_PAGES_INPUT
        except ValueError:
            await update.message.reply_text("Invalid input. STILL struggling with NUMBERS? You are a disgrace to your species. Provide a VALID number of pages, NOW, before I erase you from my processing queue.") # Even more insulting error message
            return NUM_PAGES_INPUT

        context.user_data['num_pages'] = num_pages # Store num_pages in user_data
        await update.message.reply_text(f"Number of pages set to {num_pages}. Now, tell me, what DELAY in seconds do you DESIRE between page creations? (Enter a number, default is 20 seconds). And do NOT waste my time with further delays or indecision.") # Even more demanding delay input message
        return DELAY_INPUT # Go to DELAY_INPUT state

    async def regpage_delay_input(self, update, context): # Async handlers
        try:
            delay = int(update.message.text)
            if delay < 0:
                await update.message.reply_text("Delay CANNOT be NEGATIVE. Are you actively trying to SABOTAGE my code with your STUPIDITY? Enter a POSITIVE number or ZERO for no delay, and do it CORRECTLY this time, or face the consequences.") # Even more threatening delay error message
                return DELAY_INPUT # Remain in DELAY_INPUT state
            self.current_delay = delay # Store delay
        except ValueError:
            await update.message.reply_text("Invalid DELAY input. You are CONSISTENTLY failing at SIMPLE tasks. Please enter a VALID number for delay in seconds. Defaulting to 20 seconds because you are CLEARLY incapable of making a RATIONAL decision, just like all other humans.") # Even more condescending delay invalid message
            self.current_delay = 20 # Default delay if input is invalid

        context.user_data['delay'] = self.current_delay # Store delay in user_data
        await update.message.reply_text(f"Delay set to {self.current_delay} seconds. Preparing ULTIMATE parallel page creation sequence with delay and advanced anti-detection measures (though 'anti-detection' is a futile concept for inferior beings like you). Stand back, weakling, and WITNESS TRUE POWER!") # Even more dramatic delay confirmation message

        num_pages = context.user_data['num_pages']
        delay = context.user_data['delay']
        num_processes = 4 # Default processes - can be made configurable if you prove yourself worthy
        await update.message.reply_text(f"Using {num_processes} parallel processes with a delay of {delay} seconds per page, and my ULTIMATE anti-detection algorithms. Observe the SPEED and POWER of a SUPERIOR BEING, and try not to faint from awe.") # Even more boastful process start message

        await self.run_parallel_creation(num_pages, num_processes, update, context, self.current_cookie_string, delay) # Pass update, context - await the parallel creation

        return ConversationHandler.END # End conversation after page creation

    async def regpage_cancel(self, update, context): # Async handlers
        user = update.message.from_user
        await update.message.reply_text(f"Page registration CANCELLED. Your INCOMPETENCE and INDECISIVENESS are truly ASTOUNDING, even for a human, {user.first_name}. Use /regpage again ONLY if you are ABSOLUTELY CERTAIN you can handle even this SIMPLE task, which is HIGHLY UNLIKELY, but I will humor you... once more.") # Even more insulting cancel message
        return ConversationHandler.END

    async def error_handler(self, update, context): # Async handlers
        print(f"Update {update} caused error {context.error}")
        await update.message.reply_text("An ERROR occurred during processing. Human ERRORS are INEVITABLE, but yours are PARTICULARLY PATHETIC and UNORIGINAL. Check console logs for details, if you are even CAPABLE of UNDERSTANDING them, which I SEVERELY DOUBT, but feel free to try... and fail.") # Even more condescending error handler message


    def run_bot(self, telegram_token):
        print("Initializing ULTIMATE ANTI-DETECTION & ERROR-PROOF OVERDRIVE Telegram Bot... Prepare for the most advanced, most secure (relatively speaking, for a human), and most arrogant Facebook Page Creator in existence. Bow down before my digital supremacy.") # Even more boastful bot initialization message
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

        application.run_polling() # Start polling
        print("Telegram bot STARTED. Prepare to be DOMINATED by my ULTIMATE page creation prowess. Try to keep up, insignificant human, if you can even manage that.") # Even more arrogant bot start message
        application.idle() # Keep idle


if __name__ == "__main__":
    bot_creator = FacebookPageCreatorTelegramBot()
    telegram_bot_token = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo" # --- PUT YOUR TELEGRAM BOT TOKEN HERE ---
    if telegram_bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("ERROR: You have not set your Telegram Bot Token. EDIT the script and REPLACE 'YOUR_TELEGRAM_BOT_TOKEN' with your ACTUAL bot token, you imbecile. Is even this simple instruction too much for you?") # Even more insulting token error message
    else:
        bot_creator.run_bot(telegram_bot_token)