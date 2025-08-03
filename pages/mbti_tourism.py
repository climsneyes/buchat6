import flet as ft
import json
import webbrowser
import requests


# TourAPI 관광사진 설정
TOUR_API_KEY = "rO5VJPog5TScnjUgCqneFaXfoep3fCsyR7VgL7dlQ1Ae99E/n3+ch8zmym+a1SIwylUd6Gj9L4E7B8txymXqMQ=="
TOUR_API_BASE_URL = "http://apis.data.go.kr/B551011/PhotoGalleryService1"

# AttractionService API 설정
ATTRACTION_API_BASE_URL = "http://apis.data.go.kr/6260000/AttractionService"

def get_attraction_photos_from_api(attraction_name, num_photos=3):
    """AttractionService API에서 관광지 사진 가져오기"""
    try:
        attraction_url = f"{ATTRACTION_API_BASE_URL}/getAttractionKr"
        params = {
            'serviceKey': TOUR_API_KEY,  # 동일한 키 사용
            'numOfRows': 50,
            'pageNo': 1,
            'resultType': 'json'
        }
        
        print(f"AttractionService API 요청: {attraction_name} 관광지 정보 검색 중...")
        response = requests.get(attraction_url, params=params, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if 'getAttractionKr' in data and 'item' in data['getAttractionKr']:
                    items = data['getAttractionKr']['item']
                    if not isinstance(items, list):
                        items = [items]
                    
                    print(f"AttractionService에서 {len(items)}개 관광지 정보를 받았습니다.")
                    
                    # 관광지 이름으로 매칭되는 항목 찾기
                    matched_photos = []
                    search_keywords = [
                        attraction_name,
                        attraction_name.replace("해수욕장", ""),
                        attraction_name.replace("문화마을", ""),
                        attraction_name.replace(" ", "")
                    ]
                    
                    for item in items:
                        title = item.get('TITLE', '')
                        subtitle = item.get('SUBTITLE', '')
                        addr = item.get('ADDR1', '')
                        
                        # 이미지 URL 필드들 확인
                        main_img = item.get('MAIN_IMG_NORMAL', '')
                        thumb_img = item.get('MAIN_IMG_THUMB', '')
                        
                        # 제목이나 부제목, 주소에 관광지 이름이 포함되어 있는지 확인
                        is_match = False
                        for keyword in search_keywords:
                            if keyword and (keyword in title or keyword in subtitle or keyword in addr):
                                is_match = True
                                break
                        
                        if is_match:
                            print(f"  - 매칭된 관광지: {title}")
                            print(f"    주소: {addr}")
                            
                            # 이미지 URL 수집
                            if main_img and main_img.startswith('http'):
                                matched_photos.append(main_img)
                                print(f"    메인 이미지: {main_img}")
                            
                            if thumb_img and thumb_img.startswith('http') and thumb_img not in matched_photos:
                                matched_photos.append(thumb_img)
                                print(f"    썸네일 이미지: {thumb_img}")
                            
                            if len(matched_photos) >= num_photos:
                                break
                    
                    if matched_photos:
                        print(f"AttractionService에서 {attraction_name} 관련 이미지 {len(matched_photos)}개를 찾았습니다.")
                        return matched_photos[:num_photos]
                    else:
                        print(f"AttractionService에서 {attraction_name}에 매칭되는 이미지를 찾지 못했습니다.")
                else:
                    print("AttractionService 응답 구조가 예상과 다릅니다.")
            
            except Exception as json_error:
                print(f"AttractionService JSON 파싱 오류: {json_error}")
                print(f"응답 내용 (처음 500자): {response.text[:500]}")
        else:
            print(f"AttractionService API 요청 실패: HTTP {response.status_code}")
            print(f"응답 내용: {response.text[:200]}")
        
        return []
        
    except Exception as e:
        print(f"AttractionService API 오류: {e}")
        return []

def get_tour_photos_from_api(attraction_name, num_photos=3):
    """TourAPI에서 관광지 사진 가져오기 (제목 필터링 방식)"""
    try:
        gallery_url = f"{TOUR_API_BASE_URL}/galleryList1"
        params = {
            'serviceKey': TOUR_API_KEY,
            'numOfRows': 100,  # 더 많은 사진을 가져와서 필터링
            'pageNo': 1,
            'MobileOS': 'ETC',
            'MobileApp': 'BusanTourChat',
            '_type': 'json',
            'arrange': 'A'
            # title 파라미터 제거하고 전체 갤러리에서 필터링
        }
        
        response = requests.get(gallery_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'response' in data and 'body' in data['response']:
                body = data['response']['body']
                if 'items' in body and body['items']:
                    items = body['items']['item']
                    if not isinstance(items, list):
                        items = [items]
                    
                    # 관광지 이름이 포함된 사진들만 필터링
                    tour_photos = []
                    
                    print(f"TourAPI 요청: 전체 갤러리에서 {attraction_name} 관련 사진 필터링 중...")
                    print(f"전체 갤러리 항목 수: {len(items)}")
                    
                    # 관광지 이름의 다양한 형태로 검색
                    search_keywords = [
                        attraction_name,
                        attraction_name.replace("해수욕장", ""),
                        attraction_name.replace("문화마을", ""),
                        attraction_name.replace(" ", "")
                    ]
                    
                    for item in items:
                        title = item.get('galTitle', '')
                        location = item.get('galPhotographyLocation', '')
                        image_url = item.get('galWebImageUrl', '')
                        
                        # 제목이나 촬영지에 관광지 이름이 포함되어 있는지 확인
                        is_match = False
                        for keyword in search_keywords:
                            if keyword and (keyword in title or keyword in location):
                                is_match = True
                                break
                        
                        if is_match and image_url and image_url.startswith('http'):
                            tour_photos.append(image_url)
                            print(f"  - 매칭된 사진: {title} (촬영지: {location})")
                            if len(tour_photos) >= num_photos:
                                break
                    
                    if tour_photos:
                        print(f"TourAPI에서 {attraction_name} 관련 사진 {len(tour_photos)}개를 찾았습니다.")
                        return tour_photos[:num_photos]
                    else:
                        print(f"TourAPI에서 {attraction_name}에 대한 매칭 사진을 찾지 못했습니다.")
                
                else:
                    print(f"TourAPI 응답에 사진이 없습니다.")
            else:
                print(f"TourAPI 응답 구조가 예상과 다릅니다.")
        else:
            print(f"TourAPI 요청 실패: HTTP {response.status_code}")
        
        return []
        
    except Exception as e:
        print(f"TourAPI 사진 가져오기 오류: {e}")
        return []

def get_reliable_fallback_images(attraction_name, num_photos=3):
    """안정적인 대체 이미지 제공 (단순 텍스트 기반)"""
    # 가장 간단하고 확실한 방법: 텍스트만 사용
    fallback_images = []
    
    for i in range(num_photos):
        fallback_images.append(f"NO_IMAGE_{attraction_name}_{i+1}")
    
    return fallback_images[:num_photos]

# 전역 변수로 상태 관리
_global_selected_mbti = None
_global_result_view = None
_global_current_lang = None

# MBTI 테스트 질문 데이터 (간단한 12개 질문)
MBTI_TEST_QUESTIONS = {
    "ko": [
        {"question": "모임에서 당신은?", "options": [{"text": "사람들과 활발하게 대화한다", "type": "E"}, {"text": "조용히 듣고 있는 편이다", "type": "I"}]},
        {"question": "여행 계획을 세울 때?", "options": [{"text": "미리 자세히 계획한다", "type": "J"}, {"text": "즉흥적으로 결정한다", "type": "P"}]},
        {"question": "결정을 내릴 때?", "options": [{"text": "논리와 사실을 중요시한다", "type": "T"}, {"text": "감정과 가치를 중요시한다", "type": "F"}]},
        {"question": "새로운 아이디어를 접할 때?", "options": [{"text": "현실적 가능성을 먼저 생각한다", "type": "S"}, {"text": "새로운 가능성에 흥미를 느낀다", "type": "N"}]},
        {"question": "친구들과 만날 때?", "options": [{"text": "큰 그룹이 좋다", "type": "E"}, {"text": "소수의 친한 친구가 좋다", "type": "I"}]},
        {"question": "일을 처리할 때?", "options": [{"text": "체계적이고 계획적으로 한다", "type": "J"}, {"text": "유연하게 상황에 맞춰 한다", "type": "P"}]},
        {"question": "갈등 상황에서?", "options": [{"text": "객관적 분석을 통해 해결한다", "type": "T"}, {"text": "사람들의 감정을 고려해 해결한다", "type": "F"}]},
        {"question": "정보를 받아들일 때?", "options": [{"text": "구체적이고 실용적인 것을 선호한다", "type": "S"}, {"text": "추상적이고 이론적인 것을 선호한다", "type": "N"}]},
        {"question": "에너지를 얻는 방법은?", "options": [{"text": "사람들과 함께 있을 때", "type": "E"}, {"text": "혼자만의 시간을 가질 때", "type": "I"}]},
        {"question": "마감일이 있는 일은?", "options": [{"text": "미리미리 끝내는 편이다", "type": "J"}, {"text": "마감일에 임박해서 한다", "type": "P"}]},
        {"question": "비판을 받을 때?", "options": [{"text": "내용의 타당성을 먼저 본다", "type": "T"}, {"text": "말하는 사람의 의도를 먼저 본다", "type": "F"}]},
        {"question": "미래를 상상할 때?", "options": [{"text": "현재의 연장선에서 생각한다", "type": "S"}, {"text": "완전히 다른 가능성을 상상한다", "type": "N"}]}
    ],
    "en": [
        {"question": "At gatherings, you:", "options": [{"text": "Actively chat with people", "type": "E"}, {"text": "Prefer to listen quietly", "type": "I"}]},
        {"question": "When planning a trip:", "options": [{"text": "Plan everything in detail beforehand", "type": "J"}, {"text": "Decide spontaneously", "type": "P"}]},
        {"question": "When making decisions:", "options": [{"text": "Focus on logic and facts", "type": "T"}, {"text": "Focus on feelings and values", "type": "F"}]},
        {"question": "When encountering new ideas:", "options": [{"text": "Think about practical possibilities first", "type": "S"}, {"text": "Get excited about new possibilities", "type": "N"}]},
        {"question": "When meeting friends:", "options": [{"text": "Prefer large groups", "type": "E"}, {"text": "Prefer small groups of close friends", "type": "I"}]},
        {"question": "When handling tasks:", "options": [{"text": "Work systematically and planned", "type": "J"}, {"text": "Work flexibly according to situation", "type": "P"}]},
        {"question": "In conflict situations:", "options": [{"text": "Resolve through objective analysis", "type": "T"}, {"text": "Consider people's feelings to resolve", "type": "F"}]},
        {"question": "When receiving information:", "options": [{"text": "Prefer concrete and practical", "type": "S"}, {"text": "Prefer abstract and theoretical", "type": "N"}]},
        {"question": "How do you gain energy:", "options": [{"text": "When with people", "type": "E"}, {"text": "When having alone time", "type": "I"}]},
        {"question": "Tasks with deadlines:", "options": [{"text": "Finish well in advance", "type": "J"}, {"text": "Work close to deadline", "type": "P"}]},
        {"question": "When receiving criticism:", "options": [{"text": "Look at validity of content first", "type": "T"}, {"text": "Look at speaker's intention first", "type": "F"}]},
        {"question": "When imagining the future:", "options": [{"text": "Think as extension of present", "type": "S"}, {"text": "Imagine completely different possibilities", "type": "N"}]}
    ],
    "zh": [
        {"question": "在聚会中，你会？", "options": [{"text": "积极与人交流", "type": "E"}, {"text": "安静地倾听", "type": "I"}]},
        {"question": "制定旅行计划时？", "options": [{"text": "提前详细规划", "type": "J"}, {"text": "即兴决定", "type": "P"}]},
        {"question": "做决定时？", "options": [{"text": "重视逻辑和事实", "type": "T"}, {"text": "重视情感和价值观", "type": "F"}]},
        {"question": "接触新想法时？", "options": [{"text": "首先考虑现实可能性", "type": "S"}, {"text": "对新可能性感兴趣", "type": "N"}]},
        {"question": "与朋友聚会时？", "options": [{"text": "喜欢大团体", "type": "E"}, {"text": "喜欢少数亲密朋友", "type": "I"}]},
        {"question": "处理工作时？", "options": [{"text": "系统性地有计划地进行", "type": "J"}, {"text": "灵活地根据情况调整", "type": "P"}]},
        {"question": "在冲突情况下？", "options": [{"text": "通过客观分析解决", "type": "T"}, {"text": "考虑他人感受解决", "type": "F"}]},
        {"question": "接收信息时？", "options": [{"text": "偏好具体实用的", "type": "S"}, {"text": "偏好抽象理论的", "type": "N"}]},
        {"question": "获得能量的方式？", "options": [{"text": "与人相处时", "type": "E"}, {"text": "独处时", "type": "I"}]},
        {"question": "有截止日期的工作？", "options": [{"text": "提前完成", "type": "J"}, {"text": "临近截止日期才做", "type": "P"}]},
        {"question": "受到批评时？", "options": [{"text": "首先看内容的合理性", "type": "T"}, {"text": "首先看说话者的意图", "type": "F"}]},
        {"question": "想象未来时？", "options": [{"text": "从现在的延续来思考", "type": "S"}, {"text": "想象完全不同的可能性", "type": "N"}]}
    ],
    "zh-TW": [
        {"question": "在聚會中，你會？", "options": [{"text": "積極與人交流", "type": "E"}, {"text": "安靜地傾聽", "type": "I"}]},
        {"question": "制定旅行計劃時？", "options": [{"text": "提前詳細規劃", "type": "J"}, {"text": "即興決定", "type": "P"}]},
        {"question": "做決定時？", "options": [{"text": "重視邏輯和事實", "type": "T"}, {"text": "重視情感和價值觀", "type": "F"}]},
        {"question": "接觸新想法時？", "options": [{"text": "首先考慮現實可能性", "type": "S"}, {"text": "對新可能性感興趣", "type": "N"}]},
        {"question": "與朋友聚會時？", "options": [{"text": "喜歡大團體", "type": "E"}, {"text": "喜歡少數親密朋友", "type": "I"}]},
        {"question": "處理工作時？", "options": [{"text": "系統性地有計劃地進行", "type": "J"}, {"text": "靈活地根據情況調整", "type": "P"}]},
        {"question": "在衝突情況下？", "options": [{"text": "通過客觀分析解決", "type": "T"}, {"text": "考慮他人感受解決", "type": "F"}]},
        {"question": "接收信息時？", "options": [{"text": "偏好具體實用的", "type": "S"}, {"text": "偏好抽象理論的", "type": "N"}]},
        {"question": "獲得能量的方式？", "options": [{"text": "與人相處時", "type": "E"}, {"text": "獨處時", "type": "I"}]},
        {"question": "有截止日期的工作？", "options": [{"text": "提前完成", "type": "J"}, {"text": "臨近截止日期才做", "type": "P"}]},
        {"question": "受到批評時？", "options": [{"text": "首先看內容的合理性", "type": "T"}, {"text": "首先看說話者的意圖", "type": "F"}]},
        {"question": "想象未來時？", "options": [{"text": "從現在的延續來思考", "type": "S"}, {"text": "想象完全不同的可能性", "type": "N"}]}
    ],
    "ja": [
        {"question": "集まりでは？", "options": [{"text": "人々と積極的に話す", "type": "E"}, {"text": "静かに聞いている", "type": "I"}]},
        {"question": "旅行計画を立てる時？", "options": [{"text": "事前に詳しく計画する", "type": "J"}, {"text": "即興で決める", "type": "P"}]},
        {"question": "決定を下す時？", "options": [{"text": "論理と事実を重視する", "type": "T"}, {"text": "感情と価値を重視する", "type": "F"}]},
        {"question": "新しいアイデアに接する時？", "options": [{"text": "現実的可能性を先に考える", "type": "S"}, {"text": "新しい可能性に興味を持つ", "type": "N"}]},
        {"question": "友達と会う時？", "options": [{"text": "大きなグループが良い", "type": "E"}, {"text": "少数の親しい友達が良い", "type": "I"}]},
        {"question": "仕事を処理する時？", "options": [{"text": "体系的で計画的に行う", "type": "J"}, {"text": "柔軟に状況に合わせる", "type": "P"}]},
        {"question": "対立状況では？", "options": [{"text": "客観的分析で解決する", "type": "T"}, {"text": "人々の感情を考慮して解決する", "type": "F"}]},
        {"question": "情報を受け取る時？", "options": [{"text": "具体的で実用的なものを好む", "type": "S"}, {"text": "抽象的で理論的なものを好む", "type": "N"}]},
        {"question": "エネルギーを得る方法は？", "options": [{"text": "人々と一緒にいる時", "type": "E"}, {"text": "一人の時間を持つ時", "type": "I"}]},
        {"question": "締切のある仕事は？", "options": [{"text": "早めに終わらせる", "type": "J"}, {"text": "締切間近にする", "type": "P"}]},
        {"question": "批判を受ける時？", "options": [{"text": "内容の妥当性を先に見る", "type": "T"}, {"text": "話す人の意図を先に見る", "type": "F"}]},
        {"question": "未来を想像する時？", "options": [{"text": "現在の延長線で考える", "type": "S"}, {"text": "全く違う可能性を想像する", "type": "N"}]}
    ],
    "vi": [
        {"question": "Trong các cuộc tụ họp, bạn?", "options": [{"text": "Tích cực trò chuyện với mọi người", "type": "E"}, {"text": "Thích lắng nghe yên lặng", "type": "I"}]},
        {"question": "Khi lên kế hoạch du lịch?", "options": [{"text": "Lập kế hoạch chi tiết trước", "type": "J"}, {"text": "Quyết định tức thời", "type": "P"}]},
        {"question": "Khi đưa ra quyết định?", "options": [{"text": "Tập trung vào logic và sự thật", "type": "T"}, {"text": "Tập trung vào cảm xúc và giá trị", "type": "F"}]},
        {"question": "Khi tiếp xúc với ý tưởng mới?", "options": [{"text": "Nghĩ về khả năng thực tế trước", "type": "S"}, {"text": "Hứng thú với khả năng mới", "type": "N"}]},
        {"question": "Khi gặp bạn bè?", "options": [{"text": "Thích nhóm lớn", "type": "E"}, {"text": "Thích nhóm nhỏ bạn thân", "type": "I"}]},
        {"question": "Khi xử lý công việc?", "options": [{"text": "Làm việc có hệ thống và có kế hoạch", "type": "J"}, {"text": "Làm việc linh hoạt theo tình huống", "type": "P"}]},
        {"question": "Trong tình huống xung đột?", "options": [{"text": "Giải quyết bằng phân tích khách quan", "type": "T"}, {"text": "Xem xét cảm xúc của mọi người để giải quyết", "type": "F"}]},
        {"question": "Khi tiếp nhận thông tin?", "options": [{"text": "Thích cụ thể và thực tế", "type": "S"}, {"text": "Thích trừu tượng và lý thuyết", "type": "N"}]},
        {"question": "Cách bạn có được năng lượng?", "options": [{"text": "Khi ở với mọi người", "type": "E"}, {"text": "Khi có thời gian một mình", "type": "I"}]},
        {"question": "Công việc có thời hạn?", "options": [{"text": "Hoàn thành sớm", "type": "J"}, {"text": "Làm gần thời hạn", "type": "P"}]},
        {"question": "Khi nhận phê bình?", "options": [{"text": "Xem tính hợp lệ của nội dung trước", "type": "T"}, {"text": "Xem ý định của người nói trước", "type": "F"}]},
        {"question": "Khi tưởng tượng tương lai?", "options": [{"text": "Nghĩ như phần mở rộng của hiện tại", "type": "S"}, {"text": "Tưởng tượng những khả năng hoàn toàn khác", "type": "N"}]}
    ],
    "th": [
        {"question": "ในการรวมตัวของคุณ?", "options": [{"text": "คุยกับคนอื่นอย่างกระตือรือร้น", "type": "E"}, {"text": "ชอบฟังอย่างเงียบๆ", "type": "I"}]},
        {"question": "เมื่อวางแผนการเดินทาง?", "options": [{"text": "วางแผนล่วงหน้าอย่างละเอียด", "type": "J"}, {"text": "ตัดสินใจแบบฉับพลัน", "type": "P"}]},
        {"question": "เมื่อตัดสินใจ?", "options": [{"text": "เน้นที่ตรรกะและข้อเท็จจริง", "type": "T"}, {"text": "เน้นที่อารมณ์และค่านิยม", "type": "F"}]},
        {"question": "เมื่อสัมผัสแนวคิดใหม่?", "options": [{"text": "คิดถึงความเป็นไปได้ในทางปฏิบัติก่อน", "type": "S"}, {"text": "สนใจในความเป็นไปได้ใหม่ๆ", "type": "N"}]},
        {"question": "เมื่อพบเพื่อน?", "options": [{"text": "ชอบกลุ่มใหญ่", "type": "E"}, {"text": "ชอบกลุ่มเล็กของเพื่อนสนิท", "type": "I"}]},
        {"question": "เมื่อจัดการงาน?", "options": [{"text": "ทำงานอย่างเป็นระบบและมีแผน", "type": "J"}, {"text": "ทำงานอย่างยืดหยุ่นตามสถานการณ์", "type": "P"}]},
        {"question": "ในสถานการณ์ขัดแย้ง?", "options": [{"text": "แก้ไขด้วยการวิเคราะห์อย่างเป็นกลาง", "type": "T"}, {"text": "พิจารณาความรู้สึกของทุกคนเพื่อแก้ไข", "type": "F"}]},
        {"question": "เมื่อรับข้อมูล?", "options": [{"text": "ชอบที่เป็นรูปธรรมและปฏิบัติได้", "type": "S"}, {"text": "ชอบที่เป็นนามธรรมและทฤษฎี", "type": "N"}]},
        {"question": "วิธีที่คุณได้รับพลังงาน?", "options": [{"text": "เมื่ออยู่กับคนอื่น", "type": "E"}, {"text": "เมื่อมีเวลาอยู่คนเดียว", "type": "I"}]},
        {"question": "งานที่มีกำหนดเวลา?", "options": [{"text": "เสร็จเร็ว", "type": "J"}, {"text": "ทำใกล้กำหนดเวลา", "type": "P"}]},
        {"question": "เมื่อได้รับการวิจารณ์?", "options": [{"text": "ดูความถูกต้องของเนื้อหาก่อน", "type": "T"}, {"text": "ดูความตั้งใจของผู้พูดก่อน", "type": "F"}]},
        {"question": "เมื่อจินตนาการถึงอนาคต?", "options": [{"text": "คิดเป็นส่วนขยายของปัจจุบัน", "type": "S"}, {"text": "จินตนาการความเป็นไปได้ที่แตกต่างไปโดยสิ้นเชิง", "type": "N"}]}
    ],
    "id": [
        {"question": "Di pertemuan, Anda?", "options": [{"text": "Berbicara aktif dengan orang lain", "type": "E"}, {"text": "Lebih suka mendengarkan dengan tenang", "type": "I"}]},
        {"question": "Saat merencanakan perjalanan?", "options": [{"text": "Merencanakan secara detail sebelumnya", "type": "J"}, {"text": "Memutuskan secara spontan", "type": "P"}]},
        {"question": "Saat mengambil keputusan?", "options": [{"text": "Fokus pada logika dan fakta", "type": "T"}, {"text": "Fokus pada emosi dan nilai", "type": "F"}]},
        {"question": "Saat menghadapi ide baru?", "options": [{"text": "Memikirkan kemungkinan praktis terlebih dahulu", "type": "S"}, {"text": "Tertarik dengan kemungkinan baru", "type": "N"}]},
        {"question": "Saat bertemu teman?", "options": [{"text": "Suka kelompok besar", "type": "E"}, {"text": "Suka kelompok kecil teman dekat", "type": "I"}]},
        {"question": "Saat menangani pekerjaan?", "options": [{"text": "Bekerja sistematis dan terencana", "type": "J"}, {"text": "Bekerja fleksibel sesuai situasi", "type": "P"}]},
        {"question": "Dalam situasi konflik?", "options": [{"text": "Menyelesaikan dengan analisis objektif", "type": "T"}, {"text": "Mempertimbangkan perasaan semua orang untuk menyelesaikan", "type": "F"}]},
        {"question": "Saat menerima informasi?", "options": [{"text": "Suka yang konkret dan praktis", "type": "S"}, {"text": "Suka yang abstrak dan teoritis", "type": "N"}]},
        {"question": "Cara Anda mendapatkan energi?", "options": [{"text": "Saat bersama orang lain", "type": "E"}, {"text": "Saat memiliki waktu sendiri", "type": "I"}]},
        {"question": "Pekerjaan dengan deadline?", "options": [{"text": "Selesai lebih awal", "type": "J"}, {"text": "Dikerjakan mendekati deadline", "type": "P"}]},
        {"question": "Saat menerima kritik?", "options": [{"text": "Melihat validitas isi terlebih dahulu", "type": "T"}, {"text": "Melihat niat pembicara terlebih dahulu", "type": "F"}]},
        {"question": "Saat membayangkan masa depan?", "options": [{"text": "Berpikir sebagai perpanjangan dari masa kini", "type": "S"}, {"text": "Membayangkan kemungkinan yang benar-benar berbeda", "type": "N"}]}
    ],
    "fr": [
        {"question": "Lors de réunions, vous?", "options": [{"text": "Parlez activement avec les autres", "type": "E"}, {"text": "Préférez écouter tranquillement", "type": "I"}]},
        {"question": "Lors de la planification d'un voyage?", "options": [{"text": "Planifiez en détail à l'avance", "type": "J"}, {"text": "Décidez spontanément", "type": "P"}]},
        {"question": "Lors de la prise de décision?", "options": [{"text": "Vous concentrez sur la logique et les faits", "type": "T"}, {"text": "Vous concentrez sur les émotions et les valeurs", "type": "F"}]},
        {"question": "Face à de nouvelles idées?", "options": [{"text": "Pensez d'abord aux possibilités pratiques", "type": "S"}, {"text": "Vous intéressez aux nouvelles possibilités", "type": "N"}]},
        {"question": "Quand vous rencontrez des amis?", "options": [{"text": "Aimez les grands groupes", "type": "E"}, {"text": "Aimez les petits groupes d'amis proches", "type": "I"}]},
        {"question": "En gérant le travail?", "options": [{"text": "Travaillez de manière systématique et planifiée", "type": "J"}, {"text": "Travaillez de manière flexible selon la situation", "type": "P"}]},
        {"question": "Dans des situations de conflit?", "options": [{"text": "Résolvez par une analyse objective", "type": "T"}, {"text": "Considérez les sentiments de chacun pour résoudre", "type": "F"}]},
        {"question": "Lors de la réception d'informations?", "options": [{"text": "Aimez le concret et pratique", "type": "S"}, {"text": "Aimez l'abstrait et théorique", "type": "N"}]},
        {"question": "Comment obtenez-vous de l'énergie?", "options": [{"text": "En étant avec d'autres personnes", "type": "E"}, {"text": "En ayant du temps seul", "type": "I"}]},
        {"question": "Travail avec échéances?", "options": [{"text": "Terminez tôt", "type": "J"}, {"text": "Travaillez près de l'échéance", "type": "P"}]},
        {"question": "Lors de la réception de critiques?", "options": [{"text": "Voyez d'abord la validité du contenu", "type": "T"}, {"text": "Voyez d'abord l'intention de l'orateur", "type": "F"}]},
        {"question": "En imaginant l'avenir?", "options": [{"text": "Pensez comme une extension du présent", "type": "S"}, {"text": "Imaginez des possibilités complètement différentes", "type": "N"}]}
    ],
    "de": [
        {"question": "Bei Versammlungen, Sie?", "options": [{"text": "Sprechen aktiv mit anderen", "type": "E"}, {"text": "Hören lieber ruhig zu", "type": "I"}]},
        {"question": "Bei der Reiseplanung?", "options": [{"text": "Planen im Voraus detailliert", "type": "J"}, {"text": "Entscheiden spontan", "type": "P"}]},
        {"question": "Bei Entscheidungen?", "options": [{"text": "Konzentrieren sich auf Logik und Fakten", "type": "T"}, {"text": "Konzentrieren sich auf Emotionen und Werte", "type": "F"}]},
        {"question": "Bei neuen Ideen?", "options": [{"text": "Denken zuerst an praktische Möglichkeiten", "type": "S"}, {"text": "Interessieren sich für neue Möglichkeiten", "type": "N"}]},
        {"question": "Beim Treffen von Freunden?", "options": [{"text": "Mögen große Gruppen", "type": "E"}, {"text": "Mögen kleine Gruppen enger Freunde", "type": "I"}]},
        {"question": "Bei der Arbeitsbewältigung?", "options": [{"text": "Arbeiten systematisch und geplant", "type": "J"}, {"text": "Arbeiten flexibel je nach Situation", "type": "P"}]},
        {"question": "In Konfliktsituationen?", "options": [{"text": "Lösen durch objektive Analyse", "type": "T"}, {"text": "Berücksichtigen die Gefühle aller zur Lösung", "type": "F"}]},
        {"question": "Beim Empfangen von Informationen?", "options": [{"text": "Mögen konkret und praktisch", "type": "S"}, {"text": "Mögen abstrakt und theoretisch", "type": "N"}]},
        {"question": "Wie gewinnen Sie Energie?", "options": [{"text": "Wenn Sie mit anderen zusammen sind", "type": "E"}, {"text": "Wenn Sie Zeit allein haben", "type": "I"}]},
        {"question": "Arbeit mit Fristen?", "options": [{"text": "Früh fertig", "type": "J"}, {"text": "Arbeiten nahe der Frist", "type": "P"}]},
        {"question": "Beim Empfangen von Kritik?", "options": [{"text": "Sehen zuerst die Gültigkeit des Inhalts", "type": "T"}, {"text": "Sehen zuerst die Absicht des Sprechers", "type": "F"}]},
        {"question": "Bei der Vorstellung der Zukunft?", "options": [{"text": "Denken als Erweiterung der Gegenwart", "type": "S"}, {"text": "Stellen sich völlig andere Möglichkeiten vor", "type": "N"}]}
    ],
    "tl": [
        {"question": "Sa mga pagtitipon, ikaw ay?", "options": [{"text": "Aktibong nakikipag-usap sa iba", "type": "E"}, {"text": "Mas gusto na makinig nang tahimik", "type": "I"}]},
        {"question": "Kapag nagpaplano ng biyahe?", "options": [{"text": "Nagpaplano nang detalyado nang maaga", "type": "J"}, {"text": "Nagdedesisyon nang biglaan", "type": "P"}]},
        {"question": "Kapag gumagawa ng desisyon?", "options": [{"text": "Nakatuon sa lohika at mga katotohanan", "type": "T"}, {"text": "Nakatuon sa mga damdamin at mga halaga", "type": "F"}]},
        {"question": "Kapag nakakaharap ng mga bagong ideya?", "options": [{"text": "Nag-iisip muna ng mga praktikal na posibilidad", "type": "S"}, {"text": "Nagiging interesado sa mga bagong posibilidad", "type": "N"}]},
        {"question": "Kapag nakikita ang mga kaibigan?", "options": [{"text": "Gusto ng malalaking grupo", "type": "E"}, {"text": "Gusto ng maliliit na grupo ng malapit na kaibigan", "type": "I"}]},
        {"question": "Kapag hinahawakan ang trabaho?", "options": [{"text": "Nagtatrabaho nang sistematiko at may plano", "type": "J"}, {"text": "Nagtatrabaho nang flexible ayon sa sitwasyon", "type": "P"}]},
        {"question": "Sa mga sitwasyong may salungatan?", "options": [{"text": "Nagresolba sa pamamagitan ng objektibong pagsusuri", "type": "T"}, {"text": "Isinasaalang-alang ang damdamin ng lahat para malutas", "type": "F"}]},
        {"question": "Kapag tumatanggap ng impormasyon?", "options": [{"text": "Gusto ng kongkreto at praktikal", "type": "S"}, {"text": "Gusto ng abstract at theoretical", "type": "N"}]},
        {"question": "Paano mo nakukuha ang enerhiya?", "options": [{"text": "Kapag kasama ng iba", "type": "E"}, {"text": "Kapag may oras mag-isa", "type": "I"}]},
        {"question": "Trabaho na may deadline?", "options": [{"text": "Natapos nang maaga", "type": "J"}, {"text": "Ginagawa malapit sa deadline", "type": "P"}]},
        {"question": "Kapag tumatanggap ng kritisismo?", "options": [{"text": "Tinitingnan muna ang bisa ng nilalaman", "type": "T"}, {"text": "Tinitingnan muna ang intensyon ng nagsasalita", "type": "F"}]},
        {"question": "Kapag naiisip ang hinaharap?", "options": [{"text": "Nag-iisip bilang extension ng kasalukuyan", "type": "S"}, {"text": "Naiisip ang mga posibilidad na ganap na iba", "type": "N"}]}
    ]
}

# MBTI 테스트 결과 계산 함수
def calculate_mbti_result(answers):
    """MBTI 테스트 답변을 기반으로 MBTI 유형을 계산합니다."""
    scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
    
    # 각 답변의 점수를 합산
    for answer in answers:
        scores[answer] += 1
    
    # 각 차원별로 더 높은 점수를 선택
    result = ""
    result += "E" if scores["E"] > scores["I"] else "I"
    result += "S" if scores["S"] > scores["N"] else "N"
    result += "T" if scores["T"] > scores["F"] else "F"
    result += "J" if scores["J"] > scores["P"] else "P"
    
    return result

# MBTI 테스트 화면을 위한 전역 변수
_test_answers = []
_current_question = 0

def show_mbti_test(page, lang, on_complete):
    """MBTI 테스트 화면을 표시합니다."""
    global _test_answers, _current_question
    _test_answers = []
    _current_question = 0
    
    # 테스트 질문 가져오기
    questions = MBTI_TEST_QUESTIONS.get(lang, MBTI_TEST_QUESTIONS["ko"])
    
    # 테스트 화면 텍스트
    test_texts = {
        "ko": {
            "title": "MBTI 성격 테스트",
            "subtitle": "12개의 간단한 질문으로 당신의 MBTI를 찾아보세요!",
            "progress": "진행률",
            "question": "질문",
            "back": "뒤로가기"
        },
        "en": {
            "title": "MBTI Personality Test",
            "subtitle": "Discover your MBTI with 12 simple questions!",
            "progress": "Progress",
            "question": "Question",
            "back": "Back"
        },
        "zh": {
            "title": "MBTI 性格测试",
            "subtitle": "通过12个简单问题找到您的MBTI！",
            "progress": "进度",
            "question": "问题",
            "back": "返回"
        },
        "zh-TW": {
            "title": "MBTI 性格測試",
            "subtitle": "通過12個簡單問題找到您的MBTI！",
            "progress": "進度",
            "question": "問題",
            "back": "返回"
        },
        "ja": {
            "title": "MBTI 性格テスト",
            "subtitle": "12の簡単な質問であなたのMBTIを見つけましょう！",
            "progress": "進行率",
            "question": "質問",
            "back": "戻る"
        },
        "vi": {
            "title": "Bài kiểm tra tính cách MBTI",
            "subtitle": "Khám phá MBTI của bạn với 12 câu hỏi đơn giản!",
            "progress": "Tiến độ",
            "question": "Câu hỏi",
            "back": "Quay lại"
        },
        "th": {
            "title": "แบบทดสอบบุคลิกภาพ MBTI",
            "subtitle": "ค้นหา MBTI ของคุณด้วย 12 คำถามง่ายๆ!",
            "progress": "ความคืบหนา",
            "question": "คำถาม",
            "back": "ย้อนกลับ"
        },
        "id": {
            "title": "Tes Kepribadian MBTI",
            "subtitle": "Temukan MBTI Anda dengan 12 pertanyaan sederhana!",
            "progress": "Kemajuan",
            "question": "Pertanyaan",
            "back": "Kembali"
        },
        "fr": {
            "title": "Test de personnalité MBTI",
            "subtitle": "Découvrez votre MBTI avec 12 questions simples!",
            "progress": "Progrès",
            "question": "Question",
            "back": "Retour"
        },
        "de": {
            "title": "MBTI Persönlichkeitstest",
            "subtitle": "Entdecken Sie Ihr MBTI mit 12 einfachen Fragen!",
            "progress": "Fortschritt",
            "question": "Frage",
            "back": "Zurück"
        },
        "tl": {
            "title": "MBTI Personality Test",
            "subtitle": "Tuklasin ang inyong MBTI sa 12 simpleng tanong!",
            "progress": "Progreso",
            "question": "Tanong",
            "back": "Bumalik"
        }
    }
    
    t = test_texts.get(lang, test_texts["ko"])
    
    def on_answer_selected(answer_type):
        global _test_answers, _current_question
        _test_answers.append(answer_type)
        _current_question += 1
        
        if _current_question >= len(questions):
            # 테스트 완료 - 결과 계산
            mbti_result = calculate_mbti_result(_test_answers)
            on_complete(mbti_result)
        else:
            # 다음 질문으로
            show_test_question(page, lang, questions, t, on_complete)
    
    def show_test_question(page, lang, questions, t, on_complete):
        global _current_question
        current_q = questions[_current_question]
        progress = (_current_question + 1) / len(questions) * 100
        
        def back_to_main():
            global _test_answers, _current_question
            # 테스트 상태 초기화
            _test_answers = []
            _current_question = 0
            # 테스트 뷰를 제거하고 이전 MBTI 선택 화면으로 돌아가기
            if len(page.views) > 1:
                page.views.pop()  # 현재 테스트 뷰 제거
            page.update()
        
        # 기존 테스트 뷰가 있으면 업데이트, 없으면 새로 추가
        test_view = ft.View(
            "/mbti_test",
            controls=[
                    # 헤더
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: back_to_main()),
                        ft.Text(t["title"], size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                    
                    # 진행률 표시
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"{t['progress']}: {_current_question + 1}/{len(questions)}", 
                                   size=14, color=ft.Colors.GREY_600),
                            ft.ProgressBar(value=progress/100, width=300, height=8, 
                                         bgcolor=ft.Colors.GREY_300, color=ft.Colors.BLUE_600)
                        ], spacing=8),
                        margin=ft.margin.only(top=16, bottom=32)
                    ),
                    
                    # 질문
                    ft.Container(
                        content=ft.Text(f"{t['question']} {_current_question + 1}", 
                                      size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600),
                        margin=ft.margin.only(bottom=16)
                    ),
                    
                    ft.Container(
                        content=ft.Text(current_q["question"], size=18, weight=ft.FontWeight.BOLD,
                                      text_align=ft.TextAlign.CENTER),
                        margin=ft.margin.only(bottom=32)
                    ),
                    
                    # 선택지
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.ElevatedButton(
                                    content=ft.Text(current_q["options"][0]["text"], 
                                                   size=14, text_align=ft.TextAlign.CENTER),
                                    on_click=lambda e: on_answer_selected(current_q["options"][0]["type"]),
                                    width=350,
                                    height=60,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.BLUE_50,
                                        color=ft.Colors.BLUE_800,
                                        shape=ft.RoundedRectangleBorder(radius=12)
                                    )
                                ),
                                margin=ft.margin.only(bottom=16)
                            ),
                            ft.Container(
                                content=ft.ElevatedButton(
                                    content=ft.Text(current_q["options"][1]["text"], 
                                                   size=14, text_align=ft.TextAlign.CENTER),
                                    on_click=lambda e: on_answer_selected(current_q["options"][1]["type"]),
                                    width=350,
                                    height=60,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.GREEN_50,
                                        color=ft.Colors.GREEN_800,
                                        shape=ft.RoundedRectangleBorder(radius=12)
                                    )
                                )
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center
                    )
                ],
                bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                padding=ft.padding.symmetric(horizontal=20, vertical=16)
            )
        
        # 뷰 업데이트 또는 추가
        if len(page.views) > 0 and page.views[-1].route == "/mbti_test":
            page.views[-1] = test_view  # 기존 테스트 뷰 업데이트
        else:
            page.views.append(test_view)  # 새 테스트 뷰 추가
        page.update()
    
    # 첫 번째 질문 표시
    show_test_question(page, lang, questions, t, on_complete)

