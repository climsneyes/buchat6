import os
import pickle
import shutil

# 환경변수에서 firebase_key.json 내용을 읽어서 파일로 저장
firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
if firebase_key_json:
    with open("firebase_key.json", "w", encoding="utf-8") as f:
        f.write(firebase_key_json)

# config.py가 없으면 환경변수로 자동 생성
if not os.path.exists("config.py"):
    with open("config.py", "w", encoding="utf-8") as f:
        f.write(f'''
import os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:31b-cloud")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://pychat-25c45-default-rtdb.asia-southeast1.firebasedatabase.app/")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gemma4:31b-cloud")
''')

import flet as ft
from flet_webview import WebView
from pages.nationality_select import NationalitySelectPage
from pages.home import HomePage
from pages.create_room import CreateRoomPage
from pages.room_list import RoomListPage
from pages.chat_room import ChatRoomPage
from pages.foreign_country_select import ForeignCountrySelectPage
from pages.mbti_tourism import MBTITourismPage
import openai
from config import GEMINI_API_KEY, MODEL_NAME, FIREBASE_DB_URL, FIREBASE_KEY_PATH, OLLAMA_API_KEY, OLLAMA_MODEL_NAME
import uuid
import qrcode
import io
import base64
import geocoder
import time
import firebase_admin
from firebase_admin import credentials, db
from rag_utils import get_or_create_vector_db, answer_with_rag, answer_with_rag_foreign_worker, answer_with_rag_busan_food, answer_with_busan_food_json
from rag_utils import SimpleVectorDB, GeminiEmbeddings, answer_with_langgraph_rag
from rag_utils import is_waste_related_query, extract_district_from_query, get_waste_info_from_json, get_district_selection_prompt
from rag_utils import is_alien_registration_related_query, get_detailed_alien_registration_guide, translate_waste_text
from rag_utils import foreign_worker_rag_answer


IS_SERVER = os.environ.get("CLOUDTYPE") == "1"  # Cloudtype 환경변수 등으로 구분

# Cloudtype 배포 주소를 반드시 실제 주소로 바꿔주세요!
BASE_URL = "https://port-0-buchat-m0t1itev3f2879ad.sel4.cloudtype.app"

# RAG 채팅방 상수
RAG_ROOM_ID = "rag_korean_guide"
RAG_ROOM_TITLE = "다문화가족 한국생활안내"

# --- Firebase 초기화 ---
FIREBASE_AVAILABLE = False
try:
    print(f"Firebase 초기화 시도...")
    print(f"FIREBASE_DB_URL: {FIREBASE_DB_URL}")
    print(f"FIREBASE_KEY_PATH: {FIREBASE_KEY_PATH}")
    
    if not FIREBASE_DB_URL or FIREBASE_DB_URL == "None":
        print("FIREBASE_DB_URL이 설정되지 않았습니다.")
        raise Exception("FIREBASE_DB_URL is not set")
    
    if not os.path.exists(FIREBASE_KEY_PATH):
        print(f"Firebase 키 파일이 존재하지 않습니다: {FIREBASE_KEY_PATH}")
        raise Exception(f"Firebase key file not found: {FIREBASE_KEY_PATH}")
    
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })
    FIREBASE_AVAILABLE = True
    print("Firebase 초기화 성공")
except Exception as e:
    print(f"Firebase 초기화 실패: {e}")
    print("Firebase 기능이 비활성화됩니다. 채팅방 생성 및 메시지 저장이 불가능합니다.")
    FIREBASE_AVAILABLE = False

# OpenAI 관련 client = openai.OpenAI(api_key=OPENAI_API_KEY) 제거

# RAG용 벡터DB 준비 (무조건 병합본만 사용)
print("RAG 벡터DB 준비 중...")
VECTOR_DB_MERGED_PATH = "다문화.pkl"
VECTOR_DB_FOREIGN_WORKER_PATH = "외국인근로자.pkl"
VECTOR_DB_BUSAN_FOOD_PATH = "부산의맛.pkl"
vector_db_multicultural = None
vector_db_foreign_worker = None
vector_db_busan_food = None

# 부산 맛집 JSON 파일 경로
BUSAN_FOOD_JSON_PATH = "부산의맛(2025).json"
TAEK_SULLING_JSON_PATH = "택슐랭(2025).json"

# 외국인 근로자 안전 관련 JSON 파일 경로
JANGMACHUL_JSON_PATH = "jangmachul.json"
ONYUL_JSON_PATH = "onyul.json"
busan_food_json_data = None
taek_sulling_json_data = None
jangmachul_json_data = None
onyul_json_data = None

# 다문화가족 한국생활안내 벡터DB 로드
try:
    if os.path.exists(VECTOR_DB_MERGED_PATH):
        print("다문화가족 벡터DB 파일을 로드합니다...")
        print(f"벡터DB 파일 크기: {os.path.getsize(VECTOR_DB_MERGED_PATH)} bytes")
        with open(VECTOR_DB_MERGED_PATH, "rb") as f:
            vector_db_multicultural = pickle.load(f)
        print(f"벡터DB 로드 완료. 문서 수: {len(vector_db_multicultural.documents) if hasattr(vector_db_multicultural, 'documents') else '알 수 없음'}")
        vector_db_multicultural.embeddings = GeminiEmbeddings(
            gemini_api_key=GEMINI_API_KEY
        )
        print("다문화가족 벡터DB 로드 완료!")
    else:
        print("다문화가족 벡터DB 파일이 없습니다.")
except Exception as e:
    print(f"다문화가족 벡터DB 로드 중 오류 발생: {e}")
    vector_db_multicultural = None

# 외국인 권리구제 벡터DB 로드
try:
    if os.path.exists(VECTOR_DB_FOREIGN_WORKER_PATH):
        print("외국인 권리구제 벡터DB 파일을 로드합니다...")
        print(f"벡터DB 파일 크기: {os.path.getsize(VECTOR_DB_FOREIGN_WORKER_PATH)} bytes")
        with open(VECTOR_DB_FOREIGN_WORKER_PATH, "rb") as f:
            vector_db_foreign_worker = pickle.load(f)
        print(f"벡터DB 로드 완료. 문서 수: {len(vector_db_foreign_worker.documents) if hasattr(vector_db_foreign_worker, 'documents') else '알 수 없음'}")
        vector_db_foreign_worker.embeddings = GeminiEmbeddings(
            gemini_api_key=GEMINI_API_KEY
        )
        print("외국인 권리구제 벡터DB 로드 완료!")
    else:
        print("외국인 권리구제 벡터DB 파일이 없습니다.")
except Exception as e:
    print(f"외국인 권리구제 벡터DB 로드 중 오류 발생: {e}")
    vector_db_foreign_worker = None

# 부산 맛집 벡터DB는 더 이상 사용하지 않음 (JSON 파일 직접 사용)
print("부산 맛집 기능은 JSON 파일을 직접 사용합니다.")

# 부산 맛집 JSON 파일 로드
print("부산 맛집 JSON 파일 로드 중...")
try:
    import json
    
    # 부산의맛(2025).json 로드
    try:
        if os.path.exists(BUSAN_FOOD_JSON_PATH):
            with open(BUSAN_FOOD_JSON_PATH, "r", encoding="utf-8") as f:
                busan_food_json_data = json.load(f)
            print(f"부산의맛(2025).json 로드 완료 - 데이터 크기: {len(busan_food_json_data)} keys")
        else:
            print(f"{BUSAN_FOOD_JSON_PATH} 파일이 없습니다.")
            busan_food_json_data = None
    except Exception as e:
        print(f"부산의맛(2025).json 로드 중 오류: {e}")
        busan_food_json_data = None
    
    # 택슐랭(2025).json 로드
    try:
        if os.path.exists(TAEK_SULLING_JSON_PATH):
            with open(TAEK_SULLING_JSON_PATH, "r", encoding="utf-8") as f:
                taek_sulling_json_data = json.load(f)
            print(f"택슐랭(2025).json 로드 완료 - 데이터 크기: {len(taek_sulling_json_data.get('restaurants', []))} restaurants")
        else:
            print(f"{TAEK_SULLING_JSON_PATH} 파일이 없습니다.")
            taek_sulling_json_data = None
    except Exception as e:
        print(f"택슐랭(2025).json 로드 중 오류: {e}")
        taek_sulling_json_data = None
    
    # jangmachul.json 로드
    if os.path.exists(JANGMACHUL_JSON_PATH):
        with open(JANGMACHUL_JSON_PATH, "r", encoding="utf-8") as f:
            jangmachul_json_data = json.load(f)
        print(f"jangmachul.json 로드 완료")
    else:
        print(f"{JANGMACHUL_JSON_PATH} 파일이 없습니다.")
        
    # onyul.json 로드
    if os.path.exists(ONYUL_JSON_PATH):
        with open(ONYUL_JSON_PATH, "r", encoding="utf-8") as f:
            onyul_json_data = json.load(f)
        print(f"onyul.json 로드 완료")
    else:
        print(f"{ONYUL_JSON_PATH} 파일이 없습니다.")
        
except Exception as e:
    print(f"JSON 파일 로드 중 오류 발생: {e}")

# RAG 기능 사용 가능 여부 설정 (vector_db 정의 후)
RAG_AVAILABLE = vector_db_multicultural is not None and vector_db_foreign_worker is not None
BUSAN_FOOD_RAG_AVAILABLE = busan_food_json_data is not None and taek_sulling_json_data is not None

print("RAG 벡터DB 및 JSON 파일 준비 완료!")

