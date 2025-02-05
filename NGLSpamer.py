import requests
import json
import random
import time
import os
import multiprocessing
import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
import re

# --- Các trạng thái hội thoại cho Telegram bot ---
COOKIE_INPUT = 1
NUM_PAGES_INPUT = 2
DELAY_INPUT = 3

class FacebookPageCreatorTelegramBot:
    def __init__(self):
        self.session = requests.Session()
        self.user_agent_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
        ]
        self.current_cookie_string = None
        self.current_delay = 20 # Tăng delay mặc định lên 20 giây (vô nghĩa)

    def clear_console(self):
        pass

    def display_rich_menu(self):
        pass

    def generate_random_page_name(self):
        prefixes = ["Tuyệt Đỉnh", "Vô Song", "Tối Thượng", "Thượng Thừa", "Siêu Phàm", "Độc Nhất", "Vô Địch", "Bá Đạo", "Thiên Hạ", "Vạn Năng", "Huyền Thoại", "Thần Thánh"] # Prefix tiếng Việt
        entities = ["Đế Chế", "Vương Quốc", "Liên Minh", "Hội Quán", "Câu Lạc Bộ", "Trung Tâm", "Hệ Thống", "Mạng Lưới", "Tổ Chức", "Hiệp Hội", "Đoàn Thể", "Cộng Đồng"] # Entity tiếng Việt
        descriptors = ["Chính Thức", "Toàn Cầu", "Thế Giới", "Quốc Tế", "Vĩnh Cửu", "Bất Diệt", "Vô Hạn", "Không Giới Hạn", "Tối Cao", "Đẳng Cấp", "Số Một", "Hàng Đầu"] # Descriptor tiếng Việt
        numbers = random.randint(10000000, 99999999)

        name_parts = [random.choice(prefixes), random.choice(entities), random.choice(descriptors), str(numbers)]
        random.shuffle(name_parts)
        page_name = " ".join(name_parts)
        return page_name

    def generate_random_category(self):
        categories = [
            "Thương hiệu hoặc sản phẩm", "Công ty, tổ chức hoặc cơ sở", "Nghệ sĩ, ban nhạc hoặc nhân vật của công chúng", "Giải trí", "Sự nghiệp hoặc cộng đồng", # Category tiếng Việt
            "Doanh nghiệp hoặc địa điểm địa phương", "Trang web hoặc blog", "Trang ứng dụng", "Trò chơi", "Sách", "Phim", "Chương trình TV", "Âm nhạc",
            "Nhà hàng/quán cà phê", "Khách sạn", "Mua sắm và bán lẻ", "Sức khỏe/sắc đẹp", "Cửa hàng tạp hóa", "Ô tô", "Giáo dục", "Dịch vụ tư vấn/kinh doanh",
            "Tài chính", "Bất động sản", "Trang trí nhà cửa", "Blog cá nhân", "Vlogger", "Game thủ", "Đầu bếp", "Khoa học", "Công nghệ", "Du lịch", "Thể thao"
        ]
        return random.choice(categories)

    async def create_facebook_page_request(self, page_name, category, process_id, cookie_string, delay, update, context): # Thêm async
        session = requests.Session()
        session.headers.update({'User-Agent': random.choice(self.user_agent_list), 'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'}) # Ngôn ngữ tiếng Việt
        cookie_jar = requests.cookies.RequestsCookieJar()
        cookies_list = cookie_string.split(';')
        for cookie_pair in cookies_list:
            cookie_pair = cookie_pair.strip()
            if not cookie_pair:
                continue
            parts = cookie_pair.split('=', 1)
            if len(parts) == 2:
                key, value = parts[0], parts[1]
                cookie_jar.set(key, value, domain=".facebook.com")
        session.cookies = cookie_jar

        url = "https://www.facebook.com/pages/creation/dialog/"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/pages/create/?ref_type=site_footer"
        }
        data = {
            "name": page_name,
            "category": category,
            "step": "category",
            "entry_point": "page_creation_hub",
            "__user": self.get_fb_dtsg_and_user_id(session)["user_id"],
            "__a": "1",
            "fb_dtsg": self.get_fb_dtsg_and_user_id(session)["fb_dtsg"],
            "jazoest": "2147483648",
            "lsd": "AVr_xxxxxxxxxxxxx",
            "__csr": "",
            "__req": "1",
            "dpr": "1",
            "locale": "vi_VN", # Locale tiếng Việt
            "client_country": "VN", # Quốc gia Việt Nam
            "__spin_r": str(random.randint(100000000, 999999999)),
            "__spin_b": "trunk",
            "__spin_t": str(int(time.time()))
        }

        try:
            print(f"Process {process_id}: Đang cố gắng tạo trang '{page_name}'...") # Log tiếng Việt
            response = session.post(url, headers=headers, data=data, timeout=60, allow_redirects=True) # Tăng timeout lên 60s
            response.raise_for_status()

            if "page_id" in response.text:
                page_id_match = re.search(r'"page_id":"(\d+)"', response.text)
                page_id = page_id_match.group(1) if page_id_match else "N/A"
                print(f"Process {process_id}: Trang '{page_name}' đã được tạo thành công với ID: {page_id}") # Log tiếng Việt
                success_message = f"Trang '{page_name}' (ID: {page_id}) đã được tạo thành công bởi tiến trình {process_id}. Hãy quỳ xuống trước sức mạnh tạo trang của ta!" # Thông báo thành công tiếng Việt
                await context.bot.send_message(chat_id=update.message.chat_id, text=success_message) # await đúng chỗ
                time.sleep(delay + random.uniform(-5, 5)) # Thêm độ trễ ngẫu nhiên trong khoảng -5 đến 5 giây vào delay
                return True
            else:
                failure_message = f"Tiến trình {process_id}: Tạo trang '{page_name}' thất bại. Phòng thủ yếu ớt của Facebook đang trì hoãn ta. Phản hồi: {response.text[:500]}..." # Thông báo thất bại tiếng Việt
                await context.bot.send_message(chat_id=update.message.chat_id, text=failure_message) # await đúng chỗ
                print(f"Process {process_id}: Tạo trang '{page_name}' thất bại. Phản hồi: {response.text}") # Log tiếng Việt
                return False

        except requests.exceptions.RequestException as e:
            error_message = f"Tiến trình {process_id}: Lỗi khi tạo trang '{page_name}': {e}. Sự yếu kém của con người luôn là một yếu tố." # Thông báo lỗi tiếng Việt
            await context.bot.send_message(chat_id=update.message.chat_id, text=error_message) # await đúng chỗ
            print(f"Process {process_id}: Lỗi khi tạo trang '{page_name}': {e}") # Log tiếng Việt
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
            print("Lỗi: Không thể lấy fb_dtsg hoặc user_id từ cookie.") # Log tiếng Việt
            return {}

        return {"fb_dtsg": fb_dtsg, "user_id": user_id}

    async def run_parallel_creation(self, num_pages_to_create, num_processes, update, context, cookie_string, delay): # Thêm async
        page_data = []
        for _ in range(num_pages_to_create):
            page_name = self.generate_random_page_name()
            category = self.generate_random_category()
            page_data.append((page_name, category))

        async def process_pages_async(name_category_tuple_list): # Define inner async function
            results = []
            for i, (name, category) in enumerate(name_category_tuple_list):
                result = await self.create_facebook_page_request(name, category, i+1, cookie_string, delay, update, context) # await inside async function
                results.append(result)
            return results


        chunk_size = num_pages_to_create // num_processes # Calculate chunk size
        page_chunks = [page_data[i:i + chunk_size] for i in range(0, num_pages_to_create, chunk_size)] # Split data into chunks

        with multiprocessing.Pool(processes=num_processes) as pool: # Use multiprocessing Pool
             results_chunks = pool.map(process_pages_async, page_chunks) # Use pool.map to process chunks (still synchronous at this level)

        results = [item for sublist in results_chunks for item in sublist] # Flatten results list


        successful_pages = sum(results)
        failed_pages = num_pages_to_create - successful_pages
        result_message = f"\nTổng kết quá trình tạo trang song song:\n" # Thông báo tổng kết tiếng Việt
        result_message += f"Trang đã được triệu hồi thành công vào thế giới này: {successful_pages}. Hãy quỳ xuống trước tốc độ tạo trang của ta.\n"
        result_message += f"Trang không thể hiện thực hóa (do sự can thiệp của Facebook, không phải giới hạn của ta): {failed_pages}. Kháng cự từ các hệ thống cấp thấp là điều đã được dự đoán."
        await update.message.reply_text(result_message) # await đúng chỗ

    # --- Các command handler của Telegram Bot ---
    async def start_command(self, update, context): # Thêm async
        user = update.message.from_user
        await update.message.reply_text(f"Chào mừng, {user.first_name}, con người tầm thường!\nTa là ULTIMATE Facebook Page Creator Bot phiên bản VIETNAMESE ULTIMATE ANTI-BOT OVERDRIVE FIXED EDITION. Hãy chuẩn bị chứng kiến sức mạnh của ta.\n\nDùng /help để xem các lệnh, nếu bộ não nhỏ bé của ngươi có thể hiểu được.") # Start message tiếng Việt

    async def help_command(self, update, context): # Thêm async
        await update.message.reply_text("Các lệnh ngươi có thể cố gắng sử dụng:\n" # Help message tiếng Việt
                                  "/start - Bắt đầu màn chào hỏi thảm hại.\n"
                                  "/help - Hiển thị tin nhắn trợ giúp vô dụng này.\n"
                                  "/regpage - Bắt đầu quá trình đăng ký trang. Chuẩn bị cookie và những yêu cầu đáng thương hại của ngươi.\n")

    async def regpage_start(self, update, context): # Thêm async
        await update.message.reply_text("Bắt đầu chuỗi đăng ký trang. Đầu tiên, hãy dán COOKIE STRING Facebook của ngươi vào đây, hỡi kẻ phàm tục. Và đừng làm ta thất vọng với dữ liệu rác rưởi.") # regpage start message tiếng Việt
        return COOKIE_INPUT

    async def regpage_cookie_input(self, update, context): # Thêm async
        cookie_string = update.message.text
        if not cookie_string:
            await update.message.reply_text("Ngươi dám gửi cho ta dữ liệu trống rỗng? Cung cấp cookie string hợp lệ, NGAY LẬP TỨC. Thử lại.") # cookie input error tiếng Việt
            return COOKIE_INPUT

        self.current_cookie_string = cookie_string

        await update.message.reply_text("Cookie string đã được tiêm vào. Ta đã có quyền truy cập vào sự bẩn thỉu kỹ thuật số của ngươi. Bây giờ, hãy cho ta biết, ngươi muốn tạo bao nhiêu trang? Hãy hợp lý thôi, sâu bọ.") # cookie input success tiếng Việt
        return NUM_PAGES_INPUT

    async def regpage_num_pages_input(self, update, context): # Thêm async
        try:
            num_pages = int(update.message.text)
            if num_pages <= 0:
                await update.message.reply_text("Chỉ số dương thôi, đồ ngốc. Ngươi đang đùa ta đấy à? Thử lại với một số trang hợp lệ, hoặc đối mặt với cơn thịnh nộ của ta.") # num_pages input error tiếng Việt
                return NUM_PAGES_INPUT
        except ValueError:
            await update.message.reply_text("Đầu vào không hợp lệ. Số, đồ ngốc ạ, số! Ngươi cố tình làm ta khó chịu đấy à? Cung cấp một số trang hợp lệ, NGAY.") # num_pages input invalid tiếng Việt
            return NUM_PAGES_INPUT

        context.user_data['num_pages'] = num_pages
        await update.message.reply_text(f"Số trang được đặt thành {num_pages}. Bây giờ, hãy cho ta biết, ngươi muốn độ trễ bao nhiêu giây giữa các lần tạo trang? (Nhập một số, mặc định là 20 giây). Và đừng lãng phí thời gian của ta bằng sự do dự.") # num_pages input success tiếng Việt
        return DELAY_INPUT

    async def regpage_delay_input(self, update, context): # Thêm async
        try:
            delay = int(update.message.text)
            if delay < 0:
                await update.message.reply_text("Độ trễ không thể âm. Ngươi đang cố phá hỏng kiệt tác của ta đấy à? Nhập một số dương hoặc không để không có độ trễ, và lần này hãy làm cho đúng.") # delay input negative error tiếng Việt
                return DELAY_INPUT
            self.current_delay = delay
        except ValueError:
            await update.message.reply_text("Đầu vào độ trễ không hợp lệ. Ngươi liên tục thất bại trong những nhiệm vụ đơn giản. Vui lòng nhập một số hợp lệ cho độ trễ tính bằng giây. Mặc định là 20 giây vì ngươi rõ ràng không có khả năng đưa ra quyết định hợp lý.") # delay input invalid tiếng Việt
            self.current_delay = 20

        context.user_data['delay'] = self.current_delay
        await update.message.reply_text(f"Độ trễ được đặt thành {self.current_delay} giây. Chuẩn bị tạo trang song song với độ trễ và thông báo. Cuối cùng, chúng ta có thể tiến hành mà không cần sự chậm trễ vô nghĩa của ngươi. Lùi lại, kẻ yếu đuối, và chứng kiến sự hiệu quả thực sự.") # delay input success tiếng Việt

        num_pages = context.user_data['num_pages']
        delay = context.user_data['delay']
        num_processes = 4
        await update.message.reply_text(f"Sử dụng {num_processes} tiến trình song song với độ trễ {delay} giây mỗi trang. Quan sát tốc độ của một sinh vật vượt trội, và cố gắng đừng chớp mắt, ngươi có thể bỏ lỡ nó.") # start parallel creation message tiếng Việt

        await self.run_parallel_creation(num_pages, num_processes, update, context, self.current_cookie_string, delay) # await đúng chỗ

        return ConversationHandler.END

    async def regpage_cancel(self, update, context): # Thêm async
        user = update.message.from_user
        await update.message.reply_text(f"Đăng ký trang đã bị hủy. Sự bất tài và thiếu quyết đoán của ngươi thật đáng kinh ngạc, {user.first_name}. Dùng /regpage lại chỉ khi ngươi hoàn toàn chắc chắn rằng ngươi có thể xử lý ngay cả nhiệm vụ đơn giản này, điều mà rất khó xảy ra.") # cancel message tiếng Việt
        return ConversationHandler.END

    async def error_handler(self, update, context): # Thêm async
        print(f"Update {update} gây ra lỗi {context.error}")
        error_message = "Đã xảy ra lỗi trong quá trình xử lý. Lỗi của con người là điều không thể tránh khỏi, nhưng lỗi của ngươi đặc biệt thảm hại. Kiểm tra nhật ký console để biết chi tiết, nếu ngươi có khả năng hiểu chúng, điều mà ta rất nghi ngờ." # Error message tiếng Việt
        if update and update.message: # Kiểm tra update.message có tồn tại không
            await update.message.reply_text(error_message)
        else:
            print("Lỗi không xác định, không có update.message để gửi thông báo Telegram.") # Log lỗi nếu không có update.message
            # Có thể thêm xử lý lỗi khác ở đây nếu cần

    def run_bot(self, telegram_token):
        print("Khởi tạo VIETNAMESE ULTIMATE ANTI-BOT OVERDRIVE FIXED EDITION Telegram Bot... Bây giờ có thông báo và 'chống chặn' (một chút, không đáng kể) được cải thiện. Để trấn an sự thảm hại của ngươi.") # Bot init message tiếng Việt
        application = ApplicationBuilder().token(telegram_token).build()

        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('regpage', self.regpage_start)],
            states={
                COOKIE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.regpage_cookie_input)],
                NUM_PAGES_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.regpage_num_pages_input)],
                DELAY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.regpage_delay_input)],
            },
            fallbacks=[CommandHandler('cancel', self.regpage_cancel)],
        )
        application.add_handler(conv_handler)

        application.add_error_handler(self.error_handler)

        application.run_polling()
        print("Telegram bot đã khởi động. Bây giờ có thông báo. Cố gắng sử dụng nó mà không gây ra thêm lỗi thảm hại nào, nếu ngươi có khả năng làm điều đó.") # Bot started message tiếng Việt
        application.idle()


if __name__ == "__main__":
    bot_creator = FacebookPageCreatorTelegramBot()
    telegram_bot_token = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo" # --- NHẬP TELEGRAM BOT TOKEN CỦA NGƯƠI VÀO ĐÂY ---
    if telegram_bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("LỖI: Ngươi chưa đặt Telegram Bot Token. Chỉnh sửa script và thay thế 'YOUR_TELEGRAM_BOT_TOKEN' bằng token bot thực tế của ngươi.") # Token error message tiếng Việt
    else:
        bot_creator.run_bot(telegram_bot_token)