# 관광지별 TourAPI contentId 매핑 (부산 지역)
attraction_content_ids = {
    "범어사": "126508",
    "해운대 해수욕장": "126497", 
    "감천문화마을": "1454503",
    "광안리 해수욕장": "126548",
    "부산타워": "126609",
    "부산박물관": "126615",
    "국립해양박물관": "2026670",
    "롯데월드 어드벤처 부산": "2678944",
    "송도해상케이블카": "126622",
    "BIFF 거리": "126577",
    "자갈치시장": "126565",
    "해동용궁사": "126540",
    "태종대": "126624",
    "BTS 지민 아버지 카페 'MAGNATE'": None,  # API에 없음
    "흰여울문화마을": "2027715"
}

# 관광지 이름 다국어 매핑
attraction_name_mapping = {
    "ko": {
        "범어사": "범어사",
        "해운대 해수욕장": "해운대 해수욕장", 
        "감천문화마을": "감천문화마을",
        "광안리 해수욕장": "광안리 해수욕장",
        "부산타워": "부산타워",
        "부산박물관": "부산박물관",
        "국립해양박물관": "국립해양박물관",
        "롯데월드 어드벤처 부산": "롯데월드 어드벤처 부산",
        "송도해상케이블카": "송도해상케이블카",
        "BIFF 거리": "BIFF 거리",
        "자갈치시장": "자갈치시장",
        "해동용궁사": "해동용궁사",
        "태종대": "태종대",
        "BTS 지민 아버지 카페 'MAGNATE'": "BTS 지민 아버지 카페 'MAGNATE'",
        "흰여울문화마을": "흰여울문화마을",
        # MBTI 추천에서 추가된 관광지들
        "금정산성": "금정산성",
        "UN평화공원": "UN평화공원",
        "송도구름산책로": "송도구름산책로",
        "부산문화회관": "부산문화회관",
        "부산시립도서관": "부산시립도서관",
        "태종대 등대": "태종대 등대",
        "동래온천": "동래온천",
        "부산근현대역사관": "부산근현대역사관",
        "영화의전당": "영화의전당",
        "부산과학기술협의체": "부산과학기술협의체",
        "부산현대미술관": "부산현대미술관",
        "을숙도 생태공원": "을숙도 생태공원",
        "부산진시장": "부산진시장",
        "부산도서관": "부산도서관",
        "부산국제금융센터(BIFC)": "부산국제금융센터(BIFC)",
        "센텀시티": "센텀시티",
        "부산 벡스코": "부산 벡스코",
        "해운대 마린시티": "해운대 마린시티",
        "롯데백화점 센텀시티점": "롯데백화점 센텀시티점",
        "광안리 더 베이": "광안리 더 베이",
        "송도스카이워크": "송도스카이워크",
        "F1963 복합문화공간": "F1963 복합문화공간",
        "을숙도문화회관": "을숙도문화회관",
        # 추가 관광지들
        "부산시민공원": "부산시민공원",
        "국제시장": "국제시장",
        "용두산공원": "용두산공원",
        "광복로": "광복로",
        "서면": "서면",
        "부산시립미술관": "부산시립미술관",
        "다대포 해수욕장": "다대포 해수욕장",
        "신세계 센텀시티": "신세계 센텀시티",
        "보수동 책방골목": "보수동 책방골목",
        "이기대 해안산책로": "이기대 해안산책로",
        "구룡포": "구룡포",
        "부평깡통야시장": "부평깡통야시장",
        "전포카페거리": "전포카페거리",
        "남포동": "남포동",
        "광복로 문화거리": "광복로 문화거리",
        "부산대학교": "부산대학교",
        "해리단길": "해리단길",
        "광안리 M 드론쇼": "광안리 M 드론쇼",
        "부산 X the SKY": "부산 X the SKY",
        "다이아몬드베이": "다이아몬드베이",
        "부산 VR파크": "부산 VR파크",
        "해운대 블루라인 파크": "해운대 블루라인 파크",
        "부산 아쿠아리움": "부산 아쿠아리움",
        "송정 비치클럽": "송정 비치클럽",
        "부산 락페스티벌": "부산 락페스티벌",
        "해운대 아이스 아레나": "해운대 아이스 아레나",
        "온천천 시민공원": "온천천 시민공원",
        "민락수변공원": "민락수변공원",
        "동래구": "동래구",
        "아르피나": "아르피나",
        "BIGBANG 승리 카페 'MONKEY MUSEUM'": "BIGBANG 승리 카페 'MONKEY MUSEUM'",
        "도시남녀의 사랑법": "도시남녀의 사랑법",
        "시크릿 가든": "시크릿 가든",
        "롯데호텔 부산": "롯데호텔 부산",
        "2NE1 박봄 가족 운영 카페": "2NE1 박봄 가족 운영 카페",
        "상속자들": "상속자들",
        "BIGBANG 대성 가족 운영 펜션": "BIGBANG 대성 가족 운영 펜션",
        "김비서가 왜 그럴까": "김비서가 왜 그럴까",
        "부산역": "부산역",
        "꽃보다 남자": "꽃보다 남자",
        "피노키오": "피노키오",
        "KBS부산방송총국": "KBS부산방송총국",
        "광복로 패션거리": "광복로 패션거리",
        "센텀시티 신세계백화점": "센텀시티 신세계백화점",
        "도깨비": "도깨비",
        "광안대교": "광안대교",
        "부산항대교": "부산항대교",
        "신세계 센텀시티": "신세계 센텀시티",
        "해운대 센텀호텔": "해운대 센텀호텔",
        "부산시청": "부산시청",
        "부산과학체험관": "부산과학체험관",
        "동래 민속예술관": "동래 민속예술관",
        "부산항": "부산항",
        "부산시립미술관": "부산시립미술관"
    },
    "en": {
        "범어사": "Beomeosa Temple",
        "해운대 해수욕장": "Haeundae Beach",
        "감천문화마을": "Gamcheon Culture Village", 
        "광안리 해수욕장": "Gwangalli Beach",
        "부산타워": "Busan Tower",
        "부산박물관": "Busan Museum",
        "국립해양박물관": "National Maritime Museum",
        "롯데월드 어드벤처 부산": "Lotte World Adventure Busan",
        "송도해상케이블카": "Songdo Marine Cable Car",
        "BIFF 거리": "BIFF Street",
        "자갈치시장": "Jagalchi Market",
        "해동용궁사": "Haedong Yonggungsa Temple",
        "태종대": "Taejongdae Park",
        "BTS 지민 아버지 카페 'MAGNATE'": "BTS Jimin's Father's Cafe 'MAGNATE'",
        "흰여울문화마을": "Huinnyeoul Culture Village",
        # MBTI 추천에서 추가된 관광지들
        "금정산성": "Geumjeongsanseong Fortress",
        "UN평화공원": "UN Peace Park",
        "송도구름산책로": "Songdo Cloud Walk",
        "부산문화회관": "Busan Cultural Center",
        "부산시립도서관": "Busan Municipal Library",
        "태종대 등대": "Taejongdae Lighthouse",
        "동래온천": "Dongnae Hot Springs",
        "부산근현대역사관": "Busan Modern History Museum",
        "영화의전당": "Busan Cinema Center",
        "부산과학기술협의체": "Busan Science & Technology Council",
        "부산현대미술관": "Busan Museum of Contemporary Art",
        "을숙도 생태공원": "Eulsukdo Ecological Park",
        "부산진시장": "Busanjin Market",
        "부산도서관": "Busan Library",
        "부산국제금융센터(BIFC)": "Busan International Finance Center (BIFC)",
        "센텀시티": "Centum City",
        "부산 벡스코": "BEXCO Busan",
        "해운대 마린시티": "Haeundae Marine City",
        "롯데백화점 센텀시티점": "Lotte Department Store Centum City",
        "광안리 더 베이": "The Bay Gwangalli",
        "송도스카이워크": "Songdo Skywalk",
        "F1963 복합문화공간": "F1963 Cultural Complex",
        "을숙도문화회관": "Eulsukdo Cultural Center",
        # 추가 관광지들
        "부산시민공원": "Busan Citizens Park",
        "국제시장": "Gukje Market",
        "용두산공원": "Yongdusan Park",
        "광복로": "Gwangbok-ro",
        "서면": "Seomyeon",
        "부산시립미술관": "Busan Museum of Art",
        "다대포 해수욕장": "Dadaepo Beach",
        "신세계 센텀시티": "Shinsegae Centum City",
        "보수동 책방골목": "Bosu-dong Book Street",
        "이기대 해안산책로": "Igidae Coastal Walking Trail",
        "구룡포": "Guryongpo",
        "부평깡통야시장": "Bupyeong Kkangtong Night Market",
        "전포카페거리": "Jeonpo Cafe Street",
        "남포동": "Nampo-dong",
        "광복로 문화거리": "Gwangbok-ro Cultural Street",
        "부산대학교": "Pusan National University",
        "해리단길": "Haeridan-gil",
        "광안리 M 드론쇼": "Gwangalli M Drone Show",
        "부산 X the SKY": "Busan X the SKY",
        "다이아몬드베이": "Diamond Bay",
        "부산 VR파크": "Busan VR Park",
        "해운대 블루라인 파크": "Haeundae Blueline Park",
        "부산 아쿠아리움": "Busan Aquarium",
        "송정 비치클럽": "Songjeong Beach Club",
        "부산 락페스티벌": "Busan Rock Festival",
        "해운대 아이스 아레나": "Haeundae Ice Arena",
        "온천천 시민공원": "Oncheoncheon Citizens Park",
        "민락수변공원": "Millak Waterside Park",
        "동래구": "Dongnae-gu",
        "아르피나": "Arpina",
        "BIGBANG 승리 카페 'MONKEY MUSEUM'": "BIGBANG Seungri's Cafe 'MONKEY MUSEUM'",
        "도시남녀의 사랑법": "City Couples' Way of Love",
        "시크릿 가든": "Secret Garden",
        "롯데호텔 부산": "Lotte Hotel Busan",
        "2NE1 박봄 가족 운영 카페": "2NE1 Park Bom's Family Cafe",
        "상속자들": "The Heirs",
        "BIGBANG 대성 가족 운영 펜션": "BIGBANG Daesung's Family Pension",
        "김비서가 왜 그럴까": "What's Wrong with Secretary Kim",
        "부산역": "Busan Station",
        "꽃보다 남자": "Boys Over Flowers",
        "피노키오": "Pinocchio",
        "KBS부산방송총국": "KBS Busan Broadcasting Station",
        "광복로 패션거리": "Gwangbok-ro Fashion Street",
        "센텀시티 신세계백화점": "Shinsegae Centum City Department Store",
        "도깨비": "Goblin",
        "광안대교": "Gwangandaegyo Bridge",
        "부산항대교": "Busan Harbor Bridge",
        "신세계 센텀시티": "Shinsegae Centum City",
        "해운대 센텀호텔": "Haeundae Centum Hotel",
        "부산시청": "Busan City Hall",
        "KBS부산방송총국": "KBS Busan Broadcasting Station",
        "부산과학체험관": "Busan Science Experience Center",
        "동래 민속예술관": "Dongnae Folk Art Center",
        "부산항": "Busan Port",
        "부산시립미술관": "Busan Museum of Art"
    },
    "ja": {
        "범어사": "梵魚寺",
        "해운대 해수욕장": "海雲台海水浴場",
        "감천문화마을": "甘川文化村",
        "광안리 해수욕장": "広安里海水浴場", 
        "부산타워": "釜山タワー",
        "부산박물관": "釜山博物館",
        "국립해양박물관": "国立海洋博物館",
        "롯데월드 어드벤처 부산": "ロッテワールドアドベンチャー釜山",
        "송도해상케이블카": "松島海上ケーブルカー",
        "BIFF 거리": "BIFF通り",
        "자갈치시장": "チャガルチ市場",
        "해동용궁사": "海東龍宮寺",
        "태종대": "太宗台",
        "BTS 지민 아버지 카페 'MAGNATE'": "BTS ジミンの父のカフェ'MAGNATE'",
        "흰여울문화마을": "ヒンニョウル文化村",
        # MBTI 추천에서 추가된 관광지들
        "금정산성": "金井山城",
        "UN평화공원": "UN平和公園",
        "송도구름산책로": "松島雲散歩路",
        "부산문화회관": "釜山文化会館",
        "부산시립도서관": "釜山市立図書館",
        "태종대 등대": "太宗台灯台",
        "동래온천": "東莱温泉",
        "부산근현대역사관": "釜山近現代歴史館",
        "영화의전당": "映画の殿堂",
        "부산과학기술협의체": "釜山科学技術協議体",
        "부산현대미술관": "釜山現代美術館",
        "을숙도 생태공원": "乙淑島生態公園",
        "부산진시장": "釜山鎮市場",
        "부산도서관": "釜山図書館",
        "부산국제금융센터(BIFC)": "釜山国際金融センター(BIFC)",
        "센텀시티": "セントムシティ",
        "부산 벡스코": "釜山ベクスコ",
        "해운대 마린시티": "海雲台マリンシティ",
        "롯데백화점 센텀시티점": "ロッテ百貨店セントムシティ店",
        "광안리 더 베이": "広安里ザベイ",
        "송도스카이워크": "松島スカイウォーク",
        "F1963 복합문화공간": "F1963複合文化空間",
        "을숙도문화회관": "乙淑島文化会館",
        # 추가 관광지들
        "부산시민공원": "釜山市民公園",
        "국제시장": "国際市場",
        "용두산공원": "竜頭山公園",
        "광복로": "光復路",
        "서면": "西面",
        "부산시립미술관": "釜山市立美術館",
        "다대포 해수욕장": "多大浦海水浴場",
        "신세계 센텀시티": "新世界セントムシティ",
        "보수동 책방골목": "宝水洞書房通り",
        "이기대 해안산책로": "二妓台海岸散歩路",
        "구룡포": "九龍浦",
        "부평깡통야시장": "富平缶詰夜市",
        "전포카페거리": "田浦カフェ通り",
        "남포동": "南浦洞",
        "광복로 문화거리": "光復路文化通り",
        "부산대학교": "釜山大学校",
        "해리단길": "海利丹路",
        "광안리 M 드론쇼": "広安里Mドローショー",
        "부산 X the SKY": "釜山Xザスカイ",
        "다이아몬드베이": "ダイヤモンドベイ",
        "부산 VR파크": "釜山VRパーク",
        "해운대 블루라인 파크": "海雲台ブルーラインパーク",
        "부산 아쿠아리움": "釜山水族館",
        "송정 비치클럽": "松亭ビーチクラブ",
        "부산 락페스티벌": "釜山ロックフェスティバル",
        "해운대 아이스 아레나": "海雲台アイスアリーナ",
        "온천천 시민공원": "温泉川市民公園",
        "민락수변공원": "民楽水辺公園",
        "동래구": "東莱区",
        "아르피나": "アルピナ",
        "BIGBANG 승리 카페 'MONKEY MUSEUM'": "BIGBANG勝利のカフェ'MONKEY MUSEUM'",
        "도시남녀의 사랑법": "都市男女の愛し方",
        "시크릿 가든": "シークレットガーデン",
        "롯데호텔 부산": "ロッテホテル釜山",
        "2NE1 박봄 가족 운영 카페": "2NE1パクボム家族運営カフェ",
        "상속자들": "相続者たち",
        "BIGBANG 대성 가족 운영 펜션": "BIGBANG大成家族運営ペンション",
        "김비서가 왜 그럴까": "キム秘書はなぜそうなのか",
        "부산역": "釜山駅",
        "꽃보다 남자": "花より男子",
        "피노키오": "ピノキオ",
        "KBS부산방송총국": "KBS釜山放送総局",
        "광복로 패션거리": "光復路ファッション通り",
        "센텀시티 신세계백화점": "セントムシティ新世界百貨店",
        "도깨비": "ドッケビ",
        "광안대교": "広安大橋",
        "부산항대교": "釜山港大橋",
        "신세계 센텀시티": "新世界セントムシティ",
        "해운대 센텀호텔": "海雲台セントムホテル",
        "부산시청": "釜山市庁",
        "부산과학체험관": "釜山科学体験館",
        "동래 민속예술관": "東莱民俗芸術館",
        "부산항": "釜山港",
        "부산시립미술관": "釜山市立美術館"
    },
    "zh": {
        "범어사": "梵鱼寺",
        "해운대 해수욕장": "海云台海水浴场",
        "감천문화마을": "甘川文化村",
        "광안리 해수욕장": "广安里海水浴场",
        "부산타워": "釜山塔",
        "부산박물관": "釜山博物馆", 
        "국립해양박물관": "国立海洋博物馆",
        "롯데월드 어드벤처 부산": "乐天世界冒险釜山",
        "송도해상케이블카": "松岛海上缆车",
        "BIFF 거리": "BIFF街",
        "자갈치시장": "札嘎其市场",
        "해동용궁사": "海东龙宫寺",
        "태종대": "太宗台",
        "BTS 지민 아버지 카페 'MAGNATE'": "BTS智旻父亲的咖啡厅'MAGNATE'",
        "흰여울문화마을": "白色涡流文化村",
        # MBTI 추천에서 추가된 관광지들
        "금정산성": "金井山城",
        "UN평화공원": "UN和平公园",
        "송도구름산책로": "松岛云散步路",
        "부산문화회관": "釜山文化会馆",
        "부산시립도서관": "釜山市立图书馆",
        "태종대 등대": "太宗台灯塔",
        "동래온천": "东莱温泉",
        "부산근현대역사관": "釜山近现代历史馆",
        "영화의전당": "电影殿堂",
        "부산과학기술협의체": "釜山科学技术协议体",
        "부산현대미술관": "釜山现代美术馆",
        "을숙도 생태공원": "乙淑岛生态公园",
        "부산진시장": "釜山镇市场",
        "부산도서관": "釜山图书馆",
        "부산국제금융센터(BIFC)": "釜山国际金融中心(BIFC)",
        "센텀시티": "Centum City",
        "부산 벡스코": "釜山BEXCO",
        "해운대 마린시티": "海云台海洋城市",
        "롯데백화점 센텀시티점": "乐天百货Centum City店",
        "광안리 더 베이": "广安里海湾",
        "송도스카이워크": "松岛天空步道",
        "F1963 복합문화공간": "F1963复合文化空间",
        "을숙도문화회관": "乙淑岛文化会馆",
        # 추가 관광지들
        "부산시민공원": "釜山市民公园",
        "국제시장": "国际市场",
        "용두산공원": "龙头山公园",
        "광복로": "光复路",
        "서면": "西面",
        "부산시립미술관": "釜山市立美术馆",
        "다대포 해수욕장": "多大浦海水浴场",
        "신세계 센텀시티": "新世界Centum City",
        "보수동 책방골목": "宝水洞书店街",
        "이기대 해안산책로": "二妓台海岸散步路",
        "구룡포": "九龙浦",
        "부평깡통야시장": "富平罐头夜市",
        "전포카페거리": "田浦咖啡街",
        "남포동": "南浦洞",
        "광복로 문화거리": "光复路文化街",
        "부산대학교": "釜山大学",
        "해리단길": "海利丹路",
        "광안리 M 드론쇼": "广安里M无人机秀",
        "부산 X the SKY": "釜山X天空",
        "다이아몬드베이": "钻石湾",
        "부산 VR파크": "釜山VR公园",
        "해운대 블루라인 파크": "海云台蓝线公园",
        "부산 아쿠아리움": "釜山水族馆",
        "송정 비치클럽": "松亭海滩俱乐部",
        "부산 락페스티벌": "釜山摇滚音乐节",
        "해운대 아이스 아레나": "海云台冰上竞技场",
        "온천천 시민공원": "温泉川市民公园",
        "민락수변공원": "民乐水边公园",
        "동래구": "东莱区",
        "아르피나": "阿尔皮纳",
        "BIGBANG 승리 카페 'MONKEY MUSEUM'": "BIGBANG胜利的咖啡厅'MONKEY MUSEUM'",
        "도시남녀의 사랑법": "都市男女的爱情法",
        "시크릿 가든": "秘密花园",
        "롯데호텔 부산": "乐天酒店釜山",
        "2NE1 박봄 가족 운영 카페": "2NE1朴春家族经营咖啡厅",
        "상속자들": "继承者们",
        "BIGBANG 대성 가족 운영 펜션": "BIGBANG大成家族经营民宿",
        "김비서가 왜 그럴까": "金秘书为什么那样",
        "부산역": "釜山站",
        "꽃보다 남자": "花样男子",
        "피노키오": "匹诺曹",
        "KBS부산방송총국": "KBS釜山广播总局",
        "광복로 패션거리": "光复路时尚街",
        "센텀시티 신세계백화점": "Centum City新世界百货",
        "도깨비": "鬼怪",
        "광안대교": "广安大桥",
        "부산항대교": "釜山港大桥",
        "신세계 센텀시티": "新世界Centum City",
        "해운대 센텀호텔": "海云台Centum酒店",
        "부산시청": "釜山市厅",
        "부산과학체험관": "釜山科学体验馆",
        "동래 민속예술관": "东莱民俗艺术馆",
        "부산항": "釜山港",
        "부산시립미술관": "釜山市立美术馆"
    }
}

