import logging
import os
import random
import time
from time import sleep

import requests
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. "
        f"Please install PTB version 20.0.0 or higher."
    )
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

# Các biến toàn cục (cân nhắc sử dụng cơ sở dữ liệu để lưu trữ lâu dài trong một bot thực tế)
list_clone = []
list_img = []
dem = 0
stt = 0
stt2 = 0
running = False  # Thêm biến để kiểm soát trạng thái chạy của bot


# =========================== [ CLASS + FUNCTION TOOL ] ===========================
class API_PRO5_ByNgDucPhat:
    def __init__(self):
        # Bạn có thể muốn tải cài đặt từ một tệp ở đây thay vì mã hóa cứng.
        pass

    def ndp_delay_tool(self, p):
        """Mô phỏng độ trễ. Loại bỏ phần hiển thị cho Telegram."""
        sleep(p)  # Độ trễ đơn giản nhất cho Telegram. Không cần hiệu ứng hình ảnh.

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
            url_profile = requests.get(
                "https://www.facebook.com/me", headers=headers_get, timeout=10
            ).url
            get_dulieu_profile = requests.get(url=url_profile, headers=headers_get, timeout=10).text
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi trong quá trình yêu cầu: {e}")
            return False
        except Exception as e:
            logger.exception(f"Đã xảy ra lỗi không mong muốn: {e}")
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
                f"https://api-ndpcutevcl.000webhostapp.com/api/upavtpage.php?cookie={cookie}&id={id_page}&link_anh={link_anh}", timeout=10
            ).json()
            if json_upavt["status"] == "success":
                return json_upavt
            else:
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi trong quá trình yêu cầu upAvt: {e}")  # Ghi lại lỗi
            return False
        except Exception as e:
            logger.exception(f"Đã xảy ra lỗi không mong muốn trong upAvt: {e}")  # Ghi lại lỗi
            return False

    def RegPage(self, cookie, name, uid, fb_dtsg, jazoest):
        try:
            namepage = requests.get(
                "https://story-shack-cdn-v2.glitch.me/generators/vietnamese-name-generator/male?count=2", timeout=10
            ).json()["data"][0]["name"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi khi lấy tên: {e}")
            return False, None, None
        except Exception as e:
             logger.exception(f"Đã xảy ra lỗi không mong muốn khi tạo tên: {e}")
             return False, None, None
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
            response = requests.post(
                "https://www.facebook.com/api/graphql/", headers=headers_reg, data=data_reg, timeout=20
            )
            response.raise_for_status()  # Nâng cao HTTPError cho các phản hồi xấu (4xx hoặc 5xx)
            idpage = response.json()["data"]["additional_profile_plus_create"]["additional_profile"]["id"]
            dem += 1
            return idpage, name, namepage  # Trả về tất cả dữ liệu liên quan
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi trong quá trình yêu cầu RegPage: {e}")
            return False, None, None
        except (KeyError, ValueError) as e:
            logger.error(f"Lỗi phân tích cú pháp phản hồi RegPage: {e}")
            return False, None, None
        except Exception as e:
             logger.exception(f"Đã xảy ra lỗi không mong muốn trong quá trình regpage: {e}")
             return False, None, None


# =========================== [ TELEGRAM BOT HANDLERS ] ===========================
async def start(update: Update, context: CallbackContext) -> None:
    """Gửi một tin nhắn chào mừng."""
    await update.message.reply_text(
        "Chào mừng đến với Bot Đăng Ký Trang Facebook!\n"
        "Sử dụng /help để xem các lệnh khả dụng."
    )


async def help_command(update: Update, context: CallbackContext) -> None:
    """Hiển thị các lệnh khả dụng."""
    await update.message.reply_text(
        "/start - Bắt đầu bot\n"
        "/help - Hiển thị tin nhắn trợ giúp này\n"
        "/add_cookie - Thêm cookie Facebook\n"
        "/add_image - Thêm liên kết hình ảnh cho ảnh hồ sơ\n"
        "/set_page_limit <limit> - Đặt số lượng trang cần tạo trước khi dừng\n"
        "/set_delay <seconds> - Đặt độ trễ giữa các lần đăng ký trang\n"
        "/start_registration - Bắt đầu quá trình đăng ký trang\n"
        "/stop - Dừng quá trình đăng ký trang"
    )


async def add_cookie(update: Update, context: CallbackContext) -> None:
    """Thêm cookie Facebook vào danh sách."""
    global list_clone, stt
    cookie = update.message.text.split(" ", 1)[1].strip()  # Lấy cookie, loại bỏ khoảng trắng thừa
    if not cookie:
        await update.message.reply_text("Vui lòng cung cấp một cookie sau lệnh /add_cookie.")
        return

    dpcutevcl = API_PRO5_ByNgDucPhat()
    checklive = dpcutevcl.getthongtinfacebook(cookie)
    if checklive:
        stt += 1
        list_clone.append(f"{cookie}|{checklive[0]}|{checklive[1]}|{checklive[2]}|{checklive[3]}")
        await update.message.reply_text(f"Đã thêm cookie thành công! ({checklive[0]}) Tổng số cookie: {len(list_clone)}")
    else:
        await update.message.reply_text("Cookie không hợp lệ hoặc đã hết hạn. Vui lòng kiểm tra và thử lại.")


async def add_image(update: Update, context: CallbackContext) -> None:
    """Thêm liên kết hình ảnh vào danh sách."""
    global list_img, stt2
    image_link = update.message.text.split(" ", 1)[1].strip()  # Lấy liên kết hình ảnh, loại bỏ khoảng trắng
    if not image_link:
        await update.message.reply_text("Vui lòng cung cấp một liên kết hình ảnh sau lệnh /add_image.")
        return

    list_img.append(image_link)
    stt2 += 1
    await update.message.reply_text(f"Đã thêm liên kết hình ảnh! Tổng số hình ảnh: {len(list_img)}")


async def set_page_limit(update: Update, context: CallbackContext) -> None:
    """Đặt giới hạn tạo trang."""
    global slpage
    try:
        limit = int(context.args[0])
        slpage = limit
        await update.message.reply_text(f"Giới hạn tạo trang được đặt thành: {limit}")
    except (IndexError, ValueError):
        await update.message.reply_text("Cách sử dụng: /set_page_limit <số>")


async def set_delay(update: Update, context: CallbackContext) -> None:
    """Đặt độ trễ giữa các lần đăng ký trang."""
    global delay
    try:
        delay = int(context.args[0])
        await update.message.reply_text(f"Độ trễ được đặt thành: {delay} giây")
    except (IndexError, ValueError):
        await update.message.reply_text("Cách sử dụng: /set_delay <giây>")

async def start_registration(update: Update, context: CallbackContext) -> None:
    """Bắt đầu quá trình đăng ký trang."""
    global list_clone, list_img, dem, slpage, delay, running
    dpcutevcl = API_PRO5_ByNgDucPhat()

    if running:
        await update.message.reply_text("Quá trình đăng ký đã đang chạy. Vui lòng dừng trước khi bắt đầu lại.")
        return

    if not list_clone:
        await update.message.reply_text("Chưa có cookie nào được thêm. Vui lòng thêm cookie bằng /add_cookie.")
        return

    if not list_img:
        await update.message.reply_text("Chưa có liên kết hình ảnh nào được thêm. Vui lòng thêm liên kết hình ảnh bằng /add_image.")
        return

    if slpage == 0:  # Kiểm tra xem giới hạn đã được đặt chưa
        await update.message.reply_text("Vui lòng đặt giới hạn tạo trang bằng /set_page_limit <giới hạn>")
        return

    if delay == 0:  # Kiểm tra xem độ trễ đã được đặt chưa
        await update.message.reply_text("Vui lòng đặt độ trễ giữa các lần đăng ký trang bằng /set_delay <giây>")
        return

    running = True  # Đặt trạng thái đang chạy

    await update.message.reply_text(
        f"Bắt đầu đăng ký trang...\n"
        f"Sử dụng {len(list_clone)} cookie và {len(list_img)} hình ảnh.\n"
        f"Tạo tối đa {slpage} trang với độ trễ {delay} giây giữa mỗi trang."
    )

    try:
        for dulieuclone in list_clone:
            if not running:  # Kiểm tra trạng thái dừng
                await update.message.reply_text("Đã dừng quá trình đăng ký.")
                return

            cookie, name, uid, fb_dtsg, jazoest = dulieuclone.split("|")
            result = dpcutevcl.RegPage(cookie, name, uid, fb_dtsg, jazoest)

            if result:
                idpage, fb_name, page_name = result  # Mở gói tuple

                link_anh = random.choice(list_img)
                up_result = dpcutevcl.UpAvt(cookie, idpage, link_anh)

                if up_result:
                    await update.message.reply_text(
                        f"Đã tạo trang: {page_name} (ID: {idpage})\n"
                        f"Đã cập nhật ảnh hồ sơ thành công."
                    )
                else:
                    await update.message.reply_text(
                        f"Đã tạo trang: {page_name} (ID: {idpage})\n"
                        f"Không thể cập nhật ảnh hồ sơ."
                    )
            else:
                await update.message.reply_text(f"Không thể đăng ký trang cho {name}. Cookie có thể bị chặn hoặc không hợp lệ.")

            dpcutevcl.ndp_delay_tool(delay)
            dem += 1

            if dem >= slpage:
                await update.message.reply_text(f"Đã đạt đến giới hạn tạo trang ({slpage}). Dừng lại.")
                break  # Dừng vòng lặp nếu đạt đến giới hạn
    finally:
        running = False  # Đảm bảo rằng trạng thái đang chạy được đặt thành False sau khi hoàn thành hoặc dừng lại
        await update.message.reply_text("Quá trình đăng ký hoàn tất.")


async def stop(update: Update, context: CallbackContext) -> None:
    """Dừng quá trình đăng ký."""
    global running
    running = False
    await update.message.reply_text("Đang dừng quá trình đăng ký...")


# =========================== [ MAIN FUNCTION ] ===========================
def main() -> None:
    """Bắt đầu bot."""
    # Tạo Application và chuyển token bot của bạn cho nó.
    application = Application.builder().token(BOT_TOKEN).build()

    # trên các lệnh khác nhau - trả lời trong Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_cookie", add_cookie))
    application.add_handler(CommandHandler("add_image", add_image))
    application.add_handler(CommandHandler("set_page_limit", set_page_limit))
    application.add_handler(CommandHandler("set_delay", set_delay))
    application.add_handler(CommandHandler("start_registration", start_registration))
    application.add_handler(CommandHandler("stop", stop))

    # Chạy bot cho đến khi người dùng nhấn Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()