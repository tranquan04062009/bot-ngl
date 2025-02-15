import logging
import os
import random
import time
from time import sleep

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your Telegram bot token
BOT_TOKEN = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo"

# Global variables (consider using a database for persistent storage in a real bot)
list_clone = []
list_img = []
dem = 0
stt = 0
stt2 = 0


# =========================== [ CLASS + FUNCTION TOOL ] ===========================
class API_PRO5_ByNgDucPhat:
    def __init__(self):
        # You might want to load settings from a file here instead of hardcoding.
        pass

    def ndp_delay_tool(self, p):
        """Simulates delay with visual output.  Remove the visual part for Telegram."""
        sleep(p)  # Simplest delay for Telegram.  No need for visual fluff.
        # while(p>1):
        #     p=p-1
        #     print(f'\033[0;34m[🌸DUYKHANH🌸]\033[1;32m[|][LO......][{p}]','     ',end='\r');sleep(1/6)
        #     print(f'\033[0;34m[🌸DUYKHANH🌸]\033[1;32m[/][LOA.....][{p}]','     ',end='\r');sleep(1/6)
        #     print(f'\033[0;34m[🌸DUYKHANH🌸]\033[1;32m[-][LOAD....][{p}]','     ',end='\r');sleep(1/6)
        #     print(f'\033[0;34m[🌸DUYKHANH🌸]\033[1;32m[+][LOADI...][{p}]','     ',end='\r');sleep(1/6)
        #     print(f'\033[0;34m[🌸DUYKHANH🌸]\033[1;32m[\][LOADIN..][{p}]','     ',end='\r');sleep(1/6)
        #     print(f'\033[0;34m[🌸DUYKHANH🌸]\033[1;32m[|][LOADING.][{p}]','     ',end='\r');sleep(1/6)

    def getthongtinfacebook(self, cookie: str):
        headers_get = {
            "authority": "www.facebook.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
            "sec-ch-prefers-color-scheme": "light",
            "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "viewport-width": "1184",
            "cookie": cookie,
        }
        try:
            #print(f"\033[0;31mĐang Tiến Hành Check Live", end="\r") # Remove console output
            url_profile = requests.get(
                "https://www.facebook.com/me", headers=headers_get
            ).url
            get_dulieu_profile = requests.get(url=url_profile, headers=headers_get).text
        except:
            return False
        try:
            uid_get = cookie.split("c_user=")[1].split(";")[0]
            fb_dtsg_get = (
                get_dulieu_profile.split('{"name":"fb_dtsg","value":"')[1].split('"},')[0]
            )
            jazoest_get = (
                get_dulieu_profile.split('{"name":"jazoest","value":"')[1].split('"},')[0]
            )
            name_get = get_dulieu_profile.split("<title>")[1].split("</title>")[0]
            return name_get, uid_get, fb_dtsg_get, jazoest_get
        except:
            try:
                uid_get = cookie.split("c_user=")[1].split(";")[0]
                fb_dtsg_get = get_dulieu_profile.split(',"f":"')[1].split('","l":null}')[0]
                jazoest_get = get_dulieu_profile.split("&jazoest=")[1].split('","e":"')[0]
                name_get = get_dulieu_profile.split("<title>")[1].split("</title>")[0]
                return name_get, uid_get, fb_dtsg_get, jazoest_get
            except:
                return False

    def UpAvt(self, cookie, id_page, link_anh):
        time.sleep(5)

        try:
            json_upavt = requests.get(
                f"https://api-ndpcutevcl.000webhostapp.com/api/upavtpage.php?cookie={cookie}&id={id_page}&link_anh={link_anh}"
            ).json()
            if json_upavt["status"] == "success":
                return json_upavt
            else:
                return False
        except:
            return False

    def RegPage(self, cookie, name, uid, fb_dtsg, jazoest):
        namepage = requests.get(
            "https://story-shack-cdn-v2.glitch.me/generators/vietnamese-name-generator/male?count=2"
        ).json()["data"][0]["name"]
        global dem
        headers_reg = {
            "authority": "www.facebook.com",
            "accept": "*/*",
            "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
            "origin": "https://www.facebook.com",
            "referer": "https://www.facebook.com/pages/creation?ref_type=launch_point",
            "sec-ch-prefers-color-scheme": "dark",
            "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "viewport-width": "979",
            "x-fb-friendly-name": "AdditionalProfilePlusCreationMutation",
            "x-fb-lsd": "ZM7FAk6cuRcUp3imwqvHTY",
            "cookie": cookie,
        }
        data_reg = {
            "av": uid,
            "__user": uid,
            "__a": "1",
            "__dyn": "7AzHxq1mxu1syUbFuC0BVU98nwgU29zEdEc8co5S3O2S7o11Ue8hw6vwb-q7oc81xoswIwuo886C11xmfz81sbzoaEnxO0Bo7O2l2Utwwwi831wiEjwZwlo5qfK6E7e58jwGzE8FU5e7oqBwJK2W5olwuEjUlDw-wUws9ovUaU3qxWm2Sq2-azo2NwkQ0z8c84K2e3u362-2B0oobo",
            "__csr": "gP4ZAN2d-hbbRmLObkZO8LvRcXWVvth9d9GGXKSiLCqqr9qEzGTozAXiCgyBhbHrRG8VkQm8GFAfy94bJ7xeufz8jK8yGVVEgx-7oiwxypqCwgF88rzKV8y2O4ocUak4UpDxu3x1K4opAUrwGx63J0Lw-wa90eG18wkE7y14w4hw6Bw2-o069W00CSE0PW06aU02Z3wjU6i0btw3TE1wE5u",
            "__req": "t",
            "__hs": "19296.HYP:comet_pkg.2.1.0.2.1",
            "dpr": "1",
            "__ccg": "EXCELLENT",
            "__rev": "1006496476",
            "__s": "1gapab:y4xv3f:2hb4os",
            "__hsi": "7160573037096492689",
            "__comet_req": "15",
            "fb_dtsg": fb_dtsg,
            "jazoest": jazoest,
            "lsd": "ZM7FAk6cuRcUp3imwqvHTY",
            "__aaid": "800444344545377",
            "__spin_r": "1006496476",
            "__spin_b": "trunk",
            "__spin_t": "1667200829",
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AdditionalProfilePlusCreationMutation",
            "variables": '{"input":{"bio":"reg auto by duykhanh","categories":["181475575221097"],"creation_source":"comet","name":"'
            + namepage
            + '","page_referrer":"launch_point","actor_id":"'
            + uid
            + '","client_mutation_id":"1"}}',
            "server_timestamps": "true",
            "doc_id": "5903223909690825",
        }
        try:
            idpage = requests.post(
                "https://www.facebook.com/api/graphql/", headers=headers_reg, data=data_reg, timeout=20
            ).json()["data"]["additional_profile_plus_create"]["additional_profile"]["id"]
            dem += 1
            #print(f'\033[1;35m{dem} | SUCCESS | NAME FB: {name} | UID PRO5: {idpage} | NAME PRO5: {namepage}')  # Remove Console output
            return idpage, name, namepage  # Return all relevant data
        except:
            #print('\033[0;31mReg Thất Bại Có Vẻ Acc Của Bạn Đã Bị Block!!')  # Remove console output
            return False, None, None  # Return failure


