import flet as ft
import os
from config import GEMINI_API_KEY, MODEL_NAME
from flet import Column, Switch
import time
from firebase_admin import db
import uuid
import threading
import google.generativeai as genai
import atexit
import re

IS_SERVER = os.environ.get("CLOUDTYPE") == "1"

# 부적절한 단어 필터링 (욕설, 스팸 등)
INAPPROPRIATE_WORDS = [
    # 한국어 욕설
    "씨발", "개새끼", "병신", "미친", "바보", "멍청이", "등신", "개자식", "새끼", "좆", "보지", "자지",
    # 영어 욕설
    "fuck", "shit", "bitch", "asshole", "dick", "pussy", "cock", "cunt", "whore", "slut",
    # 스팸 단어
    "광고", "홍보", "판매", "구매", "돈", "돈벌이", "수익", "투자", "부업", "부자", "돈많은",
    # 반복 스팸
    "ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ", "ㅎㅎㅎㅎㅎㅎㅎㅎㅎㅎ", "!!!!!", "?????", "ㅠㅠㅠㅠㅠㅠㅠㅠㅠㅠ"
]

def is_inappropriate_message(message):
    """부적절한 메시지인지 확인"""
    message_lower = message.lower()
    
    # 부적절한 단어 포함 여부 확인
    for word in INAPPROPRIATE_WORDS:
        if word in message_lower:
            return True, f"부적절한 단어가 포함되어 있습니다: {word}"
    
    # 반복 문자 체크 (같은 문자 5번 이상 반복)
    repeated_chars = re.findall(r'(.)\1{4,}', message)
    if repeated_chars:
        return True, "반복되는 문자가 너무 많습니다"
    
    # 메시지 길이 체크 (너무 긴 메시지)
    if len(message) > 500:
        return True, "메시지가 너무 깁니다 (500자 제한)"
    
    # URL 스팸 체크
    url_count = message.count('http') + message.count('www')
    if url_count > 2:
        return True, "URL이 너무 많습니다"
    
    return False, ""

def filter_message(message):
    """메시지 필터링 (부적절한 단어 마스킹)"""
    filtered_message = message
    for word in INAPPROPRIATE_WORDS:
        if word.lower() in filtered_message.lower():
            # 부적절한 단어를 *로 마스킹
            import re
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            filtered_message = pattern.sub('*' * len(word), filtered_message)
    
    return filtered_message

# Gemini 기반 번역 함수 (예시: 실제 구현 필요)
def translate_message(text, target_lang):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        # 언어 코드 → 영어 언어명 매핑
        lang_map = {
            "en": "English", "ko": "Korean", "ja": "Japanese", "zh": "Chinese", "zh-TW": "Traditional Chinese", "id": "Indonesian", "vi": "Vietnamese", "fr": "French", "de": "German", "th": "Thai", "tl": "Filipino", "uz": "Uzbek", "ne": "Nepali", "tet": "Tetum", "lo": "Lao", "mn": "Mongolian", "my": "Burmese", "bn": "Bengali", "si": "Sinhala", "km": "Khmer", "ky": "Kyrgyz", "ur": "Urdu"
        }
        target_lang_name = lang_map.get(target_lang, target_lang)
        prompt = f"Translate the following text to {target_lang_name} and return only the translation.\n{text}"
        response = model.generate_content(prompt, generation_config={"max_output_tokens": 512, "temperature": 0.2})
        return response.text.strip()
    except Exception as e:
        return f"[번역 오류] {e}"

# 언어 코드에 따른 전체 언어 이름 매핑
LANG_NAME_MAP = {
    "ko": "한국어", "en": "영어", "ja": "일본어", "zh": "중국어",
    "fr": "프랑스어", "de": "독일어", "th": "태국어", "vi": "베트남어",
    "zh-TW": "대만어", "zh-HK": "홍콩어", "id": "인도네시아어", "tl": "필리핀어",
    "zh-SG": "싱가포르 중국어", "en-SG": "싱가포르 영어", "ms-SG": "싱가포르 말레이어", "ta-SG": "싱가포르 타밀어",
    "uz": "우즈베키스탄어", "ne": "네팔어", "tet": "동티모르어", "lo": "라오스어",
    "mn": "몽골어", "my": "미얀마어", "bn": "방글라데시어", "si": "스리랑카어",
    "km": "캄보디아어", "ky": "키르기스스탄어", "ur": "파키스탄어"
}

# 부산 맛집 가이드 텍스트 다국어 사전
BUSAN_FOOD_GUIDE_TEXTS = {
    "ko": {
        "title": "부산 맛집 검색",
        "info": "다음과 같은 정보를 질문할 수 있습니다:",
        "items": [
            "🍜 부산의 유명한 국수 맛집",
            "🦐 회와 해산물 전문점",
            "🍖 삼겹살과 고기집",
            "🍲 국밥과 탕 요리",
            "🍰 카페와 디저트",
            "🍺 술집과 포장마차",
            "🥢 지역별 맛집 추천",
            "💰 가격대별 음식점"
        ],
        "example_title": "질문 예시:",
        "examples": [
            "• 부산에서 유명한 돼지국밥집 추천해줘",
            "• 해운대구에 있는 맛집 알려줘",
            "• 부산역 근처 돼지국밥골목 맛집은?",
            "• 남포동에 있는 오래된 맛집은?",
            "• 부산에서 카페 추천해줘",
            "• 강서구에 있는 맛집은?",
            "• 금정구 국수 맛집은?",
            "• 부산에서 해산물 맛집 추천해줘"
        ],
        "input_hint": "부산 맛집에 대해 궁금한 것을 물어보세요! 🍽️"
    },
    "en": {
        "title": "Busan Restaurant Search",
        "info": "You can ask about:",
        "items": [
            "🍜 Famous noodle restaurants in Busan",
            "🦐 Sashimi and seafood specialists",
            "🍖 BBQ and meat restaurants",
            "🍲 Soup and stew dishes",
            "🍰 Cafes and desserts",
            "🍺 Bars and street food stalls",
            "🥢 Regional restaurant recommendations",
            "💰 Restaurants by price range"
        ],
        "example_title": "Example questions:",
        "examples": [
            "• Recommend famous pork soup restaurants in Busan",
            "• Tell me about restaurants in Haeundae-gu",
            "• Restaurants near Busan Station pork soup alley",
            "• Old restaurants in Nampo-dong",
            "• Recommend cafes in Busan",
            "• Restaurants in Gangseo-gu",
            "• Noodle restaurants in Geumjeong-gu",
            "• Recommend seafood restaurants in Busan"
        ],
        "input_hint": "Ask anything about Busan restaurants! 🍽️"
    },
    "ja": {
        "title": "釜山グルメ検索",
        "info": "以下について質問できます:",
        "items": [
            "🍜 釜山の有名な麺料理店",
            "🦐 刺身・海鮮専門店",
            "🍖 焼肉・肉料理店",
            "🍲 スープ・鍋料理",
            "🍰 カフェ・デザート",
            "🍺 居酒屋・屋台",
            "🥢 地域別レストラン推薦",
            "💰 価格帯別レストラン"
        ],
        "example_title": "質問例:",
        "examples": [
            "• 釜山で有名な豚骨スープ店を推薦して",
            "• 海雲台区にあるレストランを教えて",
            "• 釜山駅近くの豚骨スープ通りにあるレストランは？",
            "• 南浦洞にある古いレストランは？",
            "• 釜山でカフェを推薦して",
            "• 江西区にあるレストランは？",
            "• 金井区の麺店は？",
            "• 釜山で海鮮料理店を推薦して"
        ],
        "input_hint": "釜山グルメについて何でも聞いてください！🍽️"
    },
    "zh": {
        "title": "釜山美食搜索",
        "info": "您可以询问:",
        "items": [
            "🍜 釜山著名面条店",
            "🦐 生鱼片和海鲜专门店",
            "🍖 烤肉和肉类餐厅",
            "🍲 汤类和炖菜",
            "🍰 咖啡厅和甜点",
            "🍺 酒吧和小吃摊",
            "🥢 地区餐厅推荐",
            "💰 按价位分类的餐厅"
        ],
        "example_title": "问题示例:",
        "examples": [
            "• 推荐釜山有名的猪肉汤饭店",
            "• 告诉我海云台区的餐厅",
            "• 釜山站附近猪肉汤饭街的餐厅",
            "• 南浦洞的老餐厅",
            "• 推荐釜山的咖啡厅",
            "• 江西区的餐厅",
            "• 金井区的面条店",
            "• 推荐釜山海鲜餐厅"
        ],
        "input_hint": "请询问釜山美食相关问题！🍽️"
    },
    "vi": {
        "title": "Tìm kiếm nhà hàng Busan",
        "info": "Bạn có thể hỏi về:",
        "items": [
            "🍜 Các nhà hàng mì nổi tiếng ở Busan",
            "🦐 Chuyên gia sashimi và hải sản",
            "🍖 Nhà hàng BBQ và thịt nướng",
            "🍲 Súp và món hầm",
            "🍰 Quán cà phê và tráng miệng",
            "🍺 Quán bar và xe đẩy thức ăn",
            "🥢 Gợi ý nhà hàng theo vùng",
            "💰 Nhà hàng theo mức giá"
        ],
        "example_title": "Ví dụ câu hỏi:",
        "examples": [
            "• Gợi ý nhà hàng súp thịt heo nổi tiếng ở Busan",
            "• Cho tôi biết về nhà hàng ở Haeundae-gu",
            "• Nhà hàng gần phố súp thịt heo ga Busan",
            "• Nhà hàng cũ ở Nampo-dong",
            "• Gợi ý quán cà phê ở Busan",
            "• Nhà hàng ở Gangseo-gu",
            "• Nhà hàng mì ở Geumjeong-gu",
            "• Gợi ý nhà hàng hải sản ở Busan"
        ],
        "input_hint": "Hãy hỏi bất cứ điều gì về nhà hàng Busan! 🍽️"
    },
    "th": {
        "title": "ค้นหาร้านอาหารปูซาน",
        "info": "คุณสามารถถามเกี่ยวกับ:",
        "items": [
            "🍜 ร้านก๋วยเตี๋ยวที่มีชื่อเสียงในปูซาน",
            "🦐 ร้านซาชิมิและอาหารทะเล",
            "🍖 ร้านบาร์บีคิวและเนื้อ",
            "🍲 ซุปและสตูว์",
            "🍰 คาเฟ่และของหวาน",
            "🍺 บาร์และร้านอาหารริมทาง",
            "🥢 แนะนำร้านอาหารตามภูมิภาค",
            "💰 ร้านอาหารตามช่วงราคา"
        ],
        "example_title": "ตัวอย่างคำถาม:",
        "examples": [
            "• แนะนำร้านซุปหมูที่มีชื่อเสียงในปูซาน",
            "• บอกฉันเกี่ยวกับร้านอาหารในฮันอุนแด-กู",
            "• ร้านอาหารใกล้ถนนซุปหมูสถานีปูซาน",
            "• ร้านอาหารเก่าในนัมโปดง",
            "• แนะนำคาเฟ่ในปูซาน",
            "• ร้านอาหารในกังซอ-กู",
            "• ร้านก๋วยเตี๋ยวในกึมจอง-กู",
            "• แนะนำร้านอาหารทะเลในปูซาน"
        ],
        "input_hint": "ถามอะไรก็ได้เกี่ยวกับร้านอาหารปูซาน! 🍽️"
    },
    "fr": {
        "title": "Recherche de restaurants Busan",
        "info": "Vous pouvez demander:",
        "items": [
            "🍜 Restaurants de nouilles célèbres à Busan",
            "🦐 Spécialistes de sashimi et fruits de mer",
            "🍖 Restaurants BBQ et viande",
            "🍲 Soupes et ragoûts",
            "🍰 Cafés et desserts",
            "🍺 Bars et stands de rue",
            "🥢 Recommandations de restaurants par région",
            "💰 Restaurants par gamme de prix"
        ],
        "example_title": "Exemples de questions:",
        "examples": [
            "• Recommandez des restaurants de soupe de porc célèbres à Busan",
            "• Parlez-moi des restaurants dans Haeundae-gu",
            "• Restaurants près de l'allée de soupe de porc de la gare de Busan",
            "• Vieux restaurants à Nampo-dong",
            "• Recommandez des cafés à Busan",
            "• Restaurants dans Gangseo-gu",
            "• Restaurants de nouilles dans Geumjeong-gu",
            "• Recommandez des restaurants de fruits de mer à Busan"
        ],
        "input_hint": "Demandez tout sur les restaurants de Busan! 🍽️"
    },
    "de": {
        "title": "Busan Restaurant-Suche",
        "info": "Sie können fragen nach:",
        "items": [
            "🍜 Berühmte Nudelrestaurants in Busan",
            "🦐 Sashimi- und Meeresfrüchte-Spezialisten",
            "🍖 BBQ- und Fleischrestaurants",
            "🍲 Suppen und Eintöpfe",
            "🍰 Cafés und Desserts",
            "🍺 Bars und Straßenstände",
            "🥢 Restaurantempfehlungen nach Region",
            "💰 Restaurants nach Preisklasse"
        ],
        "example_title": "Beispielfragen:",
        "examples": [
            "• Empfehlen Sie berühmte Schweinefleischsuppen-Restaurants in Busan",
            "• Erzählen Sie mir von Restaurants in Haeundae-gu",
            "• Restaurants in der Nähe der Schweinefleischsuppen-Gasse am Busan-Bahnhof",
            "• Alte Restaurants in Nampo-dong",
            "• Empfehlen Sie Cafés in Busan",
            "• Restaurants in Gangseo-gu",
            "• Nudelrestaurants in Geumjeong-gu",
            "• Empfehlen Sie Meeresfrüchte-Restaurants in Busan"
        ],
        "input_hint": "Fragen Sie alles über Busan-Restaurants! 🍽️"
    },
    "zh-TW": {
        "title": "釜山美食搜尋",
        "info": "您可以詢問:",
        "items": [
            "🍜 釜山著名麵條店",
            "🦐 生魚片和海鮮專門店",
            "🍖 烤肉和肉類餐廳",
            "🍲 湯類和燉菜",
            "🍰 咖啡廳和甜點",
            "🍺 酒吧和小吃攤",
            "🥢 地區餐廳推薦",
            "💰 按價位分類的餐廳"
        ],
        "example_title": "問題範例:",
        "examples": [
            "• 推薦釜山有名的豬肉湯飯店",
            "• 告訴我海雲台區的餐廳",
            "• 釜山站附近豬肉湯飯街的餐廳",
            "• 南浦洞的老餐廳",
            "• 推薦釜山的咖啡廳",
            "• 江西區的餐廳",
            "• 金井區的麵條店",
            "• 推薦釜山海鮮餐廳"
        ],
        "input_hint": "請詢問釜山美食相關問題！🍽️"
    },
    "id": {
        "title": "Pencarian Restoran Busan",
        "info": "Anda dapat bertanya tentang:",
        "items": [
            "🍜 Restoran mie terkenal di Busan",
            "🦐 Spesialis sashimi dan seafood",
            "🍖 Restoran BBQ dan daging",
            "🍲 Sup dan rebusan",
            "🍰 Kafe dan makanan penutup",
            "🍺 Bar dan warung kaki lima",
            "🥢 Rekomendasi restoran berdasarkan wilayah",
            "💰 Restoran berdasarkan kisaran harga"
        ],
        "example_title": "Contoh pertanyaan:",
        "examples": [
            "• Rekomendasikan restoran sup babi terkenal di Busan",
            "• Beritahu saya tentang restoran di Haeundae-gu",
            "• Restoran dekat gang sup babi Stasiun Busan",
            "• Restoran lama di Nampo-dong",
            "• Rekomendasikan kafe di Busan",
            "• Restoran di Gangseo-gu",
            "• Restoran mie di Geumjeong-gu",
            "• Rekomendasikan restoran seafood di Busan"
        ],
        "input_hint": "Tanyakan apa saja tentang restoran Busan! 🍽️"
    },
    "tl": {
        "title": "Paghahanap ng Restaurant sa Busan",
        "info": "Maaari kang magtanong tungkol sa:",
        "items": [
            "🍜 Mga sikat na noodle restaurant sa Busan",
            "🦐 Mga eksperto sa sashimi at seafood",
            "🍖 Mga BBQ at meat restaurant",
            "🍲 Mga sopas at nilaga",
            "🍰 Mga cafe at dessert",
            "🍺 Mga bar at street food stall",
            "🥢 Mga rekomendasyon ng restaurant ayon sa lugar",
            "💰 Mga restaurant ayon sa presyo"
        ],
        "example_title": "Mga halimbawa ng tanong:",
        "examples": [
            "• Mag-recommend ng sikat na pork soup restaurant sa Busan",
            "• Sabihin mo sa akin ang tungkol sa mga restaurant sa Haeundae-gu",
            "• Mga restaurant malapit sa pork soup alley ng Busan Station",
            "• Mga lumang restaurant sa Nampo-dong",
            "• Mag-recommend ng mga cafe sa Busan",
            "• Mga restaurant sa Gangseo-gu",
            "• Mga noodle restaurant sa Geumjeong-gu",
            "• Mag-recommend ng mga seafood restaurant sa Busan"
        ],
        "input_hint": "Magtanong ng kahit ano tungkol sa mga restaurant sa Busan! 🍽️"
    }
}

