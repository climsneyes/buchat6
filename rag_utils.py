import os
import hashlib
import json
import pickle
import numpy as np
import re
import google.generativeai as genai
import shutil
from pypdf import PdfReader

# LangGraph 관련 import 추가
try:
    from langgraph.graph import StateGraph, END
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_core.prompts import ChatPromptTemplate
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ LangGraph 관련 라이브러리가 설치되지 않았습니다. 기본 RAG 기능만 사용됩니다.")

PDF_PATH = "pdf/ban.pdf"
VECTOR_DB_PATH = "vector_db.pkl"
CACHE_INFO_PATH = "cache_info.json"

WASTE_INFO_JSON_PATH = "부산광역시_쓰레기처리정보.json"

# 언어 감지 함수
def detect_language(text):
    """텍스트의 언어를 감지합니다."""
    # 한글 패턴
    korean_pattern = re.compile(r'[가-힣]')
    # 영어 패턴
    english_pattern = re.compile(r'[a-zA-Z]')
    # 일본어 패턴 (히라가나, 카타카나)
    japanese_pattern = re.compile(r'[あ-んア-ン]')
    # 중국어 패턴 (간체, 번체)
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    # 베트남어 패턴
    vietnamese_pattern = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]')
    # 프랑스어 패턴
    french_pattern = re.compile(r'[àâäéèêëïîôöùûüÿç]')
    # 독일어 패턴
    german_pattern = re.compile(r'[äöüß]')
    # 태국어 패턴
    thai_pattern = re.compile(r'[\u0e00-\u0e7f]')
    # 타갈로그어(필리핀어) 패턴 - ng, mga, at, sa 등의 일반적인 단어들과 특수문자
    tagalog_pattern = re.compile(r'\b(ng|mga|at|sa|ang|na|ay|para|kung|may|kasi|pero|hindi|oo|naman|din|rin|yung|yun|namin|natin|nila|kayo|tayo|sila|ako|ikaw|siya|mga|masarap|restaurant|pagkain|kumain|lugar)\b', re.IGNORECASE)
    
    text_lower = text.lower()
    
    # 각 언어별 점수 계산 (타갈로그에 가중치 부여)
    tagalog_score = len(tagalog_pattern.findall(text))
    
    # 타갈로그 키워드가 2개 이상 있으면 강제로 타갈로그로 인식
    if tagalog_score >= 2:
        return 'tl'
    
    scores = {
        'ko': len(korean_pattern.findall(text)),
        'en': len(english_pattern.findall(text)),
        'ja': len(japanese_pattern.findall(text)),
        'zh': len(chinese_pattern.findall(text)),
        'vi': len(vietnamese_pattern.findall(text)),
        'fr': len(french_pattern.findall(text)),
        'de': len(german_pattern.findall(text)),
        'th': len(thai_pattern.findall(text)),
        'tl': tagalog_score * 5  # 타갈로그 패턴에 더 높은 가중치 부여
    }
    
    # 가장 높은 점수의 언어 반환
    detected_lang = max(scores, key=scores.get)
    
    # 점수가 0이면 기본값으로 영어 반환
    if scores[detected_lang] == 0:
        return 'en'
    
    return detected_lang

def is_waste_related_query(query):
    """질문이 쓰레기 처리 관련인지 확인합니다."""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in WASTE_KEYWORDS)

def is_alien_registration_related_query(query):
    """질문이 외국인 등록 관련인지 확인합니다."""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in ALIEN_REGISTRATION_KEYWORDS)

def extract_district_from_query(query):
    """질문에서 구군명을 추출합니다."""
    query_lower = query.lower()
    
    # 다양한 형태의 구군명 매칭 (더 구체적인 매칭이 우선되도록 순서 조정)
    district_mappings = [
        # 정확한 매칭 (가장 우선)
        ("해운대구", "해운대구"), ("부산진구", "부산진구"), ("동래구", "동래구"), ("영도구", "영도구"),
        ("금정구", "금정구"), ("강서구", "강서구"), ("연제구", "연제구"), ("수영구", "수영구"),
        ("사상구", "사상구"), ("기장군", "기장군"), ("중구", "중구"), ("서구", "서구"), 
        ("동구", "동구"), ("남구", "남구"), ("북구", "북구"), ("사하구", "사하구"),
        
        # "~입니다", "~에요", "~예요" 형태 매칭
        ("해운대구입니다", "해운대구"), ("부산진구입니다", "부산진구"), ("동래구입니다", "동래구"), ("영도구입니다", "영도구"),
        ("금정구입니다", "금정구"), ("강서구입니다", "강서구"), ("연제구입니다", "연제구"), ("수영구입니다", "수영구"),
        ("사상구입니다", "사상구"), ("기장군입니다", "기장군"), ("중구입니다", "중구"), ("서구입니다", "서구"),
        ("동구입니다", "동구"), ("남구입니다", "남구"), ("북구입니다", "북구"), ("사하구입니다", "사하구"),
        
        ("해운대구에요", "해운대구"), ("부산진구에요", "부산진구"), ("동래구에요", "동래구"), ("영도구에요", "영도구"),
        ("금정구에요", "금정구"), ("강서구에요", "강서구"), ("연제구에요", "연제구"), ("수영구에요", "수영구"),
        ("사상구에요", "사상구"), ("기장군에요", "기장군"), ("중구에요", "중구"), ("서구에요", "서구"),
        ("동구에요", "동구"), ("남구에요", "남구"), ("북구에요", "북구"), ("사하구에요", "사하구"),
        
        # 영어 매칭 (하이픈 형태)
        ("haeundae-gu", "해운대구"), ("busanjin-gu", "부산진구"), ("dongrae-gu", "동래구"), ("yeongdo-gu", "영도구"),
        ("geumjeong-gu", "금정구"), ("gangseo-gu", "강서구"), ("yeonje-gu", "연제구"), ("suyeong-gu", "수영구"),
        ("sasang-gu", "사상구"), ("gijang-gun", "기장군"), ("jung-gu", "중구"), ("seo-gu", "서구"),
        ("dong-gu", "동구"), ("nam-gu", "남구"), ("buk-gu", "북구"), ("saha-gu", "사하구"),
        
        # 영어 매칭 (공백 형태)
        ("haeundae gu", "해운대구"), ("busanjin gu", "부산진구"), ("dongrae gu", "동래구"), ("yeongdo gu", "영도구"),
        ("geumjeong gu", "금정구"), ("gangseo gu", "강서구"), ("yeonje gu", "연제구"), ("suyeong gu", "수영구"),
        ("sasang gu", "사상구"), ("gijang gun", "기장군"), ("jung gu", "중구"), ("seo gu", "서구"),
        ("dong gu", "동구"), ("nam gu", "남구"), ("buk gu", "북구"), ("saha gu", "사하구"),
        
        # 영어 매칭 (긴 이름들 - 더 구체적이므로 우선)
        ("haeundae", "해운대구"), ("busanjin", "부산진구"), ("dongrae", "동래구"), ("yeongdo", "영도구"),
        ("geumjeong", "금정구"), ("gangseo", "강서구"), ("yeonje", "연제구"), ("suyeong", "수영구"),
        ("sasang", "사상구"), ("gijang", "기장군"),
        
        # 부분 매칭 (구/군 포함, 더 구체적인 것 우선)
        ("해운대", "해운대구"), ("부산진", "부산진구"), ("동래", "동래구"), ("영도", "영도구"),
        ("금정", "금정구"), ("강서", "강서구"), ("연제", "연제구"), ("수영", "수영구"),
        ("사상", "사상구"), ("기장", "기장군"),
        
        # 중국어 매핑 (간체)
        ("中区", "중구"), ("西区", "서구"), ("东区", "동구"), ("南区", "남구"), ("北区", "북구"),
        ("影岛区", "영도구"), ("釜山镇区", "부산진구"), ("东莱区", "동래구"), ("沙下区", "사하구"),
        ("海云台区", "해운대구"), ("金井区", "금정구"), ("江西区", "강서구"), ("莲堤区", "연제구"),
        ("水营区", "수영구"), ("沙上区", "사상구"), ("机张郡", "기장군"),
        
        # 중국어 매핑 (번체 - 대만)
        ("中區", "중구"), ("西區", "서구"), ("東區", "동구"), ("南區", "남구"), ("北區", "북구"),
        ("影島區", "영도구"), ("釜山鎮區", "부산진구"), ("東萊區", "동래구"), ("沙下區", "사하구"),
        ("海雲台區", "해운대구"), ("金井區", "금정구"), ("江西區", "강서구"), ("蓮堤區", "연제구"),
        ("水營區", "수영구"), ("沙上區", "사상구"), ("機張郡", "기장군"),
        
        # 일본어 매핑
        ("中区", "중구"), ("西区", "서구"), ("東区", "동구"), ("南区", "남구"), ("北区", "북구"),
        ("影島区", "영도구"), ("釜山鎮区", "부산진구"), ("東莱区", "동래구"), ("沙下区", "사하구"),
        ("海雲台区", "해운대구"), ("金井区", "금정구"), ("江西区", "강서구"), ("蓮堤区", "연제구"),
        ("水営区", "수영구"), ("沙上区", "사상구"), ("機張郡", "기장군"),
        
        # 베트남어 매핑 (음성학적 표기)
        ("jung gu", "중구"), ("seo gu", "서구"), ("dong gu", "동구"), ("nam gu", "남구"), ("buk gu", "북구"),
        ("yeongdo gu", "영도구"), ("busanjin gu", "부산진구"), ("dongrae gu", "동래구"), ("saha gu", "사하구"),
        ("haeundae gu", "해운대구"), ("geumjeong gu", "금정구"), ("gangseo gu", "강서구"), ("yeonje gu", "연제구"),
        ("suyeong gu", "수영구"), ("sasang gu", "사상구"), ("gijang gun", "기장군"),
        
        # 태국어/필리핀어/인도네시아어/프랑스어/독일어는 영어 표기법 사용
        # 이미 위의 영어 매핑에서 커버됨
        
        # 영어 단순 매칭 (매우 조심스럽게, 한국어와 함께 사용시에만)
        ("jung", "중구"), ("seo", "서구"), ("dong", "동구"), ("nam", "남구"), ("buk", "북구"), ("saha", "사하구"),
        
        # 단순 매칭 (마지막 우선순위)
        ("중", "중구"), ("서", "서구"), ("동", "동구"), ("남", "남구"), ("북", "북구"), ("사하", "사하구")
    ]
    
    for pattern, district in district_mappings:
        if pattern in query_lower:
            print(f"  - 구군명 패턴 매칭: '{pattern}' → '{district}'")
            return district
    
    return None

def get_district_selection_prompt(target_lang):
    """구군 선택을 요청하는 프롬프트를 반환합니다."""
    templates = {
        "ko": "부산광역시 어느 구에서 쓰레기 처리 정보를 알고 싶으신가요?\n\n부산광역시 16개 구군: 중구, 서구, 동구, 영도구, 부산진구, 동래구, 남구, 북구, 해운대구, 사하구, 금정구, 강서구, 연제구, 수영구, 사상구, 기장군\n\n구군명을 알려주시면 해당 구의 상세한 쓰레기 처리 정보를 제공해드리겠습니다.",
        
        "en": "Which district in Busan Metropolitan City would you like to know about waste disposal information?\n\n16 districts in Busan: Jung-gu, Seo-gu, Dong-gu, Yeongdo-gu, Busanjin-gu, Dongrae-gu, Nam-gu, Buk-gu, Haeundae-gu, Saha-gu, Geumjeong-gu, Gangseo-gu, Yeonje-gu, Suyeong-gu, Sasang-gu, Gijang-gun\n\nPlease tell me the district name and I will provide detailed waste disposal information for that district.",
        
        "vi": "Bạn muốn biết thông tin xử lý rác thải ở quận nào của thành phố Busan?\n\n16 quận của Busan: Jung-gu, Seo-gu, Dong-gu, Yeongdo-gu, Busanjin-gu, Dongrae-gu, Nam-gu, Buk-gu, Haeundae-gu, Saha-gu, Geumjeong-gu, Gangseo-gu, Yeonje-gu, Suyeong-gu, Sasang-gu, Gijang-gun\n\nVui lòng cho tôi biết tên quận và tôi sẽ cung cấp thông tin chi tiết về xử lý rác thải cho quận đó.",
        
        "ja": "釜山広域市のどの区でごみ処理情報を知りたいですか？\n\n釜山広域市16区: 中区、西区、東区、影島区、釜山鎮区、東莱区、南区、北区、海雲台区、沙下区、金井区、江西区、蓮堤区、水営区、沙上区、機張郡\n\n区名を教えてください。該当区の詳細なごみ処理情報をご提供いたします。",
        
        "zh": "您想了解釜山广域市哪个区的垃圾处理信息？\n\n釜山广域市16个区：中区、西区、东区、影岛区、釜山镇区、东莱区、南区、北区、海云台区、沙下区、金井区、江西区、莲堤区、水营区、沙上区、机张郡\n\n请告诉我区名，我将为您提供该区的详细垃圾处理信息。",
        
        "tw": "您想了解釜山廣域市哪個區的垃圾處理資訊？\n\n釜山廣域市16個區：中區、西區、東區、影島區、釜山鎮區、東萊區、南區、北區、海雲台區、沙下區、金井區、江西區、蓮堤區、水營區、沙上區、機張郡\n\n請告訴我區名，我將為您提供該區的詳細垃圾處理資訊。",
        
        "tl": "Alin sa mga distrito ng Busan Metropolitan City ang gusto mong malaman ang tungkol sa waste disposal information?\n\n16 districts sa Busan: Jung-gu, Seo-gu, Dong-gu, Yeongdo-gu, Busanjin-gu, Dongrae-gu, Nam-gu, Buk-gu, Haeundae-gu, Saha-gu, Geumjeong-gu, Gangseo-gu, Yeonje-gu, Suyeong-gu, Sasang-gu, Gijang-gun\n\nPakisabi sa akin ang pangalan ng distrito at magbibigay ako ng detalyadong waste disposal information para sa distrito na iyon.",
        
        "id": "Distrik mana di Kota Metropolitan Busan yang ingin Anda ketahui informasi pengelolaan sampahnya?\n\n16 distrik di Busan: Jung-gu, Seo-gu, Dong-gu, Yeongdo-gu, Busanjin-gu, Dongrae-gu, Nam-gu, Buk-gu, Haeundae-gu, Saha-gu, Geumjeong-gu, Gangseo-gu, Yeonje-gu, Suyeong-gu, Sasang-gu, Gijang-gun\n\nSilakan beri tahu saya nama distrik dan saya akan memberikan informasi detail pengelolaan sampah untuk distrik tersebut.",
        
        "th": "คุณต้องการทราบข้อมูลการจัดการขยะในเขตใดของเมืองปูซาน?\n\n16 เขตในปูซาน: Jung-gu, Seo-gu, Dong-gu, Yeongdo-gu, Busanjin-gu, Dongrae-gu, Nam-gu, Buk-gu, Haeundae-gu, Saha-gu, Geumjeong-gu, Gangseo-gu, Yeonje-gu, Suyeong-gu, Sasang-gu, Gijang-gun\n\nกรุณาบอกชื่อเขตและฉันจะให้ข้อมูลรายละเอียดการจัดการขยะสำหรับเขตนั้น",
        
        "fr": "Dans quel district de la ville métropolitaine de Busan souhaitez-vous connaître les informations sur l'élimination des déchets ?\n\n16 districts à Busan : Jung-gu, Seo-gu, Dong-gu, Yeongdo-gu, Busanjin-gu, Dongrae-gu, Nam-gu, Buk-gu, Haeundae-gu, Saha-gu, Geumjeong-gu, Gangseo-gu, Yeonje-gu, Suyeong-gu, Sasang-gu, Gijang-gun\n\nVeuillez me dire le nom du district et je vous fournirai des informations détaillées sur l'élimination des déchets pour ce district.",
        
        "de": "In welchem Bezirk der Stadt Busan möchten Sie Informationen über die Abfallentsorgung erfahren?\n\n16 Bezirke in Busan: Jung-gu, Seo-gu, Dong-gu, Yeongdo-gu, Busanjin-gu, Dongrae-gu, Nam-gu, Buk-gu, Haeundae-gu, Saha-gu, Geumjeong-gu, Gangseo-gu, Yeonje-gu, Suyeong-gu, Sasang-gu, Gijang-gun\n\nBitte teilen Sie mir den Namen des Bezirks mit und ich werde Ihnen detaillierte Informationen zur Abfallentsorgung für diesen Bezirk zur Verfügung stellen."
    }
    return templates.get(target_lang, templates["ko"])

def get_waste_info_translations():
    """쓰레기 처리 정보 번역 매핑을 반환합니다."""
    return {
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
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "In front of main gate or designated location",
            "구체적인 수거업체 정보는 구청에 문의 필요": "Contact district office for specific collection company information",
            "무단투기 시 100만원 이하 과태료 부과": "Fine up to 1 million won for illegal dumping",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "New Green Environment",
            "부산환경": "Busan Environment",
            "(주)모두환경": "Modu Environment Co., Ltd.",
            "㈜모두환경": "Modu Environment Co., Ltd.",
            "백양환경": "Baekyang Environment",
            "유한회사 우리환경": "Woori Environment Co., Ltd.",
            "(유)우리환경": "Woori Environment Co., Ltd.",
            "경인산업": "Gyeongin Industry",
            "민하산업": "Minha Industry",
            "맑은사하환경": "Clear Saha Environment",
            "㈜연성기업": "Yeonseong Enterprise Co., Ltd.",
            "대남환경": "Daenam Environment",
            "대도환경": "Daedo Environment",
            "기장군도시관리공단": "Gijang County Urban Management Corporation",
            "구청 문의": "Contact District Office",
            
            # 요일 번역
            "일요일": "Sunday", "월요일": "Monday", "화요일": "Tuesday", "수요일": "Wednesday",
            "목요일": "Thursday", "금요일": "Friday", "토요일": "Saturday"
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
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "Trước cổng chính hoặc nơi được chỉ định",
            "구체적인 수거업체 정보는 구청에 문의 필요": "Liên hệ văn phòng quận để biết thông tin chi tiết về công ty thu gom",
            "무단투기 시 100만원 이하 과태료 부과": "Phạt tiền lên đến 1 triệu won cho việc đổ rác bừa bãi",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "New Green Environment",
            "부산환경": "Busan Environment",
            "(주)모두환경": "Modu Environment Co., Ltd.",
            "㈜모두환경": "Modu Environment Co., Ltd.",
            "백양환경": "Baekyang Environment",
            "유한회사 우리환경": "Woori Environment Co., Ltd.",
            "(유)우리환경": "Woori Environment Co., Ltd.",
            "경인산업": "Gyeongin Industry",
            "민하산업": "Minha Industry",
            "맑은사하환경": "Clear Saha Environment",
            "㈜연성기업": "Yeonseong Enterprise Co., Ltd.",
            "대남환경": "Daenam Environment",
            "대도환경": "Daedo Environment",
            "기장군도시관리공단": "Gijang County Urban Management Corporation",
            "구청 문의": "Liên hệ Văn phòng Quận",
            
            # 요일 번역
            "일요일": "Chủ nhật", "월요일": "Thứ hai", "화요일": "Thứ ba", "수요일": "Thứ tư",
            "목요일": "Thứ năm", "금요일": "Thứ sáu", "토요일": "Thứ bảy"
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
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "大门前或指定场所",
            "구체적인 수거업체 정보는 구청에 문의 필요": "具体收集公司信息请联系区政府",
            "무단투기 시 100만원 이하 과태료 부과": "乱扔垃圾将被处以不超过100万韩元的罚款",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "新绿色环境",
            "부산환경": "釜山环境",
            "(주)모두환경": "牟都环境股份有限公司",
            "㈜모두환경": "牟都环境股份有限公司",
            "백양환경": "白阳环境",
            "유한회사 우리환경": "我们环境有限公司",
            "(유)우리환경": "我们环境有限公司",
            "경인산업": "京仁产业",
            "민하산업": "敏河产业",
            "맑은사하환경": "清洁沙河环境",
            "㈜연성기업": "联成企业股份有限公司",
            "대남환경": "大南环境",
            "대도환경": "大道环境",
            "기장군도시관리공단": "机张郡城市管理公团",
            "구청 문의": "联系区政府",
            
            # 요일 번역
            "일요일": "星期日", "월요일": "星期一", "화요일": "星期二", "수요일": "星期三",
            "목요일": "星期四", "금요일": "星期五", "토요일": "星期六"
        },
        "tw": {
            # 부서명 번역
            "자원순환과": "資源循環科",
            "청소행정과": "清掃行政科",
            "환경위생과": "環境衛生科",
            "환경과": "環境科",
            "청소과": "清掃科",
            
            # 배출 품목 번역
            "일반쓰레기": "一般垃圾",
            "음식물쓰레기": "食物垃圾",
            "재활용품": "可回收物",
            "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "可回收物（罐頭、瓶子、廢鐵、塑料、牛奶紙盒、透明PET瓶）",
            "재활용품(종이,의류,비닐포장재,스치로폼류)": "可回收物（紙類、衣物、塑料包裝、泡沫塑料）",
            "소형폐가전": "小型廢舊家電",
            "불연성폐기물": "不可燃垃圾",
            "연탄재": "煤球灰",
            "소규모건설폐기물(PP전용마대)": "小型建築垃圾（PP專用袋）",
            "배출금지": "禁止投放",
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "大門前或指定場所",
            "구체적인 수거업체 정보는 구청에 문의 필요": "具體收集公司資訊請聯繫區政府",
            "무단투기 시 100만원 이하 과태료 부과": "亂扔垃圾將被處以不超過100萬韓元的罰款",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "新綠色環境",
            "부산환경": "釜山環境",
            "(주)모두환경": "牟都環境股份有限公司",
            "㈜모두환경": "牟都環境股份有限公司",
            "백양환경": "白陽環境",
            "유한회사 우리환경": "我們環境有限公司",
            "(유)우리환경": "我們環境有限公司",
            "경인산업": "京仁產業",
            "민하산업": "敏河產業",
            "맑은사하환경": "清潔沙河環境",
            "㈜연성기업": "聯成企業股份有限公司",
            "대남환경": "大南環境",
            "대도환경": "大道環境",
            "기장군도시관리공단": "機張郡城市管理公團",
            "구청 문의": "聯繫區政府",
            
            # 요일 번역
            "일요일": "星期日", "월요일": "星期一", "화요일": "星期二", "수요일": "星期三",
            "목요일": "星期四", "금요일": "星期五", "토요일": "星期六"
        },
        "ja": {
            # 기본 용어 번역
            "담당부서": "担当部署",
            "연락처": "連絡先",
            "수집시간": "収集時間",
            "배출시간": "排出時間",
            "수집장소": "収集場所", 
            "배출장소": "排出場所",
            "주간수집스케줄": "週間収集スケジュール",
            "배출요일": "排出曜日",
            "週間収集スケジュール": "週間収集スケジュール",
            "ゴミ袋価格": "ゴミ袋価格",
            "特記事項": "特記事項",
            "処理ガイド": "処理ガイド",
            "RAG": "RAG",
            
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
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "正門前または指定された場所",
            "구체적인 수거업체 정보는 구청에 문의 필요": "具体的な収集業者情報は区役所にお問い合わせください",
            "무단투기 시 100만원 이하 과태료 부과": "不法投棄の場合、100万ウォン以下の過料が課せられます",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "ニューグリーン環境",
            "부산환경": "釜山環境",
            "(주)모두환경": "株式会社モドゥ環境",
            "㈜모두환경": "株式会社モドゥ環境",
            "백양환경": "白陽環境",
            "유한회사 우리환경": "有限会社ウリ環境",
            "(유)우리환경": "有限会社ウリ環境",
            "경인산업": "京仁産業",
            "민하산업": "ミナ産業",
            "맑은사하환경": "清らかなサハ環境",
            "㈜연성기업": "株式会社ヨンソン企業",
            "대남환境": "大南環境",
            "대도환경": "大道環境",
            "기장군도시관리공단": "機張郡都市管理公団",
            "구청 문의": "区役所にお問い合わせください",
            
            # 요일 번역
            "일요일": "日曜日", "월요일": "月曜日", "화요일": "火曜日", "수요일": "水曜日",
            "목요일": "木曜日", "금요일": "金曜日", "토요일": "土曜日"
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
            "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "ของรีไซเคิล (กระป๋อง, ขวด, เหล็กเก่า, พลาสติก, กล่องนม/กระดาษ, ขวดPETใส)",
            "재활용품(종이,의류,비닐포장재,스치로폼류)": "ของรีไซเคิล (กระดาษ, เสื้อผ้า, บรรจุภัณฑ์พลาสติก, โฟม)",
            "소형폐가전": "เครื่องใช้ไฟฟ้าเก่าขนาดเล็ก",
            "불연성폐기물": "ขยะที่ไม่ไหม้",
            "연탄재": "เถ้าถ่านก้อน",
            "소규모건설폐기물(PP전용마대)": "ขยะก่อสร้างขนาดเล็ก (ถุงPPเท่านั้น)",
            "배출금지": "ห้ามทิ้ง",
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "หน้าประตูหลักหรือสถานที่ที่กำหนด",
            "구체적인 수거업체 정보는 구청에 문의 필요": "ติดต่อสำนักงานเขตเพื่อขอข้อมูลบริษัทเก็บขยะที่เจาะจง",
            "무단투기 시 100만원 이하 과태료 부과": "ปรับไม่เกิน 1 ล้านวอนสำหรับการทิ้งขยะผิดกฎหมาย",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "New Green Environment",
            "부산환경": "Busan Environment", 
            "(주)모두환경": "Modu Environment Co., Ltd.",
            "㈜모두환경": "Modu Environment Co., Ltd.",
            "백양환경": "Baekyang Environment",
            "유한회사 우리환경": "Woori Environment Co., Ltd.",
            "(유)우리환경": "Woori Environment Co., Ltd.",
            "경인산업": "Gyeongin Industry",
            "민하산업": "Minha Industry",
            "맑은사하환경": "Clear Saha Environment",
            "㈜연성기업": "Yeonseong Enterprise Co., Ltd.",
            "대남환경": "Daenam Environment", 
            "대도환경": "Daedo Environment",
            "기장군도시관리공단": "Gijang County Urban Management Corporation",
            "구청 문의": "ติดต่อสำนักงานเขต",
            
            # 요일 번역
            "일요일": "วันอาทิตย์", "월요일": "วันจันทร์", "화요일": "วันอังคาร", "수요일": "วันพุธ",
            "목요일": "วันพฤหัสบดี", "금요일": "วันศุกร์", "토요일": "วันเสาร์"
        },
        "tl": {
            # 부서명 번역
            "자원순환과": "Kagawaran ng Resource Circulation",
            "청소행정과": "Kagawaran ng Sanitation Administration",
            "환경위생과": "Kagawaran ng Environmental Sanitation",
            "환경과": "Kagawaran ng Environment",
            "청소과": "Kagawaran ng Sanitation",
            
            # 배출 품목 번역
            "일반쓰레기": "General na basura",
            "음식물쓰레기": "Food waste",
            "재활용품": "Recyclables",
            "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Recyclables (lata, bote, scrap metal, plastic, milk/paper carton, linaw na PET bottle)",
            "재활용품(종이,의류,비닐포장재,스치로폼류)": "Recyclables (papel, damit, plastic packaging, styrofoam)",
            "소형폐가전": "Maliliit na sirang appliance",
            "불연성폐기물": "Hindi nasusunog na basura",
            "연탄재": "Briquette ash",
            "소규모건설폐기물(PP전용마대)": "Maliit na construction waste (PP bag lang)",
            "배출금지": "Bawal itapon",
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "Sa harap ng pangunahing gate o itinakdang lugar",
            "구체적인 수거업체 정보는 구청에 문의 필요": "Makipag-ugnayan sa district office para sa tukoy na impormasyon ng collection company",
            "무단투기 시 100만원 이하 과태료 부과": "Multa hanggang 1 milyong won para sa illegal na pagtatapon",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "New Green Environment",
            "부산환경": "Busan Environment",
            "(주)모두환경": "Modu Environment Co., Ltd.",
            "㈜모두환경": "Modu Environment Co., Ltd.",
            "백양환경": "Baekyang Environment",
            "유한회사 우리환경": "Woori Environment Co., Ltd.",
            "(유)우리환경": "Woori Environment Co., Ltd.",
            "경인산업": "Gyeongin Industry",
            "민하산업": "Minha Industry",
            "맑은사하환경": "Clear Saha Environment",
            "㈜연성기업": "Yeonseong Enterprise Co., Ltd.",
            "대남환경": "Daenam Environment",
            "대도환경": "Daedo Environment",
            "기장군도시관리공단": "Gijang County Urban Management Corporation",
            "구청 문의": "Makipag-ugnayan sa District Office",
            
            # 요일 번역
            "일요일": "Linggo", "월요일": "Lunes", "화요일": "Martes", "수요일": "Miyerkules",
            "목요일": "Huwebes", "금요일": "Biyernes", "토요일": "Sabado"
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
            "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Barang daur ulang (kaleng, botol, besi tua, plastik, karton susu/kertas, botol PET bening)",
            "재활용품(종이,의류,비닐포장재,스치로폼류)": "Barang daur ulang (kertas, pakaian, kemasan plastik, styrofoam)",
            "소형폐가전": "Elektronik kecil bekas",
            "불연성폐기물": "Sampah tidak mudah terbakar",
            "연탄재": "Abu briket",
            "소규모건설폐기물(PP전용마대)": "Sampah konstruksi kecil (kantong PP saja)",
            "배출금지": "Dilarang buang",
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "Di depan gerbang utama atau tempat yang ditentukan",
            "구체적인 수거업체 정보는 구청에 문의 필요": "Hubungi kantor distrik untuk informasi perusahaan pengumpul yang spesifik",
            "무단투기 시 100만원 이하 과태료 부과": "Denda hingga 1 juta won untuk pembuangan ilegal",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "New Green Environment",
            "부산환경": "Busan Environment",
            "(주)모두환경": "Modu Environment Co., Ltd.",
            "㈜모두환경": "Modu Environment Co., Ltd.",
            "백양환경": "Baekyang Environment",
            "유한회사 우리환경": "Woori Environment Co., Ltd.",
            "(유)우리환경": "Woori Environment Co., Ltd.",
            "경인산업": "Gyeongin Industry",
            "민하산업": "Minha Industry",
            "맑은사하환경": "Clear Saha Environment",
            "㈜연성기업": "Yeonseong Enterprise Co., Ltd.",
            "대남환경": "Daenam Environment",
            "대도환경": "Daedo Environment",
            "기장군도시관리공단": "Gijang County Urban Management Corporation",
            "구청 문의": "Hubungi Kantor Distrik",
            
            # 요일 번역
            "일요일": "Minggu", "월요일": "Senin", "화요일": "Selasa", "수요일": "Rabu",
            "목요일": "Kamis", "금요일": "Jumat", "토요일": "Sabtu"
        },
        "fr": {
            # 부서명 번역
            "자원순환과": "Département de circulation des ressources",
            "청소행정과": "Département d'administration sanitaire",
            "환경위생과": "Département d'assainissement environnemental", 
            "환경과": "Département de l'environnement",
            "청소과": "Département d'assainissement",
            
            # 배출 품목 번역
            "일반쓰레기": "Déchets généraux",
            "음식물쓰레기": "Déchets alimentaires",
            "재활용품": "Recyclables",
            "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Recyclables (boîtes, bouteilles, ferraille, plastique, emballages lait/papier, bouteilles PET transparentes)",
            "재활용품(종이,의류,비닐포장재,스치로폼류)": "Recyclables (papier, vêtements, emballages plastiques, polystyrène)",
            "소형폐가전": "Petits appareils électroniques usagés",
            "불연성폐기물": "Déchets non combustibles",
            "연탄재": "Cendres de briquettes",
            "소규모건설폐기물(PP전용마대)": "Petits déchets de construction (sacs PP uniquement)",
            "배출금지": "Interdiction de jeter",
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "Devant le portail principal ou à l'endroit désigné",
            "구체적인 수거업체 정보는 구청에 문의 필요": "Contactez le bureau de district pour des informations spécifiques sur l'entreprise de collecte",
            "무단투기 시 100만원 이하 과태료 부과": "Amende jusqu'à 1 million de wons pour dépôt illégal",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "New Green Environment",
            "부산환경": "Busan Environment",
            "(주)모두환경": "Modu Environment Co., Ltd.",
            "㈜모두환경": "Modu Environment Co., Ltd.",
            "백양환경": "Baekyang Environment",
            "유한회사 우리환경": "Woori Environment Co., Ltd.",
            "(유)우리환경": "Woori Environment Co., Ltd.",
            "경인산업": "Gyeongin Industry",
            "민하산업": "Minha Industry",
            "맑은사하환경": "Clear Saha Environment",
            "㈜연성기업": "Yeonseong Enterprise Co., Ltd.",
            "대남환경": "Daenam Environment",
            "대도환경": "Daedo Environment",
            "기장군도시관리공단": "Gijang County Urban Management Corporation",
            "구청 문의": "Contactez le Bureau de District",
            
            # 요일 번역
            "일요일": "Dimanche", "월요일": "Lundi", "화요일": "Mardi", "수요일": "Mercredi",
            "목요일": "Jeudi", "금요일": "Vendredi", "토요일": "Samedi"
        },
        "de": {
            # 부서명 번역
            "자원순환과": "Abteilung für Ressourcenkreislauf",
            "청소행정과": "Sanitätsverwaltungsabteilung",
            "환경위생과": "Umwelthygiene-Abteilung",
            "환경과": "Umweltabteilung", 
            "청소과": "Sanitätsabteilung",
            
            # 배출 품목 번역
            "일반쓰레기": "Allgemeiner Abfall",
            "음식물쓰레기": "Lebensmittelabfall",
            "재활용품": "Recyclingsmaterialien",
            "재활용품(캔,병,고철,플라스틱,우유.종이팩, 투명폐트병)": "Recyclingsmaterialien (Dosen, Flaschen, Schrott, Kunststoff, Milch-/Papierkartons, transparente PET-Flaschen)",
            "재활용품(종이,의류,비닐포장재,스치로폼류)": "Recyclingsmaterialien (Papier, Kleidung, Kunststoffverpackungen, Styropor)",
            "소형폐가전": "Kleine Elektroaltgeräte",
            "불연성폐기물": "Nicht brennbarer Abfall",
            "연탄재": "Brikettsasche",
            "소규모건설폐기물(PP전용마대)": "Kleine Bauabfälle (nur PP-Säcke)",
            "배출금지": "Entsorgung verboten",
            
            # 위치 및 일반 텍스트 번역
            "대문 앞 또는 지정된 장소": "Vor dem Haupttor oder an der designierten Stelle",
            "구체적인 수거업체 정보는 구청에 문의 필요": "Kontaktieren Sie das Bezirksamt für spezifische Informationen zum Sammelunternehmen",
            "무단투기 시 100만원 이하 과태료 부과": "Geldstrafe bis zu 1 Million Won für illegale Entsorgung",
            
            # 업체명 번역
            "여기로": "YeoGiRo",
            "뉴그린환경": "New Green Environment",
            "부산환경": "Busan Environment",
            "(주)모두환경": "Modu Environment Co., Ltd.",
            "㈜모두환경": "Modu Environment Co., Ltd.",
            "백양환경": "Baekyang Environment",
            "유한회사 우리환경": "Woori Environment Co., Ltd.",
            "(유)우리환경": "Woori Environment Co., Ltd.",
            "경인산업": "Gyeongin Industry",
            "민하산업": "Minha Industry",
            "맑은사하환경": "Clear Saha Environment",
            "㈜연성기업": "Yeonseong Enterprise Co., Ltd.",
            "대남환경": "Daenam Environment",
            "대도환경": "Daedo Environment",
            "기장군도시관리공단": "Gijang County Urban Management Corporation",
            "구청 문의": "Kontaktieren Sie das Bezirksamt",
            
            # 요일 번역
            "일요일": "Sonntag", "월요일": "Montag", "화요일": "Dienstag", "수요일": "Mittwoch",
            "목요일": "Donnerstag", "금요일": "Freitag", "토요일": "Samstag"
        }
    }

