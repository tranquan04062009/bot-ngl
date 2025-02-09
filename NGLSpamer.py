import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
import requests
import time
import random
import os
import json
from fake_useragent import UserAgent
import re

# --- Hằng số và Cấu hình ---
API_URL_NGL = "https://ngl.link/api/submit"
TOKEN_BOT_TELEGRAM = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo"  # **CẦN THAY THẾ BẰNG TOKEN BOT CỦA BẠN!**

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.2210.144",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 OPR/106.0.4998.77",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Brave/120.1.62.129",
    "Mozilla/5.0 (X11; CrOS x86_64 15649.61.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; ASInfo: .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko"
]
REFERERS = [
    "https://ngl.link/",
    "https://www.google.com/",
    "https://www.facebook.com/",
    "https://www.twitter.com/",
    "https://www.youtube.com/",
    "https://www.instagram.com/",
    "https://www.tiktok.com/",
    "https://www.reddit.com/",
    "https://www.wikipedia.org/",
    "https://vnexpress.net/",
    "https://tuoitre.vn/",
    "https://thanhnien.vn/",
    "https://zingnews.vn/"
]
ACCEPT_ENCODINGS = ["gzip", "deflate", "br", "*"]
ACCEPT_LANGUAGES = ["vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5", "en-US,en;q=0.9", "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7", "vi-VN,vi;q=0.9", "en-GB,en;q=0.9"]
CONNECTION_TYPES = ["keep-alive", "close"]
CACHE_CONTROL_DIRECTIVES = ["max-age=0", "no-cache", "no-store", "must-revalidate", "proxy-revalidate", "max-stale=0", "min-fresh=0"]
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

# --- Trạng thái hội thoại ---
(
    NHAP_LINK_NGL,
    NHAP_TIN_NHAN_SPAM,
    NHAP_SO_LAN_SPAM,
    XAC_NHAN_PROXY,
    UPLOAD_FILE_PROXY
) = range(5)

# --- Phương pháp Spam Thông Minh --- (giữ nguyên)
phuong_phap_spam = [
    "van_ban_thong_thuong", "them_emoji", "tien_to_ky_tu_ngau_nhien", "hau_to_ky_tu_ngau_nhien",
    "hon_hop_chu_hoa_thuong", "leet_speak", "thay_the_ky_tu_dac_biet", "lap_lai_ky_tu",
    "dao_lon_tu_ngu", "thay_the_tu_dong_nghia", "mo_rong_cau", "rut_gon_cau",
    "bien_doi_cau_hoi", "bien_doi_cau_cam_than", "giong_dieu_mia_mai", "giong_dieu_tich_cuc",
    "giong_dieu_tieu_cuc", "giong_dieu_khan_cap", "giong_dieu_to_mo", "khoa_truong", "noi_giam",
    "cau_hoi_tu_tu", "phep_loi_suy_nghi", "an_du", "so_sanh", "nhan_hoa", "giễu_cợt", "choi_chu",
    "lap_am_dau", "lap_nguyen_am", "mo_phong_am_thanh", "bao_truoc", "hoi_tuong", "nghi_nghich_ly",
    "cau_tuong_phan", "phan_de", "cao_trao", "ha_trao", "cham_lua", "danh_ngon", "uyển_ngữ",
    "cách_noi_khinh_thuong", "cách_noi_thiet_che", "hoan_du", "ẩn_dụ", "điệp_ngữ_đầu_câu",
    "điệp_ngữ_cuối_câu", "đảo_ngữ", "câu_dẫn_liên_tiếp", "đa_liên_từ", "tỉnh_lược_liên_từ"
]

