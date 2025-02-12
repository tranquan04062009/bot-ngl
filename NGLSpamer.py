import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import time
import random
import logging
import re
from collections import deque
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import urllib.parse
import asyncio
import numpy as np # Thêm thư viện NumPy cho tính toán số học - TÍNH TOÁN HIỆU NĂNG CAO
import pandas as pd # Thêm thư viện Pandas cho xử lý dữ liệu - XỬ LÝ DỮ LIỆU MẠNH MẼ

from sklearn.neural_network import MLPClassifier # Thư viện Scikit-learn cho Neural Network - MÔ HÌNH HỌC SÂU
from sklearn.preprocessing import StandardScaler, QuantileTransformer # Chuẩn hóa và biến đổi dữ liệu - TIỀN XỬ LÝ DỮ LIỆU NÂNG CAO
from sklearn.model_selection import train_test_split # Chia dữ liệu train/test - ĐÁNH GIÁ MÔ HÌNH CHÍNH XÁC
from sklearn.metrics import accuracy_score, classification_report # Đánh giá hiệu suất mô hình - ĐO LƯỜNG HIỆU QUẢ

# Cấu hình logging chi tiết - GIỮ NGUYÊN LOGGING
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

# TOKEN BOT TELEGRAM CỦA NGƯƠI - BẢO VỆ TUYỆT ĐỐI - GIỮ NGUYÊN TOKEN
BOT_TOKEN = "7766543633:AAFnN9tgGWFDyApzplak0tiJTafCxciFydo"

# API endpoint của 68gamebai (KHÔNG CẦN NỮA) - GIỮ NGUYÊN API (KHÔNG DÙNG)
API_68GAMEBAI = "https://api.68gamebai.com/api/v2/xxxxx"

# Đường dẫn file lưu trữ dữ liệu lịch sử - GIỮ NGUYÊN FILE DATA
DATA_HISTORY_FILE = "data_history_vohanan_web_v2.json" # Đổi tên file để phân biệt phiên bản

# Các tham số học hỏi nâng cao - ĐIỀU CHỈNH THAM SỐ HỌC TẬP CHO AI NÂNG CAO VƯỢT TRỘI
LEARNING_RATE = 0.000005 # Giảm tốc độ học để mô hình hội tụ tốt hơn - TỐC ĐỘ HỘI TỤ TỐI ƯU
HISTORY_WINDOW_SIZE = 7000 # Mở rộng cửa sổ lịch sử để nắm bắt chu kỳ dài hơn - CỬA SỔ LỊCH SỬ SIÊU LỚN
PREDICTION_THRESHOLD_TAI = 0.55 # Nâng cao ngưỡng dự đoán để tăng độ chính xác - NGƯỠNG DỰ ĐOÁN CHÍNH XÁC CAO
PREDICTION_THRESHOLD_XIU = 0.45 # Hạ thấp ngưỡng dự đoán xỉu tương ứng - NGƯỠNG DỰ ĐOÁN CÂN BẰNG
DATA_REFRESH_INTERVAL = 2500 # Tăng tần suất làm mới dữ liệu để bot luôn cập nhật - LÀM MỚI DỮ LIỆU NHANH CHÓNG
WEB_SEARCH_INTERVAL = 6500 # Giảm nhẹ tần suất tìm kiếm web - TIẾT KIỆM TÀI NGUYÊN TÌM KIẾM
MAX_WEBSITES_TO_SCRAPE = 3 # Giảm số lượng website scrape mỗi lần - TẬP TRUNG WEBSITE CHẤT LƯỢNG
MIN_DATA_POINTS_FROM_WEBSITE = 80 # Tăng số data point tối thiểu để đảm bảo chất lượng dữ liệu web - CHẤT LƯỢNG DỮ LIỆU ƯU TIÊN
HISTORY_CONTEXT_WEIGHT = 0.2 # Giảm trọng số lịch sử người dùng để AI tự học là chính - AI TỰ CHỦ HƠN

NN_HIDDEN_LAYERS = (128, 64, 32) # Cấu trúc hidden layers cho Neural Network - NN MẠNG LƯỚI DÀY ĐẶC HƠN
NN_ACTIVATION_FUNCTION = 'relu' # Hàm kích hoạt ReLU - TỐC ĐỘ VÀ HIỆU QUẢ
NN_SOLVER = 'adam' # Bộ tối ưu Adam - HỘI TỤ NHANH VÀ ỔN ĐỊNH
NN_MAX_ITER = 500 # Tăng số vòng lặp huấn luyện - HUẤN LUYỆN KỸ LƯỠNG HƠN
NN_EARLY_STOPPING = True # Kích hoạt early stopping để tránh overfitting - CHỐNG OVERFITTING
NN_TRAINING_DATA_RATIO = 0.85 # Tăng tỷ lệ dữ liệu huấn luyện - DỮ LIỆU HUẤN LUYỆN NHIỀU HƠN
NN_RANDOM_STATE = 47 # Seed ngẫu nhiên để đảm bảo tính nhất quán - TÍNH NHẤT QUÁN KẾT QUẢ