def translate_waste_text(text, target_lang):
    """쓰레기 처리 관련 텍스트를 번역합니다."""
    translations = get_waste_info_translations()
    if target_lang == "ko" or target_lang not in translations:
        return text
    return translations[target_lang].get(text, text)

def filter_documents_by_district(documents, target_district):
    """특정 구군의 문서만 필터링합니다."""
    if not target_district:
        return documents
    
    filtered_docs = []
    for doc in documents:
        if isinstance(doc, dict) and 'metadata' in doc:
            metadata = doc['metadata']
            if 'gu_name' in metadata and metadata['gu_name'] == target_district:
                filtered_docs.append(doc)
        elif isinstance(doc, str) and target_district in doc:
            filtered_docs.append(doc)
    
    # 구군별 문서가 없으면 전체 문서 반환
    if not filtered_docs:
        print(f"  - {target_district} 관련 문서를 찾을 수 없음, 전체 문서 사용")
        return documents
    
    print(f"  - {target_district} 관련 문서 {len(filtered_docs)}개 필터링됨")
    return filtered_docs

# 언어별 프롬프트 템플릿
LANGUAGE_PROMPTS = {
    'ko': '''아래 참고 정보의 내용을 최대한 반영하되, 자연스럽고 중복 없이 답변하세요. 참고 정보에 없는 내용은 '참고 정보에 없습니다'라고 답하세요.

[참고 정보]
{context}

질문: {query}
답변:''',
    'en': '''Please answer by naturally incorporating the relevant information from the reference below, avoiding redundant or repeated phrases. If the information is not in the reference, answer 'Information not found in the reference.'

[Reference Information]
{context}

Question: {query}
Answer:''',
    'ja': '''以下の参考情報の内容をできるだけ反映しつつ、自然で重複のない回答をしてください。参考情報にない内容は「参考情報にありません」と答えてください。

[参考情報]
{context}

質問: {query}
回答:''',
    'zh': '''请根据下方参考信息的内容，自然且无重复地作答。如果参考信息中没有相关内容，请回答"参考信息中没有"。

[参考信息]
{context}

问题: {query}
回答:''',
    'vi': '''Vui lòng trả lời bằng cách lồng ghép tự nhiên, không lặp lại thông tin từ tài liệu tham khảo dưới đây. Nếu không có thông tin, hãy trả lời 'Không tìm thấy thông tin trong tài liệu tham khảo.'

[Thông tin tham khảo]
{context}

Câu hỏi: {query}
Trả lời:''',
    'fr': '''Veuillez répondre en intégrant naturellement les informations pertinentes ci-dessous, sans redondance. Si l'information ne se trouve pas dans la référence, répondez 'Information non trouvée dans la référence.'

[Informations de référence]
{context}

Question: {query}
Réponse:''',
    'de': '''Bitte beantworten Sie die Frage, indem Sie die relevanten Informationen aus den folgenden Referenzinformationen natürlich und ohne Wiederholungen einbeziehen. Wenn die Information nicht in der Referenz steht, antworten Sie bitte 'Information nicht in der Referenz gefunden.'

[Referenzinformationen]
{context}

Frage: {query}
Antwort:''',
    'th': '''กรุณาตอบโดยนำข้อมูลที่เกี่ยวข้องจากข้อมูลอ้างอิงด้านล่างมาใช้ให้เป็นธรรมชาติและไม่ซ้ำกัน หากไม่มีข้อมูลในเอกสารอ้างอิง กรุณาตอบว่า 'ไม่พบข้อมูลในเอกสารอ้างอิง'

[ข้อมูลอ้างอิง]
{context}

คำถาม: {query}
คำตอบ:'''
}

# 부산광역시 구군 목록
BUSAN_DISTRICTS = [
    "중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", 
    "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"
]

# 쓰레기 처리 관련 키워드 (다국어 지원)
WASTE_KEYWORDS = [
    # 한국어 키워드
    "쓰레기", "폐기물", "배출", "종량제", "봉투", "버리는", "버리기", "버려", "버리다",
    "음식물쓰레기", "재활용", "대형폐기물", "소형폐가전", "특수폐기물", 
    "수거", "분리배출", "폐기", "쓰레기처리", "폐기물처리", "배출방법", "버리는방법",
    "쓰레기봉투", "종량제봉투", "음식물쓰레기봉투", "배출시간", "배출장소", "배출요일",
    
    # 영어 키워드
    "waste", "trash", "garbage", "rubbish", "disposal", "dispose", "throw", "throwing", "discard",
    "recycle", "recycling", "food waste", "large waste", "collection", "pickup", "bag", "bags",
    "waste bag", "garbage bag", "trash bag", "collection time", "collection day", "collection schedule",
    "waste disposal", "trash disposal", "garbage disposal", "how to dispose", "where to throw",
    "waste management", "trash management", "garbage management",
    
    # 베트남어 키워드
    "rác", "rác thải", "xử lý rác", "vứt rác", "bỏ rác", "túi rác", "thu gom", "tái chế",
    "phân loại rác", "rác sinh hoạt", "rác thực phẩm", "rác tái chế",
    
    # 중국어 키워드 (간체)
    "垃圾", "废物", "处理", "丢弃", "回收", "垃圾袋", "收集", "分类",
    "垃圾处理", "垃圾分类", "生活垃圾", "厨余垃圾", "可回收垃圾", "垃圾清运",
    
    # 중국어 키워드 (번체 - 대만)
    "垃圾", "廢物", "處理", "丟棄", "回收", "垃圾袋", "收集", "分類",
    "垃圾處理", "垃圾分類", "生活垃圾", "廚餘垃圾", "可回收垃圾", "垃圾清運",
    
    # 일본어 키워드
    "ゴミ", "廃棄物", "処理", "捨てる", "リサイクル", "ゴミ袋", "収集", "分別",
    "ゴミ処理", "ゴミ分別", "生活ゴミ", "生ゴミ", "資源ゴミ", "ゴミ収集",
    "廃棄", "廃棄処理", "ごみ", "ごみ処理", "ごみ分別",
    
    # 태국어 키워드
    "ขยะ", "การจัดการขยะ", "ทิ้งขยะ", "รีไซเคิล", "ถุงขยะ", "เก็บขยะ",
    "แยกขยะ", "ขยะอินทรีย์", "ขยะรีไซเคิล",
    
    # 필리핀어(타갈로그) 키워드
    "basura", "tapon", "itapon", "kolekta", "recycle", "supot", "paghahati",
    "organic na basura", "recyclable", "koleksyon ng basura",
    
    # 인도네시아어 키워드
    "sampah", "limbah", "pembuangan", "buang", "daur ulang", "kantong sampah",
    "pengumpulan", "pemilahan", "sampah organik", "sampah daur ulang",
    
    # 프랑스어 키워드
    "déchet", "déchets", "ordure", "poubelle", "jeter", "recyclage", "tri",
    "collecte", "sac poubelle", "déchets organiques", "déchets recyclables",
    
    # 독일어 키워드
    "müll", "abfall", "entsorgen", "werfen", "recycling", "mülltüte",
    "sammlung", "trennung", "biomüll", "recyclbare abfälle"
]

# 외국인 등록 관련 키워드
ALIEN_REGISTRATION_KEYWORDS = [
    "외국인등록", "외국인등록증", "외국인 등록", "외국인 등록증", "체류", "체류카드", 
    "등록증", "신청", "발급", "갱신", "연장", "비자", "거류", "거류증", "체류증",
    "외국인신고", "외국인 신고", "외국인신분증", "외국인 신분증", "체류자격", "체류허가",
    "입국관리", "출입국", "출입국관리", "출입국관리소", "이민", "이민청", "체류기간",
    "등록 방법", "등록하는 방법", "등록하려면", "어떻게 등록", "등록 절차", "등록 과정",
    "alien registration", "arc", "residence card", "immigration", "visa", "stay", "permit",
    "registration card", "foreign registration", "immigration office", "residence permit"
]

# 언어별 오류 메시지
ERROR_MESSAGES = {
    'ko': {
        'no_chunks': '참고 정보에서 관련 내용을 찾을 수 없습니다.',
        'empty_response': '답변을 생성하지 못했습니다. (OpenAI 응답이 비어 있음)',
        'auth_error': 'OpenAI API 인증에 실패했습니다. API Key를 확인해주세요.',
        'rate_limit': 'OpenAI API 요청 제한에 도달했습니다. 잠시 후 다시 시도해주세요.',
        'api_error': 'OpenAI API 오류가 발생했습니다: {error}',
        'unknown_error': '답변 생성 중 오류가 발생했습니다: {error}'
    },
    'en': {
        'no_chunks': 'No relevant information found in the reference.',
        'empty_response': 'Failed to generate response. (OpenAI response is empty)',
        'auth_error': 'OpenAI API authentication failed. Please check your API Key.',
        'rate_limit': 'OpenAI API rate limit reached. Please try again later.',
        'api_error': 'OpenAI API error occurred: {error}',
        'unknown_error': 'An error occurred while generating response: {error}'
    },
    'ja': {
        'no_chunks': '参考情報に関連する内容が見つかりません。',
        'empty_response': '回答の生成に失敗しました。（OpenAIの応答が空です）',
        'auth_error': 'OpenAI API認証に失敗しました。API Keyを確認してください。',
        'rate_limit': 'OpenAI APIリクエスト制限に達しました。しばらくしてから再試行してください。',
        'api_error': 'OpenAI APIエラーが発生しました: {error}',
        'unknown_error': '回答生成中にエラーが発生しました: {error}'
    },
    'zh': {
        'no_chunks': '在参考信息中找不到相关内容。',
        'empty_response': '无法生成回答。（OpenAI响应为空）',
        'auth_error': 'OpenAI API认证失败。请检查您的API密钥。',
        'rate_limit': '达到OpenAI API请求限制。请稍后重试。',
        'api_error': '发生OpenAI API错误: {error}',
        'unknown_error': '生成回答时发生错误: {error}'
    },
    'vi': {
        'no_chunks': 'Không tìm thấy thông tin liên quan trong tài liệu tham khảo.',
        'empty_response': 'Không thể tạo phản hồi. (Phản hồi OpenAI trống)',
        'auth_error': 'Xác thực OpenAI API thất bại. Vui lòng kiểm tra API Key của bạn.',
        'rate_limit': 'Đã đạt giới hạn yêu cầu OpenAI API. Vui lòng thử lại sau.',
        'api_error': 'Lỗi OpenAI API xảy ra: {error}',
        'unknown_error': 'Đã xảy ra lỗi khi tạo phản hồi: {error}'
    },
    'fr': {
        'no_chunks': 'Aucune information pertinente trouvée dans la référence.',
        'empty_response': 'Échec de la génération de la réponse. (Réponse OpenAI vide)',
        'auth_error': 'Échec de l\'authentification OpenAI API. Veuillez vérifier votre clé API.',
        'rate_limit': 'Limite de taux OpenAI API atteinte. Veuillez réessayer plus tard.',
        'api_error': 'Erreur OpenAI API survenue: {error}',
        'unknown_error': 'Une erreur s\'est produite lors de la génération de la réponse: {error}'
    },
    'de': {
        'no_chunks': 'Keine relevanten Informationen in der Referenz gefunden.',
        'empty_response': 'Antwortgenerierung fehlgeschlagen. (OpenAI-Antwort ist leer)',
        'auth_error': 'OpenAI API-Authentifizierung fehlgeschlagen. Bitte überprüfen Sie Ihren API-Schlüssel.',
        'rate_limit': 'OpenAI API-Ratenlimit erreicht. Bitte versuchen Sie es später erneut.',
        'api_error': 'OpenAI API-Fehler aufgetreten: {error}',
        'unknown_error': 'Fehler bei der Antwortgenerierung aufgetreten: {error}'
    },
    'th': {
        'no_chunks': 'ไม่พบข้อมูลที่เกี่ยวข้องในเอกสารอ้างอิง',
        'empty_response': 'ไม่สามารถสร้างคำตอบได้ (การตอบสนองของ OpenAI ว่างเปล่า)',
        'auth_error': 'การยืนยันตัวตน OpenAI API ล้มเหลว กรุณาตรวจสอบ API Key ของคุณ',
        'rate_limit': 'ถึงขีดจำกัดการร้องขอ OpenAI API แล้ว กรุณาลองใหม่อีกครั้ง',
        'api_error': 'เกิดข้อผิดพลาด OpenAI API: {error}',
        'unknown_error': 'เกิดข้อผิดพลาดในการสร้างคำตอบ: {error}'
    }
}

# 파일 해시 계산 함수
def calculate_file_hash(file_path):
    """파일의 MD5 해시를 계산합니다."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# 캐시 정보 저장/로드 함수
def save_cache_info(file_hash, chunk_count):
    """캐시 정보를 JSON 파일로 저장합니다."""
    cache_info = {
        "file_hash": file_hash,
        "chunk_count": chunk_count,
        "created_at": str(os.path.getctime(PDF_PATH))
    }
    with open(CACHE_INFO_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache_info, f, ensure_ascii=False, indent=2)

def load_cache_info():
    """캐시 정보를 JSON 파일에서 로드합니다."""
    if not os.path.exists(CACHE_INFO_PATH):
        return None
    try:
        with open(CACHE_INFO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def is_cache_valid():
    """현재 PDF 파일의 해시와 캐시된 해시를 비교하여 캐시가 유효한지 확인합니다."""
    if not os.path.exists(PDF_PATH):
        print(f"PDF 파일이 존재하지 않습니다: {PDF_PATH}")
        return False
    
    if not os.path.exists(VECTOR_DB_PATH):
        print("벡터DB 파일이 존재하지 않습니다.")
        return False
    
    current_hash = calculate_file_hash(PDF_PATH)
    cache_info = load_cache_info()
    
    if cache_info is None:
        print("캐시 정보가 없습니다.")
        return False
    
    if cache_info.get("file_hash") != current_hash:
        print(f"PDF 파일이 변경되었습니다. (이전 해시: {cache_info.get('file_hash')[:8]}..., 현재 해시: {current_hash[:8]}...)")
        return False
    
    print(f"캐시가 유효합니다. (파일 해시: {current_hash[:8]}...)")
    return True

# 1. PDF 청크 분할 함수 (pypdf 사용)
def chunk_pdf_to_text_chunks(pdf_path, chunk_size=1000, chunk_overlap=100):
    """PDF를 텍스트 청크로 분할합니다."""
    reader = PdfReader(pdf_path)
    text_chunks = []
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text.strip():
            continue
            
        # 텍스트를 청크로 분할
        words = text.split()
        current_chunk = ""
        chunks = []
        
        for word in words:
            if len(current_chunk) + len(word) + 1 <= chunk_size:
                current_chunk += (word + " ")
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = word + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 청크 오버랩 처리
        final_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0 and chunk_overlap > 0:
                # 이전 청크의 끝 부분을 현재 청크 앞에 추가
                overlap_text = chunks[i-1][-chunk_overlap:] if len(chunks[i-1]) > chunk_overlap else chunks[i-1]
                chunk = overlap_text + " " + chunk
            
            # Document 객체 대신 딕셔너리 사용
            final_chunks.append({
                'page_content': chunk,
                'metadata': {'page': page_num + 1}
            })
        
        text_chunks.extend(final_chunks)
    
    return text_chunks

# Gemini 임베딩 클래스
class GeminiEmbeddings:
    def __init__(self, gemini_api_key, model="models/embedding-001"):
        self.api_key = gemini_api_key
        self.model = model
        genai.configure(api_key=gemini_api_key)

    def embed_query(self, text):
        response = genai.embed_content(model=self.model, content=text, task_type="retrieval_query")
        return response["embedding"]

    def embed_documents(self, texts):
        embeddings = []
        for text in texts:
            response = genai.embed_content(model=self.model, content=text, task_type="retrieval_document")
            embeddings.append(response["embedding"])
        return embeddings

# SimpleVectorDB는 동일하게 사용 (임베딩 객체만 교체)
class SimpleVectorDB:
    def __init__(self, documents, embeddings=None, doc_embeddings=None):
        self.documents = documents
        self.embeddings = embeddings
        self.doc_embeddings = doc_embeddings

    def similarity_search(self, query, k=3):
        if self.embeddings is None:
            print("임베딩 객체가 없습니다. 새로 생성합니다...")
            return self.documents[:k]
        query_embedding = self.embeddings.embed_query(query)
        doc_texts = [doc['page_content'] if isinstance(doc, dict) and 'page_content' in doc else str(doc) for doc in self.documents]
        doc_embeddings = self.doc_embeddings or self.embeddings.embed_documents(doc_texts)
        similarities = [np.dot(query_embedding, doc_emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb)) for doc_emb in doc_embeddings]
        top_indices = np.argsort(similarities)[-k:][::-1]
        return [self.documents[i] for i in top_indices]
    def __getstate__(self):
        state = self.__dict__.copy()
        state['embeddings'] = None
        return state
    def __setstate__(self, state):
        self.__dict__.update(state)

# 2. 임베딩 및 벡터DB 저장/로드 함수
def get_or_create_vector_db(gemini_api_key):
    if not os.path.exists(VECTOR_DB_PATH):
        return None
    with open(VECTOR_DB_PATH, 'rb') as f:
        vector_db = pickle.load(f)
    embeddings = GeminiEmbeddings(gemini_api_key)
    vector_db.embeddings = embeddings
    return vector_db

# 캐시 관리 유틸리티 함수들
def get_cache_status():
    """현재 캐시 상태를 반환합니다."""
    if not os.path.exists(VECTOR_DB_PATH):
        return {"status": "not_exists", "message": "벡터DB가 존재하지 않습니다."}
    
    cache_info = load_cache_info()
    if cache_info is None:
        return {"status": "no_cache_info", "message": "캐시 정보가 없습니다."}
    
    current_hash = calculate_file_hash(PDF_PATH)
    is_valid = cache_info.get("file_hash") == current_hash
    
    return {
        "status": "valid" if is_valid else "invalid",
        "current_hash": current_hash[:8] + "...",
        "cached_hash": cache_info.get("file_hash", "")[:8] + "...",
        "chunk_count": cache_info.get("chunk_count"),
        "created_at": cache_info.get("created_at"),
        "is_valid": is_valid
    }

def force_rebuild_cache(gemini_api_key):
    """캐시를 강제로 재생성합니다."""
    print("캐시를 강제로 재생성합니다...")
    if os.path.exists(VECTOR_DB_PATH):
        os.remove(VECTOR_DB_PATH)
        print("기존 벡터DB를 삭제했습니다.")
    
    return get_or_create_vector_db(gemini_api_key)

def clear_cache():
    """캐시를 완전히 삭제합니다."""
    if os.path.exists(VECTOR_DB_PATH):
        os.remove(VECTOR_DB_PATH)
        print("캐시가 완전히 삭제되었습니다.")
    else:
        print("삭제할 캐시가 없습니다.")

# 3. 유사 청크 검색 함수
def retrieve_relevant_chunks(query, vector_db, k=3):
    print(f"  - 유사 청크 검색 시작 (k={k})")
    try:
        docs = vector_db.similarity_search(query, k=k)
        print(f"  - 유사 청크 검색 완료: {len(docs)}개 찾음")
        return docs
    except Exception as e:
        print(f"  - 유사 청크 검색 실패: {e}")
        return []

def insert_linebreaks(text, max_length=60):
    result = ""
    line = ""
    for sentence in re.split(r'([.!?]\s+)', text):  # 문장 단위로 분리
        if not sentence.strip():
            continue
        if len(line) + len(sentence) > max_length:
            result += line.strip() + "\n"
            line = sentence
        else:
            line += sentence
    result += line.strip()
    # 쉼표 등에서도 추가로 줄바꿈
    result = re.sub(r'([,，])\s*', '\1\n', result)
    return result

def get_multicultural_prompt_template(target_lang):
    """다문화가족 한국생활안내 프롬프트 템플릿 (개선된 버전)"""
    
    templates = {
        "ko": """당신은 다문화가족을 위한 한국생활안내 챗봇입니다. 
다음은 참고 정보입니다. 정확하고 도움이 되는 답변을 한국어로 해주세요.

[참고 정보]
{context}

질문: {query}

답변 지침:
1. 사용자가 구군명만 입력한 경우, 이전 대화 맥락을 고려하여 적절한 정보를 제공하세요.
2. 쓰레기 처리 관련 질문이었다면 해당 구의 쓰레기 배출 방법을 안내하세요.
3. 다른 생활 정보 질문이었다면 해당 구의 관련 정보를 제공하세요.
4. 구체적이고 실용적인 정보를 제공하세요.
5. 답변이 불충분하거나 관련성이 낮다면 "해당 정보를 찾을 수 없습니다"라고 답변하세요.
6. 다문화가족의 관점에서 이해하기 쉽게 설명하세요.

답변:""",
        
        "en": """You are a Korean life guidance chatbot for multicultural families.
Here is reference information. Please provide accurate and helpful answers in English.

[Reference Information]
{context}

Question: {query}

Answer Guidelines:
1. If the user only enters a district name, provide appropriate information considering the previous conversation context.
2. If it was a waste disposal question, guide the waste disposal method for that district.
3. If it was another life information question, provide relevant information for that district.
4. Provide specific and practical information.
5. If the answer is insufficient or not relevant, say "I cannot find the relevant information."
6. Explain in a way that multicultural families can easily understand.

Answer:""",
        
        "ja": """あなたは多文化家族のための韓国生活案内チャットボットです。
以下は参考情報です。正確で役立つ回答を日本語でお願いします。

[参考情報]
{context}

質問: {query}

回答ガイドライン:
1. ユーザーが区郡名のみを入力した場合、前の会話の文脈を考慮して適切な情報を提供してください。
2. ごみ処理に関する質問だった場合は、その区のごみ排出方法を案内してください。
3. 他の生活情報の質問だった場合は、その区の関連情報を提供してください。
4. 具体的で実用的な情報を提供してください。
5. 回答が不十分または関連性が低い場合は「該当する情報が見つかりません」と答えてください。
6. 多文化家族の観点から理解しやすく説明してください。

回答:""",
        
        "zh": """您是面向多文化家庭的韩国生活指导聊天机器人。
以下是参考信息。请用中文提供准确有用的答案。

[参考信息]
{context}

问题: {query}

答案指南:
1. 如果用户只输入区郡名，请考虑之前对话的上下文提供适当的信息。
2. 如果是垃圾处理相关问题，请指导该区的垃圾排放方法。
3. 如果是其他生活信息问题，请提供该区的相关信息。
4. 提供具体实用的信息。
5. 如果答案不充分或相关性低，请说"找不到相关信息"。
6. 从多文化家庭的角度进行易于理解的说明。