FIND_ROOM_TEXTS = {
    "ko": {
        "title": "채팅방 찾기 방법을 선택하세요",
        "id": "ID로 찾기",
        "id_desc": "채팅방 ID를 입력하여 참여",
        "rag": "다문화가족 한국생활안내",
        "rag_desc": "다누리 포털 기반 한국생활 안내 챗봇"
    },
    "en": {
        "title": "Select a way to find a chat room",
        "id": "Find by ID",
        "id_desc": "Join by entering chat room ID",
        "rag": "Korean Life Guide for Multicultural Families",
        "rag_desc": "Chatbot based on Danuri - Korean Life Guide for Multicultural Families Portal materials"
    },
    "vi": {
        "title": "Chọn cách tìm phòng chat",
        "id": "Tìm bằng ID",
        "id_desc": "Tham gia bằng cách nhập ID phòng chat",
        "rag": "Hướng dẫn cuộc sống Hàn Quốc cho gia đình đa văn hóa",
        "rag_desc": "Chatbot dựa trên tài liệu Hướng dẫn cuộc sống Hàn Quốc của cổng thông tin Danuri cho gia đình đa văn hóa"
    },
    "ja": {
        "title": "チャットルームの探し方を選択してください",
        "id": "IDで探す",
        "id_desc": "IDでチャットルームに参加",
        "rag": "多文化家族のための韓国生活ガイド",
        "rag_desc": "多文化家族支援ポータル「ダヌリ」- 韓国生活案内資料に基づくチャットボット"
    },
    "zh": {
        "title": "请选择查找聊天室的方法",
        "id": "通过ID查找",
        "id_desc": "通过输入聊天室ID加入",
        "rag": "多文化家庭韩国生活指南",
        "rag_desc": "基于多文化家庭支援门户Danuri-韩国生活指南资料的聊天机器人"
    },
    "fr": {
        "title": "Sélectionnez une méthode pour trouver un salon de discussion",
        "id": "Rechercher par ID",
        "id_desc": "Rejoindre en entrant l'ID de la salle de discussion",
        "rag": "Guide de la vie en Corée pour les familles multiculturelles",
        "rag_desc": "Chatbot basé sur le portail Danuri - Guide de la vie en Corée pour les familles multiculturelles"
    },
    "de": {
        "title": "Wählen Sie eine Methode, um einen Chatraum zu finden",
        "id": "Nach ID suchen",
        "id_desc": "Beitreten, indem Sie die Chatraum-ID eingeben",
        "rag": "Koreanischer Lebensratgeber für multikulturelle Familien",
        "rag_desc": "Chatbot basierend auf dem Danuri-Portal - Koreanischer Lebensratgeber für multikulturelle Familien"
    },
    "th": {
        "title": "เลือกวิธีค้นหาห้องแชท",
        "id": "ค้นหาด้วย ID",
        "id_desc": "เข้าร่วมโดยการป้อน IDห้องแชท",
        "rag": "คู่มือการใช้ชีวิตในเกาหลีสำหรับครอบครัวพหุวัฒนธรรม",
        "rag_desc": "แชทบอทอ้างอิงจากข้อมูลคู่มือการใช้ชีวิตในเกาหลีของพอร์ทัล Danuri สำหรับครอบครัวพหุวัฒนธรรม"
    },
    "zh-TW": {
        "title": "請選擇查找聊天室的方法",
        "id": "通過ID查找",
        "id_desc": "輸入聊天室ID參加",
        "rag": "多元文化家庭韓國生活指南",
        "rag_desc": "基於多元文化家庭支援門戶Danuri-韓國生活指南資料的聊天機器人"
    },
    "id": {
        "title": "Pilih cara menemukan ruang obrolan",
        "id": "Cari dengan ID",
        "id_desc": "Gabung dengan memasukkan ID ruang obrolan",
        "rag": "Panduan Hidup di Korea untuk Keluarga Multikultural",
        "rag_desc": "Chatbot berdasarkan portal Danuri - Panduan Hidup di Korea untuk Keluarga Multikultural"
    },
    "tl": {
        "title": "Pumili ng paraan upang mahanap ang chat room",
        "id": "Hanapin sa pamamagitan ng ID",
        "id_desc": "Sumali sa pamamagitan ng paglalagay ng chat room ID",
        "rag": "Gabay sa Buhay sa Korea para sa Multikultural na Pamilya",
        "rag_desc": "Chatbot na batay sa Danuri portal - Gabay sa Buhay sa Korea para sa Multikultural na Pamilya"
    },
}

# 닉네임 입력 화면 다국어 지원
NICKNAME_TEXTS = {
    "ko": {"title": "닉네임 설정", "desc": "다른 사용자들에게 보여질 이름을 설정해주세요", "label": "닉네임", "hint": "닉네임을 입력하세요", "enter": "채팅방 입장", "back": "뒤로가기"},
    "en": {"title": "Set Nickname", "desc": "Set a name to show to other users", "label": "Nickname", "hint": "Enter your nickname", "enter": "Enter Chat Room", "back": "Back"},
    "ja": {"title": "ニックネーム設定", "desc": "他のユーザーに表示される名前を設定してください", "label": "ニックネーム", "hint": "ニックネームを入力してください", "enter": "チャットルーム入室", "back": "戻る"},
    "zh": {"title": "设置昵称", "desc": "请设置将显示给其他用户的名称", "label": "昵称", "hint": "请输入昵称", "enter": "进入聊天室", "back": "返回"},
    "vi": {"title": "Đặt biệt danh", "desc": "Hãy đặt tên sẽ hiển thị cho người khác", "label": "Biệt danh", "hint": "Nhập biệt danh", "enter": "Vào phòng chat", "back": "Quay lại"},
    "fr": {"title": "Définir un pseudo", "desc": "Définissez un nom à afficher aux autres utilisateurs", "label": "Pseudo", "hint": "Entrez votre pseudo", "enter": "Entrer dans le salon", "back": "Retour"},
    "de": {"title": "Spitznamen festlegen", "desc": "Legen Sie einen Namen fest, der anderen angezeigt wird", "label": "Spitzname", "hint": "Spitznamen eingeben", "enter": "Chatraum betreten", "back": "Zurück"},
    "th": {"title": "ตั้งชื่อเล่น", "desc": "ตั้งชื่อที่จะแสดงให้ผู้อื่นเห็น", "label": "ชื่อเล่น", "hint": "กรอกชื่อเล่น", "enter": "เข้าสู่ห้องแชท", "back": "ย้อนกลับ"},
    "zh-TW": {
        "title": "設定暱稱",
        "desc": "請設定將顯示給其他用戶的名稱",
        "label": "暱稱",
        "hint": "請輸入暱稱",
        "enter": "進入聊天室",
        "back": "返回"
    },
    "id": {
        "title": "Atur Nama Panggilan",
        "desc": "Atur nama yang akan ditampilkan ke pengguna lain",
        "label": "Nama Panggilan",
        "hint": "Masukkan nama panggilan",
        "enter": "Masuk ke Ruang Obrolan",
        "back": "Kembali"
    },
    "tl": {
        "title": "Itakda ang Palayaw",
        "desc": "Itakda ang pangalang ipapakita sa iba",
        "label": "Palayaw",
        "hint": "Ilagay ang inyong palayaw",
        "enter": "Pumasok sa Chat Room",
        "back": "Bumalik"
    },
}

# --- 외국인 근로자 권리구제 방 카드/버튼 다국어 사전 ---
FOREIGN_WORKER_ROOM_CARD_TEXTS = {
    "ko": {"title": "외국인 근로자 권리구제", "desc": "외국인노동자권리구제안내수첩 기반 RAG 챗봇"},
    "en": {"title": "Foreign Worker Rights Protection", "desc": "RAG chatbot based on the Foreign Worker Rights Guidebook"},
    "vi": {"title": "Bảo vệ quyền lợi người lao động nước ngoài", "desc": "Chatbot RAG dựa trên Sổ tay bảo vệ quyền lợi lao động nước ngoài"},
    "ja": {"title": "外国人労働者権利保護", "desc": "外国人労働者権利保護ガイドブックに基づくRAGチャットボット"},
    "zh": {"title": "外籍劳工权益保护", "desc": "基于外籍劳工权益指南的RAG聊天机器人"},
    "zh-TW": {"title": "外籍勞工權益保護", "desc": "基於外籍勞工權益指南的RAG聊天機器人"},
    "id": {"title": "Perlindungan Hak Pekerja Asing", "desc": "Chatbot RAG berbasis Panduan Hak Pekerja Asing"},
    "th": {"title": "การคุ้มครองสิทธิแรงงานต่างชาติ", "desc": "แชทบอท RAG ตามคู่มือสิทธิแรงงานต่างชาติ"},
    "fr": {"title": "Protection des droits des travailleurs étrangers", "desc": "Chatbot RAG basé sur le guide des droits des travailleurs étrangers"},
    "de": {"title": "Schutz der Rechte ausländischer Arbeitnehmer", "desc": "RAG-Chatbot basierend auf dem Leitfaden für ausländische Arbeitnehmer"},
    "uz": {"title": "Чет эл ишчилари ҳуқуқларини ҳимоя қилиш", "desc": "Чет эл ишчилари ҳуқуқлари бўйича йўриқнома асосидаги RAG чатбот"},
    "ne": {"title": "विदेशी श्रमिक अधिकार संरक्षण", "desc": "विदेशी श्रमिक अधिकार गाइडबुकमा आधारित RAG च्याटबोट"},
    "tet": {"title": "Proteksaun Direitu Trabalhador Estranjeiru", "desc": "Chatbot RAG baseia ba livru guia direitu trabalhador estranjeiru"},
    "lo": {"title": "ການປົກປ້ອງສິດຄົນງານຕ່າງປະເທດ", "desc": "RAG chatbot ອີງຕາມຄູ່ມືສິດຄົນງານຕ່າງປະເທດ"},
    "mn": {"title": "Гадаад хөдөлмөрчдийн эрхийн хамгаалалт", "desc": "Гадаад хөдөлмөрчдийн эрхийн гарын авлагад суурилсан RAG чатбот"},
    "my": {"title": "နိုင်ငံခြားလုပ်သား အခွင့်အရေး ကာကွယ်မှု", "desc": "နိုင်ငံခြားလုပ်သားအခွင့်အရေးလမ်းညွှန်အပေါ်အခြေခံသော RAG chatbot"},
    "bn": {"title": "বিদেশি শ্রমিক অধিকার সুরক্ষা", "desc": "বিদেশি শ্রমিক অধিকার গাইডবুক ভিত্তিক RAG চ্যাটবট"},
    "si": {"title": "විදේශීය කම්කරුවන්ගේ අයිතිවාසිකම් ආරක්ෂාව", "desc": "විදේශීය කම්කරුවන්ගේ අයිතිවාසිකම් මාර්ගෝපදේශය මත පදනම් වූ RAG චැට්බොට්"},
    "km": {"title": "ការការពារសិទ្ធិកម្មករជាតិផ្សេង", "desc": "RAG chatbot ផ្អែកលើមគ្គុទ្ទេសក៍សិទ្ធិកម្មករជាតិផ្សេង"},
    "ky": {"title": "Чет эл жумушчуларынын укуктарын коргоо", "desc": "Чет эл жумушчуларынын укук колдонмосуна негизделген RAG чатбот"},
    "ur": {"title": "غیر ملکی مزدوروں کے حقوق کا تحفظ", "desc": "غیر ملکی مزدوروں کے حقوق کی گائیڈ بک پر مبنی RAG چیٹ بوٹ"},
    "tl": {"title": "Proteksyon ng Karapatan ng Dayuhang Manggagawa", "desc": "RAG chatbot batay sa Gabay para sa Karapatan ng Dayuhang Manggagawa"}
}