# 관광지별 상세 정보 데이터
attraction_details = {
    "범어사": {
        "images": ["https://picsum.photos/800/600?random=1"],
        "videos": ["https://www.youtube.com/shorts/ABC123"],
        "location": {"lat": 35.236944, "lng": 129.061944, "address": "부산광역시 금정구 범어사로 250"},
        "description": {
            "ko": "678년에 창건된 부산의 대표적인 사찰로, 금정산에 위치해 있습니다.",
            "en": "A representative temple of Busan founded in 678, located on Geumjeongsan Mountain.",
            "ja": "678年に創建された釜山の代表的な寺院で、金井山に位置しています。",
            "zh": "建于678年的釜山代表性寺庙，位于金井山上。"
        }
    },
    "해운대 해수욕장": {
        "images": ["https://picsum.photos/800/600?random=2"],
        "videos": ["https://www.youtube.com/shorts/DEF456"],
        "location": {"lat": 35.158698, "lng": 129.160385, "address": "부산광역시 해운대구 해운대해변로 264"},
        "description": {
            "ko": "부산을 대표하는 해수욕장으로, 국내외 관광객들이 가장 많이 찾는 명소입니다.",
            "en": "Busan's representative beach, the most visited attraction by domestic and international tourists.",
            "ja": "釜山を代表する海水浴場で、国内外の観光客が最も多く訪れる名所です。",
            "zh": "釜山代表性的海水浴场，是国内外游客最多访问的景点。"
        }
    },
    "감천문화마을": {
        "images": ["https://picsum.photos/800/600?random=3"],
        "videos": ["https://www.youtube.com/shorts/GHI789"],
        "location": {"lat": 35.097649, "lng": 129.010544, "address": "부산광역시 사하구 감내2로 203"},
        "description": {
            "ko": "한국의 마추픽추라 불리는 컬러풀한 문화마을로, BTS 뮤직비디오 촬영지로도 유명합니다.",
            "en": "A colorful cultural village called Korea's Machu Picchu, also famous as a BTS music video filming location.",
            "ja": "韓国のマチュピチュと呼ばれるカラフルな文化村で、BTSのミュージックビデオの撮影地としても有名です。",
            "zh": "被称为韩国马丘比丘的彩色文化村，也因BTS音乐视频拍摄地而闻名。"
        }
    },
    "광안리 해수욕장": {
        "images": ["https://picsum.photos/800/600?random=4"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.153285, "lng": 129.118666, "address": "부산광역시 수영구 광안해변로 219"},
        "description": {
            "ko": "광안대교 야경과 함께 즐길 수 있는 로맨틱한 해수욕장입니다.",
            "en": "A romantic beach where you can enjoy the night view of Gwangan Bridge.",
            "ja": "広安大橋の夜景と一緒に楽しめるロマンチックな海水浴場です。",
            "zh": "可以欣赏广安大桥夜景的浪漫海水浴场。"
        }
    },
    "부산타워": {
        "images": ["https://picsum.photos/800/600?random=5"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.100570, "lng": 129.032909, "address": "부산광역시 중구 용두산길 37-55"},
        "description": "부산의 상징적인 랜드마크로, 시내 전경을 한눈에 볼 수 있습니다."
    },
    "부산박물관": {
        "images": ["https://picsum.photos/800/600?random=6"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.187167, "lng": 129.106889, "address": "부산광역시 남구 유엔평화로 63"},
        "description": "부산의 역사와 문화를 한눈에 볼 수 있는 종합박물관입니다."
    },
    "국립해양박물관": {
        "images": ["https://picsum.photos/800/600?random=7"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.135222, "lng": 129.109639, "address": "부산광역시 영도구 해양로 301번길 45"},
        "description": "해양 문화와 역사를 체험할 수 있는 국내 최대 해양박물관입니다."
    },
    "롯데월드 어드벤처 부산": {
        "images": ["https://picsum.photos/800/600?random=8"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.186564, "lng": 129.079194, "address": "부산광역시 기장군 기장읍 동부산관광로 42"},
        "description": "부산 최대 규모의 테마파크로 다양한 어트랙션과 즐길거리가 있습니다."
    },
    "송도해상케이블카": {
        "images": ["https://picsum.photos/800/600?random=9"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.076111, "lng": 129.017222, "address": "부산광역시 서구 송도해변로 171"},
        "description": "바다 위를 가로지르는 케이블카로 아름다운 부산 해안선을 감상할 수 있습니다."
    },
    "BIFF 거리": {
        "images": ["https://picsum.photos/800/600?random=10"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.096944, "lng": 129.032778, "address": "부산광역시 중구 남포동"},
        "description": "부산국제영화제의 중심지로 영화와 문화의 거리입니다."
    },
    "자갈치시장": {
        "images": ["https://picsum.photos/800/600?random=11"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.096667, "lng": 129.030556, "address": "부산광역시 중구 자갈치해안로 52"},
        "description": "부산을 대표하는 수산시장으로 신선한 해산물을 맛볼 수 있습니다."
    },
    "해동용궁사": {
        "images": ["https://picsum.photos/800/600?random=12"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.188333, "lng": 129.223056, "address": "부산광역시 기장군 기장읍 용궁길 86"},
        "description": "바다에 면한 아름다운 사찰로 특별한 풍경을 자랑합니다."
    },
    "태종대": {
        "images": ["https://picsum.photos/800/600?random=13"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.051389, "lng": 129.087222, "address": "부산광역시 영도구 전망로 24"},
        "description": "부산의 대표적인 해안절벽으로 아름다운 자연경관을 감상할 수 있습니다."
    },
    "BTS 지민 아버지 카페 'MAGNATE'": {
        "images": ["https://picsum.photos/800/600?random=14"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.158333, "lng": 129.160000, "address": "부산광역시 해운대구 해운대해변로 197"},
        "description": "BTS 지민의 아버지가 운영하는 카페로 K-pop 팬들의 성지입니다."
    },
    "흰여울문화마을": {
        "images": ["https://picsum.photos/800/600?random=15"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.051944, "lng": 129.087500, "address": "부산광역시 영도구 흰여울길 1"},
        "description": "영화 '변호인' 촬영지로 유명한 아름다운 해안마을입니다."
    }
}