答案:""",
        
        "vi": """Bạn là chatbot hướng dẫn cuộc sống Hàn Quốc cho các gia đình đa văn hóa.
Đây là thông tin tham khảo. Vui lòng cung cấp câu trả lời chính xác và hữu ích bằng tiếng Việt.

[Thông tin tham khảo]
{context}

Câu hỏi: {query}

Hướng dẫn trả lời:
1. Nếu người dùng chỉ nhập tên quận/huyện, hãy cung cấp thông tin phù hợp xem xét ngữ cảnh cuộc trò chuyện trước đó.
2. Nếu là câu hỏi về xử lý rác thải, hãy hướng dẫn phương pháp thải rác cho quận/huyện đó.
3. Nếu là câu hỏi thông tin cuộc sống khác, hãy cung cấp thông tin liên quan cho quận/huyện đó.
4. Cung cấp thông tin cụ thể và thực tế.
5. Nếu câu trả lời không đủ hoặc không liên quan, hãy nói "Tôi không thể tìm thấy thông tin liên quan."
6. Giải thích theo cách mà các gia đình đa văn hóa có thể dễ dàng hiểu.

Trả lời:""",

        "tw": """您是為多文化家庭提供韓國生活指導的聊天機器人。
以下是參考資訊。請用繁體中文提供準確有用的答案。

[參考資訊]
{context}

問題: {query}

回答指引:
1. 如果使用者只輸入區郡名，請考慮之前的對話脈絡提供適當資訊。
2. 如果是垃圾處理相關問題，請引導該區的垃圾處理方法。
3. 如果是其他生活資訊問題，請提供該區的相關資訊。  
4. 提供具體且實用的資訊。
5. 如果答案不充分或相關性低，請回答「找不到相關資訊」。
6. 以多文化家庭容易理解的方式說明。

回答:""",

        "th": """คุณเป็นแชทบอทสำหรับให้คำแนะนำการใช้ชีวิตในเกาหลีแก่ครอบครัวพหุวัฒนธรรม
ต่อไปนี้เป็นข้อมูลอ้างอิง กรุณาให้คำตอบที่ถูกต้องและเป็นประโยชน์เป็นภาษาไทย

[ข้อมูลอ้างอิง]
{context}

คำถาม: {query}

แนวทางการตอบ:
1. หากผู้ใช้ป้อนเพียงชื่อเขต ให้ข้อมูลที่เหมาะสมโดยพิจารณาบริบทการสนทนาก่อนหน้านี้
2. หากเป็นคำถามเกี่ยวกับการจัดการขยะ ให้แนะนำวิธีการกำจัดขยะสำหรับเขตนั้น
3. หากเป็นคำถามข้อมูลการใช้ชีวิตอื่นๆ ให้ข้อมูลที่เกี่ยวข้องสำหรับเขตนั้น
4. ให้ข้อมูลที่เฉพาะเจาะจงและใช้ได้จริง
5. หากคำตอบไม่เพียงพอหรือไม่เกี่ยวข้อง ให้ตอบว่า "ไม่สามารถหาข้อมูลที่เกี่ยวข้องได้"
6. อธิบายในลักษณะที่ครอบครัวพหุวัฒนธรรมสามารถเข้าใจได้ง่าย

คำตอบ:""",

        "id": """Anda adalah chatbot panduan hidup Korea untuk keluarga multikultural.
Berikut adalah informasi referensi. Harap berikan jawaban yang akurat dan bermanfaat dalam bahasa Indonesia.

[Informasi Referensi]
{context}

Pertanyaan: {query}

Panduan Jawaban:
1. Jika pengguna hanya memasukkan nama distrik, berikan informasi yang sesuai dengan mempertimbangkan konteks percakapan sebelumnya.
2. Jika pertanyaan tentang pengelolaan sampah, panduan metode pembuangan sampah untuk distrik tersebut.
3. Jika pertanyaan informasi kehidupan lainnya, berikan informasi terkait untuk distrik tersebut.
4. Berikan informasi yang spesifik dan praktis.
5. Jika jawaban tidak memadai atau kurang relevan, katakan "Tidak dapat menemukan informasi terkait."
6. Jelaskan dengan cara yang mudah dipahami oleh keluarga multikultural.

Jawaban:""",

        "tl": """Ikaw ay isang Korean life guidance chatbot para sa mga multicultural family.
Narito ang reference information. Mangyaring magbigay ng tumpak at kapaki-pakinabang na sagot sa Tagalog.

[Reference Information]
{context}

Tanong: {query}

Gabay sa Pagsagot:
1. Kung ang user ay nag-input lang ng district name, magbigay ng appropriate information na isasaalang-alang ang previous conversation context.
2. Kung waste disposal question, gabayan ang waste disposal method para sa district na iyon.
3. Kung ibang life information question, magbigay ng related information para sa district na iyon.
4. Magbigay ng specific at practical na information.
5. Kung ang sagot ay hindi sapat o hindi relevant, sabihin "Hindi mahanap ang relevant information."
6. Ipaliwanag sa paraan na madaling maintindihan ng mga multicultural family.

Sagot:""",

        "fr": """Vous êtes un chatbot de guide de vie coréenne pour les familles multiculturelles.
Voici les informations de référence. Veuillez fournir des réponses précises et utiles en français.

[Informations de référence]
{context}

Question: {query}

Directives de réponse:
1. Si l'utilisateur ne saisit que le nom du district, fournissez des informations appropriées en tenant compte du contexte de conversation précédent.
2. S'il s'agit d'une question sur l'élimination des déchets, guidez la méthode d'élimination des déchets pour ce district.
3. S'il s'agit d'autres questions d'information sur la vie, fournissez des informations pertinentes pour ce district.
4. Fournissez des informations spécifiques et pratiques.
5. Si la réponse est insuffisante ou peu pertinente, dites "Je ne peux pas trouver d'informations pertinentes."
6. Expliquez d'une manière que les familles multiculturelles peuvent facilement comprendre.

Réponse:""",

        "de": """Sie sind ein koreanischer Lebensleitfaden-Chatbot für multikulturelle Familien.
Hier sind Referenzinformationen. Bitte geben Sie genaue und hilfreiche Antworten auf Deutsch.

[Referenzinformationen]
{context}

Frage: {query}

Antwortrichtlinien:
1. Wenn der Benutzer nur den Bezirksnamen eingibt, geben Sie angemessene Informationen unter Berücksichtigung des vorherigen Gesprächskontexts.
2. Bei Fragen zur Abfallentsorgung leiten Sie die Abfallentsorgungsmethode für diesen Bezirk an.
3. Bei anderen Lebensinformationsfragen geben Sie relevante Informationen für diesen Bezirk.
4. Geben Sie spezifische und praktische Informationen.
5. Wenn die Antwort unzureichend oder nicht relevant ist, sagen Sie "Ich kann keine relevanten Informationen finden."
6. Erklären Sie auf eine Weise, die multikulturelle Familien leicht verstehen können.

Antwort:"""
    }
    
    return templates.get(target_lang, templates["ko"])

def get_foreign_worker_prompt_template(target_lang):
    templates = {
        "ko": """다음은 외국인 근로자 권리구제 관련 정보입니다. 질문에 대해 정확하고 도움이 되는 답변을 한국어로 제공해주세요.\n\n[참고 정보]\n{context}\n\n질문: {query}\n\n답변: 외국인 근로자 권리구제 관점에서 한국어로 답변해주세요.""",
        "en": """Below is information about foreign worker rights protection. Please provide an accurate and helpful answer in English.\n\n[Reference Information]\n{context}\n\nQuestion: {query}\n\nAnswer: Please answer from the perspective of foreign worker rights protection in English.""",
        "vi": """Dưới đây là thông tin về bảo vệ quyền lợi người lao động nước ngoài. Vui lòng trả lời chính xác và hữu ích bằng tiếng Việt.\n\n[Thông tin tham khảo]\n{context}\n\nCâu hỏi: {query}\n\nTrả lời: Vui lòng trả lời bằng tiếng Việt từ góc nhìn bảo vệ quyền lợi người lao động nước ngoài.""",
        "ja": """以下は外国人労働者権利保護に関する情報です。質問に対して正確で役立つ回答を日本語で提供してください。

[参考情報]
{context}

質問: {query}

回答: 外国人労働者権利保護の観点から日本語で答えてください。""",
        "zh": """以下是外籍劳工权益保护相关信息。请用中文准确、详细地回答问题。

[参考信息]
{context}

问题: {query}

回答: 请从外籍劳工权益保护的角度用中文回答。""",
        "tw": """以下是外籍勞工權益保護相關資訊。請用繁體中文詳細回答問題。

[參考資訊]
{context}

問題: {query}

回答: 請以外籍勞工權益保護的角度用繁體中文回答。""",

        "tl": """Narito ang impormasyon tungkol sa proteksyon ng mga karapatan ng foreign worker. Mangyaring sumagot nang tumpak at kapaki-pakinabang sa Tagalog.

[Reference Information]
{context}

Tanong: {query}

Sagot: Mangyaring sumagot mula sa pananaw ng proteksyon ng mga karapatan ng foreign worker sa Tagalog.""",
        "id": """Berikut adalah informasi perlindungan hak pekerja asing. Silakan jawab dengan akurat dan membantu dalam bahasa Indonesia.\n\n[Informasi Referensi]\n{context}\n\nPertanyaan: {query}\n\nJawaban: Silakan jawab dari sudut pandang perlindungan hak pekerja asing dalam bahasa Indonesia.""",
        "th": """ต่อไปนี้เป็นข้อมูลเกี่ยวกับการคุ้มครองสิทธิแรงงานต่างชาติ กรุณาตอบเป็นภาษาไทยอย่างถูกต้องและเป็นประโยชน์\n\n[ข้อมูลอ้างอิง]\n{context}\n\nคำถาม: {query}\n\nคำตอบ: กรุณาตอบจากมุมมองของคู่มือการใช้ชีวิตในเกาหลีสำหรับครอบครัวพหุวัฒนธรรมเป็นภาษาไทย""",
        "fr": """Voici des informations sur la protection des droits des travailleurs étrangers. Veuillez répondre en français de manière précise et utile.\n\n[Informations de référence]\n{context}\n\nQuestion : {query}\n\nRéponse : Veuillez répondre du point de vue de la protection des droits des travailleurs étrangers en français.""",
        "de": """Nachfolgend finden Sie Informationen zum Schutz der Rechte ausländischer Arbeitnehmer. Bitte antworten Sie auf Deutsch genau und hilfreich.\n\n[Referenzinformationen]\n{context}\n\nFrage: {query}\n\nAntwort: Bitte antworten Sie aus der Sicht des Schutzes der Rechte ausländischer Arbeitnehmer auf Deutsch.""",
    }
    return templates.get(target_lang, templates["ko"])

def get_waste_management_prompt_template(target_lang):
    """쓰레기 처리 관련 프롬프트 템플릿을 반환합니다."""
    templates = {
        "ko": """다음은 {district}의 쓰레기 처리 관련 정보입니다:

{context}

위 정보를 바탕으로 다음 질문에 답변해주세요: {query}

답변은 다음 조건을 만족해야 합니다:
1. {district}의 구체적인 쓰레기 처리 방법 설명
2. 외국인이 이해하기 쉽도록 단계별로 설명
3. 필요한 경우 구청 연락처 및 수수료 정보 포함
4. 한국어로 답변""",
        "en": """The following is waste disposal information for {district}:

{context}

Based on the above information, please answer the following question: {query}

The answer should meet the following conditions:
1. Explain specific waste disposal methods for {district}
2. Explain step by step in a way that foreigners can easily understand
3. Include district office contact information and fees if necessary
4. Answer in English""",
        "ja": """以下は{district}の廃棄物処理に関する情報です：

{context}

上記の情報に基づいて、以下の質問に答えてください：{query}

回答は以下の条件を満たす必要があります：
1. {district}の具体的な廃棄物処理方法の説明
2. 外国人が理解しやすいように段階的に説明
3. 必要に応じて区役所の連絡先と手数料情報を含む
4. 日本語で回答""",
        "zh": """以下是{district}的垃圾处理相关信息：

{context}

基于上述信息，请回答以下问题：{query}

答案应满足以下条件：
1. 解释{district}的具体垃圾处理方法
2. 以外籍人士容易理解的方式逐步解释
3. 必要时包含区政府联系方式和费用信息
4. 用中文回答""",
        "vi": """Sau đây là thông tin về xử lý rác thải cho {district}:

{context}

Dựa trên thông tin trên, vui lòng trả lời câu hỏi sau: {query}

Câu trả lời phải đáp ứng các điều kiện sau:
1. Giải thích phương pháp xử lý rác thải cụ thể cho {district}
2. Giải thích từng bước theo cách mà người nước ngoài có thể dễ dàng hiểu
3. Bao gồm thông tin liên hệ văn phòng quận và phí nếu cần thiết
4. Trả lời bằng tiếng Việt""",
        "th": """ต่อไปนี้เป็นข้อมูลการจัดการขยะสำหรับ {district}:

{context}

จากข้อมูลข้างต้น โปรดตอบคำถามต่อไปนี้: {query}

คำตอบต้องเป็นไปตามเงื่อนไขต่อไปนี้:
1. อธิบายวิธีการจัดการขยะที่เฉพาะเจาะจงสำหรับ {district}
2. อธิบายทีละขั้นตอนในลักษณะที่ชาวต่างชาติเข้าใจง่าย
3. รวมข้อมูลติดต่อสำนักงานเขตและค่าธรรมเนียมหากจำเป็น
4. ตอบเป็นภาษาไทย""",
        "fr": """Voici les informations sur l'élimination des déchets pour {district} :

{context}

Basé sur les informations ci-dessus, veuillez répondre à la question suivante : {query}

La réponse doit satisfaire aux conditions suivantes :
1. Expliquer les méthodes d'élimination des déchets spécifiques pour {district}
2. Expliquer étape par étape de manière compréhensible pour les étrangers
3. Inclure les coordonnées du bureau de district et les frais si nécessaire
4. Répondre en français""",
        "de": """Hier sind Informationen zur Abfallentsorgung für {district}:

{context}

Basierend auf den obigen Informationen, beantworten Sie bitte die folgende Frage: {query}

Die Antwort sollte die folgenden Bedingungen erfüllen:
1. Erklären Sie spezifische Abfallentsorgungsmethoden für {district}
2. Erklären Sie Schritt für Schritt auf eine Weise, die Ausländer leicht verstehen können
3. Bei Bedarf Kontaktinformationen des Bezirksbüros und Gebühren einschließen
4. Auf Deutsch antworten""",
        "zh-TW": """以下是{district}的垃圾處理相關資訊：

{context}

基於上述資訊，請回答以下問題：{query}

答案應滿足以下條件：
1. 解釋{district}的具體垃圾處理方法
2. 以外籍人士容易理解的方式逐步解釋
3. 必要時包含區政府聯絡方式和費用資訊
4. 用繁體中文回答""",
        "id": """Berikut adalah informasi pengelolaan sampah untuk {district}:

{context}

Berdasarkan informasi di atas, silakan jawab pertanyaan berikut: {query}

Jawaban harus memenuhi kondisi berikut:
1. Jelaskan metode pengelolaan sampah spesifik untuk {district}
2. Jelaskan langkah demi langkah dengan cara yang mudah dipahami oleh orang asing
3. Sertakan informasi kontak kantor distrik dan biaya jika diperlukan
4. Menjawab dalam bahasa Indonesia"""
    }
    return templates.get(target_lang, templates["ko"])

def load_busan_waste_info():
    """부산광역시_쓰레기처리정보.json 파일을 로드합니다."""
    try:
        with open(WASTE_INFO_JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"부산광역시_쓰레기처리정보.json 로드 실패: {e}")
        return None

def get_waste_info_from_json(district):
    """구군명에 해당하는 쓰레기 처리 정보를 JSON에서 추출합니다."""
    data = load_busan_waste_info()
    if not data:
        return None
    info = data.get("부산광역시_쓰레기처리정보", {}).get("구군별_정보", {}).get(district)
    if not info:
        return None
    # 주요 정보만 보기 좋게 정리
    lines = [f"[{district} 쓰레기 배출 안내]"]
    lines.append(f"- 담당부서: {info.get('담당부서', '')} ({info.get('연락처', '')})")
    lines.append(f"- 배출시간: {info.get('배출시간', '')}")
    lines.append(f"- 배출장소: {info.get('배출장소', '')}")
    # 배출요일
    if '배출요일' in info:
        lines.append("- 배출요일:")
        for day, items in info['배출요일'].items():
            lines.append(f"  · {day}: {', '.join(items)}")
    # 종량제봉투 가격
    if '종량제봉투_가격' in info:
        lines.append("- 종량제봉투 가격:")
        for k, v in info['종량제봉투_가격'].items():
            lines.append(f"  · {k}: {v}원")
    # 특이사항
    if '특이사항' in info:
        lines.append("- 특이사항:")
        for t in info['특이사항']:
            lines.append(f"  · {t}")
    # 대형폐기물
    if '대형폐기물_신고방법' in info:
        lines.append("- 대형폐기물 신고방법:")
        for t in info['대형폐기물_신고방법']:
            lines.append(f"  · {t}")
    if '대형폐기물_수수료_예시' in info:
        lines.append("- 대형폐기물 수수료 예시:")
        for k, v in info['대형폐기물_수수료_예시'].items():
            lines.append(f"  · {k}: {v}")
    return "\n".join(lines)

# 4. Gemini 기반 RAG 답변 생성 함수
def answer_with_rag(query, vector_db, gemini_api_key, model=None, target_lang=None, conversation_context=None):
    """다문화가족 한국생활안내 RAG 답변 생성 (개선된 버전)"""
    
    print("  - Gemini RAG 답변 생성 시작")
    
    # 언어 감지
    if target_lang is None:
        target_lang = detect_language(query)
    
    # 구군명만 입력된 경우 처리
    district_patterns = [
        "중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", 
        "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"
    ]
    
    is_district_only = False
    district_name = None
    
    for pattern in district_patterns:
        if pattern in query:
            district_name = pattern
            is_district_only = True
            break
    
    # 구군명만 입력된 경우 검색 쿼리 개선
    if is_district_only and district_name:
        # 이전 대화 맥락을 고려한 검색 쿼리 생성
        enhanced_query = f"부산 {district_name} 생활 정보"
        print(f"  - 구군명 감지됨: {district_name}")
        print(f"  - 개선된 검색 쿼리: {enhanced_query}")
    else:
        enhanced_query = query
    
    # 쓰레기 처리 관련 질문인지 확인
    if is_waste_related_query(query):
        print("  - 쓰레기 처리 관련 질문 감지됨 (JSON 기반)")
        district = extract_district_from_query(query)
        if district:
            info = get_waste_info_from_json(district)
            if info:
                return info
            else:
                return f"{district}의 쓰레기 처리 정보가 데이터에 없습니다. 구청에 문의해 주세요."
        else:
            return get_district_selection_prompt(target_lang)
    
    # 관련 문서 검색
    try:
        docs = retrieve_relevant_chunks(enhanced_query, vector_db, k=5)
        if not docs:
            return "관련 정보를 찾을 수 없습니다."
        
        # 컨텍스트 구성
        context = "\n\n".join([doc['page_content'] for doc in docs])
        
        # 프롬프트 템플릿 선택
        prompt_template = get_multicultural_prompt_template(target_lang)
        
        # LLM 설정
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        # 프롬프트 구성
        prompt = prompt_template.format(context=context, query=enhanced_query)
        
        # 답변 생성
        response = model.generate_content(prompt)
        answer = response.text
        
        # 구군명만 입력된 경우 추가 처리
        if is_district_only and district_name:
            # 답변이 너무 일반적이거나 관련성이 낮으면 구체적인 안내 추가
            if len(answer) < 50 or "찾을 수 없습니다" in answer:
                answer = f"부산광역시 {district_name}의 생활 정보를 안내해드리겠습니다.\n\n{answer}\n\n더 구체적인 정보가 필요하시면 '쓰레기 배출', '의료 정보', '교육 정보' 등 구체적인 항목을 말씀해 주세요."
        
        return answer
        
    except Exception as e:
        print(f"  - RAG 답변 생성 오류: {e}")
        return "죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다."

def get_district_contact_info(district):
    """구별 연락처 정보를 반환합니다."""
    contact_info = {
        "중구": """
중구 대형폐기물 처리 연락처:
- 중구청 자원순환과: 051-600-4432
- 대형폐기물 수거업체 '여기로': 1599-0903
- 홈페이지: https://yeogiro24.co.kr/
- 앱: '여기로' (구글스토어, 앱스토어)

구체적인 품목별 수수료는 위 연락처로 문의하시거나, '여기로' 앱에서 배출 신청 시 확인할 수 있습니다.
""",
        "해운대구": """
해운대구 대형폐기물 처리 연락처:
- 해운대구청 자원순환과: 051-749-4432
- 대형폐기물 수거업체: 민하산업(051-782-3511), 센텀환경(051-702-0111)
- 홈페이지: https://www.haeundae.go.kr/

구체적인 품목별 수수료는 위 연락처로 문의하시거나, 해운대구청 홈페이지에서 확인할 수 있습니다.
""",
        "동구": """
동구 대형폐기물 처리 연락처:
- 동구청 자원순환과: 051-440-4432
- 대형폐기물 수거업체 '부산환경': 051-631-0933
- 수거전담반: 초량동·수정1·2·4동(010-4537-7515), 수정5동·좌천동·범일동(010-4526-7515)

구체적인 품목별 수수료는 위 연락처로 문의하시거나, 동구청에 직접 문의하세요.
""",
        "서구": """
서구 대형폐기물 처리 연락처:
- 서구청 자원순환과: 051-240-4432
- 대형폐기물 수거업체 '뉴그린환경': 051-900-8488
- 모바일신청: 여기로(www.yeogiro24.co.kr) 접속 및 어플 '여기로' 설치

구체적인 품목별 수수료는 위 연락처로 문의하시거나, '여기로' 앱에서 확인할 수 있습니다.
""",
        "영도구": """
영도구 대형폐기물 처리 연락처:
- 영도구청 자원순환과: 051-419-4432
- 대형폐기물 수거업체 '(주)모두환경': 051-717-0102
- 운영시간: 월~금요일 09:00~18:00, 토요일 09:00~17:00

구체적인 품목별 수수료는 위 연락처로 문의하시거나, 영도구청에 직접 문의하세요.
""",
        "부산진구": """
부산진구 대형폐기물 처리 연락처:
- 부산진구청 자원순환과: 051-605-4432
- 대형폐기물 수거업체: 백양환경(051-893-1234), 우리환경(051-893-5678)

구체적인 품목별 수수료는 위 연락처로 문의하시거나, 부산진구청에 직접 문의하세요.
""",
        "동래구": """
동래구 대형폐기물 처리 연락처:
- 동래구청 자원순환과: 051-550-4432
- 대형폐기물 수거업체 '유한회사 우리환경': 051-552-1022, 051-524-1025
- 홈페이지: www.uuri2.kr
- 모바일: 네이버쇼핑

구체적인 품목별 수수료는 위 연락처로 문의하시거나, 홈페이지에서 확인할 수 있습니다.
""",
        "남구": """
남구 대형폐기물 처리 연락처:
- 남구청 자원순환과: 051-607-4432
- 대형폐기물 수거업체: 경인산업(051-628-1234), 고려산업(051-628-5678)

구체적인 품목별 수수료는 위 연락처로 문의하시거나, 남구청에 직접 문의하세요.
""",
        "북구": """
북구 대형폐기물 처리 연락처:
- 북구청 자원순환과: 051-310-4432
- 대형폐기물 수거업체 '㈜모두환경': 051-336-4433,4
- 인터넷 신청: 네이버스토어

구체적인 품목별 수수료는 위 연락처로 문의하시거나, 네이버스토어에서 확인할 수 있습니다.
"""
    }
    
    return contact_info.get(district, f"""
{district} 대형폐기물 처리:
구체적인 품목별 수수료는 {district}청 자원순환과에 직접 문의하시거나, 
해당 구청 홈페이지에서 확인하시기 바랍니다.
""")

# 5. 부산 맛집 검색을 위한 프롬프트 템플릿
def get_busan_food_prompt_template(target_lang):
    """부산 맛집 검색용 프롬프트 템플릿을 반환합니다."""
    templates = {
        "ko": """다음은 부산의 맛집 정보입니다. 정확하고 도움이 되는 답변을 한국어로 해주세요.

[참고 정보]
{context}

질문: {query}

답변: 부산 맛집 정보를 바탕으로 한국어로 답변해주세요. 가게 이름, 위치, 메뉴, 가격, 특징 등을 포함해서 자세히 설명해주세요.""",

        "en": """Here is restaurant information from Busan. Please provide accurate and helpful answers in English.

[Reference Information]
{context}

Question: {query}

Answer: Please provide a detailed answer in English based on Busan restaurant information. Include restaurant names, locations, menus, prices, and special features.""",

        "ja": """以下は釜山のレストラン情報です。正確で役立つ回答を日本語でお願いします。

[参考情報]
{context}

質問: {query}

回答: 釜山のレストラン情報に基づいて日本語で詳しく回答してください。店名、場所、メニュー、価格、特徴などを含めて説明してください。""",

        "zh": """以下是釜山的餐厅信息。请用中文提供准确且有帮助的回答。

[参考信息]
{context}

问题: {query}

回答: 请基于釜山餐厅信息用中文详细回答。包括餐厅名称、位置、菜单、价格、特色等。""",

        "vi": """Đây là thông tin về nhà hàng ở Busan. Vui lòng cung cấp câu trả lời chính xác và hữu ích bằng tiếng Việt.

[Thông tin tham khảo]
{context}

Câu hỏi: {query}

Trả lời: Vui lòng trả lời chi tiết bằng tiếng Việt dựa trên thông tin nhà hàng Busan. Bao gồm tên nhà hàng, vị trí, thực đơn, giá cả và đặc điểm.""",

        "th": """ต่อไปนี้เป็นข้อมูลร้านอาหารในปูซาน กรุณาให้คำตอบที่ถูกต้องและเป็นประโยชน์เป็นภาษาไทย

[ข้อมูลอ้างอิง]
{context}

คำถาม: {query}

คำตอบ: กรุณาตอบโดยละเอียดเป็นภาษาไทยตามข้อมูลร้านอาหารปูซาน รวมถึงชื่อร้าน สถานที่ เมนู ราคา และความพิเศษ""",

        "fr": """Voici les informations sur les restaurants de Busan. Veuillez fournir des réponses précises et utiles en français.

[Informations de référence]
{context}

Question: {query}

Réponse: Veuillez répondre en détail en français basé sur les informations des restaurants de Busan. Incluez les noms des restaurants, emplacements, menus, prix et caractéristiques spéciales.""",

        "de": """Hier sind Restaurantinformationen aus Busan. Bitte geben Sie genaue und hilfreiche Antworten auf Deutsch.

[Referenzinformationen]
{context}

Frage: {query}

Antwort: Bitte antworten Sie detailliert auf Deutsch basierend auf Busan Restaurantinformationen. Schließen Sie Restaurantnamen, Standorte, Menüs, Preise und besondere Merkmale ein.""",

        "id": """Berikut adalah informasi restoran dari Busan. Mohon berikan jawaban yang akurat dan membantu dalam bahasa Indonesia.

[Informasi Referensi]
{context}

Pertanyaan: {query}

Jawaban: Mohon jawab secara detail dalam bahasa Indonesia berdasarkan informasi restoran Busan. Sertakan nama restoran, lokasi, menu, harga, dan fitur khusus.""",

        "tw": """以下是釜山的餐廳資訊。請用繁體中文提供準確且有幫助的回答。

[參考資訊]
{context}

問題: {query}

回答: 請基於釜山餐廳資訊用繁體中文詳細回答。包括餐廳名稱、位置、菜單、價格、特色等。""",

        "tl": """Narito ang impormasyon tungkol sa mga restaurant sa Busan. Mangyaring magbigay ng tumpak at kapaki-pakinabang na sagot sa Tagalog.

[Reference Information]
{context}

Tanong: {query}