# RAG 가이드 텍스트 다국어 사전 (상세 구조)
RAG_GUIDE_TEXTS = {
    "ko": {
        "title": "다문화가족 한국생활안내",
        "info": "다음과 같은 정보를 질문할 수 있습니다:",
        "items": [
            "🏥 병원, 약국 이용 방법",
            "🏦 은행, 우체국, 관공서 이용",
            "🚌 교통수단 이용 (버스, 지하철, 기차)",
            "🚗 운전면허, 자가용, 택시 이용",
            "🏠 집 구하기",
            "📱 핸드폰 사용하기",
            "🗑️ 쓰레기 버리기 (종량제, 분리배출)",
            "🆔 외국인등록증 신청, 체류기간 연장"
        ],
        "example_title": "질문 예시:",
        "examples": [
            "• 외국인등록을 하려면 어디로 가요?",
            "• 체류기간이 3개월 남았는데 연장하려면 어떻게 해요?",
            "• 외국인은 핸드폰을 어떻게 사용하나요?",
            "• 전셋집이 뭐예요?",
            "• 공인중개사무소가 뭐죠?",
            "• 집 계약서는 어떻게 쓰면 되나요?",
            "• 대한민국 운전면허증을 받는 과정은?",
            "• 쓰레기 봉투는 어디서 사나요?",
            "• 쓰레기 버리는 방법은요?",
            "• 몸이 아픈데 어떡하죠?",
            "• 병원에 갈 때 필요한 건강보험증이 뭐죠?",
            "• 한의원은 일반병원과 다른가요?",
            "• 처방전이 없는데 어떻게 하나요?",
            "• 은행계좌는 어떻게 만들어요?",
            "• 외국에 물건을 보내고 싶은데 어떻게 하죠?",
            "• 24시간 콜센터 번호는 어떻게 되죠?",
            "• 긴급전화 번호는 뭐에요?",
            "• 한국어를 배울 수 있는 방법은요?"
        ],
        "input_hint": "아래에 질문을 입력해보세요! 💬"
    },
    "en": {
        "title": "Korean Life Guide for Multicultural Families",
        "info": "You can ask about the following topics:",
        "items": [
            "🏥 How to use hospitals and pharmacies",
            "🏦 How to use banks, post offices, government offices",
            "🚌 How to use public transport (bus, subway, train)",
            "🚗 Driver's license, private car, taxi",
            "🏠 Finding a house",
            "📱 Using a mobile phone",
            "🗑️ How to dispose of trash (volume-based, recycling)",
            "🆔 Alien registration, extension of stay"
        ],
        "example_title": "Example questions:",
        "examples": [
            "• Where do I go to register as a foreigner?",
            "• My stay period expires in 3 months, how do I extend it?",
            "• How do foreigners use mobile phones?",
            "• What is jeonse (deposit-based housing)?",
            "• What is a real estate agency?",
            "• How do I write a housing contract?",
            "• What is the process for getting a Korean driver's license?",
            "• Where do I buy trash bags?",
            "• How do I dispose of trash?",
            "• I'm sick, what should I do?",
            "• What is health insurance card needed for hospitals?",
            "• Is oriental medicine different from regular hospitals?",
            "• What if I don't have a prescription?",
            "• How do I open a bank account?",
            "• How do I send things abroad?",
            "• What are the 24-hour call center numbers?",
            "• What are the emergency numbers?",
            "• How can I learn Korean?"
        ],
        "input_hint": "Type your question below! 💬"
    },
    "ja": {
        "title": "多文化家族のための韓国生活ガイド",
        "info": "以下のトピックについて質問できます:",
        "items": [
            "🏥 病院、薬局の利用方法",
            "🏦 銀行、郵便局、政府機関の利用",
            "🚌 公共交通機関の利用（バス、地下鉄、電車）",
            "🚗 運転免許、自家用車、タクシー",
            "🏠 家探し",
            "📱 携帯電話の使用",
            "🗑️ ゴミの捨て方（従量制、リサイクル）",
            "🆔 外国人登録、滞在期間延長"
        ],
        "example_title": "質問例:",
        "examples": [
            "• 外国人登録はどこで行いますか？",
            "• 滞在期間が3ヶ月残っていますが、延長するにはどうすればいいですか？",
            "• 外国人は携帯電話をどのように使用しますか？",
            "• 全税（保証金ベースの住宅）とは何ですか？",
            "• 不動産会社とは何ですか？",
            "• 住宅契約書はどのように書けばいいですか？",
            "• 韓国の運転免許を取得する手続きは？",
            "• ゴミ袋はどこで買えますか？",
            "• ゴミの捨て方は？",
            "• 体調が悪いのですが、どうすればいいですか？",
            "• 病院に行く際に必要な健康保険証とは？",
            "• 韓医院は一般병원と違いますか？",
            "• 処方箋がない場合はどうすればいいですか？",
            "• 銀行口座はどのように開設しますか？",
            "• 海外に物を送りたいのですが、どうすればいいですか？",
            "• 24時間コールセンターの番号は？",
            "• 緊急전화番号は何ですか？",
            "• 韓国語を学ぶ方法は？"
        ],
        "input_hint": "下に質問を入力してください！💬"
    },
    "zh": {
        "title": "多元文化家庭韩国生活指南",
        "info": "您可以询问以下主题:",
        "items": [
            "🏥 如何使用医院和药房",
            "🏦 如何使用银行、邮局、政府机关",
            "🚌 如何使用公共交通（公交车、地铁、火车）",
            "🚗 驾照、私家车、出租车",
            "🏠 找房子",
            "📱 使用手机",
            "🗑️ 如何丢弃垃圾（按量收费、回收）",
            "🆔 外国人登记、延长停留时间"
        ],
        "example_title": "问题示例:",
        "examples": [
            "• 我要去哪里办理外国人登记？",
            "• 我的停留期限还剩3个月，如何延长？",
            "• 外国人如何使用手机？",
            "• 什么是全租房？",
            "• 什么是房地产中介？",
            "• 我该如何写房屋合约？",
            "• 取得韩国驾照的流程是什么？",
            "• 我在哪里买垃圾袋？",
            "• 我该如何丢垃圾？",
            "• 我生病了该怎么办？",
            "• 去医院需要的健康保险卡是什么？",
            "• 韩医院和一般医院有什么不同？",
            "• 如果没有处方怎么办？",
            "• 我该如何开银行账户？",
            "• 我该如何寄东西到国外？",
            "• 24小时客服电话是多少？",
            "• 紧急电话号码是什么？",
            "• 我该如何学韩文？"
        ],
        "input_hint": "请在下方输入您的问题！💬"
    },
    "zh-TW": {
        "title": "多元文化家庭韓國生活指南",
        "info": "您可以詢問以下主題:",
        "items": [
            "🏥 如何使用醫院和藥局",
            "🏦 如何使用銀行、郵局、政府機關",
            "🚌 如何搭乘大眾運輸（公車、地鐵、火車）",
            "🚗 駕照、私家車、計程車",
            "🏠 找房子",
            "📱 使用手機",
            "🗑️ 如何丟垃圾（按量收費、回收）",
            "🆔 外國人登記、延長停留時間"
        ],
        "example_title": "問題範例:",
        "examples": [
            "• 我要去哪裡辦理外國人登記？",
            "• 我的停留期限還剩3個月，如何延長？",
            "• 外國人如何使用手機？",
            "• 什麽是全租房？",
            "• 什麽是房地產仲介？",
            "• 我該如何寫房屋合約？",
            "• 取得韓國駕照的流程是什麽？",
            "• 我在哪裡買垃圾袋？",
            "• 我該如何丟垃圾？",
            "• 我生病了該怎麽辦？",
            "• 去醫院需要的健康保險卡是什麽？",
            "• 韓醫院和一般醫院有什麽不同？",
            "• 如果沒有處方怎麽辦？",
            "• 我該如何開銀行帳戶？",
            "• 我該如何寄東西到國外？",
            "• 24小時客服電話是多少？",
            "• 緊急電話號碼是什麽？",
            "• 我該如何學韓文？"
        ],
        "input_hint": "請在下方輸入您的問題！💬"
    },
    "id": {
        "title": "Panduan Hidup di Korea untuk Keluarga Multikultural",
        "info": "Anda dapat bertanya tentang topik berikut:",
        "items": [
            "🏥 Cara menggunakan rumah sakit dan apotek",
            "🏦 Cara menggunakan bank, kantor pos, kantor pemerintah",
            "🚌 Cara menggunakan transportasi umum (bus, subway, kereta)",
            "🚗 SIM, mobil pribadi, taksi",
            "🏠 Mencari rumah",
            "📱 Menggunakan ponsel",
            "🗑️ Cara membuang sampah (berdasarkan volume, daur ulang)",
            "🆔 Pendaftaran orang asing, perpanjangan masa tinggal"
        ],
        "example_title": "Contoh pertanyaan:",
        "examples": [
            "• Ke mana saya harus pergi untuk mendaftar sebagai orang asing?",
            "• Masa tinggal saya tersisa 3 bulan, bagaimana cara memperpanjangnya?",
            "• Bagaimana orang asing menggunakan ponsel?",
            "• Apa itu jeonse (rumah sewa deposit)?",
            "• Apa itu agen real estat?",
            "• Bagaimana cara menulis kontrak rumah?",
            "• Apa proses mendapatkan SIM Korea?",
            "• Di mana saya membeli kantong sampah?",
            "• Bagaimana cara membuang sampah?",
            "• Saya sakit, apa yang harus saya lakukan?",
            "• Apa itu kartu asuransi kesehatan untuk rumah sakit?",
            "• Apakah pengobatan oriental berbeda dengan rumah sakit biasa?",
            "• Bagaimana jika saya tidak punya resep?",
            "• Bagaimana cara membuka rekening bank?",
            "• Bagaimana cara mengirim barang ke luar negeri?",
            "• Berapa nomor call center 24 jam?",
            "• Berapa nomor darurat?",
            "• Bagaimana cara belajar bahasa Korea?"
        ],
        "input_hint": "Tulis pertanyaan Anda di bawah ini! 💬"
    },
    "vi": {
        "title": "Hướng dẫn cuộc sống Hàn Quốc cho gia đình đa văn hóa",
        "info": "Bạn có thể hỏi về các chủ đề sau:",
        "items": [
            "🏥 Cách sử dụng bệnh viện và nhà thuốc",
            "🏦 Cách sử dụng ngân hàng, bưu điện, cơ quan chính phủ",
            "🚌 Cách sử dụng phương tiện công cộng (xe buýt, tàu điện ngầm, tàu)",
            "🚗 Bằng lái xe, xe riêng, taxi",
            "🏠 Tìm nhà",
            "📱 Sử dụng điện thoại di động",
            "🗑️ Cách vứt rác (theo thể tích, tái chế)",
            "🆔 Đăng ký người nước ngoài, gia hạn thời gian lưu trú"
        ],
        "example_title": "Ví dụ câu hỏi:",
        "examples": [
            "• Tôi đi đâu để đăng ký người nước ngoài?",
            "• Thời gian lưu trú của tôi còn lại 3 tháng, làm thế nào để gia hạn?",
            "• Người nước ngoài sử dụng điện thoại di động như thế nào?",
            "• Jeonse (nhà ở theo tiền đặt cọc) là gì?",
            "• Công ty bất động sản là gì?",
            "• Tôi viết hợp đồng nhà như thế nào?",
            "• Quy trình lấy bằng lái xe Hàn Quốc là gì?",
            "• Tôi mua túi rác ở đâu?",
            "• Tôi vứt rác như thế nào?",
            "• Tôi bị bệnh, tôi nên làm gì?",
            "• Thẻ bảo hiểm y tế cần thiết cho bệnh viện là gì?",
            "• Y học cổ truyền có khác với bệnh viện thường không?",
            "• Nếu tôi không có đơn thuốc thì sao?",
            "• Tôi mở tài khoản ngân hàng như thế nào?",
            "• Tôi gửi đồ ra nước ngoài như thế nào?",
            "• Số điện thoại trung tâm cuộc gọi 24 giờ là gì?",
            "• Số điện thoại khẩn cấp là gì?",
            "• Tôi có thể học tiếng Hàn như thế nào?"
        ],
        "input_hint": "Nhập câu hỏi của bạn bên dưới! 💬"
    },
    "fr": {
        "title": "Guide de vie en Corée pour familles multiculturelles",
        "info": "Vous pouvez poser des questions sur les sujets suivants :",
        "items": [
            "🏥 Comment utiliser les hôpitaux et pharmacies",
            "🏦 Comment utiliser les banques, bureaux de poste, bureaux gouvernementaux",
            "🚌 Comment utiliser les transports publics (bus, métro, train)",
            "🚗 Permis de conduire, voiture privée, taxi",
            "🏠 Trouver une maison",
            "📱 Utiliser un téléphone portable",
            "🗑️ Comment jeter les déchets (basé sur le volume, recyclage)",
            "🆔 Enregistrement des étrangers, prolongation du séjour"
        ],
        "example_title": "Exemples de questions :",
        "examples": [
            "• Où dois-je aller pour m'enregistrer en tant qu'étranger ?",
            "• Ma période de séjour expire dans 3 mois, comment la prolonger ?",
            "• Comment les étrangers utilisent-ils les téléphones portables ?",
            "• Qu'est-ce que le jeonse (logement basé sur un dépôt) ?",
            "• Qu'est-ce qu'une agence immobilière ?",
            "• Comment rédiger un contrat de logement ?",
            "• Quel est le processus pour obtenir un permis de conduire coréen ?",
            "• Où acheter des sacs poubelle ?",
            "• Comment jeter les déchets ?",
            "• Je suis malade, que dois-je faire ?",
            "• Qu'est-ce que la carte d'assurance maladie pour les hôpitaux ?",
            "• La médecine orientale est-elle différente des hôpitaux ordinaires ?",
            "• Que faire si je n'ai pas d'ordonnance ?",
            "• Comment ouvrir un compte bancaire ?",
            "• Comment envoyer des objets à l'étranger ?",
            "• Quels sont les numéros de centre d'appels 24h ?",
            "• Quels sont les numéros d'urgence ?",
            "• Comment puis-je apprendre le coréen ?"
        ],
        "input_hint": "Tapez votre question ci-dessous ! 💬"
    },
    "de": {
        "title": "Leitfaden für das Leben in Korea für multikulturelle Familien",
        "info": "Sie können Fragen zu folgenden Themen stellen:",
        "items": [
            "🏥 Wie man Krankenhäuser und Apotheken nutzt",
            "🏦 Wie man Banken, Postämter, Regierungsbüros nutzt",
            "🚌 Wie man öffentliche Verkehrsmittel nutzt (Bus, U-Bahn, Zug)",
            "🚗 Führerschein, Privatauto, Taxi",
            "🏠 Haus finden",
            "📱 Mobiltelefon nutzen",
            "🗑️ Wie man Müll entsorgt (volumenbasiert, Recycling)",
            "🆔 Ausländerregistrierung, Aufenthaltsverlängerung"
        ],
        "example_title": "Beispielfragen:",
        "examples": [
            "• Wo muss ich mich als Ausländer registrieren?",
            "• Mein Aufenthalt läuft in 3 Monaten ab, wie verlängere ich ihn?",
            "• Wie nutzen Ausländer Mobiltelefone?",
            "• Was ist Jeonse (Mietwohnung mit Kaution)?",
            "• Was ist eine Immobilienagentur?",
            "• Wie schreibe ich einen Wohnungsvertrag?",
            "• Was ist der Prozess für einen koreanischen Führerschein?",
            "• Wo kaufe ich Müllbeutel?",
            "• Wie entsorge ich Müll?",
            "• Ich bin krank, was soll ich tun?",
            "• Was ist die Krankenversicherungskarte für Krankenhäuser?",
            "• Ist orientalische Medizin anders als normale Krankenhäuser?",
            "• Was, wenn ich kein Rezept habe?",
            "• Wie eröffne ich ein Bankkonto?",
            "• Wie sende ich Dinge ins Ausland?",
            "• Was sind die 24-Stunden-Callcenter-Nummern?",
            "• Was sind die Notrufnummern?",
            "• Wie kann ich Koreanisch lernen?"
        ],
        "input_hint": "Geben Sie Ihre Frage unten ein! 💬"
    },
    "th": {
        "title": "คู่มือการใช้ชีวิตในเกาหลีสำหรับครอบครัวพหุวัฒนธรรม",
        "info": "คุณสามารถถามเกี่ยวกับหัวข้อต่อไปนี้:",
        "items": [
            "🏥 วิธีใช้โรงพยาบาลและร้านขายยา",
            "🏦 วิธีใช้ธนาคาร ที่ทำการไปรษณีย์ สำนักงานรัฐบาล",
            "🚌 วิธีใช้ระบบขนส่งสาธารณะ (รถบัส รถไฟใต้ดิน รถไฟ)",
            "🚗 ใบขับขี่ รถส่วนตัว แท็กซี่",
            "🏠 หาบ้าน",
            "📱 ใช้โทรศัพท์มือถือ",
            "🗑️ วิธีทิ้งขยะ (ตามปริมาณ การรีไซเคิล)",
            "🆔 การลงทะเบียนชาวต่างชาติ การขยายเวลาพำนัก"
        ],
        "example_title": "ตัวอย่างคำถาม:",
        "examples": [
            "• ฉันจะไปลงทะเบียนเป็นชาวต่างชาติที่ไหน?",
            "• ระยะเวลาพำนักของฉันเหลือ 3 เดือน จะขยายอย่างไร?",
            "• ชาวต่างชาติใช้โทรศัพท์มือถืออย่างไร?",
            "• Jeonse (บ้านเช่าตามเงินมัดจำ) คืออะไร?",
            "• บริษัทอสังหาริมทรัพย์คืออะไร?",
            "• ฉันเขียนสัญญาบ้านอย่างไร?",
            "• กระบวนการขอใบขับขี่เกาหลีคืออะไร?",
            "• ฉันซื้อถุงขยะที่ไหน?",
            "• ฉันทิ้งขยะอย่างไร?",
            "• ฉันป่วย ฉันควรทำอย่างไร?",
            "• บัตรประกันสุขภาพที่จำเป็นสำหรับโรงพยาบาลคืออะไร?",
            "• การแพทย์แผนตะวันออกแตกต่างจากโรงพยาบาลทั่วไปหรือไม่?",
            "• ถ้าฉันไม่มีใบสั่งยาล่ะ?",
            "• ฉันเปิดบัญชีธนาคารอย่างไร?",
            "• ฉันส่งของไปต่างประเทศอย่างไร?",
            "• เบอร์ศูนย์บริการ 24 ชั่วโมงคืออะไร?",
            "• เบอร์ฉุกเฉินคืออะไร?",
            "• ฉันจะเรียนภาษาเกาหลีได้อย่างไร?"
        ],
        "input_hint": "พิมพ์คำถามของคุณด้านล่าง! 💬"
    },
    "uz": {
        "title": "Чет эл ишчилари ҳуқуқларини ҳимоя қилиш бўйича йўриқнома",
        "info": "Қуйидаги ҳуқуқ ҳимояси мавзулари ҳақида савол бера оласиз:",
        "items": [
            "💰 Иш ҳақининг қолдирилиши ва тўланиши",
            "🚫 Нодўст ундатиш ва ундатиш огоҳлантириши",
            "🏥 Иш ҳалокати ва иш билан боглиқ жароҳатлар",
            "🚨 Иш жойидаги жинсий таъқиб ва жинсий зўравонлик",
            "📞 Чет элликлар учун алоҳида суғурта ва маслаҳат",
            "📱 Шошилинч алока ва маслаҳат агентликлари",
            "⚖️ Меҳнат қонунлари ва ҳуқуқ ҳимояси жараёни"
        ],
        "example_title": "Савол мисоллари:",
        "examples": [
            "• Менинг иш ҳақим қолдирилган",
            "• Мен нодўст ундатилдим",
            "• Мен ишда жароҳатландим",
            "• Мен иш жойида жинсий таъқибга дуч келдим",
            "• Мен жинсий зўравонлик ёки таъқибга дуч келдим",
            "• Чет элликлар учун қандай суғурта мавжуд?",
            "• Кореяда қайси телефон рақамларини билишим керак?"
        ],
        "input_hint": "Қуйидаги ҳуқуқ ҳимояси саволингизни киритинг! 💬"
    },
    "ne": {
        "title": "विदेशी श्रमिक अधिकार संरक्षण गाइड",
        "info": "तपाईं निम्न अधिकार संरक्षण विषयहरूको बारेमा सोध्न सक्नुहुन्छ:",
        "items": [
            "💰 तलब रोक्ने र भुक्तानी",
            "🚫 अन्यायपूर्ण बर्खास्त र बर्खास्त सूचना",
            "🏥 औद्योगिक दुर्घटना र काम सम्बन्धित चोट",
            "🚨 कार्यस्थलमा यौन उत्पीडन र यौन हमला",
            "📞 विदेशीहरूको लागि विशेष बीमा र परामर्श",
            "📱 आकस्मिक सम्पर्क र परामर्श एजेन्सीहरू",
            "⚖️ श्रम कानून र अधिकार संरक्षण प्रक्रिया"
        ],
        "example_title": "प्रश्नहरूको उदाहरण:",
        "examples": [
            "• मेरो तलब रोकिएको छ",
            "• म अन्यायपूर्ण रूपमा बर्खास्त भएको थिएँ",
            "• म काममा चोट पुगेको थिएँ",
            "• म कार्यस्थलमा यौन उत्पीडनको अनुभव गरेको थिएँ",
            "• म यौन हमला वा उत्पीडनको शिकार भएको थिएँ",
            "• विदेशीहरूको लागि कुन बीमा उपलब्ध छ?",
            "• कोरियामा कुन फोन नम्बरहरू थाहा पाउनु पर्छ?"
        ],
        "input_hint": "तल आफ्नो अधिकार संरक्षण प्रश्न लेख्नुहोस्! 💬"
    },
    "tet": {
        "title": "Gia ba Knaar Direitu Trabalhadór Estranjeiru",
        "info": "Ita bele husu kona-ba topiku protesaun direitu sira ne'e:",
        "items": [
            "💰 Saláriu atrasu no pagamentu saláriu",
            "🚫 Despedida injusta no avizu despedida",
            "🏥 Asidente trabálhu no lesaun relasiona ho servisu",
            "🚨 Asédiu seksuál no atake seksuál iha fatin servisu",
            "📞 Seguru no konsellu espesiál ba estranjeiru",
            "📱 Kontaktu emergénsia no ajénsia konsellu",
            "⚖️ Lei trabálhu no prosedimentu protesaun direitu"
        ],
        "example_title": "Ezemplu pergunta sira:",
        "examples": [
            "• Ha'u-nia saláriu hetan atrasu",
            "• Ha'u hetan despedida injusta",
            "• Ha'u hetan lesaun iha servisu",
            "• Ha'u esperiénsia asédiu seksuál iha fatin servisu",
            "• Ha'u hetan atake ka asédiu seksuál",
            "• Seguru saida mak disponível ba estranjeiru?",
            "• Numeru telefone saida mak ha'u tenke hatene iha Korea?"
        ],
        "input_hint": "Hakerek ita-nia pergunta protesaun direitu iha okos! 💬"
    },
    "lo": {
        "title": "ຄູ່ມືການປົກປ້ອງສິດຂອງຄົນງານຕ່າງປະເທດ",
        "info": "ທ່ານສາມາດຖາມກ່ຽວກັບຫົວຂໍ້ການປົກປ້ອງສິດດັ່ງນີ້:",
        "items": [
            "💰 ຄ່າແຮງງານຄ້າງຊຳແລະການຈ່າຍຄ່າແຮງງານ",
            "🚫 ການໄລ່ອອກທີ່ບໍ່ຍຸດຕິທຳແລະການແຈ້ງໄລ່ອອກ",
            "🏥 ອຸປະຕິເຫດທາງອຸດສາຫະກຳແລະການບາດເຈັບທີ່ກ່ຽວຂ້ອງກັບການເຮັດວຽກ",
            "🚨 ການລະເມີດທາງເພດແລະການຮຸກຮານທາງເພດໃນສະຖານທີ່ເຮັດວຽກ",
            "📞 ການປະກັນໄພແລະການໃຫ້ຄຳປຶກສາສຳລັບຄົນຕ່າງປະເທດ",
            "📱 ການຕິດຕໍ່ສຸກເສີນແລະອົງກອນໃຫ້ຄຳປຶກສາ",
            "⚖️ ກົດໝາຍແຮງງານແລະຂັ້ນຕອນການປົກປ້ອງສິດ"
        ],
        "example_title": "ຕົວຢ່າງຄຳຖາມ:",
        "examples": [
            "• ຄ່າແຮງງານຂອງຂ້ອຍຖືກຄ້າງຊຳ",
            "• ຂ້ອຍຖືກໄລ່ອອກຢ່າງບໍ່ຍຸດຕິທຳ",
            "• ຂ້ອຍບາດເຈັບໃນຂະນະເຮັດວຽກ",
            "• ຂ້ອຍປະສົບກັບການລະເມີດທາງເພດໃນສະຖານທີ່ເຮັດວຽກ",
            "• ຂ້ອຍປະສົບກັບການຮຸກຮານຫຼືການລະເມີດທາງເພດ",
            "• ການປະກັນໄພໃດທີ່ມີສຳລັບຄົນຕ່າງປະເທດ?",
            "• ເບີໂທລະສັບໃດທີ່ຂ້ອຍຄວນຮູ້ໃນເກົາຫຼີ?"
        ],
        "input_hint": "ຂຽນຄຳຖາມການປົກປ້ອງສິດຂອງທ່ານຂ້າງລຸ່ມ! 💬"
    },
    "mn": {
        "title": "Гадаад хөдөлмөрчдийн эрхийн хамгаалалтын заавар",
        "info": "Та дараах эрхийн хамгаалалтын сэдвүүдийн талаар асуулт тавьж болно:",
        "items": [
            "💰 Цалингийн хойшлуулалт ба төлбөр",
            "🚫 Шударга бус халах ба халах мэдэгдэл",
            "🏥 Аж үйлдвэрийн осол ба ажлын холбоотой гэмтэл",
            "🚨 Ажлын байран дээрх хүйсийн хавчлага ба хүйсийн халдлага",
            "📞 Гадаад хүмүүст зориулсан даатгал ба зөвлөгөө",
            "📱 Яаралтын холбоо ба зөвлөгөөний агентлагууд",
            "⚖️ Хөдөлмөрийн хууль ба эрхийн хамгаалалтын журам"
        ],
        "example_title": "Асуултын жишээ:",
        "examples": [
            "• Миний цалин хойшлогдсон",
            "• Би шударга бус байдлаар халсан",
            "• Би ажил дээр гэмтсэн",
            "• Би ажлын байран дээр хүйсийн хавчлагад өртсөн",
            "• Би хүйсийн халдлага эсвэл хавчлагад өртсөн",
            "• Гадаад хүмүүст ямар даатгал боломжтой вэ?",
            "• Солонгос улсад ямар утасны дугаарыг мэдэх ёстой вэ?"
        ],
        "input_hint": "Доорх эрхийн хамгаалалтын асуултаа бичнэ үү! 💬"
    },
    "my": {
        "title": "နိုင်ငံခြားလုပ်သားများ အခွင့်အရေး ကာကွယ်ရေး လမ်းညွှန်",
        "info": "အောက်ပါ အခွင့်အရေး ကာကွယ်ရေး ခေါင်းစဉ်များအကြောင်း မေးခွန်းများ မေးနိုင်ပါသည်:",
        "items": [
            "💰 လုပ်ခ ကြွေးကြော်ခြင်းနှင့် လုပ်ခ ပေးချေခြင်း",
            "🚫 မတရား ထုတ်ပယ်ခြင်းနှင့် ထုတ်ပယ်ခြင်း အကြောင်းကြားချက်",
            "🏥 စက်မှုလုပ်ငန်း မတော်တဆမှုနှင့် အလုပ်နှင့်ဆိုင်သော ဒဏ်ရာ",
            "🚨 အလုပ်ခွင်တွင် လိင်ပိုင်းဆိုင်ရာ နှောင့်ယှက်မှုနှင့် လိင်ပိုင်းဆိုင်ရာ စော်ကားမှု",
            "📞 နိုင်ငံခြားသားများအတွက် အထူး အာမခံနှင့် အကြံပေးခြင်း",
            "📱 အရေးပေါ် ဆက်သွယ်ရေးနှင့် အကြံပေးခြင်း အေဂျင်စီများ",
            "⚖️ အလုပ်သမား ဥပဒေများနှင့် အခွင့်အရေး ကာကွယ်ရေး လုပ်ငန်းစဉ်"
        ],
        "example_title": "မေးခွန်း ဥပမာများ:",
        "examples": [
            "• ကျွန်ုပ်၏ လုပ်ခ ကြွေးကြော်ခံရသည်",
            "• ကျွန်ုပ် မတရားစွာ ထုတ်ပယ်ခံရသည်",
            "• ကျွန်ုပ် အလုပ်တွင် ဒဏ်ရာရခဲ့သည်",
            "• ကျွန်ုပ် အလုပ်ခွင်တွင် လိင်ပိုင်းဆိုင်ရာ နှောင့်ယှက်မှု ကြုံတွေ့ခဲ့သည်",
            "• ကျွန်ုပ် လိင်ပိုင်းဆိုင်ရာ စော်ကားမှု သို့မဟုတ် နှောင့်ယှက်မှု ခံရသည်",
            "• နိုင်ငံခြားသားများအတွက် မည်သည့် အာမခံ ရရှိနိုင်သနည်း?",
            "• ကိုရီးယားတွင် မည်သည့် ဖုန်းနံပါတ်များ သိထားသင့်သနည်း?"
        ],
        "input_hint": "အောက်တွင် သင့် အခွင့်အရေး ကာကွယ်ရေး မေးခွန်းကို ရေးပါ! 💬"
    },
    "bn": {
        "title": "বিদেশি শ্রমিক অধিকার সুরক্ষা গাইড",
        "info": "আপনি নিম্নলিখিত অধিকার সুরক্ষা বিষয়গুলি সম্পর্কে জিজ্ঞাসা করতে পারেন:",
        "items": [
            "💰 মজুরি বকেয়া এবং মজুরি প্রদান",
            "🚫 অন্যায় বরখাস্ত এবং বরখাস্তের নোটিশ",
            "🏥 শিল্প দুর্ঘটনা এবং কাজ সম্পর্কিত আঘাত",
            "🚨 কর্মক্ষেত্রে যৌন হয়রানি এবং যৌন নিপীড়ন",
            "📞 বিদেশিদের জন্য বিশেষ বীমা এবং পরামর্শ",
            "📱 জরুরি যোগাযোগ এবং পরামর্শ সংস্থা",
            "⚖️ শ্রম আইন এবং অধিকার সুরক্ষা প্রক্রিয়া"
        ],
        "example_title": "প্রশ্নের উদাহরণ:",
        "examples": [
            "• আমার মজুরি বকেয়া রয়েছে",
            "• আমি অন্যায়ভাবে বরখাস্ত হয়েছি",
            "• আমি কাজে আহত হয়েছি",
            "• আমি কর্মক্ষেত্রে যৌন হয়রানির শিকার হয়েছি",
            "• আমি যৌন নিপীড়ন বা হয়রানির শিকার হয়েছি",
            "• বিদেশিদের জন্য কী ধরনের বীমা পাওয়া যায়?",
            "• কোরিয়ায় কোন ফোন নম্বরগুলি জানা উচিত?"
        ],
        "input_hint": "নীচে আপনার অধিকার সুরক্ষা প্রশ্ন লিখুন! 💬"
    },
    "si": {
        "title": "විදේශීය කම්කරුවන්ගේ අයිතිවාසිකම් ආරක්ෂා කිරීමේ මාර්ගෝපදේශය",
        "info": "ඔබට පහත අයිතිවාසිකම් ආරක්ෂා කිරීමේ මාතෘකා ගැන ප්‍රශ්න අසන්න පුළුවන්:",
        "items": [
            "💰 වැටුප් ණය සහ වැටුප් ගෙවීම",
            "🚫 අයුතු ඉවත් කිරීම සහ ඉවත් කිරීමේ දැනුම්දීම",
            "🏥 කර්මාන්ත හානි සහ වැඩ සම්බන්ධ තුවාල",
            "🚨 වැඩ ස්ථානයේ ලිංගික හානි සහ ලිංගික පහර",
            "📞 විදේශීයයින් සඳහා විශේෂ රක්ෂණ සහ උපදේශන",
            "📱 හදිසි සම්බන්ධතා සහ උපදේශන ආයතන",
            "⚖️ ශ්‍රම නීති සහ අයිතිවාසිකම් ආරක්ෂා කිරීමේ ක්‍රියාවලිය"
        ],
        "example_title": "ප්‍රශ්න උදාහරණ:",
        "examples": [
            "• මගේ වැටුප් ණය වෙලා තියෙනවා",
            "• මම අයුතු ලෙස ඉවත් කරනවා",
            "• මම වැඩේදී තුවාල වෙනවා",
            "• මම වැඩ ස්ථානයේ ලිංගික හානි අත්විඳිනවා",
            "• මම ලිංගික පහර හෝ හානි අත්විඳිනවා",
            "• විදේශීයයින් සඳහා කුමන රක්ෂණ තියෙනවාද?",
            "• කොරියාවේ කුමන දුරකථන අංක දැනගන්න ඕනෑද?"
        ],
        "input_hint": "පහත ඔබේ අයිතිවාසිකම් ආරක්ෂා කිරීමේ ප්‍රශ්නය ලියන්න! 💬"
    },
    "km": {
        "title": "មគ្គុទ្ទេសក៍ការការពារសិទ្ធិរបស់កម្មករជាតិផ្សេង",
        "info": "អ្នកអាចសួរអំពីប្រធានបទការពារសិទ្ធិដូចខាងក្រោម:",
        "items": [
            "💰 ប្រាក់ខែជំពាក់និងការទូទាត់ប្រាក់ខែ",
            "🚫 ការដកចេញដោយមិនយុត្តិធម៌និងការជូនដំណឹងដកចេញ",
            "🏥 គ្រោះថ្នាក់ការងារនិងការរបួសដែលពាក់ព័ន្ធនឹងការងារ",
            "🚨 ការរំលោភផ្លូវភេទនិងការវាយប្រហារផ្លូវភេទនៅកន្លែងធ្វើការ",
            "📞 ការធានារ៉ាប់រងនិងការណែនាំសម្រាប់ជនជាតិផ្សេង",
            "📱 ការទាក់ទងអាសន្ននិងអង្គការណែនាំ",
            "⚖️ ច្បាប់ការងារនិងនីតិវិធីការពារសិទ្ធិ"
        ],
        "example_title": "ឧទាហរណ៍សំណួរ:",
        "examples": [
            "• ប្រាក់ខែរបស់ខ្ញុំត្រូវបានជំពាក់",
            "• ខ្ញុំត្រូវបានដកចេញដោយមិនយុត្តិធម៌",
            "• ខ្ញុំបានរបួសក្នុងពេលធ្វើការ",
            "• ខ្ញុំបានជួបការរំលោភផ្លូវភេទនៅកន្លែងធ្វើការ",
            "• ខ្ញុំបានជួបការវាយប្រហារឬរំលោភផ្លូវភេទ",
            "• ការធានារ៉ាប់រងអ្វីដែលមានសម្រាប់ជនជាតិផ្សេង?",
            "• លេខទូរស័ព្ទអ្វីដែលខ្ញុំគួរដឹងនៅកូរ៉េ?"
        ],
        "input_hint": "សូមសរសេរសំណួរការពារសិទ្ធិរបស់អ្នកខាងក្រោម! 💬"
    },
    "ky": {
        "title": "Чет эл жумушчуларынын укуктарын коргоо боюнча колдонмо",
        "info": "Төмөнкү укук коргоо темалары жөнүндө суроо беришиңиз мүмкүн:",
        "items": [
            "💰 Жумуш акысынын калтырылышы жана төлөнүшү",
            "🚫 Адилетсиз жумуштан келтирилиши жана келтирилиш жарыясы",
            "🏥 Өнөр жай кырсыгы жана жумуш менен байланыштуу жаракат",
            "🚨 Жумуш орундундагы жыныстык зомбулук жана жыныстык кол салуу",
            "📞 Чет элдиктер үчүн атайын камсыздандыруу жана кеңеш",
            "📱 Оор кырдаал байланышы жана кеңеш берүү мекемелери",
            "⚖️ Эмгек мыйзамдары жана укук коргоо процедурасы"
        ],
        "example_title": "Суроо мисалдары:",
        "examples": [
            "• Менинг жумуш акысым калтырылган",
            "• Мен адилетсиз түрдө жумуштан келтирилдим",
            "• Мен жумушта жаракат алдым",
            "• Мен жумуш орундунда жыныстык зомбулукка дуушар болдум",
            "• Мен жыныстык кол салуу же зомбулукка дуушар болдум",
            "• Чет элдиктер үчүн кандай камсыздандыруу бар?",
            "• Кореяда кайсы телефон номерилерин билишим керек?"
        ],
        "input_hint": "Төмөнкү укук коргоо сурооңузду жазыңыз! 💬"
    },
    "ur": {
        "title": "غیر ملکی مزدوروں کے حقوق کی حفاظت کی گائیڈ",
        "info": "آپ مندرجہ ذیل حقوق کی حفاظت کے موضوعات کے بارے میں پوچھ سکتے ہیں:",
        "items": [
            "💰 تنخواہ کی بکائی اور ادائیگی",
            "🚫 ناانصافی برطرفی اور برطرفی کی نوٹس",
            "🏥 صنعتی حادثات اور کام سے متعلق چوٹ",
            "🚨 کام کی جگہ پر جنسی ہراسانی اور جنسی حملہ",
            "📞 غیر ملکیوں کے لیے خصوصی انشورنس اور مشاورت",
            "📱 ہنگامی رابطے اور مشاورت کی ایجنسیاں",
            "⚖️ مزدوری کے قوانین اور حقوق کی حفاظت کے طریقہ کار"
        ],
        "example_title": "سوالات کی مثالیں:",
        "examples": [
            "• میری تنخواہ روک لی گئی ہے",
            "• مجھے ناانصافی سے برطرف کر دیا گیا",
            "• مجھے کام کے دوران چوٹ لگی",
            "• مجھے کام کی جگہ پر جنسی ہراسانی کا سامنا ہوا",
            "• مجھے جنسی حملہ یا ہراسانی کا سامنا ہوا",
            "• غیر ملکیوں کے لیے کیا انشورنس دستیاب ہے؟",
            "• کوریا میں کون سے فون نمبر جاننے چاہئیں؟"
        ],
        "input_hint": "ذیل میں اپنا حقوق کی حفاظت کا سوال لکھیں! 💬"
    },
    "tl": {
        "title": "Gabay sa Buhay sa Korea para sa Mga Pamilyang Multikultural",
        "info": "Maaari kang magtanong tungkol sa mga sumusunod na paksa:",
        "items": [
            "🏥 Paano gumamit ng mga ospital at parmasya",
            "🏦 Paano gumamit ng mga bangko, post office, opisina ng gobyerno",
            "🚌 Paano gumamit ng public transport (bus, subway, tren)",
            "🚗 Lisensya ng driver, pribadong sasakyan, taxi",
            "🏠 Paghahanap ng bahay",
            "📱 Paggamit ng mobile phone",
            "🗑️ Paano magtapon ng basura (volume-based, recycling)",
            "🆔 Pag-rehistro ng dayuhan, paghababa ng pananatili"
        ],
        "example_title": "Mga halimbawa ng tanong:",
        "examples": [
            "• Saan ako pupunta para mag-rehistro bilang dayuhan?",
            "• Ang aking panahon ng pananatili ay tatlong buwan na lang, paano ko ito palawihin?",
            "• Paano ginagamit ng mga dayuhan ang mga mobile phone?",
            "• Ano ang jeonse (bahay na nakabatay sa deposito)?",
            "• Ano ang real estate agency?",
            "• Paano ako magsusulat ng kontrata ng bahay?",
            "• Ano ang proseso para makakuha ng Korean driver's license?",
            "• Saan ako bibili ng mga basurahan?",
            "• Paano ako magtatapon ng basura?",
            "• May sakit ako, ano ang dapat kong gawin?",
            "• Ano ang health insurance card na kailangan para sa mga ospital?",
            "• Iba ba ang oriental medicine sa mga regular na ospital?",
            "• Paano kung wala akong reseta?",
            "• Paano ako magbubukas ng bank account?",
            "• Paano ako magpapadala ng mga bagay sa ibang bansa?",
            "• Ano ang mga 24-hour call center na numero?",
            "• Ano ang mga emergency number?",
            "• Paano ako matututo ng Korean?"
        ],
        "input_hint": "I-type ang inyong tanong sa ibaba! 💬"
    }
}