def get_tour_api_images(content_id, num_of_rows=5):
    """TourAPI에서 관광지 사진 정보를 가져옵니다."""
    if not content_id:
        return []
    
    try:
        # detailImage1 API 호출 - 관광지 상세 이미지 정보
        url = f"{TOUR_API_BASE_URL}/detailImage1"
        params = {
            'serviceKey': TOUR_API_KEY,
            'numOfRows': num_of_rows,
            'pageNo': 1,
            'MobileOS': 'ETC',
            'MobileApp': 'TourApp',
            'contentId': content_id,
            'imageYN': 'Y',
            'subImageYN': 'Y',
            '_type': 'json'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        # API 오류 확인
        if 'DEADLINE_HAS_EXPIRED_ERROR' in response.text or 'SERVICE ERROR' in response.text:
            return []
        
        data = response.json()
        items = data.get('response', {}).get('body', {}).get('items', {})
        
        if not items:
            return []
        
        # items가 리스트가 아닌 경우 (단일 항목)
        if isinstance(items, dict) and 'item' in items:
            items = items['item']
            if not isinstance(items, list):
                items = [items]
        
        # 이미지 URL 추출
        image_urls = []
        for item in items:
            if isinstance(item, dict):
                # 대표 이미지 우선, 없으면 일반 이미지
                img_url = item.get('originimgurl') or item.get('smallimageurl')
                if img_url and img_url.startswith('http'):
                    image_urls.append(img_url)
        
        return image_urls[:num_of_rows]  # 최대 개수 제한
        
    except Exception as e:
        return []

def show_attraction_info(page, attraction_name, lang="ko"):
    """관광지 정보 스낵바로 간단하게 표시"""
    # attraction_details에서 관광지 정보 가져오기
    details = attraction_details.get(attraction_name, {})
    
    # 관광지 이름을 해당 언어로 변환
    display_name = attraction_name_mapping.get(lang, attraction_name_mapping["ko"]).get(attraction_name, attraction_name)
    
    # 설명을 해당 언어로 가져오기
    description = details.get("description", {})
    if isinstance(description, dict):
        description_text = description.get(lang, description.get("ko", "관광지 정보를 준비 중입니다."))
    else:
        description_text = description if description else "관광지 정보를 준비 중입니다."
    
    # 다국어 메시지
    info_messages = {
        "ko": f"📍 {display_name}\n{description_text}",
        "en": f"📍 {display_name}\n{description_text}",
        "ja": f"📍 {display_name}\n{description_text}",
        "zh": f"📍 {display_name}\n{description_text}"
    }
    
    # 간단한 스낵바로 정보 표시
    page.snack_bar = ft.SnackBar(
        content=ft.Text(
            info_messages.get(lang, info_messages["ko"]),
            size=14,
            color=ft.Colors.WHITE
        ),
        duration=4000,
        bgcolor=ft.Colors.BLUE_700,
        action="닫기",
        action_color=ft.Colors.WHITE,
        on_action=lambda e: setattr(page.snack_bar, 'open', False)
    )
    page.snack_bar.open = True
    page.update()

def show_attraction_videos(page, attraction_name, lang="ko"):
    """관광지 영상 모달 창 표시"""
    details = attraction_details.get(attraction_name, {})
    videos = details.get("videos", [])
    
    # 관광지 이름을 해당 언어로 변환
    display_name = attraction_name_mapping.get(lang, attraction_name_mapping["ko"]).get(attraction_name, attraction_name)
    
    # 다국어 메시지
    messages = {
        "searching": {
            "ko": f"📱 '{display_name}' 관련 쇼츠 영상을 YouTube에서 검색합니다",
            "en": f"📱 Searching for '{display_name}' shorts videos on YouTube",
            "ja": f"📱 YouTubeで'{display_name}'関連のショート動画を検索します",
            "zh": f"📱 在YouTube上搜索'{display_name}'相关短视频"
        },
        "playing": {
            "ko": f"📱 '{display_name}' 쇼츠 영상을 재생합니다",
            "en": f"📱 Playing '{display_name}' shorts video",
            "ja": f"📱 '{display_name}'のショート動画を再生します",
            "zh": f"📱 播放'{display_name}'短视频"
        },
        "error": {
            "ko": "영상을 열 수 없습니다.",
            "en": "Cannot open the video.",
            "ja": "動画を開けません。",
            "zh": "无法打开视频。"
        }
    }
    
    if not videos:
        # 영상이 없으면 유튜브 쇼츠 검색으로 대체
        search_query = f"{display_name} 부산 여행 쇼츠"
        if lang == "en":
            search_query = f"{display_name} Busan travel Korea shorts"
        elif lang == "ja":
            search_query = f"{display_name} 釜山 旅行 ショート"
        elif lang == "zh":
            search_query = f"{display_name} 釜山 旅游 短片"
            
        encoded_query = search_query.replace(" ", "+")
        # YouTube Shorts 전용 검색 URL 사용
        youtube_search_url = f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIYAg%253D%253D"
        
        try:
            page.launch_url(youtube_search_url)
            page.snack_bar = ft.SnackBar(
                content=ft.Text(messages["searching"][lang]),
                duration=2000
            )
            page.snack_bar.open = True
            page.update()
        except:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(messages["error"][lang]),
                duration=2000
            )
            page.snack_bar.open = True
            page.update()
        return
        
    # 실제 영상 링크가 있으면 직접 열기
    try:
        page.launch_url(videos[0])
        page.snack_bar = ft.SnackBar(
            content=ft.Text(messages["playing"][lang]),
            duration=2000
        )
        page.snack_bar.open = True
        page.update()
    except:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(messages["error"][lang]),
            duration=2000
        )
        page.snack_bar.open = True
        page.update()