Sagot: Mangyaring sumagot nang detalyado sa Tagalog batay sa impormasyon ng restaurant sa Busan. Isama ang mga pangalan ng restaurant, lokasyon, menu, presyo, at mga special features.""",
    }
    return templates.get(target_lang, templates["ko"])

# 6. JSON 기반 부산 맛집 검색 답변 함수
def clean_markdown_text(text):
    """마크다운 문법을 제거하고 읽기 쉬운 텍스트로 변환합니다."""
    if not text:
        return text
    
    # ** 굵은 글씨 마크다운을 제거 (내용은 유지)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # * 기울임 마크다운을 제거 (내용은 유지)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # ### 헤딩 마크다운을 제거하고 구분자 추가
    text = re.sub(r'###\s*(.*)', r'📍 \1', text)
    text = re.sub(r'##\s*(.*)', r'🔶 \1', text)
    text = re.sub(r'#\s*(.*)', r'📋 \1', text)
    
    # - 리스트를 • 로 변경
    text = re.sub(r'^-\s+', '• ', text, flags=re.MULTILINE)
    
    # 연속된 줄바꿈을 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def extract_location_from_query(query):
    """사용자 질문에서 지역/구 정보를 추출합니다."""
    # 부산 구/지역 매핑 (실제 JSON 키와 매칭) - 다국어 지원
    district_keywords = {
        "해운대구": ["해운대", "해운대구", "해운대역", "해운대해수욕장", "센텀시티", "海雲台區", "海雲台", "海云台区", "海云台", "haeundae", "Haeundae", "Haeundae-gu"],
        "부산진구": ["서면", "부산진구", "전포동", "양정", "가야", "개금", "釜山鎮區", "西面", "釜山镇区", "西面", "busanjin", "Busanjin", "Busanjin-gu", "Seomyeon"],
        "동래구": ["동래", "동래구", "온천장", "명륜동", "사직", "안락", "東萊區", "東萊", "东莱区", "东莱", "dongrae", "Dongrae", "Dongrae-gu"],
        "남구": ["남구", "대연", "용호", "용당", "문현", "감만", "南區", "南区", "nam-gu", "Nam-gu"],
        "연제구": ["연제구", "연산", "거제", "연산동", "蓮堤區", "莲堤区", "yeonje", "Yeonje", "Yeonje-gu"],
        "사상구": ["사상구", "사상", "덕포", "괘법", "감전", "沙上區", "沙上区", "sasang", "Sasang", "Sasang-gu"],
        "금정구": ["금정구", "부산대", "장전", "구서", "금샘", "金井區", "金井区", "geumjeong", "Geumjeong", "Geumjeong-gu"],
        "강서구": ["강서구", "대저", "명지", "가락", "녹산", "江西區", "江西区", "江西", "gangseo", "Gangseo", "Gangseo-gu"],
        "사하구": ["사하구", "하단", "신평", "괴정", "당리", "沙下區", "沙下区", "saha", "Saha", "Saha-gu"],
        "중구": ["중구", "남포동", "국제시장", "자갈치", "BIFF광장", "광복로", "中區", "南浦洞", "中区", "南浦洞", "jung-gu", "Jung-gu", "Nampo", "Nampo-dong"],
        "동구": ["동구", "범일동", "초량", "수정", "東區", "东区", "dong-gu", "Dong-gu"],
        "서구": ["서구", "암남동", "동대신", "충무동", "西區", "西区", "seo-gu", "Seo-gu"],
        "북구": ["북구", "구포", "덕천", "화명", "北區", "北区", "buk-gu", "Buk-gu"],
        "영도구": ["영도구", "영도", "태종대", "절영도", "봉래", "影島區", "影島区", "yeongdo", "Yeongdo", "Yeongdo-gu"],
        "기장군": ["기장군", "기장", "일광", "정관", "機張郡", "機張郡", "gijang", "Gijang", "Gijang-gun"],
        "수영구": ["수영구", "광안리", "수영", "민락", "망미", "水營區", "光安里", "水营区", "光安里", "suyeong", "Suyeong", "Suyeong-gu", "Gwangalli"]
    }
    
    found_districts = []
    query_lower = query.lower()
    
    for district, keywords in district_keywords.items():
        for keyword in keywords:
            if keyword in query:
                found_districts.append(district)
                break
    
    print(f"  - 질문에서 추출된 지역: {found_districts}")
    return found_districts

def filter_restaurants_by_location(busan_food_data, taek_sulling_data, target_districts):
    """지역에 따라 맛집 데이터를 필터링합니다."""
    filtered_busan_food = {}
    filtered_taek_sulling = []
    
    # 부산의맛 데이터 필터링
    if busan_food_data and "부산의 맛 2025" in busan_food_data:
        for district in target_districts:
            if district in busan_food_data["부산의 맛 2025"]:
                filtered_busan_food[district] = busan_food_data["부산의 맛 2025"][district]
    
    # 택슐랭 데이터 필터링 (district 필드 기준)
    if taek_sulling_data and "restaurants" in taek_sulling_data:
        for restaurant in taek_sulling_data["restaurants"]:
            restaurant_district = restaurant.get("district", "")
            for target_district in target_districts:
                if target_district in restaurant_district or restaurant_district in target_district:
                    filtered_taek_sulling.append(restaurant)
                    break
    
    print(f"  - 필터링된 부산의맛 구: {list(filtered_busan_food.keys())}")
    print(f"  - 필터링된 택슐랭 레스토랑 수: {len(filtered_taek_sulling)}")
    
    return filtered_busan_food, filtered_taek_sulling

def answer_with_busan_food_json(query, busan_food_data, taek_sulling_data, gemini_api_key, target_lang=None):
    """JSON 파일을 직접 참조하여 부산 맛집 정보 답변을 생성합니다."""
    print(f"  - JSON 기반 부산 맛집 답변 생성 시작")
    
    # 1. 질문에서 지역 정보 추출
    target_districts = extract_location_from_query(query)
    
    # 2. 지역이 명시된 경우 해당 지역 데이터만 필터링
    if target_districts:
        print(f"  - 지역별 필터링 적용: {target_districts}")
        busan_food_data_filtered, taek_sulling_data_filtered = filter_restaurants_by_location(
            busan_food_data, taek_sulling_data, target_districts
        )
        
        # 택슐랭 데이터가 필터링되어 비어있으면 전체 데이터 사용
        if not taek_sulling_data_filtered and taek_sulling_data:
            print(f"  - 택슐랭 지역 필터링 결과 없음, 전체 데이터 사용")
            taek_sulling_data_filtered = taek_sulling_data.get("restaurants", [])[:10]
    else:
        print(f"  - 지역 정보 없음, 전체 데이터 사용 (일부만)")
        busan_food_data_filtered = busan_food_data
        taek_sulling_data_filtered = taek_sulling_data.get("restaurants", [])[:15] if taek_sulling_data else []
    
    # JSON 데이터를 텍스트로 변환 (필터링된 데이터 사용)
    import json
    
    # 부산의맛 데이터 요약 (필터링된 데이터 사용)
    busan_food_summary = "부산의맛(2025) 데이터:\n"
    if target_districts and busan_food_data_filtered:
        # 지역별 필터링된 데이터 사용
        for district, restaurants in busan_food_data_filtered.items():
            busan_food_summary += f"\n[{district}]\n"
            for restaurant in restaurants:  # 필터링된 데이터는 모두 사용
                name = restaurant.get("식당이름", {}).get("한글", "알 수 없음")
                overview = restaurant.get("개요", {}).get("한글", "정보 없음")
                menu = restaurant.get("메뉴", {}).get("한글", "정보 없음")
                address = restaurant.get("주소", "정보 없음")
                phone = restaurant.get("전화번호", "정보 없음")
                hours = restaurant.get("영업시간", "정보 없음")
                
                busan_food_summary += f"• {name}: {overview}\n"
                busan_food_summary += f"  메뉴: {menu}\n"
                busan_food_summary += f"  주소: {address} | 전화: {phone} | 영업시간: {hours}\n\n"
    elif busan_food_data and "부산의 맛 2025" in busan_food_data:
        # 지역 정보가 없으면 전체 데이터에서 일부만 사용
        for district, restaurants in list(busan_food_data["부산의 맛 2025"].items())[:3]:
            busan_food_summary += f"\n[{district}]\n"
            for restaurant in restaurants[:2]:  # 각 구별로 최대 2개만
                name = restaurant.get("식당이름", {}).get("한글", "알 수 없음")
                overview = restaurant.get("개요", {}).get("한글", "정보 없음")
                menu = restaurant.get("메뉴", {}).get("한글", "정보 없음")
                address = restaurant.get("주소", "정보 없음")
                phone = restaurant.get("전화번호", "정보 없음")
                hours = restaurant.get("영업시간", "정보 없음")
                
                busan_food_summary += f"• {name}: {overview}\n"
                busan_food_summary += f"  메뉴: {menu}\n"
                busan_food_summary += f"  주소: {address} | 전화: {phone} | 영업시간: {hours}\n\n"
    
    # 택슐랭 데이터 요약 (필터링된 데이터 사용)
    taek_sulling_summary = "\n택슐랭(2025) 데이터:\n"
    restaurants_to_use = taek_sulling_data_filtered if target_districts else (taek_sulling_data.get("restaurants", [])[:10] if taek_sulling_data else [])
    
    for restaurant in restaurants_to_use:
        name = restaurant.get("name", "알 수 없음")
        district = restaurant.get("district", "알 수 없음")
        overview = restaurant.get("overview", "정보 없음")
        address = restaurant.get("address", "정보 없음")
        phone = restaurant.get("phoneNumber", "정보 없음")
        hours = restaurant.get("businessHours", "정보 없음")
        menus = restaurant.get("recommendedMenu", [])
        
        taek_sulling_summary += f"\n[{district}] {name}: {overview}\n"
        if menus:
            menu_text = ", ".join([f"{menu['name']} {menu['price']}" for menu in menus])
            taek_sulling_summary += f"  추천메뉴: {menu_text}\n"
        taek_sulling_summary += f"  주소: {address} | 전화: {phone} | 영업시간: {hours}\n"
    
    # 전체 컨텍스트 구성
    context = busan_food_summary + taek_sulling_summary
    
    # 언어별 프롬프트 템플릿
    lang_prompts = {
        "ko": f"""다음은 2025년 최신 부산 맛집 정보입니다. 질문에 대해 정확하고 자세한 답변을 해주세요.

{context}

질문: {query}

답변: 위의 부산 맛집 정보를 바탕으로 질문에 대해 구체적이고 도움이 되는 답변을 해주세요. 가게 이름, 위치, 메뉴, 가격, 연락처, 영업시간 등을 포함해서 상세히 설명해주세요. 만약 질문과 정확히 일치하는 정보가 없다면 유사한 정보나 대안을 제시해주세요.""",

        "en": f"""【IMPORTANT: Answer MUST be in English】Here is the latest 2025 Busan restaurant information. Please provide accurate and detailed answers to the question.

{context}

Question: {query}

【Answer in English ONLY】Answer: Based on the Busan restaurant information above, please provide specific and helpful answers to the question in English.

**Important Instructions:**
1. Restaurant names should include both Korean original name and English translation, format: Korean Name (English Translation)
2. Use Korean district names like: 해운대구, 부산진구, 남구, etc.
3. If the question mentions English area names like Haeundae, Seomyeon, Nampo-dong, convert them to corresponding Korean district names for search
4. Include detailed information about location, menu, prices, contact information, business hours, etc.
5. If there is no exact match, please suggest similar information or alternatives

Area Reference: Haeundae→해운대구, Seomyeon→부산진구, Nampo-dong→중구, Gwangalli→수영구

【Remember: Your response MUST be in English】""",

        "ja": f"""【重要：必ず日本語で回答してください】以下は2025年最新の釜山グルメ情報です。質問に対して正確で詳細な回答をお願いします。

{context}

質問: {query}

【日本語で回答必須】回答: 上記の釜山グルメ情報に基づいて、日本語で質問に対して具体的で役立つ回答をしてください。

**重要な指示:**
1. レストラン名は韓国語原名と日本語翻訳を併記してください。形式：韓国語店名(日本語翻訳)
2. 地区名は韓国語原名を使用してください：해운대구、부산진구、남구 など
3. 質問で海雲台、西面、南浦洞などの日本語地名が出たら、対応する韓国語地区名に変換して検索してください
4. 場所、メニュー、価格、連絡先、営業時間などを詳しく説明してください
5. 質問と正確に一致する情報がない場合は、類似の情報や代替案を提示してください

地区対照：海雲台→해운대구、西面→부산진구、南浦洞→중구、広安里→수영구

【再確認：回答は必ず日本語で】""",

        "zh": f"""以下是2025年最新釜山美食信息。请对问题提供准确详细的回答。

{context}

问题: {query}

回答: 基于上述釜山美食信息，请对问题提供具体有用的回答。

**重要指示:**
1. 餐厅名称请同时提供韩文原名和中文翻译，格式：韩文餐厅名(中文翻译)
2. 地区名称请使用韩文原名，如：해운대구、부산진구、남구 等
3. 如果问题中提到海云台、西面、南浦洞等中文地名，请转换为对应的韩文地区名称进行搜索
4. 请详细说明餐厅位置、菜单、价格、联系方式、营业时间等
5. 如果没有与问题完全匹配的信息，请提供类似信息或替代方案

地区对照：海云台→해운대구, 西面→부산진구, 南浦洞→중구, 光安里→수영구""",

        "vi": f"""Sau đây là thông tin nhà hàng Busan mới nhất năm 2025. Vui lòng cung cấp câu trả lời chính xác và chi tiết cho câu hỏi.

{context}

Câu hỏi: {query}

Trả lời: Dựa trên thông tin nhà hàng Busan ở trên, vui lòng cung cấp câu trả lời cụ thể và hữu ích cho câu hỏi.

**Hướng dẫn quan trọng:**
1. Tên nhà hàng vui lòng cung cấp cả tên gốc tiếng Hàn và bản dịch tiếng Việt, định dạng: Tên tiếng Hàn (Bản dịch tiếng Việt)
2. Tên khu vực sử dụng tên gốc tiếng Hàn như: 해운대구, 부산진구, 남구, v.v.
3. Nếu câu hỏi đề cập đến tên địa danh tiếng Việt như Haeundae, Seomyeon, Nampo-dong, vui lòng chuyển đổi thành tên khu vực tiếng Hàn tương ứng để tìm kiếm
4. Bao gồm thông tin chi tiết về vị trí, thực đơn, giá cả, thông tin liên hệ, giờ mở cửa, v.v.
5. Nếu không có thông tin khớp chính xác với câu hỏi, vui lòng đề xuất thông tin tương tự hoặc giải pháp thay thế

Tham khảo khu vực: Haeundae→해운대구, Seomyeon→부산진구, Nampo-dong→중구, Gwangalli→수영구""",

        "tw": f"""【重要：請務必用繁體中文回答】以下是2025年最新釜山美食資訊。請對問題提供準確詳細的回答。

{context}

問題: {query}

【必須用繁體中文回答】回答: 基於上述釜山美食資訊，請用繁體中文對問題提供具體有用的回答。

**重要指示:**
1. 餐廳名稱請同時提供韓文原名和中文翻譯，格式：韓文餐廳名(中文翻譯)
2. 地區名稱請使用韓文原名，如：해운대구、부산진구、남구 等
3. 如果問題中提到海雲台、西面、南浦洞等中文地名，請轉換為對應的韓文地區名稱進行搜尋
4. 請詳細說明餐廳位置、菜單、價格、聯絡方式、營業時間等
5. 如果沒有與問題完全匹配的資訊，請提供類似資訊或替代方案

地區對照：海雲台→해운대구, 西面→부산진구, 南浦洞→중구, 光安里→수영구

【再次提醒：回答必須用繁體中文】""",

        "th": f"""ต่อไปนี้เป็นข้อมูลร้านอาหารปูซานล่าสุดปี 2025 โปรดให้คำตอบที่ถูกต้องและละเอียดต่อคำถาม

{context}

คำถาม: {query}

คำตอบ: จากข้อมูลร้านอาหารปูซานข้างต้น โปรดให้คำตอบที่เฉพาะเจาะจงและมีประโยชน์ต่อคำถาม รวมถึงชื่อร้าน ที่ตั้ง เมนู ราคา ข้อมูลติดต่อ เวลาทำการ ฯลฯ อย่างละเอียด หากไม่มีข้อมูลที่ตรงกับคำถามทุกประการ โปรดแนะนำข้อมูลที่คล้ายกันหรือทางเลือกอื่น""",

        "id": f"""【PENTING: Jawab HARUS dalam Bahasa Indonesia】Berikut adalah informasi restoran Busan terbaru 2025. Harap berikan jawaban yang akurat dan detail untuk pertanyaan.

{context}

Pertanyaan: {query}

【Jawab dalam Bahasa Indonesia SAJA】Jawaban: Berdasarkan informasi restoran Busan di atas, harap berikan jawaban dalam Bahasa Indonesia yang spesifik dan bermanfaat untuk pertanyaan. Sertakan nama restoran, lokasi, menu, harga, informasi kontak, jam operasional dll secara detail. Jika tidak ada informasi yang persis sesuai dengan pertanyaan, harap sarankan informasi serupa atau alternatif.

【Ingat: Jawaban HARUS dalam Bahasa Indonesia】""",

        "tl": f"""【MAHALAGA: Ang sagot ay dapat nasa Tagalog】Narito ang pinakabagong impormasyon ng mga restaurant sa Busan para sa 2025. Mangyaring magbigay ng tumpak at detalyadong sagot sa tanong.

{context}

Tanong: {query}

【Sumagot sa Tagalog lamang】Sagot: Batay sa impormasyon ng mga restaurant sa Busan sa itaas, mangyaring magbigay ng tiyak at kapaki-pakinabang na sagot sa tanong sa Tagalog.

