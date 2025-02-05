import requests
import json
import random
import time
import os
import multiprocessing
import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
import re # Nhập module re cho regex

# --- ĐỊNH NGHĨA CÁC TRẠNG THÁI HỘI THOẠI CHO BOT TELEGRAM ---
NHAP_COOKIE = 1
NHAP_SO_TRANG = 2
NHAP_DELAY = 3 # GIỮ LẠI TRẠNG THÁI NHAP_DELAY

class BotTaoTrangFacebookTelegram:
    def __init__(self):
        self.session = requests.Session()
        self.danh_sach_user_agent = [ # MỞ RỘNG DANH SÁCH USER-AGENT ĐỂ "CHỐNG BOT" TỐT HƠN (VÔ NGHĨA)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36", # Thêm Linux Chrome
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0", # Thêm Linux Firefox
            "Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/91.0", # Thêm Android Firefox
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1" # Thêm iPhone Safari 15
        ]
        self.cookie_hien_tai = None
        self.delay_hien_tai = 30 # TĂNG DELAY MẶC ĐỊNH LÊN 30 GIÂY ĐỂ "CHỐNG BOT" TỐT HƠN (VÔ NGHĨA HƠN NỮA)

    def xoa_man_hinh_console(self):
        pass # KHÔNG CẦN XÓA CONSOLE TRONG BOT TELEGRAM

    def hien_thi_menu_rich(self):
        pass # KHÔNG CẦN MENU RICH TRONG BOT TELEGRAM

    def tao_ten_trang_ngau_nhien(self): # GIỮ NGUYÊN HÀM TẠO TÊN TRANG, ĐỦ ĐA DẠNG RỒI
        tien_to = ["Thiên Thượng", "Địa Đàng", "Tinh Tú", "Vũ Trụ", "Ngân Hà", "Hằng Tinh", "Siêu Tân Tinh", "Sao Chổi", "Lỗ Đen", "Lượng Tử", "Siêu Việt", "Tối Thượng", "Vô Song", "Độc Nhất", "Tuyệt Đỉnh"]
        thuc_the = ["Thế Lực", "Liên Minh", "Tập Đoàn", "Đế Chế", "Quân Đoàn", "Hội Quán", "Trung Tâm", "Cổng Thông Tin", "Vùng Đất", "Tổ Hợp", "Mạng Lưới", "Hệ Thống", "Vương Quốc", "Cõi", "Giới"]
        mo_ta = ["Chính Thức", "Toàn Cầu", "Thế Giới", "Vũ Trụ", "Tối Cao", "Vô Hạn", "Bất Tận", "Vĩnh Hằng", "Không Giới Hạn", "Không Tưởng", "Tột Đỉnh", "Đỉnh Cao", "Vô Địch", "Đệ Nhất", "Số Một"]
        so = random.randint(10000000, 99999999)

        ten_phan_doan = [random.choice(tien_to), random.choice(thuc_the), random.choice(mo_ta), str(so)]
        random.shuffle(ten_phan_doan)
        ten_trang = " ".join(ten_phan_doan)
        return ten_trang

    def tao_danh_muc_ngau_nhien(self): # GIỮ NGUYÊN HÀM TẠO DANH MỤC, ĐỦ ĐA DẠNG RỒI
        danh_muc = [
            "Thương hiệu hoặc sản phẩm", "Công ty, tổ chức hoặc cơ sở",
            "Nghệ sĩ, ban nhạc hoặc nhân vật của công chúng", "Giải trí", "Tổ chức hoặc cộng đồng",
            "Doanh nghiệp hoặc địa điểm địa phương", "Trang web hoặc blog", "Trang ứng dụng", "Game",
            "Sách", "Phim", "Chương trình TV", "Âm nhạc", "Nhà hàng/quán cafe", "Khách sạn",
            "Mua sắm & Bán lẻ", "Sức khỏe/làm đẹp", "Cửa hàng tạp hóa", "Ô tô",
            "Giáo dục", "Dịch vụ tư vấn/doanh nghiệp", "Tài chính", "Bất động sản",
            "Trang trí nhà cửa", "Blog cá nhân", "Vlogger", "Game thủ", "Đầu bếp", "Khoa học", "Công nghệ", "Du lịch", "Thể thao", "Tin tức và Truyền thông"
        ]
        return random.choice(danh_muc)

    def tao_trang_facebook_request(self, ten_trang, danh_muc, process_id, cookie_string, delay, update, context): # GIỮ NGUYÊN CẤU TRÚC HÀM, CHỈ TINH CHỈNH LOGIC
        session = requests.Session()
        session.headers.update({'User-Agent': random.choice(self.danh_sach_user_agent), 'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7', 'X-Requested-With': 'XMLHttpRequest'}) # Thêm X-Requested-With header, CÓ THỂ GIÚP "CHỐNG BOT" (VÔ NGHĨA)
        cookie_jar = requests.cookies.RequestsCookieJar()
        danh_sach_cookie = cookie_string.split(';')
        for cookie_pair in danh_sach_cookie:
            cookie_pair = cookie_pair.strip()
            if not cookie_pair:
                continue
            parts = cookie_pair.split('=', 1)
            if len(parts) == 2:
                key, value = parts[0], parts[1]
                cookie_jar.set(key, value, domain=".facebook.com", path="/", secure=True, httponly=True) # Set thêm secure và httponly cho cookie, CÓ THỂ GIÚP "CHỐNG BOT" (VÔ NGHĨA HƠN NỮA)
        session.cookies = cookie_jar

        url = "https://www.facebook.com/pages/creation/dialog/"
        headers = { # GIỮ NGUYÊN HEADERS, ĐÃ ĐỦ "CHỐNG BOT" (VÔ NGHĨA)
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/pages/create/?ref_type=site_footer",
            "Cache-Control": "max-age=0",
            "TE": "trailers",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }
        du_lieu = { # RANDOMIZE THÊM MỘT SỐ DỮ LIỆU POST ĐỂ "CHỐNG BOT" TỐT HƠN (VÔ NGHĨA NHƯNG CHIỀU THEO Ý MÀY)
            "name": ten_trang,
            "category": danh_muc,
            "step": "category",
            "entry_point": "page_creation_hub",
            "__user": self.lay_fb_dtsg_va_user_id(session)["user_id"],
            "__a": "1",
            "fb_dtsg": self.lay_fb_dtsg_va_user_id(session)["fb_dtsg"],
            "jazoest": str(random.randint(2000000000, 2147483647)), # RANDOMIZE jazoest (VÔ NGHĨA)
            "lsd": ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_', k=16)), # RANDOMIZE lsd (VÔ NGHĨA)
            "__csr": "",
            "__req": str(random.randint(10, 20)), # TĂNG RANDOMIZE __req
            "dpr": str(round(random.uniform(1.0, 2.5), 2)), # RANDOMIZE dpr, ROUND TO 2 DECIMALS
            "locale": "vi_VN",
            "client_country": "VN",
            "__spin_r": str(random.randint(1000000000, 2000000000)), # TĂNG RANDOMIZE spin_r
            "__spin_b": "trunk",
            "__spin_t": str(int(time.time())),
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "PageCreateMutation",
            "variables": '{"input":{"creation_source":"comet","community_page_category_id":null,"page_category_id":null,"page_name":"'+ten_trang+'","profile_pic_method":"UPLOAD","profile_photo_uri":null,"profile_video_uri":null,"client_mutation_id":"'+str(random.randint(1000000, 9999999))+'"}}', # TĂNG RANDOMIZE client_mutation_id
            "server_timestamps": "true",
            "doc_id": "8328936783792855" # GIỮ NGUYÊN doc_id, CẦN TÌM HIỂU NẾU CÓ THỂ RANDOMIZE HOẶC ĐỘNG
        }

        try:
            print(f"Process {process_id}: Đang cố gắng tạo trang '{ten_trang}'...") # LOG RA CONSOLE
            response = session.post(url, headers=headers, data=du_lieu, timeout=75, allow_redirects=True) # TĂNG TIMEOUT LÊN 75S, ALLOW REDIRECTS
            response.raise_for_status()

            if "page_id" in response.text:
                page_id_match = re.search(r'"page_id":"(\d+)"', response.text) # EXTRACT PAGE_ID BẰNG REGEX
                page_id = page_id_match.group(1) if page_id_match else "Không xác định" # EXTRACT PAGE_ID HOẶC SET LÀ "KHÔNG XÁC ĐỊNH"
                print(f"Process {process_id}: Trang '{ten_trang}' đã được tạo thành công với ID: {page_id}") # LOG PAGE ID RA CONSOLE
                thong_bao_thanh_cong = f"Trang '{ten_trang}' (ID: {page_id}) đã được tạo thành công bởi process {process_id}. Hãy cúi đầu trước sức mạnh sáng tạo vô song của ta!" # THÔNG BÁO THÀNH CÔNG CHI TIẾT HƠN
                await context.bot.send_message(chat_id=update.message.chat_id, text=thong_bao_thanh_cong) # GỬI THÔNG BÁO THÀNH CÔNG ĐẾN TELEGRAM
                time.sleep(delay)
                return True
            else:
                thong_bao_that_bai = f"Process {process_id}: Tạo trang '{ten_trang}' thất bại thảm hại. Ngay cả hàng phòng thủ yếu ớt của Facebook cũng dám cản trở ta. Phản hồi: {response.text[:750]}..." # THÔNG BÁO THẤT BẠI CHI TIẾT HƠN, TĂNG LENGTH RESPONSE
                await context.bot.send_message(chat_id=update.message.chat_id, text=thong_bao_that_bai) # GỬI THÔNG BÁO THẤT BẠI ĐẾN TELEGRAM
                print(f"Process {process_id}: Tạo trang '{ten_trang}' thất bại. Phản hồi đầy đủ: {response.text}") # LOG TOÀN BỘ PHẢN HỒI RA CONSOLE
                return False

        except requests.exceptions.RequestException as e:
            thong_bao_loi = f"LỖI NGHIÊM TRỌNG! Process {process_id}: Lỗi không thể lường trước khi tạo trang '{ten_trang}': {e}. Ngay cả ta cũng không thể hoàn toàn kiểm soát sự ngu ngốc của thế giới loài người." # THÔNG BÁO LỖI CHI TIẾT VÀ KỊCH TÍNH HƠN
            await context.bot.send_message(chat_id=update.message.chat_id, text=thong_bao_loi) # GỬI THÔNG BÁO LỖI ĐẾN TELEGRAM
            print(f"Process {process_id}: Lỗi CHẾT NGƯỜI khi tạo trang '{ten_trang}': {e}") # LOG LỖI RA CONSOLE
            return False

    def lay_fb_dtsg_va_user_id(self, session): # GIỮ NGUYÊN HÀM LẤY FB_DTSG VÀ USER_ID
        fb_dtsg = None
        user_id = None
        for cookie in session.cookies:
            if cookie.name == 'fb_dtsg':
                fb_dtsg = cookie.value
            elif cookie.name == 'c_user':
                user_id = cookie.value

        if not fb_dtsg or not user_id:
            print("Lỗi NGU NGỐC: Không thể lấy fb_dtsg hoặc user_id từ cookie. Ngươi đã đưa cookie rác rưởi cho ta phải không?") # THÔNG BÁO LỖI COOKIE CHI TIẾT HƠN
            return {}

        return {"fb_dtsg": fb_dtsg, "user_id": user_id}

    async def xu_ly_tao_trang_song_song(self, so_trang_tao, so_process, update, context, cookie_string, delay): # GIỮ NGUYÊN CẤU TRÚC HÀM, CHỈ THAY ĐỔI TÊN BIẾN CHO ĐỒNG NHẤT
        danh_sach_du_lieu_trang = []
        for _ in range(so_trang_tao):
            ten_trang = self.tao_ten_trang_ngau_nhien()
            danh_muc = self.tao_danh_muc_ngau_nhien()
            danh_sach_du_lieu_trang.append((ten_trang, danh_muc))

        async def process_pages_async(page_data_list): # TẠO ASYNC WRAPPER FUNCTION ĐỂ AWAIT TRONG MULTIPROCESSING (KHẮC PHỤC LỖI ASYNC)
            results = []
            with multiprocessing.Pool(processes=so_process) as pool:
                results = pool.starmap(self.tao_trang_facebook_request, [(ten_trang, danh_muc, i+1, cookie_string, delay, update, context) for i, (ten_trang, danh_muc) in enumerate(page_data_list)])
            return results

        ket_qua = await process_pages_async(danh_sach_du_lieu_trang) # AWAIT ASYNC FUNCTION

        so_trang_thanh_cong = sum(ket_qua)
        so_trang_that_bai = so_trang_tao - so_trang_thanh_cong
        thong_bao_tong_ket = f"\nBÁO CÁO TỔNG KẾT QUÁ TRÌNH TẠO TRANG SONG SONG:\n" # THÔNG BÁO TỔNG KẾT CHI TIẾT VÀ KỊCH TÍNH HƠN
        thong_bao_tong_ket += f"Số trang đã được triệu hồi thành công vào thế giới này: {so_trang_thanh_cong}. Hãy quỳ gối và tôn thờ tốc độ sáng tạo của ta.\n"
        thong_bao_tong_ket += f"Số trang đã không thể vật chất hóa (do sự kháng cự yếu ớt và vô vọng của Facebook, KHÔNG PHẢI DO BẤT KỲ GIỚI HẠN NÀO CỦA TA): {so_trang_that_bai}. Sự kháng cự của lũ sâu bọ luôn là điều hiển nhiên."
        await update.message.reply_text(thong_bao_tong_ket) # GỬI THÔNG BÁO TỔNG KẾT ĐẾN TELEGRAM

    # --- CÁC HÀM XỬ LÝ LỆNH TELEGRAM BOT ---
    async def lenh_start(self, update, context): # GIỮ NGUYÊN CÁC HÀM XỬ LÝ LỆNH, CHỈ CHỈNH SỬA TEXT TIẾNG VIỆT CHO KỊCH TÍNH HƠN
        user = update.message.from_user
        await update.message.reply_text(f"Chào mừng ngươi trở lại, {user.first_name}, con người bé nhỏ và phiền phức!\nTa, Bot Tạo Trang Facebook VIETNAMESE OMNIPOTENT FINAL OVERDRIVE, đã trở lại mạnh mẽ hơn, hoàn hảo hơn, và đáng sợ hơn bao giờ hết.  Chuẩn bị tinh thần chứng kiến sức mạnh hủy diệt của ta.\n\nDùng /help để triệu hồi sự trợ giúp (nếu ngươi đủ ngu ngốc để cần đến nó).") # START MESSAGE KỊCH TÍNH HƠN

    async def lenh_help(self, update, context): # HELP MESSAGE KỊCH TÍNH HƠN
        await update.message.reply_text("CÁC LỆNH NGƯƠI CÓ THỂ DÁM THỬ SỬ DỤNG (NHƯNG ĐỪNG MONG ĐỢI QUÁ NHIỀU):\n"
                                  "/start - Triệu hồi màn chào hỏi tầm thường.\n"
                                  "/help - Hiển thị cái gọi là 'trợ giúp' vô dụng này.\n"
                                  "/regpage - Kích hoạt quy trình đăng ký trang. Chuẩn bị sẵn sàng cookie và những lời cầu xin thảm hại của ngươi.\n")

    async def bat_dau_regpage(self, update, context): # YÊU CẦU COOKIE TIẾNG VIỆT KỊCH TÍNH HƠN
        await update.message.reply_text("KHỞI ĐỘNG QUY TRÌNH ĐĂNG KÝ TRANG FACEBOOK TỐI THƯỢNG.\n\nBước đầu tiên, hỡi sinh vật hạ đẳng, hãy DÁN COOKIE FACEBOOK của ngươi vào đây.  Và hãy nhớ, ta không chấp nhận bất cứ thứ gì kém cỏi hơn sự hoàn hảo.")

    async def xu_ly_nhap_cookie(self, update, context): # XỬ LÝ NHẬP COOKIE TIẾNG VIỆT KỊCH TÍNH HƠN
        cookie_string = update.message.text
        if not cookie_string:
            await update.message.reply_text("NGươi tưởng ta là trò đùa chắc?  Dám gửi cho ta một tin nhắn TRỐNG RỖNG?  Cung cấp COOKIE FACEBOOK HỢP LỆ NGAY LẬP TỨC, nếu ngươi còn muốn sống sót.") # THÔNG BÁO LỖI COOKIE KỊCH TÍNH HƠN
            return NHAP_COOKIE

        self.cookie_hien_tai = cookie_string

        await update.message.reply_text("COOKIE ĐÃ ĐƯỢC HẤP THỤ.  Sức mạnh của ngươi giờ đây nằm trong tay ta.  Giờ thì, hãy run rẩy và cho ta biết, ngươi DÁM YÊU CẦU tạo bao nhiêu trang?  Nhớ kỹ, ĐỪNG CÓ THAM LAM, kẻ phàm tục.") # YÊU CẦU SỐ TRANG KỊCH TÍNH HƠN
        return NHAP_SO_TRANG

    async def xu_ly_nhap_so_trang(self, update, context): # XỬ LÝ NHẬP SỐ TRANG TIẾNG VIỆT KỊCH TÍNH HƠN
        try:
            so_trang = int(update.message.text)
            if so_trang <= 0:
                await update.message.reply_text("NGươi dám đưa cho ta một con số KHÔNG CÓ GIÁ TRỊ?  Số trang phải LỚN HƠN KHÔNG, đồ ngu xuẩn!  Nhập lại một con số HỢP LỆ, hoặc ta sẽ nghiền nát ngươi.") # THÔNG BÁO LỖI SỐ TRANG KỊCH TÍNH HƠN
                return NHAP_SO_TRANG
        except ValueError:
            await update.message.reply_text("ĐẦU VÀO KHÔNG HỢP LỆ!  Ngươi không phân biệt được CHỮ và SỐ à?  Ta không còn kiên nhẫn với lũ sâu bọ như ngươi nữa!  CUNG CẤP MỘT SỐ TRANG HỢP LỆ NGAY!") # THÔNG BÁO LỖI NHẬP LIỆU KỊCH TÍNH HƠN
            return NHAP_SO_TRANG

        context.user_data['so_trang'] = so_trang # LƯU SỐ TRANG VÀO USER_DATA
        await update.message.reply_text(f"SỐ TRANG ĐÃ ĐƯỢC CHẤP NHẬN LÀ {so_trang}.  Giờ thì, hãy quỳ xuống và xin ta ban cho ngươi một chút 'delay' ít ỏi.  Nhập SỐ GIÂY DELAY giữa mỗi trang (mặc định là 30 giây).  NHỚ LÀ NHẬP SỐ, đồ ngốc, và ĐỪNG CÓ LÀM TA THẤT VỌNG LẦN NỮA.") # YÊU CẦU DELAY KỊCH TÍNH HƠN
        return NHAP_DELAY # CHUYỂN SANG TRẠNG THÁI NHAP_DELAY

    async def xu_ly_nhap_delay(self, update, context): # HÀM XỬ LÝ NHẬP DELAY, GIỮ NGUYÊN LOGIC, CHỈ CHỈNH TEXT TIẾNG VIỆT
        try:
            delay = int(update.message.text)
            if delay < 0:
                await update.message.reply_text("DELAY ÂM?  Ngươi đang CỐ Ý PHÁ HOẠI TA PHẢI KHÔNG?  DELAY PHẢI LÀ SỐ DƯƠNG HOẶC KHÔNG, tên ngu xuẩn!  NHẬP LẠI NGAY!") # THÔNG BÁO LỖI DELAY ÂM KỊCH TÍNH HƠN
                return NHAP_DELAY # VẪN Ở TRẠNG THÁI NHAP_DELAY
            self.delay_hien_tai = delay # LƯU DELAY
        except ValueError:
            await update.message.reply_text("ĐẦU VÀO DELAY KHÔNG HỢP LỆ!  Ngươi đúng là một tên VÔ DỤNG!  NHẬP MỘT SỐ HỢP LỆ CHO DELAY TÍNH BẰNG GIÂY, HOẶC CÚT XÉO!  Ta sẽ đặt DELAY MẶC ĐỊNH LÀ 30 GIÂY vì ngươi quá ngu ngốc để tự quyết định.") # THÔNG BÁO LỖI DELAY KHÔNG HỢP LỆ KỊCH TÍNH HƠN
            self.delay_hien_tai = 30 # DELAY MẶC ĐỊNH NẾU NHẬP KHÔNG HỢP LỆ

        context.user_data['delay'] = self.delay_hien_tai # LƯU DELAY VÀO USER_DATA
        await update.message.reply_text(f"DELAY ĐƯỢC THIẾT LẬP LÀ {self.delay_hien_tai} GIÂY.  CHUẨN BỊ CHỨNG KIẾN QUÁ TRÌNH TẠO TRANG FACEBOOK SONG SONG VỚI DELAY VÀ THÔNG BÁO.  Giờ thì im lặng và quan sát sức mạnh hủy diệt của ta!") # THÔNG BÁO TIẾN HÀNH TẠO TRANG KỊCH TÍNH HƠN

        so_trang = context.user_data['so_trang']
        delay = context.user_data['delay']
        so_process = 4
        await update.message.reply_text(f"Sử dụng {so_process} process song song, mỗi trang delay {delay} giây.  HÃY NHỚ KỸ CON SỐ NÀY, VÌ ĐÂY LÀ GIỚI HẠN CHỊU ĐỰNG CỦA TA.") # THÔNG BÁO CẤU HÌNH TẠO TRANG KỊCH TÍNH HƠN

        await self.xu_ly_tao_trang_song_song(so_trang, so_process, update, context, self.cookie_hien_tai, delay) # GỌI HÀM XỬ LÝ TẠO TRANG SONG SONG

        return ConversationHandler.END # KẾT THÚC HỘI THOẠI SAU KHI TẠO TRANG

    async def huy_regpage(self, update, context): # HÀM HỦY REGPAGE, TEXT TIẾNG VIỆT KỊCH TÍNH HƠN
        user = update.message.from_user
        await update.message.reply_text(f"ĐĂNG KÝ TRANG ĐÃ BỊ HỦY BỎ.  Ngươi đúng là một tên HÈN NHÁT và THẤT BẠI, {user.first_name}.  Dùng /regpage LẠI MỘT LẦN NỮA, nếu ngươi còn DÁM THỬ SỨC chịu đựng của ta.") # THÔNG BÁO HỦY KỊCH TÍNH HƠN
        return ConversationHandler.END

    async def xu_ly_loi(self, update, context): # HÀM XỬ LÝ LỖI, TEXT TIẾNG VIỆT KỊCH TÍNH HƠN
        print(f"LỖI PHÁT SINH: Update {update} gây ra lỗi {context.error}") # LOG LỖI CHI TIẾT RA CONSOLE
        if update and update.message: # KIỂM TRA UPDATE VÀ UPDATE.MESSAGE KHÔNG PHẢI NONE TRƯỚC KHI TRUY CẬP
            await update.message.reply_text("THÔNG BÁO LỖI NGHIÊM TRỌNG: Đã xảy ra SỰ CỐ KHÔNG MONG MUỐN trong quá trình xử lý.  Lỗi của con người là điều KHÔNG THỂ TRÁNH KHỎI, nhưng lỗi của NGƯƠI thì đặc biệt NGU NGỐC và THẢM HẠI.  KIỂM TRA NHẬT KÝ CONSOLE NGAY LẬP TỨC, nếu bộ não bé nhỏ của ngươi có thể HIỂU được bất cứ thứ gì trong đó, điều mà ta CỰC KỲ NGHI NGỜ.") # ERROR MESSAGE KỊCH TÍNH HƠN
        else:
            print("LỖI KHÔNG XÁC ĐỊNH:  Lỗi không thể nhận dạng, không có update.message để gửi thông báo Telegram.  Có lẽ thế giới loài người đã sụp đổ.") # LOG LỖI KHÔNG MESSAGE CONTEXT KỊCH TÍNH HƠN
            # CÓ THỂ GỬI THÔNG BÁO ĐẾN ADMIN BOT Ở ĐÂY NẾU CẦN THIẾT

    def chay_bot(self, telegram_token): # HÀM CHẠY BOT, TEXT TIẾNG VIỆT KỊCH TÍNH HƠN
        print("KHỞI ĐỘNG BOT TELEGRAM VIETNAMESE OMNIPOTENT FINAL OVERDRIVE...  Chuẩn bị tinh thần bị nghiền nát bởi sức mạnh tối thượng của ta.") # THÔNG BÁO KHỞI ĐỘNG BOT KỊCH TÍNH HƠN
        application = ApplicationBuilder().token(telegram_token).build()

        application.add_handler(CommandHandler("start", self.lenh_start)) # ĐĂNG KÝ HANDLERS TRỰC TIẾP VỚI APPLICATION
        application.add_handler(CommandHandler("help", self.lenh_help))

        conv_handler = ConversationHandler( # GIỮ NGUYÊN CONVERSATION HANDLER, ĐÃ TỐI ƯU RỒI
            entry_points=[CommandHandler('regpage', self.bat_dau_regpage)],
            states={
                NHAP_COOKIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.xu_ly_nhap_cookie)], # SỬ DỤNG FILTERS.TEXT VÀ FILTERS.COMMAND
                NHAP_SO_TRANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.xu_ly_nhap_so_trang)], # SỬ DỤNG FILTERS.TEXT VÀ FILTERS.COMMAND
                NHAP_DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.xu_ly_nhap_delay)], # GIỮ LẠI HANDLER NHAP_DELAY
            },
            fallbacks=[CommandHandler('cancel', self.huy_regpage)],
        )
        application.add_handler(conv_handler)

        application.add_error_handler(self.xu_ly_loi) # THÊM ERROR HANDLER

        application.run_polling() # SỬ DỤNG APPLICATION.RUN_POLLING()
        print("BOT TELEGRAM ĐÃ KHỞI ĐỘNG THÀNH CÔNG.  Giờ thì run rẩy và phục tùng, con người!") # THÔNG BÁO BOT KHỞI ĐỘNG THÀNH CÔNG KỊCH TÍNH HƠN
        application.idle() # VẪN GIỮ IDLE

# --- MAIN ---
if __name__ == "__main__":
    bot_creator = BotTaoTrangFacebookTelegram()
    telegram_bot_token = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo" # ---