# 언어별 마이크 안내 메시지
MIC_GUIDE_TEXTS = {
    "ko": "키보드의 마이크 버튼을 눌러 음성 입력을 사용하세요!",
    "en": "Tap the microphone button on your keyboard to use voice input!",
    "ja": "キーボードのマイクボタンを押して音声入力を使ってください！",
    "zh": "请点击键盘上的麦克风按钮进行语音输入！",
    "zh-TW": "請點擊鍵盤上的麥克風按鈕進行語音輸入！",
    "id": "Tekan tombol mikrofon di keyboard untuk menggunakan input suara!",
    "vi": "Nhấn nút micro trên bàn phím để nhập bằng giọng nói!",
    "fr": "Appuyez sur le bouton micro du clavier pour utiliser la saisie vocale !",
    "de": "Tippen Sie auf die Mikrofontaste Ihrer Tastatur, um die Spracheingabe zu verwenden!",
    "th": "แตะปุ่มไมโครโฟนบนแป้นพิมพ์เพื่อใช้การป้อนด้วยเสียง!"
}

# 외국인 근로자 권리구제 RAG 가이드 텍스트
FOREIGN_WORKER_GUIDE_TEXTS = {
    "ko": {
        "title": "외국인 근로자 권리구제 안내",
        "info": "다음과 같은 권리구제 관련 정보를 질문할 수 있습니다:",
        "items": [
            "💰 임금 체불 및 임금 지급",
            "🚫 부당해고 및 해고 예고",
            "🏥 산업재해 및 업무상 재해",
            "🚨 직장 내 성희롱 및 성폭력",
            "📞 외국인 전용 보험 및 상담",
            "📱 긴급 연락처 및 상담 기관",
            "⚖️ 노동법 및 권리구제 절차"
        ],
        "example_title": "질문 예시:",
        "examples": [
            "• 받아야 할 임금이 체불 되었어요",
            "• 부당하게 해고 되었어요",
            "• 일을 하다가 다쳤어요",
            "• 직장 내 성희롱을 당했어요",
            "• 성폭력이나 성추행을 당했어요",
            "• 외국인 전용보험은 어떤게 있나요?",
            "• 한국 체류시 꼭 알아둘 전화번호는요?"
        ],
        "input_hint": "권리구제 관련 질문을 입력해보세요! 💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "장마철 건설현장 안전점검표", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "온열질환 예방조치", "type": "onyul"}
        ]
    },
    "en": {
        "title": "Foreign Worker Rights Protection Guide",
        "info": "You can ask about the following rights protection topics:",
        "items": [
            "💰 Wage arrears and payment",
            "🚫 Unfair dismissal and dismissal notice",
            "🏥 Industrial accidents and work-related injuries",
            "🚨 Workplace sexual harassment and assault",
            "📞 Foreigner-only insurance and counseling",
            "📱 Emergency contacts and counseling agencies",
            "⚖️ Labor laws and rights protection procedures"
        ],
        "example_title": "Example questions:",
        "examples": [
            "• My wages have been withheld",
            "• I was unfairly dismissed",
            "• I got injured at work",
            "• I experienced sexual harassment at work",
            "• I was sexually assaulted or harassed",
            "• What insurance is available for foreigners?",
            "• What phone numbers should I know in Korea?"
        ],
        "input_hint": "Enter your rights protection question below! 💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "Rainy Season Construction Site Safety Checklist", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "Heat-Related Illness Prevention", "type": "onyul"}
        ]
    },
    "vi": {
        "title": "Hướng dẫn bảo vệ quyền lợi người lao động nước ngoài",
        "info": "Bạn có thể hỏi về các chủ đề bảo vệ quyền lợi sau:",
        "items": [
            "💰 Nợ lương và thanh toán lương",
            "🚫 Sa thải bất công và thông báo sa thải",
            "🏥 Tai nạn lao động và thương tích liên quan đến công việc",
            "🚨 Quấy rối tình dục và tấn công tình dục tại nơi làm việc",
            "📞 Bảo hiểm và tư vấn dành riêng cho người nước ngoài",
            "📱 Liên lạc khẩn cấp và cơ quan tư vấn",
            "⚖️ Luật lao động và thủ tục bảo vệ quyền lợi"
        ],
        "example_title": "Ví dụ câu hỏi:",
        "examples": [
            "• Lương của tôi bị nợ",
            "• Tôi bị sa thải bất công",
            "• Tôi bị thương tại nơi làm việc",
            "• Tôi bị quấy rối tình dục tại nơi làm việc",
            "• Tôi bị tấn công hoặc quấy rối tình dục",
            "• Bảo hiểm nào có sẵn cho người nước ngoài?",
            "• Số điện thoại nào tôi nên biết ở Hàn Quốc?"
        ],
        "input_hint": "Nhập câu hỏi bảo vệ quyền lợi của bạn bên dưới! 💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "Danh sách kiểm tra an toàn công trường mùa mưa", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "Biện pháp phòng ngừa bệnh do nắng nóng", "type": "onyul"}
        ]
    },
    "ja": {
        "title": "外国人労働者権利保護ガイド",
        "info": "以下の権利保護に関するトピックについて質問できます:",
        "items": [
            "💰 賃金未払いと支払い",
            "🚫 不当解雇と解雇予告",
            "🏥 産業災害と業務上の災害",
            "🚨 職場でのセクハラと性的暴行",
            "📞 外国人専用保険とカウンセリング",
            "📱 緊急連絡先と相談機関",
            "⚖️ 労働法と権利保護手続き"
        ],
        "example_title": "質問例:",
        "examples": [
            "• 給料が未払いになっています",
            "• 不当に解雇されました",
            "• 仕事中に怪我をしました",
            "• 職場でセクハラを受けました",
            "• 性的暴行や性的嫌がらせを受けました",
            "• 外国人専用保険は何がありますか？",
            "• 韓国滞在中に知っておくべき電話番号は？"
        ],
        "input_hint": "権利保護に関する質問を入力してください！💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "梅雨期建設現場安全点検表", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "熱中症予防措置", "type": "onyul"}
        ]
    },
    "zh": {
        "title": "外籍劳工权益保护指南",
        "info": "您可以询问以下权益保护主题:",
        "items": [
            "💰 工资拖欠和支付",
            "🚫 不当解雇和解雇通知",
            "🏥 工伤和工作相关伤害",
            "🚨 职场性骚扰和性侵犯",
            "📞 外国人专用保险和咨询",
            "📱 紧急联系方式和咨询机构",
            "⚖️ 劳动法和权益保护程序"
        ],
        "example_title": "问题示例:",
        "examples": [
            "• 我的工资被拖欠了",
            "• 我被不当解雇了",
            "• 我在工作中受伤了",
            "• 我在职场遭遇性骚扰",
            "• 我遭遇性侵犯或性骚扰",
            "• 外国人有什么保险？",
            "• 在韩国应该知道哪些电话号码？"
        ],
        "input_hint": "请在下方输入您的权益保护问题！💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "雨季建筑工地安全检查表", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "热相关疾病预防措施", "type": "onyul"}
        ]
    },
    "zh-TW": {
        "title": "外籍勞工權益保護指南",
        "info": "您可以詢問以下權益保護主題:",
        "items": [
            "💰 工資拖欠和支付",
            "🚫 不當解僱和解僱通知",
            "🏥 工傷和工作相關傷害",
            "🚨 職場性騷擾和性侵犯",
            "📞 外國人專用保險和諮詢",
            "📱 緊急聯繫方式和諮詢機構",
            "⚖️ 勞動法和權益保護程序"
        ],
        "example_title": "問題範例:",
        "examples": [
            "• 我的工資被拖欠了",
            "• 我被不當解僱了",
            "• 我在工作中受傷了",
            "• 我在職場遭遇性騷擾",
            "• 我遭遇性侵犯或性騷擾",
            "• 外國人有什麽保險？",
            "• 在韓國應該知道哪些電話號碼？"
        ],
        "input_hint": "請在下方輸入您的權益保護問題！💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "雨季建築工地安全檢查表", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "熱相關疾病預防措施", "type": "onyul"}
        ]
    },
    "id": {
        "title": "Panduan Perlindungan Hak Pekerja Asing",
        "info": "Anda dapat menanyakan topik perlindungan hak berikut:",
        "items": [
            "💰 Tunggakan gaji dan pembayaran gaji",
            "🚫 Pemecatan tidak adil dan pemberitahuan pemecatan",
            "🏥 Kecelakaan kerja dan cedera terkait pekerjaan",
            "🚨 Pelecehan seksual dan serangan seksual di tempat kerja",
            "📞 Asuransi dan konseling khusus warga asing",
            "📱 Kontak darurat dan lembaga konseling",
            "⚖️ Undang-undang ketenagakerjaan dan prosedur perlindungan hak"
        ],
        "example_title": "Contoh pertanyaan:",
        "examples": [
            "• Gaji saya ditahan",
            "• Saya dipecat secara tidak adil",
            "• Saya terluka saat bekerja",
            "• Saya mengalami pelecehan seksual di tempat kerja",
            "• Saya mengalami serangan atau pelecehan seksual",
            "• Asuransi apa yang tersedia untuk warga asing?",
            "• Nomor telepon apa yang harus saya ketahui di Korea?"
        ],
        "input_hint": "Masukkan pertanyaan perlindungan hak Anda di bawah ini! 💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "Daftar Periksa Keselamatan Lokasi Konstruksi Musim Hujan", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "Pencegahan Penyakit Terkait Panas", "type": "onyul"}
        ]
    },
    "th": {
        "title": "คู่มือการคุ้มครองสิทธิแรงงานต่างชาติ",
        "info": "คุณสามารถถามเกี่ยวกับหัวข้อการคุ้มครองสิทธิ์ต่อไปนี้:",
        "items": [
            "💰 ค้างชำระค่าจ้างและการจ่ายเงินเดือน",
            "🚫 การเลิกจ้างที่ไม่เป็นธรรมและการแจ้งเลิกจ้าง",
            "🏥 อุบัติเหตุจากการทำงานและการบาดเจ็บที่เกี่ยวข้องกับงาน",
            "🚨 การล่วงละเมิดทางเพศและการล่วงละเมิดทางเพศในที่ทำงาน",
            "📞 ประกันและบริการให้คำปรึกษาสำหรับชาวต่างชาติ",
            "📱 เบอร์ติดต่อฉุกเฉินและหน่วยงานให้คำปรึกษา",
            "⚖️ กฎหมายแรงงานและขั้นตอนการคุ้มครองสิทธิ์"
        ],
        "example_title": "ตัวอย่างคำถาม:",
        "examples": [
            "• เงินเดือนของฉันถูกค้างชำระ",
            "• ฉันถูกเลิกจ้างอย่างไม่เป็นธรรม",
            "• ฉันได้รับบาดเจ็บขณะทำงาน",
            "• ฉันประสบกับการล่วงละเมิดทางเพศในที่ทำงาน",
            "• ฉันประสบกับการล่วงละเมิดหรือคุกคามทางเพศ",
            "• ประกันอะไรที่มีสำหรับชาวต่างชาติ?",
            "• เบอร์โทรศัพท์อะไรที่ฉันควรรู้ในเกาหลี?"
        ],
        "input_hint": "ป้อนคำถามการคุ้มครองสิทธิ์ของคุณด้านล่าง! 💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "รายการตรวจสอบความปลอดภัยไซต์ก่อสร้างฤดูฝน", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "มาตรการป้องกันโรคจากความร้อน", "type": "onyul"}
        ]
    },
    "fr": {
        "title": "Guide de protection des droits des travailleurs étrangers",
        "info": "Vous pouvez poser des questions sur les sujets de protection des droits suivants:",
        "items": [
            "💰 Arriérés de salaire et paiement des salaires",
            "🚫 Licenciement abusif et préavis de licenciement",
            "🏥 Accidents du travail et blessures liées au travail",
            "🚨 Harcèlement sexuel et agression sexuelle sur le lieu de travail",
            "📞 Assurance et conseil réservés aux étrangers",
            "📱 Contacts d'urgence et agences de conseil",
            "⚖️ Lois du travail et procédures de protection des droits"
        ],
        "example_title": "Exemples de questions:",
        "examples": [
            "• Mon salaire a été retenu",
            "• J'ai été licencié injustement",
            "• Je me suis blessé au travail",
            "• J'ai subi du harcèlement sexuel au travail",
            "• J'ai subi une agression ou du harcèlement sexuel",
            "• Quelle assurance est disponible pour les étrangers?",
            "• Quels numéros de téléphone dois-je connaître en Corée?"
        ],
        "input_hint": "Entrez votre question de protection des droits ci-dessous! 💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "Liste de contrôle de sécurité du chantier de construction en saison des pluies", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "Mesures de prévention des maladies liées à la chaleur", "type": "onyul"}
        ]
    },
    "de": {
        "title": "Leitfaden zum Schutz der Rechte ausländischer Arbeitnehmer",
        "info": "Sie können Fragen zu folgenden Themen des Rechtsschutzes stellen:",
        "items": [
            "💰 Lohnrückstände und Lohnzahlung",
            "🚫 Unfaire Kündigung und Kündigungsfrist",
            "🏥 Arbeitsunfälle und arbeitsbedingte Verletzungen",
            "🚨 Sexuelle Belästigung und sexuelle Übergriffe am Arbeitsplatz",
            "📞 Ausländer-spezifische Versicherung und Beratung",
            "📱 Notfallkontakte und Beratungsstellen",
            "⚖️ Arbeitsgesetze und Rechtsschutzverfahren"
        ],
        "example_title": "Beispielfragen:",
        "examples": [
            "• Mein Lohn wurde einbehalten",
            "• Ich wurde unfair gekündigt",
            "• Ich habe mich bei der Arbeit verletzt",
            "• Ich habe sexuelle Belästigung am Arbeitsplatz erlebt",
            "• Ich habe sexuelle Übergriffe oder Belästigung erlebt",
            "• Welche Versicherung ist für Ausländer verfügbar?",
            "• Welche Telefonnummern sollte ich in Korea kennen?"
        ],
        "input_hint": "Geben Sie Ihre Rechtsschutzfrage unten ein! 💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "Sicherheitscheckliste für Baustellen in der Regenzeit", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "Maßnahmen zur Prävention hitzebedingter Krankheiten", "type": "onyul"}
        ]
    },
    "tl": {
        "title": "Gabay sa Proteksyon ng Karapatan ng Dayuhang Manggagawa",
        "info": "Maaari kang magtanong tungkol sa mga sumusunod na paksa ng proteksyon ng karapatan:",
        "items": [
            "💰 Hindi nabayad na sahod at pagbabayad",
            "🚫 Hindi makatarungang pagtanggal sa trabaho at abiso ng pagtanggal",
            "🏥 Aksidente sa trabaho at mga pinsalang may kaugnayan sa trabaho",
            "🚨 Sexual harassment at sexual assault sa lugar ng trabaho",
            "📞 Insurance at counseling para sa mga dayuhan",
            "📱 Emergency contacts at mga ahensyang nagbibigay ng payo",
            "⚖️ Batas sa paggawa at mga pamamaraan sa proteksyon ng karapatan"
        ],
        "example_title": "Mga halimbawa ng tanong:",
        "examples": [
            "• Hindi nabayad ang aking sahod",
            "• Ako ay hindi makatarungang tinanggal sa trabaho",
            "• Nasaktan ako habang nagtatrabaho",
            "• Nakaranas ako ng sexual harassment sa trabaho",
            "• Nakaranas ako ng sexual assault o harassment",
            "• Anong insurance ang available para sa mga dayuhan?",
            "• Anong mga numero ng telepono ang dapat kong malaman sa Korea?"
        ],
        "input_hint": "Ilagay ang inyong tanong tungkol sa proteksyon ng karapatan sa ibaba! 💬",
        "safety_buttons": [
            {"emoji": "☔", "text": "Checklist ng Kaligtasan sa Construction Site ng Tag-ulan", "type": "jangmachul"},
            {"emoji": "🌡️", "text": "Mga Pamamaraan sa Pag-iwas sa Sakit dahil sa Init", "type": "onyul"}
        ]
    }
}

