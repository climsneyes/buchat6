import flet as ft
import json
import webbrowser


# 전역 변수로 상태 관리
_global_selected_mbti = None
_global_result_view = None

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
        "흰여울문화마을": "흰여울문화마을"
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
        "흰여울문화마을": "Huinnyeoul Culture Village"
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
        "흰여울문화마을": "ヒンニョウル文化村"
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
        "흰여울문화마을": "白色涡流文化村"
    }
}

# 관광지별 상세 정보 데이터
attraction_details = {
    "범어사": {
        "images": ["https://images.unsplash.com/photo-1544737151618-6e4b999de2a4?w=800&h=600&fit=crop"],
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
        "images": ["https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"],
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
        "images": ["https://images.unsplash.com/photo-1578842554932-82aa9c5e90e5?w=800&h=600&fit=crop"],
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
        "images": ["https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop&q=80"],
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
        "images": ["https://images.unsplash.com/photo-1601628828688-632f38a5a7d0?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.100570, "lng": 129.032909, "address": "부산광역시 중구 용두산길 37-55"},
        "description": "부산의 상징적인 랜드마크로, 시내 전경을 한눈에 볼 수 있습니다."
    },
    "부산박물관": {
        "images": ["https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.187167, "lng": 129.106889, "address": "부산광역시 남구 유엔평화로 63"},
        "description": "부산의 역사와 문화를 한눈에 볼 수 있는 종합박물관입니다."
    },
    "국립해양박물관": {
        "images": ["https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.135222, "lng": 129.109639, "address": "부산광역시 영도구 해양로 301번길 45"},
        "description": "해양 문화와 역사를 체험할 수 있는 국내 최대 해양박물관입니다."
    },
    "롯데월드 어드벤처 부산": {
        "images": ["https://images.unsplash.com/photo-1544427920-c49ccfb85579?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.186564, "lng": 129.079194, "address": "부산광역시 기장군 기장읍 동부산관광로 42"},
        "description": "부산 최대 규모의 테마파크로 다양한 어트랙션과 즐길거리가 있습니다."
    },
    "송도해상케이블카": {
        "images": ["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.076111, "lng": 129.017222, "address": "부산광역시 서구 송도해변로 171"},
        "description": "바다 위를 가로지르는 케이블카로 아름다운 부산 해안선을 감상할 수 있습니다."
    },
    "BIFF 거리": {
        "images": ["https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.096944, "lng": 129.032778, "address": "부산광역시 중구 남포동"},
        "description": "부산국제영화제의 중심지로 영화와 문화의 거리입니다."
    },
    "자갈치시장": {
        "images": ["https://images.unsplash.com/photo-1578662996441-48f60103fc96?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.096667, "lng": 129.030556, "address": "부산광역시 중구 자갈치해안로 52"},
        "description": "부산을 대표하는 수산시장으로 신선한 해산물을 맛볼 수 있습니다."
    },
    "해동용궁사": {
        "images": ["https://images.unsplash.com/photo-1578662996442-0a3d7c32a2c8?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.188333, "lng": 129.223056, "address": "부산광역시 기장군 기장읍 용궁길 86"},
        "description": "바다에 면한 아름다운 사찰로 특별한 풍경을 자랑합니다."
    },
    "태종대": {
        "images": ["https://images.unsplash.com/photo-1578842554932-82aa9c5e90e5?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.051389, "lng": 129.087222, "address": "부산광역시 영도구 전망로 24"},
        "description": "부산의 대표적인 해안절벽으로 아름다운 자연경관을 감상할 수 있습니다."
    },
    "BTS 지민 아버지 카페 'MAGNATE'": {
        "images": ["https://images.unsplash.com/photo-1521017432531-fbd92d768814?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.158333, "lng": 129.160000, "address": "부산광역시 해운대구 해운대해변로 197"},
        "description": "BTS 지민의 아버지가 운영하는 카페로 K-pop 팬들의 성지입니다."
    },
    "흰여울문화마을": {
        "images": ["https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop&q=80"],
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "location": {"lat": 35.051944, "lng": 129.087500, "address": "부산광역시 영도구 흰여울길 1"},
        "description": "영화 '변호인' 촬영지로 유명한 아름다운 해안마을입니다."
    }
}

def show_attraction_images(page, attraction_name, lang="ko"):
    """관광지 사진 모달 창 표시"""
    details = attraction_details.get(attraction_name, {})
    images = details.get("images", [])
    
    # 다국어 텍스트
    no_image_texts = {
        "ko": "이 관광지의 사진이 준비되지 않았습니다.",
        "en": "Photos for this attraction are not available.",
        "ja": "この観光地の写真は準備されていません。",
        "zh": "此景点的照片尚未准备好。"
    }
    
    if not images:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(no_image_texts.get(lang, no_image_texts["en"])),
            duration=2000
        )
        page.snack_bar.open = True
        page.update()
        return
        
    def close_modal(e):
        page.overlay.pop()
        page.update()
    
    # 관광지 이름을 해당 언어로 변환
    display_name = attraction_name_mapping.get(lang, attraction_name_mapping["ko"]).get(attraction_name, attraction_name)
    
    # 설명을 해당 언어로 가져오기
    description = details.get("description", {})
    if isinstance(description, dict):
        description_text = description.get(lang, description.get("ko", ""))
    else:
        description_text = description
    
    # 여러 이미지가 있는 경우 처리
    image_containers = []
    for i, img_url in enumerate(images[:3]):  # 최대 3개
        image_containers.append(
            ft.Container(
                height=300 if len(images) == 1 else 200,
                width=450 if len(images) == 1 else 140,
                margin=ft.margin.only(right=10 if i < len(images)-1 else 0),
                content=ft.Image(src=img_url, fit=ft.ImageFit.COVER, border_radius=8),
                border_radius=8
            )
        )
    
    modal_content = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(f"📸 {display_name}", size=20, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.CLOSE, on_click=close_modal)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row(image_containers, scroll=ft.ScrollMode.AUTO) if len(images) > 1 
            else image_containers[0],
            ft.Text(description_text, size=14, color=ft.Colors.GREY_700, 
                   text_align=ft.TextAlign.CENTER),
        ], spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        width=500,
        max_height=600
    )
    
    page.overlay.append(
        ft.Container(
            content=modal_content,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK54,
            expand=True,
            on_click=close_modal
        )
    )
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

def show_attraction_map(page, attraction_name, lang="ko"):
    """관광지 지도 모달 창 표시"""
    details = attraction_details.get(attraction_name, {})
    location = details.get("location", {})
    
    # 관광지 이름을 해당 언어로 변환
    display_name = attraction_name_mapping.get(lang, attraction_name_mapping["ko"]).get(attraction_name, attraction_name)
    
    # 다국어 텍스트
    map_texts = {
        "no_location": {
            "ko": "이 관광지의 위치 정보가 준비되지 않았습니다.",
            "en": "Location information for this attraction is not available.",
            "ja": "この観光地の位置情報は準備されていません。",
            "zh": "此景点的位置信息尚未准备好。"
        },
        "address": {
            "ko": "주소",
            "en": "Address",
            "ja": "住所",  
            "zh": "地址"
        },
        "latitude": {
            "ko": "위도",
            "en": "Latitude",
            "ja": "緯度",
            "zh": "纬度"
        },
        "longitude": {
            "ko": "경도", 
            "en": "Longitude",
            "ja": "経度",
            "zh": "经度"
        },
        "view_in_maps": {
            "ko": "Google Maps에서 보기",
            "en": "View in Google Maps",
            "ja": "Google Mapsで見る",
            "zh": "在Google地图中查看"
        }
    }
    
    if not location:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(map_texts["no_location"][lang]),
            duration=2000
        )
        page.snack_bar.open = True
        page.update()
        return
        
    def close_modal(e):
        page.overlay.pop()
        page.update()
    
    # Google Maps 링크 생성
    google_maps_url = f"https://www.google.com/maps?q={location['lat']},{location['lng']}"
    
    # 설명을 해당 언어로 가져오기
    description = details.get("description", {})
    if isinstance(description, dict):
        description_text = description.get(lang, description.get("ko", ""))
    else:
        description_text = description
    
    modal_content = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(f"📍 {display_name}", size=20, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.CLOSE, on_click=close_modal)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text(f"{map_texts['address'][lang]}: {location.get('address', '')}", size=14),
            ft.Text(f"{map_texts['latitude'][lang]}: {location.get('lat', '')}", size=12, color=ft.Colors.GREY_600),
            ft.Text(f"{map_texts['longitude'][lang]}: {location.get('lng', '')}", size=12, color=ft.Colors.GREY_600),
            ft.Container(height=16),
            ft.ElevatedButton(
                map_texts["view_in_maps"][lang],
                on_click=lambda e: page.launch_url(google_maps_url),
                icon=ft.Icons.MAP,
                width=200
            ),
            ft.Text(description_text, size=14, color=ft.Colors.GREY_700),
        ], spacing=12),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        width=400
    )
    
    page.overlay.append(
        ft.Container(
            content=modal_content,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK54,
            expand=True,
            on_click=close_modal
        )
    )
    page.update()

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
        }
    }
    
    t = texts.get(lang, texts["ko"])
    
    # MBTI별 관광지 추천 데이터 (K-pop, 드라마 촬영지 포함)
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
    global _global_selected_mbti, _global_result_view
    
    # 전역 변수에서 값 가져오기
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
    

    
    def show_recommendations():
        print(f"추천받기 버튼 클릭됨! 선택된 MBTI: {selected_mbti[0]}")
        if not selected_mbti[0]:
            print("선택된 MBTI가 없습니다.")
            return
        
        mbti = selected_mbti[0]
        print(f"MBTI {mbti}에 대한 추천을 생성합니다...")
        
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
        
        rec_data = recommendations.get(lang, recommendations["ko"])
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
                                ft.Row([
                                    ft.Text(
                                        attraction_name_mapping.get(lang, attraction_name_mapping["ko"]).get(attraction["name"], attraction["name"]), 
                                        size=text_size, weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Container(
                                        content=ft.Text(attraction["category"], size=button_size),
                                        bgcolor=ft.Colors.BLUE_100,
                                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                        border_radius=12
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(attraction["reason"], size=text_size, color=ft.Colors.GREY_600),
                                ft.Container(height=8),
                                # 사진, 영상, 지도 버튼 추가 (다국어)
                                ft.Row([
                                    ft.ElevatedButton(
                                        {
                                            "ko": "📸 사진",
                                            "en": "📸 Photos", 
                                            "ja": "📸 写真",
                                            "zh": "📸 照片"
                                        }.get(lang, "📸 Photos"),
                                        on_click=lambda e, name=attraction["name"]: show_attraction_images(page, name, lang),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREEN_100,
                                            color=ft.Colors.GREEN_800,
                                            padding=ft.padding.symmetric(horizontal=12, vertical=8)
                                        ),
                                        height=32
                                    ),
                                    ft.ElevatedButton(
                                        {
                                            "ko": "📱 쇼츠",
                                            "en": "📱 Shorts",
                                            "ja": "📱 ショート",
                                            "zh": "📱 短视频"
                                        }.get(lang, "📱 Shorts"),
                                        on_click=lambda e, name=attraction["name"]: show_attraction_videos(page, name, lang),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.RED_100,  
                                            color=ft.Colors.RED_800,
                                            padding=ft.padding.symmetric(horizontal=12, vertical=8)
                                        ),
                                        height=32
                                    ),
                                    ft.ElevatedButton(
                                        {
                                            "ko": "📍 지도",
                                            "en": "📍 Map",
                                            "ja": "📍 地図", 
                                            "zh": "📍 地图"
                                        }.get(lang, "📍 Map"),
                                        on_click=lambda e, name=attraction["name"]: show_attraction_map(page, name, lang),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.ORANGE_100,
                                            color=ft.Colors.ORANGE_800,
                                            padding=ft.padding.symmetric(horizontal=12, vertical=8)
                                        ),
                                        height=32
                                    )
                                ], spacing=8, alignment=ft.MainAxisAlignment.START)
                            ], spacing=4),
                            padding=12,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            margin=ft.margin.only(bottom=8)
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
        
        mbti_buttons.append(
            ft.Container(
                content=ft.Text(mbti, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_selected else ft.Colors.BLACK87),
                width=80,
                height=80,
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
            
            # 추천 버튼
            ft.Container(
                content=ft.ElevatedButton(
                    t["recommend"],
                    on_click=lambda e: show_recommendations(),
                    disabled=selected_mbti[0] is None,
                    width=200,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_600 if selected_mbti[0] else ft.Colors.GREY_400,
                        color=ft.Colors.WHITE
                    )
                ),
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=16)
            ),
            
            # 결과 표시
            result_view[0] if result_view[0] else ft.Container(),
        ],
        bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=ft.padding.only(bottom=20 if is_mobile else 32)
    ) 