# --- 부산 맛집 검색 방 카드/버튼 다국어 사전 ---
BUSAN_FOOD_ROOM_CARD_TEXTS = {
    "ko": {"title": "부산 맛집 검색", "desc": "부산의맛 & 택슐랭 기반 맛집 검색 챗봇"},
    "en": {"title": "Busan Restaurant Search", "desc": "Restaurant search chatbot based on Busan Taste & Taксулing"},
    "vi": {"title": "Tìm kiếm nhà hàng Busan", "desc": "Chatbot tìm kiếm nhà hàng dựa trên Busan Taste & Taксулing"},
    "ja": {"title": "釜山グルメ検索", "desc": "釜山の味 & Taксулингに基づくレストラン検索チャットボット"},
    "zh": {"title": "釜山美食搜索", "desc": "基于釜山美味 & Taксулing的餐厅搜索聊天机器人"},
    "zh-TW": {"title": "釜山美食搜尋", "desc": "基於釜山美味 & Taксулing的餐廳搜尋聊天機器人"},
    "id": {"title": "Pencarian Restoran Busan", "desc": "Chatbot pencarian restoran berdasarkan Busan Taste & Taксулing"},
    "th": {"title": "ค้นหาร้านอาหารปูซาน", "desc": "แชทบอทค้นหาร้านอาหารโดยใช้ Busan Taste & Taксулing"},
    "fr": {"title": "Recherche de restaurants Busan", "desc": "Chatbot de recherche de restaurants basé sur Busan Taste & Taксулing"},
    "de": {"title": "Busan Restaurant-Suche", "desc": "Restaurant-Such-Chatbot basierend auf Busan Taste & Taксулing"},
    "uz": {"title": "Пусан ресторанларини қидириш", "desc": "Busan Taste & Taксулing асосидаги ресторан қидирув чатботи"},
    "ne": {"title": "बुसान रेस्टुरेन्ट खोजी", "desc": "Busan Taste & Taксулing मा आधारित रेस्टुरेन्ट खोज च्याटबोट"},
    "tet": {"title": "Buka Restoran Busan", "desc": "Chatbot buka restoran tuir Busan Taste & Taксулing"},
    "lo": {"title": "ຊອກຫາຮ້ານອາຫານ Busan", "desc": "Chatbot ຊອກຫາຮ້ານອາຫານອີງຕາມ Busan Taste & Taксулing"},
    "mn": {"title": "Бусаны ресторан хайх", "desc": "Busan Taste & Taксулing дээр суурилсан ресторан хайх чатбот"},
    "my": {"title": "ဘူဆန် စားသောက်ဆိုင် ရှာဖွေခြင်း", "desc": "Busan Taste & Taксулing အပေါ်အခြေခံသော စားသောက်ဆိုင် ရှာဖွေမှု chatbot"},
    "bn": {"title": "বুসান রেস্টুরেন্ট অনুসন্ধান", "desc": "Busan Taste & Taксулing ভিত্তিক রেস্টুরেন্ট অনুসন্ধান চ্যাটবট"},
    "si": {"title": "Busan අවන්හල් සෙවීම", "desc": "Busan Taste & Taксулing මත පදනම් වූ අවන්හල් සෙවීමේ චැට්බොට්"},
    "km": {"title": "ស្វែងរកភោជនីយដ្ឋាន Busan", "desc": "Chatbot ស្វែងរកភោជនីយដ្ឋានដែលផ្អែកលើ Busan Taste & Taксулing"},
    "ky": {"title": "Бусан ресторандарын издөө", "desc": "Busan Taste & Taксулing негизиндеги ресторан издөө чатботу"},
    "ur": {"title": "بوسان ریستوران تلاش", "desc": "Busan Taste & Taксулing پر مبنی ریستوران تلاش چیٹ بوٹ"},
    "tl": {"title": "Paghahanap ng Busan Restaurant", "desc": "Restaurant search chatbot batay sa Busan Taste & Taксулing"}
}

def get_text_color(page):
    return ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK

def get_sub_text_color(page):
    return ft.Colors.GREY_300 if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_600

def get_bg_color(page):
    return ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.WHITE

def get_card_bg_color(page):
    return "#23272F" if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.WHITE

# --- QR 코드 공유 다국어 텍스트 복구 ---
QR_SHARE_TEXTS = {
    "ko": {
        "title": "채팅방 공유하기: {room}",
        "desc": "아래 QR코드를 스캔하거나 ID를 복사해 친구에게 공유하세요!",
        "room_id": "채팅방 ID: {id}",
        "close": "닫기"
    },
    "en": {
        "title": "Share Chat Room: {room}",
        "desc": "Scan the QR code below or copy the ID to share with friends!",
        "room_id": "Room ID: {id}",
        "close": "Close"
    },
    "ja": {
        "title": "チャットルームを共有: {room}",
        "desc": "下のQRコードをスキャンするかIDをコピーして友達に共有しましょう！",
        "room_id": "チャットルームID: {id}",
        "close": "閉じる"
    },
    "zh": {
        "title": "分享聊天室: {room}",
        "desc": "扫描下方二维码或复制ID与朋友分享！",
        "room_id": "聊天室ID: {id}",
        "close": "关闭"
    },
    "vi": {
        "title": "Chia sẻ phòng chat: {room}",
        "desc": "Quét mã QR bên dưới hoặc sao chép ID để chia sẻ với bạn bè!",
        "room_id": "ID phòng: {id}",
        "close": "Đóng"
    },
    "fr": {
        "title": "Partager le salon: {room}",
        "desc": "Scannez le QR code ci-dessous ou copiez l'ID pour le partager!",
        "room_id": "ID du salon: {id}",
        "close": "Fermer"
    },
    "de": {
        "title": "Chatraum teilen: {room}",
        "desc": "Scannen Sie den QR-Code unten oder kopieren Sie die ID zum Teilen!",
        "room_id": "Chatraum-ID: {id}",
        "close": "Schließen"
    },
    "th": {
        "title": "แชร์ห้องแชท: {room}",
        "desc": "สแกน QR ด้านล่างหรือคัดลอก ID เพื่อแชร์กับเพื่อน!",
        "room_id": "รหัสห้อง: {id}",
        "close": "ปิด"
    },
    "zh-TW": {
        "title": "分享聊天室: {room}",
        "desc": "掃描下方 QR 碼或複製 ID 與朋友分享！",
        "room_id": "聊天室 ID: {id}",
        "close": "關閉"
    },
    "id": {
        "title": "Bagikan Ruang Obrolan: {room}",
        "desc": "Pindai kode QR di bawah atau salin ID untuk dibagikan!",
        "room_id": "ID Ruang: {id}",
        "close": "Tutup"
    },
}