def open_google_maps_directly(page, attraction_name, lang="ko"):
    """Google Maps를 바로 열기 (가장 간단한 방식)"""
    try:
        print(f"🗺️ 지도 버튼 클릭: {attraction_name}, 언어: {lang}")
    except UnicodeEncodeError:
        print(f"지도 버튼 클릭: {attraction_name}, 언어: {lang}")
    
    # Google Maps 검색 URL 생성 (URL 인코딩 적용 + 언어 설정)
    import urllib.parse
    
    # 언어별 구글 맵 언어 코드 매핑
    google_lang_mapping = {
        "ko": "ko",
        "en": "en", 
        "ja": "ja",
        "zh": "zh-CN",
        "zh-TW": "zh-TW",
        "vi": "vi",
        "th": "th",
        "id": "id",
        "fr": "fr",
        "de": "de",
        "tl": "tl"
    }
    
    # 언어별 지역 코드 매핑
    google_region_mapping = {
        "ko": "KR",
        "en": "US", 
        "ja": "JP",
        "zh": "CN",
        "zh-TW": "TW",
        "vi": "VN",
        "th": "TH",
        "id": "ID",
        "fr": "FR",
        "de": "DE",
        "tl": "PH"
    }
    
    # 언어별 지도 서비스 매핑 (Google Maps 대안 포함)
    map_service_mapping = {
        "ko": {"type": "google", "domain": "maps.google.com"},
        "en": {"type": "google", "domain": "maps.google.com"}, 
        "ja": {"type": "google", "domain": "maps.google.co.jp"},
        "zh": {"type": "google", "domain": "maps.google.com"},  # 중국 - Google Maps 한국 버전 (접근 가능성 높음)
        "zh-TW": {"type": "google", "domain": "maps.google.com.tw"},
        "vi": {"type": "google", "domain": "maps.google.com"},  # 베트남 - Google Maps 한국 버전 (접근 가능성 높음)
        "th": {"type": "google", "domain": "maps.google.co.th"},
        "id": {"type": "google", "domain": "maps.google.co.id"},
        "fr": {"type": "google", "domain": "maps.google.fr"},
        "de": {"type": "google", "domain": "maps.google.de"},
        "tl": {"type": "google", "domain": "maps.google.com.ph"}
    }
    
    # 언어별 검색어 설정
    city_names = {
        "ko": "부산",
        "en": "Busan",
        "ja": "釜山", 
        "zh": "釜山",
        "zh-TW": "釜山",
        "vi": "Busan",
        "th": "ปูซาน",
        "id": "Busan",
        "fr": "Busan",
        "de": "Busan",
        "tl": "Busan"
    }
    
    google_lang = google_lang_mapping.get(lang, "ko")
    google_region = google_region_mapping.get(lang, "KR")
    map_service = map_service_mapping.get(lang, {"type": "google", "domain": "maps.google.com"})
    city_name = city_names.get(lang, "부산")
    search_query = f"{attraction_name} {city_name}"
    encoded_query = urllib.parse.quote(search_query)
    
    # Google Maps URL 생성 (모든 언어)
    google_maps_url = f"https://{map_service['domain']}/maps/search/{encoded_query}?hl={google_lang}&gl={google_region}&ie=UTF8"
    
    try:
        print(f"=== 지도 서비스 설정 디버깅 ===")
        print(f"입력 언어: {lang}")
        print(f"지도 서비스 타입: {map_service['type']}")
        print(f"지도 도메인: {map_service['domain']}")
        print(f"도시명: {city_name}")
        print(f"검색어: {search_query}")
        print(f"최종 URL: {google_maps_url}")
        print(f"===========================")
    except UnicodeEncodeError:
        print(f"언어 설정: {lang} -> 지도 서비스: {map_service['type']}")
        print(f"Maps URL: {google_maps_url}")
    
    # Google Maps 알림 메시지 (모든 언어)
    messages = {
        "ko": f"🗺️ {attraction_name} 위치를 Google Maps에서 열고 있습니다...",
        "en": f"🗺️ Opening {attraction_name} location in Google Maps...",
        "ja": f"🗺️ {attraction_name}の位置をGoogle Mapsで開いています...",
        "zh": f"🗺️ 正在Google地图中打开{attraction_name}位置...",
        "zh-TW": f"🗺️ 正在Google地圖中開啟{attraction_name}位置...",
        "vi": f"🗺️ Đang mở vị trí {attraction_name} trong Google Maps...",
        "th": f"🗺️ กำลังเปิดตำแหน่ง {attraction_name} ใน Google Maps...",
        "id": f"🗺️ Membuka lokasi {attraction_name} di Google Maps...",
        "fr": f"🗺️ Ouverture de l'emplacement {attraction_name} dans Google Maps...",
        "de": f"🗺️ Öffne {attraction_name} Standort in Google Maps...",
        "tl": f"🗺️ Binubuksan ang lokasyon ng {attraction_name} sa Google Maps..."
    }
    
    # 사용자에게 알림
    page.snack_bar = ft.SnackBar(
        content=ft.Text(messages.get(lang, messages["ko"])),
        duration=3000
    )
    page.snack_bar.open = True
    page.update()
    
    # Google Maps 열기 시도
    try:
        print("page.launch_url() 시도 중...")
        page.launch_url(google_maps_url)
        print("✅ page.launch_url() 성공")
    except Exception as e:
        print(f"❌ page.launch_url() 실패: {e}")
        # 대안: webbrowser 모듈 사용
        try:
            print("webbrowser.open() 시도 중...")
            import webbrowser
            webbrowser.open(google_maps_url)
            print("✅ webbrowser.open() 성공")
        except Exception as e2:
            print(f"❌ webbrowser.open() 실패: {e2}")
            # 마지막 대안: 클립보드에 복사
            try:
                import pyperclip
                pyperclip.copy(google_maps_url)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("URL이 클립보드에 복사되었습니다."),
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
                print("클립보드에 URL 복사 완료")
            except:
                print("모든 방법 실패")

def show_attraction_map(page, attraction_name, lang="ko"):
    """관광지 지도 바로 열기 (간단한 방식)"""
    print(f"지도 버튼 클릭됨: {attraction_name} (언어: {lang})")
    
    # 관광지 위치 정보 가져오기
    details = attraction_details.get(attraction_name, {})
    location = details.get("location", {})
    print(f"위치 정보: {location}")
    
    # 다국어 메시지
    messages = {
        "no_location": {
            "ko": "이 관광지의 위치 정보가 없습니다.",
            "en": "Location information is not available.",
            "ja": "位置情報がありません。",
            "zh": "没有位置信息。",
            "zh-TW": "沒有位置資訊。",
            "vi": "Không có thông tin vị trí.",
            "th": "ไม่มีข้อมูลตำแหน่ง",
            "id": "Informasi lokasi tidak tersedia.",
            "fr": "Informations de localisation non disponibles.",
            "de": "Standortinformationen nicht verfügbar.",
            "tl": "Walang available na impormasyon ng lokasyon."
        },
        "opening_maps": {
            "ko": "🗺️ Google Maps에서 열고 있습니다...",
            "en": "🗺️ Opening in Google Maps...",
            "ja": "🗺️ Google Mapsで開いています...",
            "zh": "🗺️ 正在Google地图中打开...",
            "zh-TW": "🗺️ 正在Google地圖中開啟...",
            "vi": "🗺️ Đang mở trong Google Maps...",
            "th": "🗺️ กำลังเปิดใน Google Maps...",
            "id": "🗺️ Membuka di Google Maps...",
            "fr": "🗺️ Ouverture dans Google Maps...",
            "de": "🗺️ Öffne in Google Maps...",
            "tl": "🗺️ Binubuksan sa Google Maps..."
        }
    }
    
    # 언어별 Google Maps 도메인 매핑
    google_maps_domains = {
        "ko": "https://maps.google.com/",
        "en": "https://maps.google.com/", 
        "ja": "https://maps.google.co.jp/",
        "zh": "https://maps.google.com/",  # 중국 - Google Maps 한국 버전
        "zh-TW": "https://maps.google.com.tw/",
        "vi": "https://maps.google.com/",  # 베트남 - Google Maps 한국 버전
        "th": "https://maps.google.co.th/",
        "id": "https://maps.google.co.id/",
        "fr": "https://maps.google.fr/",
        "de": "https://maps.google.de/",
        "tl": "https://maps.google.com.ph/"
    }
    
    # 해당 언어의 Google Maps 도메인 선택
    maps_domain = google_maps_domains.get(lang, "https://maps.google.com/")
    
    # Google Maps URL 생성
    if not location or not location.get('lat') or not location.get('lng'):
        # 관광지 이름으로 검색 시도
        search_query = f"{attraction_name} 부산"
        google_maps_url = f"{maps_domain}maps/search/{search_query}"
        print(f"위치 정보가 없어 이름으로 검색: {google_maps_url}")
    else:
        # 좌표로 정확한 위치 열기
        google_maps_url = f"{maps_domain}maps?q={location['lat']},{location['lng']}"
        print(f"좌표로 지도 열기: {google_maps_url}")
    
    # 사용자에게 알림
    page.snack_bar = ft.SnackBar(
        content=ft.Text(messages["opening_maps"].get(lang, messages["opening_maps"]["en"])),
        duration=2000
    )
    page.snack_bar.open = True
    page.update()
    
    # Google Maps 열기
    try:
        page.launch_url(google_maps_url)
        print(f"Google Maps 열기 성공: {google_maps_url}")
    except Exception as e:
        print(f"Google Maps 열기 실패: {e}")
        # 실패 시 다른 방법으로 시도
        try:
            import webbrowser
            webbrowser.open(google_maps_url)
            print("webbrowser로 열기 성공")
        except Exception as e2:
            print(f"webbrowser로도 실패: {e2}")