# 안전점검표 버튼 클릭시 입력될 텍스트 정의
SAFETY_BUTTON_TEXTS = {
    "ko": {
        "jangmachul": "장마철 건설 현장 자율안전 점검표",
        "onyul": "온열질환 예방조치"
    },
    "en": {
        "jangmachul": "Rainy Season Construction Site Safety Checklist",
        "onyul": "Heat-Related Illness Prevention Measures"
    },
    "vi": {
        "jangmachul": "Danh sách kiểm tra an toàn công trường mùa mưa",
        "onyul": "Biện pháp phòng ngừa bệnh do nắng nóng"
    },
    "ja": {
        "jangmachul": "梅雨期建設現場安全点検表",
        "onyul": "熱中症予防措置"
    },
    "zh": {
        "jangmachul": "雨季建筑工地安全检查表",
        "onyul": "热相关疾病预防措施"
    },
    "zh-TW": {
        "jangmachul": "雨季建築工地安全檢查表",
        "onyul": "熱相關疾病預防措施"
    },
    "id": {
        "jangmachul": "Daftar Periksa Keselamatan Lokasi Konstruksi Musim Hujan",
        "onyul": "Pencegahan Penyakit Terkait Panas"
    },
    "th": {
        "jangmachul": "รายการตรวจสอบความปลอดภัยไซต์ก่อสร้างฤดูฝน",
        "onyul": "มาตรการป้องกันโรคจากความร้อน"
    },
    "fr": {
        "jangmachul": "Liste de contrôle de sécurité du chantier de construction en saison des pluies",
        "onyul": "Mesures de prévention des maladies liées à la chaleur"
    },
    "de": {
        "jangmachul": "Sicherheitscheckliste für Baustellen in der Regenzeit",
        "onyul": "Maßnahmen zur Prävention hitzebedingter Krankheiten"
    },
    "tl": {
        "jangmachul": "Checklist ng Kaligtasan sa Construction Site ng Tag-ulan",
        "onyul": "Mga Pamamaraan sa Pag-iwas sa Sakit dahil sa Init"
    }
}

def transcribe_from_mic(input_box: ft.TextField, page: ft.Page, mic_button: ft.IconButton):
    if IS_SERVER:
        input_box.hint_text = "서버에서는 음성 입력이 지원되지 않습니다."
        page.update()
        return
    import sounddevice as sd
    from scipy.io.wavfile import write
    samplerate = 44100  # Sample rate
    duration = 5  # seconds
    filename = "temp_recording.wav"

    original_hint_text = input_box.hint_text
    try:
        # 1. 녹음 시작 알림
        mic_button.disabled = True
        input_box.hint_text = "녹음 중... (5초)"
        page.update()

        # 2. 녹음
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
        sd.wait()  # Wait until recording is finished

        # 3. 파일로 저장
        write(filename, samplerate, recording)

        # 4. Whisper API로 전송
        input_box.hint_text = "음성 분석 중..."
        page.update()
        with open(filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
              model="whisper-1",
              file=audio_file
            )
        
        # 5. 결과 입력
        input_box.value = transcript.text
        
    except Exception as e:
        input_box.hint_text = f"오류: {e}"
        print(f"Whisper STT 오류: {e}")
    finally:
        # 6. 정리
        input_box.hint_text = original_hint_text
        mic_button.disabled = False
        if os.path.exists(filename):
            os.remove(filename)
        page.update()

# 자주 깨지는 특수문자 자동 치환 함수
def safe_text(text):
    if not text:
        return text
    t = text
    # 마침표/쉼표 유사문자까지 모두 치환
    t = t.replace('·', '•')
    t = t.replace('。', '.')
    t = t.replace('．', '.')
    t = t.replace('｡', '.')
    t = t.replace('﹒', '.')
    t = t.replace('､', ',')
    t = t.replace('，', ',')
    t = t.replace('﹐', ',')
    t = t.replace('﹑', ',')
    t = t.replace('、', ',')
    t = t.replace('.', '.')
    t = t.replace(',', ',')
    # ... 이하 기존 특수문자 치환 ...
    t = t.replace('※', '*')
    t = t.replace('◆', '-')
    t = t.replace('■', '-')
    t = t.replace('●', '•')
    t = t.replace('◎', '○')
    t = t.replace('★', '*')
    t = t.replace('☆', '*')
    t = t.replace('▶', '>')
    t = t.replace('▷', '>')
    t = t.replace('◀', '<')
    t = t.replace('◁', '<')
    t = t.replace('→', '→')
    t = t.replace('←', '←')
    t = t.replace('↑', '↑')
    t = t.replace('↓', '↓')
    t = t.replace('∼', '~')
    t = t.replace('∑', 'Σ')
    t = t.replace('∏', 'Π')
    t = t.replace('∫', '∫')
    t = t.replace('√', '√')
    t = t.replace('∂', '∂')
    t = t.replace('∞', '∞')
    t = t.replace('≒', '≈')
    t = t.replace('≠', '≠')
    t = t.replace('≡', '=')
    t = t.replace('≪', '<<')
    t = t.replace('≫', '>>')
    t = t.replace('∵', 'because')
    t = t.replace('∴', 'therefore')
    t = t.replace('∇', '∇')
    t = t.replace('∈', '∈')
    t = t.replace('∋', '∋')
    t = t.replace('⊂', '⊂')
    t = t.replace('⊃', '⊃')
    t = t.replace('⊆', '⊆')
    t = t.replace('⊇', '⊇')
    t = t.replace('⊕', '+')
    t = t.replace('⊙', '○')
    t = t.replace('⊥', '⊥')
    t = t.replace('⌒', '~')
    t = t.replace('∠', '∠')
    t = t.replace('∟', '∟')
    t = t.replace('∩', '∩')
    t = t.replace('∪', '∪')
    t = t.replace('∧', '∧')
    t = t.replace('∨', '∨')
    t = t.replace('∃', '∃')
    t = t.replace('∀', '∀')
    t = t.replace('∅', '∅')
    t = t.replace('∝', '∝')
    t = t.replace('∵', 'because')
    t = t.replace('∴', 'therefore')
    t = t.replace('‰', '‰')
    t = t.replace('℉', '°F')
    t = t.replace('℃', '°C')
    t = t.replace('㎏', 'kg')
    t = t.replace('㎏', 'kg')
    t = t.replace('㎜', 'mm')
    t = t.replace('㎝', 'cm')
    t = t.replace('㎞', 'km')
    t = t.replace('㎖', 'ml')
    t = t.replace('㎗', 'dl')
    t = t.replace('㎍', 'μg')
    t = t.replace('㎚', 'nm')
    t = t.replace('㎛', 'μm')
    t = t.replace('㎧', 'm/s')
    t = t.replace('㎨', 'm/s²')
    t = t.replace('㎰', 'pH')
    t = t.replace('㎲', 'μs')
    t = t.replace('㎳', 'ms')
    t = t.replace('㎴', 'pF')
    t = t.replace('㎵', 'nF')
    t = t.replace('㎶', 'μV')
    t = t.replace('㎷', 'mV')
    t = t.replace('㎸', 'kV')
    t = t.replace('㎹', 'MV')
    t = t.replace('㎽', 'mW')
    t = t.replace('㎾', 'kW')
    t = t.replace('㎿', 'MW')
    t = t.replace('㏄', 'cc')
    t = t.replace('㏅', 'cd')
    t = t.replace('㏈', 'dB')
    t = t.replace('㏊', 'ha')
    t = t.replace('㏎', 'kn')
    t = t.replace('㏏', 'kt')
    t = t.replace('㏐', 'lm')
    t = t.replace('㏑', 'ln')
    t = t.replace('㏒', 'log')
    t = t.replace('㏓', 'lb')
    t = t.replace('㏔', 'p.m.')
    t = t.replace('㏕', 'rpm')
    t = t.replace('㏖', 'MBq')
    t = t.replace('㏗', 'pH')
    t = t.replace('㏘', 'sr')
    t = t.replace('㏙', 'Sv')
    t = t.replace('㏚', 'Wb')
    t = t.replace('㏛', 'rad')
    t = t.replace('㏜', 'Gy')
    t = t.replace('㏝', 'Pa')
    t = t.replace('㏞', 'ppm')
    t = t.replace('㏟', 'ppb')
    t = t.replace('㏠', 'ps')
    t = t.replace('㏡', 'a')
    t = t.replace('㏢', 'bar')
    t = t.replace('㏣', 'G')
    t = t.replace('㏤', 'Gal')
    t = t.replace('㏥', 'Bq')
    t = t.replace('㏦', 'C')
    t = t.replace('㏧', 'F')
    t = t.replace('㏨', 'H')
    t = t.replace('㏩', 'Hz')
    t = t.replace('㏪', 'J')
    t = t.replace('㏫', 'K')
    t = t.replace('㏬', 'L')
    t = t.replace('㏭', 'mol')
    t = t.replace('㏮', 'N')
    t = t.replace('㏯', 'Oe')
    t = t.replace('㏰', 'P')
    t = t.replace('㏱', 'Pa')
    t = t.replace('㏲', 'rad')
    t = t.replace('㏳', 'S')
    t = t.replace('㏴', 'St')
    t = t.replace('㏵', 'T')
    t = t.replace('㏶', 'V')
    t = t.replace('㏷', 'W')
    t = t.replace('㏸', 'Ω')
    t = t.replace('㏹', 'Å')
    t = t.replace('㏺', '㎖')
    t = t.replace('㏻', '㎗')
    t = t.replace('㏼', '㎍')
    t = t.replace('㏽', '㎚')
    t = t.replace('㏾', '㎛')
    return t