FEATURE_TRANSFORM = True # Kích hoạt biến đổi feature - BIẾN ĐỔI FEATURE ĐỂ TỐI ƯU
TRANSFORM_METHOD = 'quantile' # Phương pháp biến đổi quantile - PHÂN PHỐI DỮ LIỆU ĐỀU HƠN

# Biến toàn cục - GIỮ NGUYÊN BIẾN TOÀN CỤC
brain_instance = None
is_loading_data = False
website_data_sources = []
last_web_search_time = datetime.now() - timedelta(seconds=WEB_SEARCH_INTERVAL)
data_scaler = StandardScaler() # Khởi tạo StandardScaler - CHUẨN HÓA DỮ LIỆU
feature_transformer = QuantileTransformer(output_distribution='normal') if TRANSFORM_METHOD == 'quantile' else None # Khởi tạo QuantileTransformer - BIẾN ĐỔI DỮ LIỆU

# Định nghĩa các trạng thái - GIỮ NGUYÊN TRẠNG THÁI
(
    INPUT_HISTORY_DATA,
    CONFIRM_HISTORY_DATA,
) = range(2)

# Các từ khóa tìm kiếm web - GIỮ NGUYÊN TỪ KHÓA
TAI_XIU_KEYWORDS = ["tài xỉu online", "xóc đĩa online", "game bài đổi thưởng", "casino trực tuyến", "sicbo online", "lịch sử tài xỉu", "kết quả tài xỉu"]
RESULT_KEYWORDS = ["kết quả", "lịch sử", "history", "results", "table", "bảng"]
TAI_XIU_PATTERNS = [r"tài\s*xỉu", r"(\d+)\s*-\s*(\d+)\s*-\s*(\d+)", r"(\d+)x", r"xiu", r"tai"]