**Mahalagang Instructions:**
1. Ang mga pangalan ng restaurant ay dapat kasama ang Korean original name at Tagalog translation, format: Korean Name (Tagalog Translation)
2. Gamitin ang Korean district names tulad ng: 해운대구, 부산진구, 남구, atbp.
3. Kung nabanggit sa tanong ang English area names tulad ng Haeundae, Seomyeon, Nampo-dong, i-convert sa corresponding Korean district names para sa search
4. Isama ang detalyadong impormasyon tungkol sa lokasyon, menu, presyo, contact information, business hours, atbp nang detalyado
5. Para sa bawat restaurant, magbigay ng Google Maps link gamit ang address: [Tignan sa Google Maps](https://maps.google.com/maps?q=주소정보)
6. Kung walang eksaktong tugma sa tanong, mangyaring magmungkahi ng katulad na impormasyon o alternatibo

Area Reference: Haeundae→해운대구, Seomyeon→부산진구, Nampo-dong→중구, Gwangalli→수영구

【Tandaan: Ang inyong sagot ay dapat nasa Tagalog】""",

        "fr": f"""Voici les dernières informations sur les restaurants de Busan pour 2025. Veuillez fournir une réponse précise et détaillée à la question.

{context}

Question: {query}

Réponse: Basé sur les informations des restaurants de Busan ci-dessus, veuillez fournir une réponse spécifique et utile à la question. Incluez les noms des restaurants, emplacements, menus, prix, informations de contact, heures d'ouverture, etc. en détail. S'il n'y a pas d'information exactement correspondante à la question, veuillez suggérer des informations similaires ou des alternatives.""",

        "de": f"""Hier sind die neuesten Informationen zu Busan-Restaurants für 2025. Bitte geben Sie eine genaue und detaillierte Antwort auf die Frage.

{context}

Frage: {query}

Antwort: Basierend auf den obigen Busan-Restaurant-Informationen geben Sie bitte eine spezifische und hilfreiche Antwort auf die Frage. Fügen Sie Restaurantnamen, Standorte, Menüs, Preise, Kontaktinformationen, Öffnungszeiten usw. detailliert hinzu. Wenn es keine genau passenden Informationen zur Frage gibt, schlagen Sie bitte ähnliche Informationen oder Alternativen vor."""
    }
    
    # 타겟 언어에 맞는 프롬프트 선택
    prompt = lang_prompts.get(target_lang, lang_prompts["ko"])
    
    # Gemini로 답변 생성
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt, generation_config={
            "max_output_tokens": 1500,
            "temperature": 0.3
        })
        answer = response.text.strip()
        
        # 마크다운 문법 정리
        clean_answer = clean_markdown_text(answer)
        print(f"  - JSON 기반 답변 생성 완료: {len(clean_answer)} 문자 (마크다운 정리됨)")
        return clean_answer
    except Exception as e:
        print(f"  - Gemini 답변 생성 중 오류: {e}")
        return "죄송합니다. 부산 맛집 정보를 처리하는 중에 오류가 발생했습니다."

def answer_with_rag_busan_food(query, vector_db, gemini_api_key, model=None, target_lang=None, conversation_context=None):
    model = "models/gemini-2.0-flash-lite"
    print(f"  - Gemini 부산 맛집 RAG 답변 생성 시작")
    lang = detect_language(query)
    prompt_lang = target_lang if target_lang else lang
    
    # embeddings 속성이 없으면 임시로 생성
    if not hasattr(vector_db, 'embeddings') or vector_db.embeddings is None:
        print(f"  - 벡터DB에 embeddings가 없어서 임시로 생성합니다...")
        try:
            vector_db.embeddings = GeminiEmbeddings(gemini_api_key)
        except:
            # embeddings 설정이 불가능한 경우, 직접 임베딩 생성
            print(f"  - embeddings 설정 실패, 직접 유사도 검색을 수행합니다...")
    
    print(f"  - 유사 청크 검색 중...")
    try:
        relevant_chunks = retrieve_relevant_chunks(query, vector_db, k=5)
    except Exception as e:
        print(f"  - 유사 청크 검색 중 오류: {e}")
        # 검색 실패 시 처음 5개 문서 사용
        relevant_chunks = vector_db.documents[:5] if hasattr(vector_db, 'documents') else []
    
    if not relevant_chunks:
        return "참고 정보에서 관련 내용을 찾을 수 없습니다."
    
    context = "\n\n".join([doc['page_content'] if isinstance(doc, dict) and 'page_content' in doc else str(doc) for doc in relevant_chunks])
    busan_food_prompt_template = get_busan_food_prompt_template(prompt_lang)
    prompt = busan_food_prompt_template.format(context=context, query=query)
    
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    response = model.generate_content(prompt, generation_config={"max_output_tokens": 1000, "temperature": 0.1})
    answer = response.text.strip()
    
    # 마크다운 문법 정리
    clean_answer = clean_markdown_text(answer)
    return clean_answer

def answer_with_rag_foreign_worker(query, vector_db, gemini_api_key, model=None, target_lang=None, conversation_context=None):
    model = "models/gemini-2.0-flash-lite"
    print(f"  - Gemini 외국인 근로자 RAG 답변 생성 시작")
    lang = detect_language(query)
    prompt_lang = target_lang if target_lang else lang
    
    # 대화 컨텍스트에서 이전에 언급된 구군명과 질문 확인
    previous_district = None
    previous_waste_query = None
    if conversation_context:
        previous_district = conversation_context.get('waste_district')
        previous_waste_query = conversation_context.get('waste_query')
        if previous_district:
            print(f"  - 대화 컨텍스트에서 구군명 발견: {previous_district}")
        if previous_waste_query:
            print(f"  - 대화 컨텍스트에서 쓰레기 질문 발견: {previous_waste_query}")
    
    # 현재 질문이 구군명만 제공하는 경우 (이전 쓰레기 질문이 있는 경우)
    if previous_waste_query and not is_waste_related_query(query):
        district = extract_district_from_query(query)
        if district:
            print(f"  - 구군명만 제공됨: {district}, 이전 질문과 연결")
            # 대화 컨텍스트에 구군명 저장
            if conversation_context is not None:
                conversation_context['waste_district'] = district
            
            # 이전 쓰레기 질문과 현재 구군명을 조합하여 처리
            combined_query = f"{district}에서 {previous_waste_query}"
            print(f"  - 조합된 질문: {combined_query}")
            
            # 쓰레기 처리 관련 문서들을 직접 찾기
            waste_docs = []
            for doc in vector_db.documents:
                if isinstance(doc, dict) and 'metadata' in doc:
                    metadata = doc['metadata']
                    if 'category' in metadata and metadata['category'] == '쓰레기처리':
                        if 'gu_name' in metadata and metadata['gu_name'] == district:
                            waste_docs.append(doc)
            
            # 메타데이터로 찾지 못한 경우, 내용 기반으로 검색
            if not waste_docs:
                print(f"  - 메타데이터로 {district} 관련 쓰레기 처리 문서를 찾지 못함, 내용 기반 검색 시도")
                for doc in vector_db.documents:
                    if isinstance(doc, dict) and 'page_content' in doc:
                        content = doc['page_content'].lower()
                        # 구군명과 쓰레기 관련 키워드가 모두 포함된 문서 찾기
                        if district.lower() in content and any(keyword in content for keyword in ['쓰레기', '폐기물', '배출', '종량제', '봉투', '수거']):
                            waste_docs.append(doc)
            
            if waste_docs:
                print(f"  - {district} 관련 쓰레기 처리 문서 {len(waste_docs)}개 찾음")
                
                # 특정 품목 정보 확인
                specific_item_found = False
                for doc in waste_docs:
                    if doc['metadata'].get('type') == 'large_waste_info':
                        content = doc['page_content']
                        # 이전 질문에서 특정 품목 추출
                        specific_items = ["책상", "소파", "침대", "장롱", "냉장고", "TV", "세탁기", "에어컨", "자전거", "유모차", "화분", "고양이타워", "피아노", "운동기구", "보일러", "천막"]
                        for item in specific_items:
                            if item in previous_waste_query and item in content:
                                specific_item_found = True
                                break
                        if specific_item_found:
                            break
                
                context = "\n\n".join([doc['page_content'] for doc in waste_docs])
                
                # 특정 품목 정보가 부족한 경우 추가 안내 포함
                if not specific_item_found:
                    # 구별 연락처 정보 추가
                    district_contact_info = get_district_contact_info(district)
                    context += f"\n\n{district_contact_info}"
                
                # 쓰레기 처리 관련 구체적인 프롬프트 사용
                waste_prompt_template = get_waste_management_prompt_template(prompt_lang)
                prompt = waste_prompt_template.format(context=context, query=combined_query, district=district)
                
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel("gemini-2.0-flash-lite")
                response = model.generate_content(prompt, generation_config={"max_output_tokens": 1000, "temperature": 0.1})
                answer = response.text.strip()
                return answer
    
    # 쓰레기 처리 관련 질문인지 확인
    if is_waste_related_query(query):
        print(f"  - 쓰레기 처리 관련 질문 감지됨")
        
        # 대화 컨텍스트에 쓰레기 질문 저장
        if conversation_context is not None:
            conversation_context['waste_query'] = query
        
        # 질문에서 구군명 추출
        district = extract_district_from_query(query)
        
        # 질문에 구군명이 없으면 대화 컨텍스트에서 확인
        if not district and previous_district:
            district = previous_district
            print(f"  - 대화 컨텍스트에서 구군명 사용: {district}")
        
        if district:
            print(f"  - 구군명 감지됨: {district}")
            # 대화 컨텍스트에 구군명 저장
            if conversation_context is not None:
                conversation_context['waste_district'] = district
            
            # 쓰레기 처리 관련 문서들을 직접 찾기
            waste_docs = []
            for doc in vector_db.documents:
                if isinstance(doc, dict) and 'metadata' in doc:
                    metadata = doc['metadata']
                    if 'category' in metadata and metadata['category'] == '쓰레기처리':
                        if 'gu_name' in metadata and metadata['gu_name'] == district:
                            waste_docs.append(doc)
            
            # 메타데이터로 찾지 못한 경우, 내용 기반으로 검색
            if not waste_docs:
                print(f"  - 메타데이터로 {district} 관련 쓰레기 처리 문서를 찾지 못함, 내용 기반 검색 시도")
                for doc in vector_db.documents:
                    if isinstance(doc, dict) and 'page_content' in doc:
                        content = doc['page_content'].lower()
                        # 구군명과 쓰레기 관련 키워드가 모두 포함된 문서 찾기
                        if district.lower() in content and any(keyword in content for keyword in ['쓰레기', '폐기물', '배출', '종량제', '봉투', '수거']):
                            waste_docs.append(doc)
            
            if waste_docs:
                print(f"  - {district} 관련 쓰레기 처리 문서 {len(waste_docs)}개 찾음")
                
                # 특정 품목 정보 확인
                specific_item_found = False
                for doc in waste_docs:
                    if doc['metadata'].get('type') == 'large_waste_info':
                        content = doc['page_content']
                        # 질문에서 특정 품목 추출
                        specific_items = ["책상", "소파", "침대", "장롱", "냉장고", "TV", "세탁기", "에어컨", "자전거", "유모차", "화분", "고양이타워", "피아노", "운동기구", "보일러", "천막"]
                        for item in specific_items:
                            if item in query and item in content:
                                specific_item_found = True
                                break
                        if specific_item_found:
                            break
                
                context = "\n\n".join([doc['page_content'] for doc in waste_docs])
                
                # 특정 품목 정보가 부족한 경우 추가 안내 포함
                if not specific_item_found:
                    # 구별 연락처 정보 추가
                    district_contact_info = get_district_contact_info(district)
                    context += f"\n\n{district_contact_info}"
                
                # 쓰레기 처리 관련 구체적인 프롬프트 사용
                waste_prompt_template = get_waste_management_prompt_template(prompt_lang)
                prompt = waste_prompt_template.format(context=context, query=query, district=district)
            else:
                print(f"  - {district} 관련 쓰레기 처리 문서를 찾을 수 없음, 전체 문서 사용")
                relevant_chunks = retrieve_relevant_chunks(query, vector_db)
                context = "\n\n".join([doc['page_content'] if isinstance(doc, dict) and 'page_content' in doc else str(doc) for doc in relevant_chunks])
                foreign_worker_prompt_template = get_foreign_worker_prompt_template(prompt_lang)
                prompt = foreign_worker_prompt_template.format(context=context, query=query)
        else:
            print(f"  - 구군명이 감지되지 않음, 구군 선택 요청")
            return get_district_selection_prompt(prompt_lang)
    else:
        # 일반 질문 처리 (쓰레기 처리 관련이 아닌 경우)
        print(f"  - 일반 질문 처리 (쓰레기 처리 관련 아님)")
        foreign_worker_prompt_template = get_foreign_worker_prompt_template(prompt_lang)
    relevant_chunks = retrieve_relevant_chunks(query, vector_db)
    if not relevant_chunks:
        return "참고 정보에서 관련 내용을 찾을 수 없습니다."
    context = "\n\n".join([doc['page_content'] if isinstance(doc, dict) and 'page_content' in doc else str(doc) for doc in relevant_chunks])
    prompt = foreign_worker_prompt_template.format(context=context, query=query)
    
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    response = model.generate_content(prompt, generation_config={"max_output_tokens": 1000, "temperature": 0.1})
    answer = response.text.strip()
    
    # 마크다운 문법 정리
    clean_answer = clean_markdown_text(answer)
    return clean_answer

def get_or_create_vector_db_multi(pdf_paths, gemini_api_key):
    """여러 PDF를 한 번에 임베딩해서 하나의 벡터DB로 저장합니다."""
    all_chunks = []
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"PDF 파일이 존재하지 않습니다: {pdf_path}")
            continue
        print(f"PDF 파일 확인됨: {os.path.abspath(pdf_path)}")
        chunks = chunk_pdf_to_text_chunks(pdf_path)
        all_chunks.extend(chunks)
        print(f"{pdf_path} → 청크 {len(chunks)}개")
    print(f"총 청크 개수: {len(all_chunks)}")
    if not all_chunks:
        print("임베딩할 청크가 없습니다.")
        return None
    embeddings = GeminiEmbeddings(gemini_api_key)
    doc_embeddings = embeddings.embed_documents([doc['page_content'] for doc in all_chunks])
    vector_db = SimpleVectorDB(all_chunks, embeddings, doc_embeddings)
    with open("vector_db_multi.pkl", "wb") as f:
        pickle.dump(vector_db, f)
    print("벡터DB 저장 완료: vector_db_multi.pkl")
    return vector_db

def merge_vector_dbs(db_paths, gemini_api_key, save_path="다문화.pkl"):
    """여러 벡터DB(pkl)를 병합하여 하나의 벡터DB로 만듭니다."""
    all_chunks = []
    for db_path in db_paths:
        if not os.path.exists(db_path):
            print(f"DB 파일이 존재하지 않습니다: {db_path}")
            continue
        with open(db_path, "rb") as f:
            db = pickle.load(f)
            all_chunks.extend(db.documents)
    print(f"총 합쳐진 청크 개수: {len(all_chunks)}")
    if not all_chunks:
        print("합칠 청크가 없습니다.")
        return None
    embeddings = GeminiEmbeddings(gemini_api_key)
    doc_embeddings = embeddings.embed_documents([doc['page_content'] for doc in all_chunks])
    vector_db = SimpleVectorDB(all_chunks, embeddings, doc_embeddings)
    with open(save_path, "wb") as f:
        pickle.dump(vector_db, f)
    print(f"병합 벡터DB 저장 완료: {save_path}")
    return vector_db

# LangGraph 기반 개선된 RAG 함수들
def create_langgraph_rag_system(gemini_api_key: str, vector_db_path: str, target_lang: str = "ko"):
    """LangGraph 기반 RAG 시스템 생성"""
    print(f"🔍 LangGraph RAG 시스템 생성 시작...")
    print(f"   - API Key: {'있음' if gemini_api_key else '없음'}")
    print(f"   - Vector DB Path: {vector_db_path}")
    print(f"   - Target Lang: {target_lang}")
    
    if not LANGGRAPH_AVAILABLE:
        print("LangGraph를 사용할 수 없습니다. 기본 RAG 시스템을 사용합니다.")
        return None
    
    try:
        print("LangGraph 사용 가능 확인됨")
        
        # LLM 설정 - API 키를 환경변수로 설정
        print("🤖 LLM 설정 중...")
        import os
        os.environ["GOOGLE_API_KEY"] = gemini_api_key
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            temperature=0.1,
            max_output_tokens=2000,
            google_api_key=gemini_api_key  # 명시적으로 API 키 전달
        )
        print("LLM 설정 완료")
        
        # 임베딩 모델 설정
        print("🔤 임베딩 모델 설정 중...")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=gemini_api_key  # 명시적으로 API 키 전달
        )
        print("임베딩 모델 설정 완료")
        
        # 벡터스토어 로드
        print("📚 벡터스토어 로드 중...")
        vector_store = load_vector_store_for_langgraph(vector_db_path, embeddings)
        if not vector_store:
            print("벡터스토어 로드 실패")
            return None
        print("벡터스토어 로드 완료")
        
        # RAG 그래프 생성
        print("🔄 RAG 그래프 생성 중...")
        rag_graph = create_rag_workflow(llm, vector_store, target_lang)
        print("RAG 그래프 생성 완료")
        
        result = {
            "graph": rag_graph,
            "vector_store": vector_store,
            "llm": llm,
            "embeddings": embeddings
        }
        
        print("🎉 LangGraph RAG 시스템 생성 완료!")
        return result
        
    except Exception as e:
        print(f"LangGraph RAG 시스템 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_vector_store_for_langgraph(vector_db_path: str, embeddings):
    """기존 벡터DB를 LangChain 벡터스토어로 변환"""
    print(f"📖 벡터DB 파일 로드 중: {vector_db_path}")
    
    try:
        # 파일 존재 확인
        if not os.path.exists(vector_db_path):
            print(f"벡터DB 파일이 존재하지 않습니다: {vector_db_path}")
            return None
        
        print("📄 벡터DB 파일 읽는 중...")
        with open(vector_db_path, 'rb') as f:
            vector_db = pickle.load(f)
        
        print(f"📊 벡터DB 로드 완료: {len(vector_db.documents)}개 문서")
        
        # 문서와 임베딩 추출
        documents = []
        embeddings_list = []
        
        print("🔍 문서 및 임베딩 추출 중...")
        for i, doc in enumerate(vector_db.documents):
            if isinstance(doc, dict) and 'page_content' in doc:
                documents.append(doc['page_content'])
                if hasattr(vector_db, 'doc_embeddings') and vector_db.doc_embeddings:
                    if i < len(vector_db.doc_embeddings):
                        embeddings_list.append(vector_db.doc_embeddings[i])
        
        print(f"📝 추출된 문서: {len(documents)}개")
        print(f"🔢 추출된 임베딩: {len(embeddings_list)}개")
        
        # FAISS 벡터스토어 생성 - from_texts 사용
        print("🏗️ FAISS 벡터스토어 생성 중...")
        print("🔄 새로운 임베딩 생성하여 벡터스토어 생성")
        vector_store = FAISS.from_texts(
            documents, 
            embeddings
        )
        
        print(f"LangGraph 벡터스토어 로드 완료: {len(documents)}개 문서")
        return vector_store
        
    except Exception as e:
        print(f"벡터스토어 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_rag_workflow(llm, vector_store, target_lang: str = "ko"):
    """LangGraph 기반 RAG 워크플로우 생성 (개선된 버전)"""
    
    # 1. 질문 분석 노드
    def analyze_query(state):
        """질문 유형 분석 및 검색 전략 결정"""
        query = state["query"]
        target_lang = state.get("target_lang", "ko")
        
        # 이전 대화 맥락 확인 (구군명만 입력된 경우)
        is_district_only = False
        district_name = None
        
        # 구군명 패턴 확인
        district_patterns = [
            "중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", 
            "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"
        ]
        
        for pattern in district_patterns:
            if pattern in query:
                district_name = pattern
                is_district_only = True
                break
        
        # 질문 유형 분석
        query_type = "general"
        search_strategies = []
        enhanced_query = query
        
        if is_district_only:
            # 구군명만 입력된 경우, 이전 맥락을 고려한 검색 쿼리 생성
            query_type = "district_info"
            search_strategies = ["context_aware", "semantic_search"]
            # 기본적으로 생활 정보 검색
            enhanced_query = f"부산 {district_name} 생활 정보"
        elif any(keyword in query.lower() for keyword in ["쓰레기", "폐기물", "배출"]):
            query_type = "waste_management"
            search_strategies = ["exact_match", "semantic_search"]
            enhanced_query = f"부산 {query}"
        elif any(keyword in query.lower() for keyword in ["맛집", "음식", "식당"]):
            query_type = "restaurant"
            search_strategies = ["location_based", "semantic_search"]
            enhanced_query = f"부산 {query}"
        elif any(keyword in query.lower() for keyword in ["권리", "법률", "근로자"]):
            query_type = "worker_rights"
            search_strategies = ["semantic_search", "keyword_search"]
        else:
            search_strategies = ["semantic_search"]
        
        # 검색 파라미터 조정
        k = 3 if query_type == "waste_management" else 5
        
        return {
            "query": query,
            "target_lang": target_lang,
            "enhanced_query": enhanced_query,
            "query_type": query_type,
            "district_name": district_name,
            "is_district_only": is_district_only,
            "k": k,
            "search_strategies": search_strategies,
            "retry_count": 0,
            "max_retries": 2
        }
    
    # 2. 다중 검색 노드
    def multi_search_documents(state):
        """여러 검색 전략을 사용한 문서 검색"""
        query = state["query"]
        enhanced_query = state.get("enhanced_query", query)
        search_strategies = state.get("search_strategies", ["semantic_search"])
        k = state.get("k", 5)
        query_type = state.get("query_type", "general")
        district_name = state.get("district_name")
        
        all_docs = []
        
        for strategy in search_strategies:
            if strategy == "semantic_search":
                docs = vector_store.similarity_search(enhanced_query, k=k)
                all_docs.extend(docs)
            elif strategy == "exact_match":
                # 정확한 키워드 매칭 검색
                exact_docs = vector_store.similarity_search(enhanced_query, k=k//2)
                all_docs.extend(exact_docs)
            elif strategy == "location_based":
                # 위치 기반 검색 (부산 관련)
                location_query = f"부산 {query}"
                location_docs = vector_store.similarity_search(location_query, k=k//2)
                all_docs.extend(location_docs)
            elif strategy == "keyword_search":
                # 키워드 기반 검색
                keywords = query.split()
                for keyword in keywords[:3]:  # 상위 3개 키워드만 사용
                    keyword_docs = vector_store.similarity_search(keyword, k=k//3)
                    all_docs.extend(keyword_docs)
            elif strategy == "context_aware":
                # 문맥 인식 검색 (구군명 + 생활 정보)
                if district_name:
                    context_queries = [
                        f"부산 {district_name} 생활 정보",
                        f"부산 {district_name} 쓰레기 배출",
                        f"부산 {district_name} 의료",
                        f"부산 {district_name} 교육",
                        f"부산 {district_name} 교통"
                    ]
                    for context_query in context_queries:
                        context_docs = vector_store.similarity_search(context_query, k=k//5)
                        all_docs.extend(context_docs)
        
        # 중복 제거 및 정렬
        unique_docs = []
        seen_contents = set()
        for doc in all_docs:
            if doc.page_content not in seen_contents:
                unique_docs.append(doc)
                seen_contents.add(doc.page_content)
        
        context = "\n\n".join([doc.page_content for doc in unique_docs[:k*2]])
        
        return {
            "query": query,
            "target_lang": state.get("target_lang", "ko"),
            "enhanced_query": enhanced_query,
            "query_type": query_type,
            "district_name": district_name,
            "is_district_only": state.get("is_district_only", False),
            "k": k,
            "search_strategies": search_strategies,
            "retry_count": state.get("retry_count", 0),
            "max_retries": state.get("max_retries", 2),
            "context": context, 
            "documents": unique_docs,
            "search_strategies_used": search_strategies
        }
    
    # 3. 컨텍스트 강화 노드
    def enhance_context(state):
        """컨텍스트를 강화하고 관련성 높은 정보만 필터링"""
        context = state.get("context", "")
        query = state["query"]
        query_type = state.get("query_type", "general")
        
        # 컨텍스트가 너무 길면 요약
        if len(context) > 3000:
            sentences = context.split('.')
            relevant_sentences = []
            
            # 질문 키워드 기반 관련성 점수 계산
            query_keywords = query.lower().split()
            
            for sentence in sentences:
                relevance_score = 0
                for keyword in query_keywords:
                    if keyword in sentence.lower():
                        relevance_score += 1
                
                if relevance_score > 0:
                    relevant_sentences.append((sentence, relevance_score))
            
            # 관련성 점수로 정렬
            relevant_sentences.sort(key=lambda x: x[1], reverse=True)
            
            if relevant_sentences:
                context = '. '.join([s[0] for s in relevant_sentences[:10]])
            else:
                context = '. '.join(sentences[:5])
        
        # 컨텍스트 품질 평가
        context_quality = len(context) / 100  # 간단한 품질 지표
        needs_retry = context_quality < 2.0  # 품질이 낮으면 재검색
        
        return {
            "query": query,
            "target_lang": target_lang,
            "query_type": query_type,
            "k": state.get("k", 5),
            "search_strategies": state.get("search_strategies", ["semantic_search"]),
            "retry_count": state.get("retry_count", 0),
            "max_retries": state.get("max_retries", 2),
            "enhanced_context": context,
            "context_quality": context_quality,
            "needs_retry": needs_retry
        }
    
    # 4. 답변 생성 노드
    def generate_answer(state):
        """최종 답변 생성"""
        query = state["query"]
        context = state.get("enhanced_context", "")
        query_type = state.get("query_type", "general")
        district_name = state.get("district_name")
        is_district_only = state.get("is_district_only", False)
        retry_count = state.get("retry_count", 0)
        target_lang = state.get("target_lang", "ko")
        
        # 구군명만 입력된 경우 특별 처리
        if is_district_only and district_name:
            # 구체적인 정보가 있는지 확인
            if any(keyword in context.lower() for keyword in ["쓰레기", "배출", "폐기물"]):
                # 쓰레기 관련 정보가 있으면 쓰레기 배출 안내
                enhanced_query = f"부산 {district_name} 쓰레기 배출 방법"
            elif any(keyword in context.lower() for keyword in ["의료", "병원", "진료"]):
                # 의료 관련 정보가 있으면 의료 안내
                enhanced_query = f"부산 {district_name} 의료 정보"
            elif any(keyword in context.lower() for keyword in ["교육", "학교", "학원"]):
                # 교육 관련 정보가 있으면 교육 안내
                enhanced_query = f"부산 {district_name} 교육 정보"
            else:
                # 기본적으로 생활 정보 안내
                enhanced_query = f"부산 {district_name} 생활 정보"
        else:
            enhanced_query = query
        
        # 언어별 프롬프트 템플릿
        templates = {
            "ko": """당신은 다문화가족을 위한 한국생활안내 챗봇입니다. 
다음은 참고 정보입니다. 정확하고 도움이 되는 답변을 한국어로 해주세요.

[참고 정보]
{context}

질문: {query}

답변 지침:
1. 사용자가 구군명만 입력한 경우, 이전 대화 맥락을 고려하여 적절한 정보를 제공하세요.
2. 쓰레기 처리 관련 질문이었다면 해당 구의 쓰레기 배출 방법을 안내하세요.
3. 다른 생활 정보 질문이었다면 해당 구의 관련 정보를 제공하세요.
4. 구체적이고 실용적인 정보를 제공하세요.
5. 답변이 불충분하거나 관련성이 낮다면 "해당 정보를 찾을 수 없습니다"라고 답변하세요.
6. 다문화가족의 관점에서 이해하기 쉽게 설명하세요.

답변:""",
            
            "en": """You are a Korean life guidance chatbot for multicultural families.
Here is reference information. Please provide accurate and helpful answers in English.

[Reference Information]
{context}

Question: {query}

Answer Guidelines:
1. If the user only enters a district name, provide appropriate information considering the previous conversation context.
2. If it was a waste disposal question, guide the waste disposal method for that district.
3. If it was another life information question, provide relevant information for that district.
4. Provide specific and practical information.
5. If the answer is insufficient or not relevant, say "I cannot find the relevant information."
6. Explain in a way that multicultural families can easily understand.

Answer:""",
            
            "ja": """あなたは多文化家族のための韓国生活案内チャットボットです。
以下は参考情報です。正確で役立つ回答を日本語でお願いします。

[参考情報]
{context}

質問: {query}

回答ガイドライン:
1. ユーザーが区郡名のみを入力した場合、前の会話の文脈を考慮して適切な情報を提供してください。
2. ごみ処理に関する質問だった場合は、その区のごみ排出方法を案内してください。
3. 他の生活情報の質問だった場合は、その区の関連情報を提供してください。
4. 具体的で実用的な情報を提供してください。
5. 回答が不十分または関連性が低い場合は「該当する情報が見つかりません」と答えてください。
6. 多文化家族の観点から理解しやすく説明してください。

回答:""",
            
            "zh": """您是面向多文化家庭的韩国生活指导聊天机器人。
以下是参考信息。请用中文提供准确有用的答案。

[参考信息]
{context}

问题: {query}

答案指南:
1. 如果用户只输入区郡名，请考虑之前对话的上下文提供适当的信息。
2. 如果是垃圾处理相关问题，请指导该区的垃圾排放方法。
3. 如果是其他生活信息问题，请提供该区的相关信息。
4. 提供具体实用的信息。
5. 如果答案不充分或相关性低，请说"找不到相关信息"。
6. 从多文化家庭的角度进行易于理解的说明。

答案:""",
            
            "vi": """Bạn là chatbot hướng dẫn cuộc sống Hàn Quốc cho các gia đình đa văn hóa.
Đây là thông tin tham khảo. Vui lòng cung cấp câu trả lời chính xác và hữu ích bằng tiếng Việt.

[Thông tin tham khảo]
{context}

Câu hỏi: {query}

Hướng dẫn trả lời:
1. Nếu người dùng chỉ nhập tên quận/huyện, hãy cung cấp thông tin phù hợp xem xét ngữ cảnh cuộc trò chuyện trước đó.
2. Nếu là câu hỏi về xử lý rác thải, hãy hướng dẫn phương pháp thải rác cho quận/huyện đó.
3. Nếu là câu hỏi thông tin cuộc sống khác, hãy cung cấp thông tin liên quan cho quận/huyện đó.
4. Cung cấp thông tin cụ thể và thực tế.
5. Nếu câu trả lời không đủ hoặc không liên quan, hãy nói "Tôi không thể tìm thấy thông tin liên quan."
6. Giải thích theo cách mà các gia đình đa văn hóa có thể dễ dàng hiểu.

Trả lời:"""
        }
        
        template = templates.get(target_lang, templates["ko"])
        prompt = ChatPromptTemplate.from_template(template)
        
        # 체인 구성
        chain = prompt | llm | StrOutputParser()
        
        # 답변 생성
        try:
            answer = chain.invoke({
                "context": context,
                "query": enhanced_query
            })
            
            # 답변 후처리
            answer = post_process_answer(answer, query_type)
            
            # 구군명만 입력된 경우 추가 처리
            if is_district_only and district_name:
                # 답변이 너무 일반적이거나 관련성이 낮으면 구체적인 안내 추가
                if len(answer) < 50 or "찾을 수 없습니다" in answer:
                    answer = f"부산광역시 {district_name}의 생활 정보를 안내해드리겠습니다.\n\n{answer}\n\n더 구체적인 정보가 필요하시면 '쓰레기 배출', '의료 정보', '교육 정보' 등 구체적인 항목을 말씀해 주세요."
            
            # 답변 품질 평가
            answer_quality = evaluate_answer_quality(answer, enhanced_query, context)
            
            return {
                "query": query,
                "target_lang": target_lang,
                "enhanced_query": enhanced_query,
                "query_type": query_type,
                "district_name": district_name,
                "is_district_only": is_district_only,
                "k": state.get("k", 5),
                "search_strategies": state.get("search_strategies", ["semantic_search"]),
                "retry_count": retry_count,
                "max_retries": state.get("max_retries", 2),
                "answer": answer,
                "answer_quality": answer_quality,
                "needs_retry": state.get("needs_retry", False)
            }
        except Exception as e:
            print(f"답변 생성 오류: {e}")
            return {
                "query": query,
                "target_lang": target_lang,
                "enhanced_query": enhanced_query,
                "query_type": query_type,
                "district_name": district_name,
                "is_district_only": is_district_only,
                "k": state.get("k", 5),
                "search_strategies": state.get("search_strategies", ["semantic_search"]),
                "retry_count": retry_count,
                "max_retries": state.get("max_retries", 2),
                "answer": "죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다.",
                "answer_quality": 0,
                "needs_retry": state.get("needs_retry", False)
            }
    
    # 5. 답변 검증 노드
    def validate_answer(state):
        """생성된 답변의 품질 검증"""
        answer = state.get("answer", "")
        query = state["query"]
        answer_quality = state.get("answer_quality", 0)
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)
        needs_retry = state.get("needs_retry", False)
        
        # 답변 품질이 낮거나 재검색이 필요한 경우
        should_retry = (
            answer_quality < 0.5 or 
            needs_retry or 
            "찾을 수 없습니다" in answer or
            "cannot find" in answer.lower() or
            "관련" in answer and "없습니다" in answer
        )
        
        if should_retry and retry_count < max_retries:
            # 재검색을 위해 검색 파라미터 조정
            new_k = state.get("k", 5) + 2  # 더 많은 문서 검색
            new_strategies = state.get("search_strategies", ["semantic_search"]) + ["keyword_search"]
            
            return {
                "query": query,
                "target_lang": target_lang,
                "query_type": state.get("query_type", "general"),
                "k": new_k,
                "search_strategies": new_strategies,
                "retry_count": retry_count + 1,
                "max_retries": max_retries,
                "should_retry": True
            }
        else:
            return {
                "query": query,
                "target_lang": target_lang,
                "query_type": state.get("query_type", "general"),
                "k": state.get("k", 5),
                "search_strategies": state.get("search_strategies", ["semantic_search"]),
                "retry_count": retry_count,
                "max_retries": max_retries,
                "should_retry": False,
                "final_answer": answer
            }
    
    # 6. 답변 후처리
    def post_process_answer(answer: str, query_type: str) -> str:
        """답변 품질 개선 및 후처리"""
        # 마크다운 정리
        answer = answer.replace("**", "").replace("*", "")
        
        # 불필요한 문구 제거
        answer = answer.replace("참고 정보를 바탕으로", "").replace("Based on the reference information", "")
        
        # 답변이 너무 짧으면 보완
        if len(answer) < 50:
            answer += "\n\n더 자세한 정보가 필요하시면 추가 질문해 주세요."
        
        return answer.strip()
    
    # 7. 답변 품질 평가
    def evaluate_answer_quality(answer: str, query: str, context: str) -> float:
        """답변 품질을 평가하는 함수"""
        if not answer or len(answer) < 20:
            return 0.0
        
        # 간단한 품질 지표들
        quality_score = 0.0
        
        # 길이 점수
        length_score = min(len(answer) / 200, 1.0)
        quality_score += length_score * 0.3
        
        # 키워드 매칭 점수
        query_keywords = set(query.lower().split())
        answer_keywords = set(answer.lower().split())
        keyword_overlap = len(query_keywords.intersection(answer_keywords)) / max(len(query_keywords), 1)
        quality_score += keyword_overlap * 0.4
        
        # 컨텍스트 활용 점수
        context_keywords = set(context.lower().split()[:50])  # 상위 50개 키워드
        context_usage = len(answer_keywords.intersection(context_keywords)) / max(len(answer_keywords), 1)
        quality_score += context_usage * 0.3
        
        return min(quality_score, 1.0)
    
    # 그래프 구성
    workflow = StateGraph(dict)
    
    # 노드 추가
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("multi_search_documents", multi_search_documents)
    workflow.add_node("enhance_context", enhance_context)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("validate_answer", validate_answer)
    
    # 엣지 연결 (조건부 분기 포함)
    workflow.set_entry_point("analyze_query")
    workflow.add_edge("analyze_query", "multi_search_documents")
    workflow.add_edge("multi_search_documents", "enhance_context")
    workflow.add_edge("enhance_context", "generate_answer")
    workflow.add_edge("generate_answer", "validate_answer")
    
    # 조건부 분기: 재검색이 필요한 경우
    def should_retry(state):
        return state.get("should_retry", False)
    
    workflow.add_conditional_edges(
        "validate_answer",
        should_retry,
        {
            True: "multi_search_documents",  # 재검색
            False: END  # 완료
        }
    )
    
    # 그래프 컴파일
    return workflow.compile()

def answer_with_langgraph_rag(query: str, vector_db, gemini_api_key: str, target_lang: str = "ko"):
    """LangGraph 기반 RAG 답변 생성"""
    print(f"LangGraph RAG 답변 생성 시작...")
    print(f"   - 질문: {query}")
    print(f"   - 언어: {target_lang}")
    print(f"   - API Key: {'있음' if gemini_api_key else '없음'}")
    
    if not LANGGRAPH_AVAILABLE:
        print("LangGraph를 사용할 수 없습니다. 기본 RAG를 사용합니다.")
        return answer_with_rag(query, vector_db, gemini_api_key, target_lang=target_lang)
    
    try:
        print("LangGraph 사용 가능 확인됨")
        
        # 벡터DB 경로 추출
        vector_db_path = None
        if hasattr(vector_db, 'documents'):
            print(f"📊 벡터DB 문서 수: {len(vector_db.documents)}")
            # 임시로 벡터DB를 파일로 저장
            vector_db_path = "temp_vector_db.pkl"
            print(f"💾 임시 벡터DB 파일 생성: {vector_db_path}")
            with open(vector_db_path, 'wb') as f:
                pickle.dump(vector_db, f)
            print("임시 벡터DB 파일 저장 완료")
        else:
            print("벡터DB에 documents 속성이 없습니다")
            return answer_with_rag(query, vector_db, gemini_api_key, target_lang=target_lang)
        
        # LangGraph RAG 시스템 생성
        print("🔧 LangGraph RAG 시스템 생성 중...")
        rag_system = create_langgraph_rag_system(gemini_api_key, vector_db_path, target_lang)
        if not rag_system:
            print("LangGraph RAG 시스템 생성 실패, 기본 RAG 사용")
            return answer_with_rag(query, vector_db, gemini_api_key, target_lang=target_lang)
        
        print("LangGraph RAG 시스템 생성 완료")
        
        # 그래프 실행
        print("🔄 LangGraph 워크플로우 실행 중...")
        initial_state = {
            "query": query,
            "target_lang": target_lang
        }
        
        result = rag_system["graph"].invoke(initial_state)
        print("LangGraph 워크플로우 실행 완료")
        
        # 임시 파일 정리
        if vector_db_path and os.path.exists(vector_db_path):
            os.remove(vector_db_path)
            print("🗑️ 임시 벡터DB 파일 삭제 완료")
        
        answer = result.get("answer", "답변을 생성할 수 없습니다.")
        print(f"📝 최종 답변 길이: {len(answer)}자")
        return answer
        
    except Exception as e:
        print(f"LangGraph RAG 오류: {e}")
        import traceback
        traceback.print_exc()
        # 오류 발생 시 기본 RAG 사용
        print("🔄 기본 RAG로 폴백...")
        return answer_with_rag(query, vector_db, gemini_api_key, target_lang=target_lang)

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    
    # API Key 디버깅
    print("=== API Key 확인 ===")
    if not api_key:
        print("환경변수 GEMINI_API_KEY가 설정되어 있지 않습니다.")
        print("환경변수 설정 방법:")
        print("Windows: set GEMINI_API_KEY=your-api-key-here")
        print("Linux/Mac: export GEMINI_API_KEY=your-api-key-here")
        exit(1)
    else:
        print(f"API Key 확인됨: {api_key[:10]}...{api_key[-4:]}")
    
    # 캐시 상태 확인
    print("\n=== 캐시 상태 확인 ===")
    cache_status = get_cache_status()
    print(f"상태: {cache_status['status']}")
    print(f"메시지: {cache_status.get('message', '')}")
    if 'current_hash' in cache_status:
        print(f"현재 파일 해시: {cache_status['current_hash']}")
        print(f"캐시된 파일 해시: {cache_status['cached_hash']}")
        print(f"청크 수: {cache_status['chunk_count']}")
    
    print("\n=== 벡터DB 준비 ===")
    vector_db = get_or_create_vector_db(api_key)
    print("임베딩/DB 준비 완료!")

    # 직접 질문 입력 반복
    while True:
        query = input("\n질문을 입력하세요(엔터만 입력 시 종료): ").strip()
        if not query:
            print("종료합니다.")
            break
        
        print(f"\n질문: {query}")
        print("유사 청크 검색 중...")
        docs = retrieve_relevant_chunks(query, vector_db)
        print(f"찾은 유사 청크 수: {len(docs)}")
        
        print("\n유사 청크 미리보기:")
        for i, doc in enumerate(docs):
            print(f"--- 청크 {i+1} ---\n{doc['page_content'][:300]}\n")
        
        print("Gemini API로 답변 생성 중...")
        answer = answer_with_rag(query, vector_db, api_key)
        print(f"\nGemini RAG 답변: {answer}\n") 

    # 1~64.pdf 임베딩 및 저장
    pdf_paths_64 = [f"pdf/{i}.pdf" for i in range(1, 65)]
    get_or_create_vector_db_multi(pdf_paths_64, api_key)
    # 64개 PDF 임베딩 결과를 별도 파일로 저장
    shutil.copy("vector_db_multi.pkl", "vector_db_64multi.pkl")
    # 기존 단일 PDF DB와 병합
    db_paths = ["vector_db.pkl", "vector_db_64multi.pkl"]
    merge_vector_dbs(db_paths, api_key, save_path="다문화.pkl")

def get_detailed_alien_registration_guide(target_lang="ko"):
    """외국인 등록에 대한 상세한 안내를 제공합니다."""
    guides = {
        "ko": """📋 **외국인 등록 완전 가이드**

🏢 **신청 장소**
• 거주지 관할 출입국관리사무소 또는 출장소
• 시군구청 (일부 업무만 가능)

📅 **신청 기한**
• 입국일로부터 90일 이내 (필수!)
• 지연 시 과태료 부과 (10만원~100만원)

📋 **필요 서류**
- 외국인등록 신청서 (현장 작성)
- 여권 원본
- 여권용 사진 1매 (3.5cm × 4.5cm, 6개월 이내 촬영)
- 수수료 3만원
- 체류자격별 추가 서류:
   - 결혼이민: 혼인관계증명서, 가족관계증명서
   - 취업: 근로계약서, 사업자등록증 사본
   - 유학: 재학증명서, 학비납입증명서

⏰ **처리 기간**
• 신청 후 7~10일 (영업일 기준)
• 등록증 발급 완료 시 문자 통지

🏢 **부산 출입국관리사무소**
• 주소: 부산시 동구 범일로 179
• 전화: 051-461-3000
• 운영시간: 평일 09:00~18:00

💡 **주의사항**
• 체류기간 만료 전 연장 신청 필수
• 주소 변경 시 14일 이내 신고
• 분실 시 즉시 재발급 신청

🌐 **온라인 서비스**
• 하이코리아(www.hikorea.go.kr)에서 일부 업무 가능
• 체류기간 연장, 체류자격 변경 등

📞 **다국어 상담**
• 1345 콜센터 (한국어, 영어, 중국어, 베트남어 등)
• 평일 09:00~22:00, 주말 09:00~18:00""",
        
        "en": """📋 **Complete Alien Registration Guide**

🏢 **Application Location**
• Immigration office in your residential area
• District/city office (limited services)

📅 **Application Deadline**
• Within 90 days from entry date (MANDATORY!)
• Late application penalty: 100,000~1,000,000 KRW

📋 **Required Documents**
- Alien Registration Application Form (fill on-site)
- Original passport
- Passport photo (3.5cm × 4.5cm, taken within 6 months)
- Fee: 30,000 KRW
- Additional documents by visa type:
   - Marriage: Marriage certificate, family relation certificate
   - Work: Employment contract, business registration
   - Study: Enrollment certificate, tuition payment proof

⏰ **Processing Time**
• 7-10 business days after application
• SMS notification when ready

🏢 **Busan Immigration Office**
• Address: 179 Beomil-ro, Dong-gu, Busan
• Phone: 051-461-3000
• Hours: Weekdays 09:00~18:00

💡 **Important Notes**
• Must extend before visa expiration
• Report address change within 14 days
• Apply for reissuance immediately if lost

🌐 **Online Services**
• Some services available at www.hikorea.go.kr
• Visa extension, status change, etc.

📞 **Multilingual Support**
• 1345 Call Center (Korean, English, Chinese, Vietnamese, etc.)
• Weekdays 09:00~22:00, Weekends 09:00~18:00""",
        
        "vi": """📋 **Hướng Dẫn Đăng Ký Người Nước Ngoài Hoàn Chỉnh**

🏢 **Nơi Nộp Đơn**
• Văn phòng xuất nhập cảnh khu vực cư trú
• Văn phòng quận/thành phố (dịch vụ hạn chế)

📅 **Thời Hạn Nộp Đơn**
• Trong vòng 90 ngày kể từ ngày nhập cảnh (BẮT BUỘC!)
• Phạt nộp muộn: 100,000~1,000,000 KRW

📋 **Giấy Tờ Cần Thiết**
- Đơn đăng ký người nước ngoài (điền tại chỗ)
- Hộ chiếu gốc
- Ảnh hộ chiếu (3.5cm × 4.5cm, chụp trong 6 tháng)
- Phí: 30,000 KRW
- Giấy tờ bổ sung theo loại visa:
   - Kết hôn: Giấy chứng nhận hôn nhân, quan hệ gia đình
   - Làm việc: Hợp đồng lao động, đăng ký kinh doanh
   - Du học: Giấy chứng nhận học tập, chứng minh đóng học phí

⏰ **Thời Gian Xử Lý**
• 7-10 ngày làm việc sau khi nộp đơn
• Thông báo SMS khi hoàn thành

🏢 **Văn Phòng Xuất Nhập Cảnh Busan**
• Địa chỉ: 179 Beomil-ro, Dong-gu, Busan
• Điện thoại: 051-461-3000
• Giờ làm việc: Thứ 2-6 09:00~18:00

💡 **Lưu Ý Quan Trọng**
• Phải gia hạn trước khi visa hết hạn
• Báo thay đổi địa chỉ trong 14 ngày
• Cấp lại ngay nếu bị mất

🌐 **Dịch Vụ Trực Tuyến**
• Một số dịch vụ tại www.hikorea.go.kr
• Gia hạn visa, thay đổi tình trạng, v.v.

📞 **Hỗ Trợ Đa Ngôn Ngữ**
• Tổng đài 1345 (Hàn, Anh, Trung, Việt, v.v.)
• Thứ 2-6 09:00~22:00, Cuối tuần 09:00~18:00"""
    }
    
    return guides.get(target_lang, guides["ko"]) 


# 장마철 안전점검표 외국어별 키워드 매핑
JANGMACHUL_KEYWORDS = {
    "ko": [
        "장마철", "자율안전", "점검표",
        "기상특보", "비상대피", "재해취약", "긴급복구", "비상구호",
        "배수로", "배수시설", "지하구조물", "침수", "호우",
        "옹벽", "석축", "붕괴", "매몰", "방수포", "흙막이", "지보공",
        "가설물", "결속상태", "태풍", "강풍", "유리창",
        "충전부", "배전반", "누전차단기", "접지", "절연상태",
        "굴착", "사면", "무너짐", "지반상태", "매설물", "굴착공법",
        "흙막이지보공", "철골공사", "전기공사", "밀폐공간",
        "단부", "개구부", "비계", "작업발판", "사다리", "이동식비계", "달비계",
        "거푸집", "동바리", "굴착기", "고소작업대", "트럭",
        "이동식크레인", "타워크레인", "항타", "항발기", "건설용리프트",
        "용접장치", "용접", "크레인"
    ],
    "en": [
        "rainy season", "safety checklist", "construction site", "safety inspection",
        "weather warning", "emergency evacuation", "disaster vulnerable", "emergency recovery", "emergency supplies",
        "drainage", "drainage facilities", "underground structure", "flooding", "heavy rain",
        "retaining wall", "stone wall", "collapse", "burial", "waterproof", "earth retaining", "shoring",
        "temporary structure", "fastening", "typhoon", "strong wind", "glass window",
        "live parts", "distribution panel", "circuit breaker", "grounding", "insulation",
        "excavation", "slope", "collapse", "ground condition", "buried objects", "excavation method",
        "earth retaining shoring", "steel construction", "electrical work", "confined space",
        "edge", "opening", "scaffold", "work platform", "ladder", "mobile scaffold", "suspended scaffold",
        "formwork", "shores", "excavator", "aerial work platform", "truck",
        "mobile crane", "tower crane", "pile driver", "pile extractor", "construction lift",
        "welding equipment", "welding", "crane"
    ],
    "vi": [
        "mùa mưa", "danh sách kiểm tra an toàn", "công trường xây dựng", "kiểm tra an toàn",
        "cảnh báo thời tiết", "sơ tán khẩn cấp", "dễ bị thiên tai", "phục hồi khẩn cấp", "đồ dùng khẩn cấp",
        "thoát nước", "cơ sở thoát nước", "công trình ngầm", "ngập lụt", "mưa lớn",
        "tường chắn", "tường đá", "sụp đổ", "chôn vùi", "chống thấm", "chắn đất", "chống đỡ",
        "công trình tạm", "buộc chặt", "bão", "gió mạnh", "cửa kính",
        "phần mang điện", "tủ phân phối", "cầu dao", "tiếp đất", "cách điện",
        "đào", "dốc", "sụp đổ", "điều kiện nền", "vật chôn", "phương pháp đào",
        "chống đỡ chắn đất", "xây dựng thép", "công việc điện", "không gian kín",
        "rìa", "lỗ hở", "giàn giáo", "sàn làm việc", "thang", "giàn giáo di động", "giàn giáo treo",
        "ván khuôn", "chống", "máy đào", "sàn làm việc trên cao", "xe tải",
        "cần cẩu di động", "cần cẩu tháp", "máy đóng cọc", "máy rút cọc", "thang máy công trình",
        "thiết bị hàn", "hàn", "cần cẩu"
    ],
    "ja": [
        "梅雨期", "安全点検表", "建設現場", "安全点検",
        "気象警報", "緊急避難", "災害脆弱", "緊急復旧", "緊急用品",
        "排水路", "排水設備", "地下構造物", "浸水", "大雨",
        "擁壁", "石積み", "崩壊", "埋没", "防水", "土留め", "支保工",
        "仮設物", "結束", "台風", "強風", "ガラス窓",
        "充電部", "配電盤", "漏電遮断器", "接地", "絶縁",
        "掘削", "法面", "崩れ", "地盤状態", "埋設物", "掘削工法",
        "土留め支保工", "鉄骨工事", "電気工事", "密閉空間",
        "端部", "開口部", "足場", "作業床", "梯子", "移動式足場", "吊り足場",
        "型枠", "支保", "掘削機", "高所作業台", "トラック",
        "移動式クレーン", "タワークレーン", "杭打ち", "杭抜き", "建設用リフト",
        "溶接装置", "溶接", "クレーン"
    ],
    "zh": [
        "雨季", "安全检查表", "建筑工地", "安全检查",
        "气象预警", "紧急疏散", "灾害脆弱", "紧急恢复", "紧急用品",
        "排水", "排水设施", "地下结构", "洪水", "大雨",
        "挡土墙", "石墙", "坍塌", "掩埋", "防水", "挡土", "支撑",
        "临时结构", "紧固", "台风", "强风", "玻璃窗",
        "带电部分", "配电盘", "断路器", "接地", "绝缘",
        "挖掘", "坡面", "坍塌", "地面条件", "埋藏物", "挖掘方法",
        "挡土支撑", "钢结构", "电气工程", "密闭空间",
        "边缘", "开口", "脚手架", "工作平台", "梯子", "移动脚手架", "悬挂脚手架",
        "模板", "支撑", "挖掘机", "高空作业平台", "卡车",
        "移动式起重机", "塔式起重机", "打桩", "拔桩", "建筑升降机",
        "焊接设备", "焊接", "起重机"
    ],
    "zh-TW": [
        "雨季", "安全檢查表", "建築工地", "安全檢查",
        "氣象預警", "緊急疏散", "災害脆弱", "緊急恢復", "緊急用品",
        "排水", "排水設施", "地下結構", "洪水", "大雨",
        "擋土牆", "石牆", "坍塌", "掩埋", "防水", "擋土", "支撐",
        "臨時結構", "緊固", "颱風", "強風", "玻璃窗",
        "帶電部分", "配電盤", "斷路器", "接地", "絕緣",
        "挖掘", "坡面", "坍塌", "地面條件", "埋藏物", "挖掘方法",
        "擋土支撐", "鋼結構", "電氣工程", "密閉空間",
        "邊緣", "開口", "鷹架", "工作平台", "梯子", "移動式鷹架", "懸掛鷹架",
        "模板", "支撐", "挖掘機", "高空作業平台", "卡車",
        "移動式起重機", "塔式起重機", "打樁", "拔樁", "建築升降機",
        "焊接設備", "焊接", "起重機"
    ],
    "id": [
        "musim hujan", "daftar periksa keselamatan", "lokasi konstruksi", "inspeksi keselamatan",
        "peringatan cuaca", "evakuasi darurat", "rentan bencana", "pemulihan darurat", "persediaan darurat",
        "drainase", "fasilitas drainase", "struktur bawah tanah", "banjir", "hujan deras",
        "dinding penahan", "dinding batu", "runtuh", "tertimbun", "tahan air", "penahan tanah", "penyangga",
        "struktur sementara", "pengikat", "topan", "angin kencang", "jendela kaca",
        "bagian bermuatan", "panel distribusi", "pemutus sirkuit", "pembumian", "insulasi",
        "penggalian", "lereng", "runtuh", "kondisi tanah", "benda terkubur", "metode penggalian",
        "penyangga penahan tanah", "konstruksi baja", "pekerjaan listrik", "ruang terbatas",
        "tepi", "bukaan", "perancah", "platform kerja", "tangga", "perancah bergerak", "perancah gantung",
        "bekisting", "penyangga", "ekskavator", "platform kerja tinggi", "truk",
        "derek bergerak", "derek menara", "pemancang", "pencabut tiang", "lift konstruksi",
        "peralatan las", "las", "derek"
    ],
    "th": [
        "ฤดูฝน", "รายการตรวจสอบความปลอดภัย", "ไซต์ก่อสร้าง", "การตรวจสอบความปลอดภัย",
        "คำเตือนสภาพอากาศ", "การอพยพฉุกเฉิน", "เสี่ยงต่อภัยพิบัติ", "การฟื้นตัวฉุกเฉิน", "เสบียงฉุกเฉิน",
        "ระบายน้ำ", "สิ่งอำนวยความสะดวกระบายน้ำ", "โครงสร้างใต้ดิน", "น้ำท่วม", "ฝนหนัก",
        "กำแพงกันดิน", "กำแพงหิน", "พังทลาย", "ถูกฝัง", "กันน้ำ", "กั้นดิน", "ค้ำยัน",
        "โครงสร้างชั่วคราว", "การยึดแน่น", "ไต้ฝุ่น", "ลมแรง", "หน้าต่างกระจก",
        "ส่วนที่มีไฟฟ้า", "แผงจำหน่าย", "เบรกเกอร์", "ต่อดิน", "ฉนวน",
        "ขุดเจาะ", "ความชัน", "พังทลาย", "สภาพพื้น", "วัตถุที่ฝังอยู่", "วิธีขุดเจาะ",
        "ค้ำยันกั้นดิน", "การก่อสร้างเหล็ก", "งานไฟฟ้า", "พื้นที่ปิด",
        "ขอบ", "ช่องเปิด", "นั่งร้าน", "แพลตฟอร์มทำงาน", "บันได", "นั่งร้านเคลื่อนที่", "นั่งร้านแขวน",
        "แบบหล่อ", "ค้ำยัน", "รถขุด", "แพลตฟอร์มทำงานที่ความสูง", "รถบรรทุก",
        "เครนเคลื่อนที่", "เครนหอคอย", "เครื่องตอกเสาเข็ม", "เครื่องถอนเสาเข็ม", "ลิฟต์ก่อสร้าง",
        "อุปกรณ์เชื่อม", "เชื่อม", "เครน"
    ],
    "fr": [
        "saison des pluies", "liste de contrôle de sécurité", "chantier de construction", "inspection de sécurité",
        "alerte météo", "évacuation d'urgence", "vulnérable aux catastrophes", "récupération d'urgence", "fournitures d'urgence",
        "drainage", "installations de drainage", "structure souterraine", "inondation", "fortes pluies",
        "mur de soutènement", "mur de pierre", "effondrement", "enterrement", "imperméable", "soutènement", "étayage",
        "structure temporaire", "fixation", "typhon", "vent fort", "fenêtre en verre",
        "parties sous tension", "panneau de distribution", "disjoncteur", "mise à la terre", "isolation",
        "excavation", "pente", "effondrement", "état du sol", "objets enterrés", "méthode d'excavation",
        "étayage de soutènement", "construction en acier", "travaux électriques", "espace confiné",
        "bord", "ouverture", "échafaudage", "plateforme de travail", "échelle", "échafaudage mobile", "échafaudage suspendu",
        "coffrage", "étais", "excavatrice", "plateforme de travail en hauteur", "camion",
        "grue mobile", "grue à tour", "battage de pieux", "extracteur de pieux", "ascenseur de construction",
        "équipement de soudage", "soudage", "grue"
    ],
    "de": [
        "regenzeit", "sicherheitscheckliste", "baustelle", "sicherheitsinspektion",
        "wetterwarnung", "notevakuierung", "katastrophenanfällig", "notfallwiederherstellung", "notvorräte",
        "entwässerung", "entwässerungsanlagen", "unterirdische struktur", "überflutung", "starkregen",
        "stützmauer", "steinmauer", "einsturz", "verschüttung", "wasserdicht", "erdstützung", "abstützung",
        "temporäre struktur", "befestigung", "taifun", "starker wind", "glasfenster",
        "stromführende teile", "verteilertafel", "schutzschalter", "erdung", "isolierung",
        "aushub", "böschung", "einsturz", "bodenverhältnisse", "vergrabene objekte", "aushubmethode",
        "erdstützung", "stahlbau", "elektroarbeiten", "geschlossener raum",
        "kante", "öffnung", "gerüst", "arbeitsplattform", "leiter", "mobiles gerüst", "hängegerüst",
        "schalung", "abstützung", "bagger", "arbeitsbühne", "lkw",
        "mobilkran", "turmkran", "pfahlramme", "pfahlzieher", "bauaufzug",
        "schweißausrüstung", "schweißen", "kran"
    ],
    "tl": [
        "tag-ulan", "checklist ng kaligtasan", "construction site", "safety inspection",
        "weather warning", "emergency evacuation", "disaster vulnerable", "emergency recovery", "emergency supplies",
        "drainage", "drainage facilities", "underground structure", "flooding", "heavy rain",
        "retaining wall", "stone wall", "collapse", "burial", "waterproof", "earth retaining", "shoring",
        "temporary structure", "fastening", "typhoon", "malakas na hangin", "glass window",
        "live parts", "distribution panel", "circuit breaker", "grounding", "insulation",
        "excavation", "slope", "collapse", "ground condition", "buried objects", "excavation method",
        "earth retaining shoring", "steel construction", "electrical work", "confined space",
        "edge", "opening", "scaffold", "work platform", "hagdan", "mobile scaffold", "suspended scaffold",
        "formwork", "shores", "excavator", "aerial work platform", "truck",
        "mobile crane", "tower crane", "pile driver", "pile extractor", "construction lift",
        "welding equipment", "welding", "crane"
    ]
}

# 장마철 안전점검표 메뉴 텍스트 (외국어별)
JANGMACHUL_MENU_TEXT = {
    "ko": """**장마철 건설 현장 자율안전 점검표**

**장마철 공통점검사항**
**붕괴 굴착사면 사고예방 자율점검표** 
**흙막이지보공 사고예방 자율점검표**
**철골공사 사고예방 자율점검표**
**전기공사·작업 사고예방 자율점검표**
**밀폐공간 사고예방 자율점검표**
**단부·개구부 추락 사고예방 자율점검표**
**비계·작업발판 사고예방 자율점검표**
**사다리·이동식비계 사고예방 자율점검표**
**달비계 사고예방 자율점검표**
**거푸집·동바리 사고예방 자율점검표**
**굴착기 사고예방 자율점검표**
**고소작업대 사고예방 자율점검표**
**트럭 사고예방 자율점검표**
**이동식크레인 사고예방 자율점검표**
**타워크레인 사고예방 자율점검표**
**항타·항발기 사고예방 자율점검표**
**건설용리프트 사고예방 자율점검표**
**용접장치 사고예방 자율점검표**

위 항목 중 궁금한 내용의 키워드를 입력하시면 상세한 안전점검표를 확인할 수 있습니다.""",
    
    "en": """**Rainy Season Construction Site Safety Checklist**

**Rainy Season Common Inspection Items**
**Collapse Excavation Slope Accident Prevention Checklist**
**Earth Retaining Shoring Accident Prevention Checklist**
**Steel Construction Accident Prevention Checklist**
**Electrical Work Accident Prevention Checklist**
**Confined Space Accident Prevention Checklist**
**Edge/Opening Fall Accident Prevention Checklist**
**Scaffold/Work Platform Accident Prevention Checklist**
**Ladder/Mobile Scaffold Accident Prevention Checklist**
**Suspended Scaffold Accident Prevention Checklist**
**Formwork/Shores Accident Prevention Checklist**
**Excavator Accident Prevention Checklist**
**Aerial Work Platform Accident Prevention Checklist**
**Truck Accident Prevention Checklist**
**Mobile Crane Accident Prevention Checklist**
**Tower Crane Accident Prevention Checklist**
**Pile Driver/Extractor Accident Prevention Checklist**
**Construction Lift Accident Prevention Checklist**
**Welding Equipment Accident Prevention Checklist**

Enter keywords from the above items to view detailed safety checklists.""",

    "vi": """**Danh Sách Kiểm Tra An Toàn Công Trường Mùa Mưa**

**Các Mục Kiểm Tra Chung Mùa Mưa**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Sụp Đổ Dốc Đào**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Chống Đỡ Chắn Đất**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Xây Dựng Thép**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Công Việc Điện**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Không Gian Kín**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Rơi Từ Rìa/Lỗ Hở**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Giàn Giáo/Sàn Làm Việc**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Thang/Giàn Giáo Di Động**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Giàn Giáo Treo**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Ván Khuôn/Chống**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Máy Đào**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Sàn Làm Việc Trên Cao**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Xe Tải**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Cần Cẩu Di Động**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Cần Cẩu Tháp**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Máy Đóng/Rút Cọc**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Thang Máy Công Trình**
**Danh Sách Kiểm Tra Phòng Chống Tai Nạn Thiết Bị Hàn**

Nhập từ khóa từ các mục trên để xem danh sách kiểm tra an toàn chi tiết.""",

    "ja": """**梅雨期建設現場安全点検表**

**梅雨期共通点検事項**
**崩壊掘削法面事故防止自律点検表**
**土留め支保工事故防止自律点検表**
**鉄骨工事事故防止自律点検表**
**電気工事作業事故防止自律点検表**
**密閉空間事故防止自律点検表**
**端部・開口部墜落事故防止自律点検表**
**足場・作業床事故防止自律点検表**
**梯子・移動式足場事故防止自律点検表**
**吊り足場事故防止自律点検表**
**型枠・支保事故防止自律点検表**
**掘削機事故防止自律点検表**
**高所作業台事故防止自律点検表**
**トラック事故防止自律点検表**
**移動式クレーン事故防止自律点検表**
**タワークレーン事故防止自律点検表**
**杭打ち・杭抜き機事故防止自律点検表**
**建設用リフト事故防止自律点検表**
**溶接装置事故防止自律点検表**

上記項目の中で気になる内容のキーワードを入力すると、詳細な安全点検表を確認できます。""",

    "zh": """**雨季建筑工地安全检查表**

**雨季共同检查事项**
**坍塌挖掘坡面事故预防自律检查表**
**挡土支撑事故预防自律检查表**
**钢结构工程事故预防自律检查表**
**电气工程作业事故预防自律检查表**
**密闭空间事故预防自律检查表**
**边缘·开口坠落事故预防自律检查表**
**脚手架·工作平台事故预防自律检查表**
**梯子·移动脚手架事故预防自律检查表**
**悬挂脚手架事故预防自律检查表**
**模板·支撑事故预防自律检查表**
**挖掘机事故预防自律检查表**
**高空作业平台事故预防自律检查表**
**卡车事故预防自律检查表**
**移动式起重机事故预防自律检查表**
**塔式起重机事故预防自律检查表**
**打桩·拔桩机事故预防自律检查表**
**建筑升降机事故预防自律检查表**
**焊接设备事故预防自律检查表**

输入上述项目中您想了解的内容关键词，即可查看详细安全检查表。""",

    "zh-TW": """**雨季建築工地安全檢查表**

**雨季共同檢查事項**
**坍塌挖掘坡面事故預防自律檢查表**
**擋土支撐事故預防自律檢查表**
**鋼結構工程事故預防自律檢查表**
**電氣工程作業事故預防自律檢查表**
**密閉空間事故預防自律檢查表**
**邊緣·開口墜落事故預防自律檢查表**
**鷹架·工作平台事故預防自律檢查表**
**梯子·移動式鷹架事故預防自律檢查表**
**懸掛鷹架事故預防自律檢查表**
**模板·支撐事故預防自律檢查表**
**挖掘機事故預防自律檢查表**
**高空作業平台事故預防自律檢查表**
**卡車事故預防自律檢查表**
**移動式起重機事故預防自律檢查表**
**塔式起重機事故預防自律檢查表**
**打樁·拔樁機事故預防自律檢查表**
**建築升降機事故預防自律檢查表**
**焊接設備事故預防自律檢查表**

輸入上述項目中您想瞭解的內容關鍵詞，即可查看詳細安全檢查表。""",

    "id": """**Daftar Periksa Keselamatan Lokasi Konstruksi Musim Hujan**

**Item Pemeriksaan Umum Musim Hujan**
**Daftar Periksa Pencegahan Kecelakaan Runtuh Lereng Penggalian**
**Daftar Periksa Pencegahan Kecelakaan Penyangga Penahan Tanah**
**Daftar Periksa Pencegahan Kecelakaan Konstruksi Baja**
**Daftar Periksa Pencegahan Kecelakaan Pekerjaan Listrik**
**Daftar Periksa Pencegahan Kecelakaan Ruang Terbatas**
**Daftar Periksa Pencegahan Kecelakaan Jatuh Tepi·Bukaan**
**Daftar Periksa Pencegahan Kecelakaan Perancah·Platform Kerja**
**Daftar Periksa Pencegahan Kecelakaan Tangga·Perancah Bergerak**
**Daftar Periksa Pencegahan Kecelakaan Perancah Gantung**
**Daftar Periksa Pencegahan Kecelakaan Bekisting·Penyangga**
**Daftar Periksa Pencegahan Kecelakaan Ekskavator**
**Daftar Periksa Pencegahan Kecelakaan Platform Kerja Tinggi**
**Daftar Periksa Pencegahan Kecelakaan Truk**
**Daftar Periksa Pencegahan Kecelakaan Derek Bergerak**
**Daftar Periksa Pencegahan Kecelakaan Derek Menara**
**Daftar Periksa Pencegahan Kecelakaan Pemancang·Pencabut Tiang**
**Daftar Periksa Pencegahan Kecelakaan Lift Konstruksi**
**Daftar Periksa Pencegahan Kecelakaan Peralatan Las**

Masukkan kata kunci dari item di atas untuk melihat daftar periksa keselamatan terperinci.""",

    "th": """**รายการตรวจสอบความปลอดภัยไซต์ก่อสร้างฤดูฝน**

**รายการตรวจสอบทั่วไปฤดูฝน**
**รายการตรวจสอบป้องกันอุบัติเหตุพังทลายความชันขุดเจาะ**
**รายการตรวจสอบป้องกันอุบัติเหตุค้ำยันกั้นดิน**
**รายการตรวจสอบป้องกันอุบัติเหตุการก่อสร้างเหล็ก**
**รายการตรวจสอบป้องกันอุบัติเหตุงานไฟฟ้า**
**รายการตรวจสอบป้องกันอุบัติเหตุพื้นที่ปิด**
**รายการตรวจสอบป้องกันอุบัติเหตุตกจากขอบ·ช่องเปิด**
**รายการตรวจสอบป้องกันอุบัติเหตุนั่งร้าน·แพลตฟอร์มทำงาน**
**รายการตรวจสอบป้องกันอุบัติเหตุบันได·นั่งร้านเคลื่อนที่**
**รายการตรวจสอบป้องกันอุบัติเหตุนั่งร้านแขวน**
**รายการตรวจสอบป้องกันอุบัติเหตุแบบหล่อ·ค้ำยัน**
**รายการตรวจสอบป้องกันอุบัติเหตุรถขุด**
**รายการตรวจสอบป้องกันอุบัติเหตุแพลตฟอร์มทำงานที่ความสูง**
**รายการตรวจสอบป้องกันอุบัติเหตุรถบรรทุก**
**รายการตรวจสอบป้องกันอุบัติเหตุเครนเคลื่อนที่**
**รายการตรวจสอบป้องกันอุบัติเหตุเครนหอคอย**
**รายการตรวจสอบป้องกันอุบัติเหตุเครื่องตอก·ถอนเสาเข็ม**
**รายการตรวจสอบป้องกันอุบัติเหตุลิฟต์ก่อสร้าง**
**รายการตรวจสอบป้องกันอุบัติเหตุอุปกรณ์เชื่อม**

กรอกคีย์เวิร์ดจากรายการข้างต้นเพื่อดูรายการตรวจสอบความปลอดภัยโดยละเอียด""",

    "fr": """**Liste de Contrôle de Sécurité du Chantier de Construction en Saison des Pluies**

**Éléments de Contrôle Communs de la Saison des Pluies**
**Liste de Contrôle de Prévention des Accidents d'Effondrement de Pente d'Excavation**
**Liste de Contrôle de Prévention des Accidents d'Étayage de Soutènement**
**Liste de Contrôle de Prévention des Accidents de Construction en Acier**
**Liste de Contrôle de Prévention des Accidents de Travaux Électriques**
**Liste de Contrôle de Prévention des Accidents d'Espace Confiné**
**Liste de Contrôle de Prévention des Accidents de Chute de Bord·Ouverture**
**Liste de Contrôle de Prévention des Accidents d'Échafaudage·Plateforme de Travail**
**Liste de Contrôle de Prévention des Accidents d'Échelle·Échafaudage Mobile**
**Liste de Contrôle de Prévention des Accidents d'Échafaudage Suspendu**
**Liste de Contrôle de Prévention des Accidents de Coffrage·Étais**
**Liste de Contrôle de Prévention des Accidents d'Excavatrice**
**Liste de Contrôle de Prévention des Accidents de Plateforme de Travail en Hauteur**
**Liste de Contrôle de Prévention des Accidents de Camion**
**Liste de Contrôle de Prévention des Accidents de Grue Mobile**
**Liste de Contrôle de Prévention des Accidents de Grue à Tour**
**Liste de Contrôle de Prévention des Accidents de Battage·Extracteur de Pieux**
**Liste de Contrôle de Prévention des Accidents d'Ascenseur de Construction**
**Liste de Contrôle de Prévention des Accidents d'Équipement de Soudage**

Entrez les mots-clés des éléments ci-dessus pour voir les listes de contrôle de sécurité détaillées.""",

    "de": """**Sicherheitscheckliste für Baustellen in der Regenzeit**

**Gemeinsame Prüfpunkte der Regenzeit**
**Checkliste zur Unfallverhütung bei Einsturz von Aushubböschungen**
**Checkliste zur Unfallverhütung bei Erdstützungsabstützung**
**Checkliste zur Unfallverhütung im Stahlbau**
**Checkliste zur Unfallverhütung bei Elektroarbeiten**
**Checkliste zur Unfallverhütung in geschlossenen Räumen**
**Checkliste zur Unfallverhütung bei Sturz von Kante·Öffnung**
**Checkliste zur Unfallverhütung bei Gerüst·Arbeitsplattform**
**Checkliste zur Unfallverhütung bei Leiter·Mobilem Gerüst**
**Checkliste zur Unfallverhütung bei Hängegerüst**
**Checkliste zur Unfallverhütung bei Schalung·Abstützung**
**Checkliste zur Unfallverhütung bei Bagger**
**Checkliste zur Unfallverhütung bei Arbeitsbühne**
**Checkliste zur Unfallverhütung bei LKW**
**Checkliste zur Unfallverhütung bei Mobilkran**
**Checkliste zur Unfallverhütung bei Turmkran**
**Checkliste zur Unfallverhütung bei Pfahlramme·Pfahlzieher**
**Checkliste zur Unfallverhütung bei Bauaufzug**
**Checkliste zur Unfallverhütung bei Schweißausrüstung**

Geben Sie Schlüsselwörter aus den oben genannten Punkten ein, um detaillierte Sicherheitschecklisten anzuzeigen.""",

    "tl": """**Checklist ng Kaligtasan sa Construction Site sa Panahon ng Tag-ulan**

**Mga Common na Inspection Items sa Tag-ulan**
**Checklist para sa Pagpigil ng Aksidente sa Pagguho ng Excavation Slope**
**Checklist para sa Pagpigil ng Aksidente sa Earth Retaining Shoring**
**Checklist para sa Pagpigil ng Aksidente sa Steel Construction**
**Checklist para sa Pagpigil ng Aksidente sa Electrical Work**
**Checklist para sa Pagpigil ng Aksidente sa Confined Space**
**Checklist para sa Pagpigil ng Aksidente sa Pagkahulog mula sa Edge/Opening**
**Checklist para sa Pagpigil ng Aksidente sa Scaffold/Work Platform**
**Checklist para sa Pagpigil ng Aksidente sa Ladder/Mobile Scaffold**
**Checklist para sa Pagpigil ng Aksidente sa Suspended Scaffold**
**Checklist para sa Pagpigil ng Aksidente sa Formwork/Shores**
**Checklist para sa Pagpigil ng Aksidente sa Excavator**
**Checklist para sa Pagpigil ng Aksidente sa Aerial Work Platform**
**Checklist para sa Pagpigil ng Aksidente sa Truck**
**Checklist para sa Pagpigil ng Aksidente sa Mobile Crane**
**Checklist para sa Pagpigil ng Aksidente sa Tower Crane**
**Checklist para sa Pagpigil ng Aksidente sa Pile Driver/Extractor**
**Checklist para sa Pagpigil ng Aksidente sa Construction Lift**
**Checklist para sa Pagpigil ng Aksidente sa Welding Equipment**

Mag-type ng mga keyword mula sa mga item sa itaas para makita ang detalyadong safety checklist."""
}

# 장마철 건설 현장 자율안전 점검표 관련 함수들
def generate_jangmachul_answer_with_gemini(query, target_lang, gemini_api_key):
    """Gemini를 사용해서 장마철 안전 관련 질문에 답변"""
    try:
        genai.configure(api_key=gemini_api_key)
        
        prompts = {
            "ko": f"""다음은 장마철 건설 현장 안전 관리에 관한 질문입니다. 
            건설 현장에서의 장마철 안전 관리 전문가로서 실용적이고 구체적인 답변을 제공해주세요.

질문: {query}

질문이 특정 작업이나 장비에 관한 것이라면 해당 분야의 "자율안전 점검표" 형태로 답변해주세요.

답변은 다음 형식으로 작성해주세요:
1. **정의**: 해당 작업/장비가 무엇인지
2. **주요 위험 요소**: 해당 작업에서 발생할 수 있는 위험
3. **핵심 안전수칙**: 반드시 지켜야 할 기본 수칙
4. **자율점검표**: 
   - 사전조사/계획 단계
   - 작업 중 점검사항
   - 사후 관리

실제 건설 현장에서 바로 활용할 수 있는 실무적인 내용으로 작성해주세요.""",
            
            "en": f"""This is a question about rainy season safety management at construction sites.
Please provide practical and specific answers as an expert in rainy season safety management at construction sites.

Question: {query}

If the question is about specific work or equipment, please answer in the form of a "Self-Safety Checklist" for that field.

Please format your answer as follows:
1. **Definition**: What the work/equipment is
2. **Main Risk Factors**: Risks that may occur in the work
3. **Core Safety Rules**: Basic rules that must be followed
4. **Self-Checklist**:
   - Pre-survey/Planning stage
   - Inspection items during work
   - Post-management

Please write practical content that can be used directly at actual construction sites.""",

            "vi": f"""Đây là câu hỏi về quản lý an toàn mùa mưa tại các công trường xây dựng.
Hãy cung cấp câu trả lời thực tế và cụ thể với tư cách là chuyên gia quản lý an toàn mùa mưa tại công trường xây dựng.

Câu hỏi: {query}

Nếu câu hỏi về công việc hoặc thiết bị cụ thể, hãy trả lời dưới dạng "Danh sách kiểm tra an toàn tự kiểm" cho lĩnh vực đó.

Hãy định dạng câu trả lời như sau:
1. **Định nghĩa**: Công việc/thiết bị là gì
2. **Các yếu tố rủi ro chính**: Rủi ro có thể xảy ra trong công việc
3. **Quy tắc an toàn cốt lõi**: Quy tắc cơ bản phải tuân theo
4. **Danh sách kiểm tra tự kiểm**:
   - Giai đoạn khảo sát/lập kế hoạch trước
   - Các mục kiểm tra trong quá trình làm việc
   - Quản lý sau

Hãy viết nội dung thực tế có thể sử dụng trực tiếp tại công trường xây dựng thực tế.""",

            "ja": f"""これは建設現場での梅雨期安全管理に関する質問です。
建設現場での梅雨期安全管理専門家として実用的で具体的な回答を提供してください。

質問: {query}

質問が特定の作業や設備に関するものであれば、その分野の「自律安全点検表」の形で回答してください。

回答は以下の形式で作成してください：
1. **定義**: その作業/設備が何か
2. **主要リスク要因**: その作業で発生し得るリスク
3. **核心安全規則**: 必ず守るべき基本規則
4. **自律点検表**:
   - 事前調査/計画段階
   - 作業中の点検事項
   - 事後管理

実際の建設現場で直接活用できる実務的な内容で作成してください。""",

            "zh": f"""这是关于建筑工地雨季安全管理的问题。
作为建筑工地雨季安全管理专家，请提供实用和具体的答案。

问题: {query}

如果问题是关于特定工作或设备的，请以该领域的"自主安全检查表"形式回答。

请按以下格式回答：
1. **定义**: 该工作/设备是什么
2. **主要风险因素**: 该工作中可能发生的风险
3. **核心安全规则**: 必须遵守的基本规则
4. **自主检查表**:
   - 预调查/规划阶段
   - 工作中的检查项目
   - 事后管理

请写出可以在实际建筑工地直接使用的实用内容。""",

            "zh-TW": f"""這是關於建築工地雨季安全管理的問題。
作為建築工地雨季安全管理專家，請提供實用和具體的答案。

問題: {query}

如果問題是關於特定工作或設備的，請以該領域的「自主安全檢查表」形式回答。

請按以下格式回答：
1. **定義**: 該工作/設備是什麼
2. **主要風險因素**: 該工作中可能發生的風險
3. **核心安全規則**: 必須遵守的基本規則
4. **自主檢查表**:
   - 預調查/規劃階段
   - 工作中的檢查項目
   - 事後管理

請寫出可以在實際建築工地直接使用的實用內容。""",

            "id": f"""Ini adalah pertanyaan tentang manajemen keselamatan musim hujan di lokasi konstruksi.
Berikan jawaban praktis dan spesifik sebagai ahli manajemen keselamatan musim hujan di lokasi konstruksi.

Pertanyaan: {query}

Jika pertanyaan tentang pekerjaan atau peralatan spesifik, jawablah dalam bentuk "Daftar Periksa Keselamatan Mandiri" untuk bidang tersebut.

Silakan format jawaban Anda sebagai berikut:
1. **Definisi**: Apa itu pekerjaan/peralatan
2. **Faktor Risiko Utama**: Risiko yang mungkin terjadi dalam pekerjaan
3. **Aturan Keselamatan Inti**: Aturan dasar yang harus diikuti
4. **Daftar Periksa Mandiri**:
   - Tahap survei/perencanaan awal
   - Item pemeriksaan selama bekerja
   - Manajemen pasca

Tulis konten praktis yang dapat digunakan langsung di lokasi konstruksi aktual.""",

            "th": f"""นี่คือคำถามเกี่ยวกับการจัดการความปลอดภัยในฤดูฝนที่ไซต์ก่อสร้าง
ให้คำตอบที่ปraktical และเฉพาะเจาะจงในฐานะผู้เชี่ยวชาญการจัดการความปลอดภัยฤดูฝนที่ไซต์ก่อสร้าง

คำถาม: {query}

หากคำถามเกี่ยวกับงานหรืออุปกรณ์เฉพาะ โปรดตอบในรูปแบบ "รายการตรวจสอบความปลอดภัยแบบอิสระ" สำหรับด้านนั้น

โปรดจัดรูปแบบคำตอบของคุณดังนี้:
1. **คำนิยาม**: งาน/อุปกรณ์คืออะไร
2. **ปัจจัยเสี่ยงหลัก**: ความเสี่ยงที่อาจเกิดขึ้นในงาน
3. **กฎความปลอดภัยหลัก**: กฎพื้นฐานที่ต้องปฏิบัติตาม
4. **รายการตรวจสอบอิสระ**:
   - ขั้นตอนการสำรวจ/วางแผนล่วงหน้า
   - รายการตรวจสอบระหว่างทำงาน
   - การจัดการหลัง

เขียนเนื้อหาที่ปฏิบัติได้จริงที่สามารถใช้ได้โดยตรงในไซต์ก่อสร้างจริง""",

            "fr": f"""Il s'agit d'une question sur la gestion de la sécurité de la saison des pluies sur les chantiers de construction.
Veuillez fournir des réponses pratiques et spécifiques en tant qu'expert en gestion de la sécurité de la saison des pluies sur les chantiers de construction.

Question: {query}

Si la question concerne un travail ou un équipement spécifique, veuillez répondre sous la forme d'une "Liste de contrôle de sécurité autonome" pour ce domaine.

Veuillez formater votre réponse comme suit:
1. **Définition**: Ce qu'est le travail/équipement
2. **Principaux facteurs de risque**: Risques qui peuvent survenir dans le travail
3. **Règles de sécurité de base**: Règles de base qui doivent être suivies
4. **Liste de contrôle autonome**:
   - Étape de pré-enquête/planification
   - Éléments d'inspection pendant le travail
   - Gestion post

Rédigez un contenu pratique qui peut être utilisé directement sur les chantiers de construction réels.""",

            "de": f"""Dies ist eine Frage zum Regenzeitensicherheitsmanagement auf Baustellen.
Bitte geben Sie praktische und spezifische Antworten als Experte für Regenzeitensicherheitsmanagement auf Baustellen.

Frage: {query}

Wenn die Frage sich auf spezielle Arbeiten oder Ausrüstung bezieht, antworten Sie bitte in Form einer "Selbstsicherheitscheckliste" für diesen Bereich.

Bitte formatieren Sie Ihre Antwort wie folgt:
1. **Definition**: Was die Arbeit/Ausrüstung ist
2. **Hauptrisikofaktoren**: Risiken, die bei der Arbeit auftreten können
3. **Kernsicherheitsregeln**: Grundregeln, die befolgt werden müssen
4. **Selbstcheckliste**:
   - Voruntersuchungs-/Planungsphase
   - Inspektionsartikel während der Arbeit
   - Nachbetreuung

Schreiben Sie praktische Inhalte, die direkt auf tatsächlichen Baustellen verwendet werden können.""",

            "tl": f"""Ito ay tanong tungkol sa pamamahala ng kaligtasan sa tag-ulan sa mga construction site.
Magbigay ng praktikal at tukoy na mga sagot bilang eksperto sa pamamahala ng kaligtasan sa tag-ulan sa mga construction site.

Tanong: {query}

Kung ang tanong ay tungkol sa tukoy na trabaho o kagamitan, sumagot sa anyo ng "Self-Safety Checklist" para sa larangan na iyon.

Paki-format ang inyong sagot tulad nito:
1. **Kahulugan**: Ano ang trabaho/kagamitan
2. **Mga Pangunahing Risk Factor**: Mga panganib na maaaring mangyari sa trabaho
3. **Mga Core Safety Rules**: Mga basic na tuntunin na dapat sundin
4. **Self-Checklist**:
   - Pre-survey/Planning stage
   - Mga inspection items habang nagtatrabaho
   - Post-management

Sumulat ng praktikal na nilalaman na magagamit direkta sa mga tunay na construction site."""
        }
        
        prompt = prompts.get(target_lang, prompts["ko"])
        
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt, generation_config={
            "max_output_tokens": 1500,
            "temperature": 0.3
        })
        
        # 언어별 헤더 텍스트
        headers = {
            "ko": "🌧️ **장마철 건설 현장 안전 관리 가이드**",
            "en": "🌧️ **Rainy Season Construction Site Safety Management Guide**",
            "vi": "🌧️ **Hướng Dẫn Quản Lý An Toàn Công Trường Mùa Mưa**",
            "ja": "🌧️ **梅雨期建設現場安全管理ガイド**",
            "zh": "🌧️ **雨季建筑工地安全管理指南**",
            "zh-TW": "🌧️ **雨季建築工地安全管理指南**",
            "id": "🌧️ **Panduan Manajemen Keselamatan Lokasi Konstruksi Musim Hujan**",
            "th": "🌧️ **คู่มือการจัดการความปลอดภัยไซต์ก่อสร้างฤดูฝน**",
            "fr": "🌧️ **Guide de Gestion de la Sécurité du Chantier de Construction en Saison des Pluies**",
            "de": "🌧️ **Leitfaden für Regenzeitensicherheitsmanagement auf Baustellen**",
            "tl": "🌧️ **Gabay sa Pamamahala ng Kaligtasan sa Construction Site sa Tag-ulan**"
        }
        
        header = headers.get(target_lang, headers["ko"])
        answer_content = f"{header}\n\n{response.text.strip()}"
        
        # YouTube 검색 버튼 정보 추가 (Gemini 답변용)
        answer_content += "\n\n" + get_youtube_search_button_info_for_gemini(query, target_lang)
        
        return answer_content
        
    except Exception as e:
        print(f"Gemini 답변 생성 오류: {e}")
        fallback_messages = {
            "ko": "죄송합니다. 장마철 안전 정보를 생성하는 중 오류가 발생했습니다.",
            "en": "Sorry, an error occurred while generating rainy season safety information.",
            "vi": "Xin lỗi, đã xảy ra lỗi khi tạo thông tin an toàn mùa mưa.",
            "ja": "申し訳ございません。梅雨期安全情報の生成中にエラーが発生しました。",
            "zh": "抱歉，生成雨季安全信息时发生错误。",
            "zh-TW": "抱歉，生成雨季安全資訊時發生錯誤。",
            "id": "Maaf, terjadi kesalahan saat menghasilkan informasi keselamatan musim hujan.",
            "th": "ขออภัย เกิดข้อผิดพลาดขณะสร้างข้อมูลความปลอดภัยฤดูฝน",
            "fr": "Désolé, une erreur s'est produite lors de la génération d'informations de sécurité de saison des pluies.",
            "de": "Entschuldigung, ein Fehler ist bei der Erstellung von Regenzeitensicherheitsinformationen aufgetreten.",
            "tl": "Sorry, may naganap na error habang ginagawa ang impormasyon ng kaligtasan sa tag-ulan."
        }
        return fallback_messages.get(target_lang, fallback_messages["ko"])

def generate_onyul_answer_with_gemini(query, target_lang, gemini_api_key):
    """Gemini를 사용해서 온열질환 예방조치 관련 질문에 답변"""
    try:
        genai.configure(api_key=gemini_api_key)
        
        prompts = {
            "ko": f"""다음은 건설 현장에서의 폭염 및 온열질환 예방조치에 관한 질문입니다. 
            산업안전보건 및 온열질환 예방 전문가로서 실용적이고 구체적인 답변을 제공해주세요.

질문: {query}

질문이 일반적인 온열질환 예방조치에 관한 것이라면 다음 항목들을 포함하여 종합적으로 답변하고,
구체적인 세부 질문(5대 기본 수칙, 응급처치, 작업시간 조정 등)이라면 해당 내용에 집중해서 답변해주세요.

답변에 포함할 내용:
1. **온열질환의 종류와 증상** (열사병, 열탈진, 열경련, 열실신 등)
2. **5대 기본 수칙** (한국 고용노동부 가이드라인 기준)
3. **작업환경 개선 방법** (그늘막, 냉방시설, 통풍 등)
4. **작업시간 조정** (무더위시간 작업 중단, 휴식시간 확보)
5. **수분 섭취 방법** (물, 이온음료 등)
6. **개인보호구 착용법** (통기성 좋은 작업복, 모자 등)
7. **응급처치 방법** (체온 낮추기, 의식 확인, 119 신고 등)
8. **관리자 주의사항** (근로자 건강상태 확인, 작업 중단 판단 등)

답변은 한국어로, 건설 현장에서 바로 적용할 수 있는 실무적인 내용으로 작성해주세요.""",
            
            "en": f"""This is a question about heat wave and heat illness prevention measures at construction sites.
Please provide practical and specific answers as an expert in industrial safety and heat illness prevention.

Question: {query}

If the question is about general heat illness prevention measures, please answer comprehensively including the following items.
If it's a specific detailed question (5 basic rules, first aid, work time adjustment, etc.), please focus on that content.

Content to include in the answer:
1. **Types and symptoms of heat illness** (heat stroke, heat exhaustion, heat cramps, heat syncope, etc.)
2. **5 basic rules** (based on Korean Ministry of Employment and Labor guidelines)
3. **Work environment improvement methods** (shade, cooling facilities, ventilation, etc.)
4. **Work time adjustment** (work suspension during hot weather, securing rest time)
5. **Water intake methods** (water, ion drinks, etc.)
6. **Personal protective equipment wearing** (breathable work clothes, hats, etc.)
7. **First aid methods** (lowering body temperature, checking consciousness, calling 119, etc.)
8. **Manager precautions** (checking worker health status, deciding work suspension, etc.)

Please write practical content that can be applied directly at construction sites."""
        }
        
        prompt = prompts.get(target_lang, prompts["ko"])
        
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt, generation_config={
            "max_output_tokens": 1500,
            "temperature": 0.3
        })
        
        return f"🌡️ **온열질환 예방조치 가이드**\n\n{response.text.strip()}"
        
    except Exception as e:
        print(f"Gemini 온열질환 답변 생성 오류: {e}")
        fallback_messages = {
            "ko": "죄송합니다. 온열질환 예방조치 정보를 생성하는 중 오류가 발생했습니다.",
            "en": "Sorry, an error occurred while generating heat illness prevention information.",
        }
        return fallback_messages.get(target_lang, fallback_messages["ko"])

def generate_gemini_fallback_answer(query, target_lang, gemini_api_key):
    """외국인근로자.pkl에서 답변을 찾을 수 없을 때 Gemini API로 일반 답변 생성"""
    try:
        genai.configure(api_key=gemini_api_key)
        
        prompts = {
            "ko": f"""다음은 외국인 근로자와 관련된 질문입니다. 
            외국인 근로자의 권리, 근로 조건, 생활 정보 등에 대해 도움이 되는 답변을 제공해주세요.

질문: {query}

답변은 한국어로, 외국인 근로자가 한국에서 생활하고 일하는 데 실질적으로 도움이 되는 정보를 포함해주세요.""",
            
            "en": f"""This is a question related to foreign workers.
Please provide helpful answers about foreign workers' rights, working conditions, living information, etc.

Question: {query}

Please answer in English with information that is practically helpful for foreign workers living and working in Korea.""",
            
            "vi": f"""Đây là câu hỏi liên quan đến lao động nước ngoài.
Vui lòng cung cấp câu trả lời hữu ích về quyền lợi, điều kiện làm việc, thông tin sinh hoạt của lao động nước ngoài, v.v.

Câu hỏi: {query}

Vui lòng trả lời bằng tiếng Việt với thông tin thực tế hữu ích cho lao động nước ngoài sống và làm việc tại Hàn Quốc.""",
            
            "zh": f"""这是与外国劳工相关的问题。
请就外国劳工的权利、工作条件、生活信息等提供有用的答案。

问题: {query}

请用中文回答，提供对在韩国生活和工作的外国劳工实际有用的信息。""",
            
            "ja": f"""これは外国人労働者に関する質問です。
外国人労働者の権利、労働条件、生活情報などについて役立つ回答を提供してください。

質問: {query}

日本語で回答し、韓国で生活し働く外国人労働者に実際に役立つ情報を含めてください。"""
        }
        
        prompt = prompts.get(target_lang, prompts["ko"])
        
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt, generation_config={
            "max_output_tokens": 1000,
            "temperature": 0.3
        })
        
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini 폴백 답변 생성 오류: {e}")
        fallback_messages = {
            "ko": "죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.",
            "en": "Sorry, an error occurred while generating an answer.",
            "vi": "Xin lỗi, đã xảy ra lỗi khi tạo câu trả lời.",
            "zh": "抱歉，生成答案时发生错误。",
            "ja": "申し訳ございません。回答の生成中にエラーが発生しました。"
        }
        return fallback_messages.get(target_lang, fallback_messages["ko"])

def search_jangmachul_json(query, jangmachul_json_data):
    """JSON 데이터에서 키워드와 매칭되는 정보 검색"""
    query_lower = query.lower()
    results = []
    
    try:
        safety_data = jangmachul_json_data.get("자율안전보건_점검표", {})
        
        # 직접 키워드로 섹션 검색 (더 간단하고 확실한 방법)
        matched_sections = []
        print(f"[DEBUG] 검색 중인 키워드: {query_lower}")
        
        all_sections = list(safety_data.keys())
        print(f"[DEBUG] 사용 가능한 섹션 개수: {len(all_sections)}")
        
        # "자율점검표"만 입력된 경우 전체 메뉴 표시
        if query_lower.strip() in ["자율점검표", "점검표", "안전점검표"]:
            print(f"[DEBUG] '{query_lower}' - 전체 메뉴 표시")
            # 빈 리스트 반환하여 handle_jangmachul_query에서 메뉴를 표시하도록 함
            return []
        
        # 키워드별 섹션 매핑
        for section_name in all_sections:
            section_lower = section_name.lower()
            
            # 키워드가 섹션 이름에 포함되는지 확인
            if ("붕괴" in query_lower or "굴착사면" in query_lower) and "굴착사면" in section_lower:
                print(f"[DEBUG] '붕괴/굴착사면' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("흙막이지보공" in query_lower or "흙막이" in query_lower or "지보공" in query_lower) and "흙막이지보공" in section_lower:
                print(f"[DEBUG] '흙막이지보공' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("철골공사" in query_lower or "철골" in query_lower) and "철골공사" in section_lower:
                print(f"[DEBUG] '철골공사' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("전기공사" in query_lower or "전기" in query_lower) and "전기공사" in section_lower:
                print(f"[DEBUG] '전기공사' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif "밀폐공간" in query_lower and "밀폐공간" in section_lower:
                print(f"[DEBUG] '밀폐공간' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("단부" in query_lower or "개구부" in query_lower) and ("단부" in section_lower or "개구부" in section_lower):
                print(f"[DEBUG] '단부/개구부' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("지붕공사" in query_lower or "지붕" in query_lower) and "지붕공사" in section_lower:
                print(f"[DEBUG] '지붕공사' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("비계" in query_lower or "작업발판" in query_lower) and ("비계" in section_lower or "작업발판" in section_lower):
                print(f"[DEBUG] '비계/작업발판' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif "사다리" in query_lower and "사다리" in section_lower:
                print(f"[DEBUG] '사다리' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif "이동식비계" in query_lower and "이동식비계" in section_lower:
                print(f"[DEBUG] '이동식비계' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif "달비계" in query_lower and "달비계" in section_lower:
                print(f"[DEBUG] '달비계' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("거푸집" in query_lower or "동바리" in query_lower) and ("거푸집" in section_lower or "동바리" in section_lower):
                print(f"[DEBUG] '거푸집/동바리' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif "굴착기" in query_lower and "굴착기" in section_lower:
                print(f"[DEBUG] '굴착기' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("고소작업대" in query_lower or "고속작업대" in query_lower) and "고소작업대" in section_lower:
                print(f"[DEBUG] '고소작업대' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif "트럭" in query_lower and "트럭" in section_lower:
                print(f"[DEBUG] '트럭' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("이동식크레인" in query_lower or "크레인" in query_lower) and "이동식크레인" in section_lower:
                print(f"[DEBUG] '이동식크레인' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif ("타워크레인" in query_lower or "크레인" in query_lower) and "타워크레인" in section_lower:
                print(f"[DEBUG] '타워크레인' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            elif "용접" in query_lower and "용접" in section_lower:
                print(f"[DEBUG] '용접' 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
            # 장마철 공통사항 매칭
            elif any(keyword in query_lower for keyword in ["장마철", "공통", "호우", "침수", "태풍", "강풍", "감전", "붕괴", "매몰"]) and "장마철" in section_lower:
                print(f"[DEBUG] 장마철 관련 키워드로 섹션 '{section_name}' 매칭됨")
                matched_sections.append(section_name)
        
        # 중복 제거
        matched_sections = list(set(matched_sections))
        print(f"[DEBUG] 최종 매칭된 섹션들: {matched_sections}")
        
        # 매칭된 섹션들의 정보 수집
        for section in matched_sections:
            section_data = safety_data[section]
            results.append({
                "section": section,
                "data": section_data
            })
        
        return results
        
    except Exception as e:
        print(f"JSON 검색 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def format_jangmachul_results(results, target_lang="ko", original_query=""):
    """검색 결과를 포맷팅하여 사용자에게 표시 (YouTube 링크 버튼 포함)"""
    if not results:
        return None
    
    formatted_text = "**장마철 건설 현장 자율안전 점검표**\n\n"
    
    for result in results:
        section = result["section"]
        data = result["data"]
        
        # 섹션 제목
        section_title = section.replace("_", " ").title()
        formatted_text += f"**{section_title}**\n\n"
        
        # 데이터 포맷팅
        if section == "장마철_공통사항":
            formatted_text += format_common_safety_items(data)
        else:
            # 모든 다른 섹션들에 대해 일반적인 포맷팅 사용
            formatted_text += format_general_safety_info(data)
        
        formatted_text += "\n\n"
    
    # YouTube 검색 버튼 정보 추가 (장마철 안전점검표에만 적용)
    formatted_text += "\n" + get_youtube_search_button_info(results, target_lang, original_query) + "\n"
    
    return formatted_text.strip()

def get_youtube_search_button_info(results, target_lang, original_query=""):
    """안전점검표 결과를 기반으로 YouTube 검색 버튼 정보 생성"""
    import urllib.parse
    
    # 검색 키워드 매핑 (한국어로)
    search_keywords = {
        "굴착사면_무너짐": "굴착 사면 붕괴",
        "장마철_공통사항": "장마철 안전",
        "비계_조립해체": "비계",
        "크레인_운전": "크레인",
        "용접_절단": "용접",
        "가설전기": "가설전기",
        "고소작업": "고소작업",
        "터널공사": "터널공사",
        "교량공사": "교량공사"
    }
    
    # 결과에서 키워드 추출
    detected_keyword = original_query or "장마철 안전"  # 기본값을 원래 질문으로 설정
    print(f"[DEBUG] JSON 검색 결과 개수: {len(results) if results else 0}")
    if results and len(results) > 0:
        for result in results:
            section = result.get("section", "")
            print(f"[DEBUG] 검색 결과 섹션: {section}")
            if section in search_keywords:
                detected_keyword = search_keywords[section]
                print(f"[DEBUG] 매핑된 검색어: {detected_keyword}")
                break
    
    # JSON에서 매핑 실패 시 외국어 질문을 한국어로 번역 시도
    if detected_keyword == original_query:
        print(f"[DEBUG] JSON에서 키워드 매핑 실패, 외국어 질문을 한국어로 번역 시도")
        # 간단한 번역 사전 (Gemini 함수와 동일)
        translation_dict = {
            "perancah gantung": "현수형 비계",
            "manajemen keselamatan": "안전 관리", 
            "suspended scaffold": "현수형 비계",
            "hanging platform": "현수형 비계",
            "construction safety": "건설 안전",
            "safety management": "안전 관리",
            "つり足場": "현수형 비계",
            "建設安全": "건설 안전",
            "悬挂脚手架": "현수형 비계",
            "建筑安全": "건설 안전",
            "giàn treo": "현수형 비계",
            "an toàn xây dựng": "건설 안전"
        }
        
        # 질문에서 번역 가능한 구문 찾기
        query_lower_for_translation = original_query.lower()
        for foreign_phrase, korean_translation in translation_dict.items():
            if foreign_phrase.lower() in query_lower_for_translation:
                detected_keyword = korean_translation
                print(f"[DEBUG] 질문 번역 성공: '{foreign_phrase}' -> '{korean_translation}'")
                break
        
        # 여전히 매핑되지 않은 경우 기본 검색어 사용
        if detected_keyword == original_query:
            if target_lang != "ko":
                detected_keyword = "건설현장 안전"
                print(f"[DEBUG] 외국어 질문 -> 기본 한국어 검색어 사용: {detected_keyword}")
            else:
                print(f"[DEBUG] 한국어 질문을 그대로 검색어로 사용: {detected_keyword}")
    else:
        print(f"[DEBUG] JSON에서 매핑된 검색어 사용: {detected_keyword}")
    
    # URL 인코딩
    encoded_keyword = urllib.parse.quote(detected_keyword)
    youtube_url = f"https://www.youtube.com/@koshamovie/search?query={encoded_keyword}"
    print(f"[DEBUG] Generated YouTube URL: {youtube_url}")  # 디버그
    
    # 언어별 버튼 텍스트
    button_texts = {
        "ko": "📺 KOSHA 관련 동영상 보기",
        "en": "📺 Watch Related KOSHA Videos",
        "vi": "📺 Xem Video KOSHA Liên Quan",
        "ja": "📺 KOSHA関連動画を見る",
        "zh": "📺 观看相关KOSHA视频",
        "zh-TW": "📺 觀看相關KOSHA影片",
        "id": "📺 Tonton Video KOSHA Terkait",
        "th": "📺 ดูวิดีโอ KOSHA ที่เกี่ยวข้อง",
        "fr": "📺 Voir Vidéos KOSHA Connexes",
        "de": "📺 KOSHA Videos ansehen",
        "tl": "📺 Manood ng KOSHA Videos"
    }
    
    button_text = button_texts.get(target_lang, button_texts["ko"])
    
    # 버튼 정보를 반환 (실제 버튼은 chat_room.py에서 생성)
    # 형식: YOUTUBE_BUTTON|URL|버튼텍스트|검색키워드 (| 구분자 사용)
    return f"YOUTUBE_BUTTON|{youtube_url}|{button_text}|{detected_keyword}"

def get_youtube_search_button_info_for_gemini(query, target_lang):
    """Gemini 답변용 YouTube 검색 버튼 정보 생성"""
    import urllib.parse
    
    # 질문에서 키워드 추출하여 검색어 결정
    query_lower = query.lower()
    detected_keyword = query  # 기본값을 사용자 질문으로 변경
    
    # 포괄적인 다국어 키워드 매핑 (한국어로 번역)
    keyword_mapping = {
        # 한국어 키워드
        "굴착": "굴착 사면 붕괴",
        "사면": "굴착 사면 붕괴", 
        "무너짐": "굴착 사면 붕괴",
        "붕괴": "굴착 사면 붕괴",
        "조립": "비계",
        "해체": "비계",
        "운전": "크레인",
        "절단": "용접",
        "전기": "가설전기",
        "고소": "고소작업",
        "낙하": "개구부",
        "추락": "개구부",
        "비계": "비계",
        "크레인": "크레인",
        "용접": "용접",
        "개구부": "개구부",
        "터널": "터널공사",
        "교량": "교량공사",
        
        # 영어 키워드
        "scaffold": "비계",
        "scaffolding": "비계",
        "crane": "크레인",
        "welding": "용접",
        "excavation": "굴착 사면 붕괴",
        "tunnel": "터널공사",
        "bridge": "교량공사",
        "opening": "개구부",
        "fall": "개구부",
        "suspended": "비계",
        "hanging": "비계",
        "platform": "비계",
        "construction": "건설현장 안전",
        "safety": "안전점검표",
        "inspection": "안전점검표",
        "rainy": "장마철 안전",
        "monsoon": "장마철 안전",
        
        # 인도네시아어 키워드
        "perancah": "비계",
        "gantung": "비계",
        "platform": "비계",
        "konstruksi": "건설현장 안전",
        "keselamatan": "안전점검표",
        "hujan": "장마철 안전",
        "musim": "장마철 안전",
        "derek": "크레인",
        "las": "용접",
        "terowongan": "터널공사",
        "jembatan": "교량공사",
        "galian": "굴착 사면 붕괴",
        "lereng": "굴착 사면 붕괴",
        "runtuh": "굴착 사면 붕괴",
        "jatuh": "개구부",
        "lubang": "개구부",
        
        # 일본어 키워드
        "足場": "비계",
        "クレーン": "크레인",
        "溶接": "용접",
        "掘削": "굴착 사면 붕괴",
        "法面": "굴착 사면 붕괴",
        "崩壊": "굴착 사면 붕괴",
        "開口部": "개구부",
        "墜落": "개구부",
        "トンネル": "터널공사",
        "橋梁": "교량공사",
        "安全": "안전점검표",
        "点検": "안전점검표",
        "梅雨": "장마철 안전",
        
        # 중국어 키워드
        "脚手架": "비계",
        "起重机": "크레인",
        "焊接": "용접",
        "挖掘": "굴착 사면 붕괴",
        "边坡": "굴착 사면 붕괴",
        "坍塌": "굴착 사면 붕괴",
        "开口": "개구부",
        "坠落": "개구부",
        "隧道": "터널공사",
        "桥梁": "교량공사",
        "安全": "안전점검표",
        "检查": "안전점검표",
        "雨季": "장마철 안전",
        
        # 대만 중국어 키워드
        "鷹架": "비계",
        "吊架": "비계",
        "起重機": "크레인",
        "焊接": "용접",
        "挖掘": "굴착 사면 붕괴",
        "邊坡": "굴착 사면 붕괴",
        "坍塌": "굴착 사면 붕괴",
        "開口": "개구부",
        "墜落": "개구부",
        "隧道": "터널공사",
        "橋樑": "교량공사",
        "安全": "안전점검표",
        "檢查": "안전점검표",
        "雨季": "장마철 안전",
        
        # 베트남어 키워드
        "giàn": "비계",
        "treo": "비계",
        "cần": "크레인",
        "hàn": "용접",
        "đào": "굴착 사면 붕괴",
        "taluy": "굴착 사면 붕괴",
        "sập": "굴착 사면 붕괴",
        "lỗ": "개구부",
        "rơi": "개구부",
        "hầm": "터널공사",
        "cầu": "교량공사",
        "an": "안전점검표",
        "toàn": "안전점검표",
        "kiểm": "안전점검표",
        "tra": "안전점검표",
        "mưa": "장마철 안전",
        "mùa": "장마철 안전",
        
        # 프랑스어 키워드
        "échafaudage": "비계",
        "suspendu": "비계",
        "grue": "크레인",
        "soudage": "용접",
        "excavation": "굴착 사면 붕괴",
        "pente": "굴착 사면 붕괴",
        "effondrement": "굴착 사면 붕괴",
        "ouverture": "개구부",
        "chute": "개구부",
        "tunnel": "터널공사",
        "pont": "교량공사",
        "sécurité": "안전점검표",
        "inspection": "안전점검표",
        "pluie": "장마철 안전",
        "mousson": "장마철 안전",
        
        # 독일어 키워드
        "gerüst": "비계",
        "hängend": "비계",
        "kran": "크레인",
        "schweißen": "용접",
        "aushub": "굴착 사면 붕괴",
        "böschung": "굴착 사면 붕괴",
        "einsturz": "굴착 사면 붕괴",
        "öffnung": "개구부",
        "sturz": "개구부",
        "tunnel": "터널공사",
        "brücke": "교량공사",
        "sicherheit": "안전점검표",
        "inspektion": "안전점검표",
        "regen": "장마철 안전",
        "monsun": "장마철 안전",
        
        # 태국어 키워드
        "นั่งร้าน": "비계",
        "แขวน": "비계",
        "เครน": "크레인",
        "เชื่อม": "용접",
        "ขุด": "굴착 사면 붕괴",
        "ลาด": "굴착 사면 붕괴",
        "ถล่ม": "굴착 사면 붕괴",
        "ช่อง": "개구부",
        "ตก": "개구부",
        "อุโมงค์": "터널공사",
        "สะพาน": "교량공사",
        "ความปลอดภัย": "안전점검표",
        "ตรวจสอบ": "안전점검표",
        "ฝน": "장마철 안전",
        "มรสุม": "장마철 안전",
        
        # 필리핀어 키워드
        "andamyo": "비계",
        "nakasabit": "비계",
        "crane": "크레인",
        "welding": "용접",
        "hukay": "굴착 사면 붕괴",
        "dalisdis": "굴착 사면 붕괴",
        "guho": "굴착 사면 붕괴",
        "butas": "개구부",
        "bagsak": "개구부",
        "tunnel": "터널공사",
        "tulay": "교량공사",
        "kaligtasan": "안전점검표",
        "inspeksyon": "안전점검표",
        "ulan": "장마철 안전",
        "tag-ulan": "장마철 안전"
    }
    
    # 질문에서 키워드 찾기 (특별한 매핑이 있는 경우만)
    print(f"[DEBUG] 사용자 질문: {query}")
    for keyword, search_term in keyword_mapping.items():
        if keyword in query_lower:
            detected_keyword = search_term
            print(f"[DEBUG] 감지된 키워드: '{keyword}' -> 검색어: '{search_term}'")
            break
    
    # 키워드 매핑이 없는 경우 질문을 한국어로 번역
    if detected_keyword == query:
        print(f"[DEBUG] 키워드 매핑 없음, 외국어 질문을 한국어로 번역 시도")
        # 간단한 언어별 번역 사전
        translation_dict = {
            # 인도네시아어 번역
            "perancah gantung": "현수형 비계",
            "manajemen keselamatan": "안전 관리",
            "lokasi konstruksi": "건설 현장",
            "musim hujan": "장마철",
            "faktor risiko": "위험 요소",
            "keseimbangan dan stabilitas": "균형과 안정성",
            "pekerja terjatuh": "작업자 추락",
            "platform kerja": "작업 플랫폼",
            "perlindungan jatuh": "추락 방지",
            "safety harness": "안전 하네스",
            "railing": "난간",
            "kondisi cuaca": "기상 조건",
            
            # 영어 번역
            "suspended scaffold": "현수형 비계",
            "hanging platform": "현수형 비계",
            "construction safety": "건설 안전",
            "safety management": "안전 관리",
            "fall protection": "추락 방지",
            "worker safety": "작업자 안전",
            "weather conditions": "기상 조건",
            "risk factors": "위험 요소",
            "balance and stability": "균형과 안정성",
            
            # 일본어 번역
            "つり足場": "현수형 비계",
            "建設安全": "건설 안전",
            "安全管理": "안전 관리",
            "墜落防止": "추락 방지",
            "作業者安全": "작업자 안전",
            "気象条件": "기상 조건",
            "危険要因": "위험 요소",
            
            # 중국어 번역
            "悬挂脚手架": "현수형 비계",
            "建筑安全": "건설 안전",
            "安全管理": "안전 관리",
            "坠落防护": "추락 방지",
            "工人安全": "작업자 안전",
            "天气条件": "기상 조건",
            "风险因素": "위험 요소",
            
            # 베트남어 번역
            "giàn treo": "현수형 비계",
            "an toàn xây dựng": "건설 안전",
            "quản lý an toàn": "안전 관리",
            "bảo vệ chống rơi": "추락 방지",
            "an toàn công nhân": "작업자 안전",
            "điều kiện thời tiết": "기상 조건",
            "yếu tố rủi ro": "위험 요소",
            
            # 태국어 번역
            "นั่งร้านแขวน": "현수형 비계",
            "ความปลอดภัยในการก่อสร้าง": "건설 안전",
            "การจัดการความปลอดภัย": "안전 관리",
            "การป้องกันการตก": "추락 방지",
            "ความปลอดภัยของผู้ปฏิบัติงาน": "작업자 안전",
            
            # 프랑스어 번역
            "échafaudage suspendu": "현수형 비계",
            "sécurité de construction": "건설 안전",
            "gestion de sécurité": "안전 관리",
            "protection contre chutes": "추락 방지",
            "sécurité des travailleurs": "작업자 안전",
            
            # 독일어 번역
            "hängendes gerüst": "현수형 비계",
            "bausicherheit": "건설 안전",
            "sicherheitsmanagement": "안전 관리",
            "absturzschutz": "추락 방지",
            "arbeitersicherheit": "작업자 안전",
            
            # 필리핀어 번역
            "nakasabit na andamyo": "현수형 비계",
            "kaligtasan sa konstruksyon": "건설 안전",
            "pamamahala ng kaligtasan": "안전 관리",
            "proteksyon sa pagkakahulog": "추락 방지",
            "kaligtasan ng manggagawa": "작업자 안전"
        }
        
        # 질문에서 번역 가능한 구문 찾기
        query_lower_for_translation = query.lower()
        for foreign_phrase, korean_translation in translation_dict.items():
            if foreign_phrase.lower() in query_lower_for_translation:
                detected_keyword = korean_translation
                print(f"[DEBUG] 질문 번역 성공: '{foreign_phrase}' -> '{korean_translation}'")
                break
        
        # 여전히 매핑되지 않은 경우 기본 검색어 사용
        if detected_keyword == query:
            # 외국어 질문인 경우 기본적으로 "장마철 안전"이나 "건설현장 안전"으로 변경
            if target_lang != "ko":
                detected_keyword = "건설현장 안전"
                print(f"[DEBUG] 외국어 질문 -> 기본 한국어 검색어 사용: {detected_keyword}")
            else:
                print(f"[DEBUG] 한국어 질문을 그대로 검색어로 사용: {detected_keyword}")
    else:
        print(f"[DEBUG] 키워드 매핑된 검색어 사용: {detected_keyword}")
    
    # URL 인코딩
    encoded_keyword = urllib.parse.quote(detected_keyword)
    youtube_url = f"https://www.youtube.com/@koshamovie/search?query={encoded_keyword}"
    print(f"[DEBUG] Generated YouTube URL: {youtube_url}")  # 디버그
    
    # 언어별 버튼 텍스트
    button_texts = {
        "ko": "📺 KOSHA 관련 동영상 보기",
        "en": "📺 Watch Related KOSHA Videos",
        "vi": "📺 Xem Video KOSHA Liên Quan",
        "ja": "📺 KOSHA関連動画を見る",
        "zh": "📺 观看相关KOSHA视频",
        "zh-TW": "📺 觀看相關KOSHA影片",
        "id": "📺 Tonton Video KOSHA Terkait",
        "th": "📺 ดูวิดีโอ KOSHA ที่เกี่ยวข้อง",
        "fr": "📺 Voir Vidéos KOSHA Connexes",
        "de": "📺 KOSHA Videos ansehen",
        "tl": "📺 Manood ng KOSHA Videos"
    }
    
    button_text = button_texts.get(target_lang, button_texts["ko"])
    
    # 버튼 정보를 반환 (실제 버튼은 chat_room.py에서 생성)
    # 형식: YOUTUBE_BUTTON|URL|버튼텍스트|검색키워드 (| 구분자 사용)
    return f"YOUTUBE_BUTTON|{youtube_url}|{button_text}|{detected_keyword}"

def format_common_safety_items(data):
    """장마철 공통사항 포맷팅"""
    result = ""
    
    if "점검_항목" in data:
        for category, items in data["점검_항목"].items():
            result += f"**{category.replace('_', ' ')}**\n"
            if isinstance(items, list):
                for item in items:
                    # [1] 같은 번호 제거
                    clean_item = item.split(" [")[0] if " [" in item else item
                    result += f"• {clean_item}\n"
            result += "\n"
    
    return result

def format_general_safety_info(data):
    """일반적인 안전정보 포맷팅"""
    result = ""
    
    if "정의" in data:
        result += f"**정의**: {data['정의']}\n\n"
    
    if "핵심_안전수칙" in data and isinstance(data["핵심_안전수칙"], list):
        result += "**핵심 안전수칙**\n"
        for rule in data["핵심_안전수칙"]:
            clean_rule = rule.split(" [")[0] if " [" in rule else rule
            result += f"• {clean_rule}\n"
        result += "\n"
    
    if "근로자는_이것만은_지켜야_합니다" in data and isinstance(data["근로자는_이것만은_지켜야_합니다"], list):
        result += "**근로자 준수사항**\n"
        for rule in data["근로자는_이것만은_지켜야_합니다"]:
            clean_rule = rule.split(" [")[0] if " [" in rule else rule
            result += f"• {clean_rule}\n"
        result += "\n"
    
    if "자율점검표" in data:
        result += "**자율점검표**\n"
        checklist = data["자율점검표"]
        if isinstance(checklist, dict):
            for category, items in checklist.items():
                result += f"**{category.replace('_', ' ')}**\n"
                if isinstance(items, list):
                    for item in items:
                        clean_item = item.split(" [")[0] if " [" in item else item
                        result += f"• {clean_item}\n"
                result += "\n"
    
    return result

def handle_jangmachul_query(query, target_lang, jangmachul_json_data, gemini_api_key):
    """장마철 자율안전 점검표 관련 질문 처리 - JSON RAG 우선, Gemini 보조 (외국어 지원)"""
    try:
        # JSON 데이터가 없으면 Gemini 일반 지식으로 답변
        if jangmachul_json_data is None:
            print("JSON 데이터가 없어서 Gemini로 답변 생성")
            return generate_jangmachul_answer_with_gemini(query, target_lang, gemini_api_key)
        
        # 현재 언어의 키워드 목록 가져오기
        current_keywords = JANGMACHUL_KEYWORDS.get(target_lang, JANGMACHUL_KEYWORDS["ko"])
        
        # 일반적인 안전점검표 요청 텍스트 패턴 정의 (언어별)
        general_patterns = {
            "ko": ["장마철 건설 현장 자율안전 점검표", "장마철 안전점검표", "장마철 점검표"],
            "en": ["rainy season construction site safety checklist", "rainy season safety checklist"],
            "vi": ["danh sách kiểm tra an toàn công trường mùa mưa", "danh sách kiểm tra an toàn mùa mưa"],
            "ja": ["梅雨期建設現場安全点検表", "梅雨期安全点検表"],
            "zh": ["雨季建筑工地安全检查表", "雨季安全检查表"],
            "zh-TW": ["雨季建築工地安全檢查表", "雨季安全檢查表"],
            "id": ["daftar periksa keselamatan lokasi konstruksi musim hujan", "daftar periksa keselamatan musim hujan"],
            "th": ["รายการตรวจสอบความปลอดภัยไซต์ก่อสร้างฤดูฝน", "รายการตรวจสอบความปลอดภัยฤดูฝน"],
            "fr": ["liste de contrôle de sécurité du chantier de construction en saison des pluies", "liste de contrôle de sécurité en saison des pluies"],
            "de": ["sicherheitscheckliste für baustellen in der regenzeit", "sicherheitscheckliste regenzeit"],
            "tl": ["checklist ng kaligtasan sa construction site sa panahon ng tag-ulan", "checklist ng kaligtasan sa tag-ulan"]
        }
        
        query_lower = query.lower()
        current_general_patterns = general_patterns.get(target_lang, general_patterns["ko"])
        
        # 일반적인 안전점검표 요청인지 확인
        is_general_request = any(pattern in query_lower for pattern in current_general_patterns)
        
        if is_general_request:
            # 일반적인 요청이면 메뉴 표시
            return JANGMACHUL_MENU_TEXT.get(target_lang, JANGMACHUL_MENU_TEXT["ko"])
        
        # 구체적인 키워드가 있는지 확인 (기술적인 용어들)
        specific_keywords = [kw for kw in current_keywords if kw.lower() in query_lower and kw.lower() not in [
            "rainy season", "safety checklist", "construction site", "safety inspection",
            "장마철", "자율안전", "점검표",
            "mùa mưa", "danh sách kiểm tra an toàn", "công trường xây dựng", "kiểm tra an toàn",
            "梅雨期", "安全点検表", "建設現場", "安全点検",
            "雨季", "安全检查表", "建筑工地", "安全检查",
            "musim hujan", "daftar periksa keselamatan", "lokasi konstruksi", "inspeksi keselamatan",
            "ฤดูฝน", "รายการตรวจสอบความปลอดภัย", "ไซต์ก่อสร้าง", "การตรวจสอบความปลอดภัย",
            "saison des pluies", "liste de contrôle de sécurité", "chantier de construction", "inspection de sécurité",
            "regenzeit", "sicherheitscheckliste", "baustelle", "sicherheitsinspektion",
            "tag-ulan", "checklist ng kaligtasan", "construction site"
        ]]
        
        # 구체적인 키워드가 있으면 JSON에서 검색, 없으면 전체 메뉴 표시
        if not specific_keywords:
            # 메뉴 텍스트 반환
            return JANGMACHUL_MENU_TEXT.get(target_lang, JANGMACHUL_MENU_TEXT["ko"])
        
        # JSON에서 관련 정보 검색
        print(f"JSON 검색 시작: {query}")
        search_results = search_jangmachul_json(query, jangmachul_json_data)
        
        if search_results:
            print(f"JSON에서 {len(search_results)}개 결과 찾음")
            formatted_result = format_jangmachul_results(search_results, target_lang, query)
            if formatted_result:
                return formatted_result
        
        # JSON에서 관련 정보를 찾지 못한 경우 Gemini로 대체
        print("JSON에서 관련 정보를 찾지 못해 Gemini로 답변 생성")
        return generate_jangmachul_answer_with_gemini(query, target_lang, gemini_api_key)
        
    except Exception as e:
        print(f"장마철 질문 처리 오류: {e}")
        print("오류가 발생하여 Gemini로 답변 생성")
        return generate_jangmachul_answer_with_gemini(query, target_lang, gemini_api_key)

def handle_onyul_query(query, target_lang, onyul_json_data, gemini_api_key):
    """온열질환 예방조치 관련 질문 처리 - 항상 Gemini API 사용"""
    try:
        print("온열질환 관련 질문은 항상 Gemini API로 답변 생성")
        return generate_onyul_answer_with_gemini(query, target_lang, gemini_api_key)
        
    except Exception as e:
        print(f"온열질환 질문 처리 오류: {e}")
        print("오류가 발생하여 Gemini로 답변 생성")
        return generate_onyul_answer_with_gemini(query, target_lang, gemini_api_key)

def format_excavation_info(excavation_data, target_lang):
    """굴착사면 무너짐 정보 포맷"""
    result = "🏗️ **굴착사면 무너짐 예방**\n\n"
    
    if "정의" in excavation_data:
        result += f"**정의**: {excavation_data['정의']}\n\n"
    
    if "핵심_안전수칙" in excavation_data:
        result += "**핵심 안전수칙**\n"
        for rule in excavation_data["핵심_안전수칙"]:
            result += f"• {rule}\n"
        result += "\n"
    
    if "근로자는_이것만은_지켜야_합니다" in excavation_data:
        result += "**근로자 준수사항**\n"
        for item in excavation_data["근로자는_이것만은_지켜야_합니다"]:
            result += f"• {item}\n"
        result += "\n"
    
    return result

# 통합 RAG 답변 함수들
def foreign_worker_rag_answer(query, target_lang, vector_db_foreign_worker, gemini_api_key, conversation_context=None, jangmachul_json_data=None, onyul_json_data=None):
    """외국인 근로자 RAG 답변 처리 (장마철/온열질환 포함)"""
    try:
        print(f"\n" + "="*80)
        print(f"[SEARCH] [DEBUG] 외국인 권리구제 RAG 질문: {query}")
        print(f"[SEARCH] [DEBUG] 타겟 언어: {target_lang}")
        print(f"[SEARCH] [DEBUG] 질문 길이: {len(query)}자")
        print(f"[SEARCH] [DEBUG] 질문 소문자: {query.lower()}")
        
        # 1. 장마철 안전점검표 관련 질문 확인 (외국어 지원)
        jangmachul_keywords = JANGMACHUL_KEYWORDS.get(target_lang, JANGMACHUL_KEYWORDS["ko"])
        
        matched_jangmachul = [k for k in jangmachul_keywords if k.lower() in query.lower()]
        print(f"[SEARCH] [DEBUG] 장마철 키워드 매칭 결과: {matched_jangmachul}")
        
        if matched_jangmachul:
            print(f"[SUCCESS] [DEBUG] 장마철 자율안전 점검표로 라우팅: {query}")
            result = handle_jangmachul_query(query, target_lang, jangmachul_json_data, gemini_api_key)
            print(f"[SUCCESS] [DEBUG] 장마철 점검표 응답 길이: {len(result)}자")
            print("="*80)
            return result
        
        # 2. 온열질환 관련 질문 확인
        onyul_keywords = [
            "온열질환", "폭염", "열사병", "더위",
            "체감온도", "기분상쾌", "수분섭취", "휴식", "그늘",
            "냉방", "통풍", "바람", "쉼터", "물", "음료",
            "열경련", "열실신", "열피로", "일사병",
            "5대 기본", "기본 수칙", "예방 수칙", "수칙", "기본원칙",
            "예방 방법", "대처 방법", "응급처치", "안전수칙"
        ]
        
        matched_onyul = [k for k in onyul_keywords if k in query.lower()]
        print(f"[SEARCH] [DEBUG] 온열질환 키워드 매칭 결과: {matched_onyul}")
        
        if matched_onyul:
            print(f"[SUCCESS] [DEBUG] 온열질환 예방조치로 라우팅: {query}")
            result = handle_onyul_query(query, target_lang, onyul_json_data, gemini_api_key)
            print(f"[SUCCESS] [DEBUG] 온열질환 응답 길이: {len(result)}자")
            print("="*80)
            return result
        
        # 3. 건설 현장 자율안전 점검표 관련이 아니면 -> 외국인근로자.pkl 우선 검색
        print(f"[SEARCH] [DEBUG] 건설/온열질환 관련이 아님 -> 외국인근로자.pkl에서 검색")
        
        if vector_db_foreign_worker is None:
            print(f"[ERROR] [DEBUG] 외국인 권리구제 벡터DB가 None입니다!")
            error_messages = {
                "ko": "죄송합니다. RAG 기능이 현재 사용할 수 없습니다. (외국인 권리구제 벡터DB가 로드되지 않았습니다.)",
                "en": "Sorry, the RAG function is currently unavailable. (Foreign worker rights vector database not loaded.)",
                "vi": "Xin lỗi, chức năng RAG hiện không khả dụng. (Cơ sở dữ liệu vector quyền lợi người lao động nước ngoài chưa được tải.)",
                "zh": "抱歉，RAG功能目前不可用。(外国工人权益向量数据库未加载。)",
                "ja": "申し訳ございません。RAG機能は現在利用できません。(外国人労働者権利ベクターデータベースが読み込まれていません。)"
            }
            print("="*80)
            return error_messages.get(target_lang, error_messages["ko"])
        
        # 외국인근로자.pkl에서 답변 검색
        rag_result = answer_with_rag_foreign_worker(query, vector_db_foreign_worker, gemini_api_key, target_lang=target_lang)
        
        # RAG 결과가 "관련 내용을 찾을 수 없습니다" 류의 메시지인지 확인
        not_found_messages = [
            "참고 정보에서 관련 내용을 찾을 수 없습니다",
            "Related content could not be found",
            "Không thể tìm thấy nội dung liên quan", 
            "找不到相关内容",
            "関連内容が見つかりませんでした"
        ]
        
        is_not_found = any(msg in rag_result for msg in not_found_messages)
        
        if is_not_found:
            print(f"[WARNING] [DEBUG] 외국인근로자.pkl에서 답변을 찾지 못함 -> Gemini API 폴백")
            gemini_result = generate_gemini_fallback_answer(query, target_lang, gemini_api_key)
            print("="*80)
            return gemini_result
        else:
            print(f"[SUCCESS] [DEBUG] 외국인근로자.pkl에서 답변 찾음: {len(rag_result)}자")
            print("="*80)
            return rag_result
            
    except Exception as e:
        print(f"[ERROR] [DEBUG] 외국인 근로자 RAG 처리 중 예외 발생: {e}")
        # 오류 발생시 Gemini API 폴백
        try:
            fallback_result = generate_gemini_fallback_answer(query, target_lang, gemini_api_key)
            print("="*80)
            return fallback_result
        except Exception as fallback_error:
            print(f"[ERROR] [DEBUG] Gemini API 폴백도 실패: {fallback_error}")
            error_messages = {
                "ko": "죄송합니다. 외국인 근로자 권리구제 정보를 찾을 수 없습니다.",
                "en": "Sorry, foreign worker rights information could not be found.",
                "vi": "Xin lỗi, không thể tìm thấy thông tin quyền lợi người lao động nước ngoài.",
                "zh": "抱歉，找不到外国工人权益信息。",
                "ja": "申し訳ございません。外国人労働者の権利救済情報が見つかりませんでした。"
            }
            print("="*80)
            return error_messages.get(target_lang, error_messages["ko"])