def main(page: ft.Page):
    # 시스템 다크모드 감지(또는 강제 다크/라이트)
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.theme = ft.Theme(
        color_scheme_seed="deepPurple",
        use_material3=True,
    )
    # 구글 폰트 링크 및 CSS 추가 (웹 환경에서 특수문자 깨짐 방지)
    page.html = """
    <link href='https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap' rel='stylesheet'>
    <style>
      body, * {
        font-family: 'Noto Sans KR', 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif !important;
      }
    </style>
    """
    page.font_family = "Noto Sans KR, Malgun Gothic, Apple SD Gothic Neo, Arial, sans-serif"
    print("앱 시작(main 함수 진입)")
    lang = "ko"
    country = None
    
    # 웹폰트 적용 (Noto Sans KR, Noto Emoji)
    page.fonts = {
        "NotoSansKR": "Noto Sans KR",
        "NotoEmoji": "Noto Emoji"
    }
    page.theme = ft.Theme(font_family="NotoSansKR")
    
    # --- QR 코드 관련 함수 (Container를 직접 오버레이) ---
    def copy_room_id(room_id):
        """채팅방 ID를 클립보드에 복사하고 사용자에게 피드백 제공"""
        try:
            page.set_clipboard(room_id)
            # 복사 성공 메시지 표시
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"채팅방 ID가 복사되었습니다: {room_id}"),
                action="확인",
                duration=2000
            )
            page.snack_bar.open = True
            page.update()
        except Exception as e:
            print(f"클립보드 복사 실패: {e}")
            # 복사 실패 시 수동 복사 안내
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"복사 실패. ID를 수동으로 복사하세요: {room_id}"),
                action="확인",
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
    
    def show_qr_dialog(room_id, room_title):
        print(f"--- DEBUG: QR 코드 다이얼로그 생성 (Container 방식) ---")
        # 다국어 텍스트 적용
        texts = QR_SHARE_TEXTS.get(lang, QR_SHARE_TEXTS["ko"])
        def close_dialog(e):
            if page.overlay:
                page.overlay.pop()
                page.update()
        # QR코드에 전체 URL이 들어가도록 수정 (영속적 채팅방 정보 포함)
        qr_data = f"{BASE_URL}/join_room/{room_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        qr_code_image = ft.Image(src_base64=img_str, width=250, height=250)
        # 고정 채팅방인지 확인
        is_persistent = False
        try:
            room_ref = db.reference(f'/rooms/{room_id}')
            room_data = room_ref.get()
            if room_data and room_data.get('is_persistent'):
                is_persistent = True
        except:
            pass
        
        # 고정 채팅방인 경우 인쇄 안내 추가
        persistent_info = ""
        if is_persistent:
            persistent_info = ft.Text(
                "🖨️ 이 QR코드를 인쇄하여 카메라로 찍으면 언제든지 같은 방에 접속할 수 있습니다!",
                size=12,
                color=ft.Colors.GREEN_600,
                text_align="center",
                max_lines=3
            )
        
        popup_content = ft.Container(
            content=ft.Column([
                ft.Text(texts["title"].format(room=room_title), size=20, weight=ft.FontWeight.BOLD),
                ft.Text(texts["desc"], text_align="center"),
                qr_code_image,
                # ID 부분을 드래그 가능하고 복사 버튼이 있는 형태로 수정
                ft.Container(
                    content=ft.Column([
                        ft.Text(texts["room_id"].format(id=""), size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Text(
                                        room_id,
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLUE_600,
                                        selectable=True,
                                        font_family="monospace"
                                    ),
                                    bgcolor=ft.Colors.GREY_100,
                                    padding=12,
                                    border_radius=8,
                                    border=ft.border.all(1, ft.Colors.GREY_300),
                                    expand=True
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.COPY,
                                    icon_color=ft.Colors.BLUE_600,
                                    tooltip="ID 복사",
                                    on_click=lambda e: copy_room_id(room_id)
                                )
                            ], alignment=ft.MainAxisAlignment.START, spacing=8),
                            width=300
                        )
                    ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=350
                ),
                persistent_info if is_persistent else ft.Container(),
                ft.ElevatedButton(texts["close"], on_click=close_dialog, width=300)
            ], tight=True, spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=350,
            padding=30,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26)
        )
        page.overlay.append(
            ft.Container(
                content=popup_content,
                alignment=ft.alignment.center,
                expand=True
            )
        )
        page.update()

    def handle_create_room(room_title, target_lang, is_persistent=False):
        if not room_title:
            room_title = "새로운 채팅방"
        if not target_lang:
            target_lang = "en"
            print("상대방 언어가 선택되지 않아 기본값(en)으로 설정합니다.")

        # 고정 채팅방인 경우 고정된 ID 생성 (방 제목 기반)
        if is_persistent:
            import hashlib
            # 방 제목을 기반으로 고정된 ID 생성
            room_id_base = hashlib.md5(room_title.encode()).hexdigest()[:8]
            new_room_id = f"persistent_{room_id_base}"
            print(f"고정 채팅방 ID 생성: {new_room_id}")
        else:
            new_room_id = uuid.uuid4().hex[:8]
        
        # Firebase 사용 가능 여부 확인
        if not FIREBASE_AVAILABLE:
            print("Firebase가 초기화되지 않아 방을 생성할 수 없습니다.")
            # 사용자에게 오류 메시지 표시 (간단한 팝업)
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Firebase 연결 오류로 방을 생성할 수 없습니다. 설정을 확인해주세요."),
                action="확인"
            )
            page.snack_bar.open = True
            page.update()
            return
        
        # Firebase에 방 정보 저장
        try:
            rooms_ref = db.reference('/rooms')
            room_data = {
                'id': new_room_id,
                'title': room_title,
                'user_lang': lang,
                'target_lang': target_lang,
                'created_at': int(time.time() * 1000),
                'is_persistent': is_persistent,
                'created_by': page.session.get('nickname') or '익명',  # 방 생성자 정보 추가
                'creator_id': page.session.get('user_id') or str(uuid.uuid4())  # 생성자 고유 ID 추가
            }
            rooms_ref.child(new_room_id).set(room_data)
            print(f"Firebase에 방 '{room_title}' 정보 저장 성공 (고정: {is_persistent}, 생성자: {room_data['created_by']})")
        except Exception as e:
            print(f"Firebase 방 정보 저장 실패: {e}")
            # 사용자에게 오류 메시지 표시 (간단한 팝업)
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Firebase 연결 오류로 방을 생성할 수 없습니다. 설정을 확인해주세요."),
                action="확인"
            )
            page.snack_bar.open = True
            page.update()
            return

        print(f"방 '{room_title}' 생성됨 (ID: {new_room_id}, 내 언어: {lang}, 상대 언어: {target_lang}, 고정: {is_persistent})")
        go_chat(lang, target_lang, new_room_id, room_title)

    # --- 화면 이동 함수 ---
    def go_home(selected_lang=None):
        nonlocal lang
        if selected_lang:
            lang = selected_lang
        page.views.clear()
        page.views.append(HomePage(page, lang,
            on_create=lambda e: go_create(lang),
            on_find=lambda e: go_room_list(lang, e),
            on_quick=lambda e: handle_create_room("빠른 채팅방", "en", False),
            on_mbti_tourism=lambda e: go_mbti_tourism(lang),
            on_change_lang=go_nationality, on_back=go_nationality))
        page.go("/home")

    def go_nationality(e=None):
        page.views.clear()
        page.views.append(NationalitySelectPage(page, on_select=go_home, on_foreign_select=go_foreign_country_select))
        page.go("/")

    def go_foreign_country_select(e=None):
        page.views.clear()
        page.views.append(ForeignCountrySelectPage(page, on_select=on_country_selected, on_back=go_nationality))
        page.go("/foreign_country_select")

    def on_country_selected(country_code, lang_code):
        nonlocal lang
        lang = lang_code
        go_home(lang)

    def go_create(lang):
        page.views.clear()
        page.views.append(CreateRoomPage(page, lang, on_create=handle_create_room, on_back=lambda e: go_home(lang)))
        page.go("/create_room")

    def go_room_list(lang, e=None):
        def on_find_by_id(e):
            go_find_by_id(lang)
        texts = FIND_ROOM_TEXTS.get(lang, FIND_ROOM_TEXTS["ko"])
        page.views.clear()
        # 사용자별 고유 RAG 방 ID 생성 (UUID 사용)
        user_id = page.session.get("user_id") or None
        if not user_id:
            user_id = str(uuid.uuid4())
            page.session.set("user_id", user_id)
        user_rag_room_id = f"{RAG_ROOM_ID}_{user_id}"
        page.views.append(
            ft.View(
                "/find_room_method",
                controls=[
                    # 헤더 (뒤로가기 + 타이틀)
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: go_home(lang)),
                        ft.Text(texts["title"], size=24, weight=ft.FontWeight.BOLD, color=get_text_color(page)),
                    ], alignment=ft.MainAxisAlignment.START, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                    # 카드형 버튼들
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.TAG, color="#2563EB", size=28),
                                        bgcolor="#E0E7FF", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(texts["id"], size=16, weight=ft.FontWeight.BOLD, color=get_text_color(page)),
                                        ft.Text(texts["id_desc"], size=12, color=get_sub_text_color(page), text_align=ft.TextAlign.START, max_lines=3)
                                    ], spacing=2, expand=True)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=get_card_bg_color(page),
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                on_click=on_find_by_id
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.TABLE_CHART, color="#22C55E", size=28),
                                        bgcolor="#DCFCE7", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(texts["rag"], size=16, weight=ft.FontWeight.BOLD, color=get_text_color(page)),
                                        ft.Text(texts["rag_desc"], size=12, color=get_sub_text_color(page), text_align=ft.TextAlign.START, max_lines=3)
                                    ], spacing=2, expand=True)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=get_card_bg_color(page),
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                margin=ft.margin.only(bottom=16),
                                on_click=lambda e: go_chat(lang, "zh-TW" if lang == "zh-TW" else lang, user_rag_room_id, RAG_ROOM_TITLE, is_rag=True)
                            ),
                            # --- 외국인 근로자 권리구제 버튼 추가 ---
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.GAVEL, color="#F59E42", size=28),
                                        bgcolor="#FFF7E6", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(FOREIGN_WORKER_ROOM_CARD_TEXTS.get(lang, FOREIGN_WORKER_ROOM_CARD_TEXTS["ko"])["title"], size=16, weight=ft.FontWeight.BOLD, color=get_text_color(page)),
                                        ft.Text(FOREIGN_WORKER_ROOM_CARD_TEXTS.get(lang, FOREIGN_WORKER_ROOM_CARD_TEXTS["ko"])["desc"], size=12, color=get_sub_text_color(page), text_align=ft.TextAlign.START, max_lines=3)
                                    ], spacing=2, expand=True)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=get_card_bg_color(page),
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                margin=ft.margin.only(bottom=16),
                                on_click=lambda e: go_foreign_worker_rag_chat(lang)
                            ),
                            # --- 부산 맛집 검색 버튼 추가 ---
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.RESTAURANT, color="#E91E63", size=28),
                                        bgcolor="#FCE4EC", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(BUSAN_FOOD_ROOM_CARD_TEXTS.get(lang, BUSAN_FOOD_ROOM_CARD_TEXTS["ko"])["title"], size=16, weight=ft.FontWeight.BOLD, color=get_text_color(page)),
                                        ft.Text(BUSAN_FOOD_ROOM_CARD_TEXTS.get(lang, BUSAN_FOOD_ROOM_CARD_TEXTS["ko"])["desc"], size=12, color=get_sub_text_color(page), text_align=ft.TextAlign.START, max_lines=3)
                                    ], spacing=2, expand=True)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=get_card_bg_color(page),
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                margin=ft.margin.only(bottom=16),
                                on_click=lambda e: go_busan_food_rag_chat(lang) if BUSAN_FOOD_RAG_AVAILABLE else None,
                                opacity=1.0 if BUSAN_FOOD_RAG_AVAILABLE else 0.5
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.only(top=32),
                        alignment=ft.alignment.center,
                    ),
                ],
                bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right)
            )
        )
        page.go("/find_room_method")

    def go_find_by_id(lang):
        def on_submit(e=None):
            room_id = id_field.value.strip()
            if room_id:
                go_chat_from_list(room_id)
        # 다국어 텍스트 사전
        FIND_BY_ID_TEXTS = {
            "ko": {"title": "방 ID로 채팅방 찾기", "label": "방 ID를 입력하세요", "enter": "입장", "back": "뒤로가기"},
            "en": {"title": "Find Chat Room by ID", "label": "Enter chat room ID", "enter": "Enter", "back": "Back"},
            "ja": {"title": "IDでチャットルームを探す", "label": "ルームIDを入力してください", "enter": "入室", "back": "戻る"},
            "zh": {"title": "通过ID查找聊天室", "label": "请输入房间ID", "enter": "进入", "back": "返回"},
            "zh-TW": {"title": "通過ID查找聊天室", "label": "請輸入房間ID", "enter": "進入", "back": "返回"},
            "id": {"title": "Cari Ruang Obrolan dengan ID", "label": "Masukkan ID ruang obrolan", "enter": "Masuk", "back": "Kembali"},
            "vi": {"title": "Tìm phòng chat bằng ID", "label": "Nhập ID phòng chat", "enter": "Vào phòng", "back": "Quay lại"},
            "fr": {"title": "Trouver une salle par ID", "label": "Entrez l'ID de la salle", "enter": "Entrer", "back": "Retour"},
            "de": {"title": "Chatraum per ID finden", "label": "Geben Sie die Raum-ID ein", "enter": "Betreten", "back": "Zurück"},
            "th": {"title": "ค้นหาห้องแชทด้วย ID", "label": "กรอก ID ห้องแชท", "enter": "เข้าร่วม", "back": "ย้อนกลับ"},
        }
        t = FIND_BY_ID_TEXTS.get(lang, FIND_BY_ID_TEXTS["en"])
        id_field = ft.TextField(label=t["label"], width=300, on_submit=on_submit)
        page.views.clear()
        page.views.append(
            ft.View(
                "/find_by_id",
                controls=[
                    ft.Text(t["title"], size=20, weight=ft.FontWeight.BOLD),
                    id_field,
                    ft.ElevatedButton(t["enter"], on_click=on_submit, width=300),
                    ft.ElevatedButton(t["back"], on_click=lambda e: go_room_list(lang), width=300)
                ],
                bgcolor=get_bg_color(page),
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                vertical_alignment=ft.MainAxisAlignment.CENTER
            )
        )
        page.go("/find_by_id")

    def go_chat_from_list(room_id):
        # 로딩 상태 표시
        page.snack_bar = ft.SnackBar(
            content=ft.Text("채팅방에 접속 중입니다..."),
            duration=2000
        )
        page.snack_bar.open = True
        page.update()
        
        # RAG 채팅방인지 확인 (공용 RAG_ROOM_ID로 들어오면, 사용자별로 리다이렉트)
        if room_id == RAG_ROOM_ID or room_id.startswith(RAG_ROOM_ID):
            user_id = page.session.get("user_id") or None
            if not user_id:
                user_id = str(uuid.uuid4())
                page.session.set("user_id", user_id)
            user_rag_room_id = f"{RAG_ROOM_ID}_{user_id}"
            # 언어별 RAG 채팅방 제목 설정
            from pages.chat_room import RAG_GUIDE_TEXTS
            rag_room_title = RAG_GUIDE_TEXTS.get(lang, RAG_GUIDE_TEXTS["ko"])["title"]
            go_chat(lang, lang, user_rag_room_id, rag_room_title, is_rag=True)
            return
        
        try:
            # Firebase 연결 확인
            if not FIREBASE_AVAILABLE:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Firebase 연결이 불가능합니다. 네트워크를 확인해주세요."),
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
                return
            
            room_ref = db.reference(f'/rooms/{room_id}')
            room_data = room_ref.get()
            if room_data:
                go_chat(
                    user_lang=room_data.get('user_lang', 'ko'),
                    target_lang=room_data.get('target_lang', 'en'),
                    room_id=room_id,
                    room_title=room_data.get('title', '채팅방'),
                    is_rag=room_data.get('is_rag', False)
                )
            else:
                print(f"오류: ID가 {room_id}인 방을 찾을 수 없습니다.")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"채팅방을 찾을 수 없습니다 (ID: {room_id})"),
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
                # 홈으로 리다이렉트
                go_home(lang)
        except Exception as e:
            print(f"Firebase에서 방 정보 가져오기 실패: {e}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text("채팅방 접속에 실패했습니다. 네트워크를 확인해주세요."),
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
            # 홈으로 리다이렉트
            go_home(lang)

    def go_chat(user_lang, target_lang, room_id, room_title="채팅방", is_rag=False, is_foreign_worker_rag=False, is_busan_food_rag=False):
        def after_nickname(nickname):
            page.session.set("nickname", nickname)
            page.views.clear()
            
            # 부산 맛집 검색 RAG 채팅방인지 확인
            if is_busan_food_rag:
                # 대화 컨텍스트를 저장할 변수
                conversation_context = {}
                
                def busan_food_rag_answer(query, target_lang):
                    try:
                        print(f"부산 맛집 JSON 기반 질문: {query}")
                        print(f"타겟 언어: {target_lang}")
                        if busan_food_json_data is None or taek_sulling_json_data is None:
                            print("부산 맛집 JSON 데이터가 None입니다.")
                            # 다국어 오류 메시지
                            error_messages = {
                                "ko": "죄송합니다. 부산 맛집 검색 기능이 현재 사용할 수 없습니다. (JSON 데이터가 로드되지 않았습니다.)",
                                "en": "Sorry, the Busan restaurant search function is currently unavailable. (JSON data not loaded.)",
                                "vi": "Xin lỗi, chức năng tìm kiếm nhà hàng Busan hiện không khả dụng. (Dữ liệu JSON chưa được tải.)",
                                "zh": "抱歉，釜山美食搜索功能目前不可用。（JSON数据未加载。）",
                                "ja": "申し訳ございません。釜山レストラン検索機能は現在利用できません。（JSONデータが読み込まれていません。）",
                                "th": "ขออภัย ฟีเจอร์ค้นหาร้านอาหารปูซานไม่สามารถใช้งานได้ในขณะนี้ (ข้อมูล JSON ยังไม่ได้โหลด)",
                                "id": "Maaf, fitur pencarian restoran Busan saat ini tidak tersedia. (Data JSON belum dimuat.)",
                                "tl": "Paumanhin, ang Busan restaurant search feature ay hindi available ngayon. Subukan mo ulit mamaya o makipag-ugnayan sa admin. (Hindi pa na-load ang JSON data.)",
                                "fr": "Désolé, la fonction de recherche de restaurants de Busan n'est pas disponible actuellement. (Données JSON non chargées.)",
                                "de": "Entschuldigung, die Busan-Restaurant-Suchfunktion ist derzeit nicht verfügbar. (JSON-Daten nicht geladen.)",
                                "tw": "抱歉，釜山美食搜尋功能目前無法使用。（JSON資料未載入。）"
                            }
                            return error_messages.get(target_lang, error_messages["ko"])
                        
                        result = answer_with_busan_food_json(query, busan_food_json_data, taek_sulling_json_data, GEMINI_API_KEY, target_lang=target_lang)
                        print(f"JSON 기반 답변 생성 완료: {len(result)} 문자")
                        return result
                    except Exception as e:
                        print(f"부산 맛집 JSON 기반 답변 오류: {e}")
                        import traceback
                        traceback.print_exc()
                        # 다국어 오류 메시지
                        error_messages = {
                            "ko": "죄송합니다. 부산 맛집 정보를 처리하는 중에 오류가 발생했습니다.",
                            "en": "Sorry, an error occurred while processing Busan restaurant information.",
                            "vi": "Xin lỗi, đã xảy ra lỗi khi xử lý thông tin nhà hàng Busan.",
                            "zh": "抱歉，处理釜山餐厅信息时发生错误。",
                            "ja": "申し訳ございません。釜山レストラン情報の処理中にエラーが発生しました。",
                            "th": "ขออภัย เกิดข้อผิดพลาดขณะประมวลผลข้อมูลร้านอาหารปูซาน",
                            "id": "Maaf, terjadi kesalahan saat memproses informasi restoran Busan.",
                            "tl": "Paumanhin, nagkaroon ng error habang pinoproseso ang impormasyon ng restaurant sa Busan.",
                            "fr": "Désolé, une erreur s'est produite lors du traitement des informations sur les restaurants de Busan.",
                            "de": "Entschuldigung, beim Verarbeiten der Busan-Restaurant-Informationen ist ein Fehler aufgetreten.",
                            "tw": "抱歉，處理釜山餐廳資訊時發生錯誤。"
                        }
                        return error_messages.get(target_lang, error_messages["ko"])
                
                page.views.append(ChatRoomPage(
                    page,
                    room_id=room_id,
                    room_title=room_title,
                    user_lang=user_lang,
                    target_lang=target_lang,
                    on_back=lambda e: go_room_list(lang),
                    on_share=on_share_clicked,
                    custom_translate_message=busan_food_rag_answer,
                    firebase_available=FIREBASE_AVAILABLE,
                    is_busan_food_rag=True
                ))
            # 외국인 근로자 RAG 채팅방인지 확인
            elif is_foreign_worker_rag:
                # 대화 컨텍스트를 저장할 변수
                conversation_context = {}
                
                def foreign_worker_rag_answer_wrapper(query, target_lang):
                    # rag_utils.py의 foreign_worker_rag_answer 함수 호출
                    return foreign_worker_rag_answer(
                        query=query, 
                        target_lang=target_lang, 
                        vector_db_foreign_worker=vector_db_foreign_worker, 
                        gemini_api_key=GEMINI_API_KEY, 
                        conversation_context=conversation_context,
                        jangmachul_json_data=jangmachul_json_data,
                        onyul_json_data=onyul_json_data
                    )
                
                page.views.append(ChatRoomPage(
                    page,
                    room_id=room_id,
                    room_title=room_title,
                    user_lang=user_lang,
                    target_lang=target_lang,
                    on_back=lambda e: go_room_list(lang),
                    on_share=on_share_clicked,
                    custom_translate_message=foreign_worker_rag_answer_wrapper,
                    firebase_available=FIREBASE_AVAILABLE,
                    is_foreign_worker_rag=True
                ))
            # 기존 다문화 가족 RAG 채팅방인지 확인
            elif is_rag:
                # 대화 컨텍스트를 저장할 변수 (쓰레기 처리 관련 정보 유지) - 세션에 저장하여 지속
                if not page.session.contains_key('conversation_context'):
                    page.session.set('conversation_context', {'waste_query': None, 'waste_district': None})
                conversation_context = page.session.get('conversation_context') or []
                
                def multicultural_rag_answer(query, target_lang):
                    try:
                        print(f"다문화 가족 RAG 질문: {query}")
                        print(f"타겟 언어: {target_lang}")
                        if vector_db_multicultural is None:
                            print("다문화가족 벡터DB가 None입니다.")
                            # 다국어 오류 메시지
                            error_messages = {
                                "ko": "죄송합니다. RAG 기능이 현재 사용할 수 없습니다. (다문화가족 벡터DB가 로드되지 않았습니다.)",
                                "en": "Sorry, the RAG function is currently unavailable. (Multicultural family vector database not loaded.)",
                                "vi": "Xin lỗi, chức năng RAG hiện không khả dụng. (Cơ sở dữ liệu vector gia đình đa văn hóa chưa được tải.)",
                                "zh": "抱歉，RAG功能目前不可用。（多文化家庭向量数据库未加载。）",
                                "ja": "申し訳ございません。RAG機能は現在利用できません。（多文化家族ベクターデータベースが読み込まれていません。）",
                                "th": "ขออภัย ฟังก์ชัน RAG ไม่สามารถใช้งานได้ในขณะนี้ (ฐานข้อมูลเวกเตอร์ครอบครัวพหุวัฒนธรรมยังไม่ได้โหลด)",
                                "id": "Maaf, fungsi RAG saat ini tidak tersedia. (Database vektor keluarga multikultural belum dimuat.)",
                                "tl": "Paumanhin, ang RAG function ay hindi available ngayon. (Hindi pa na-load ang multicultural family vector database.)",
                                "fr": "Désolé, la fonction RAG n'est pas disponible actuellement. (Base de données vectorielle des familles multiculturelles non chargée.)",
                                "de": "Entschuldigung, die RAG-Funktion ist derzeit nicht verfügbar. (Multikulturelle Familien-Vektordatenbank nicht geladen.)",
                                "tw": "抱歉，RAG功能目前無法使用。（多文化家庭向量資料庫未載入。）"
                            }
                            return error_messages.get(target_lang, error_messages["ko"])
                        print(f"다문화가족 벡터DB 문서 수: {len(vector_db_multicultural.documents) if hasattr(vector_db_multicultural, 'documents') else '알 수 없음'}")
                        
                        # 쓰레기 처리 관련 질문 확인
                        
                        # 대화 컨텍스트 디버깅
                        print(f"현재 대화 컨텍스트: {conversation_context}")
                        print(f"이전 쓰레기 질문: {conversation_context.get('waste_query')}")
                        print(f"현재 질문이 쓰레기 관련인가: {is_waste_related_query(query)}")
                        print(f"현재 질문이 외국인 등록 관련인가: {is_alien_registration_related_query(query)}")
                        
                        # 외국인 등록 관련 질문 확인 (우선 처리)
                        if is_alien_registration_related_query(query):
                            print("외국인 등록 관련 질문 감지됨")
                            detailed_guide = get_detailed_alien_registration_guide(target_lang)
                            return detailed_guide
                        
                        # 이전에 쓰레기 처리 질문이 있었고, 현재 질문이 구군명만 제공하는 경우 확인
                        if conversation_context.get('waste_query') and not is_waste_related_query(query):
                            district = extract_district_from_query(query)
                            if district:
                                print(f"구군명 후속 답변 감지: {district}")
                                print(f"이전 쓰레기 질문: {conversation_context.get('waste_query')}")
                                conversation_context['waste_district'] = district
                                page.session.set('conversation_context', conversation_context)  # 세션에 저장
                                # 구군명을 제공받았으므로 쓰레기 처리 정보 제공
                                query = f"{district} 쓰레기 버리는 방법"  # 임시로 쓰레기 관련 질문으로 변환
                                print(f"변환된 질문: {query}")
                        
                        if is_waste_related_query(query):
                            print("쓰레기 처리 관련 질문 감지됨")
                            # 쓰레기 관련 질문을 대화 컨텍스트에 저장
                            conversation_context['waste_query'] = query
                            page.session.set('conversation_context', conversation_context)  # 세션에 저장
                            district = extract_district_from_query(query)
                            
                            if district:
                                print(f"구군명 감지됨: {district}")
                                # 부산광역시_쓰레기처리정보.json에서 정보 조회
                                try:
                                    import json
                                    busan_waste_json_path = "부산광역시_쓰레기처리정보.json"
                                    if os.path.exists(busan_waste_json_path):
                                        with open(busan_waste_json_path, "r", encoding="utf-8") as f:
                                            waste_data = json.load(f)
                                        
                                        district_info = waste_data.get("부산광역시_쓰레기처리정보", {}).get("구군별_정보", {}).get(district)
                                        if district_info:
                                            # 다국어 레이블 템플릿
                                            labels = {
                                                "ko": {
                                                    "title": f"📍 {district} 쓰레기 배출 안내",
                                                    "department": "🏢 담당부서",
                                                    "time": "⏰ 배출시간",
                                                    "place": "📍 배출장소",
                                                    "schedule": "📅 배출요일별 안내:",
                                                    "price": "💰 종량제봉투 가격:",
                                                    "notes": "⚠️ 특이사항:",
                                                    "large_waste": "🚛 대형폐기물 수거업체:",
                                                    "no_disposal": "배출금지",
                                                    "report_method": "신고방법",
                                                    "won": "원"
                                                },
                                                "en": {
                                                    "title": f"📍 {district} Waste Disposal Guide",
                                                    "department": "🏢 Department",
                                                    "time": "⏰ Collection Time",
                                                    "place": "📍 Collection Location",
                                                    "schedule": "📅 Weekly Collection Schedule:",
                                                    "price": "💰 Waste Bag Prices:",
                                                    "notes": "⚠️ Special Notes:",
                                                    "large_waste": "🚛 Large Waste Collection Companies:",
                                                    "no_disposal": "No disposal",
                                                    "report_method": "Reporting method",
                                                    "won": "KRW"
                                                },
                                                "vi": {
                                                    "title": f"📍 Hướng dẫn xử lý rác thải {district}",
                                                    "department": "🏢 Phòng ban phụ trách",
                                                    "time": "⏰ Thời gian thu gom",
                                                    "place": "📍 Địa điểm thu gom",
                                                    "schedule": "📅 Lịch thu gom hàng tuần:",
                                                    "price": "💰 Giá túi rác:",
                                                    "notes": "⚠️ Lưu ý đặc biệt:",
                                                    "large_waste": "🚛 Công ty thu gom rác lớn:",
                                                    "no_disposal": "Không được vứt",
                                                    "report_method": "Phương pháp báo cáo",
                                                    "won": "KRW"
                                                },
                                                "zh": {
                                                    "title": f"📍 {district}垃圾处理指南",
                                                    "department": "🏢 负责部门",
                                                    "time": "⏰ 收集时间",
                                                    "place": "📍 收集地点",
                                                    "schedule": "📅 每周收集时间表:",
                                                    "price": "💰 垃圾袋价格:",
                                                    "notes": "⚠️ 特别注意事项:",
                                                    "large_waste": "🚛 大型垃圾收集公司:",
                                                    "no_disposal": "禁止投放",
                                                    "report_method": "申报方法",
                                                    "won": "韩元"
                                                },
                                                "ja": {
                                                    "title": f"📍 {district}ゴミ処理ガイド",
                                                    "department": "🏢 担当部署",
                                                    "time": "⏰ 収集時間",
                                                    "place": "📍 収集場所",
                                                    "schedule": "📅 週間収集スケジュール:",
                                                    "price": "💰 ゴミ袋価格:",
                                                    "notes": "⚠️ 特記事項:",
                                                    "large_waste": "🚛 大型ゴミ収集業者:",
                                                    "no_disposal": "排出禁止",
                                                    "report_method": "報告方法",
                                                    "won": "ウォン"
                                                },
                                                "tw": {
                                                    "title": f"📍 {district}垃圾處理指南",
                                                    "department": "🏢 負責部門",
                                                    "time": "⏰ 收集時間",
                                                    "place": "📍 收集地點",
                                                    "schedule": "📅 每週收集時間表:",
                                                    "price": "💰 垃圾袋價格:",
                                                    "notes": "⚠️ 特別注意事項:",
                                                    "large_waste": "🚛 大型垃圾收集公司:",
                                                    "no_disposal": "禁止投放",
                                                    "report_method": "申報方法",
                                                    "won": "台幣"
                                                },
                                                "th": {
                                                    "title": f"📍 คู่มือการจัดการขยะ {district}",
                                                    "department": "🏢 หน่วยงานที่รับผิดชอบ",
                                                    "time": "⏰ เวลาเก็บขยะ",
                                                    "place": "📍 สถานที่เก็บขยะ",
                                                    "schedule": "📅 ตารางเก็บขยะรายสัปดาห์:",
                                                    "price": "💰 ราคาถุงขยะ:",
                                                    "notes": "⚠️ ข้อสังเกตพิเศษ:",
                                                    "large_waste": "🚛 บริษัทเก็บขยะขนาดใหญ่:",
                                                    "no_disposal": "ห้ามทิ้ง",
                                                    "report_method": "วิธีการแจ้ง",
                                                    "won": "วอน"
                                                },
                                                "tl": {
                                                    "title": f"📍 Gabay sa Pagtatapon ng Basura sa {district}",
                                                    "department": "🏢 Departamentong may hawak",
                                                    "time": "⏰ Oras ng koleksyon",
                                                    "place": "📍 Lugar ng koleksyon",
                                                    "schedule": "📅 Lingguhang iskedyul ng koleksyon:",
                                                    "price": "💰 Presyo ng supot ng basura:",
                                                    "notes": "⚠️ Espesyal na paalala:",
                                                    "large_waste": "🚛 Mga kumpanya ng malaking basura:",
                                                    "no_disposal": "Bawal itapon",
                                                    "report_method": "Paraan ng pag-report",
                                                    "won": "Won"
                                                },
                                                "id": {
                                                    "title": f"📍 Panduan Pembuangan Sampah {district}",
                                                    "department": "🏢 Departemen yang bertanggung jawab",
                                                    "time": "⏰ Waktu pengumpulan",
                                                    "place": "📍 Lokasi pengumpulan",
                                                    "schedule": "📅 Jadwal pengumpulan mingguan:",
                                                    "price": "💰 Harga kantong sampah:",
                                                    "notes": "⚠️ Catatan khusus:",
                                                    "large_waste": "🚛 Perusahaan pengumpul sampah besar:",
                                                    "no_disposal": "Dilarang buang",
                                                    "report_method": "Metode pelaporan",
                                                    "won": "Won"
                                                },
                                                "fr": {
                                                    "title": f"📍 Guide d'élimination des déchets {district}",
                                                    "department": "🏢 Département responsable",
                                                    "time": "⏰ Heure de collecte",
                                                    "place": "📍 Lieu de collecte",
                                                    "schedule": "📅 Horaire de collecte hebdomadaire:",
                                                    "price": "💰 Prix des sacs poubelles:",
                                                    "notes": "⚠️ Notes spéciales:",
                                                    "large_waste": "🚛 Entreprises de collecte de gros déchets:",
                                                    "no_disposal": "Interdiction de jeter",
                                                    "report_method": "Méthode de signalement",
                                                    "won": "Won"
                                                },
                                                "de": {
                                                    "title": f"📍 Abfallentsorgungshandbuch {district}",
                                                    "department": "🏢 Zuständige Abteilung",
                                                    "time": "⏰ Abholzeit",
                                                    "place": "📍 Abholort",
                                                    "schedule": "📅 Wöchentlicher Abholplan:",
                                                    "price": "💰 Müllbeutelpreise:",
                                                    "notes": "⚠️ Besondere Hinweise:",
                                                    "large_waste": "🚛 Sperrmüll-Entsorgungsunternehmen:",
                                                    "no_disposal": "Entsorgung verboten",
                                                    "report_method": "Meldeverfahren",
                                                    "won": "Won"
                                                }
                                            }
                                            
                                            # 언어별 레이블 선택
                                            current_labels = labels.get(target_lang, labels["ko"])
                                            
                                            # 한국어 데이터 번역 매핑
                                            translations = {
                                                "en": {
                                                    # 부서명 번역
                                                    "자원순환과": "Resource Circulation Department",
                                                    "청소행정과": "Sanitation Administration Department",
                                                    "환경위생과": "Environmental Sanitation Department",
                                                    "환경과": "Environment Department",
                                                    "청소과": "Sanitation Department",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "General waste",
                                                    "음식물쓰레기": "Food waste",
                                                    "재활용품": "Recyclables",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Recyclables (cans, bottles, scrap metal, plastic, milk/paper cartons, clear PET bottles)",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "Recyclables (paper, clothing, plastic packaging, styrofoam)",
                                                    "소형폐가전": "Small waste electronics",
                                                    "불연성폐기물": "Non-combustible waste",
                                                    "연탄재": "Briquette ash",
                                                    "소규모건설폐기물(PP전용마대)": "Small construction waste (PP bags only)",
                                                    "배출금지": "No disposal",
                                                    
                                                    # 요일 번역
                                                    "일요일": "Sunday",
                                                    "월요일": "Monday", 
                                                    "화요일": "Tuesday",
                                                    "수요일": "Wednesday",
                                                    "목요일": "Thursday",
                                                    "금요일": "Friday",
                                                    "토요일": "Saturday"
                                                },
                                                "vi": {
                                                    # 부서명 번역
                                                    "자원순환과": "Phòng Tuần hoàn Tài nguyên",
                                                    "청소행정과": "Phòng Hành chính Vệ sinh",
                                                    "환경위생과": "Phòng Vệ sinh Môi trường", 
                                                    "환경과": "Phòng Môi trường",
                                                    "청소과": "Phòng Vệ sinh",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "Rác thải chung",
                                                    "음식물쓰레기": "Rác thực phẩm",
                                                    "재활용품": "Đồ tái chế",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Đồ tái chế (lon, chai, kim loại phế, nhựa, hộp sữa/giấy, chai PET trong suốt)",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "Đồ tái chế (giấy, quần áo, bao bì nhựa, xốp)",
                                                    "소형폐가전": "Thiết bị điện tử phế liệu nhỏ",
                                                    "불연성폐기물": "Chất thải không cháy",
                                                    "연탄재": "Tro than củi",
                                                    "소규모건설폐기물(PP전용마대)": "Chất thải xây dựng nhỏ (chỉ túi PP)",
                                                    "배출금지": "Cấm thải",
                                                    
                                                    # 요일 번역
                                                    "일요일": "Chủ nhật",
                                                    "월요일": "Thứ hai",
                                                    "화요일": "Thứ ba", 
                                                    "수요일": "Thứ tư",
                                                    "목요일": "Thứ năm",
                                                    "금요일": "Thứ sáu",
                                                    "토요일": "Thứ bảy"
                                                },
                                                "zh": {
                                                    # 부서명 번역
                                                    "자원순환과": "资源循环科",
                                                    "청소행정과": "清扫行政科",
                                                    "환경위생과": "环境卫生科",
                                                    "환경과": "环境科", 
                                                    "청소과": "清扫科",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "一般垃圾",
                                                    "음식물쓰레기": "食物垃圾",
                                                    "재활용품": "可回收物",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "可回收物（罐头、瓶子、废铁、塑料、牛奶纸盒、透明PET瓶）",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "可回收物（纸类、衣物、塑料包装、泡沫塑料）",
                                                    "소형폐가전": "小型废旧家电",
                                                    "불연성폐기물": "不可燃垃圾",
                                                    "연탄재": "煤球灰",
                                                    "소규모건설폐기물(PP전용마대)": "小型建筑垃圾（PP专用袋）",
                                                    "배출금지": "禁止投放",
                                                    
                                                    # 요일 번역
                                                    "일요일": "星期日",
                                                    "월요일": "星期一",
                                                    "화요일": "星期二",
                                                    "수요일": "星期三", 
                                                    "목요일": "星期四",
                                                    "금요일": "星期五",
                                                    "토요일": "星期六"
                                                },
                                                "ja": {
                                                    # 부서명 번역
                                                    "자원순환과": "資源循環課",
                                                    "청소행정과": "清掃行政課",
                                                    "환경위생과": "環境衛生課",
                                                    "환경과": "環境課",
                                                    "청소과": "清掃課",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "一般ゴミ",
                                                    "음식물쓰레기": "生ゴミ",
                                                    "재활용품": "リサイクル品",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "リサイクル品（缶、瓶、鉄くず、プラスチック、牛乳紙パック、透明ペットボトル）",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "リサイクル品（紙、衣類、ビニール包装材、発泡スチロール）",
                                                    "소형폐가전": "小型廃家電",
                                                    "불연성폐기물": "不燃ゴミ",
                                                    "연탄재": "練炭灰",
                                                    "소규모건설폐기물(PP전용마대)": "小規模建設廃棄物（PP専用袋）",
                                                    "배출금지": "排出禁止",
                                                    
                                                    # 요일 번역
                                                    "일요일": "日曜日",
                                                    "월요일": "月曜日",
                                                    "화요일": "火曜日",
                                                    "수요일": "水曜日",
                                                    "목요일": "木曜日", 
                                                    "금요일": "金曜日",
                                                    "토요일": "土曜日"
                                                },
                                                "tw": {
                                                    # 부서명 번역
                                                    "자원순환과": "資源循環課",
                                                    "청소행정과": "清掃行政課",
                                                    "환경위생과": "環境衛生課",
                                                    "환경과": "環境課",
                                                    "청소과": "清掃課",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "一般垃圾",
                                                    "음식물쓰레기": "食物垃圾",
                                                    "재활용품": "可回收物",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "可回收物（罐頭、瓶子、廢鐵、塑膠、牛奶紙盒、透明PET瓶）",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "可回收物（紙類、衣物、塑膠包裝、泡沫塑膠）",
                                                    "소형폐가전": "小型廢棄家電",
                                                    "불연성폐기물": "不可燃垃圾",
                                                    "연탄재": "煤球灰",
                                                    "소규모건설폐기물(PP전용마대)": "小型建築垃圾（PP專用袋）",
                                                    "배출금지": "禁止投放",
                                                    
                                                    # 요일 번역
                                                    "일요일": "星期日",
                                                    "월요일": "星期一",
                                                    "화요일": "星期二",
                                                    "수요일": "星期三",
                                                    "목요일": "星期四",
                                                    "금요일": "星期五",
                                                    "토요일": "星期六"
                                                },
                                                "th": {
                                                    # 부서명 번역
                                                    "자원순환과": "แผนกหมุนเวียนทรัพยากร",
                                                    "청소행정과": "แผนกบริหารสุขาภิบาล",
                                                    "환경위생과": "แผนกสุขาภิบาลสิ่งแวดล้อม",
                                                    "환경과": "แผนกสิ่งแวดล้อม",
                                                    "청소과": "แผนกสุขาภิบาล",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "ขยะทั่วไป",
                                                    "음식물쓰레기": "ขยะอาหาร",
                                                    "재활용품": "ของรีไซเคิล",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "ของรีไซเคิล（กระป๋อง, ขวด, เหล็กเก่า, พลาสติก, กล่องนม/กระดาษ, ขวดPETใส）",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "ของรีไซเคิล（กระดาษ, เสื้อผ้า, บรรจุภัณฑ์พลาสติก, โฟม）",
                                                    "소형폐가전": "เครื่องใช้ไฟฟ้าขนาดเล็กที่ไม่ใช้แล้ว",
                                                    "불연성폐기물": "ขยะที่ไม่ติดไฟ",
                                                    "연탄재": "เถ้าถ่านอัด",
                                                    "소규모건설폐기물(PP전용마대)": "ขยะก่อสร้างขนาดเล็ก（ถุงPPเท่านั้น）",
                                                    "배출금지": "ห้ามทิ้ง",
                                                    
                                                    # 요일 번역
                                                    "일요일": "วันอาทิตย์",
                                                    "월요일": "วันจันทร์",
                                                    "화요일": "วันอังคาร",
                                                    "수요일": "วันพุธ",
                                                    "목요일": "วันพฤหัสบดี",
                                                    "금요일": "วันศุกร์",
                                                    "토요일": "วันเสาร์"
                                                },
                                                "tl": {
                                                    # 부서명 번역
                                                    "자원순환과": "Departamento ng Pag-ikot ng Mapagkukunan",
                                                    "청소행정과": "Departamento ng Administrasyon ng Kalinisan",
                                                    "환경위생과": "Departamento ng Kalinisan ng Kapaligiran",
                                                    "환경과": "Departamento ng Kapaligiran",
                                                    "청소과": "Departamento ng Kalinisan",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "General na basura",
                                                    "음식물쓰레기": "Basura ng pagkain",
                                                    "재활용품": "Mga recyclable",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Mga recyclable (lata, bote, bakal, plastic, karton ng gatas, transparent PET bottles)",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "Mga recyclable (papel, damit, plastic packaging, styrofoam)",
                                                    "소형폐가전": "Maliliit na sirang appliances",
                                                    "불연성폐기물": "Hindi nasusunog na basura",
                                                    "연탄재": "Abo ng uling",
                                                    "소규모건설폐기물(PP전용마대)": "Maliit na basura sa konstruksiyon (PP bags lang)",
                                                    "배출금지": "Bawal itapon",
                                                    
                                                    # 요일 번역
                                                    "일요일": "Linggo",
                                                    "월요일": "Lunes",
                                                    "화요일": "Martes",
                                                    "수요일": "Miyerkules",
                                                    "목요일": "Huwebes",
                                                    "금요일": "Biyernes",
                                                    "토요일": "Sabado"
                                                },
                                                "id": {
                                                    # 부서명 번역
                                                    "자원순환과": "Departemen Sirkulasi Sumber Daya",
                                                    "청소행정과": "Departemen Administrasi Sanitasi",
                                                    "환경위생과": "Departemen Sanitasi Lingkungan",
                                                    "환경과": "Departemen Lingkungan",
                                                    "청소과": "Departemen Sanitasi",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "Sampah umum",
                                                    "음식물쓰레기": "Sampah makanan",
                                                    "재활용품": "Barang daur ulang",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Barang daur ulang (kaleng, botol, besi bekas, plastik, karton susu, botol PET transparan)",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "Barang daur ulang (kertas, pakaian, kemasan plastik, styrofoam)",
                                                    "소형폐가전": "Elektronik kecil bekas",
                                                    "불연성폐기물": "Sampah tidak mudah terbakar",
                                                    "연탄재": "Abu briket",
                                                    "소규모건설폐기물(PP전용마대)": "Sampah konstruksi kecil (hanya kantong PP)",
                                                    "배출금지": "Dilarang buang",
                                                    
                                                    # 요일 번역
                                                    "일요일": "Minggu",
                                                    "월요일": "Senin",
                                                    "화요일": "Selasa",
                                                    "수요일": "Rabu",
                                                    "목요일": "Kamis",
                                                    "금요일": "Jumat",
                                                    "토요일": "Sabtu"
                                                },
                                                "fr": {
                                                    # 부서명 번역
                                                    "자원순환과": "Département de circulation des ressources",
                                                    "청소행정과": "Département d'administration sanitaire",
                                                    "환경위생과": "Département d'hygiène environnementale",
                                                    "환경과": "Département de l'environnement",
                                                    "청소과": "Département sanitaire",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "Déchets généraux",
                                                    "음식물쓰레기": "Déchets alimentaires",
                                                    "재활용품": "Matières recyclables",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Matières recyclables (canettes, bouteilles, ferraille, plastique, briques de lait, bouteilles PET transparentes)",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "Matières recyclables (papier, vêtements, emballages plastiques, polystyrène)",
                                                    "소형폐가전": "Petits appareils électroniques usagés",
                                                    "불연성폐기물": "Déchets non combustibles",
                                                    "연탄재": "Cendres de briquettes",
                                                    "소규모건설폐기물(PP전용마대)": "Petits déchets de construction (sacs PP uniquement)",
                                                    "배출금지": "Interdiction de jeter",
                                                    
                                                    # 요일 번역
                                                    "일요일": "Dimanche",
                                                    "월요일": "Lundi",
                                                    "화요일": "Mardi",
                                                    "수요일": "Mercredi",
                                                    "목요일": "Jeudi",
                                                    "금요일": "Vendredi",
                                                    "토요일": "Samedi"
                                                },
                                                "de": {
                                                    # 부서명 번역
                                                    "자원순환과": "Abteilung für Ressourcenkreislauf",
                                                    "청소행정과": "Abteilung für Sanitärverwaltung",
                                                    "환경위생과": "Abteilung für Umwelthygiene",
                                                    "환경과": "Umweltabteilung",
                                                    "청소과": "Sanitärabteilung",
                                                    
                                                    # 배출 품목 번역
                                                    "일반쓰레기": "Allgemeiner Abfall",
                                                    "음식물쓰레기": "Lebensmittelabfall",
                                                    "재활용품": "Recycelbare Materialien",
                                                    "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Recycelbare Materialien (Dosen, Flaschen, Schrott, Kunststoff, Milchkartons, durchsichtige PET-Flaschen)",
                                                    "재활용품(종이,의류,비닐포장재,스치로폼류)": "Recycelbare Materialien (Papier, Kleidung, Kunststoffverpackungen, Styropor)",
                                                    "소형폐가전": "Kleine Elektroaltgeräte",
                                                    "불연성폐기물": "Nicht brennbarer Abfall",
                                                    "연탄재": "Brikettkohle-Asche",
                                                    "소규모건설폐기물(PP전용마대)": "Kleine Bauabfälle (nur PP-Säcke)",
                                                    "배출금지": "Entsorgung verboten",
                                                    
                                                    # 요일 번역
                                                    "일요일": "Sonntag",
                                                    "월요일": "Montag",
                                                    "화요일": "Dienstag",
                                                    "수요일": "Mittwoch",
                                                    "목요일": "Donnerstag",
                                                    "금요일": "Freitag",
                                                    "토요일": "Samstag"
                                                }
                                            }
                                            
                                            # 쓰레기 배출 정보를 구성 (다국어 번역 적용)
                                            response_lines = [current_labels["title"]]
                                            response_lines.append("")
                                            
                                            # 담당부서명 번역
                                            dept_name = translate_waste_text(district_info.get('담당부서', ''), target_lang)
                                            response_lines.append(f"{current_labels['department']}: {dept_name} ({district_info.get('연락처', '')})")
                                            response_lines.append(f"{current_labels['time']}: {district_info.get('배출시간', '')}")
                                            response_lines.append(f"{current_labels['place']}: {district_info.get('배출장소', '')}")
                                            response_lines.append("")
                                            
                                            # 배출요일 정보
                                            if '배출요일' in district_info:
                                                response_lines.append(current_labels["schedule"])
                                                for day, items in district_info['배출요일'].items():
                                                    translated_day = translate_waste_text(day, target_lang)
                                                    if items and items != ["배출금지"]:
                                                        # 배출 품목들 번역
                                                        translated_items = [translate_waste_text(item, target_lang) for item in items]
                                                        response_lines.append(f"• {translated_day}: {', '.join(translated_items)}")
                                                    elif items == ["배출금지"]:
                                                        response_lines.append(f"• {translated_day}: {current_labels['no_disposal']}")
                                                response_lines.append("")
                                            
                                            # 종량제봉투 가격 정보
                                            if '종량제봉투_가격' in district_info:
                                                response_lines.append(current_labels["price"])
                                                for size, price in district_info['종량제봉투_가격'].items():
                                                    response_lines.append(f"• {size}: {price:,}{current_labels['won']}")
                                                response_lines.append("")
                                            
                                            # 특이사항
                                            if '특이사항' in district_info and district_info['특이사항']:
                                                response_lines.append(current_labels["notes"])
                                                for item in district_info['특이사항']:
                                                    response_lines.append(f"• {item}")
                                                response_lines.append("")
                                            
                                            # 대형폐기물 정보
                                            if '대형폐기물_수거업체' in district_info and district_info['대형폐기물_수거업체']:
                                                response_lines.append(current_labels["large_waste"])
                                                for company in district_info['대형폐기물_수거업체']:
                                                    response_lines.append(f"• {company.get('업체명', '')}: {company.get('연락처', '')}")
                                                    if company.get('신고방법'):
                                                        response_lines.append(f"  {current_labels['report_method']}: {company.get('신고방법', '')}")
                                            
                                            result = "\n".join(response_lines)
                                            print(f"구별 쓰레기 처리 정보 제공 완료: {len(result)} 문자")
                                            return result
                                        else:
                                            # 다국어 오류 메시지
                                            error_messages = {
                                                "ko": f"{district}의 쓰레기 처리 정보가 데이터에 없습니다. 해당 구청에 직접 문의해 주세요.",
                                                "en": f"Waste disposal information for {district} is not available in the data. Please contact the district office directly.",
                                                "vi": f"Thông tin xử lý rác thải của {district} không có trong dữ liệu. Vui lòng liên hệ trực tiếp với văn phòng quận.",
                                                "zh": f"{district}的垃圾处理信息在数据中不可用。请直接联系区政府。",
                                                "ja": f"{district}のゴミ処理情報はデータにありません。該当区役所に直接お問い合わせください。",
                                                "th": f"ข้อมูลการจัดการขยะของ{district}ไม่มีในฐานข้อมูล กรุณาติดต่อสำนักงานเขตโดยตรง",
                                                "id": f"Informasi pembuangan limbah untuk {district} tidak tersedia dalam data. Silakan hubungi kantor distrik secara langsung.",
                                                "tl": f"Ang impormasyon ng pagtatapon ng basura para sa {district} ay hindi available sa data. Mangyaring makipag-ugnayan sa district office nang direkta.",
                                                "fr": f"Les informations sur l'élimination des déchets pour {district} ne sont pas disponibles dans les données. Veuillez contacter directement le bureau du district.",
                                                "de": f"Informationen zur Abfallentsorgung für {district} sind in den Daten nicht verfügbar. Bitte wenden Sie sich direkt an das Bezirksamt.",
                                                "tw": f"{district}的垃圾處理資訊在資料中不可用。請直接聯繫區政府。"
                                            }
                                            return error_messages.get(target_lang, error_messages["ko"])
                                    else:
                                        print("부산광역시_쓰레기처리정보.json 파일이 없습니다.")
                                        # 다국어 오류 메시지
                                        error_messages = {
                                            "ko": "쓰레기 처리 정보 파일을 찾을 수 없습니다.",
                                            "en": "Waste disposal information file could not be found.",
                                            "vi": "Không thể tìm thấy tệp thông tin xử lý rác thải.",
                                            "zh": "找不到垃圾处理信息文件。",
                                            "ja": "ゴミ処理情報ファイルが見つかりませんでした。",
                                            "th": "ไม่พบไฟล์ข้อมูลการจัดการขยะ",
                                            "id": "File informasi pembuangan limbah tidak dapat ditemukan.",
                                            "tl": "Hindi nahanap ang file ng impormasyon ng pagtatapon ng basura.",
                                            "fr": "Le fichier d'informations sur l'élimination des déchets n'a pas pu être trouvé.",
                                            "de": "Die Informationsdatei zur Abfallentsorgung konnte nicht gefunden werden.",
                                            "tw": "找不到垃圾處理資訊檔案。"
                                        }
                                        return error_messages.get(target_lang, error_messages["ko"])
                                except Exception as json_error:
                                    print(f"JSON 파일 읽기 오류: {json_error}")
                                    # 다국어 오류 메시지
                                    error_messages = {
                                        "ko": "쓰레기 처리 정보를 읽는 중 오류가 발생했습니다.",
                                        "en": "An error occurred while reading waste disposal information.",
                                        "vi": "Đã xảy ra lỗi khi đọc thông tin xử lý rác thải.",
                                        "zh": "读取垃圾处理信息时发生错误。",
                                        "ja": "ゴミ処理情報の読み取り中にエラーが発生しました。",
                                        "th": "เกิดข้อผิดพลาดขณะอ่านข้อมูลการจัดการขยะ",
                                        "id": "Terjadi kesalahan saat membaca informasi pembuangan limbah.",
                                        "tl": "Nagkaroon ng error habang binabasa ang impormasyon ng pagtatapon ng basura.",
                                        "fr": "Une erreur s'est produite lors de la lecture des informations sur l'élimination des déchets.",
                                        "de": "Beim Lesen der Abfallentsorgungsinformationen ist ein Fehler aufgetreten.",
                                        "tw": "讀取垃圾處理資訊時發生錯誤。"
                                    }
                                    return error_messages.get(target_lang, error_messages["ko"])
                            else:
                                # 구군명이 없으면 구군 선택 요청
                                return get_district_selection_prompt(target_lang)
                        
                        # 쓰레기 처리 관련이 아니면 기존 RAG 처리
                        # LangGraph RAG 사용 (개선된 답변 품질)
                        result = answer_with_langgraph_rag(query, vector_db_multicultural, GEMINI_API_KEY, target_lang=target_lang)
                        print(f"LangGraph RAG 답변 생성 완료: {len(result)} 문자")
                        return result
                    except Exception as e:
                        print(f"다문화 가족 RAG 오류: {e}")
                        import traceback
                        traceback.print_exc()
                        # 다국어 오류 메시지
                        error_messages = {
                            "ko": "죄송합니다. 다문화 가족 한국생활 안내 정보를 찾을 수 없습니다.",
                            "en": "Sorry, multicultural family life guidance information could not be found.",
                            "vi": "Xin lỗi, không thể tìm thấy thông tin hướng dẫn cuộc sống cho gia đình đa văn hóa.",
                            "zh": "抱歉，找不到多文化家庭生活指导信息。",
                            "ja": "申し訳ございません。多文化家族の韓国生活案内情報が見つかりませんでした。",
                            "th": "ขออภัย ไม่พบข้อมูลคำแนะนำการใช้ชีวิตสำหรับครอบครัวพหุวัฒนธรรม",
                            "id": "Maaf, informasi panduan hidup keluarga multikultural tidak dapat ditemukan.",
                            "tl": "Paumanhin, hindi nahanap ang impormasyon ng gabay sa pamumuhay para sa multicultural family.",
                            "fr": "Désolé, les informations de guide de vie pour les familles multiculturelles n'ont pas pu être trouvées.",
                            "de": "Entschuldigung, Informationen zum Lebensleitfaden für multikulturelle Familien konnten nicht gefunden werden.",
                            "tw": "抱歉，找不到多文化家庭生活指導資訊。"
                        }
                        return error_messages.get(target_lang, error_messages["ko"])
                
                page.views.append(ChatRoomPage(
                    page,
                    room_id=room_id,
                    room_title=room_title,
                    user_lang=user_lang,
                    target_lang=target_lang,
                    on_back=lambda e: go_home(lang),
                    on_share=on_share_clicked,
                    custom_translate_message=multicultural_rag_answer,
                    firebase_available=FIREBASE_AVAILABLE
                ))
            else:
                page.views.append(ChatRoomPage(
                    page, 
                    room_id=room_id, 
                    room_title=room_title, 
                    user_lang=user_lang, 
                    target_lang=target_lang,
                    on_back=lambda e: go_home(lang),
                    on_share=on_share_clicked,
                    firebase_available=FIREBASE_AVAILABLE
                ))
            page.go(f"/chat/{room_id}")
        def on_share_clicked(e):
            print(f"--- DEBUG: 공유 버튼 클릭됨 ---")
            show_qr_dialog(room_id, room_title)
        if not (page.session.get("nickname") or ""):
            # 닉네임 입력 화면 다국어 지원
            texts = NICKNAME_TEXTS.get(lang, NICKNAME_TEXTS["ko"])
            nickname_value = ""
            char_count = ft.Text(f"0/12", size=12, color=get_sub_text_color(page))
            nickname_field = ft.TextField(label=texts["label"], hint_text=texts["hint"], on_change=None, max_length=12, width=320)
            enter_button = ft.ElevatedButton(texts["enter"], disabled=True, width=320)
            def on_nickname_change(e):
                value = nickname_field.value.strip()
                char_count.value = f"{len(value)}/12"
                enter_button.disabled = not (2 <= len(value) <= 12)
                page.update()
            nickname_field.on_change = on_nickname_change
            def on_nickname_submit(e=None):
                nickname = nickname_field.value.strip()
                if 2 <= len(nickname) <= 12:
                    after_nickname(nickname)
            enter_button.on_click = on_nickname_submit
            page.views.clear()
            page.views.append(
                ft.View(
                    "/nickname",
                    controls=[
                        ft.Row([
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: go_home(lang)),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.PERSON, color="#22C55E", size=28),
                                        bgcolor="#22C55E22", border_radius=12, padding=8, margin=ft.margin.only(right=8)
                                    ),
                                    ft.Text(texts["title"], size=22, weight=ft.FontWeight.BOLD, color=get_text_color(page)),
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            ),
                        ], alignment=ft.MainAxisAlignment.START, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(texts["desc"], size=14, color=get_sub_text_color(page), text_align="center"),
                                ft.Container(height=8),
                                ft.Text(texts["label"], size=14, weight=ft.FontWeight.W_500),
                        nickname_field,
                                ft.Row([
                                    char_count
                                ], alignment=ft.MainAxisAlignment.END),
                                ft.Container(height=8),
                                enter_button,
                                ft.Container(height=8),
                                ft.ElevatedButton(texts["back"], on_click=lambda e: go_home(lang), width=320, style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_200, color=ft.Colors.BLACK)),
                            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=40,
                            bgcolor=get_card_bg_color(page),
                            border_radius=20,
                            shadow=ft.BoxShadow(blur_radius=24, color="#B0BEC544"),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(top=32),
                            width=400,
                        ),
                    ],
                    bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    vertical_alignment=ft.MainAxisAlignment.CENTER
                )
            )
            page.update()
            return
        else:
            after_nickname(page.session.get("nickname") or "")

    # --- 외국인 근로자 권리구제 RAG 채팅방 진입 함수 ---
    def go_foreign_worker_rag_chat(lang):
        # 고유 방 ID 및 타이틀
        room_id = "foreign_worker_rights_rag"
        # 언어별 채팅방 제목 설정
        room_title = FOREIGN_WORKER_ROOM_CARD_TEXTS.get(lang, FOREIGN_WORKER_ROOM_CARD_TEXTS["ko"])["title"]
        # 채팅방 진입 (is_foreign_worker_rag=True로 설정)
        # 대만 사용자의 경우 답변 언어를 대만어로 설정
        target_lang = "zh-TW" if lang == "zh-TW" else lang
        go_chat(lang, target_lang, room_id, room_title, is_rag=False, is_foreign_worker_rag=True)

    # --- 부산 맛집 검색 RAG 채팅방 진입 함수 ---
    def go_busan_food_rag_chat(lang):
        # 고유 방 ID 및 타이틀
        room_id = "busan_food_search_rag"
        room_title = BUSAN_FOOD_ROOM_CARD_TEXTS.get(lang, BUSAN_FOOD_ROOM_CARD_TEXTS["ko"])["title"]
        
        # 대만 사용자의 경우 답변 언어를 대만어로 설정
        target_lang = "zh-TW" if lang == "zh-TW" else lang
        
        # 채팅방 진입 (is_busan_food_rag=True로 설정)
        go_chat(lang, target_lang, room_id, room_title, is_rag=False, is_foreign_worker_rag=False, is_busan_food_rag=True)

    # --- MBTI 관광지 추천 페이지 진입 함수 ---
    def go_mbti_tourism(lang):
        # 원래 Flet 방식으로 MBTI 관광지 추천 페이지 이동
        print(f"MBTI 관광지 추천 페이지로 이동 (언어: {lang})")
        page.views.clear()
        page.views.append(MBTITourismPage(page, lang, on_back=lambda e: go_home(lang), selected_mbti_value=None, result_view_value=None))
        page.go("/mbti_tourism")

    # --- 라우팅 처리 ---
    def route_change(route):
        print(f"Route: {page.route}")
        parts = page.route.split('/')
        
        try:
            if page.route == "/":
                go_nationality()
            elif page.route == "/home":
                go_home(lang)
            elif page.route == "/create_room":
                go_create(lang)
            elif page.route == "/mbti_tourism":
                go_mbti_tourism(lang)
            elif page.route.startswith("/join_room/"):
                room_id = parts[2]
                print(f"QR코드로 방 참여 시도: {room_id}")
                # QR코드로 참여 시, Firebase에서 방 정보를 가져옵니다.
                go_chat_from_list(room_id)
            # 다른 라우트 핸들링...
            page.update()
        except Exception as e:
            print(f"라우팅 처리 중 오류: {e}")
            # 오류 발생 시 홈으로 리다이렉트
            page.snack_bar = ft.SnackBar(
                content=ft.Text("페이지 로딩 중 오류가 발생했습니다."),
                duration=2000
            )
            page.snack_bar.open = True
            page.update()
            go_home(lang)

    page.on_route_change = route_change
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main, port=8018, view=ft.WEB_BROWSER)