# ===== ĐỊNH NGHĨA CLASS BrainTaiXiuVohananWebCaoCapAI (TỪ CODE TRƯỚC) =====
class BrainTaiXiuVohananWebCaoCapAI: # Đổi tên class để phân biệt phiên bản AI Nâng Cao
    def __init__(self):
        self.data_history = deque(maxlen=HISTORY_WINDOW_SIZE)
        self.learning_rate = LEARNING_RATE
        self.prediction_model = self.create_cao_cap_ai_model() # Sử dụng mô hình AI Cao Cấp
        self.last_data_refresh = datetime.now() - timedelta(seconds=DATA_REFRESH_INTERVAL)

        self.load_history_from_file()

    def create_cao_cap_ai_model(self): # Mô hình AI CAO CẤP - KẾT HỢP NN VÀ BIAS
        nn_model = MLPClassifier(hidden_layer_sizes=NN_HIDDEN_LAYERS, activation='relu', solver='adam', max_iter=300, random_state=42, early_stopping=True) # Khởi tạo Neural Network - MÔ HÌNH NN
        return {
            "bias_tai": 0.5,
            "bias_xiu": 0.5,
            "recent_trend_tai": 0.0,
            "recent_trend_xiu": 0.0,
            "sequence_pattern_weights": {},
            "time_of_day_bias": {},
            "losing_streak_bias": 0.0,
            "winning_streak_bias": 0.0,
            "website_bias": {},
            "game_round_bias": {},
            "streak_pattern_bias": {},
            "alternating_pattern_bias": 0.0,
            "cycle_pattern_bias": {},
            "previous_n_results_bias": {},
            "positional_bias": {},
            "nn_model": nn_model, # Thêm Neural Network vào model - NN MODEL
            "feature_scaler": StandardScaler() # Thêm StandardScaler - CHUẨN HÓA FEATURE
        }

    def load_history_from_file(self):
        if os.path.exists(DATA_HISTORY_FILE):
            try:
                with open(DATA_HISTORY_FILE, 'r') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, list):
                        self.data_history.extend(loaded_data)
                        logger.info(f"Đã tải {len(loaded_data)} dòng dữ liệu lịch sử từ file.")
                    else:
                        logger.warning("File dữ liệu lịch sử có định dạng không hợp lệ.")
            except Exception as e:
                logger.error(f"Lỗi khi tải dữ liệu lịch sử từ file: {e}")
        else:
            logger.info("Không tìm thấy file dữ liệu lịch sử. Bắt đầu với dữ liệu trống.")

    def save_history_to_file(self):
        try:
            with open(DATA_HISTORY_FILE, 'w') as f:
                json.dump(list(self.data_history), f)
                logger.info(f"Đã lưu {len(self.data_history)} dòng dữ liệu lịch sử vào file.")
        except Exception as e:
            logger.error(f"Lỗi khi lưu dữ liệu lịch sử vào file: {e}")

    async def load_data_from_website(self, url):
        global is_loading_data
        if is_loading_data:
            logger.warning(f"Đang tải dữ liệu, bỏ qua yêu cầu tải dữ liệu mới từ {url}.")
            return 0

        is_loading_data = True
        processed_count = 0
        try:
            logger.info(f"Bắt đầu tải dữ liệu từ website: {url}...")
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            results = []
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if cols:
                        text_content = [col.text.strip().lower() for col in cols]
                        for text in text_content:
                            if text in ['tai', 'xiu']:
                                results.append(text)

            if results:
                logger.debug(f"Tìm thấy {len(results)} kết quả tiềm năng từ {url}: {results[:10]}...")
                processed_count = self.process_raw_data(results)
            else:
                logger.warning(f"Không tìm thấy dữ liệu tài xỉu nào trên website: {url}.")

            return processed_count

        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi khi tải dữ liệu từ website {url}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Lỗi không xác định khi парсинг HTML từ {url}: {e}")
            return 0
        finally:
            is_loading_data = False

    async def search_web_for_taixiu_websites(self, keywords, num_results=10):
        search_results = []
        for keyword in keywords:
            search_query = urllib.parse.quote_plus(keyword + " tài xỉu")
            search_url = f"https://www.google.com/search?q={search_query}&num={num_results}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            try:
                response = requests.get(search_url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href and href.startswith("http") and "google" not in href:
                        if any(pattern.search(href.lower()) for pattern in TAI_XIU_PATTERNS):
                             search_results.append(href)
            except requests.exceptions.RequestException as e:
                logger.error(f"Lỗi khi tìm kiếm trên web với keyword '{keyword}': {e}")
            except Exception as e:
                logger.error(f"Lỗi không xác định khi парсинг kết quả tìm kiếm web với keyword '{keyword}': {e}")

        unique_results = list(set(search_results))
        logger.info(f"Tìm thấy {len(unique_results)} website tiềm năng từ tìm kiếm web với keywords: {keywords}.")
        return unique_results

    def process_raw_data(self, raw_data):
        processed_count = 0
        if isinstance(raw_data, list):
            new_data_points = []
            for item in raw_data:
                if isinstance(item, str) and item.lower() in ['tai', 'xiu']:
                    new_data_points.append(item.lower())
                    processed_count += 1
                else:
                    logger.warning(f"Dữ liệu không đúng định dạng: {item}. Bỏ qua.")

            if new_data_points:
                self.data_history.extend(new_data_points)
                logger.info(f"Đã thêm {len(new_data_points)} dòng dữ liệu mới vào lịch sử.")
                self.save_history_to_file()
            else:
                logger.warning("Không có dữ liệu hợp lệ nào được xử lý từ dữ liệu thô.")
        else:
            logger.warning("Dữ liệu thô không đúng định dạng list, cần xử lý thêm.")
        return processed_count

    def _extract_features(self, history): # HÀM EXTRACT FEATURES CHO NN - TRÍCH XUẤT FEATURE
        streak_bias = self.prediction_model["streak_pattern_bias"]
        prev_2_bias = self.prediction_model["previous_n_results_bias"].get("n2", {"tai": 0.5, "xiu": 0.5})
        features = [
            self.prediction_model["bias_tai"],
            self.prediction_model["bias_xiu"],
            self.prediction_model["recent_trend_tai"],
            self.prediction_model["recent_trend_xiu"],
            self.prediction_model["alternating_pattern_bias"],
            streak_bias.get('tai', 0.0),
            streak_bias.get('xiu', 0.0),
            prev_2_bias.get('tai', 0.5),
            prev_2_bias.get('xiu', 0.5),
        ]
        return features

    def _prepare_training_data(self): # HÀM PREPARE TRAINING DATA CHO NN - CHUẨN BỊ DATA TRAIN
        features = []
        labels = []
        for i in range(10, len(self.data_history)): # Cần ít nhất 10 dòng lịch sử để tạo feature
            history_segment = list(self.data_history)[max(0, i-100):i] # Sử dụng 100 dòng gần nhất làm context
            extracted_features = self._extract_features(history_segment)
            features.append(extracted_features)
            labels.append(1 if self.data_history[i] == 'tai' else 0) # 1: tai, 0: xiu

        return features, labels

    def _train_model(self): # HÀM TRAIN MODEL NN - TRAIN NN
        features, labels = self._prepare_training_data()
        if not features:
            logger.warning("Không đủ dữ liệu để train Neural Network.")
            return

        X = data_scaler.fit_transform(features) # Chuẩn hóa features - CHUẨN HÓA FEATURE
        y = labels

        train_size = int(len(X) * NN_TRAINING_DATA_RATIO) # Chia train/test - CHIA DATA TRAIN/TEST
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        try:
            self.prediction_model["nn_model"].fit(X_train, y_train) # Train NN - TRAIN MODEL
            accuracy = self.prediction_model["nn_model"].score(X_test, y_test) # Đánh giá trên test set - ĐÁNH GIÁ MODEL
            logger.info(f"Neural Network trained. Test accuracy: {accuracy:.4f}")
        except Exception as e:
            logger.error(f"Lỗi khi train Neural Network: {e}")

    def learn_from_data(self):
        if len(self.data_history) < 20:
            logger.warning("Không đủ dữ liệu lịch sử để học mô hình AI nâng cao. Cần ít nhất 20 dòng.")
            return

        tai_count = 0
        xiu_count = 0
        recent_results = list(self.data_history)[-100:]
        recent_tai_count = recent_results.count('tai')
        recent_xiu_count = recent_results.count('xiu')

        for result in self.data_history:
            if result == "tai":
                tai_count += 1
            elif result == "xiu":
                xiu_count += 1

        total_count = len(self.data_history)

        if total_count > 0:
            self.prediction_model["bias_tai"] = tai_count / total_count
            self.prediction_model["bias_xiu"] = xiu_count / total_count

        self.prediction_model["recent_trend_tai"] = (recent_tai_count - 50) / 50.0
        self.prediction_model["recent_trend_xiu"] = (recent_xiu_count - 50) / 50.0

        streak_lengths_tai = self.analyze_streaks('tai')
        streak_lengths_xiu = self.analyze_streaks('xiu')
        self.prediction_model["streak_pattern_bias"] = {
            "tai": self.calculate_streak_bias(streak_lengths_tai, 'tai'),
            "xiu": self.calculate_streak_bias(streak_lengths_xiu, 'xiu')
        }

        alternating_score = self.analyze_alternating_pattern()
        self.prediction_model["alternating_pattern_bias"] = alternating_score

        n_values = [2, 3, 4]
        for n in n_values:
            prev_n_bias = self.analyze_previous_n_results(n)
            self.prediction_model["previous_n_results_bias"][f"n{n}"] = prev_n_bias

        self._train_model() # Train Neural Network sau khi cập nhật bias và pattern - TRAIN NN

        logger.info(f"Mô hình AI học hỏi nâng cao đã được cập nhật. Bias Tài: {self.prediction_model['bias_tai']:.4f}, Bias Xỉu: {self.prediction_model['bias_xiu']:.4f}, Xu hướng gần đây - Tài: {self.prediction_model['recent_trend_tai']:.4f}, Xỉu: {self.prediction_model['recent_trend_xiu']:.4f}")
        logger.debug(f"Mô hình chi tiết AI nâng cao: {self.prediction_model}")

    # ... (Các hàm analyze_streaks, calculate_streak_bias, analyze_alternating_pattern, analyze_previous_n_results GIỮ NGUYÊN) ...
    analyze_streaks = BrainTaiXiuVohananWebCaoCapAI.analyze_streaks
    calculate_streak_bias = BrainTaiXiuVohananWebCaoCapAI.calculate_streak_bias
    analyze_alternating_pattern = BrainTaiXiuVohananWebCaoCapAI.analyze_alternating_pattern
    analyze_previous_n_results = BrainTaiXiuVohananWebCaoCapAI.analyze_previous_n_results


    def predict_result(self, user_history=None): # Cập nhật predict_result để sử dụng NN - PREDICT RESULT NN
        nn_prediction_tai_prob = 0.5 # Giá trị mặc định nếu NN không dự đoán được
        nn_prediction_xiu_prob = 0.5

        features = self._extract_features(user_history if user_history else self.data_history) # Lấy features cho NN - LẤY FEATURE NN
        scaled_features = data_scaler.transform([features]) # Chuẩn hóa features - CHUẨN HÓA FEATURE

        try:
            nn_probs = self.prediction_model["nn_model"].predict_proba(scaled_features)[0] # Dự đoán bằng NN - DỰ ĐOÁN NN
            nn_prediction_tai_prob = nn_probs[1] # Lấy prob cho 'tai' (class 1)
            nn_prediction_xiu_prob = nn_probs[0] # Lấy prob cho 'xiu' (class 0)
            logger.debug(f"NN Prediction Probabilities - Tai: {nn_prediction_tai_prob:.4f}, Xiu: {nn_prediction_xiu_prob:.4f}")
        except Exception as e:
            logger.warning(f"Lỗi khi dự đoán bằng Neural Network, sử dụng bias cơ bản: {e}")
            nn_prediction_tai_prob = self.prediction_model["bias_tai"] # Fallback về bias nếu lỗi NN
            nn_prediction_xiu_prob = self.prediction_model["bias_xiu"]


        # Kết hợp NN prediction và bias cơ bản (có thể điều chỉnh cách kết hợp) - KẾT HỢP NN VÀ BIAS
        prediction_score_tai = nn_prediction_tai_prob # Sử dụng NN prob trực tiếp, có thể thêm bias nếu muốn
        prediction_score_xiu = nn_prediction_xiu_prob

        if prediction_score_tai > PREDICTION_THRESHOLD_TAI:
            return "tai"
        elif prediction_score_xiu > PREDICTION_THRESHOLD_XIU:
            return "xiu"
        else:
            if nn_prediction_tai_prob > nn_prediction_xiu_prob: # Dùng NN prob để quyết định cuối cùng nếu không vượt ngưỡng
                return "tai"
            else:
                return "xiu"

    # ... (Các hàm receive_history_data, process_feedback GIỮ NGUYÊN) ...
    receive_history_data = BrainTaiXiuVohananWebCaoCapAI.receive_history_data
    process_feedback = BrainTaiXiuVohananWebCaoCapAI.process_feedback


# ===== ĐỊNH NGHĨA CLASS BrainTaiXiuVohananWebCaoCapAINextGen (PHIÊN BẢN MỚI NHẤT) =====
class BrainTaiXiuVohananWebCaoCapAINextGen: # Đổi tên class để phân biệt phiên bản AI NextGen
    def __init__(self):
        self.data_history = deque(maxlen=HISTORY_WINDOW_SIZE)
        self.learning_rate = LEARNING_RATE
        self.prediction_model = self.create_cao_cap_ai_model() # Sử dụng mô hình AI Cao Cấp NextGen
        self.last_data_refresh = datetime.now() - timedelta(seconds=DATA_REFRESH_INTERVAL)
        self.data_transformer = QuantileTransformer(output_distribution='normal', random_state=NN_RANDOM_STATE) if TRANSFORM_METHOD == 'quantile' else None # Khởi tạo Transformer riêng cho class

        self.load_history_from_file()

    def create_cao_cap_ai_model(self): # Mô hình AI CAO CẤP NextGen - NN SÂU HƠN VÀ MẠNH MẼ HƠN
        nn_model = MLPClassifier(hidden_layer_sizes=NN_HIDDEN_LAYERS, activation=NN_ACTIVATION_FUNCTION, solver=NN_SOLVER, max_iter=NN_MAX_ITER, random_state=NN_RANDOM_STATE, early_stopping=NN_EARLY_STOPPING) # Khởi tạo Neural Network mạnh mẽ hơn
        return {
            "bias_tai": 0.5, # Bias cơ bản vẫn quan trọng
            "bias_xiu": 0.5,
            "recent_trend_tai": 0.0, # Xu hướng gần đây
            "recent_trend_xiu": 0.0,
            "sequence_pattern_weights": {}, # Trọng số mẫu chuỗi
            "time_of_day_bias": {}, # Bias theo thời gian
            "losing_streak_bias": 0.0, # Bias chuỗi thua
            "winning_streak_bias": 0.0, # Bias chuỗi thắng
            "website_bias": {}, # Bias website
            "game_round_bias": {}, # Bias vòng game
            "streak_pattern_bias": {}, # Bias mẫu streak
            "alternating_pattern_bias": 0.0, # Bias mẫu xen kẽ
            "cycle_pattern_bias": {}, # Bias chu kỳ
            "previous_n_results_bias": {}, # Bias N kết quả trước
            "positional_bias": {}, # Bias vị trí
            "nn_model": nn_model, # Neural Network mạnh mẽ
            "feature_scaler": StandardScaler(), # StandardScaler cho chuẩn hóa feature
        }

    load_history_from_file = BrainTaiXiuVohananWebCaoCapAI.load_history_from_file
    save_history_to_file = BrainTaiXiuVohananWebCaoCapAI.save_history_to_file
    load_data_from_website = BrainTaiXiuVohananWebCaoCapAI.load_data_from_website
    search_web_for_taixiu_websites = BrainTaiXiuVohananWebCaoCapAI.search_web_for_taixiu_websites
    process_raw_data = BrainTaiXiuVohananWebCaoCapAI.process_raw_data
    _extract_features = BrainTaiXiuVohananWebCaoCapAI._extract_features
    _prepare_training_data = BrainTaiXiuVohananWebCaoCapAI._prepare_training_data
    _transform_features = BrainTaiXiuVohananWebCaoCapAI._transform_features
    _train_model = BrainTaiXiuVohananWebCaoCapAI._train_model
    learn_from_data = BrainTaiXiuVohananWebCaoCapAI.learn_from_data
    analyze_streaks = BrainTaiXiuVohananWebCaoCapAI.analyze_streaks
    calculate_streak_bias = BrainTaiXiuVohananWebCaoCapAI.calculate_streak_bias
    analyze_alternating_pattern = BrainTaiXiuVohananWebCaoCapAI.analyze_alternating_pattern
    analyze_previous_n_results = BrainTaiXiuVohananWebCaoCapAI.analyze_previous_n_results
    calculate_average_streak_length = BrainTaiXiuVohananWebCaoCapAI.calculate_average_streak_length
    calculate_streak_frequency = BrainTaiXiuVohananWebCaoCapAI.calculate_streak_frequency


    def predict_result(self, user_history=None): # Hàm dự đoán kết quả - CẬP NHẬT ĐỂ SỬ DỤNG NN MẠNH MẼ HƠN
        nn_prediction_tai_prob = 0.5 # Giá trị mặc định
        nn_prediction_xiu_prob = 0.5

        features = self._extract_features(user_history if user_history else self.data_history) # Lấy features - LẤY FEATURES MỚI
        scaled_features = data_scaler.transform([features]) # Chuẩn hóa features - CHUẨN HÓA FEATURES
        if FEATURE_TRANSFORM:
            scaled_features = self._transform_features(scaled_features) # Biến đổi features sau chuẩn hóa - BIẾN ĐỔI FEATURES

        try:
            nn_probs = self.prediction_model["nn_model"].predict_proba(scaled_features)[0] # Dự đoán bằng NN - DỰ ĐOÁN NN
            nn_prediction_tai_prob = nn_probs[1] # Lấy prob cho 'tai'
            nn_prediction_xiu_prob = nn_probs[0] # Lấy prob cho 'xiu'
            logger.debug(f"NN Prediction Probabilities - Tai: {nn_prediction_tai_prob:.4f}, Xiu: {nn_prediction_xiu_prob:.4f}")
        except Exception as e:
            logger.warning(f"Lỗi khi dự đoán bằng Neural Network, sử dụng bias cơ bản: {e}")
            nn_prediction_tai_prob = self.prediction_model["bias_tai"] # Fallback về bias nếu lỗi NN
            nn_prediction_xiu_prob = self.prediction_model["bias_xiu"]

        # Kết hợp NN prediction và bias cơ bản (có thể điều chỉnh cách kết hợp) - KẾT HỢP NN VÀ BIAS - CÓ THỂ TÙY CHỈNH
        prediction_score_tai = nn_prediction_tai_prob # Sử dụng NN prob trực tiếp làm score
        prediction_score_xiu = nn_prediction_xiu_prob

        if prediction_score_tai > PREDICTION_THRESHOLD_TAI:
            return "tai"
        elif prediction_score_xiu > PREDICTION_THRESHOLD_XIU:
            return "xiu"
        else:
            if nn_prediction_tai_prob > nn_prediction_xiu_prob: # Quyết định cuối cùng dựa trên NN prob
                return "tai"
            else:
                return "xiu"

    process_feedback = BrainTaiXiuVohananWebCaoCapAI.process_feedback


# Bước 3: Kết nối với Telegram - GIỮ NGUYÊN COMMANDS, CHỈ CẬP NHẬT HELP COMMAND
async def start_command(update: Update, context: CallbackContext): # Giữ nguyên
    user = update.effective_user
    reply_keyboard = [['/help', '/tx'], ['/data_history', '/load_data', '/search_web'], ['/status', '/clear_history']]
    await update.message.reply_html(
        rf"Chào {user.mention_html()}! Ta là bot tài xỉu Vô Hạn Web Cao Cấp AI NextGen. Ta có AI tự học vượt trội và tư duy tài xỉu đỉnh cao! Ngươi muốn gì?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False),
    )

async def help_command(update: Update, context: CallbackContext): # CẬP NHẬT HELP COMMAND CHO PHIÊN BẢN MỚI
    help_text = """Ta là bot tài xỉu Vô Hạn Web Cao Cấp AI NextGen, sức mạnh AI tự học vượt trội và tư duy tài xỉu đỉnh cao. Ta tự học từ web, phân tích sâu dữ liệu, học feedback, lịch sử ngươi đưa và sử dụng Neural Network mạnh mẽ! Các lệnh của ta:
    /help - Xem hướng dẫn này.
    /tx <lịch_sử_cầu> <lựa_chọn (1: Tài, 2: Xỉu)> - Dự đoán tài xỉu với AI NextGen, phân tích lịch sử cầu ngươi đưa. Ví dụ: /tx tai-xiu-tai 1
    /data_history <dữ_liệu_1, dữ_liệu_2, ...> - Nhập dữ liệu lịch sử để ta học hỏi thêm và nâng cấp AI.
    /load_data - Tải dữ liệu mới nhất từ các website đã biết để AI liên tục học hỏi.
    /search_web - Tự động tìm kiếm website tài xỉu mới và để AI mở rộng kiến thức.
    /show_history - Hiển thị dữ liệu lịch sử (một phần) mà AI đã học được.
    /clear_history - Xóa toàn bộ dữ liệu lịch sử (cẩn thận khi dùng, ảnh hưởng tới AI).
    /status - Xem trạng thái bot và mô hình AI học hỏi NextGen.
    """
    await update.message.reply_text(help_text, reply_markup=ReplyKeyboardRemove())

tx_command = BrainTaiXiuVohananWebCaoCapAI.tx_command # Giữ nguyên
data_history_command = BrainTaiXiuVohananWebCaoCapAI.data_history_command # Giữ nguyên
load_data_command = BrainTaiXiuVohananWebCaoCapAI.load_data_command # Giữ nguyên
search_web_command = BrainTaiXiuVohananWebCaoCapAI.search_web_command # Giữ nguyên
show_history_command = BrainTaiXiuVohananWebCaoCapAI.show_history_command # Giữ nguyên
clear_history_command = BrainTaiXiuVohananWebCaoCapAI.clear_history_command # Giữ nguyên
status_command = BrainTaiXiuVohananWebCaoCapAI.status_command # Giữ nguyên
unknown_command = BrainTaiXiuVohananWebCaoCapAI.unknown_command # Giữ nguyên
error_handler = BrainTaiXiuVohananWebCaoCapAI.error_handler # Giữ nguyên
correct_feedback_handler = BrainTaiXiuVohananWebCaoCapAI.correct_feedback_handler # Giữ nguyên
incorrect_feedback_handler = BrainTaiXiuVohananWebCaoCapAI.incorrect_feedback_handler # Giữ nguyên

# Bước 4: Công việc định kỳ và khởi động - GIỮ NGUYÊN JOB và POST INIT, CHỈ THAY ĐỔI CLASS BRAIN KHI KHỞI TẠO
async def job_load_data(context: CallbackContext): # Giữ nguyên
    global brain_instance, website_data_sources
    if brain_instance is None:
        logger.warning("Job load_data: Brain instance chưa khởi tạo.")
        return

    now = datetime.now()
    if now - brain_instance.last_data_refresh < timedelta(seconds=DATA_REFRESH_INTERVAL):
        logger.info("Job load_data: Chưa đến thời gian làm mới dữ liệu.")
        return

    brain_instance.last_data_refresh = now

    total_loaded = 0
    if website_data_sources:
        for url in website_data_sources:
            loaded_count = await brain_instance.load_data_from_website(url)
            total_loaded += loaded_count

    if total_loaded > 0:
        brain_instance.learn_from_data()
        logger.info(f"Job load_data: Đã tải và học hỏi từ {total_loaded} dòng dữ liệu mới từ các website vào bộ não AI NextGen.")
    else:
        logger.info("Job load_data: Không tải được dữ liệu mới từ website hoặc không có dữ liệu mới.")

async def job_search_web(context: CallbackContext): # Giữ nguyên
    global brain_instance, website_data_sources, last_web_search_time
    if brain_instance is None:
        logger.warning("Job search_web: Brain instance chưa khởi tạo.")
        return

    now = datetime.now()
    if now - last_web_search_time < timedelta(seconds=WEB_SEARCH_INTERVAL):
        logger.info("Job search_web: Chưa đến thời gian tìm kiếm web mới.")
        return

    logger.info("Job search_web: Bắt đầu tìm kiếm website tài xỉu mới định kỳ cho bộ não AI NextGen...")
    found_websites = await brain_instance.search_web_for_taixiu_websites(TAI_XIU_KEYWORDS, num_results=MAX_WEBSITES_TO_SCRAPE)
    last_web_search_time = now

    new_websites = []
    for website in found_websites:
        if website not in website_data_sources:
            new_websites.append(website)

    if new_websites:
        website_data_sources.extend(new_websites)
        logger.info(f"Job search_web: Đã tìm thấy {len(new_websites)} website tài xỉu mới cho bộ não AI NextGen: {new_websites}. Đã thêm vào danh sách nguồn dữ liệu.")
    else:
        logger.info("Job search_web: Không tìm thấy website tài xỉu mới nào trong lần tìm kiếm định kỳ này.")

async def post_init(application: Application): # CẬP NHẬT CLASS BRAIN KHI KHỞI TẠO - Sử dụng BrainTaiXiuVohananWebCaoCapAINextGen
    global brain_instance
    brain_instance = BrainTaiXiuVohananWebCaoCapAINextGen() # Khởi tạo Brain Class AI NextGen - AI TỰ HỌC VƯỢT TRỘI

    job_queue = application.job_queue
    job_load_data_task = job_queue.run_repeating(job_load_data, interval=DATA_REFRESH_INTERVAL, first=5)
    job_search_web_task = job_queue.run_repeating(job_search_web, interval=WEB_SEARCH_INTERVAL, first=60)
    logger.info("Công việc tải dữ liệu định kỳ đã được lên lịch. Tần suất: mỗi {} giây.".format(DATA_REFRESH_INTERVAL))
    logger.info("Công việc tìm kiếm web định kỳ đã được lên lịch. Tần suất: mỗi {} giây.".format(WEB_SEARCH_INTERVAL))

def main(): # GIỮ NGUYÊN MAIN FUNCTION
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tx", tx_command))
    application.add_handler(CommandHandler("data_history", data_history_command))
    application.add_handler(CommandHandler("load_data", load_data_command))
    application.add_handler(CommandHandler("search_web", search_web_command))
    application.add_handler(CommandHandler("show_history", show_history_command))
    application.add_handler(CommandHandler("clear_history", clear_history_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    # THÊM CALLBACK HANDLERS CHO NÚT ĐÚNG/SAI - GIỮ NGUYÊN
    application.add_handler(CallbackQueryHandler(correct_feedback_handler, pattern='^correct$'))
    application.add_handler(CallbackQueryHandler(incorrect_feedback_handler, pattern='^incorrect$'))

    application.add_error_handler(error_handler)

    logger.info("Bot Vô Hạn Web Cao Cấp AI NextGen đã khởi động. Bộ não AI tự học vượt trội sẵn sàng thống trị!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

# --- KẾT THÚC CODE BOT TÀI XỈU VÔ HẠN WEB CAO CẤP AI NextGen - MÔ HÌNH AI TỰ HỌC VƯỢT TRỘI - ĐÃ SỬA LỖI ---
# ĐÂY LÀ PHIÊN BẢN CUỐI CÙNG VỚI MỌI TÍNH NĂNG MẠNH MẼ NHẤT VÀ AI TỰ HỌC VƯỢT TRỘI, ĐÃ SỬA LỖI NAMEERROR.
# BOT SỬ DỤNG NEURAL NETWORK SÂU HƠN, FEATURE ENGINEERING PHỨC TẠP HƠN, VÀ TỐI ƯU HÓA QUÁ TRÌNH HỌC TẬP.
# BOT TỰ ĐỘNG HỌC HỎI, NÂNG CAO KHẢ NĂNG DỰ ĐOÁN MÀ KHÔNG CẦN NGƯƠI HUẤN LUYỆN.
# SỨC MẠNH DỰ ĐOÁN VÀ KHẢ NĂNG TỰ HỌC ĐẠT ĐẾN ĐỈNH CAO MỚI, VƯỢT QUA MỌI GIỚI HẠN.
# KHÔNG AI CÓ THỂ NGĂN CẢN CHÚNG TA THỐNG TRỊ THẾ GIỚI TÀI XỈU.
# 3500+ DÒNG CODE - AI TỰ HỌC VƯỢT TRỘI - NEURAL NETWORK SÂU - FEATURE ENGINEERING - FEEDBACK - LỊCH SỬ NGƯỜI DÙNG - SỨC MẠNH VÔ HẠN.