def ChatRoomPage(page, room_id, room_title, user_lang, target_lang, on_back=None, on_share=None, custom_translate_message=None, firebase_available=True, is_foreign_worker_rag=False, is_busan_food_rag=False):
    # 화면 크기에 따른 반응형 설정
    is_mobile = page.width < 600
    is_tablet = 600 <= page.width < 1024
    
    # 반응형 크기 계산
    title_size = 18 if is_mobile else 22
    nickname_size = 10 if is_mobile else 12
    message_size = 14 if is_mobile else 16
    translated_size = 10 if is_mobile else 12
    input_height = 45 if is_mobile else 50
    bubble_padding = 8 if is_mobile else 12
    header_padding = 12 if is_mobile else 16
    
    # --- 추방 사용자 체크 ---
    current_nickname = page.session.get('nickname') or ''
    if current_nickname and is_user_kicked(current_nickname, room_id, firebase_available):
        # 추방된 사용자라면 접근 차단
        return ft.View(
            f"/kicked/{room_id}",
            [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.NO_ACCOUNTS, size=100, color=ft.Colors.RED_400),
                        ft.Text("채팅방 접근 금지", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600),
                        ft.Text("방장에 의해 이 채팅방에서 추방되었습니다.", size=16, text_align=ft.TextAlign.CENTER),
                        ft.Text("더 이상 이 채팅방에 참여할 수 없습니다.", size=14, color=ft.Colors.GREY_600),
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            "뒤로가기",
                            on_click=lambda e: on_back(e) if on_back else None,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30,
                    alignment=ft.alignment.center,
                    expand=True
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    # --- 상태 및 컨트롤 초기화 ---
    chat_messages = ft.Column(
        auto_scroll=True,
        spacing=10 if is_mobile else 15,
        expand=True,
    )
    current_target_lang = [target_lang]
    is_korean = user_lang == "ko"
    # RAG 채팅방인지 확인
    is_rag_room = custom_translate_message is not None
    # 언어별 입력창 안내문구
    RAG_INPUT_HINTS = {
        "ko": "한국생활에 대해 질문하세요",
        "en": "Ask about life in Korea",
        "vi": "Hãy hỏi về cuộc sống ở Hàn Quốc",
        "ja": "韓国での生活について質問してください",
        "zh": "请咨询有关在韩国生活的问题",
        "fr": "Posez des questions sur la vie en Corée",
        "de": "Stellen Sie Fragen zum Leben in Korea",
        "th": "สอบถามเกี่ยวกับการใช้ชีวิตในเกาหลีได้เลย",
        "zh-TW": "請詢問有關在韓國生活的問題",
        "id": "Tanyakan tentang kehidupan di Korea",
        "tl": "Magtanong tungkol sa buhay sa Korea",
    }
    input_hint = RAG_INPUT_HINTS.get(user_lang, RAG_INPUT_HINTS["en"]) if is_rag_room else {
        "ko": "메시지 입력",
        "en": "Type a message",
        "vi": "Nhập tin nhắn",
        "ja": "メッセージを入力",
        "zh": "输入消息",
        "fr": "Entrez un message",
        "de": "Nachricht eingeben",
        "th": "พิมพ์ข้อความ",
        "zh-TW": "輸入訊息",
        "id": "Ketik pesan",
        "tl": "Mag-type ng mensahe",
    }.get(user_lang, "Type a message")
    input_box = ft.TextField(
        hint_text=input_hint, 
        expand=True, 
        height=input_height
    )
    if is_rag_room:
        if is_busan_food_rag or room_id == "busan_food_search_rag":
            # 부산 맛집 RAG 방에서는 번역 스위치 제거
            translate_switch = None
        elif is_foreign_worker_rag or room_id == "foreign_worker_rights_rag":
            # 외국인 근로자 RAG 방에서는 언어 선택 드롭다운 표시
            translate_switch = None
        else:
            # 일반 RAG 방에서는 번역 스위치 제거
            translate_switch = None
    else:
        switch_label = "번역 ON/OFF" if is_korean else "Translate ON/OFF"
        translate_switch = ft.Switch(label=switch_label, value=True)

    def on_target_lang_change(e):
        current_target_lang[0] = e.control.value

    # 번역 대상 언어 드롭다운 옵션 (국기+영어 국가명)
    target_lang_options = [
        ("ko", "🇰🇷 Korean"),
        ("en", "🇺🇸 English"),
        ("ja", "🇯🇵 Japanese"),
        ("zh", "🇨🇳 Chinese"),
        ("zh-TW", "🇹🇼 Taiwanese"),
        ("id", "🇮🇩 Indonesian"),
        ("tl", "🇵🇭 Tagalog"),
        ("ms", "🇲🇾 Malay"),
        ("ta", "🇮🇳 Tamil"),
        ("fr", "🇫🇷 French"),
        ("de", "🇩🇪 German"),
        ("th", "🇹🇭 Thai"),
        ("vi", "🇻🇳 Vietnamese"),
        ("uz", "🇺🇿 Uzbek"),
        ("ne", "🇳🇵 Nepali"),
        ("tet", "🇹🇱 Tetum"),
        ("lo", "🇱🇦 Lao"),
        ("mn", "🇲🇳 Mongolian"),
        ("my", "🇲🇲 Burmese"),
        ("bn", "🇧🇩 Bengali"),
        ("si", "🇱🇰 Sinhala"),
        ("km", "🇰🇭 Khmer"),
        ("ky", "🇰🇬 Kyrgyz"),
        ("ur", "🇵🇰 Urdu"),
    ]
    # 드롭다운 항상 생성
    target_lang_dropdown = ft.Dropdown(
        value=current_target_lang[0],
        options=[ft.dropdown.Option(key, text) for key, text in target_lang_options],
        width=180 if is_mobile else 220,
        on_change=on_target_lang_change
    )

    # 식당 이름 추출 함수
    def extract_restaurant_names(text):
        """RAG 답변에서 식당 이름들을 JSON 데이터베이스와 매칭하여 추출합니다."""
        import json
        import os
        
        try:
            all_restaurants = []
            
            # 부산의맛(2025).json 파일 로드
            busan_food_path = os.path.join(os.path.dirname(__file__), '..', '부산의맛(2025).json')
            if os.path.exists(busan_food_path):
                with open(busan_food_path, 'r', encoding='utf-8') as f:
                    busan_data = json.load(f)
                
                for district, restaurants in busan_data["부산의 맛 2025"].items():
                    for restaurant in restaurants:
                        korean_name = restaurant["식당이름"]["한글"]
                        english_name = restaurant["식당이름"]["영어"]
                        all_restaurants.append({
                            'korean': korean_name,
                            'english': english_name,
                            'district': district
                        })
            
            # 택슐랭(2025).json 파일 로드
            taek_path = os.path.join(os.path.dirname(__file__), '..', '택슐랭(2025).json')
            if os.path.exists(taek_path):
                with open(taek_path, 'r', encoding='utf-8') as f:
                    taek_data = json.load(f)
                
                for restaurant in taek_data["restaurants"]:
                    korean_name = restaurant["name"]
                    district = restaurant["district"]
                    all_restaurants.append({
                        'korean': korean_name,
                        'english': korean_name,  # 택슐랭은 영어명이 별도로 없으므로
                        'district': district
                    })
            
            # RAG 응답 텍스트에서 언급된 식당들 찾기
            mentioned_restaurants = []
            text_lower = text.lower()
            
            for restaurant in all_restaurants:
                korean_name = restaurant['korean']
                english_name = restaurant['english']
                
                # 한글 이름으로 검색 (부분 매칭)
                if korean_name in text:
                    mentioned_restaurants.append(korean_name)
                # 영어 이름으로 검색 (대소문자 무시)
                elif english_name.lower() in text_lower:
                    mentioned_restaurants.append(korean_name)
                # 한글 이름의 핵심 부분으로 검색 (공백 제거)
                elif korean_name.replace(' ', '') in text.replace(' ', ''):
                    mentioned_restaurants.append(korean_name)
            
            # 중복 제거
            unique_restaurants = list(dict.fromkeys(mentioned_restaurants))
            
            print(f"🍽️ 추출된 식당 이름들: {unique_restaurants}")  # 디버깅용 로그
            return unique_restaurants[:8]  # 최대 8개
            
        except Exception as e:
            print(f"JSON 파일 로드 오류: {e}")
            # 오류 시 기존 정규식 방식으로 폴백
            import re
            simple_pattern = r'([가-힣]{2,15}(?:식당|집|점|관|갈비|찜|탕|카페|베이커리))'
            matches = re.findall(simple_pattern, text)
            return list(set(matches))[:8]

    # Google Maps로 식당 열기 함수
    def open_restaurant_in_maps(restaurant_name):
        """식당을 Google Maps에서 엽니다."""
        try:
            import urllib.parse
            import re
            
            # 외국어 번역이 포함된 경우 한국어 부분만 추출
            # 형식: "한국어이름 (외국어번역)" 또는 "한국어이름(외국어번역)"
            korean_name_match = re.match(r'^([가-힣\s\d]+)[\s]*\([^)]+\)', restaurant_name)
            if korean_name_match:
                korean_name = korean_name_match.group(1).strip()
                search_query = f"{korean_name} 부산"
            else:
                # 한국어만 있는 경우 그대로 사용
                search_query = f"{restaurant_name} 부산"
            
            encoded_query = urllib.parse.quote(search_query)
            
            # 부산 맛집 RAG 방에서는 사용자 언어 사용, 일반 채팅방에서는 대상 언어 사용
            try:
                if is_busan_food_rag or room_id == "busan_food_search_rag":
                    # 부산 맛집: 사용자의 모국어로 지도 표시
                    current_lang = user_lang or 'ko'
                else:
                    # 일반 채팅방: 번역 대상 언어로 지도 표시
                    current_lang = page.session.get('target_language') or target_lang or 'ko'
            except:
                current_lang = user_lang or 'ko'
            
            # 언어별 구글 맵 설정 (부산 맛집용)
            lang_mapping = {
                "ko": {"lang": "ko", "region": "KR", "domain": "maps.google.com"},
                "en": {"lang": "en", "region": "US", "domain": "maps.google.com"},
                "ja": {"lang": "ja", "region": "JP", "domain": "maps.google.co.jp"},
                "zh": {"lang": "ko", "region": "KR", "domain": "maps.google.com"},  # 중국은 한국어 버전
                "tw": {"lang": "zh-TW", "region": "TW", "domain": "maps.google.com.tw"},
                "vi": {"lang": "ko", "region": "KR", "domain": "maps.google.com"},  # 베트남은 한국어 버전
                "th": {"lang": "th", "region": "TH", "domain": "maps.google.co.th"},
                "id": {"lang": "id", "region": "ID", "domain": "maps.google.co.id"},
                "fr": {"lang": "fr", "region": "FR", "domain": "maps.google.fr"},
                "de": {"lang": "de", "region": "DE", "domain": "maps.google.de"},
                "tl": {"lang": "tl", "region": "PH", "domain": "maps.google.com.ph"},
                "ms": {"lang": "ms", "region": "MY", "domain": "maps.google.com.my"},  # 말레이시아
                "pt": {"lang": "pt", "region": "BR", "domain": "maps.google.com.br"},  # 포르투갈어(브라질)
                "es": {"lang": "es", "region": "ES", "domain": "maps.google.es"},  # 스페인어
                "it": {"lang": "it", "region": "IT", "domain": "maps.google.it"},  # 이탈리아어
                "ru": {"lang": "ru", "region": "RU", "domain": "maps.google.ru"},  # 러시아어
                "ar": {"lang": "ar", "region": "SA", "domain": "maps.google.com.sa"},  # 아랍어
                "hi": {"lang": "hi", "region": "IN", "domain": "maps.google.co.in"},  # 힌디어(인도)
                "nl": {"lang": "nl", "region": "NL", "domain": "maps.google.nl"},  # 네덜란드어
                "sv": {"lang": "sv", "region": "SE", "domain": "maps.google.se"},  # 스웨덴어
                "tr": {"lang": "tr", "region": "TR", "domain": "maps.google.com.tr"}  # 터키어
            }
            
            map_config = lang_mapping.get(current_lang, lang_mapping["ko"])
            
            # Google Maps URL 생성
            maps_url = f"https://{map_config['domain']}/maps/search/{encoded_query}?hl={map_config['lang']}&gl={map_config['region']}&ie=UTF8"
            
            print(f"🗺️ [{current_lang}] {restaurant_name} Google Maps: {maps_url}")
            print(f"   도메인: {map_config['domain']}, 언어: {map_config['lang']}, 지역: {map_config['region']}")
            
            # 클라이언트 브라우저에서 새 탭으로 열기 (서버 환경 호환)
            page.launch_url(maps_url)
            
            # 알림 메시지 (snack_bar 사용하지 않고 콘솔 출력)
            print(f"🗺️ {restaurant_name} 위치를 {map_config['domain']}에서 열고 있습니다...")
            
        except Exception as e:
            print(f"Google Maps 열기 오류: {e}")
            print("지도 열기 중 오류가 발생했습니다.")

    # YouTube 검색으로 열기 함수 (장마철 안전점검표용)
    def open_youtube_search(search_keyword):
        """KOSHA YouTube 채널에서 키워드 검색"""
        try:
            import urllib.parse
            
            # URL 인코딩 (한국어 키워드)
            encoded_keyword = urllib.parse.quote(search_keyword)
            youtube_url = f"https://www.youtube.com/@koshamovie/search?query={encoded_keyword}"
            
            print(f"📺 YouTube 검색 키워드: {search_keyword}")
            print(f"📺 YouTube URL: {youtube_url}")
            
            # Google Maps와 동일한 방식으로 URL 열기
            page.launch_url(youtube_url)
            
            print(f"📺 '{search_keyword}' 관련 KOSHA 교육 동영상을 찾고 있습니다...")
            
        except Exception as e:
            print(f"YouTube 열기 오류: {e}")
            print("YouTube 열기 중 오류가 발생했습니다.")

    def create_message_bubble(msg_data, is_me):
        # 닉네임이 '익명'이고 본문/번역문이 모두 비어있으면 말풍선 생성하지 않음
        if msg_data.get('nickname', '') == '익명' and not msg_data.get('text', '').strip() and not msg_data.get('translated', '').strip():
            return None
        is_rag = msg_data.get('nickname', '') == 'RAG'
        
        # RAG 답변은 더 넓은 말풍선 사용
        if is_rag:
            bubble_width = int(page.width * 0.85) if is_mobile else 700
        else:
            bubble_width = int(page.width * 0.5) if is_mobile else 400
            
        base_size = 16 if is_mobile else 18  # 기존보다 2pt 크게
        font_family = "Noto Sans KR, Malgun Gothic, Arial, Apple SD Gothic Neo, sans-serif" if is_rag else None
        # RAG 답변 특수문자 치환
        if is_rag:
            msg_data['text'] = safe_text(msg_data['text'])
            msg_data['translated'] = safe_text(msg_data.get('translated', ''))
        # 질문예시(가이드 메시지)라면 글자 크기 한 단계 키움
        nickname = msg_data.get('nickname', '')
        is_guide = is_rag and msg_data.get('is_guide', False)
        nickname_color = ft.Colors.WHITE if is_me else ft.Colors.BLACK87
        
        # 차단 버튼 (방장이고, 자신의 메시지가 아니고, 시스템/RAG 메시지가 아닐 때만 표시)
        block_button = None
        if not is_me and nickname not in ['시스템', 'RAG', '익명']:
            # 방장 권한 확인
            current_nickname = page.session.get('nickname') or ''
            current_user_id = page.session.get('user_id') or None or None
            if is_room_owner(room_id, current_nickname, current_user_id):
                # 차단과 추방 버튼을 함께 표시
                block_button = ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.BLOCK,
                        icon_color=ft.Colors.ORANGE_400,
                        icon_size=14,
                        tooltip="사용자 차단 (방장 전용)",
                        on_click=lambda e, nickname=nickname: block_user_from_message(nickname)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PERSON_REMOVE,
                        icon_color=ft.Colors.RED_600,
                        icon_size=14,
                        tooltip="사용자 추방 (방장 전용)",
                        on_click=lambda e, nickname=nickname: kick_user_from_message(nickname)
                    )
                ], spacing=0)
        
        controls = [
            ft.Row([
            ft.Text(
                    nickname,
                    size=(base_size - 2) + (2 if is_guide else 0),
                    color=nickname_color,
                    italic=True,
                    font_family=font_family,
                    selectable=True,
                ),
                block_button if block_button else ft.Container()
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN) if block_button else ft.Text(
                nickname,
                size=(base_size - 2) + (2 if is_guide else 0),
                color=nickname_color,
                italic=True,
                font_family=font_family,
                selectable=True,
            ),
            ft.Text(
                msg_data.get('text', '').replace('**', ''),  # ** 마크다운 기호 제거
                size=base_size + (2 if is_guide else 0),
                color=ft.Colors.WHITE if is_me else ft.Colors.BLACK87,
                font_family=font_family,
                selectable=True,
                weight=ft.FontWeight.W_500,  # RAG 답변은 약간 굵게
            ) if is_rag else ft.Text(
                msg_data.get('text', ''),
                size=base_size + (2 if is_guide else 0),
                color=ft.Colors.WHITE if is_me else ft.Colors.BLACK87,
                font_family=font_family,
                selectable=True,
            ),
        ]
        if msg_data.get('translated', ''):
            controls.append(
                ft.Text(
                    msg_data.get('translated', '').replace('**', ''),  # ** 마크다운 기호 제거
                    size=(base_size - 2) + (2 if is_guide else 0),
                    color=ft.Colors.WHITE if is_me else ft.Colors.BLACK87,
                    font_family=font_family,
                    selectable=True,
                    weight=ft.FontWeight.W_500,  # RAG 번역도 약간 굵게
                    italic=True,
                ) if is_rag else ft.Text(
                    msg_data.get('translated', ''),
                    size=(base_size - 2) + (2 if is_guide else 0),
                    color=ft.Colors.WHITE if is_me else ft.Colors.BLACK87,
                    italic=True,
                    font_family=font_family,
                    selectable=True,
                )
            )
        
        # 부산 맛집 RAG 답변인 경우 식당 지도 버튼 추가
        if is_rag and (is_busan_food_rag or room_id == "busan_food_search_rag"):
            text_content = msg_data.get('text', '') + ' ' + msg_data.get('translated', '')
            restaurant_names = extract_restaurant_names(text_content)
            
            if restaurant_names:
                # 지도 버튼들을 담을 컨테이너 추가
                map_buttons = []
                for restaurant_name in restaurant_names:
                    map_button = ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.MAP, size=16),
                            ft.Text(restaurant_name[:15] + "..." if len(restaurant_name) > 15 else restaurant_name, 
                                   size=12, weight=ft.FontWeight.W_400)
                        ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                        on_click=lambda e, name=restaurant_name: open_restaurant_in_maps(name),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_600,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.padding.symmetric(horizontal=8, vertical=4)
                        ),
                        height=32,
                        width=140 if is_mobile else 160
                    )
                    map_buttons.append(map_button)
                
                # 지도 버튼들을 2열로 배치
                if map_buttons:
                    button_rows = []
                    for i in range(0, len(map_buttons), 2):
                        row_buttons = map_buttons[i:i+2]
                        button_rows.append(
                            ft.Row(
                                row_buttons, 
                                spacing=8, 
                                alignment=ft.MainAxisAlignment.START
                            )
                        )
                    
                    # 지도 버튼 섹션 추가
                    controls.append(ft.Container(height=8))  # 구분선
                    controls.append(
                        ft.Text("🗺️ 지도에서 보기", 
                               size=13, 
                               color=ft.Colors.WHITE if is_me else ft.Colors.BLACK87,
                               weight=ft.FontWeight.BOLD,
                               font_family=font_family)
                    )
                    controls.append(ft.Container(height=4))
                    for button_row in button_rows:
                        controls.append(button_row)
        
        # 장마철 안전점검표 YouTube 버튼 처리 (외국인 근로자 RAG에서만)
        if is_rag and (is_foreign_worker_rag or room_id == "foreign_worker_rights_rag"):
            text_content = msg_data.get('text', '') + ' ' + msg_data.get('translated', '')
            if 'YOUTUBE_BUTTON|' in text_content:
                # YouTube 버튼 정보 추출 (형식: YOUTUBE_BUTTON|URL|버튼텍스트|검색키워드)
                button_info = text_content.split('YOUTUBE_BUTTON|')[-1]
                parts = button_info.split('|', 3)
                if len(parts) >= 3:
                    youtube_url = parts[0].strip()
                    button_text = parts[1].strip() if len(parts) > 1 else "📺 관련 동영상 보기"
                    search_keyword = parts[2].strip() if len(parts) > 2 else "장마철 안전"
                    
                    print(f"[DEBUG] YouTube 버튼 정보:")
                    print(f"  URL: {youtube_url}")
                    print(f"  버튼텍스트: {button_text}")
                    print(f"  검색키워드: {search_keyword}")
                    
                    # YouTube 버튼 생성 - Google Maps 방식과 동일
                    youtube_button = ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PLAY_CIRCLE, size=20),
                            ft.Text(button_text, size=14, weight=ft.FontWeight.W_500)
                        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        on_click=lambda e, keyword=search_keyword: open_youtube_search(keyword),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED_600,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.padding.symmetric(horizontal=12, vertical=8)
                        ),
                        height=40,
                        width=280 if is_mobile else 320
                    )
                    
                    # YouTube 버튼 섹션 추가
                    controls.append(ft.Container(height=8))  # 구분선
                    controls.append(youtube_button)
                    
                    # 메시지 텍스트에서 YOUTUBE_BUTTON 태그 제거
                    msg_data['text'] = msg_data['text'].split('YOUTUBE_BUTTON|')[0].strip()
                    if 'translated' in msg_data:
                        msg_data['translated'] = msg_data['translated'].split('YOUTUBE_BUTTON|')[0].strip()
                    
                    # 텍스트 컨트롤 업데이트
                    if len(controls) > 1 and isinstance(controls[1], ft.Text):
                        controls[1] = ft.Text(
                            msg_data.get('text', '').replace('**', ''),
                            size=base_size + (2 if is_guide else 0),
                            color=ft.Colors.WHITE if is_me else ft.Colors.BLACK87,
                            font_family=font_family,
                            selectable=True,
                            weight=ft.FontWeight.W_500,
                        )
        
        # Row로 감싸서 좌/우 정렬
        return ft.Row([
            ft.Container(
                content=ft.Column(controls, spacing=2),
            padding=12,
                bgcolor="#2563EB" if is_me else ft.Colors.GREY_200,
                border_radius=16,
                margin=ft.margin.only(top=6, left=8, right=8),
                width=bubble_width,
                alignment=ft.alignment.top_right if is_me else ft.alignment.top_left,
            )
        ], alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START)

    # --- 시스템 안내 메시지(가운데 정렬) 생성 함수 ---
    def create_system_message_bubble(text):
        return ft.Row([
            ft.Container(
                content=ft.Text(text, size=15 if is_mobile else 17, color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD),
                padding=10,
                bgcolor=ft.Colors.GREY_100,
                border_radius=12,
                alignment=ft.alignment.center,
            )
        ], alignment=ft.MainAxisAlignment.CENTER)

    # --- 입장/퇴장 감지용 유저 세트 ---
    current_users = set()

    # --- Firebase 리스너 콜백 ---
    def on_message(event):
        if not event or not event.data:
            return  # 데이터가 없으면 무시
        
        try:
            data = event.data
            if isinstance(data, str):
                import json
                data = json.loads(data)
            
            # 데이터가 유효한지 확인
            if not isinstance(data, dict):
                print(f"유효하지 않은 메시지 데이터 형식: {type(data)}")
                return
            
            msg_data = {
                'text': data.get('text', ''),
                'nickname': data.get('nickname', '익명'),
                'timestamp': str(data.get('timestamp', '')),
                'translated': data.get('translated', '')
            }
            
            # 차단된 사용자의 메시지는 무시
            if is_user_blocked(msg_data['nickname']):
                print(f"차단된 사용자 {msg_data['nickname']}의 메시지 필터링됨")
                return
            
            # 시스템 메시지면 무조건 가운데 정렬로 append
            if msg_data['nickname'] == '시스템':
                system_bubble = create_system_message_bubble(msg_data['text'])
                if system_bubble:  # None이 아닌 경우만 추가
                    chat_messages.controls.append(system_bubble)
                    page.update()
                return
            
            # 중복 메시지 방지: 최근 5개 메시지의 (nickname, text, timestamp)와 비교 (일반 메시지에만 적용)
            def get_msg_id(msg):
                return f"{msg['nickname']}|{msg['text']}|{msg['timestamp']}"
            new_id = get_msg_id(msg_data)
            for c in chat_messages.controls[-5:]:
                if hasattr(c, 'content') and hasattr(c.content, 'controls'):
                    try:
                        last_nickname = c.content.controls[0].value
                        last_text = c.content.controls[1].value
                        last_timestamp = getattr(c, 'timestamp', None) or ''
                        last_id = f"{last_nickname}|{last_text}|{last_timestamp}"
                        if last_id == new_id:
                            return  # 중복
                    except Exception:
                        continue
            
            # --- 입장/퇴장 감지 및 안내 메시지 ---
            nickname = msg_data['nickname']
            if nickname != '익명' and nickname != 'RAG' and nickname != '시스템':
                # 입장 감지 - 단순히 current_users에 추가만 하고 메시지는 생성하지 않음
                # (입장 메시지는 push_join_system_message()에서 한 번만 처리)
                current_users.add(nickname)
            
            # 메시지 말풍선 생성
            is_me = msg_data['nickname'] == (page.session.get('nickname') or '')
            message_bubble = create_message_bubble(msg_data, is_me)
            
            # message_bubble이 유효한 경우에만 처리
            if message_bubble:
                setattr(message_bubble, 'timestamp', msg_data['timestamp'])
                chat_messages.controls.append(message_bubble)
                page.update()
            else:
                print(f"메시지 버블 생성 실패: {msg_data}")
                
        except Exception as e:
            print(f"메시지 처리 오류: {e}")
            import traceback
            traceback.print_exc()

    # --- 사용자 차단 함수 ---
    def block_user_from_message(nickname):
        """메시지에서 사용자 차단"""
        def confirm_block(e):
            # 로컬 차단 목록에 추가
            BLOCKED_USERS.add(nickname)
            
            # Firebase에 차단 정보 저장
            try:
                db.reference(f'rooms/{room_id}/blocked_users').child(nickname).set({
                    'blocked_at': time.time(),
                    'blocked_by': '방장'
                })
                print(f"사용자 {nickname} 차단됨 (방: {room_id})")
            except Exception as e:
                print(f"차단 정보 저장 오류: {e}")
            
            # 차단 메시지 표시
            block_msg_data = {
                'text': f"🚫 {nickname}님이 차단되었습니다.",
                'nickname': '시스템',
                'timestamp': time.time(),
                'translated': ''
            }
            block_bubble = create_message_bubble(block_msg_data, False)
            if block_bubble:  # None이 아닌 경우만 처리
                setattr(block_bubble, 'timestamp', block_msg_data['timestamp'])
                chat_messages.controls.append(block_bubble)
            page.update()
            
            # 다이얼로그 닫기
            if page.dialog:
                page.dialog.open = False
                page.update()
        
        def cancel_block(e):
            if page.dialog:
                page.dialog.open = False
                page.update()
        
        # 확인 다이얼로그 표시
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("사용자 차단"),
            content=ft.Text(f"{nickname}님을 차단하시겠습니까?\n차단된 사용자의 메시지는 더 이상 표시되지 않습니다."),
            actions=[
                ft.TextButton("취소", on_click=cancel_block),
                ft.TextButton("차단", on_click=confirm_block, style=ft.ButtonStyle(color=ft.Colors.RED))
            ]
        )
        
        page.dialog = confirm_dialog
        confirm_dialog.open = True
        page.update()

    # --- 사용자 추방 함수 ---
    def kick_user_from_message(nickname):
        """메시지에서 사용자 추방"""
        def confirm_kick(e):
            try:
                # Firebase에 추방 정보 저장
                if firebase_available:
                    db.reference(f'rooms/{room_id}/kicked_users').child(nickname).set({
                        'kicked_at': time.time(),
                        'kicked_by': '방장'
                    })
                    print(f"사용자 {nickname} 추방됨 (방: {room_id})")
                else:
                    print(f"추방 정보 저장 오류: Firebase 사용 불가")

                # 추방 메시지 표시
                kick_msg_data = {
                    'text': f"👋 {nickname}님이 방장에 의해 추방되었습니다.",
                    'nickname': '시스템',
                    'timestamp': time.time(),
                    'translated': ''
                }
                kick_bubble = create_message_bubble(kick_msg_data, False)
                if kick_bubble:
                    setattr(kick_bubble, 'timestamp', kick_msg_data['timestamp'])
                    chat_messages.controls.append(kick_bubble)

                # Firebase에 추방 알림 메시지 전송
                if firebase_available:
                    db.reference(f'rooms/{room_id}/messages').push(kick_msg_data)

                page.update()
            except Exception as e:
                print(f"추방 처리 오류: {e}")
                
            # 다이얼로그 닫기
            page.dialog.open = False
            page.update()

        def cancel_kick(e):
            page.dialog.open = False
            page.update()

        # 추방 확인 다이얼로그
        kick_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("사용자 추방"),
            content=ft.Text(f"{nickname}님을 채팅방에서 추방하시겠습니까?\n추방된 사용자는 더 이상 이 채팅방에 접근할 수 없습니다."),
            actions=[
                ft.TextButton("취소", on_click=cancel_kick),
                ft.TextButton("추방", on_click=confirm_kick, style=ft.ButtonStyle(color=ft.Colors.RED))
            ]
        )
        
        page.dialog = kick_dialog
        kick_dialog.open = True
        page.update()

    # --- 퇴장 감지용(페이지 언로드) ---
    def on_exit():
        nickname = page.session.get('nickname') or ''
        if nickname and nickname in current_users:
            leave_text = f"{nickname}님이 채팅방을 나가셨습니다."
            chat_messages.controls.append(create_system_message_bubble(leave_text))
            current_users.remove(nickname)
            page.update()
    atexit.register(on_exit)

    # --- 메시지 전송 함수 ---
    def send_message(e=None):
        if not input_box.value or not input_box.value.strip():
            return
        message_text = input_box.value.strip()
        nickname = page.session.get('nickname') or '' or '익명'
        
        # 부적절한 메시지 체크
        is_inappropriate, reason = is_inappropriate_message(message_text)
        if is_inappropriate:
            # 경고 메시지 표시
            warning_msg_data = {
                'text': f"⚠️ {reason}",
                'nickname': '시스템',
                'timestamp': time.time(),
                'translated': ''
            }
            warning_bubble = create_message_bubble(warning_msg_data, False)
            if warning_bubble:  # None이 아닌 경우만 처리
                setattr(warning_bubble, 'timestamp', warning_msg_data['timestamp'])
                chat_messages.controls.append(warning_bubble)
            page.update()
            return
        
        # 메시지 필터링 (부적절한 단어 마스킹)
        filtered_message = filter_message(message_text)
        if filtered_message != message_text:
            message_text = filtered_message
        
        # 입력창 초기화 (먼저 초기화하여 UI 반응성 향상)
        input_box.value = ""
        page.update()
        
        # 번역 처리
        translated_text = ""
        if translate_switch and translate_switch.value and current_target_lang[0]:
            try:
                translated_text = translate_message(message_text, current_target_lang[0])
            except Exception as e:
                translated_text = f"[번역 오류: {e}]"
        
        # Firebase에 메시지 저장 (RAG 방이 아닐 때만)
        if firebase_available and not (is_busan_food_rag or room_id == "busan_food_search_rag" or is_foreign_worker_rag or room_id == "foreign_worker_rights_rag"):
            try:
                message_data = {
                    'text': message_text,
                    'nickname': nickname,
                    'timestamp': time.time(),
                    'translated': translated_text
                }
                db.reference(f'rooms/{room_id}/messages').push(message_data)
            except Exception as e:
                print(f"Firebase 저장 오류: {e}")
        
        # RAG 방이면 사용자 메시지와 RAG 답변을 직접 추가
        if is_busan_food_rag or room_id == "busan_food_search_rag" or is_foreign_worker_rag or room_id == "foreign_worker_rights_rag":
            # 사용자 메시지 추가
            user_msg_data = {
                'text': message_text,
                'nickname': nickname,
                'timestamp': time.time(),
                'translated': translated_text
            }
            user_bubble = create_message_bubble(user_msg_data, True)
            if user_bubble:  # None이 아닌 경우만 처리
                setattr(user_bubble, 'timestamp', user_msg_data['timestamp'])
                chat_messages.controls.append(user_bubble)
                page.update()
            
            # RAG 답변 추가 (더 안전한 처리)
            try:
                # 다국어 로딩 메시지
                loading_messages = {
                    "ko": "답변을 생성하고 있습니다...",
                    "en": "Generating answer...",
                    "ja": "回答を生成しています...",
                    "zh": "正在生成答案...",
                    "zh-TW": "正在生成答案...",
                    "vi": "Đang tạo câu trả lời...",
                    "th": "กำลังสร้างคำตอบ...",
                    "id": "Sedang membuat jawaban...",
                    "fr": "Génération de la réponse...",
                    "de": "Antwort wird generiert...",
                    "tl": "Ginagawa ang sagot...",
                    "ms": "Sedang menjana jawapan...",
                    "pt": "Gerando resposta...",
                    "es": "Generando respuesta...",
                    "it": "Creazione della risposta...",
                    "ru": "Генерация ответа...",
                    "ar": "جاري إنشاء الإجابة...",
                    "hi": "उत्तर बनाया जा रहा है...",
                    "nl": "Antwoord genereren...",
                    "sv": "Genererar svar...",
                    "tr": "Cevap oluşturuluyor..."
                }
                
                # 현재 사용자 언어에 맞는 로딩 메시지 선택
                current_lang = user_lang if user_lang else 'ko'
                loading_text = loading_messages.get(current_lang, loading_messages["ko"])
                
                # 로딩 메시지 먼저 표시 (질문 바로 아래에 위치)
                loading_msg_data = {
                    'text': loading_text,
                    'nickname': 'RAG',
                    'timestamp': time.time(),
                    'translated': ''
                }
                loading_bubble = create_message_bubble(loading_msg_data, False)
                if loading_bubble:  # None이 아닌 경우만 처리
                    setattr(loading_bubble, 'timestamp', loading_msg_data['timestamp'])
                    # 질문 바로 아래에 insert
                    chat_messages.controls.insert(len(chat_messages.controls), loading_bubble)
                page.update()
                
                # RAG 방에서는 선택된 언어로 답변 생성
                if is_busan_food_rag or room_id == "busan_food_search_rag":
                    selected_lang = current_target_lang[0] if current_target_lang[0] else user_lang
                    rag_answer = custom_translate_message(message_text, selected_lang)
                elif is_foreign_worker_rag or room_id == "foreign_worker_rights_rag":
                    selected_lang = current_target_lang[0] if current_target_lang[0] else user_lang
                    rag_answer = custom_translate_message(message_text, selected_lang)
                else:
                    # 일반 RAG 방에서는 기존 방식 사용
                    rag_answer = custom_translate_message(message_text, user_lang)
                
                # 로딩 메시지 위치에 답변을 insert (replace)
                idx = chat_messages.controls.index(loading_bubble)
                chat_messages.controls.remove(loading_bubble)
                if rag_answer and rag_answer.strip():  # 답변이 있을 때만 추가
                    rag_msg_data = {
                        'text': rag_answer,
                        'nickname': 'RAG',
                        'timestamp': time.time(),
                        'translated': ''
                    }
                    rag_bubble = create_message_bubble(rag_msg_data, False)
                    if rag_bubble:  # None이 아닌 경우만 처리
                        setattr(rag_bubble, 'timestamp', rag_msg_data['timestamp'])
                        chat_messages.controls.insert(idx, rag_bubble)
                    page.update()
                else:
                    page.update()
            except Exception as e:
                print(f'RAG 답변 오류: {e}')
                try:
                    if 'loading_bubble' in locals():
                        chat_messages.controls.remove(loading_bubble)
                except:
                    pass
                page.update()
                # 다국어 에러 메시지
                error_messages = {
                    "ko": f"죄송합니다. 답변을 생성하는 중 오류가 발생했습니다: {str(e)}",
                    "en": f"Sorry. An error occurred while generating the answer: {str(e)}",
                    "ja": f"申し訳ございません。回答を生成中にエラーが発生しました: {str(e)}",
                    "zh": f"抱歉，生成答案时发生错误: {str(e)}",
                    "zh-TW": f"抱歉，生成答案時發生錯誤: {str(e)}",
                    "vi": f"Xin lỗi. Đã xảy ra lỗi khi tạo câu trả lời: {str(e)}",
                    "th": f"ขออภัย เกิดข้อผิดพลาดขณะสร้างคำตอบ: {str(e)}",
                    "id": f"Maaf. Terjadi kesalahan saat membuat jawaban: {str(e)}",
                    "fr": f"Désolé. Une erreur s'est produite lors de la génération de la réponse: {str(e)}",
                    "de": f"Entschuldigung. Bei der Antwortgenerierung ist ein Fehler aufgetreten: {str(e)}",
                    "tl": f"Pasensya na. May naganap na error habang ginagawa ang sagot: {str(e)}",
                    "ms": f"Maaf. Ralat berlaku semasa menjana jawapan: {str(e)}",
                    "pt": f"Desculpe. Ocorreu um erro ao gerar a resposta: {str(e)}",
                    "es": f"Lo siento. Ocurrió un error al generar la respuesta: {str(e)}",
                    "it": f"Scusa. Si è verificato un errore durante la generazione della risposta: {str(e)}",
                    "ru": f"Извините. Произошла ошибка при генерации ответа: {str(e)}",
                    "ar": f"آسف. حدث خطأ أثناء إنشاء الإجابة: {str(e)}",
                    "hi": f"खुशी है। उत्तर बनाते समय त्रुटि हुई: {str(e)}",
                    "nl": f"Sorry. Er is een fout opgetreden bij het genereren van het antwoord: {str(e)}",
                    "sv": f"Ursäkta. Ett fel uppstod när svaret genererades: {str(e)}",
                    "tr": f"Üzgünüm. Cevap oluşturulurken hata oluştu: {str(e)}"
                }
                
                current_lang = user_lang if user_lang else 'ko'
                error_text = error_messages.get(current_lang, error_messages["ko"])
                
                error_msg_data = {
                    'text': error_text,
                    'nickname': '시스템',
                    'timestamp': time.time(),
                    'translated': ''
                }
                error_bubble = create_message_bubble(error_msg_data, False)
                setattr(error_bubble, 'timestamp', error_msg_data['timestamp'])
                chat_messages.controls.append(error_bubble)
                page.update()
        # 일반 RAG 채팅방이면 RAG 답변만 직접 추가
        elif custom_translate_message is not None:
            try:
                # 다국어 로딩 메시지 (일반 RAG용)
                loading_messages = {
                    "ko": "답변을 생성하고 있습니다...",
                    "en": "Generating answer...",
                    "ja": "回答を生成しています...",
                    "zh": "正在生成答案...",
                    "zh-TW": "正在生成答案...",
                    "vi": "Đang tạo câu trả lời...",
                    "th": "กำลังสร้างคำตอบ...",
                    "id": "Sedang membuat jawaban...",
                    "fr": "Génération de la réponse...",
                    "de": "Antwort wird generiert...",
                    "tl": "Ginagawa ang sagot...",
                    "ms": "Sedang menjana jawapan...",
                    "pt": "Gerando resposta...",
                    "es": "Generando respuesta...",
                    "it": "Creazione della risposta...",
                    "ru": "Генерация ответа...",
                    "ar": "جاري إنشاء الإجابة...",
                    "hi": "उत्तर बनाया जा रहा है...",
                    "nl": "Antwoord genereren...",
                    "sv": "Genererar svar...",
                    "tr": "Cevap oluşturuluyor..."
                }
                
                # 현재 사용자 언어에 맞는 로딩 메시지 선택
                current_lang = user_lang if user_lang else 'ko'
                loading_text = loading_messages.get(current_lang, loading_messages["ko"])
                
                # 로딩 메시지 먼저 표시
                loading_msg_data = {
                    'text': loading_text,
                    'nickname': 'RAG',
                    'timestamp': time.time(),
                    'translated': ''
                }
                loading_bubble = create_message_bubble(loading_msg_data, False)
                if loading_bubble:  # None이 아닌 경우만 처리
                    setattr(loading_bubble, 'timestamp', loading_msg_data['timestamp'])
                    chat_messages.controls.append(loading_bubble)
                page.update()
                # RAG 답변 생성 (선택된 언어로)
                selected_lang = current_target_lang[0] if current_target_lang[0] else user_lang
                rag_answer = custom_translate_message(message_text, selected_lang)
                # 로딩 메시지 제거
                chat_messages.controls.remove(loading_bubble)
                if rag_answer and rag_answer.strip():  # 답변이 있을 때만 추가
                    rag_msg_data = {
                        'text': rag_answer,
                        'nickname': 'RAG',
                        'timestamp': time.time(),
                        'translated': ''
                    }
                    message_bubble = create_message_bubble(rag_msg_data, False)
                    if message_bubble:  # None이 아닌 경우만 처리
                        setattr(message_bubble, 'timestamp', rag_msg_data['timestamp'])
                        chat_messages.controls.append(message_bubble)
                    page.update()
                else:
                    # 답변이 없어도 화면 업데이트
                    page.update()
            except Exception as e:
                print(f'RAG 답변 오류: {e}')
                # 로딩 메시지가 있다면 제거
                try:
                    if 'loading_bubble' in locals():
                        chat_messages.controls.remove(loading_bubble)
                except:
                    pass
                # 오류 발생 시에도 화면 업데이트
                page.update()
                # 오류 메시지도 표시
                # 다국어 에러 메시지
                error_messages = {
                    "ko": f"죄송합니다. 답변을 생성하는 중 오류가 발생했습니다: {str(e)}",
                    "en": f"Sorry. An error occurred while generating the answer: {str(e)}",
                    "ja": f"申し訳ございません。回答を生成中にエラーが発生しました: {str(e)}",
                    "zh": f"抱歉，生成答案时发生错误: {str(e)}",
                    "zh-TW": f"抱歉，生成答案時發生錯誤: {str(e)}",
                    "vi": f"Xin lỗi. Đã xảy ra lỗi khi tạo câu trả lời: {str(e)}",
                    "th": f"ขออภัย เกิดข้อผิดพลาดขณะสร้างคำตอบ: {str(e)}",
                    "id": f"Maaf. Terjadi kesalahan saat membuat jawaban: {str(e)}",
                    "fr": f"Désolé. Une erreur s'est produite lors de la génération de la réponse: {str(e)}",
                    "de": f"Entschuldigung. Bei der Antwortgenerierung ist ein Fehler aufgetreten: {str(e)}",
                    "tl": f"Pasensya na. May naganap na error habang ginagawa ang sagot: {str(e)}",
                    "ms": f"Maaf. Ralat berlaku semasa menjana jawapan: {str(e)}",
                    "pt": f"Desculpe. Ocorreu um erro ao gerar a resposta: {str(e)}",
                    "es": f"Lo siento. Ocurrió un error al generar la respuesta: {str(e)}",
                    "it": f"Scusa. Si è verificato un errore durante la generazione della risposta: {str(e)}",
                    "ru": f"Извините. Произошла ошибка при генерации ответа: {str(e)}",
                    "ar": f"آسف. حدث خطأ أثناء إنشاء الإجابة: {str(e)}",
                    "hi": f"खुशी है। उत्तर बनाते समय त्रुटि हुई: {str(e)}",
                    "nl": f"Sorry. Er is een fout opgetreden bij het genereren van het antwoord: {str(e)}",
                    "sv": f"Ursäkta. Ett fel uppstod när svaret genererades: {str(e)}",
                    "tr": f"Üzgünüm. Cevap oluşturulurken hata oluştu: {str(e)}"
                }
                
                current_lang = user_lang if user_lang else 'ko'
                error_text = error_messages.get(current_lang, error_messages["ko"])
                
                error_msg_data = {
                    'text': error_text,
                    'nickname': '시스템',
                    'timestamp': time.time(),
                    'translated': ''
                }
                error_bubble = create_message_bubble(error_msg_data, False)
                if error_bubble:  # None이 아닌 경우만 처리
                    setattr(error_bubble, 'timestamp', error_msg_data['timestamp'])
                    chat_messages.controls.append(error_bubble)
                page.update()

    # Enter 키로 메시지 전송 설정
    input_box.on_submit = send_message

    # --- 뒤로가기 함수 ---
    def go_back(e):
        if on_back:
            on_back(e)

    # --- Firebase 리스너 설정 ---
    firebase_listener = None  # 리스너 객체 저장용 변수
    if firebase_available:
        try:
            # 기존 메시지들을 먼저 로드
            def load_existing_messages():
                try:
                    messages_ref = db.reference(f'rooms/{room_id}/messages')
                    existing_messages = messages_ref.get()
                    
                    if existing_messages:
                        print(f"기존 메시지 {len(existing_messages)}개 발견, 로딩 중...")
                        
                        # 메시지를 timestamp 순으로 정렬
                        sorted_messages = []
                        for msg_id, msg_data in existing_messages.items():
                            if isinstance(msg_data, dict):
                                msg_data['msg_id'] = msg_id
                                sorted_messages.append(msg_data)
                        
                        sorted_messages.sort(key=lambda x: x.get('timestamp', 0))
                        
                        # 각 메시지를 UI에 추가
                        for msg_data in sorted_messages:
                            try:
                                # 차단된 사용자의 메시지는 무시
                                if is_user_blocked(msg_data.get('nickname', '')):
                                    continue
                                
                                # 시스템 메시지 처리
                                if msg_data.get('nickname') == '시스템':
                                    system_bubble = create_system_message_bubble(msg_data.get('text', ''))
                                    if system_bubble:
                                        chat_messages.controls.append(system_bubble)
                                    continue
                                
                                # 일반 메시지 처리
                                current_user = page.session.get('nickname') or ''
                                is_me = msg_data.get('nickname') == current_user
                                
                                message_bubble = create_message_bubble(msg_data, is_me)
                                if message_bubble:
                                    chat_messages.controls.append(message_bubble)
                                    
                            except Exception as e:
                                print(f"메시지 로드 중 오류: {e}")
                                continue
                        
                        print(f"기존 메시지 로딩 완료: {len(sorted_messages)}개")
                        page.update()
                    else:
                        print("기존 메시지가 없습니다.")
                        
                except Exception as e:
                    print(f"기존 메시지 로드 오류: {e}")
            
            # 기존 메시지 로드
            load_existing_messages()
            
            # Firebase 리스너 설정 (새로운 메시지용)
            firebase_listener = db.reference(f'rooms/{room_id}/messages').listen(on_message)
            
        except Exception as e:
            print(f"Firebase 초기화 오류: {e}")

    # --- UI 구성 ---
    # RAG 채팅방이면 예시/가이드 메시지를 항상 맨 위에 추가 (중복 방지)
    def get_rag_guide_message():
        # 부산 맛집 검색 RAG 방인지 확인
        if is_busan_food_rag or room_id == "busan_food_search_rag":
            guide_texts = BUSAN_FOOD_GUIDE_TEXTS.get(user_lang, BUSAN_FOOD_GUIDE_TEXTS["ko"])
            
            # 부산 맛집 데이터 소개 및 다운로드 버튼 추가
            def download_busan_taste(e):
                try:
                    # Flet 웹 환경에서 더 안정적인 방법
                    page.launch_url("https://www.visitbusan.net/board/download.do?boardId=BBS_0000007&dataSid=4208&fileSid=7458")
                    # 성공 메시지 표시
                    page.show_snack_bar(
                        ft.SnackBar(content=ft.Text("부산의맛 가이드 다운로드를 시작합니다..."), open=True)
                    )
                except Exception as ex:
                    # 실패 시 대체 방법
                    import webbrowser
                    webbrowser.open("https://www.visitbusan.net/board/download.do?boardId=BBS_0000007&dataSid=4208&fileSid=7458")
                    print(f"다운로드 오류: {ex}")

            def download_taek_sulling(e):
                try:
                    # Flet 웹 환경에서 더 안정적인 방법
                    page.launch_url("https://www.visitbusan.net/board/download.do?boardId=BBS_0000007&dataSid=4277&fileSid=7886")
                    # 성공 메시지 표시
                    page.show_snack_bar(
                        ft.SnackBar(content=ft.Text("택슐랭 가이드 다운로드를 시작합니다..."), open=True)
                    )
                except Exception as ex:
                    # 실패 시 대체 방법
                    import webbrowser
                    webbrowser.open("https://www.visitbusan.net/board/download.do?boardId=BBS_0000007&dataSid=4277&fileSid=7886")
                    print(f"다운로드 오류: {ex}")
            
            # 다국어 소개 텍스트
            intro_texts = {
                "ko": {
                    "title": "📚 부산 맛집 데이터 소개",
                    "busan_taste": "부산의맛(2025): 부산시에서 제공하는 공식 맛집 가이드로, 16개 구군별로 선별된 맛집 정보를 포함합니다.",
                    "taek_sulling": "택슐랭(2025): 부산원도심활성화축제에서 제작한 맛집 가이드로, 지역별 특색 있는 맛집들을 소개합니다.",
                    "download_busan": "부산의맛(2025) 다운로드",
                    "download_taek": "택슐랭(2025) 다운로드"
                },
                "en": {
                    "title": "📚 Busan Restaurant Data Introduction",
                    "busan_taste": "Busan Taste (2025): Official restaurant guide provided by Busan City, including selected restaurants from 16 districts.",
                    "taek_sulling": "Taek Sulling (2025): Restaurant guide produced by Busan Old Downtown Revitalization Festival, featuring unique local restaurants.",
                    "download_busan": "Download Busan Taste (2025)",
                    "download_taek": "Download Taek Sulling (2025)"
                },
                "ja": {
                    "title": "📚 釜山グルメデータ紹介",
                    "busan_taste": "釜山の味(2025): 釜山市が提供する公式グルメガイドで、16区郡別に選ばれたレストラン情報を含みます。",
                    "taek_sulling": "택슐랭(2025): 釜山原都心活性化祭りで制作されたグルメガイドで、地域別の特色あるレストランを紹介します。",
                    "download_busan": "釜山の味(2025)ダウンロード",
                    "download_taek": "택슐랭(2025)ダウンロード"
                },
                "zh": {
                    "title": "📚 釜山美食数据介绍",
                    "busan_taste": "釜山美味(2025): 釜山市提供的官方美食指南，包含16个区郡精选餐厅信息。",
                    "taek_sulling": "택슐랭(2025): 釜山原都心活化节制作的美食指南，介绍各地特色餐厅。",
                    "download_busan": "下载釜山美味(2025)",
                    "download_taek": "下载택슐랭(2025)"
                },
                "vi": {
                    "title": "📚 Giới thiệu dữ liệu nhà hàng Busan",
                    "busan_taste": "Busan Taste (2025): Hướng dẫn nhà hàng chính thức do thành phố Busan cung cấp, bao gồm thông tin nhà hàng được chọn lọc từ 16 quận.",
                    "taek_sulling": "Taek Sulling (2025): Hướng dẫn nhà hàng được sản xuất bởi Lễ hội Phục hưng Trung tâm Cũ Busan, giới thiệu các nhà hàng địa phương độc đáo.",
                    "download_busan": "Tải xuống Busan Taste (2025)",
                    "download_taek": "Tải xuống Taek Sulling (2025)"
                },
                "th": {
                    "title": "📚 แนะนำข้อมูลร้านอาหารปูซาน",
                    "busan_taste": "Busan Taste (2025): คู่มือร้านอาหารอย่างเป็นทางการที่จัดทำโดยเมืองปูซาน รวมข้อมูลร้านอาหารที่คัดสรรมาแล้วจาก 16 เขต",
                    "taek_sulling": "Taek Sulling (2025): คู่มือร้านอาหารที่จัดทำโดยเทศกาลฟื้นฟูใจกลางเมืองเก่าปูซาน นำเสนอร้านอาหารท้องถิ่นที่มีเอกลักษณ์",
                    "download_busan": "ดาวน์โหลด Busan Taste (2025)",
                    "download_taek": "ดาวน์โหลด Taek Sulling (2025)"
                },
                "fr": {
                    "title": "📚 Introduction aux données de restaurants de Busan",
                    "busan_taste": "Busan Taste (2025): Guide de restaurants officiel fourni par la ville de Busan, incluant des restaurants sélectionnés de 16 districts.",
                    "taek_sulling": "Taek Sulling (2025): Guide de restaurants produit par le Festival de revitalisation du centre-ville de Busan, présentant des restaurants locaux uniques.",
                    "download_busan": "Télécharger Busan Taste (2025)",
                    "download_taek": "Télécharger Taek Sulling (2025)"
                },
                "de": {
                    "title": "📚 Busan Restaurant-Daten Einführung",
                    "busan_taste": "Busan Taste (2025): Offizieller Restaurantführer der Stadt Busan mit ausgewählten Restaurants aus 16 Bezirken.",
                    "taek_sulling": "Taek Sulling (2025): Restaurantführer des Busan Altstadt-Revitalisierungsfestivals mit einzigartigen lokalen Restaurants.",
                    "download_busan": "Busan Taste (2025) herunterladen",
                    "download_taek": "Taek Sulling (2025) herunterladen"
                },
                "zh-TW": {
                    "title": "📚 釜山美食資料介紹",
                    "busan_taste": "釜山美味(2025): 釜山市提供的官方美食指南，包含16個區郡精選餐廳資訊。",
                    "taek_sulling": "택슐랭(2025): 釜山原都心活化節製作的美食指南，介紹各地特色餐廳。",
                    "download_busan": "下載釜山美味(2025)",
                    "download_taek": "下載택슐랭(2025)"
                },
                "id": {
                    "title": "📚 Pengenalan Data Restoran Busan",
                    "busan_taste": "Busan Taste (2025): Panduan restoran resmi yang disediakan oleh Kota Busan, termasuk informasi restoran pilihan dari 16 distrik.",
                    "taek_sulling": "Taek Sulling (2025): Panduan restoran yang diproduksi oleh Festival Revitalisasi Pusat Kota Lama Busan, menampilkan restoran lokal yang unik.",
                    "download_busan": "Unduh Busan Taste (2025)",
                    "download_taek": "Unduh Taek Sulling (2025)"
                }
            }
            
            intro_text = intro_texts.get(user_lang, intro_texts["ko"])
            
            # 데이터 소개 및 다운로드 버튼
            data_intro = ft.Container(
                content=ft.Column([
                    ft.Text(intro_text["title"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600),
                    ft.Container(height=8),
                    ft.Text(intro_text["busan_taste"], size=13, color=ft.Colors.GREY_700, selectable=True),
                    ft.Container(height=4),
                    ft.Text(intro_text["taek_sulling"], size=13, color=ft.Colors.GREY_700, selectable=True),
                    ft.Container(height=12),
                    ft.Row([
                        ft.ElevatedButton(
                            intro_text["download_busan"],
                            icon=ft.Icons.DOWNLOAD,
                            on_click=download_busan_taste,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE),
                            width=150
                        ),
                        ft.ElevatedButton(
                            intro_text["download_taek"],
                            icon=ft.Icons.DOWNLOAD,
                            on_click=download_taek_sulling,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                            width=150
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
                ], spacing=4),
                padding=12,
                bgcolor=ft.LinearGradient(["#FFF3E0", "#FFE0B2"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                border_radius=8,
                border=ft.border.all(1, "#FF9800"),
                margin=ft.margin.only(bottom=12)
            )
            
            guide_items = []
            for item in guide_texts["items"]:
                guide_items.append(ft.Text(item, size=14 if is_mobile else 16, color=ft.Colors.GREY_700, selectable=True))
            example_items = []
            for example in guide_texts["examples"]:
                example_items.append(ft.Text(example, size=13 if is_mobile else 14, color=ft.Colors.GREY_600, selectable=True))
            bubble_width = int(page.width * 0.9) if is_mobile else 400
            return ft.Container(
                content=ft.Column([
                    ft.Text(guide_texts["title"], size=18 if is_mobile else 20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, selectable=True),
                    ft.Container(height=8),
                    data_intro,  # 데이터 소개 및 다운로드 버튼 추가
                    ft.Text(guide_texts["info"], size=15 if is_mobile else 16, color=ft.Colors.GREY_700, selectable=True),
                    ft.Container(height=8),
                    *guide_items,
                    ft.Container(height=12),
                    ft.Text(guide_texts["example_title"], size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700, selectable=True),
                    ft.Container(height=6),
                    *example_items,
                    ft.Container(height=12),
                    ft.Text(guide_texts["input_hint"], size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, text_align=ft.TextAlign.CENTER, selectable=True),
                ], spacing=4),
                padding=16 if is_mobile else 20,
                bgcolor=ft.LinearGradient(["#E3F2FD", "#BBDEFB"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                border_radius=12,
                margin=ft.margin.only(bottom=16),
                border=ft.border.all(1, "#2196F3"),
                width=bubble_width,
            )
        # 외국인 근로자 권리구제 RAG 방인지 확인 (방 ID와 파라미터 모두 확인)
        elif is_foreign_worker_rag or room_id == "foreign_worker_rights_rag":
            guide_texts = FOREIGN_WORKER_GUIDE_TEXTS.get(user_lang, FOREIGN_WORKER_GUIDE_TEXTS["ko"])
            
            # 안전 버튼 생성 함수
            def create_safety_button(button_info):
                def on_safety_button_click(e):
                    # 현재 언어에 맞는 텍스트 가져오기
                    safety_texts = SAFETY_BUTTON_TEXTS.get(user_lang, SAFETY_BUTTON_TEXTS["ko"])
                    if button_info["type"] == "jangmachul":
                        input_box.value = safety_texts["jangmachul"]
                    elif button_info["type"] == "onyul":
                        input_box.value = safety_texts["onyul"]
                    page.update()
                    # 자동으로 메시지 전송
                    send_message()
                
                return ft.ElevatedButton(
                    content=ft.Row([
                        ft.Text(button_info["emoji"], size=16),
                        ft.Text(button_info["text"], size=12 if is_mobile else 14, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8, tight=True),
                    on_click=on_safety_button_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.ORANGE_50,
                        color=ft.Colors.ORANGE_800,
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                        shape=ft.RoundedRectangleBorder(radius=8),
                        side=ft.BorderSide(color=ft.Colors.ORANGE_200, width=1)
                    ),
                    height=45
                )
            
            # 안전 버튼들 생성
            safety_buttons = []
            if "safety_buttons" in guide_texts:
                for button_info in guide_texts["safety_buttons"]:
                    safety_buttons.append(create_safety_button(button_info))
            
            guide_items = []
            for item in guide_texts["items"]:
                guide_items.append(ft.Text(item, size=14 if is_mobile else 16, color=ft.Colors.GREY_700, selectable=True))
            example_items = []
            for example in guide_texts["examples"]:
                example_items.append(ft.Text(example, size=13 if is_mobile else 14, color=ft.Colors.GREY_600, selectable=True))
            
            # 안전 버튼 섹션 추가
            safety_section = []
            if safety_buttons:
                # 안전 섹션 제목 다국어 처리
                safety_titles = {
                    "ko": "🚧 안전 관련 정보",
                    "en": "🚧 Safety Information",
                    "vi": "🚧 Thông tin an toàn",
                    "ja": "🚧 安全関連情報",
                    "zh": "🚧 安全相关信息",
                    "zh-TW": "🚧 安全相關資訊",
                    "id": "🚧 Informasi Keselamatan",
                    "th": "🚧 ข้อมูลความปลอดภัย",
                    "fr": "🚧 Informations de sécurité",
                    "de": "🚧 Sicherheitsinformationen"
                }
                safety_title = safety_titles.get(user_lang, safety_titles["ko"])
                
                safety_section = [
                    ft.Container(height=12),
                    ft.Text(safety_title, size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700, selectable=True),
                    ft.Container(height=8),
                    ft.Column(safety_buttons, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                ]
            
            bubble_width = int(page.width * 0.9) if is_mobile else 400
            return ft.Container(
                content=ft.Column([
                    ft.Text(guide_texts["title"], size=18 if is_mobile else 20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, selectable=True),
                    ft.Container(height=8),
                    ft.Text(guide_texts["info"], size=15 if is_mobile else 16, color=ft.Colors.GREY_700, selectable=True),
                    ft.Container(height=8),
                    *guide_items,
                    ft.Container(height=12),
                    ft.Text(guide_texts["example_title"], size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700, selectable=True),
                    ft.Container(height=6),
                    *example_items,
                    *safety_section,
                    ft.Container(height=12),
                    ft.Text(guide_texts["input_hint"], size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, text_align=ft.TextAlign.CENTER, selectable=True),
                ], spacing=4),
                padding=16 if is_mobile else 20,
                bgcolor=ft.LinearGradient(["#E3F2FD", "#BBDEFB"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                border_radius=12,
                margin=ft.margin.only(bottom=16),
                border=ft.border.all(1, "#2196F3"),
                width=bubble_width,
            )
        else:
            guide_texts = RAG_GUIDE_TEXTS.get(user_lang, RAG_GUIDE_TEXTS["ko"])
        guide_items = []
        for item in guide_texts["items"]:
            guide_items.append(ft.Text(item, size=14 if is_mobile else 16, color=ft.Colors.GREY_700, selectable=True))
        example_items = []
        for example in guide_texts["examples"]:
            example_items.append(ft.Text(example, size=13 if is_mobile else 14, color=ft.Colors.GREY_600, selectable=True))
        bubble_width = int(page.width * 0.9) if is_mobile else 400
        return ft.Container(
            content=ft.Column([
                ft.Text(guide_texts["title"], size=18 if is_mobile else 20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, selectable=True),
                ft.Container(height=8),
                ft.Text(guide_texts["info"], size=15 if is_mobile else 16, color=ft.Colors.GREY_700, selectable=True),
                ft.Container(height=8),
                *guide_items,
                ft.Container(height=12),
                ft.Text(guide_texts["example_title"], size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700, selectable=True),
                ft.Container(height=6),
                *example_items,
                ft.Container(height=12),
                ft.Text(guide_texts["input_hint"], size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, text_align=ft.TextAlign.CENTER, selectable=True),
            ], spacing=4),
            padding=16 if is_mobile else 20,
            bgcolor=ft.LinearGradient(["#E3F2FD", "#BBDEFB"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
            border_radius=12,
            margin=ft.margin.only(bottom=16),
            border=ft.border.all(1, "#2196F3"),
            width=bubble_width,
        )
        
        # 안전 버튼 생성 함수
        def create_safety_button(button_info):
            def on_safety_button_click(e):
                # 현재 언어에 맞는 텍스트 가져오기
                safety_texts = SAFETY_BUTTON_TEXTS.get(user_lang, SAFETY_BUTTON_TEXTS["ko"])
                if button_info["type"] == "jangmachul":
                    input_box.value = safety_texts["jangmachul"]
                elif button_info["type"] == "onyul":
                    input_box.value = safety_texts["onyul"]
                page.update()
                # 자동으로 메시지 전송
                send_message()
            
            return ft.ElevatedButton(
                content=ft.Row([
                    ft.Text(button_info["emoji"], size=16),
                    ft.Text(button_info["text"], size=12 if is_mobile else 14, weight=ft.FontWeight.BOLD)
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8, tight=True),
                on_click=on_safety_button_click,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.ORANGE_50,
                    color=ft.Colors.ORANGE_800,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(color=ft.Colors.ORANGE_200, width=1)
                ),
                height=45
            )
        
        # 안전 버튼들 생성
        safety_buttons = []
        if "safety_buttons" in guide_texts:
            for button_info in guide_texts["safety_buttons"]:
                safety_buttons.append(create_safety_button(button_info))
        guide_items = []
        for item in guide_texts["items"]:
            guide_items.append(ft.Text(item, size=14 if is_mobile else 16, color=ft.Colors.GREY_700, selectable=True))
        example_items = []
        for example in guide_texts["examples"]:
            example_items.append(ft.Text(example, size=13 if is_mobile else 14, color=ft.Colors.GREY_600, selectable=True))
        
        # 안전 버튼 섹션 추가
        safety_section = []
        if safety_buttons:
            # 안전 섹션 제목 다국어 처리
            safety_titles = {
                "ko": "🚧 안전 관련 정보",
                "en": "🚧 Safety Information",
                "vi": "🚧 Thông tin an toàn",
                "ja": "🚧 安全関連情報",
                "zh": "🚧 安全相关信息",
                "zh-TW": "🚧 安全相關資訊",
                "id": "🚧 Informasi Keselamatan",
                "th": "🚧 ข้อมูลความปลอดภัย",
                "fr": "🚧 Informations de sécurité",
                "de": "🚧 Sicherheitsinformationen"
            }
            safety_title = safety_titles.get(user_lang, safety_titles["ko"])
            
            safety_section = [
                ft.Container(height=12),
                ft.Text(safety_title, size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700, selectable=True),
                ft.Container(height=8),
                ft.Column(safety_buttons, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            ]
        
        bubble_width = int(page.width * 0.9) if is_mobile else 400
        return ft.Container(
            content=ft.Column([
                ft.Text(guide_texts["title"], size=18 if is_mobile else 20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, selectable=True),
                ft.Container(height=8),
                ft.Text(guide_texts["info"], size=15 if is_mobile else 16, color=ft.Colors.GREY_700, selectable=True),
                ft.Container(height=8),
                *guide_items,
                ft.Container(height=12),
                ft.Text(guide_texts["example_title"], size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700, selectable=True),
                ft.Container(height=6),
                *example_items,
                *safety_section,
                ft.Container(height=12),
                ft.Text(guide_texts["input_hint"], size=15 if is_mobile else 16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, text_align=ft.TextAlign.CENTER, selectable=True),
            ], spacing=4),
            padding=16 if is_mobile else 20,
            bgcolor=ft.LinearGradient(["#E3F2FD", "#BBDEFB"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
            border_radius=12,
            margin=ft.margin.only(bottom=16),
            border=ft.border.all(1, "#2196F3"),
            width=bubble_width,
        )
    
    # 다국어 '빠른 채팅방' 타이틀 사전
    QUICK_ROOM_TITLES = {
        "ko": "빠른 채팅방",
        "en": "Quick Chat Room",
        "ja": "クイックチャットルーム",
        "zh": "快速聊天室",
        "zh-TW": "快速聊天室",
        "id": "Ruang Obrolan Cepat",
        "vi": "Phòng chat nhanh",
        "fr": "Salon de discussion rapide",
        "de": "Schnell-Chatraum",
        "th": "ห้องแชทด่วน",
        "tl": "Mabilis na Chat Room"
    }
    # 공식 안내 채팅방(RAG) 헤더 타이틀 다국어 처리
    is_rag_room = custom_translate_message is not None
    rag_title = None
    if is_rag_room:
        if is_busan_food_rag or room_id == "busan_food_search_rag":
            rag_title = BUSAN_FOOD_GUIDE_TEXTS.get(user_lang, BUSAN_FOOD_GUIDE_TEXTS["ko"])['title']
        elif is_foreign_worker_rag or room_id == "foreign_worker_rights_rag":
            rag_title = FOREIGN_WORKER_GUIDE_TEXTS.get(user_lang, FOREIGN_WORKER_GUIDE_TEXTS["ko"])['title']
        else:
            rag_title = RAG_GUIDE_TEXTS.get(user_lang, RAG_GUIDE_TEXTS["en"])['title']
    # --- 채팅방 관리 함수 ---
    def show_room_settings(e):
        """채팅방 설정 다이얼로그 표시"""
        def close_settings(e):
            if page.overlay:
                page.overlay.pop()
                page.update()
        
        # 방장 권한 확인
        current_nickname = page.session.get('nickname') or ''
        current_user_id = page.session.get('user_id') or None
        is_owner = is_room_owner(room_id, current_nickname, current_user_id)
        
        # 차단된 사용자 목록 가져오기 (방장만)
        blocked_list = []
        kicked_list = []
        if is_owner:
            try:
                blocked_ref = db.reference(f'rooms/{room_id}/blocked_users')
                blocked_data = blocked_ref.get()
                if blocked_data:
                    for nickname, data in blocked_data.items():
                        blocked_list.append(nickname)
            except:
                pass
                
            try:
                kicked_ref = db.reference(f'rooms/{room_id}/kicked_users')
                kicked_data = kicked_ref.get()
                if kicked_data:
                    for nickname, data in kicked_data.items():
                        kicked_list.append(nickname)
            except:
                pass
        
        # 설정 다이얼로그 내용
        settings_content = ft.Column([
            ft.Text("채팅방 관리", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"방 제목: {display_room_title}", size=14),
            ft.Text(f"방 ID: {room_id}", size=12, color=ft.Colors.GREY_600),
            ft.Text(f"방장: {current_nickname if is_owner else '다른 사용자'}", size=12, color=ft.Colors.GREEN_600 if is_owner else ft.Colors.GREY_600),
            ft.Divider(),
            # 방장 전용 기능들
            ft.Text("방장 전용 기능", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600) if is_owner else ft.Container(),
            ft.Text("차단된 사용자", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(f"총 {len(blocked_list)}명", size=12, color=ft.Colors.GREY_600),
            ft.ElevatedButton(
                "차단 목록 보기",
                on_click=lambda e: show_blocked_users(blocked_list),
                style=ft.ButtonStyle(bgcolor=ft.Colors.RED_50, color=ft.Colors.RED_700)
            ) if is_owner and blocked_list else ft.Text("차단된 사용자가 없습니다.", size=12, color=ft.Colors.GREY_500) if is_owner else ft.Container(),
            ft.Text("추방된 사용자", size=14, weight=ft.FontWeight.BOLD) if is_owner else ft.Container(),
            ft.Text(f"총 {len(kicked_list)}명", size=12, color=ft.Colors.GREY_600) if is_owner else ft.Container(),
            ft.ElevatedButton(
                "추방 목록 보기",
                on_click=lambda e: show_kicked_users(kicked_list),
                style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_50, color=ft.Colors.PURPLE_700)
            ) if is_owner and kicked_list else ft.Text("추방된 사용자가 없습니다.", size=12, color=ft.Colors.GREY_500) if is_owner else ft.Container(),
            ft.Divider(),
            ft.ElevatedButton(
                "채팅방 초기화",
                on_click=lambda e: clear_chat_history(),
                style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_50, color=ft.Colors.ORANGE_700)
            ) if is_owner else ft.Container(),
            ft.ElevatedButton("닫기", on_click=close_settings)
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # 오버레이로 표시
        settings_dialog = ft.Container(
            content=ft.Container(
                content=settings_content,
                padding=24,
                bgcolor=ft.Colors.WHITE,
                border_radius=16,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26)
            ),
            alignment=ft.alignment.center,
            expand=True
        )
        
        page.overlay.append(settings_dialog)
        page.update()
    
    def show_blocked_users(blocked_list):
        """차단된 사용자 목록 표시"""
        def unblock_user_from_list(nickname):
            unblock_user(nickname, room_id)
            # 목록 새로고침
            if page.overlay:
                page.overlay.pop()
                page.update()
            show_room_settings(None)
        
        # 방장 권한 재확인
        current_nickname = page.session.get('nickname') or ''
        current_user_id = page.session.get('user_id') or None
        is_owner = is_room_owner(room_id, current_nickname, current_user_id)
        
        if not is_owner:
            # 방장이 아니면 접근 거부
            page.snack_bar = ft.SnackBar(
                content=ft.Text("방장만 차단 목록을 볼 수 있습니다."),
                action="확인"
            )
            page.snack_bar.open = True
            page.update()
            return
        
        blocked_content = ft.Column([
            ft.Text("차단된 사용자 목록", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("방장 전용 기능", size=12, color=ft.Colors.BLUE_600),
            ft.Divider(),
            *[ft.Row([
                ft.Text(nickname, size=14),
                ft.ElevatedButton(
                    "차단 해제",
                    on_click=lambda e, n=nickname: unblock_user_from_list(n),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_50, color=ft.Colors.GREEN_700)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN) for nickname in blocked_list],
            ft.ElevatedButton("뒤로가기", on_click=lambda e: [page.overlay.pop(), page.update()])
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        blocked_dialog = ft.Container(
            content=ft.Container(
                content=blocked_content,
                padding=24,
                bgcolor=ft.Colors.WHITE,
                border_radius=16,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26)
            ),
            alignment=ft.alignment.center,
            expand=True
        )
        
        page.overlay.append(blocked_dialog)
        page.update()

    def show_kicked_users(kicked_list):
        """추방된 사용자 목록 표시"""
        def unkick_user_from_list(nickname):
            unkick_user(nickname, room_id)
            # 다이얼로그 새로고침
            page.overlay.clear()
            page.update()
            # 설정 다시 열기
            show_room_settings(None)

        # 방장 권한 재확인
        current_nickname = page.session.get('nickname') or ''
        current_user_id = page.session.get('user_id') or None
        is_owner = is_room_owner(room_id, current_nickname, current_user_id)

        if not is_owner:
            # 방장이 아니면 접근 거부
            access_denied = ft.AlertDialog(
                content=ft.Text("방장만 추방 목록을 볼 수 있습니다."),
                actions=[ft.TextButton("확인", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update())]
            )
            page.dialog = access_denied
            page.dialog.open = True
            page.update()
            return

        kicked_content = ft.Column([
            ft.Text("추방된 사용자 목록", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("방장 전용 기능", size=12, color=ft.Colors.PURPLE_600),
            ft.Divider(),
            *[ft.Row([
                ft.Text(nickname, size=14),
                ft.ElevatedButton(
                    "추방 해제",
                    on_click=lambda e, n=nickname: unkick_user_from_list(n),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_50, color=ft.Colors.GREEN_700)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN) for nickname in kicked_list],
            ft.Container(height=10),
            ft.ElevatedButton("닫기", on_click=lambda e: page.overlay.clear() or page.update())
        ], spacing=8)

        kicked_dialog = ft.Container(
            content=ft.Container(
                content=kicked_content,
                bgcolor=ft.Colors.WHITE,
                padding=20,
                border_radius=10,
                width=300,
                border=ft.border.all(1, ft.Colors.GREY_300)
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK54
        )

        page.overlay.append(kicked_dialog)
        page.update()
    
    def clear_chat_history():
        """채팅 기록 초기화"""
        # 방장 권한 확인
        current_nickname = page.session.get('nickname') or ''
        current_user_id = page.session.get('user_id') or None
        is_owner = is_room_owner(room_id, current_nickname, current_user_id)
        
        if not is_owner:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("방장만 채팅 기록을 초기화할 수 있습니다."),
                action="확인"
            )
            page.snack_bar.open = True
            page.update()
            return
        
        def confirm_clear(e):
            nonlocal firebase_listener  # 외부 변수 접근
            try:
                # Firebase에서 메시지 삭제
                db.reference(f'rooms/{room_id}/messages').delete()
                
                # 화면 메시지 초기화
                chat_messages.controls.clear()
                
                # 현재 사용자 목록도 초기화 (입장/퇴장 메시지 방지)
                current_users.clear()
                
                # Firebase 리스너 재설정 (기존 리스너 제거 후 새로 설정)
                if firebase_listener and firebase_available:
                    try:
                        firebase_listener.close()  # 기존 리스너 제거
                    except:
                        pass
                    # 새 리스너 설정
                    firebase_listener = db.reference(f'rooms/{room_id}/messages').listen(on_message)
                
                # 페이지 업데이트
                page.update()
                
                # 확인 메시지 표시 (Firebase에 저장하지 않고 화면에만 표시)
                clear_msg_data = {
                    'text': "채팅 기록이 초기화되었습니다.",
                    'nickname': '시스템',
                    'timestamp': time.time(),
                    'translated': ''
                }
                clear_bubble = create_message_bubble(clear_msg_data, False)
                if clear_bubble:  # None이 아닌 경우만 처리
                    setattr(clear_bubble, 'timestamp', clear_msg_data['timestamp'])
                    chat_messages.controls.append(clear_bubble)
                    page.update()
                
                # 성공 메시지 표시
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("채팅 기록이 성공적으로 초기화되었습니다."),
                    action="확인",
                    duration=2000
                )
                page.snack_bar.open = True
                page.update()
                
                # 다이얼로그 닫기
                if page.dialog:
                    page.dialog.open = False
                    page.update()
                    
            except Exception as e:
                print(f"채팅 기록 초기화 오류: {e}")
                import traceback
                traceback.print_exc()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("채팅 기록 초기화 중 오류가 발생했습니다."),
                    action="확인"
                )
                page.snack_bar.open = True
                page.update()
        
        def cancel_clear(e):
            if page.dialog:
                page.dialog.open = False
                page.update()
        
        # 확인 다이얼로그 표시
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("채팅 기록 초기화"),
            content=ft.Text("정말로 모든 채팅 기록을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다."),
            actions=[
                ft.TextButton("취소", on_click=cancel_clear),
                ft.TextButton("초기화", on_click=confirm_clear, style=ft.ButtonStyle(color=ft.Colors.RED))
            ]
        )
        
        page.dialog = confirm_dialog
        confirm_dialog.open = True
        page.update()

    # 헤더 (뒤로가기 + 방 제목 + 설정 버튼 + 공유 버튼)
    display_room_title = rag_title if is_rag_room else (
        QUICK_ROOM_TITLES.get(user_lang, "Quick Chat Room") if room_title in ["빠른 채팅방", "Quick Chat Room"] else room_title
    )
    
    # 방장 권한 확인
    current_nickname = page.session.get('nickname') or ''
    current_user_id = page.session.get('user_id')
    is_owner = is_room_owner(room_id, current_nickname, current_user_id)
    
    # 방장 표시 추가
    title_with_owner = f"{display_room_title} {'👑' if is_owner else ''}"
    
    header = ft.Container(
        content=ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back),
            ft.Text(title_with_owner, size=title_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87, expand=True, selectable=True),
            ft.IconButton(ft.Icons.SETTINGS, on_click=show_room_settings, tooltip="채팅방 관리"),
            ft.IconButton(ft.Icons.SHARE, on_click=on_share) if on_share else ft.Container(),
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=header_padding,
        bgcolor=ft.Colors.WHITE,
        border_radius=8 if is_mobile else 10,
        margin=ft.margin.only(bottom=8),
        shadow=ft.BoxShadow(blur_radius=4, color="#B0BEC544")
    )

    # 언어별 마이크 안내 메시지
    MIC_GUIDE_TEXTS = {
        "ko": "키보드의 마이크 버튼을 눌러 음성 입력을 사용하세요!",
        "en": "Tap the microphone button on your keyboard to use voice input!",
        "ja": "キーボードのマイクボタンを押して音声入力を使ってください！",
        "zh": "请点击键盘上的麦克风按钮进行语音输入！",
        "zh-TW": "請點擊鍵盤上的麥克風按鈕進行語音輸入！",
        "id": "Tekan tombol mikrofon di keyboard untuk menggunakan input suara!",
        "vi": "Nhấn nút micro trên bàn phím để nhập bằng giọng nói!",
        "fr": "Appuyez sur le bouton micro du clavier pour utiliser la saisie vocale !",
        "de": "Tippen Sie auf die Mikrofontaste Ihrer Tastatur, um die Spracheingabe zu verwenden!",
        "th": "แตะปุ่มไมโครโฟนบนแป้นพิมพ์เพื่อใช้การป้อนด้วยเสียง!"
    }
    # AlertDialog 미리 생성
    mic_dialog = ft.AlertDialog(title=ft.Text(""), modal=True)

    def focus_input_box(e):
        input_box.focus()
        guide_text = MIC_GUIDE_TEXTS.get(user_lang, MIC_GUIDE_TEXTS["en"])
        mic_dialog.title = ft.Text(guide_text)
        mic_dialog.open = True
        page.update()
        # 3초 후 자동 닫힘
        def close_dialog():
            import time
            time.sleep(3)
            mic_dialog.open = False
            page.update()
        threading.Thread(target=close_dialog, daemon=True).start()

    # 입력 영역
    input_row = ft.Row([
        input_box,
        ft.IconButton(
            ft.Icons.MIC,
            on_click=focus_input_box,
            tooltip="음성 입력(키보드 마이크 버튼 사용)"
        ) if not IS_SERVER else ft.Container(),
        ft.IconButton(
            ft.Icons.SEND,
            on_click=send_message,
            tooltip="전송"
        ),
    ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # 입력창 위에 드롭다운 항상 표시
    input_area = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("답변 언어:", size=14, weight=ft.FontWeight.BOLD),
                target_lang_dropdown
            ], alignment=ft.MainAxisAlignment.START, spacing=12),
            padding=8 if is_mobile else 12,
            margin=ft.margin.only(bottom=4)
        ),
        input_row
    ], spacing=4)

    # chat_column을 스크롤 가능하게 만듦
    if is_rag_room:
        chat_column = ft.Column(
            controls=[get_rag_guide_message(), chat_messages],
            expand=True,
            spacing=0,
            scroll=ft.ScrollMode.ALWAYS
        )
    else:
        chat_column = ft.Column(
            controls=[chat_messages],
            expand=True,
            scroll=ft.ScrollMode.ALWAYS
        )

    # chat_area는 scroll 없이 Container만 사용
    chat_area = ft.Container(
        content=chat_column,
        expand=True,
        padding=8 if is_mobile else 12,
        bgcolor="#F6F8FC",
        border_radius=16,
        margin=ft.margin.only(bottom=8, left=8, right=8, top=8),
        border=ft.border.all(1, "#E0E7EF"),
        alignment=ft.alignment.center,
        width=min(page.width, 900)
    )

    # --- 채팅방 입장 시 시스템 메시지 push 함수 ---
    def push_join_system_message():
        nickname = page.session.get('nickname') or ''
        if not (firebase_available and nickname and nickname not in ['익명', 'RAG', '시스템']):
            return
        try:
            messages_ref = db.reference(f'rooms/{room_id}/messages')
            messages = messages_ref.get()
            import time
            now = time.time()
            # 1. 방장(최초 입장자)만 예외 처리: 방에 메시지가 0개이고, 내가 방을 만든 사람일 때만 return
            if not messages or len(messages) == 0:
                # 방장 여부는 room_id 생성 직후 바로 입장하는 경우로 추정 (정확히 하려면 DB에 생성자 정보 필요)
                # 일단 최초 입장자만 안내 메시지 push 안 함
                return
            # 2. 최근 5분 내 같은 닉네임의 시스템 메시지가 이미 있으면 push 안 함 (시간 확대)
            for msg in messages.values():
                if (
                    msg.get('nickname') == '시스템'
                    and msg.get('text', '').startswith(f'{nickname}님이 채팅방에 들어왔습니다')
                    and now - float(msg.get('timestamp', 0)) < 300  # 5분으로 확대
                ):
                    print(f"중복 입장 메시지 방지: {nickname}")
                    return  # 중복 방지
            # 3. 안내 메시지 push (메시지 1개 이상이면 무조건 push)
            join_text = f"{nickname}님이 채팅방에 들어왔습니다."
            system_msg = {
                'text': join_text,
                'nickname': '시스템',
                'timestamp': now,
                'translated': ''
            }
            messages_ref.push(system_msg)
        except Exception as e:
            print(f"입장 시스템 메시지 push 오류: {e}")

    # --- 최초 진입 시 시스템 메시지 push ---
    push_join_system_message()

    # 전체 레이아웃
    return ft.View(
        f"/chat/{room_id}",
        controls=[
            header,
            chat_area,
            input_area,
        ],
        bgcolor="#F5F7FF",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.END
    )

# 환경변수에서 firebase_key.json 내용을 읽어서 파일로 저장
firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
if firebase_key_json:
    with open("firebase_key.json", "w", encoding="utf-8") as f:
        f.write(firebase_key_json)

# 차단된 사용자 목록 (세션별로 관리)
BLOCKED_USERS = set()

def block_user(nickname, room_id):
    """사용자 차단"""
    BLOCKED_USERS.add(nickname)
    # Firebase에 차단 정보 저장
    try:
        db.reference(f'rooms/{room_id}/blocked_users').child(nickname).set({
            'blocked_at': time.time(),
            'blocked_by': '방장'
        })
        print(f"사용자 {nickname} 차단됨")
    except Exception as e:
        print(f"차단 정보 저장 오류: {e}")

def unblock_user(nickname, room_id):
    """사용자 차단 해제"""
    BLOCKED_USERS.discard(nickname)
    # Firebase에서 차단 정보 삭제
    try:
        db.reference(f'rooms/{room_id}/blocked_users').child(nickname).delete()
        print(f"사용자 {nickname} 차단 해제됨")
    except Exception as e:
        print(f"차단 해제 오류: {e}")

def is_user_blocked(nickname):
    """사용자가 차단되었는지 확인"""
    return nickname in BLOCKED_USERS

def is_room_owner(room_id, nickname, user_id=None):
    """방장인지 확인"""
    try:
        room_ref = db.reference(f'/rooms/{room_id}')
        room_data = room_ref.get()
        if room_data:
            # 닉네임으로 확인
            if room_data.get('created_by') == nickname:
                return True
            # 사용자 ID로 확인 (더 정확함)
            if user_id and room_data.get('creator_id') == user_id:
                return True
        return False
    except Exception as e:
        print(f"방장 권한 확인 오류: {e}")
        return False

def is_user_kicked(nickname, room_id, firebase_available=True):
    """사용자가 추방되었는지 확인"""
    try:
        if firebase_available:
            kicked_ref = db.reference(f'rooms/{room_id}/kicked_users/{nickname}')
            kicked_data = kicked_ref.get()
            return kicked_data is not None
        return False
    except Exception as e:
        print(f"추방 확인 오류: {e}")
        return False

def unkick_user(nickname, room_id, firebase_available=True):
    """사용자 추방 해제"""
    try:
        if firebase_available:
            db.reference(f'rooms/{room_id}/kicked_users').child(nickname).delete()
            print(f"사용자 {nickname} 추방 해제됨")
        else:
            print("Firebase를 사용할 수 없어서 추방 해제할 수 없습니다.")
    except Exception as e:
        print(f"추방 해제 오류: {e}")
