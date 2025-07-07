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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://pychat-25c45-default-rtdb.asia-southeast1.firebasedatabase.app/")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")
''')

import flet as ft
from flet_webview import WebView
from pages.nationality_select import NationalitySelectPage
from pages.home import HomePage
from pages.create_room import CreateRoomPage
from pages.room_list import RoomListPage
from pages.chat_room import ChatRoomPage
from pages.foreign_country_select import ForeignCountrySelectPage
import openai
from config import OPENAI_API_KEY, MODEL_NAME, FIREBASE_DB_URL, FIREBASE_KEY_PATH
import uuid
import qrcode
import io
import base64
import geocoder
import time
import firebase_admin
from firebase_admin import credentials, db
from rag_utils import get_or_create_vector_db, answer_with_rag, answer_with_rag_foreign_worker
from rag_utils import SimpleVectorDB, OpenAIEmbeddings


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
        print("❌ FIREBASE_DB_URL이 설정되지 않았습니다.")
        raise Exception("FIREBASE_DB_URL is not set")
    
    if not os.path.exists(FIREBASE_KEY_PATH):
        print(f"❌ Firebase 키 파일이 존재하지 않습니다: {FIREBASE_KEY_PATH}")
        raise Exception(f"Firebase key file not found: {FIREBASE_KEY_PATH}")
    
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })
    FIREBASE_AVAILABLE = True
    print("✅ Firebase 초기화 성공")
except Exception as e:
    print(f"❌ Firebase 초기화 실패: {e}")
    print("⚠️ Firebase 기능이 비활성화됩니다. 채팅방 생성 및 메시지 저장이 불가능합니다.")
    FIREBASE_AVAILABLE = False

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# RAG용 벡터DB 준비 (무조건 병합본만 사용)
print("RAG 벡터DB 준비 중...")
VECTOR_DB_MERGED_PATH = "vector_db_merged.pkl"
vector_db = None

try:
    if os.path.exists(VECTOR_DB_MERGED_PATH):
        print("기존 벡터DB 파일을 로드합니다...")
        with open(VECTOR_DB_MERGED_PATH, "rb") as f:
            vector_db = pickle.load(f)
        # 임베딩 객체 다시 생성
        vector_db.embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
        print("기존 병합 벡터DB 로드 완료!")
    else:
        print("벡터DB 파일이 없습니다.")
        print("RAG 기능이 비활성화됩니다.")
except Exception as e:
    print(f"벡터DB 로드 중 오류 발생: {e}")
    if "langchain" in str(e).lower():
        print("langchain 의존성 오류로 인해 기존 벡터DB를 변환합니다...")
        try:
            # 기존 벡터DB 파일을 백업
            backup_path = VECTOR_DB_MERGED_PATH + ".backup"
            if os.path.exists(VECTOR_DB_MERGED_PATH):
                shutil.copy2(VECTOR_DB_MERGED_PATH, backup_path)
                print(f"기존 벡터DB 백업 완료: {backup_path}")
            
            # 기존 벡터DB에서 데이터 추출
            with open(VECTOR_DB_MERGED_PATH, 'rb') as f:
                old_db = pickle.load(f)
            
            print("기존 벡터DB에서 데이터 추출 중...")
            
            # 기존 벡터DB에서 문서 추출
            documents = []
            if hasattr(old_db, 'documents'):
                documents = old_db.documents
                print(f"기존 문서 수: {len(documents)}")
            elif hasattr(old_db, 'docstore') and hasattr(old_db.docstore, '_dict'):
                # ChromaDB 형식에서 문서 추출
                for doc_id, doc in old_db.docstore._dict.items():
                    if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                        documents.append({
                            'page_content': doc.page_content,
                            'metadata': doc.metadata
                        })
                print(f"추출된 문서 수: {len(documents)}")
            
            if documents:
                # 새로운 임베딩 생성
                from rag_utils import SimpleVectorDB
                embeddings = OpenAIEmbeddings(
                    openai_api_key=OPENAI_API_KEY,
                    model="text-embedding-3-small"
                )
                
                # 문서 임베딩 생성
                print("새로운 임베딩 생성 중...")
                doc_embeddings = embeddings.embed_documents([doc['page_content'] for doc in documents])
                
                # SimpleVectorDB 생성
                vector_db = SimpleVectorDB(documents, embeddings, doc_embeddings)
                
                # 새로운 벡터DB 저장
                with open(VECTOR_DB_MERGED_PATH, "wb") as f:
                    pickle.dump(vector_db, f)
                
                # 변환 완료 표시
                with open(VECTOR_DB_MERGED_PATH + ".converted", "w") as f:
                    f.write("converted")
                print("벡터DB 변환 완료!")
            else:
                print("추출할 문서가 없습니다.")
                vector_db = None
                
        except Exception as e2:
            print(f"벡터DB 변환 실패: {e2}")
            vector_db = None
    else:
        print("RAG 기능이 비활성화됩니다.")
        vector_db = None

# RAG 기능 사용 가능 여부 설정 (vector_db 정의 후)
RAG_AVAILABLE = vector_db is not None

print("RAG 벡터DB 준비 완료!")

FIND_ROOM_TEXTS = {
    "ko": {
        "title": "채팅방 찾기 방법을 선택하세요",
        "id": "ID로 찾기",
        "id_desc": "채팅방 ID를 입력하여 참여",
        "qr": "QR코드로 찾기",
        "qr_desc": "QR 코드를 스캔하여 빠른 참여",
        "rag": "다문화가족 한국생활안내",
        "rag_desc": "다문화 가족지원 포털 다누리- 한국생활 안내 자료에 근거한 챗봇"
    },
    "en": {
        "title": "Select a way to find a chat room",
        "id": "Find by ID",
        "id_desc": "Join by entering chat room ID",
        "qr": "Find by QR code",
        "qr_desc": "Quick join by scanning QR code",
        "rag": "Korean Life Guide for Multicultural Families",
        "rag_desc": "Chatbot based on Danuri - Korean Life Guide for Multicultural Families Portal materials"
    },
    "vi": {
        "title": "Chọn cách tìm phòng chat",
        "id": "Tìm bằng ID",
        "id_desc": "Tham gia bằng cách nhập ID phòng chat",
        "qr": "Tìm bằng mã QR",
        "qr_desc": "Tham gia nhanh bằng quét mã QR",
        "rag": "Hướng dẫn cuộc sống Hàn Quốc cho gia đình đa văn hóa",
        "rag_desc": "Chatbot dựa trên tài liệu Hướng dẫn cuộc sống Hàn Quốc của cổng thông tin Danuri cho gia đình đa văn hóa"
    },
    "ja": {
        "title": "チャットルームの探し方を選択してください",
        "id": "IDで探す",
        "id_desc": "IDでチャットルームに参加",
        "qr": "QRコードで探す",
        "qr_desc": "QRコードをスキャンして参加",
        "rag": "多文化家族のための韓国生活ガイド",
        "rag_desc": "多文化家族支援ポータル「ダヌリ」- 韓国生活案内資料に基づくチャットボット"
    },
    "zh": {
        "title": "请选择查找聊天室的方法",
        "id": "通过ID查找",
        "id_desc": "通过输入聊天室ID加入",
        "qr": "通过二维码查找",
        "qr_desc": "扫描二维码快速加入",
        "rag": "多文化家庭韩国生活指南",
        "rag_desc": "基于多文化家庭支援门户Danuri-韩国生活指南资料的聊天机器人"
    },
    "fr": {
        "title": "Sélectionnez une méthode pour trouver un salon de discussion",
        "id": "Rechercher par ID",
        "id_desc": "Rejoindre en entrant l'ID de la salle de discussion",
        "qr": "Rechercher par QR code",
        "qr_desc": "Rejoindre rapidement en scanant le code QR",
        "rag": "Guide de la vie en Corée pour les familles multiculturelles",
        "rag_desc": "Chatbot basé sur le portail Danuri - Guide de la vie en Corée pour les familles multiculturelles"
    },
    "de": {
        "title": "Wählen Sie eine Methode, um einen Chatraum zu finden",
        "id": "Nach ID suchen",
        "id_desc": "Beitreten, indem Sie die Chatraum-ID eingeben",
        "qr": "Mit QR-Code suchen",
        "qr_desc": "Schnell beitreten, indem Sie den QR-Code scannen",
        "rag": "Koreanischer Lebensratgeber für multikulturelle Familien",
        "rag_desc": "Chatbot basierend auf dem Danuri-Portal - Koreanischer Lebensratgeber für multikulturelle Familien"
    },
    "th": {
        "title": "เลือกวิธีค้นหาห้องแชท",
        "id": "ค้นหาด้วย ID",
        "id_desc": "เข้าร่วมโดยการป้อน IDห้องแชท",
        "qr": "ค้นหาด้วย QR โค้ด",
        "qr_desc": "เข้าร่วมอย่างรวดเร็วโดยสแกน QR โค้ด",
        "rag": "คู่มือการใช้ชีวิตในเกาหลีสำหรับครอบครัวพหุวัฒนธรรม",
        "rag_desc": "แชทบอทอ้างอิงจากข้อมูลคู่มือการใช้ชีวิตในเกาหลีของพอร์ทัล Danuri สำหรับครอบครัวพหุวัฒนธรรม"
    },
    "zh-TW": {
        "title": "請選擇查找聊天室的方法",
        "id": "通過ID查找",
        "id_desc": "輸入聊天室ID參加",
        "qr": "通過二維碼查找",
        "qr_desc": "掃描二維碼快速參加",
        "rag": "多元文化家庭韓國生活指南",
        "rag_desc": "基於多元文化家庭支援門戶Danuri-韓國生活指南資料的聊天機器人"
    },
    "id": {
        "title": "Pilih cara menemukan ruang obrolan",
        "id": "Cari dengan ID",
        "id_desc": "Gabung dengan memasukkan ID ruang obrolan",
        "qr": "Cari dengan kode QR",
        "qr_desc": "Gabung cepat dengan memindai kode QR",
        "rag": "Panduan Hidup di Korea untuk Keluarga Multikultural",
        "rag_desc": "Chatbot berdasarkan portal Danuri - Panduan Hidup di Korea untuk Keluarga Multikultural"
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
}

# QR 코드 공유 다국어 텍스트 사전 추가
QR_SHARE_TEXTS = {
    "ko": {
        "title": "방 '{room}' 공유",
        "desc": "다른 사용자가 QR코드를 스캔하면 이 방으로 바로 참여할 수 있습니다.",
        "room_id": "방 ID: {id}",
        "close": "닫기"
    },
    "en": {
        "title": "Share room '{room}'",
        "desc": "Other users can join this room by scanning the QR code.",
        "room_id": "Room ID: {id}",
        "close": "Close"
    },
    "ja": {
        "title": "ルーム『{room}』を共有",
        "desc": "他のユーザーがQRコードをスキャンするとこのルームに参加できます。",
        "room_id": "ルームID: {id}",
        "close": "閉じる"
    },
    "zh": {
        "title": "分享房间'{room}'",
        "desc": "其他用户扫描二维码即可加入此房间。",
        "room_id": "房间ID: {id}",
        "close": "关闭"
    },
    "zh-TW": {
        "title": "分享房間「{room}」",
        "desc": "其他用戶掃描 QR 碼即可加入此房間。",
        "room_id": "房間ID: {id}",
        "close": "關閉"
    },
    "id": {
        "title": "Bagikan ruang '{room}'",
        "desc": "Pengguna lain dapat bergabung dengan memindai kode QR ini.",
        "room_id": "ID Ruang: {id}",
        "close": "Tutup"
    },
    "fr": {
        "title": "Partager la salle '{room}'",
        "desc": "D'autres utilisateurs peuvent rejoindre cette salle en scannant le QR code.",
        "room_id": "ID de la salle : {id}",
        "close": "Fermer"
    },
    "de": {
        "title": "Raum '{room}' teilen",
        "desc": "Andere Nutzer können diesem Raum per QR-Code beitreten.",
        "room_id": "Raum-ID: {id}",
        "close": "Schließen"
    },
    "th": {
        "title": "แชร์ห้อง '{room}'",
        "desc": "ผู้ใช้อื่นสามารถเข้าร่วมห้องนี้ได้โดยสแกน QR โค้ด",
        "room_id": "รหัสห้อง: {id}",
        "close": "ปิด"
    },
    "vi": {
        "title": "Chia sẻ phòng '{room}'",
        "desc": "Người khác có thể tham gia phòng này bằng cách quét mã QR.",
        "room_id": "ID phòng: {id}",
        "close": "Đóng"
    }
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
    "ur": {"title": "غیر ملکی مزدوروں کے حقوق کا تحفظ", "desc": "غیر ملکی مزدوروں کے حقوق کی گائیڈ بک پر مبنی RAG چیٹ بوٹ"}
}

def main(page: ft.Page):
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
        "NotoSansKR": "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap",
        "NotoEmoji": "https://fonts.googleapis.com/css2?family=Noto+Emoji&display=swap"
    }
    page.theme = ft.Theme(font_family="NotoSansKR")
    
    # --- QR 코드 관련 함수 (Container를 직접 오버레이) ---
    def show_qr_dialog(room_id, room_title):
        print(f"--- DEBUG: QR 코드 다이얼로그 생성 (Container 방식) ---")
        # 다국어 텍스트 적용
        texts = QR_SHARE_TEXTS.get(lang, QR_SHARE_TEXTS["ko"])
        def close_dialog(e):
            if page.overlay:
                page.overlay.pop()
                page.update()
        # QR코드에 전체 URL이 들어가도록 수정
        qr_data = f"{BASE_URL}/join_room/{room_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        qr_code_image = ft.Image(src_base64=img_str, width=250, height=250)
        popup_content = ft.Container(
            content=ft.Column([
                ft.Text(texts["title"].format(room=room_title), size=20, weight=ft.FontWeight.BOLD),
                ft.Text(texts["desc"], text_align="center"),
                qr_code_image,
                ft.Text(texts["room_id"].format(id=room_id)),
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

    def handle_create_room(room_title, target_lang):
        if not room_title:
            room_title = "새로운 채팅방"
        if not target_lang:
            target_lang = "en"
            print("상대방 언어가 선택되지 않아 기본값(en)으로 설정합니다.")

        new_room_id = uuid.uuid4().hex[:8]
        
        # Firebase 사용 가능 여부 확인
        if not FIREBASE_AVAILABLE:
            print("❌ Firebase가 초기화되지 않아 방을 생성할 수 없습니다.")
            # 사용자에게 오류 메시지 표시 (간단한 팝업)
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Firebase 연결 오류로 방을 생성할 수 없습니다. 설정을 확인해주세요."),
                    action="확인"
                )
            )
            return
        
        # Firebase에 방 정보 저장
        try:
            rooms_ref = db.reference('/rooms')
            rooms_ref.child(new_room_id).set({
                'id': new_room_id,
                'title': room_title,
                'user_lang': lang,
                'target_lang': target_lang,
                'created_at': int(time.time() * 1000)
            })
            print(f"✅ Firebase에 방 '{room_title}' 정보 저장 성공")
        except Exception as e:
            print(f"❌ Firebase 방 정보 저장 실패: {e}")
            # 사용자에게 오류 메시지 표시
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("방 생성 중 오류가 발생했습니다. 다시 시도해주세요."),
                    action="확인"
                )
            )
            return

        print(f"방 '{room_title}' 생성됨 (ID: {new_room_id}, 내 언어: {lang}, 상대 언어: {target_lang})")
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
            on_quick=lambda e: handle_create_room("빠른 채팅방", lang),
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
        def on_find_by_qr(e):
            go_find_by_qr(lang)
        texts = FIND_ROOM_TEXTS.get(lang, FIND_ROOM_TEXTS["ko"])
        page.views.clear()
        # 사용자별 고유 RAG 방 ID 생성 (UUID 사용)
        user_id = page.session.get("user_id")
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
                        ft.Text(texts["title"], size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
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
                                        ft.Text(texts["id"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                        ft.Text(texts["id_desc"], size=12, color=ft.Colors.GREY_600)
                                    ], spacing=2)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.WHITE,
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                on_click=on_find_by_id
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.QR_CODE, color="#A259FF", size=28),
                                        bgcolor="#F3E8FF", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(texts["qr"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                        ft.Text(texts["qr_desc"], size=12, color=ft.Colors.GREY_600)
                                    ], spacing=2)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.WHITE,
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                on_click=on_find_by_qr
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.TABLE_CHART, color="#22C55E", size=28),
                                        bgcolor="#DCFCE7", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(texts["rag"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                        ft.Text(texts["rag_desc"], size=12, color=ft.Colors.GREY_600)
                                    ], spacing=2)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.WHITE,
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                margin=ft.margin.only(bottom=16),
                                on_click=lambda e: go_chat(lang, lang, user_rag_room_id, RAG_ROOM_TITLE, is_rag=True)
                            ),
                            # --- 외국인 근로자 권리구제 버튼 추가 ---
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.GAVEL, color="#F59E42", size=28),
                                        bgcolor="#FFF7E6", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(FOREIGN_WORKER_ROOM_CARD_TEXTS.get(lang, FOREIGN_WORKER_ROOM_CARD_TEXTS["ko"])["title"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                        ft.Text(FOREIGN_WORKER_ROOM_CARD_TEXTS.get(lang, FOREIGN_WORKER_ROOM_CARD_TEXTS["ko"])["desc"], size=12, color=ft.Colors.GREY_600)
                                    ], spacing=2)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.WHITE,
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                margin=ft.margin.only(bottom=16),
                                on_click=lambda e: go_foreign_worker_rag_chat(lang)
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
                bgcolor=ft.Colors.WHITE,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                vertical_alignment=ft.MainAxisAlignment.CENTER
            )
        )
        page.go("/find_by_id")

    def go_find_by_qr(lang):
        def on_message(e):
            qr_text = e.data  # JS에서 전달된 QR코드 텍스트
            # QR코드에서 방 ID 추출
            if "/join_room/" in qr_text:
                room_id = qr_text.split("/join_room/")[-1].split("/")[0]
            else:
                room_id = qr_text
            if room_id:
                go_chat_from_list(room_id)

        def on_manual_input(e):
            manual_room_id = manual_input_field.value.strip()
            if manual_room_id:
                # URL에서 방 ID 추출
                if "/join_room/" in manual_room_id:
                    room_id = manual_room_id.split("/join_room/")[-1].split("/")[0]
                else:
                    room_id = manual_room_id
                go_chat_from_list(room_id)

        # 다국어 텍스트 사전
        FIND_BY_QR_TEXTS = {
            "ko": {"title": "QR 코드 스캔", "desc": "QR 코드를 스캔하거나 내용을 직접 입력하세요", "label": "QR 코드 내용을 직접 입력하세요", "enter": "입력한 내용으로 입장", "tip": "💡 팁: QR 코드를 스캔할 수 없는 경우,\n위 입력창에 QR 코드 내용을 복사해서 붙여넣으세요.", "back": "뒤로가기"},
            "en": {"title": "Scan QR Code", "desc": "Scan the QR code or enter the content manually", "label": "Enter QR code content", "enter": "Enter with input", "tip": "💡 Tip: If you can't scan the QR code,\npaste the QR code content into the input box above.", "back": "Back"},
            "ja": {"title": "QRコードスキャン", "desc": "QRコードをスキャンするか内容を直接入力してください", "label": "QRコード内容を直接入力してください", "enter": "入力内容で入室", "tip": "💡 ヒント: QRコードをスキャンできない場合、\n上の入力欄にQRコード内容を貼り付けてください。", "back": "戻る"},
            "zh": {"title": "扫描二维码", "desc": "扫描二维码或手动输入内容", "label": "请直接输入二维码内容", "enter": "用输入内容进入", "tip": "💡 提示：如果无法扫描二维码，\n请将二维码内容粘贴到上方输入框。", "back": "返回"},
            "zh-TW": {"title": "掃描二維碼", "desc": "掃描二維碼或手動輸入內容", "label": "請直接輸入二維碼內容", "enter": "用輸入內容進入", "tip": "💡 提示：若無法掃描二維碼，\n請將二維碼內容貼到上方輸入框。", "back": "返回"},
            "id": {"title": "Pindai Kode QR", "desc": "Pindai kode QR atau masukkan isinya secara manual", "label": "Masukkan isi kode QR", "enter": "Masuk dengan input", "tip": "💡 Tips: Jika tidak dapat memindai kode QR,\ntempelkan isi kode QR ke kotak input di atas.", "back": "Kembali"},
            "vi": {"title": "Quét mã QR", "desc": "Quét mã QR hoặc nhập nội dung thủ công", "label": "Nhập nội dung mã QR", "enter": "Vào bằng nội dung nhập", "tip": "💡 Mẹo: Nếu không quét được mã QR,\ndán nội dung mã QR vào ô nhập phía trên.", "back": "Quay lại"},
            "fr": {"title": "Scanner le code QR", "desc": "Scannez le code QR ou saisissez le contenu manuellement", "label": "Saisissez le contenu du code QR", "enter": "Entrer avec le contenu saisi", "tip": "💡 Astuce : Si vous ne pouvez pas scanner le code QR,\ncollez le contenu du code QR dans la zone de saisie ci-dessus.", "back": "Retour"},
            "de": {"title": "QR-Code scannen", "desc": "Scannen Sie den QR-Code oder geben Sie den Inhalt manuell ein", "label": "Geben Sie den QR-Code-Inhalt ein", "enter": "Mit Eingabe beitreten", "tip": "💡 Tipp: Wenn Sie den QR-Code nicht scannen können,\nfügen Sie den QR-Code-Inhalt in das obige Eingabefeld ein.", "back": "Zurück"},
            "th": {"title": "สแกนคิวอาร์โค้ด", "desc": "สแกนคิวอาร์โค้ดหรือกรอกเนื้อหาด้วยตนเอง", "label": "กรอกเนื้อหาคิวอาร์โค้ด", "enter": "เข้าร่วมด้วยเนื้อหาที่กรอก", "tip": "💡 เคล็ดลับ: หากสแกนคิวอาร์โค้ดไม่ได้\nให้นำเนื้อหาคิวอาร์โค้ดไปวางในช่องกรอกด้านบน", "back": "ย้อนกลับ"},
        }
        t = FIND_BY_QR_TEXTS.get(lang, FIND_BY_QR_TEXTS["en"])
        manual_input_field = ft.TextField(
            label=t["label"],
            hint_text=t["label"],
            width=350,
            on_submit=on_manual_input
        )

        # 안내 메시지와 수동 입력 옵션 제공
        page.views.clear()
        page.views.append(
            ft.View(
                "/find_by_qr",
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(
                                name=ft.Icons.QR_CODE,
                                size=64,
                                color=ft.Colors.BLUE_500
                            ),
                            ft.Text(
                                t["title"],
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                t["desc"],
                                size=14,
                                color=ft.Colors.GREY_600,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Container(height=20),
                            manual_input_field,
                            ft.ElevatedButton(
                                t["enter"],
                                on_click=on_manual_input,
                                width=350
                            ),
                            ft.Container(height=20),
                            ft.Text(
                                t["tip"],
                                size=12,
                                color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=32,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=20,
                        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK12),
                    ),
                    ft.ElevatedButton(t["back"], on_click=lambda e: go_room_list(lang), width=350)
                ],
                bgcolor=ft.Colors.WHITE,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                vertical_alignment=ft.MainAxisAlignment.CENTER
            )
        )
        page.go("/find_by_qr")

    def go_chat_from_list(room_id):
        # RAG 채팅방인지 확인 (공용 RAG_ROOM_ID로 들어오면, 사용자별로 리다이렉트)
        if room_id == RAG_ROOM_ID or room_id.startswith(RAG_ROOM_ID):
            user_id = page.session.get("user_id")
            if not user_id:
                user_id = str(uuid.uuid4())
                page.session.set("user_id", user_id)
            user_rag_room_id = f"{RAG_ROOM_ID}_{user_id}"
            go_chat(lang, lang, user_rag_room_id, RAG_ROOM_TITLE, is_rag=True)
            return
        
        try:
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
        except Exception as e:
            print(f"Firebase에서 방 정보 가져오기 실패: {e}")

    def go_chat(user_lang, target_lang, room_id, room_title="채팅방", is_rag=False, is_foreign_worker_rag=False):
        def after_nickname(nickname):
            page.session.set("nickname", nickname)
            page.views.clear()
            
            # 외국인 근로자 RAG 채팅방인지 확인
            if is_foreign_worker_rag:
                def foreign_worker_rag_answer(query, target_lang):
                    # 다문화 가족 RAG 방과 동일한 방식으로 answer_with_rag 사용
                    # 기존 vector_db를 사용하되, 외국인 근로자 관련 프롬프트 사용
                    try:
                        # 기존 vector_db 사용 (다문화 가족 DB)
                        if vector_db is None:
                            return "죄송합니다. RAG 기능이 현재 사용할 수 없습니다. (벡터DB가 로드되지 않았습니다.)"
                        
                        # 외국인 근로자 관련 프롬프트로 수정된 answer_with_rag 사용 (타겟 언어 전달)
                        return answer_with_rag_foreign_worker(query, vector_db, OPENAI_API_KEY, target_lang=target_lang)
                    except Exception as e:
                        print(f"외국인 근로자 RAG 오류: {e}")
                        return "죄송합니다. 외국인 근로자 권리구제 정보를 찾을 수 없습니다."
                
                page.views.append(ChatRoomPage(
                    page,
                    room_id=room_id,
                    room_title=room_title,
                    user_lang=user_lang,
                    target_lang=target_lang,
                    on_back=lambda e: go_room_list(lang),
                    on_share=on_share_clicked,
                    custom_translate_message=foreign_worker_rag_answer,
                    firebase_available=FIREBASE_AVAILABLE,
                    is_foreign_worker_rag=True
                ))
            # 기존 다문화 가족 RAG 채팅방인지 확인
            elif is_rag:
                def multicultural_rag_answer(query, target_lang):
                    try:
                        import chromadb
                        from create_foreign_worker_db import OpenAIEmbeddingFunction
                        # 다문화 가족 전용 ChromaDB 연결 (기존 vector_db 대신 별도 DB 사용)
                        db_name = "multicultural_family_guide_openai"
                        persist_directory = "./chroma_db"
                        chroma_client = chromadb.PersistentClient(path=persist_directory)
                        embedding_function = OpenAIEmbeddingFunction(OPENAI_API_KEY)
                        collection = chroma_client.get_or_create_collection(
                            name=db_name,
                            embedding_function=embedding_function,
                            metadata={"hnsw:space": "cosine"}
                        )
                        # 쿼리 임베딩 및 유사도 검색
                        results = collection.query(query_texts=[query], n_results=3)
                        docs = results.get("documents", [[]])[0]
                        # 컨텍스트 생성
                        context = "\n\n".join(docs)
                        prompt = f"아래 참고 정보의 내용을 최대한 반영해 자연스럽게 답변하세요. 참고 정보에 없는 내용은 '참고 정보에 없습니다'라고 답하세요.\n\n[참고 정보]\n{context}\n\n질문: {query}\n답변:"
                        # OpenAI 답변 생성
                        client = openai.OpenAI(api_key=OPENAI_API_KEY)
                        response = client.chat.completions.create(
                            model="gpt-4.1-nano-2025-04-14",
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=1000,
                            temperature=0.1
                        )
                        return response.choices[0].message.content.strip()
                    except Exception as e:
                        print(f"다문화 가족 RAG 오류: {e}")
                        return "죄송합니다. 다문화 가족 한국생활 안내 정보를 찾을 수 없습니다."
                
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
        if not page.session.get("nickname"):
            # 닉네임 입력 화면 다국어 지원
            texts = NICKNAME_TEXTS.get(lang, NICKNAME_TEXTS["ko"])
            nickname_value = ""
            char_count = ft.Text(f"0/12", size=12, color=ft.Colors.GREY_600)
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
                                    ft.Text(texts["title"], size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            ),
                        ], alignment=ft.MainAxisAlignment.START, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(texts["desc"], size=14, color=ft.Colors.GREY_600, text_align="center"),
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
                            bgcolor=ft.Colors.WHITE,
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
        room_title = "외국인 근로자 권리구제"
        # 채팅방 진입 (is_foreign_worker_rag=True로 설정)
        go_chat(lang, lang, room_id, room_title, is_rag=False, is_foreign_worker_rag=True)

    # --- 라우팅 처리 ---
    def route_change(route):
        print(f"Route: {page.route}")
        parts = page.route.split('/')
        
        if page.route == "/":
            go_nationality()
        elif page.route == "/home":
            go_home(lang)
        elif page.route == "/create_room":
            go_create(lang)
        elif page.route.startswith("/join_room/"):
            room_id = parts[2]
            # QR코드로 참여 시, Firebase에서 방 정보를 가져옵니다.
            go_chat_from_list(room_id)
        # 다른 라우트 핸들링...
        page.update()

    page.on_route_change = route_change
    page.go(page.route)

ft.app(target=main)