# =========================== [ TELEGRAM BOT HANDLERS ] ===========================
async def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message."""
    await update.message.reply_text(
        "Welcome to the Facebook Page Registration Bot!\n"
        "Use /help to see available commands."
    )


async def help_command(update: Update, context: CallbackContext) -> None:
    """Displays available commands."""
    await update.message.reply_text(
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/add_cookie - Add a Facebook cookie\n"
        "/add_image - Add an image link for profile picture\n"
        "/set_page_limit <limit> - Set the number of pages to create before stopping\n"
        "/set_delay <seconds> - Set the delay between page registrations\n"
        "/start_registration - Start the page registration process"
    )


async def add_cookie(update: Update, context: CallbackContext) -> None:
    """Adds a Facebook cookie to the list."""
    global list_clone, stt
    cookie = update.message.text.split(" ")[1]  # Get the cookie from the command
    dpcutevcl = API_PRO5_ByNgDucPhat()
    checklive = dpcutevcl.getthongtinfacebook(cookie)
    if checklive:
        # await update.message.reply_text(f"Name Facebook: {checklive[0]}") #Removed formatting
        stt += 1
        list_clone.append(f"{cookie}|{checklive[0]}|{checklive[1]}|{checklive[2]}|{checklive[3]}")
        await update.message.reply_text(f"Cookie added successfully! ({checklive[0]}) Total cookies: {len(list_clone)}")
    else:
        await update.message.reply_text("Invalid or dead cookie.  Please check and try again.")


async def add_image(update: Update, context: CallbackContext) -> None:
    """Adds an image link to the list."""
    global list_img, stt2
    image_link = update.message.text.split(" ")[1]  # Get the image link
    list_img.append(image_link)
    stt2 += 1
    await update.message.reply_text(f"Image link added! Total images: {len(list_img)}")


async def set_page_limit(update: Update, context: CallbackContext) -> None:
    """Sets the page creation limit."""
    global slpage
    try:
        limit = int(context.args[0])
        slpage = limit
        await update.message.reply_text(f"Page creation limit set to: {limit}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /set_page_limit <number>")


async def set_delay(update: Update, context: CallbackContext) -> None:
    """Sets the delay between page registrations."""
    global delay
    try:
        delay = int(context.args[0])
        await update.message.reply_text(f"Delay set to: {delay} seconds")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /set_delay <seconds>")

async def start_registration(update: Update, context: CallbackContext) -> None:
    """Starts the page registration process."""
    global list_clone, list_img, dem, slpage, delay
    dpcutevcl = API_PRO5_ByNgDucPhat()

    if not list_clone:
        await update.message.reply_text("No cookies added. Please add cookies using /add_cookie.")
        return

    if not list_img:
        await update.message.reply_text("No image links added. Please add image links using /add_image.")
        return

    if slpage == 0:  #Check if limit has been set
        await update.message.reply_text("Please set a page creation limit using /set_page_limit <limit>")
        return

    if delay == 0: #Check if delay has been set
        await update.message.reply_text("Please set a delay between page registrations using /set_delay <seconds>")
        return
    await update.message.reply_text(
        f"Starting page registration...\n"
        f"Using {len(list_clone)} cookies and {len(list_img)} images.\n"
        f"Creating up to {slpage} pages with a delay of {delay} seconds between each."
    )

    for dulieuclone in list_clone:
        cookie, name, uid, fb_dtsg, jazoest = dulieuclone.split("|")
        result = dpcutevcl.RegPage(cookie, name, uid, fb_dtsg, jazoest)

        if result:
            idpage, fb_name, page_name = result # unpack the tuple

            link_anh = random.choice(list_img)
            up_result = dpcutevcl.UpAvt(cookie, idpage, link_anh)

            if up_result:
                await update.message.reply_text(
                    f"Created page: {page_name} (ID: {idpage})\n"
                    f"Updated profile picture successfully."
                )
            else:
                await update.message.reply_text(
                    f"Created page: {page_name} (ID: {idpage})\n"
                    f"Failed to update profile picture."
                )
        else:
             await update.message.reply_text(f"Failed to register page for {name}.  Cookie may be blocked.")

        dpcutevcl.ndp_delay_tool(delay)
        dem += 1

        if dem >= slpage:
            await update.message.reply_text(f"Reached page creation limit ({slpage}). Stopping.")
            return

    await update.message.reply_text("All cookies processed.")


# =========================== [ MAIN FUNCTION ] ===========================
def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_cookie", add_cookie))
    application.add_handler(CommandHandler("add_image", add_image))
    application.add_handler(CommandHandler("set_page_limit", set_page_limit))
    application.add_handler(CommandHandler("set_delay", set_delay))
    application.add_handler(CommandHandler("start_registration", start_registration))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()