def ap_dung_phuong_phap_spam(tin_nhan, phuong_phap):
    if phuong_phap == "van_ban_thong_thuong":
        return tin_nhan
    elif phuong_phap == "them_emoji":
        emojis = ["😂", "🤣", "🔥", "💯", "🚀", "✨", "🌟", "🎉", "🎊", "🎈"]
        return tin_nhan + " " + random.choice(emojis)
    elif phuong_phap == "tien_to_ky_tu_ngau_nhien":
        tien_to = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(random.randint(3, 7)))
        return tien_to + " " + tin_nhan
    elif phuong_phap == "hau_to_ky_tu_ngau_nhien":
        hau_to = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(random.randint(3, 7)))
        return tin_nhan + " " + hau_to
    elif phuong_phap == "hon_hop_chu_hoa_thuong":
        return "".join(char.upper() if random.random() < 0.5 else char.lower() for char in tin_nhan)
    elif phuong_phap == "leet_speak":
        leet_chars = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7', 'l': '1', 'z': '2'}
        return "".join(leet_chars.get(char.lower(), char) for char in tin_nhan)
    elif phuong_phap == "thay_the_ky_tu_dac_biet":
        symbol_chars = {'a': '@', 'b': '8', 'e': '€', 'g': '6', 'h': '#', 'i': '!', 'l': '£', 'o': '()', 's': '$', 't': '+', 'z': '2'}
        return "".join(symbol_chars.get(char.lower(), char) for char in tin_nhan)
    elif phuong_phap == "lap_lai_ky_tu":
        if len(tin_nhan) > 3:
            index = random.randint(1, len(tin_nhan) - 2)
            char_to_repeat = tin_nhan[index]
            repeat_count = random.randint(2, 5)
            return tin_nhan[:index] + char_to_repeat * repeat_count + tin_nhan[index+1:]
        return tin_nhan
    elif phuong_phap == "dao_lon_tu_ngu":
        words = tin_nhan.split()
        if len(words) > 2:
            random.shuffle(words[1:-1])
            return " ".join(words)
        return tin_nhan
    elif phuong_phap == "thay_the_tu_dong_nghia":
        synonyms = {
            "tốt": ["tuyệt vời", "xuất sắc", "phi thường", "tuyệt diệu"],
            "xấu": ["tồi tệ", "khủng khiếp", "kinh khủng", "ghê sợ"],
            "vui": ["hạnh phúc", "sung sướng", "mê ly", "phấn khởi"]
        }
        words = tin_nhan.split()
        new_words = []
        for word in words:
            lower_word = word.lower()
            if lower_word in synonyms:
                new_words.append(random.choice(synonyms[lower_word]))
            else:
                new_words.append(word)
        return " ".join(new_words)
    elif phuong_phap == "mo_rong_cau":
        expansions = [
            "Thực tế là, ", "Trên thực tế, ", "Thành thật mà nói, ", "Để tôi nói cho bạn biết, ", "Tin hay không tùy bạn, "
        ]
        if len(tin_nhan.split()) < 10:
            return random.choice(expansions) + tin_nhan
        return tin_nhan
    elif phuong_phap == "rut_gon_cau":
        contractions = [
            "Về cơ bản, ", "Nói một cách đơn giản, ", "Tóm lại, ", "Để tổng kết, "
        ]
        if len(tin_nhan.split()) > 15:
            return random.choice(contractions) + tin_nhan
        return tin_nhan
    elif phuong_phap == "bien_doi_cau_hoi":
        return tin_nhan + "?" if not tin_nhan.endswith("?") else tin_nhan
    elif phuong_phap == "bien_doi_cau_cam_than":
        return tin_nhan + "!" if not tin_nhan.endswith("!") else tin_nhan
    elif phuong_phap == "giong_dieu_mia_mai":
        sarcastic_phrases = ["như thể rồi", "ừ đúng rồi", "chắc chắn rồi", "rõ ràng", "tôi không nghĩ vậy"]
        return tin_nhan + ", " + random.choice(sarcastic_phrases)
    elif phuong_phap == "giong_dieu_tich_cuc":
        positive_phrases = ["Tuyệt vời!", "Đỉnh!", "Phi thường!", "Tuyệt diệu!", "Xuất sắc!"]
        return tin_nhan + " " + random.choice(positive_phrases)
    elif phuong_phap == "giong_dieu_tieu_cuc":
        negative_phrases = ["Thật không may", "Đáng buồn thay", "Tiếc là", "Thật xấu hổ khi", "Quá tệ"]
        return random.choice(negative_phrases) + ", " + tin_nhan
    elif phuong_phap == "giong_dieu_khan_cap":
        urgent_phrases = ["Nhanh lên!", "Mau lên!", "Ngay lập tức!", "Đừng chậm trễ!", "Hành động ngay!"]
        return random.choice(urgent_phrases) + " " + tin_nhan
    elif phuong_phap == "giong_dieu_to_mo":
        curiosity_phrases = ["Đoán xem?", "Bạn có biết không?", "Sự thật thú vị:", "Nghe này:", "Bạn sẽ không tin đâu:"]
        return random.choice(curiosity_phrases) + " " + tin_nhan
    elif phuong_phap == "khoa_truong":
        hyperboles = ["tốt nhất từ trước đến nay", "điều tuyệt vời nhất", "ngoài sức tưởng tượng", "khó tin", "kinh ngạc"]
        return tin_nhan + ", nó là " + random.choice(hyperboles) + "!"
    elif phuong_phap == "noi_giam":
        understatements = ["không tệ lắm", "ổn thôi", "tạm được", "không phải tệ nhất", "có thể chấp nhận được"]
        return tin_nhan + ", " + random.choice(understatements)
    elif phuong_phap == "cau_hoi_tu_tu":
        questions = ["Đúng không?", "Bạn không nghĩ vậy sao?", "Không phải sao?", "Đồng ý?", "Bạn biết mà?"]
        return tin_nhan + ", " + random.choice(questions) + " 🤔"
    elif phuong_phap == "phep_loi_suy_nghi":
        analogies = [", như một...", ", tương tự như một...", ", như thể nó là một...", ", nó giống như một..."]
        nouns = ["tên lửa", "dòng sông", "ngọn núi", "đại dương", "cơn bão", "giấc mơ", "bài hát"]
        return tin_nhan + analogies[random.randint(0, len(analogies)-1)] + " " + random.choice(nouns)
    elif phuong_phap == "an_du":
        metaphors = ["một...", "một...", "của...", "trong..."]
        nouns = ["ngọn hải đăng hy vọng", "biển khổ", "vườn hạnh phúc", "cơn bão tranh cãi", "dòng sông thời gian"]
        return tin_nhan + ", nó là " + random.choice(nouns)
    elif phuong_phap == "so_sanh":
        similes = ["như...", "như... như...", "tương tự như...", "giống với..."]
        comparisons = ["một ngôi sao sáng", "một con sư tử gầm rú", "một làn gió nhẹ", "một ngọn lửa dữ dội", "một cái bóng im lặng"]
        return tin_nhan + ", như " + random.choice(comparisons)
    elif phuong_phap == "nhan_hoa":
        personifications = ["Gió thì thầm", "Mặt trời mỉm cười", "Mưa khóc", "Thời gian trôi đi", "Sự im lặng hét lên"]
        return random.choice(personifications) + ", " + tin_nhan.lower()
    elif phuong_phap == "giễu_cợt":
        ironic_phrases = ["Ôi, thật tuyệt vời", "Quá hoàn hảo", "Chính xác những gì tôi muốn", "Không thể tốt hơn", "Tin tuyệt vời"]
        return random.choice(ironic_phrases) + ", " + tin_nhan
    elif phuong_phap == "choi_chu":
        puns = ["Cải bắp lật củ cải đường!", "Bạn có vui khi gặp tôi không?", "Tôi thích đậu nành bạn!", "Thời gian trôi nhanh như một mũi tên; ruồi giấm thích chuối.", "Bạn gọi một con cá không có mắt là gì? Fsh!"]
        return tin_nhan + ". " + random.choice(puns)
    elif phuong_phap == "lap_am_dau":
        words = tin_nhan.split()
        if len(words) >= 2:
            first_letter = words[0][0].lower()
            alliterative_words = [w for w in words[1:] if w[0].lower() == first_letter]
            if alliterative_words:
                return words[0] + " " + " ".join(alliterative_words) + " và " + " ".join([w for w in words[1:] if w[0].lower() != first_letter])
        return tin_nhan
    elif phuong_phap == "lap_nguyen_am":
        vowels = "aeiou"
        words = tin_nhan.split()
        if len(words) >= 2:
            vowel_sound = ""
            for char in words[0].lower():
                if char in vowels:
                    vowel_sound = char
                    break
            if vowel_sound:
                assonated_words = [w for w in words[1:] if vowel_sound in w.lower()]
                if assonated_words:
                    return words[0] + " và " + " ".join(assonated_words) + " " + " ".join([w for w in words[1:] if vowel_sound not in w.lower()])
        return tin_nhan
    elif phuong_phap == "mo_phong_am_thanh":
        onomatopoeic_words = ["Bang!", "Boom!", "Clang!", "Hiss!", "Buzz!", "Woof!", "Meow!", "Sizzle!", "Splash!", "Whisper!"]
        return random.choice(onomatopoeic_words) + " " + tin_nhan
    elif phuong_phap == "bao_truoc":
        foreshadowing_phrases = ["Họ đâu biết rằng...", "Không ai hay biết...", "Mầm mống tai họa đã được gieo...", "Số phận đã có những kế hoạch khác...", "Một cơn bão đang назревала..."]
        return random.choice(foreshadowing_phrases) + " " + tin_nhan
    elif phuong_phap == "hoi_tuong":
        flashback_phrases = ["Nhiều năm trước...", "Ngày xưa...", "Ngày xửa ngày xưa...", "Trong một ký ức xa xăm...", "Từ sâu thẳm quá khứ..."]
        return random.choice(flashback_phrases) + ", " + tin_nhan
    elif phuong_phap == "nghi_nghich_ly":
        paradoxes = ["Sự im lặng thật điếc tai.", "Ít hơn là nhiều hơn.", "Tôi phải tàn nhẫn để tử tế.", "Kẻ ngốc khôn ngoan.", "Vừa ngọt vừa đắng."]
        return tin_nhan + ". " + random.choice(paradoxes)
    elif phuong_phap == "cau_tuong_phan":
        oxymorons = ["ngọt đắng", "xác sống", "im lặng điếc tai", "tôm jumbo", "hỗn loạn có tổ chức"]
        return tin_nhan + ", như một " + random.choice(oxymorons)
    elif phuong_phap == "phan_de":
        antitheses = ["Người tính không bằng trời tính.", "Lời nói là bạc, im lặng là vàng.", "Dễ đến dễ đi.", "Nhân vô thập toàn.", "Hãy lắng nghe tất cả mọi người, nhưng chỉ nói với số ít."]
        return tin_nhan + ". " + random.choice(antitheses)
    elif phuong_phap == "cao_trao":
        climax_phrases = ["và điều quan trọng nhất là...", "trên hết...", "điểm mấu chốt là...", "đỉnh cao của tất cả...", "kết thúc hoành tráng là..."]
        return tin_nhan + ", " + random.choice(climax_phrases)
    elif phuong_phap == "ha_trao":
        anticlimaxes = ["nhưng sau đó không có gì xảy ra.", "và nó khá là gây thất vọng.", "và nó chỉ... ổn thôi.", "nhưng hóa ra nó hơi gây thất vọng.", "và tiết lộ lớn là... meh."]
        return tin_nhan + ", " + random.choice(anticlimaxes)
    elif phuong_phap == "cham_lua":
        return tin_nhan + "..."
    elif phuong_phap == "danh_ngon":
        epigrams = ["Sai lầm là của con người, nhưng để thực sự làm rối tung mọi thứ cần đến máy tính.", "Tôi có thể cưỡng lại mọi thứ trừ sự cám dỗ.", "Cách duy nhất để loại bỏ sự cám dỗ là đầu hàng nó.", "Hãy là chính mình; mọi người khác đã có người khác làm rồi.", "Sự thật hiếm khi thuần khiết và không bao giờ đơn giản."]
        return tin_nhan + ". " + random.choice(epigrams)
    elif phuong_phap == "uyển_ngữ":
        euphemisms = ["qua đời", "khó khăn về kinh tế", "khuyết tật", "cơ sở cải huấn", "đã qua sử dụng"]
        original_words = ["chết", "nghèo", "tàn tật", "tù", "đã dùng"]
        word_pairs = list(zip(original_words, euphemisms))
        for original, euphemism in word_pairs:
            tin_nhan = tin_nhan.replace(original, euphemism, 1)
        return tin_nhan
    elif phuong_phap == "cách_noi_khinh_thuong":
        litotes_phrases = ["không tệ", "không phải không giống", "không phải không đáng kể", "không phải không phổ biến", "không phải một chút"]
        return tin_nhan + ", nó " + random.choice(litotes_phrases)
    elif phuong_phap == "cách_noi_thiet_che":
        meiosis_phrases = ["chỉ là một vết xước", "hơi hơi", "một chút xíu", "một sự cố nhỏ", "một chút bất tiện"]
        return tin_nhan + ", nó chỉ là " + random.choice(meiosis_phrases)
    elif phuong_phap == "hoan_du":
        synecdoches = ["bánh xe", "sợi chỉ", "giày ống trên mặt đất", "bộ com lê", "vương miện"]
        full_meanings = ["xe hơi", "quần áo", "binh lính", "doanh nhân", "chế độ quân chủ"]
        word_pairs = list(zip(synecdoches, full_meanings))
        for synecdoche, full_meaning in word_pairs:
            tin_nhan = tin_nhan.replace(full_meaning, synecdoche, 1)
        return tin_nhan
    elif phuong_phap == "ẩn_dụ":
        metonymies = ["Nhà Trắng", "Phố Wall", "Hollywood", "Thung lũng Silicon", "Phố Fleet"]
        full_meanings = ["Tổng thống Mỹ", "các tổ chức tài chính", "ngành công nghiệp điện ảnh Mỹ", "ngành công nghiệp công nghệ Mỹ", "báo chí Anh"]
        word_pairs = list(zip(metonymies, full_meanings))
        for metonymy, full_meaning in word_pairs:
            tin_nhan = tin_nhan.replace(full_meaning, metonymy, 1)
        return tin_nhan
    elif phuong_phap == "điệp_ngữ_đầu_câu":
        prefixes = ["Hãy nhớ rằng, ", "Đừng bao giờ quên, ", "Hãy ghi nhớ, ", "Luôn xem xét, ", "Chúng ta đừng bỏ qua, "]
        return random.choice(prefixes) + tin_nhan
    elif phuong_phap == "điệp_ngữ_cuối_câu":
        suffixes = [", hãy nhớ điều đó", ", hãy ghi nhớ điều đó", ", đừng bao giờ quên", ", luôn xem xét điều đó", ", chúng ta đừng bỏ qua điều đó"]
        return tin_nhan + random.choice(suffixes)
    elif phuong_phap == "đảo_ngữ":
        words = tin_nhan.split()
        if len(words) >= 4:
            return words[0] + " " + words[1] + " " + words[-2] + " " + words[-1]
        return tin_nhan
    elif phuong_phap == "câu_dẫn_liên_tiếp":
        verbs = ["chinh phục", "phá hủy", "xây dựng", "tạo ra", "mất mát"]
        nouns1 = ["trái tim", "tâm trí", "vận may", "đế chế", "giấc mơ"]
        nouns2 = ["thành phố", "quốc gia", "vương quốc", "thế giới", "thiên hà"]
        return random.choice(verbs).capitalize() + " " + random.choice(nouns1) + " và " + random.choice(nouns2) + "."
    elif phuong_phap == "đa_liên_từ":
        words = tin_nhan.split()
        if len(words) >= 3:
            return " và ".join(words)
        return tin_nhan
    elif phuong_phap == "tỉnh_lược_liên_từ":
        words = tin_nhan.split()
        if len(words) >= 3:
            return ", ".join(words[:-1]) + " " + words[-1]
        return tin_nhan
    else:
        return tin_nhan