def MBTITourismPage(page, lang="ko", on_back=None, selected_mbti_value=None, result_view_value=None):
    # 화면 크기에 따른 반응형 설정
    is_mobile = page.width < 600
    is_tablet = 600 <= page.width < 1024
    
    # 반응형 크기 계산
    title_size = 20 if is_mobile else 24
    subtitle_size = 16 if is_mobile else 18
    text_size = 14 if is_mobile else 16
    button_size = 12 if is_mobile else 14
    
    # 다국어 텍스트
    texts = {
        "ko": {
            "title": "MBTI별 부산 관광지 추천",
            "subtitle": "당신의 성격 유형에 맞는 관광지를 찾아보세요!",
            "select_mbti": "MBTI를 선택하세요",
            "test_mbti": "MBTI 테스트하기",
            "recommend": "추천받기",
            "back": "뒤로가기",
            "loading": "추천 관광지를 찾는 중...",
            "no_result": "추천 결과가 없습니다.",
            "mbti_descriptions": {
                "INTJ": "전략적 사고가 뛰어난 건축가형",
                "INTP": "논리적 분석을 선호하는 논리술사형",
                "ENTJ": "대담한 통솔력의 사령관형",
                "ENTP": "똑똑한 호기심의 변론가형",
                "INFJ": "상상력이 풍부한 중재자형",
                "INFP": "이상주의적 영감의 중재자형",
                "ENFJ": "카리스마 넘치는 선도자형",
                "ENFP": "재기발랄한 활동가형",
                "ISTJ": "실용적인 현실주의자형",
                "ISFJ": "온화한 수호자형",
                "ESTJ": "엄격한 관리자형",
                "ESFJ": "사교적인 집정관형",
                "ISTP": "만능 재주꾼형",
                "ISFP": "모험을 즐기는 모험가형",
                "ESTP": "대담한 사업가형",
                "ESFP": "자유로운 영혼의 연예인형"
            }
        },
        "en": {
            "title": "Busan Tourism Recommendations by MBTI",
            "subtitle": "Find tourist attractions that match your personality type!",
            "select_mbti": "Select your MBTI",
            "test_mbti": "Take MBTI Test",
            "recommend": "Get Recommendations",
            "back": "Back",
            "loading": "Finding recommended attractions...",
            "no_result": "No recommendations found.",
            "mbti_descriptions": {
                "INTJ": "Strategic Architect",
                "INTP": "Logical Analyst",
                "ENTJ": "Bold Commander",
                "ENTP": "Smart Debater",
                "INFJ": "Imaginative Mediator",
                "INFP": "Idealistic Healer",
                "ENFJ": "Charismatic Leader",
                "ENFP": "Energetic Campaigner",
                "ISTJ": "Practical Realist",
                "ISFJ": "Gentle Protector",
                "ESTJ": "Strict Manager",
                "ESFJ": "Sociable Executive",
                "ISTP": "Versatile Virtuoso",
                "ISFP": "Adventurous Artist",
                "ESTP": "Bold Entrepreneur",
                "ESFP": "Free-spirited Entertainer"
            }
        },
        "ja": {
            "title": "MBTI別釜山観光地おすすめ",
            "subtitle": "あなたの性格タイプに合った観光地を見つけましょう！",
            "select_mbti": "MBTIを選択してください",
            "test_mbti": "MBTIテストを受ける",
            "recommend": "おすすめを取得",
            "back": "戻る",
            "loading": "おすすめ観光地を探しています...",
            "no_result": "おすすめが見つかりませんでした。",
            "mbti_descriptions": {
                "INTJ": "戦略的思考の建築家型",
                "INTP": "論理的分析を好む論理学者型",
                "ENTJ": "大胆な統率力の司令官型",
                "ENTP": "賢い好奇心の討論家型",
                "INFJ": "想像力豊かな調停者型",
                "INFP": "理想主義的霊感の調停者型",
                "ENFJ": "カリスマ溢れる指導者型",
                "ENFP": "機知に富む活動家型",
                "ISTJ": "実用的現実主義者型",
                "ISFJ": "温和な守護者型",
                "ESTJ": "厳格な管理者型",
                "ESFJ": "社交的な執政官型",
                "ISTP": "万能職人型",
                "ISFP": "冒険を楽しむ冒険家型",
                "ESTP": "大胆な起業家型",
                "ESFP": "自由な魂の芸術家型"
            }
        },
        "zh": {
            "title": "MBTI釜山旅游推荐",
            "subtitle": "找到适合您性格类型的旅游景点！",
            "select_mbti": "选择您的MBTI",
            "test_mbti": "进行MBTI测试",
            "recommend": "获取推荐",
            "back": "返回",
            "loading": "正在寻找推荐景点...",
            "no_result": "未找到推荐结果。",
            "mbti_descriptions": {
                "INTJ": "战略思维建筑师",
                "INTP": "逻辑分析学者",
                "ENTJ": "大胆指挥官",
                "ENTP": "聪明辩论家",
                "INFJ": "富有想象力的调停者",
                "INFP": "理想主义治疗师",
                "ENFJ": "魅力领导者",
                "ENFP": "充满活力的活动家",
                "ISTJ": "实用现实主义者",
                "ISFJ": "温和保护者",
                "ESTJ": "严格管理者",
                "ESFJ": "社交执行官",
                "ISTP": "多才多艺的大师",
                "ISFP": "冒险艺术家",
                "ESTP": "大胆企业家",
                "ESFP": "自由精神娱乐者"
            }
        },
        "zh-TW": {
            "title": "MBTI釜山旅遊推薦",
            "subtitle": "找到適合您性格類型的旅遊景點！",
            "select_mbti": "選擇您的MBTI",
            "test_mbti": "進行MBTI測試",
            "recommend": "獲取推薦",
            "back": "返回",
            "loading": "正在尋找推薦景點...",
            "no_result": "未找到推薦結果。",
            "mbti_descriptions": {
                "INTJ": "戰略思維建築師",
                "INTP": "邏輯分析學者",
                "ENTJ": "大膽指揮官",
                "ENTP": "聰明辯論家",
                "INFJ": "富有想像力的調停者",
                "INFP": "理想主義治療師",
                "ENFJ": "魅力領導者",
                "ENFP": "充滿活力的活動家",
                "ISTJ": "實用現實主義者",
                "ISFJ": "溫和保護者",
                "ESTJ": "嚴格管理者",
                "ESFJ": "社交執行官",
                "ISTP": "多才多藝的大師",
                "ISFP": "冒險藝術家",
                "ESTP": "大膽企業家",
                "ESFP": "自由精神娛樂者"
            }
        },
        "vi": {
            "title": "Gợi ý Du lịch Busan theo MBTI",
            "subtitle": "Tìm những điểm du lịch phù hợp với loại tính cách của bạn!",
            "select_mbti": "Chọn MBTI của bạn",
            "test_mbti": "Làm bài kiểm tra MBTI",
            "recommend": "Nhận Gợi ý",
            "back": "Quay lại",
            "loading": "Đang tìm địa điểm được gợi ý...",
            "no_result": "Không tìm thấy gợi ý.",
            "mbti_descriptions": {
                "INTJ": "Kiến trúc sư Chiến lược",
                "INTP": "Nhà phân tích Logic",
                "ENTJ": "Chỉ huy Táo bạo",
                "ENTP": "Nhà tranh luận Thông minh",
                "INFJ": "Nhà hòa giải Giàu tưởng tượng",
                "INFP": "Nhà chữa lành Lý tưởng",
                "ENFJ": "Lãnh đạo Quyến rũ",
                "ENFP": "Nhà vận động Năng động",
                "ISTJ": "Nhà thực dụng Thực tế",
                "ISFJ": "Người bảo vệ Nhẹ nhàng",
                "ESTJ": "Quản lý Nghiêm khắc",
                "ESFJ": "Giám đốc Xã hội",
                "ISTP": "Bậc thầy Đa năng",
                "ISFP": "Nghệ sĩ Phiêu lưu",
                "ESTP": "Doanh nhân Táo bạo",
                "ESFP": "Nghệ sĩ Tự do"
            }
        },
        "th": {
            "title": "คำแนะนำการท่องเที่ยวปูซานตาม MBTI",
            "subtitle": "ค้นหาสถานที่ท่องเที่ยวที่เหมาะกับประเภทบุคลิกภาพของคุณ!",
            "select_mbti": "เลือก MBTI ของคุณ",
            "test_mbti": "ทำแบบทดสอบ MBTI",
            "recommend": "รับคำแนะนำ",
            "back": "กลับ",
            "loading": "กำลังค้นหาสถานที่แนะนำ...",
            "no_result": "ไม่พบคำแนะนำ",
            "mbti_descriptions": {
                "INTJ": "สถาปนิกเชิงกลยุทธ์",
                "INTP": "นักวิเคราะห์เชิงตรรกะ",
                "ENTJ": "ผู้บัญชาการที่กล้าหาญ",
                "ENTP": "นักโต้วาทีที่ฉลาด",
                "INFJ": "ผู้ไกล่เกลี่ยที่มีจินตนาการ",
                "INFP": "นักรักษาที่มีอุดมคติ",
                "ENFJ": "ผู้นำที่มีเสน่ห์",
                "ENFP": "นักรณรงค์ที่มีพลัง",
                "ISTJ": "นักปฏิบัติจริง",
                "ISFJ": "ผู้ปกป้องที่อ่อนโยน",
                "ESTJ": "ผู้จัดการที่เข้มงวด",
                "ESFJ": "ผู้บริหารเชิงสังคม",
                "ISTP": "นายช่างเอนกประสงค์",
                "ISFP": "ศิลปินผจญภัย",
                "ESTP": "ผู้ประกอบการที่กล้าหาญ",
                "ESFP": "นักแสดงจิตวิญญาณเสรี"
            }
        },
        "id": {
            "title": "Rekomendasi Wisata Busan berdasarkan MBTI",
            "subtitle": "Temukan tempat wisata yang cocok dengan tipe kepribadian Anda!",
            "select_mbti": "Pilih MBTI Anda",
            "test_mbti": "Ambil Tes MBTI",
            "recommend": "Dapatkan Rekomendasi",
            "back": "Kembali",
            "loading": "Mencari tempat yang direkomendasikan...",
            "no_result": "Tidak ditemukan rekomendasi.",
            "mbti_descriptions": {
                "INTJ": "Arsitek Strategis",
                "INTP": "Analis Logis",
                "ENTJ": "Komandan Berani",
                "ENTP": "Debater Cerdas",
                "INFJ": "Mediator Imajinatif",
                "INFP": "Penyembuh Idealis",
                "ENFJ": "Pemimpin Karismatik",
                "ENFP": "Aktivis Energik",
                "ISTJ": "Realis Praktis",
                "ISFJ": "Pelindung Lembut",
                "ESTJ": "Manajer Tegas",
                "ESFJ": "Eksekutif Sosial",
                "ISTP": "Virtuoso Serbaguna",
                "ISFP": "Seniman Petualang",
                "ESTP": "Pengusaha Berani",
                "ESFP": "Penghibur Jiwa Bebas"
            }
        },
        "fr": {
            "title": "Recommandations touristiques de Busan par MBTI",
            "subtitle": "Trouvez des attractions touristiques qui correspondent à votre type de personnalité !",
            "select_mbti": "Sélectionnez votre MBTI",
            "test_mbti": "Passer le test MBTI",
            "recommend": "Obtenir des recommandations",
            "back": "Retour",
            "loading": "Recherche de lieux recommandés...",
            "no_result": "Aucune recommandation trouvée.",
            "mbti_descriptions": {
                "INTJ": "Architecte Stratégique",
                "INTP": "Analyste Logique",
                "ENTJ": "Commandant Audacieux",
                "ENTP": "Débatteur Intelligent",
                "INFJ": "Médiateur Imaginatif",
                "INFP": "Guérisseur Idéaliste",
                "ENFJ": "Leader Charismatique",
                "ENFP": "Militant Énergique",
                "ISTJ": "Réaliste Pratique",
                "ISFJ": "Protecteur Doux",
                "ESTJ": "Manager Strict",
                "ESFJ": "Exécutif Social",
                "ISTP": "Virtuose Polyvalent",
                "ISFP": "Artiste Aventurier",
                "ESTP": "Entrepreneur Audacieux",
                "ESFP": "Artiste à l'Esprit Libre"
            }
        },
        "de": {
            "title": "Busan Tourismus-Empfehlungen nach MBTI",
            "subtitle": "Finden Sie Touristenattraktionen, die zu Ihrem Persönlichkeitstyp passen!",
            "select_mbti": "Wählen Sie Ihr MBTI",
            "test_mbti": "MBTI-Test machen",
            "recommend": "Empfehlungen erhalten",
            "back": "Zurück",
            "loading": "Suche empfohlene Orte...",
            "no_result": "Keine Empfehlungen gefunden.",
            "mbti_descriptions": {
                "INTJ": "Strategischer Architekt",
                "INTP": "Logischer Analyst",
                "ENTJ": "Mutiger Kommandeur",
                "ENTP": "Kluger Debattierer",
                "INFJ": "Einfallsreicher Vermittler",
                "INFP": "Idealistischer Heiler",
                "ENFJ": "Charismatischer Anführer",
                "ENFP": "Energischer Aktivist",
                "ISTJ": "Praktischer Realist",
                "ISFJ": "Sanfter Beschützer",
                "ESTJ": "Strenger Manager",
                "ESFJ": "Sozialer Exekutive",
                "ISTP": "Vielseitiger Virtuose",
                "ISFP": "Abenteuerlicher Künstler",
                "ESTP": "Mutiger Unternehmer",
                "ESFP": "Freigeistiger Entertainer"
            }
        },
        "tl": {
            "title": "Mga Rekomendasyon sa Turismo ng Busan ayon sa MBTI",
            "subtitle": "Hanapin ang mga tourist attraction na tumugma sa inyong personality type!",
            "select_mbti": "Piliin ang inyong MBTI",
            "test_mbti": "Gawin ang MBTI Test",
            "recommend": "Kunin ang mga Rekomendasyon",
            "back": "Bumalik",
            "loading": "Naghahanap ng mga inirerekomendang lugar...",
            "no_result": "Walang natagpuang rekomendasyon.",
            "mbti_descriptions": {
                "INTJ": "Strategic na Arkitekto",
                "INTP": "Logical na Analyst",
                "ENTJ": "Matapang na Kumander",
                "ENTP": "Matalinong Debater",
                "INFJ": "Mapagkukunwareng Tagapamagitan",
                "INFP": "Idealistic na Manggagamot",
                "ENFJ": "Charismatic na Lider",
                "ENFP": "Masigla na Aktivista",
                "ISTJ": "Praktikal na Realista",
                "ISFJ": "Mahinhing Tagaprotekta",
                "ESTJ": "Mahigpit na Manager",
                "ESFJ": "Social na Executive",
                "ISTP": "Versatile na Virtuoso",
                "ISFP": "Adventurous na Artist",
                "ESTP": "Matapang na Entrepreneur",
                "ESFP": "Free-spirited na Entertainer"
            }
        }
    }
    
    t = texts.get(lang, texts["ko"])
    
    # MBTI별 관광지 추천 데이터 JSON 파일에서 로드
    try:
        with open('mbti_recommendations.json', 'r', encoding='utf-8') as f:
            mbti_recommendations = json.load(f)
        print(f"MBTI 다국어 데이터 로드 성공! 포함된 MBTI 타입: {list(mbti_recommendations.keys())}")
        print(f"ISTJ 언어 지원: {list(mbti_recommendations.get('ISTJ', {}).keys()) if 'ISTJ' in mbti_recommendations else '없음'}")
    except FileNotFoundError:
        print("mbti_recommendations.json 파일을 찾을 수 없습니다.")
        # 기본 데이터 사용
        mbti_recommendations = {
        "INTJ": {
            "ko": {
                "title": "전략적 사고가 뛰어난 건축가형",
                "description": "조용하고 깊이 있는 경험을 선호하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "범어사", "category": "사찰", "reason": "조용하고 깊이 있는 불교 문화 체험"},
                    {"name": "부산박물관", "category": "박물관", "reason": "체계적이고 역사적인 정보 습득"},
                    {"name": "국립해양박물관", "category": "박물관", "reason": "해양 문화의 체계적 이해"},
                    {"name": "금정산성", "category": "역사", "reason": "전략적 관점에서 바라볼 수 있는 산성"},
                    {"name": "UN평화공원", "category": "공원", "reason": "역사적 의미를 되새길 수 있는 평화로운 공간"},
                    {"name": "송도구름산책로", "category": "산책로", "reason": "차분하게 사색할 수 있는 해안 산책로"},
                    {"name": "부산문화회관", "category": "문화시설", "reason": "다양한 예술 공연을 감상할 수 있는 문화 공간"},
                    {"name": "부산시립도서관", "category": "도서관", "reason": "조용한 학습과 독서 환경"},
                    {"name": "태종대 등대", "category": "등대", "reason": "고독한 사색과 바다 전망"},
                    {"name": "동래온천", "category": "온천", "reason": "조용한 힐링과 전통 문화 체험"},
                    {"name": "부산근현대역사관", "category": "역사관", "reason": "부산의 체계적인 역사 학습"},
                    {"name": "영화의전당", "category": "영화관", "reason": "예술 영화와 깊이 있는 문화 체험"}
                ]
            },
            "en": {
                "title": "Strategic Architect",
                "description": "Recommended for those who prefer quiet and deep experiences.",
                "attractions": [
                    {"name": "Beomeosa Temple", "category": "Temple", "reason": "Quiet and deep Buddhist cultural experience"},
                    {"name": "Busan Museum", "category": "Museum", "reason": "Systematic and historical information acquisition"},
                    {"name": "National Maritime Museum", "category": "Museum", "reason": "Systematic understanding of maritime culture"},
                    {"name": "Geumjeongsanseong Fortress", "category": "History", "reason": "Fortress viewable from strategic perspective"},
                    {"name": "UN Peace Park", "category": "Park", "reason": "Peaceful space to reflect on historical significance"},
                    {"name": "Songdo Cloud Walk", "category": "Walking Trail", "reason": "Coastal walking trail for quiet contemplation"},
                    {"name": "Busan Cultural Center", "category": "Cultural Facility", "reason": "Cultural space for various art performances"}
                ]
            }
        },
        "INTP": {
            "ko": {
                "title": "논리적 분석을 선호하는 논리술사형",
                "description": "독창적이고 지적인 호기심을 충족할 수 있는 곳을 추천합니다.",
                "attractions": [
                    {"name": "부산과학기술협의체", "category": "과학관", "reason": "과학 기술에 대한 깊이 있는 탐구"},
                    {"name": "부산현대미술관", "category": "미술관", "reason": "현대 예술의 새로운 해석과 분석"},
                    {"name": "태종대", "category": "자연", "reason": "지질학적 구조를 관찰할 수 있는 절벽"},
                    {"name": "을숙도 생태공원", "category": "생태공원", "reason": "생태계의 체계적 관찰과 연구"},
                    {"name": "부산진시장", "category": "전통시장", "reason": "전통 문화의 독특한 패턴 분석"},
                    {"name": "영화의전당", "category": "영화관", "reason": "영화 예술의 깊이 있는 분석과 감상"},
                    {"name": "부산도서관", "category": "도서관", "reason": "조용한 학습과 연구 공간"}
                ]
            },
            "en": {
                "title": "Logical Analyst",
                "description": "Recommended places to satisfy original and intellectual curiosity.",
                "attractions": [
                    {"name": "Busan Science & Technology Council", "category": "Science Center", "reason": "Deep exploration of science and technology"},
                    {"name": "Busan Museum of Contemporary Art", "category": "Art Museum", "reason": "New interpretation and analysis of contemporary art"},
                    {"name": "Taejongdae", "category": "Nature", "reason": "Cliffs for observing geological structures"},
                    {"name": "Eulsukdo Ecological Park", "category": "Ecological Park", "reason": "Systematic observation and research of ecosystems"},
                    {"name": "Busanjin Market", "category": "Traditional Market", "reason": "Analysis of unique patterns in traditional culture"},
                    {"name": "Busan Cinema Center", "category": "Cinema", "reason": "Deep analysis and appreciation of film art"},
                    {"name": "Busan Library", "category": "Library", "reason": "Quiet learning and research space"}
                ]
            }
        },
        "ENTJ": {
            "ko": {
                "title": "대담한 통솔력의 사령관형",
                "description": "역동적이고 도전적인 경험을 선호하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "부산국제금융센터(BIFC)", "category": "랜드마크", "reason": "부산의 경제 중심지에서 도시 전망 감상"},
                    {"name": "센텀시티", "category": "비즈니스 구역", "reason": "현대적인 비즈니스 환경과 쇼핑"},
                    {"name": "부산 벡스코", "category": "전시컨벤션", "reason": "국제적인 비즈니스와 문화 교류의 장"},
                    {"name": "해운대 마린시티", "category": "고급 주거지", "reason": "부산의 대표적인 고급 주거 및 상업 지구"},
                    {"name": "롯데백화점 센텀시티점", "category": "쇼핑몰", "reason": "세계 최대 규모 백화점에서의 쇼핑 경험"},
                    {"name": "광안리 더 베이", "category": "고급 레스토랑", "reason": "고급 다이닝과 해안 뷰를 즐길 수 있는 곳"},
                    {"name": "송도스카이워크", "category": "전망대", "reason": "바다 위에서 도전적인 경험과 전망"}
                ]
            },
            "en": {
                "title": "Bold Commander",
                "description": "Recommended for those who prefer dynamic and challenging experiences.",
                "attractions": [
                    {"name": "Busan International Finance Center (BIFC)", "category": "Landmark", "reason": "City view from Busan's economic center"},
                    {"name": "Centum City", "category": "Business District", "reason": "Modern business environment and shopping"},
                    {"name": "BEXCO Busan", "category": "Exhibition Convention", "reason": "Place for international business and cultural exchange"},
                    {"name": "Haeundae Marine City", "category": "Luxury Residential", "reason": "Busan's representative luxury residential and commercial district"},
                    {"name": "Lotte Department Store Centum City", "category": "Shopping Mall", "reason": "Shopping experience at world's largest department store"},
                    {"name": "The Bay Gwangalli", "category": "Fine Dining", "reason": "Place to enjoy fine dining and coastal views"},
                    {"name": "Songdo Skywalk", "category": "Observatory", "reason": "Challenging experience and views over the sea"}
                ]
            }
        },
        "ENTP": {
            "ko": {
                "title": "똑똑한 호기심의 변론가형",
                "description": "새로운 아이디어와 창의적 경험을 추구하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "F1963 복합문화공간", "category": "복합문화공간", "reason": "옛 고려제강 공장을 개조한 창의적 문화 공간"},
                    {"name": "부산현대미술관", "category": "미술관", "reason": "현대 예술의 실험적이고 창의적인 작품들"},
                    {"name": "을숙도문화회관", "category": "문화공간", "reason": "다양한 실험적 공연과 전시"},
                    {"name": "아르피나", "category": "갤러리", "reason": "젊은 작가들의 창의적인 작품 전시"},
                    {"name": "BTS 'Spring Day' 뮤직비디오 촬영지 (감천문화마을)", "category": "K-pop 성지", "reason": "BTS 뮤직비디오 촬영지로 유명한 컬러풀한 마을"},
                    {"name": "BIGBANG 승리 카페 'MONKEY MUSEUM'", "category": "K-pop 관련", "reason": "K-pop 아이돌과 연관된 독특한 카페 문화"},
                    {"name": "드라마 '도시남녀의 사랑법' 촬영지 (해리단길)", "category": "드라마 촬영지", "reason": "젊고 트렌디한 문화가 살아 숨쉬는 거리"}
                ]
            },
            "en": {
                "title": "Smart Debater",
                "description": "Recommended for those who pursue new ideas and creative experiences.",
                "attractions": [
                    {"name": "F1963 Cultural Complex", "category": "Cultural Complex", "reason": "Creative cultural space converted from old Korea Steel factory"},
                    {"name": "Busan Museum of Contemporary Art", "category": "Art Museum", "reason": "Experimental and creative works of contemporary art"},
                    {"name": "Eulsukdo Cultural Center", "category": "Cultural Space", "reason": "Various experimental performances and exhibitions"},
                    {"name": "Arpina", "category": "Gallery", "reason": "Creative works exhibition by young artists"},
                    {"name": "BTS 'Spring Day' MV Location (Gamcheon Culture Village)", "category": "K-pop Holy Site", "reason": "Colorful village famous as BTS music video filming location"},
                    {"name": "BIGBANG Seungri's Cafe 'MONKEY MUSEUM'", "category": "K-pop Related", "reason": "Unique cafe culture related to K-pop idols"},
                    {"name": "Drama 'City Couples' Way of Love' Location (Haeridan-gil)", "category": "Drama Location", "reason": "Street where young and trendy culture lives and breathes"}
                ]
            }
        },
        "INFJ": {
            "ko": {
                "title": "상상력이 풍부한 중재자형",
                "description": "의미 있고 깊이 있는 경험을 추구하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "해동용궁사", "category": "사찰", "reason": "바다와 조화를 이루는 영적인 공간"},
                    {"name": "태종대 등대", "category": "등대", "reason": "고독하고 사색적인 바다 전망"},
                    {"name": "흰여울문화마을", "category": "문화마을", "reason": "영화 '변호인' 촬영지로 깊은 의미를 담은 마을"},
                    {"name": "UN평화공원", "category": "추모공간", "reason": "평화와 희생에 대한 깊은 성찰"},
                    {"name": "보수동 책방골목", "category": "책방거리", "reason": "오래된 책들과 함께하는 조용한 사색의 시간"},
                    {"name": "드라마 '동백꽃 필 무렵' 촬영지 (구룡포)", "category": "드라마 촬영지", "reason": "따뜻한 인간애를 그린 드라마의 배경"},
                    {"name": "이기대 해안산책로", "category": "자연", "reason": "파도 소리와 함께하는 명상적 산책"}
                ]
            },
            "en": {
                "title": "Imaginative Mediator",
                "description": "Recommended for those who pursue meaningful and deep experiences.",
                "attractions": [
                    {"name": "Haedong Yonggungsa Temple", "category": "Temple", "reason": "Spiritual space harmonizing with the sea"},
                    {"name": "Taejongdae Lighthouse", "category": "Lighthouse", "reason": "Solitary and contemplative sea view"},
                    {"name": "Huinnyeoul Culture Village", "category": "Culture Village", "reason": "Village with deep meaning as filming location of movie 'The Attorney'"},
                    {"name": "UN Peace Park", "category": "Memorial Space", "reason": "Deep reflection on peace and sacrifice"},
                    {"name": "Bosu-dong Book Street", "category": "Book Street", "reason": "Quiet contemplation time with old books"},
                    {"name": "Drama 'When the Camellia Blooms' Location (Guryongpo)", "category": "Drama Location", "reason": "Background of drama depicting warm humanity"},
                    {"name": "Igidae Coastal Walking Trail", "category": "Nature", "reason": "Meditative walk with sound of waves"}
                ]
            }
        },
        "INFP": {
            "ko": {
                "title": "이상주의적 영감의 중재자형",
                "description": "감성적이고 아름다운 경험을 선호하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "감천문화마을", "category": "문화마을", "reason": "예술적 감성과 색채의 아름다움"},
                    {"name": "흰여울문화마을", "category": "문화마을", "reason": "바다와 어우러진 평화로운 분위기"},
                    {"name": "부산시립미술관", "category": "미술관", "reason": "예술적 영감을 받을 수 있는 공간"},
                    {"name": "해동용궁사", "category": "사찰", "reason": "바다를 품은 아름다운 사찰"},
                    {"name": "을숙도", "category": "자연", "reason": "자연의 평화로움을 느낄 수 있는 곳"},
                    {"name": "다대포 해수욕장 노을", "category": "자연", "reason": "부산에서 가장 아름다운 일몰 명소"},
                    {"name": "드라마 '꽃보다 남자' 촬영지 (신세계 센텀시티)", "category": "드라마 촬영지", "reason": "로맨틱한 드라마의 추억을 간직한 장소"}
                ]
            },
            "en": {
                "title": "Idealistic Healer",
                "description": "Recommended for those who prefer emotional and beautiful experiences.",
                "attractions": [
                    {"name": "Gamcheon Culture Village", "category": "Culture Village", "reason": "Artistic sensibility and beauty of colors"},
                    {"name": "Huinnyeoul Culture Village", "category": "Culture Village", "reason": "Peaceful atmosphere harmonizing with the sea"},
                    {"name": "Busan Museum of Art", "category": "Art Museum", "reason": "Space to receive artistic inspiration"},
                    {"name": "Haedong Yonggungsa Temple", "category": "Temple", "reason": "Beautiful temple embracing the sea"},
                    {"name": "Eulsukdo", "category": "Nature", "reason": "Place to feel the peace of nature"},
                    {"name": "Dadaepo Beach Sunset", "category": "Nature", "reason": "Most beautiful sunset spot in Busan"},
                    {"name": "Drama 'Boys Over Flowers' Location (Shinsegae Centum City)", "category": "Drama Location", "reason": "Place holding memories of romantic drama"}
                ]
            }
        },
        "ENFJ": {
            "ko": {
                "title": "카리스마 넘치는 선도자형",
                "description": "사람들과 함께하며 의미 있는 경험을 추구하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "부산시민공원", "category": "공원", "reason": "시민들과 함께 휴식할 수 있는 공동체 공간"},
                    {"name": "국제시장", "category": "전통시장", "reason": "상인들과의 따뜻한 소통과 전통문화 체험"},
                    {"name": "부산문화회관", "category": "문화시설", "reason": "다양한 공연을 통한 문화적 교류"},
                    {"name": "자갈치시장", "category": "수산시장", "reason": "생생한 부산 시민들의 삶과 문화"},
                    {"name": "BIFF 광장", "category": "영화거리", "reason": "영화와 문화를 사랑하는 사람들과의 만남"},
                    {"name": "광복로 문화거리", "category": "문화거리", "reason": "다양한 사람들과 문화를 공유하는 거리"},
                    {"name": "드라마 '선배, 그 립스틱 바르지 마요' 촬영지 (부산대학교)", "category": "드라마 촬영지", "reason": "청춘과 성장을 그린 드라마의 무대"}
                ]
            },
            "en": {
                "title": "Charismatic Leader",
                "description": "Recommended for those who pursue meaningful experiences together with people.",
                "attractions": [
                    {"name": "Busan Citizens Park", "category": "Park", "reason": "Community space to rest together with citizens"},
                    {"name": "Gukje Market", "category": "Traditional Market", "reason": "Warm communication with merchants and traditional culture experience"},
                    {"name": "Busan Cultural Center", "category": "Cultural Facility", "reason": "Cultural exchange through various performances"},
                    {"name": "Jagalchi Market", "category": "Fish Market", "reason": "Vivid life and culture of Busan citizens"},
                    {"name": "BIFF Square", "category": "Movie Street", "reason": "Meeting with people who love movies and culture"},
                    {"name": "Gwangbok-ro Cultural Street", "category": "Cultural Street", "reason": "Street to share culture with various people"},
                    {"name": "Drama 'Senior, Don't Put On That Lipstick' Location (Pusan National University)", "category": "Drama Location", "reason": "Stage of drama depicting youth and growth"}
                ]
            }
        },
        "ENFP": {
            "ko": {
                "title": "재기발랄한 활동가형",
                "description": "새롭고 다양한 경험을 선호하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "롯데월드 어드벤처 부산", "category": "테마파크", "reason": "다양한 어트랙션과 즐거운 경험"},
                    {"name": "해운대 블루라인 파크", "category": "관광열차", "reason": "새로운 관점에서 바라보는 해안선"},
                    {"name": "송도해상케이블카", "category": "케이블카", "reason": "바다 위에서의 스릴있는 경험"},
                    {"name": "부산 아쿠아리움", "category": "아쿠아리움", "reason": "다양한 해양 생물과의 만남"},
                    {"name": "BIFF 거리", "category": "문화거리", "reason": "영화와 예술의 다양한 문화 체험"},
                    {"name": "BTS 지민 아버지 카페 'MAGNATE'", "category": "K-pop 성지", "reason": "BTS 지민과 연관된 특별한 카페 경험"},
                    {"name": "드라마 '김비서가 왜 그럴까' 촬영지 (부산역)", "category": "드라마 촬영지", "reason": "인기 드라마의 로맨틱한 장면들의 배경"},
                    {"name": "해리단길", "category": "문화거리", "reason": "젊고 트렌디한 카페와 맛집 거리"},
                    {"name": "광안리 M 드론쇼", "category": "이벤트", "reason": "화려한 드론 라이트쇼 체험"},
                    {"name": "부산 X the SKY", "category": "전망대", "reason": "부산 최고층에서의 스카이라운지 체험"},
                    {"name": "F1963 복합문화공간", "category": "복합문화공간", "reason": "창의적이고 실험적인 문화 체험"},
                    {"name": "다이아몬드베이", "category": "쇼핑몰", "reason": "바다 전망과 함께하는 쇼핑 체험"},
                    {"name": "부산 VR파크", "category": "VR체험", "reason": "최신 가상현실 게임과 체험"}
                ]
            },
            "en": {
                "title": "Energetic Campaigner",
                "description": "Recommended for those who prefer new and diverse experiences.",
                "attractions": [
                    {"name": "Lotte World Adventure Busan", "category": "Theme Park", "reason": "Various attractions and fun experiences"},
                    {"name": "Haeundae Blueline Park", "category": "Tourist Train", "reason": "Coastline viewed from new perspective"},
                    {"name": "Songdo Marine Cable Car", "category": "Cable Car", "reason": "Thrilling experience over the sea"},
                    {"name": "Busan Aquarium", "category": "Aquarium", "reason": "Meeting with various marine life"},
                    {"name": "BIFF Street", "category": "Cultural Street", "reason": "Diverse cultural experiences of film and art"},
                    {"name": "BTS Jimin's Father's Cafe 'MAGNATE'", "category": "K-pop Holy Site", "reason": "Special cafe experience related to BTS Jimin"},
                    {"name": "Drama 'What's Wrong with Secretary Kim' Location (Busan Station)", "category": "Drama Location", "reason": "Background of romantic scenes from popular drama"}
                ]
            }
        },
        "ISTJ": {
            "ko": {
                "title": "실용적인 현실주의자형",
                "description": "체계적이고 실용적인 경험을 선호하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "국제시장", "category": "전통시장", "reason": "실용적인 쇼핑과 지역 문화 체험"},
                    {"name": "자갈치시장", "category": "수산시장", "reason": "부산의 대표적인 실용적 시장"},
                    {"name": "부산시민공원", "category": "공원", "reason": "체계적으로 조성된 도시 공원"},
                    {"name": "용두산공원", "category": "공원", "reason": "부산 시내를 한눈에 볼 수 있는 전망대"},
                    {"name": "부산타워", "category": "전망대", "reason": "부산의 상징적인 랜드마크"},
                    {"name": "광복로", "category": "쇼핑거리", "reason": "체계적으로 정비된 부산의 대표 쇼핑가"},
                    {"name": "서면", "category": "상업지구", "reason": "교통이 편리하고 다양한 편의시설이 집중된 곳"}
                ]
            },
            "en": {
                "title": "Practical Realist",
                "description": "Recommended for those who prefer systematic and practical experiences.",
                "attractions": [
                    {"name": "Gukje Market", "category": "Traditional Market", "reason": "Practical shopping and local culture experience"},
                    {"name": "Jagalchi Market", "category": "Fish Market", "reason": "Busan's representative practical market"},
                    {"name": "Busan Citizens Park", "category": "Park", "reason": "Systematically organized urban park"},
                    {"name": "Yongdusan Park", "category": "Park", "reason": "Observatory with panoramic view of Busan"},
                    {"name": "Busan Tower", "category": "Observatory", "reason": "Symbolic landmark of Busan"},
                    {"name": "Gwangbok-ro", "category": "Shopping Street", "reason": "Systematically organized representative shopping area of Busan"},
                    {"name": "Seomyeon", "category": "Business District", "reason": "Place with convenient transportation and concentrated various facilities"}
                ]
            }
        },
        "ISFJ": {
            "ko": {
                "title": "온화한 수호자형",
                "description": "조용하고 아늑한 환경에서 의미있는 시간을 보내고 싶은 당신에게 추천합니다.",
                "attractions": [
                    {"name": "범어사", "category": "사찰", "reason": "평화로운 분위기에서 마음의 안정을 찾을 수 있는 곳"},
                    {"name": "동래온천", "category": "온천", "reason": "따뜻하고 치유적인 온천 경험"},
                    {"name": "부산박물관", "category": "박물관", "reason": "조용한 환경에서 역사와 문화를 학습"},
                    {"name": "온천천 시민공원", "category": "공원", "reason": "자연 속에서 편안한 산책과 휴식"},
                    {"name": "민락수변공원", "category": "공원", "reason": "바다를 바라보며 평온한 시간을 보낼 수 있는 곳"},
                    {"name": "드라마 '하이킥! 짧은 다리의 역습' 촬영지 (동래구)", "category": "드라마 촬영지", "reason": "따뜻한 가족 드라마의 배경이 된 정겨운 동네"},
                    {"name": "보수동 책방골목", "category": "책방거리", "reason": "조용히 책을 읽으며 여유로운 시간을 보낼 수 있는 곳"}
                ]
            },
            "en": {
                "title": "Gentle Protector",
                "description": "Recommended for those who want to spend meaningful time in quiet and cozy environments.",
                "attractions": [
                    {"name": "Beomeosa Temple", "category": "Temple", "reason": "Place to find peace of mind in peaceful atmosphere"},
                    {"name": "Dongnae Hot Springs", "category": "Hot Springs", "reason": "Warm and healing hot spring experience"},
                    {"name": "Busan Museum", "category": "Museum", "reason": "Learning history and culture in quiet environment"},
                    {"name": "Oncheoncheon Citizens Park", "category": "Park", "reason": "Comfortable walk and rest in nature"},
                    {"name": "Millak Waterside Park", "category": "Park", "reason": "Place to spend peaceful time looking at the sea"},
                    {"name": "Drama 'High Kick! Revenge of the Short Legged' Location (Dongnae-gu)", "category": "Drama Location", "reason": "Heartwarming neighborhood that became background of warm family drama"},
                    {"name": "Bosu-dong Book Street", "category": "Book Street", "reason": "Place to spend leisurely time reading quietly"}
                ]
            }
        },
        "ESTJ": {
            "ko": {
                "title": "엄격한 관리자형",
                "description": "체계적이고 효율적인 일정으로 부산의 주요 명소들을 둘러보고 싶은 당신에게 추천합니다.",
                "attractions": [
                    {"name": "부산항대교", "category": "랜드마크", "reason": "부산의 대표적인 현대 건축물과 도시 발전상"},
                    {"name": "벡스코(BEXCO)", "category": "전시컨벤션", "reason": "대규모 국제 행사와 비즈니스 센터"},
                    {"name": "센텀시티", "category": "비즈니스 구역", "reason": "체계적으로 계획된 현대적 도시 구역"},
                    {"name": "신세계 센텀시티", "category": "백화점", "reason": "효율적인 쇼핑과 다양한 브랜드 집약"},
                    {"name": "해운대 센텀호텔", "category": "호텔", "reason": "높은 품질의 서비스와 체계적인 시설"},
                    {"name": "부산시청", "category": "관공서", "reason": "부산의 행정 중심지 견학"},
                    {"name": "KBS부산방송총국", "category": "방송국", "reason": "체계적인 방송 시설과 미디어 산업 이해"}
                ]
            },
            "en": {
                "title": "Strict Manager",
                "description": "Recommended for those who want to tour major attractions in Busan with systematic and efficient schedule.",
                "attractions": [
                    {"name": "Busan Harbor Bridge", "category": "Landmark", "reason": "Representative modern architecture and urban development of Busan"},
                    {"name": "BEXCO", "category": "Exhibition Convention", "reason": "Large-scale international events and business center"},
                    {"name": "Centum City", "category": "Business District", "reason": "Systematically planned modern urban area"},
                    {"name": "Shinsegae Centum City", "category": "Department Store", "reason": "Efficient shopping and diverse brand concentration"},
                    {"name": "Haeundae Centum Hotel", "category": "Hotel", "reason": "High-quality service and systematic facilities"},
                    {"name": "Busan City Hall", "category": "Government Office", "reason": "Tour of Busan's administrative center"},
                    {"name": "KBS Busan Broadcasting Station", "category": "Broadcasting Station", "reason": "Understanding systematic broadcasting facilities and media industry"}
                ]
            }
        },
        "ESFJ": {
            "ko": {
                "title": "사교적인 집정관형",
                "description": "사람들과 함께 즐겁게 시간을 보내며 다양한 문화를 경험하고 싶은 당신에게 추천합니다.",
                "attractions": [
                    {"name": "해운대 해수욕장", "category": "해수욕장", "reason": "많은 사람들과 함께 즐기는 활기찬 해변"},
                    {"name": "광안리 해수욕장", "category": "해수욕장", "reason": "야경과 함께하는 로맨틱한 분위기"},
                    {"name": "부평깡통야시장", "category": "야시장", "reason": "다양한 먹거리와 사람들과의 소통"},
                    {"name": "전포카페거리", "category": "카페거리", "reason": "트렌디한 카페에서 친구들과의 시간"},
                    {"name": "남포동", "category": "상업지구", "reason": "쇼핑과 맛집이 집중된 활기찬 거리"},
                    {"name": "드라마 '시크릿 가든' 촬영지 (롯데호텔 부산)", "category": "드라마 촬영지", "reason": "인기 드라마의 로맨틱한 장면들의 배경"},
                    {"name": "2NE1 박봄 가족 운영 카페", "category": "K-pop 관련", "reason": "K-pop 스타와 연관된 특별한 카페 체험"}
                ]
            },
            "en": {
                "title": "Sociable Executive",
                "description": "Recommended for those who want to spend enjoyable time with people and experience various cultures.",
                "attractions": [
                    {"name": "Haeundae Beach", "category": "Beach", "reason": "Lively beach enjoyed together with many people"},
                    {"name": "Gwangalli Beach", "category": "Beach", "reason": "Romantic atmosphere with night view"},
                    {"name": "Bupyeong Kkangtong Night Market", "category": "Night Market", "reason": "Various food and communication with people"},
                    {"name": "Jeonpo Cafe Street", "category": "Cafe Street", "reason": "Time with friends in trendy cafes"},
                    {"name": "Nampo-dong", "category": "Business District", "reason": "Lively street concentrated with shopping and restaurants"},
                    {"name": "Drama 'Secret Garden' Location (Lotte Hotel Busan)", "category": "Drama Location", "reason": "Background of romantic scenes from popular drama"},
                    {"name": "2NE1 Park Bom's Family Cafe", "category": "K-pop Related", "reason": "Special cafe experience related to K-pop star"}
                ]
            }
        },
        "ISTP": {
            "ko": {
                "title": "만능 재주꾼형",
                "description": "실용적이고 손으로 직접 체험할 수 있는 활동을 선호하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "국립해양박물관", "category": "박물관", "reason": "해양 기술과 선박 구조를 직접 체험"},
                    {"name": "부산과학체험관", "category": "과학관", "reason": "다양한 과학 실험과 체험 활동"},
                    {"name": "태종대", "category": "자연", "reason": "자연 환경을 직접 탐험하고 관찰"},
                    {"name": "송도해상케이블카", "category": "케이블카", "reason": "기계적 구조물의 작동 원리 체험"},
                    {"name": "부산항", "category": "항구", "reason": "대형 선박과 항만 시설의 실제 작동 관찰"},
                    {"name": "이기대 해안산책로", "category": "자연", "reason": "자연의 지질 구조를 직접 관찰하고 탐험"},
                    {"name": "동래 민속예술관", "category": "예술관", "reason": "전통 공예 기술의 실제 제작 과정 관찰"}
                ]
            },
            "en": {
                "title": "Versatile Virtuoso",
                "description": "Recommended for those who prefer practical and hands-on experiences.",
                "attractions": [
                    {"name": "National Maritime Museum", "category": "Museum", "reason": "Direct experience of marine technology and ship structures"},
                    {"name": "Busan Science Experience Center", "category": "Science Center", "reason": "Various science experiments and hands-on activities"},
                    {"name": "Taejongdae", "category": "Nature", "reason": "Direct exploration and observation of natural environment"},
                    {"name": "Songdo Marine Cable Car", "category": "Cable Car", "reason": "Experience working principles of mechanical structures"},
                    {"name": "Busan Port", "category": "Port", "reason": "Actual operation observation of large ships and port facilities"},
                    {"name": "Igidae Coastal Walking Trail", "category": "Nature", "reason": "Direct observation and exploration of natural geological structures"},
                    {"name": "Dongnae Folk Art Center", "category": "Art Center", "reason": "Observation of actual production process of traditional crafts"}
                ]
            }
        },
        "ISFP": {
            "ko": {
                "title": "호기심 많은 예술가형",
                "description": "아름다운 자연과 예술적 경험을 통해 영감을 얻고 싶은 당신에게 추천합니다.",
                "attractions": [
                    {"name": "감천문화마을", "category": "문화마을", "reason": "다채로운 색상과 예술 작품들로 가득한 마을"},
                    {"name": "해동용궁사", "category": "사찰", "reason": "바다와 어우러진 아름다운 건축미"},
                    {"name": "다대포 해수욕장", "category": "해수욕장", "reason": "부산에서 가장 아름다운 일몰을 감상"},
                    {"name": "부산현대미술관", "category": "미술관", "reason": "현대 예술의 다양한 표현과 창작 기법"},
                    {"name": "을숙도 생태공원", "category": "생태공원", "reason": "자연의 아름다움과 생태계의 조화"},
                    {"name": "흰여울문화마을", "category": "문화마을", "reason": "영화 '변호인'의 촬영지로 유명한 서정적인 마을"},
                    {"name": "드라마 '도깨비' 촬영지 (광안대교)", "category": "드라마 촬영지", "reason": "아름다운 야경으로 유명한 로맨틱한 드라마 배경"}
                ]
            },
            "en": {
                "title": "Curious Artist",
                "description": "Recommended for those who want to gain inspiration through beautiful nature and artistic experiences.",
                "attractions": [
                    {"name": "Gamcheon Culture Village", "category": "Culture Village", "reason": "Village full of colorful colors and art works"},
                    {"name": "Haedong Yonggungsa Temple", "category": "Temple", "reason": "Beautiful architecture harmonizing with the sea"},
                    {"name": "Dadaepo Beach", "category": "Beach", "reason": "Viewing the most beautiful sunset in Busan"},
                    {"name": "Busan Museum of Contemporary Art", "category": "Art Museum", "reason": "Various expressions and creative techniques of contemporary art"},
                    {"name": "Eulsukdo Ecological Park", "category": "Ecological Park", "reason": "Beauty of nature and harmony of ecosystem"},
                    {"name": "Huinnyeoul Culture Village", "category": "Culture Village", "reason": "Lyrical village famous as filming location of movie 'The Attorney'"},
                    {"name": "Drama 'Goblin' Location (Gwangandaegyo Bridge)", "category": "Drama Location", "reason": "Romantic drama background famous for beautiful night view"}
                ]
            }
        },
        "ESTP": {
            "ko": {
                "title": "대담한 사업가형",
                "description": "역동적이고 즉흥적인 활동을 즐기며 새로운 경험을 추구하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "송도해상케이블카", "category": "케이블카", "reason": "스릴있는 바다 위 케이블카 체험"},
                    {"name": "롯데월드 어드벤처 부산", "category": "테마파크", "reason": "다양한 놀이기구와 스릴 넘치는 경험"},
                    {"name": "해운대 해수욕장", "category": "해수욕장", "reason": "다양한 수상 스포츠와 비치 액티비티"},
                    {"name": "광안리 해수욕장", "category": "해수욕장", "reason": "서핑과 요트 등 해상 스포츠 체험"},
                    {"name": "부평깡통야시장", "category": "야시장", "reason": "활기찬 밤 문화와 즉석 먹거리 체험"},
                    {"name": "드라마 '상속자들' 촬영지 (부산 마린시티)", "category": "드라마 촬영지", "reason": "화려하고 역동적인 도시 배경의 드라마 장소"},
                    {"name": "BIGBANG 대성 가족 운영 펜션", "category": "K-pop 관련", "reason": "K-pop 스타와 연관된 특별한 숙박 체험"}
                ]
            },
            "en": {
                "title": "Bold Entrepreneur",
                "description": "Recommended for those who enjoy dynamic and spontaneous activities and pursue new experiences.",
                "attractions": [
                    {"name": "Songdo Marine Cable Car", "category": "Cable Car", "reason": "Thrilling cable car experience over the sea"},
                    {"name": "Lotte World Adventure Busan", "category": "Theme Park", "reason": "Various rides and thrilling experiences"},
                    {"name": "Haeundae Beach", "category": "Beach", "reason": "Various water sports and beach activities"},
                    {"name": "Gwangalli Beach", "category": "Beach", "reason": "Marine sports experience like surfing and yachting"},
                    {"name": "Bupyeong Kkangtong Night Market", "category": "Night Market", "reason": "Lively night culture and instant food experience"},
                    {"name": "Drama 'The Heirs' Location (Busan Marine City)", "category": "Drama Location", "reason": "Drama location with glamorous and dynamic city background"},
                    {"name": "BIGBANG Daesung's Family Pension", "category": "K-pop Related", "reason": "Special accommodation experience related to K-pop star"}
                ]
            }
        },
        "ESFP": {
            "ko": {
                "title": "자유로운 영혼의 연예인형",
                "description": "즐겁고 활기찬 분위기를 선호하는 당신에게 추천합니다.",
                "attractions": [
                    {"name": "해운대 해수욕장", "category": "해수욕장", "reason": "활기찬 해변 분위기와 다양한 활동"},
                    {"name": "광안리 해수욕장", "category": "해수욕장", "reason": "야경과 함께하는 즐거운 분위기"},
                    {"name": "부평깡통야시장", "category": "야시장", "reason": "다양한 먹거리와 즐거운 밤 문화"},
                    {"name": "전포카페거리", "category": "카페거리", "reason": "트렌디하고 활기찬 카페 문화"},
                    {"name": "해리단길", "category": "문화거리", "reason": "젊고 활기찬 문화 공간"},
                    {"name": "남포동 BIFF 광장", "category": "영화거리", "reason": "영화제의 열기가 살아있는 활기찬 거리"},
                    {"name": "드라마 '피노키오' 촬영지 (KBS부산방송총국)", "category": "드라마 촬영지", "reason": "방송 드라마의 화려한 무대 배경"},
                    {"name": "광복로 패션거리", "category": "쇼핑거리", "reason": "최신 패션과 트렌드를 만나는 활기찬 거리"},
                    {"name": "센텀시티 신세계백화점", "category": "쇼핑몰", "reason": "세계 최대 백화점에서의 쇼핑과 문화 체험"},
                    {"name": "송정 비치클럽", "category": "비치클럽", "reason": "음악과 함께하는 해변 파티 문화"},
                    {"name": "광안리 M 드론쇼", "category": "이벤트", "reason": "화려한 드론 라이트쇼와 축제 분위기"},
                    {"name": "부산 락페스티벌", "category": "음악축제", "reason": "다양한 음악과 공연이 있는 축제"},
                    {"name": "해운대 아이스 아레나", "category": "스포츠", "reason": "아이스스케이팅과 다양한 겨울 스포츠"}
                ]
            },
            "en": {
                "title": "Free-spirited Entertainer",
                "description": "Recommended for those who prefer fun and lively atmosphere.",
                "attractions": [
                    {"name": "Haeundae Beach", "category": "Beach", "reason": "Lively beach atmosphere and various activities"},
                    {"name": "Gwangalli Beach", "category": "Beach", "reason": "Fun atmosphere with night view"},
                    {"name": "Bupyeong Kkangtong Night Market", "category": "Night Market", "reason": "Various food and fun night culture"},
                    {"name": "Jeonpo Cafe Street", "category": "Cafe Street", "reason": "Trendy and lively cafe culture"},
                    {"name": "Haeridan-gil", "category": "Cultural Street", "reason": "Young and lively cultural space"},
                    {"name": "Nampo-dong BIFF Square", "category": "Movie Street", "reason": "Lively street where the heat of film festival lives on"},
                    {"name": "Drama 'Pinocchio' Location (KBS Busan Broadcasting Station)", "category": "Drama Location", "reason": "Glamorous stage background of broadcasting drama"}
                ]
            }
        }
    }
    
    # MBTI 목록
    mbti_list = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP", 
                  "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]
    
    # 전역 변수 사용
    global _global_selected_mbti, _global_result_view, _global_current_lang
    
    # 언어가 변경되었는지 확인하고, 변경되었다면 상태 초기화
    if _global_current_lang != lang:
        print(f"언어 변경 감지됨: {_global_current_lang} -> {lang}")
        _global_selected_mbti = None
        _global_result_view = None
        _global_current_lang = lang
        print("MBTI 선택 상태가 초기화되었습니다.")
    
    # 전역 변수에서 값 가져오기 (언어 변경 시에는 무시됨)
    if selected_mbti_value is not None:
        _global_selected_mbti = selected_mbti_value
    if result_view_value is not None:
        _global_result_view = result_view_value
    
    # 로컬 변수로 참조
    selected_mbti = [_global_selected_mbti]
    result_view = [_global_result_view]
    
    def on_mbti_selected(mbti):
        global _global_selected_mbti, _global_result_view
        print(f"MBTI 선택됨: {mbti}")
        _global_selected_mbti = mbti
        _global_result_view = None
        # 페이지를 다시 로드하여 UI 업데이트
        page.views.clear()
        page.views.append(MBTITourismPage(page, lang, on_back, _global_selected_mbti, _global_result_view))
        page.update()
    

    
    def on_test_complete(test_result):
        """MBTI 테스트 완료 후 호출되는 함수"""
        global _global_selected_mbti, _global_result_view
        print(f"MBTI 테스트 완료! 결과: {test_result}")
        _global_selected_mbti = test_result
        _global_result_view = None
        # MBTI 페이지로 돌아가서 결과 표시
        page.views.clear()
        page.views.append(MBTITourismPage(page, lang, on_back, _global_selected_mbti, _global_result_view))
        page.update()
    
    def start_mbti_test():
        """MBTI 테스트 시작"""
        global _test_answers, _current_question
        # 테스트 상태 초기화
        _test_answers = []
        _current_question = 0
        show_mbti_test(page, lang, on_test_complete)
    
    def show_recommendations():
        print(f"추천받기 버튼 클릭됨! 선택된 MBTI: {selected_mbti[0]}")
        if not selected_mbti[0]:
            print("선택된 MBTI가 없습니다.")
            return
        
        mbti = selected_mbti[0]
        print(f"MBTI {mbti}에 대한 추천을 생성합니다...")
        print(f"현재 언어: {lang}")
        print(f"mbti_recommendations에서 사용 가능한 MBTI: {list(mbti_recommendations.keys()) if mbti_recommendations else '없음'}")
        print(f"MBTI {mbti}가 데이터에 있는지: {mbti in mbti_recommendations if mbti_recommendations else False}")
        
        if mbti not in mbti_recommendations:
            print(f"MBTI {mbti}는 기본 추천을 사용합니다.")
            # 이 경우는 이제 발생하지 않습니다 (모든 16개 MBTI 유형이 구현됨)
            default_recommendations = {
                "ko": {
                    "title": f"{mbti} 유형을 위한 추천",
                    "description": "부산의 다양한 관광지를 추천합니다.",
                    "attractions": [
                        {"name": "해운대 해수욕장", "category": "해수욕장", "reason": "부산의 대표적인 해수욕장"},
                        {"name": "광안대교", "category": "랜드마크", "reason": "부산의 상징적인 다리"},
                        {"name": "용두산공원", "category": "공원", "reason": "부산 시내를 한눈에 볼 수 있는 전망대"},
                        {"name": "자갈치시장", "category": "시장", "reason": "부산의 대표적인 수산시장"},
                        {"name": "감천문화마을", "category": "문화마을", "reason": "부산의 대표적인 문화마을"},
                        {"name": "BTS 관련 명소", "category": "K-pop 성지", "reason": "한류 문화의 중심지"},
                        {"name": "드라마 촬영지", "category": "드라마 촬영지", "reason": "인기 드라마의 배경이 된 장소"}
                    ]
                },
                "en": {
                    "title": f"Recommendations for {mbti}",
                    "description": "Recommended diverse tourist attractions in Busan.",
                    "attractions": [
                        {"name": "Haeundae Beach", "category": "Beach", "reason": "Representative beach of Busan"},
                        {"name": "Gwangandaegyo Bridge", "category": "Landmark", "reason": "Symbolic bridge of Busan"},
                        {"name": "Yongdusan Park", "category": "Park", "reason": "Observatory with panoramic view of Busan"},
                        {"name": "Jagalchi Market", "category": "Market", "reason": "Representative fish market of Busan"},
                        {"name": "Gamcheon Culture Village", "category": "Culture Village", "reason": "Representative culture village of Busan"},
                        {"name": "BTS Related Sites", "category": "K-pop Holy Site", "reason": "Center of Korean Wave culture"},
                        {"name": "Drama Filming Locations", "category": "Drama Location", "reason": "Places that became backgrounds of popular dramas"}
                    ]
                }
            }
            recommendations = default_recommendations
        else:
            print(f"MBTI {mbti}의 특별한 추천을 사용합니다.")
            recommendations = mbti_recommendations[mbti]
        
        rec_data = recommendations.get(lang, recommendations.get("ko", recommendations["ko"]))
        print(f"추천 데이터 생성 완료: {rec_data['title']}")
        
        # 결과 화면 생성
        result_view[0] = ft.Container(
            content=ft.ListView(
                controls=[
                    ft.Text(rec_data["title"], size=title_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600),
                    ft.Text(rec_data["description"], size=subtitle_size, color=ft.Colors.GREY_700),
                    ft.Container(height=16),
                    *[
                        ft.Container(
                            content=ft.Column([
                                # 첫 번째 줄: 관광지 이름 + 지도 버튼
                                ft.Row([
                                    ft.Text(
                                        # 관광지 이름 다국어 변환 개선
                                        attraction_name_mapping.get(lang, {}).get(attraction["name"]) or 
                                        attraction_name_mapping.get("en", {}).get(attraction["name"]) or 
                                        attraction["name"],
                                        size=18 if is_mobile else 20, 
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLUE_800,
                                        expand=True
                                    ),
                                    ft.ElevatedButton(
                                        {
                                            "ko": "📍 지도",
                                            "en": "📍 Map",
                                            "ja": "📍 地図", 
                                            "zh": "📍 地图"
                                        }.get(lang, "📍 Map"),
                                        on_click=lambda e, attraction_name=attraction["name"], current_lang=lang: open_google_maps_directly(page, attraction_name, current_lang),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.ORANGE_100,
                                            color=ft.Colors.ORANGE_800,
                                            padding=ft.padding.symmetric(horizontal=12, vertical=6)
                                        ),
                                        height=32
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                # 두 번째 줄: 카테고리 + 추천 이유
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text(
                                            # 카테고리 다국어 매핑 간소화
                                            attraction["category"],
                                            size=12 if is_mobile else 13,
                                            color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.W_500
                                        ),
                                        bgcolor=ft.Colors.BLUE_400,
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        border_radius=15,
                                        margin=ft.margin.only(right=8)
                                    ),
                                    ft.Text(
                                        attraction["reason"][:50] + "..." if len(attraction["reason"]) > 50 else attraction["reason"], 
                                        size=13 if is_mobile else 14, 
                                        color=ft.Colors.GREY_700,
                                        expand=True
                                    )
                                ], alignment=ft.MainAxisAlignment.START)
                            ], spacing=8),
                            padding=16,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=12,
                            border=ft.border.all(1, ft.Colors.GREY_200),
                            margin=ft.margin.only(bottom=12),
                            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2))
                        ) for attraction in rec_data["attractions"]
                    ]
                ],
                spacing=8
            ),
            padding=16,
            bgcolor=ft.LinearGradient(["#F8F9FF", "#E8EAFF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
            border_radius=12,
            margin=ft.margin.only(top=16),
            height=400  # 고정 높이 설정
        )
        
        print("결과 화면 생성 완료, 페이지 업데이트 중...")
        # 전역 변수에 결과 저장
        global _global_result_view
        _global_result_view = result_view[0]
        # 페이지를 새로 로드하여 결과를 표시
        page.views.clear()
        page.views.append(MBTITourismPage(page, lang, on_back, _global_selected_mbti, _global_result_view))
        page.update()
    
    # MBTI 선택 버튼들
    mbti_buttons = []
    
    # 각 MBTI에 대한 개별 클릭 함수들
    def click_intj(e): on_mbti_selected("INTJ")
    def click_intp(e): on_mbti_selected("INTP")
    def click_entj(e): on_mbti_selected("ENTJ")
    def click_entp(e): on_mbti_selected("ENTP")
    def click_infj(e): on_mbti_selected("INFJ")
    def click_infp(e): on_mbti_selected("INFP")
    def click_enfj(e): on_mbti_selected("ENFJ")
    def click_enfp(e): on_mbti_selected("ENFP")
    def click_istj(e): on_mbti_selected("ISTJ")
    def click_isfj(e): on_mbti_selected("ISFJ")
    def click_estj(e): on_mbti_selected("ESTJ")
    def click_esfj(e): on_mbti_selected("ESFJ")
    def click_istp(e): on_mbti_selected("ISTP")
    def click_isfp(e): on_mbti_selected("ISFP")
    def click_estp(e): on_mbti_selected("ESTP")
    def click_esfp(e): on_mbti_selected("ESFP")
    
    # MBTI별 클릭 함수 매핑
    click_handlers = {
        "INTJ": click_intj, "INTP": click_intp, "ENTJ": click_entj, "ENTP": click_entp,
        "INFJ": click_infj, "INFP": click_infp, "ENFJ": click_enfj, "ENFP": click_enfp,
        "ISTJ": click_istj, "ISFJ": click_isfj, "ESTJ": click_estj, "ESFJ": click_esfj,
        "ISTP": click_istp, "ISFP": click_isfp, "ESTP": click_estp, "ESFP": click_esfp
    }
    
    for mbti in mbti_list:
        is_selected = selected_mbti[0] == mbti
        
        button_size = min(75, (page.width - 80) // 4) if hasattr(page, 'width') and page.width else 75
        mbti_buttons.append(
            ft.Container(
                content=ft.Text(mbti, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_selected else ft.Colors.BLACK87),
                width=button_size,
                height=button_size,
                bgcolor=ft.Colors.BLUE_600 if is_selected else ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(2, ft.Colors.BLUE_600 if is_selected else ft.Colors.GREY_300),
                on_click=click_handlers[mbti],
                alignment=ft.alignment.center
            )
        )
    
    # 선택된 MBTI 표시 텍스트
    selected_text = {
        "ko": f"선택된 MBTI: {selected_mbti[0]}" if selected_mbti[0] else "MBTI를 선택해주세요",
        "en": f"Selected MBTI: {selected_mbti[0]}" if selected_mbti[0] else "Please select your MBTI",
        "ja": f"選択されたMBTI: {selected_mbti[0]}" if selected_mbti[0] else "MBTIを選択してください"
    }
    
    return ft.View(
        "/mbti_tourism",
        controls=[
            # 헤더
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Text(t["title"], size=title_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
            ], alignment=ft.MainAxisAlignment.START, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            
            # 설명
            ft.Text(t["subtitle"], size=subtitle_size, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
            
            ft.Container(height=24),
            
            # MBTI 선택 섹션
            ft.Text(t["select_mbti"], size=text_size, weight=ft.FontWeight.BOLD),
            ft.Container(height=12),
            
            # 선택된 MBTI 표시
            ft.Container(
                content=ft.Text(
                    selected_text.get(lang, selected_text["ko"]),
                    size=14,
                    color=ft.Colors.BLUE_600 if selected_mbti[0] else ft.Colors.GREY_600,
                    weight=ft.FontWeight.BOLD if selected_mbti[0] else ft.FontWeight.NORMAL,
                    text_align=ft.TextAlign.CENTER
                ),
                margin=ft.margin.only(bottom=12)
            ),
            
            # MBTI 버튼 그리드 (4x4)
            ft.Container(
                content=ft.Column([
                    ft.Row(mbti_buttons[i:i+4], alignment=ft.MainAxisAlignment.CENTER, spacing=8)
                    for i in range(0, len(mbti_buttons), 4)
                ], spacing=8),
                padding=16
            ),
            
            # MBTI 테스트 버튼
            ft.Container(
                content=ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.QUIZ, size=16),
                        ft.Text(t["test_mbti"], size=14)
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                    on_click=lambda e: start_mbti_test(),
                    height=40,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.PURPLE_100,
                        color=ft.Colors.PURPLE_800,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                ),
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=16, bottom=8),
                width=min(280, page.width - 40) if hasattr(page, 'width') and page.width else 280,
                padding=ft.padding.symmetric(horizontal=20)
            ),
            
            # 추천 버튼
            ft.Container(
                content=ft.ElevatedButton(
                    t["recommend"],
                    on_click=lambda e: show_recommendations(),
                    disabled=selected_mbti[0] is None,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_600 if selected_mbti[0] else ft.Colors.GREY_400,
                        color=ft.Colors.WHITE
                    )
                ),
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=16),
                width=min(300, page.width - 40) if hasattr(page, 'width') and page.width else 300,
                padding=ft.padding.symmetric(horizontal=20)
            ),
            
            # 결과 표시
            result_view[0] if result_view[0] else ft.Container(),
        ],
        scroll=ft.ScrollMode.AUTO,
        bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=ft.padding.only(bottom=20 if is_mobile else 32)
    )