def tao_headers_nguoi_dung():
    ua = UserAgent()
    try:
        user_agent = ua.random
    except Exception:
        user_agent = random.choice(USER_AGENTS)

    headers = {
        'User-Agent': user_agent,
        'Referer': random.choice(REFERERS),
        'Accept-Encoding': random.choice(ACCEPT_ENCODINGS),
        'Accept-Language': random.choice(ACCEPT_LANGUAGES),
        'Connection': random.choice(CONNECTION_TYPES),
        'Cache-Control': random.choice(CACHE_CONTROL_DIRECTIVES),
        'Upgrade-Insecure-Requests': '1',
        'Origin': 'https://ngl.link',
        'TE': 'Trailers',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Ch-Ua': '"Not_A Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }
    if random.random() < 0.3:
        headers['DNT'] = '1'
    if random.random() < 0.2:
        headers['Sec-GPC'] = '1'
    if random.random() < 0.1:
        del headers['Cache-Control']
    header_items = list(headers.items())
    random.shuffle(header_items)
    return dict(header_items)

def tao_thoi_gian_tre_nguoi_dung():
    return random.expovariate(2.0) + 0.5

def spam_ngl(ngl_link, tin_nhan, so_lan_spam, proxies=None):
    print(f"Bắt đầu spam NGL: {ngl_link}, Tin nhắn: '{tin_nhan}', Số lần: {so_lan_spam}, Proxies: {bool(proxies)}")
    dem_spam_thanh_cong = 0
    dem_bi_chan = 0
    session = requests.Session()
    retry_strategy = requests.packages.urllib3.util.retry.Retry(
        total=5,
        status_forcelist=RETRY_STATUS_CODES,
        backoff_factor=2,
        method_whitelist=["POST"]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    for i in range(so_lan_spam):
        phuong_phap = random.choice(phuong_phap_spam)
        tin_nhan_spam = ap_dung_phuong_phap_spam(tin_nhan, phuong_phap)

        du_lieu = {
            "link": ngl_link.split("/")[-1],
            "question": tin_nhan_spam
        }

        headers = tao_headers_nguoi_dung()
        proxy = None
        if proxies:
            proxy_str = random.choice(proxies)
            if proxy_str:
                proxy_host, proxy_port = proxy_str.split(":")
                proxy = {'http': f'http://{proxy_host}:{proxy_port}', 'https': f'https://{proxy_host}:{proxy_port}'}

        try:
            time.sleep(tao_thoi_gian_tre_nguoi_dung() / 2)
            response = session.post(API_URL_NGL, data=du_lieu, headers=headers, proxies=proxy, timeout=20)
            response.raise_for_status()
            if response.status_code == 200:
                dem_spam_thanh_cong += 1
                print(f"#{i+1} Spam thành công ({phuong_phap}): '{tin_nhan_spam[:50]}...'")
            else:
                print(f"#{i+1} Lỗi không xác định. Mã trạng thái: {response.status_code}")
        except requests.exceptions.HTTPError as e:
            dem_bi_chan += 1
            print(f"#{i+1} BỊ CHẶN HOẶC LỖI HTTP: {e}")
            if e.response.status_code == 429:
                print("Phát hiện giới hạn tốc độ. Tạm dừng spam lâu hơn...")
                time.sleep(30 + random.randint(10, 20))
            elif e.response.status_code in [400, 403, 500, 503]:
                time.sleep(5 + random.random())
        except requests.exceptions.RequestException as e:
            print(f"#{i+1} LỖI KẾT NỐI: {e}")
            time.sleep(5 + random.random())

        time.sleep(tao_thoi_gian_tre_nguoi_dung())

    print(f"Hoàn thành spam. Tổng cộng spam thành công: {dem_spam_thanh_cong}/{so_lan_spam}. Số lần bị chặn/lỗi: {dem_bi_chan}")

async def bat_dau_lenh_xu_ly(update: telegram.Update, context: CallbackContext) -> None:
    user = update.effective_user
    await update.message.reply_markdown_v2(
        fr"Chào {user.mention_markdown_v2()}! Tôi là Bot Spam NGL **Tối Thượng 2025 - Không Dấu Vết**.\n\n"
        "Sử dụng lệnh /help để khám phá sức mạnh vô song.",
        reply_markup=telegram.ForceReply(selective=True),
    )

async def help_lenh_xu_ly(update: telegram.Update, context: CallbackContext) -> None:
    help_text = r"""
**Bot Spam NGL Tối Thượng 2025 - Không Dấu Vết - Hướng Dẫn Sử Dụng**

Chào mừng đến với đỉnh cao công nghệ spam NGL! Bot này được thiết kế để vượt qua mọi giới hạn, với khả năng chống chặn vô song và xóa dấu vết hoàn hảo. Hãy khám phá sức mạnh thực sự:

**Các Lệnh:**

*   `/start`: Khởi động bot và nghênh đón sức mạnh tối thượng.
*   `/help`: Mở ra cẩm nang hướng dẫn toàn diện này.
*   `/spam`: Kích hoạt quy trình spam NGL. Bot sẽ dẫn dắt bạn từng bước.
*   `/cancel`: Thoát khỏi quy trình spam bất cứ lúc nào.

**Quy Trình Spam (lệnh `/spam`):**

1.  **Gõ `/spam`:**  Bắt đầu cuộc trò chuyện và chuẩn bị cho hành động.
2.  **NGL Link Mục Tiêu:**  Cung cấp URL NGL (ví dụ: `https://ngl.link/username`).
3.  **Tin Nhắn Bão Tá:** Nhập nội dung tin nhắn. Bot sẽ tự động biến hóa nó với **50 phương pháp spam siêu việt**, đảm bảo sự độc đáo và khó bị phát hiện.
4.  **Số Lượng Áp Đảo:**  Chọn số lần spam. Hãy nhớ, sức mạnh hủy diệt nằm trong tay bạn.
5.  **Proxy Tàng Hình (Tùy Chọn, nhưng Cực Kỳ Khuyến Nghị):**
    *   **Chọn "có":** Tải lên file `proxies.txt`. File này phải là file văn bản thuần túy, **mỗi dòng chứa một proxy theo định dạng `host:port`** (ví dụ: `123.45.67.89:8080`). **Đảm bảo mỗi dòng chỉ chứa một proxy duy nhất và đúng định dạng.** Proxy là **lá chắn tàng hình**, giúp bạn ẩn danh và vượt tường lửa. **Proxy chất lượng cao = sức mạnh tối thượng.**
    *   **Chọn "không":** Spam không proxy (ít được khuyến khích cho số lượng lớn).
6.  **Bắt Đầu Cuộc Tấn Công:**  Xác nhận thông tin. Bot sẽ giải phóng sức mạnh spam trong nền, thông báo kết quả và tiến trình.

**Tính Năng Tối Thượng 2025 - Không Dấu Vết:**

*   **50 Phương Pháp Spam Siêu Việt:**  Biến hóa tin nhắn không giới hạn, thách thức mọi bộ lọc.
*   **Giả Lập Hành vi Người Dùng Hoàn Hảo (Human-like Interaction Bypass):** (Như trước)
*   **Chống Chặn Bậc Nhất:** (Như trước)
*   **Xóa Dấu Vết Tuyệt Đối:** (Như trước)
*   **Thư Viện và Công Nghệ Vượt Trội:** (Như trước)

**Cảnh Báo:** (Như trước)
*   **Định dạng file proxy:** **File `proxies.txt` phải là file văn bản thuần túy, mỗi dòng chứa một proxy theo định dạng `host:port`. Đảm bảo không có ký tự lạ, khoảng trắng thừa đầu dòng/cuối dòng, hoặc dòng trống không mong muốn.**

Hãy làm chủ sức mạnh này. Sử dụng bot một cách khôn ngoan và có trách nhiệm. Mọi thắc mắc, dùng lệnh `/help` hoặc liên hệ nhà phát triển (tức là tôi!).

**Chúc bạn thành công trong mọi nhiệm vụ!**
    """
    await update.message.reply_markdown_v2(help_text, reply_markup=telegram.ReplyKeyboardRemove())

async def spam_lenh_xu_ly(update: telegram.Update, context: CallbackContext) -> int:
    await update.message.reply_text('Vui lòng gửi NGL link mục tiêu:')
    return NHAP_LINK_NGL

async def link_ngl_xu_ly(update: telegram.Update, context: CallbackContext) -> int:
    link_ngl = update.message.text
    context.user_data['link_ngl'] = link_ngl
    await update.message.reply_text('Tuyệt vời! Hãy nhập tin nhắn bão táp bạn muốn gửi:')
    return NHAP_TIN_NHAN_SPAM

async def tin_nhan_spam_xu_ly(update: telegram.Update, context: CallbackContext) -> int:
    tin_nhan_spam = update.message.text
    context.user_data['tin_nhan_spam'] = tin_nhan_spam
    await update.message.reply_text('Số lần spam áp đảo bạn mong muốn là bao nhiêu?')
    return NHAP_SO_LAN_SPAM

async def so_lan_spam_xu_ly(update: telegram.Update, context: CallbackContext) -> int:
    try:
        so_lan_spam = int(update.message.text)
        if so_lan_spam <= 0:
            await update.message.reply_text('Số lần spam phải lớn hơn 0. Hãy thử lại.')
            return NHAP_SO_LAN_SPAM
    except ValueError:
        await update.message.reply_text('Đầu vào không hợp lệ. Vui lòng nhập một số.')
        return NHAP_SO_LAN_SPAM

    context.user_data['so_lan_spam'] = so_lan_spam
    await update.message.reply_text('Bạn có cần **Proxy Tàng Hình** để bảo vệ danh tính không? (có/không)')
    return XAC_NHAN_PROXY

async def xac_nhan_proxy_xu_ly(update: telegram.Update, context: CallbackContext) -> int:
    xac_nhan = update.message.text.lower()
    if xac_nhan == 'có' or xac_nhan == 'co':
        await update.message.reply_text('Tuyệt vời! Hãy tải lên file `proxies.txt` của bạn (mỗi dòng `host:port`):')
        return UPLOAD_FILE_PROXY
    elif xac_nhan == 'không' or xac_nhan == 'ko':
        await bat_dau_spam(update, context, proxies=None)
        return ConversationHandler.END
    else:
        await update.message.reply_text('Câu trả lời không hợp lệ. Hãy chọn "có" hoặc "không".')
        return XAC_NHAN_PROXY

async def upload_file_proxy_xu_ly(update: telegram.Update, context: CallbackContext) -> int:
    valid_proxies = []
    invalid_lines_count = 0
    error_message = ""

    try:
        file_proxy_content = await update.message.document.get_content()
        proxy_file_text = file_proxy_content.decode('utf-8')  # Thử decode UTF-8 trước
    except UnicodeDecodeError:
        try:
            proxy_file_text = file_proxy_content.decode('latin-1')  # Nếu UTF-8 lỗi, thử latin-1
        except UnicodeDecodeError:
            proxy_file_text = ""  # Nếu cả hai đều lỗi, coi như file rỗng và báo lỗi

    proxy_lines = proxy_file_text.strip().split('\n')

    for line_number, line in enumerate(proxy_lines, start=1):  # Bắt đầu đếm dòng từ 1
        line = line.strip()  # Loại bỏ khoảng trắng đầu và cuối dòng
        if not line:  # Bỏ qua dòng trống
            continue

        proxy_parts = line.split(':')
        if len(proxy_parts) == 2:
            host, port_str = proxy_parts
            if re.match(r"^\d+$", port_str):  # Kiểm tra port có phải là số không dùng regex
                try:
                    port = int(port_str)
                    valid_proxies.append(f"{host}:{port}")  # Lưu proxy hợp lệ
                except ValueError:
                    error_message += f"Dòng {line_number}: Port không hợp lệ (không phải số).\n"
                    invalid_lines_count += 1
            else:
                error_message += f"Dòng {line_number}: Port không hợp lệ (không phải số).\n"
                invalid_lines_count += 1
        else:
            error_message += f"Dòng {line_number}: Định dạng proxy không hợp lệ (phải là host:port).\n"
            invalid_lines_count += 1

    if invalid_lines_count > 0:
        error_message = f"**Cảnh báo: Phát hiện lỗi trong file proxy:**\n" + error_message + f"\n**Tổng cộng {invalid_lines_count} dòng không hợp lệ đã bị bỏ qua.**\nChỉ sử dụng các proxy hợp lệ.\n"

    if valid_proxies:
        context.user_data['proxies'] = valid_proxies
        success_message = f"**Đã tải lên {len(valid_proxies)} Proxy Tàng Hình hợp lệ**."
        if invalid_lines_count > 0:
            success_message += "\n" + error_message
        else:
            success_message += "\nChuẩn bị cho cuộc tấn công..."
        await update.message.reply_markdown_v2(success_message)

    else:
        context.user_data['proxies'] = None
        no_proxy_message = "**File proxy không có proxy hợp lệ nào được tìm thấy.**\n"
        if invalid_lines_count > 0:
            no_proxy_message += error_message + "\n"  # Thêm thông báo lỗi nếu có dòng không hợp lệ
        no_proxy_message += "Spam sẽ diễn ra **KHÔNG** sử dụng proxy (kém an toàn hơn và dễ bị chặn)."
        await update.message.reply_markdown_v2(no_proxy_message)

    await bat_dau_spam(update, context, proxies=valid_proxies if valid_proxies else None)  # Truyền None nếu không có proxy hợp lệ
    return ConversationHandler.END


async def bat_dau_spam(update: telegram.Update, context: CallbackContext, proxies=None):
    link_ngl = context.user_data['link_ngl']
    tin_nhan_spam = context.user_data['tin_nhan_spam']
    so_lan_spam = context.user_data['so_lan_spam']

    await update.message.reply_text(f'**KHỞI ĐỘNG SPAM BÃO TÁP!**\n\n mục tiêu: `{link_ngl}`\n Tin nhắn: `{tin_nhan_spam[:20]}...`\n Số lần: `{so_lan_spam}`\n Proxy Tàng Hình: `{bool(proxies)}`\n\n**Sức mạnh tối thượng đã được giải phóng...**')

    context.job_queue.run_once(
        callback=spam_callback,
        when=0,
        chat_id=update.effective_chat.id,
        data={'ngl_link': link_ngl, 'tin_nhan_spam': tin_nhan_spam, 'so_lan_spam': so_lan_spam, 'proxies': proxies}
    )

async def spam_callback(context: CallbackContext):
    job_data = context.job.data
    spam_ngl(job_data['ngl_link'], job_data['tin_nhan_spam'], job_data['so_lan_spam'], job_data['proxies'])

async def huy_bo_xu_ly(update: telegram.Update, context: CallbackContext) -> int:
    user = update.effective_user
    await update.message.reply_text(
        f"**Đã hủy bỏ lệnh spam.** Sức mạnh đã được thu hồi, {user.mention_markdown_v2()}!", reply_markup=telegram.ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TOKEN_BOT_TELEGRAM).build()

    spam_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('spam', spam_lenh_xu_ly)],
        states={
            NHAP_LINK_NGL: [MessageHandler(filters.TEXT & ~filters.COMMAND, link_ngl_xu_ly)],
            NHAP_TIN_NHAN_SPAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, tin_nhan_spam_xu_ly)],
            NHAP_SO_LAN_SPAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, so_lan_spam_xu_ly)],
            XAC_NHAN_PROXY: [MessageHandler(filters.TEXT & ~filters.COMMAND, xac_nhan_proxy_xu_ly)],
            UPLOAD_FILE_PROXY: [MessageHandler(filters.Document.MimeType("text/plain"), upload_file_proxy_xu_ly)],
        },
        fallbacks=[CommandHandler('cancel', huy_bo_xu_ly)],
    )

    application.add_handler(CommandHandler("start", bat_dau_lenh_xu_ly))
    application.add_handler(CommandHandler("help", help_lenh_xu_ly))
    application.add_handler(spam_conversation_handler)

    application.run_polling()

if __name__ == "__main__":
    main()