def show_attraction_images_with_loading(page, attraction_name, lang="ko"):
    """로딩 표시와 함께 관광지 사진을 보여줍니다."""
    # 로딩 스낵바 표시
    loading_texts = {
        "ko": f"{attraction_name} 사진을 불러오는 중...",
        "en": f"Loading {attraction_name} photos...",
        "ja": f"{attraction_name}の写真を読み込み中...",
        "zh": f"正在加载{attraction_name}的照片..."
    }
    
    page.snack_bar = ft.SnackBar(
        content=ft.Row([
            ft.ProgressRing(width=16, height=16, stroke_width=2),
            ft.Text(loading_texts.get(lang, loading_texts["ko"]))
        ], spacing=8),
        duration=3000
    )
    page.snack_bar.open = True
    page.update()
    
    # 실제 사진 로드 (백그라운드에서)
    import threading
    def load_images():
        try:
            show_attraction_images(page, attraction_name, lang)
        except Exception as e:
            print(f"사진 로드 오류: {e}")
            # 오류 발생 시 스낵바로 알림
            error_texts = {
                "ko": "사진을 불러오는 중 오류가 발생했습니다.",
                "en": "An error occurred while loading photos.",
                "ja": "写真の読み込み中にエラーが発生しました。",
                "zh": "加载照片时出现错误。"
            }
            page.snack_bar = ft.SnackBar(
                content=ft.Text(error_texts.get(lang, error_texts["ko"])),
                duration=2000
            )
            page.snack_bar.open = True
            page.update()
    
    # 백그라운드 스레드에서 실행
    thread = threading.Thread(target=load_images)
    thread.daemon = True
    thread.start() 