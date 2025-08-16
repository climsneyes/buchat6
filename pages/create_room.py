import flet as ft

def CreateRoomPage(page, lang="ko", on_create=None, on_back=None):
    # 화면 크기에 따른 반응형 설정
    is_mobile = page.width < 600
    is_tablet = 600 <= page.width < 1024
    
    # 반응형 크기 계산
    container_width = min(page.width * 0.95, 500) if not is_mobile else page.width * 0.98
    field_width = min(360, page.width * 0.85)
    title_size = 20 if is_mobile else 24
    subtitle_size = 18 if is_mobile else 22
    label_size = 12 if is_mobile else 14
    hint_size = 11 if is_mobile else 13
    icon_size = 24 if is_mobile else 28
    header_icon_size = 24 if is_mobile else 28
    
    # 언어별 텍스트 사전
    texts = {
        "ko": {
            "title": "📌 채팅방 만들기",
            "subtitle": "새로운 채팅방 설정",
            "room_title_label": "방 제목 입력",
            "room_title_hint": "예: 외국인에게 길을 알려주는 방",
            "your_lang": "🇰🇷 한국어 (자동 선택)",
            "target_lang_label": "상대방 언어 선택",
            "target_lang_hint": "예: 영어, 일본어, 중국어 등",
            "purpose_label": "채팅 목적 선택 (선택사항)",
            "purpose_options": ["길안내", "음식 추천", "관광지 설명", "자유 대화", "긴급 도움 요청"],
            "persistent_room_label": "고정 채팅방 만들기",
            "persistent_room_desc": "체크하면 QR코드로 언제든지 같은 방에 접속할 수 있습니다 (식당, 가게 등에 적합)",
            "create_btn": "✅ 채팅방 만들기",
            "tip": "구체적인 방 제목을 작성하면 더 많은 사람들이 참여할 수 있어요!"
        },
        "en": {
            "title": "📌 Create Chat Room",
            "subtitle": "Set up a new chat room",
            "room_title_label": "Enter Room Title",
            "room_title_hint": "e.g. Need help finding subway station",
            "your_lang": "🇺🇸 English (auto-detected)",
            "target_lang_label": "Target Language",
            "target_lang_hint": "e.g. Korean, Japanese, Chinese",
            "purpose_label": "Purpose of Chat (optional)",
            "purpose_options": ["Directions", "Food Recommendations", "Tourist Info", "Casual Talk", "Emergency Help"],
            "persistent_room_label": "Create Fixed Chat Room",
            "persistent_room_desc": "Check to create a room that can be accessed anytime via QR code (suitable for restaurants, shops, etc.)",
            "create_btn": "✅ Create Chat Room",
            "tip": "If you write a specific room title, more people can join!"
        },
        "ja": {
            "title": "📌 チャットルーム作成",
            "subtitle": "新しいチャットルームの設定",
            "room_title_label": "ルームタイトルを入力",
            "room_title_hint": "例: 外国人に道案内する部屋",
            "your_lang": "🇯🇵 日本語 (自動検出)",
            "target_lang_label": "相手の言語を選択",
            "target_lang_hint": "例: 英語、韓国語、中国語など",
            "purpose_label": "チャットの目的（任意）",
            "purpose_options": ["道案内", "食事のおすすめ", "観光案内", "フリートーク", "緊急支援"],
            "persistent_room_label": "固定チャットルームを作成",
            "persistent_room_desc": "チェックするとQRコードでいつでも同じ部屋にアクセスできます（レストラン、店舗などに適しています）",
            "create_btn": "✅ チャットルーム作成",
            "tip": "具体的なルームタイトルを書くと、より多くの人が参加しやすくなります！"
        },
        "zh": {
            "title": "📌 创建聊天室",
            "subtitle": "新建聊天室设置",
            "room_title_label": "输入房间标题",
            "room_title_hint": "例如：帮助外国人找路的房间",
            "your_lang": "🇨🇳 中文（自动检测）",
            "target_lang_label": "选择对方语言",
            "target_lang_hint": "例如：英语、日语、韩语等",
            "purpose_label": "聊天目的（可选）",
            "purpose_options": ["导航", "美食推荐", "旅游信息", "自由聊天", "紧急求助"],
            "persistent_room_label": "创建固定聊天室",
            "persistent_room_desc": "勾选后可通过二维码随时访问同一房间（适合餐厅、商店等）",
            "create_btn": "✅ 创建聊天室",
            "tip": "写一个具体的房间标题会有更多人加入哦！"
        },
        "zh-TW": {
            "title": "📌 建立聊天室",
            "subtitle": "建立新聊天室設定",
            "room_title_label": "輸入房間標題",
            "room_title_hint": "例如：幫助外國人找路的房間",
            "your_lang": "🇹🇼 台灣中文（自動偵測）",
            "target_lang_label": "選擇對方語言",
            "target_lang_hint": "例如：英文、日文、韓文等",
            "purpose_label": "聊天目的（可選）",
            "purpose_options": ["導航", "美食推薦", "旅遊資訊", "自由聊天", "緊急求助"],
            "persistent_room_label": "建立固定聊天室",
            "persistent_room_desc": "勾選後可透過QR碼隨時存取同一房間（適合餐廳、商店等）",
            "create_btn": "✅ 建立聊天室",
            "tip": "寫下具體的房間標題，會有更多人參加喔！"
        },
        "id": {
            "title": "📌 Buat Ruang Obrolan",
            "subtitle": "Pengaturan ruang obrolan baru",
            "room_title_label": "Masukkan Judul Ruangan",
            "room_title_hint": "misal: Ruang untuk membantu orang asing menemukan jalan",
            "your_lang": "🇮🇩 Bahasa Indonesia (terdeteksi otomatis)",
            "target_lang_label": "Pilih Bahasa Lawan Bicara",
            "target_lang_hint": "misal: Inggris, Jepang, Korea, dll",
            "purpose_label": "Tujuan Obrolan (opsional)",
            "purpose_options": ["Petunjuk Arah", "Rekomendasi Makanan", "Info Wisata", "Obrolan Bebas", "Bantuan Darurat"],
            "persistent_room_label": "Buat Ruang Obrolan Tetap",
            "persistent_room_desc": "Centang untuk membuat ruang yang dapat diakses kapan saja melalui QR code (cocok untuk restoran, toko, dll)",
            "create_btn": "✅ Buat Ruang Obrolan",
            "tip": "Jika Anda menulis judul ruang yang spesifik, lebih banyak orang dapat bergabung!"
        },
        "fr": {
            "title": "📌 Créer une salle de chat",
            "subtitle": "Configurer une nouvelle salle de chat",
            "room_title_label": "Entrez le titre de la salle",
            "room_title_hint": "ex : Salle pour aider les étrangers",
            "your_lang": "🇫🇷 Français (auto-détecté)",
            "target_lang_label": "Langue de l'autre",
            "target_lang_hint": "ex : Anglais, Japonais, Chinois",
            "purpose_label": "But du chat (optionnel)",
            "purpose_options": ["Itinéraire", "Recommandation de nourriture", "Info touristique", "Discussion libre", "Aide d'urgence"],
            "persistent_room_label": "Créer une salle de chat fixe",
            "persistent_room_desc": "Cochez pour créer une salle accessible à tout moment via QR code (adapté aux restaurants, magasins, etc.)",
            "create_btn": "✅ Créer la salle",
            "tip": "Si vous écrivez un titre de salle précis, plus de personnes pourront rejoindre !"
        },
        "de": {
            "title": "📌 Chatraum erstellen",
            "subtitle": "Neuen Chatraum einrichten",
            "room_title_label": "Raumtitel eingeben",
            "room_title_hint": "z.B. Raum zur Wegbeschreibung für Ausländer",
            "your_lang": "🇩🇪 Deutsch (automatisch erkannt)",
            "target_lang_label": "Zielsprache wählen",
            "target_lang_hint": "z.B. Englisch, Japanisch, Chinesisch",
            "purpose_label": "Chat-Zweck (optional)",
            "purpose_options": ["Wegbeschreibung", "Essensempfehlung", "Touristeninfo", "Freies Gespräch", "Notfallhilfe"],
            "persistent_room_label": "Festen Chatraum erstellen",
            "persistent_room_desc": "Aktivieren Sie diese Option, um einen Raum zu erstellen, der jederzeit über QR-Code zugänglich ist (geeignet für Restaurants, Geschäfte usw.)",
            "create_btn": "✅ Chatraum erstellen",
            "tip": "Wenn Sie einen konkreten Raumnamen angeben, können mehr Leute teilnehmen!"
        },
        "th": {
            "title": "📌 สร้างห้องแชท",
            "subtitle": "ตั้งค่าห้องแชทใหม่",
            "room_title_label": "กรอกชื่อห้อง",
            "room_title_hint": "เช่น ห้องช่วยเหลือชาวต่างชาติ",
            "your_lang": "🇹🇭 ไทย (ตรวจจับอัตโนมัติ)",
            "target_lang_label": "เลือกภาษาของคู่สนทนา",
            "target_lang_hint": "เช่น อังกฤษ ญี่ปุ่น จีน",
            "purpose_label": "วัตถุประสงค์ของแชท (ไม่บังคับ)",
            "purpose_options": ["นำทาง", "แนะนำอาหาร", "ข้อมูลท่องเที่ยว", "พูดคุยทั่วไป", "ขอความช่วยเหลือฉุกเฉิน"],
            "persistent_room_label": "สร้างห้องแชทประจำ",
            "persistent_room_desc": "เลือกเพื่อสร้างห้องที่สามารถเข้าถึงได้ตลอดเวลาผ่านQR code (เหมาะสำหรับร้านอาหาร ร้านค้า ฯลฯ)",
            "create_btn": "✅ สร้างห้องแชท",
            "tip": "หากตั้งชื่อห้องให้เฉพาะเจาะจง จะมีคนเข้าร่วมมากขึ้น!"
        },
        "vi": {
            "title": "📌 Tạo phòng trò chuyện",
            "subtitle": "Cài đặt phòng trò chuyện mới",
            "room_title_label": "Nhập tên phòng",
            "room_title_hint": "VD: Phòng hướng dẫn cho người nước ngoài",
            "your_lang": "🇻🇳 Tiếng Việt (tự động phát hiện)",
            "target_lang_label": "Chọn ngôn ngữ đối phương",
            "target_lang_hint": "VD: Tiếng Anh, Tiếng Nhật, Tiếng Trung",
            "purpose_label": "Mục đích trò chuyện (tùy chọn)",
            "purpose_options": ["Chỉ đường", "Gợi ý món ăn", "Thông tin du lịch", "Trò chuyện tự do", "Yêu cầu khẩn cấp"],
            "persistent_room_label": "Tạo phòng trò chuyện cố định",
            "persistent_room_desc": "Chọn để tạo phòng có thể truy cập bất cứ lúc nào qua QR code (phù hợp cho nhà hàng, cửa hàng, v.v.)",
            "create_btn": "✅ Tạo phòng",
            "tip": "Nếu bạn đặt tên phòng cụ thể, sẽ có nhiều người tham gia hơn!"
        },
        "tl": {
            "title": "📌 Gumawa ng Chat Room",
            "subtitle": "I-setup ang bagong chat room",
            "room_title_label": "Ilagay ang pamagat ng room",
            "room_title_hint": "Halimbawa: Room para sa pag-guide sa mga dayuhan",
            "your_lang": "🇵🇭 Filipino (automatic)",
            "target_lang_label": "Piliin ang wika ng kausap",
            "target_lang_hint": "Halimbawa: Ingles, Hapon, Tsino",
            "purpose_label": "Layunin ng chat (opsyonal)",
            "purpose_options": ["Pag-guide sa daan", "Rekomendasyon ng pagkain", "Impormasyon sa turismo", "Libreng usapan", "Emergency na tulong"],
            "persistent_room_label": "Gumawa ng fixed chat room",
            "persistent_room_desc": "I-check para gumawa ng room na maaaring ma-access anumang oras sa pamamagitan ng QR code (angkop para sa mga restaurant, tindahan, atbp.)",
            "create_btn": "✅ Gumawa ng Room",
            "tip": "Kung maglagay ka ng specific na pamagat ng room, mas maraming tao ang sasali!"
        }
    }
    t = texts.get(lang, texts["en"])

    # 언어 선택 드롭다운 예시
    lang_options = [
        ft.dropdown.Option("en", "🇺🇸 English"),
        ft.dropdown.Option("ko", "🇰🇷 한국어"),
        ft.dropdown.Option("ja", "🇯🇵 日本語"),
        ft.dropdown.Option("zh", "🇨🇳 中文"),
        ft.dropdown.Option("zh-TW", "🇹🇼 台灣中文"),
        ft.dropdown.Option("id", "🇮🇩 Bahasa Indonesia"),
        ft.dropdown.Option("fr", "🇫🇷 Français"),
        ft.dropdown.Option("de", "🇩🇪 Deutsch"),
        ft.dropdown.Option("th", "🇹🇭 ไทย"),
        ft.dropdown.Option("vi", "🇻🇳 Tiếng Việt"),
    ]

    # 컨트롤 참조 생성
    room_title_field = ft.TextField(hint_text=t["room_title_hint"], width=field_width)
    target_lang_dd = ft.Dropdown(
        options=[
            ft.dropdown.Option("ko", "🇰🇷 한국어"),
            ft.dropdown.Option("en", "🇺🇸 English"),
            ft.dropdown.Option("ja", "🇯🇵 日本語"),
            ft.dropdown.Option("zh", "🇨🇳 中文"),
            ft.dropdown.Option("zh-TW", "🇹🇼 台灣中文"),
            ft.dropdown.Option("id", "🇮🇩 Bahasa Indonesia"),
            ft.dropdown.Option("fr", "🇫🇷 Français"),
            ft.dropdown.Option("de", "🇩🇪 Deutsch"),
            ft.dropdown.Option("th", "🇹🇭 ไทย"),
            ft.dropdown.Option("vi", "🇻🇳 Tiếng Việt"),
            ft.dropdown.Option("uz", "🇺🇿 Uzbek"),
            ft.dropdown.Option("ne", "🇳🇵 Nepali"),
            ft.dropdown.Option("tet", "🇹🇱 Tetum"),
            ft.dropdown.Option("lo", "🇱🇦 Lao"),
            ft.dropdown.Option("mn", "🇲🇳 Mongolian"),
            ft.dropdown.Option("my", "🇲🇲 Burmese"),
            ft.dropdown.Option("bn", "🇧🇩 Bengali"),
            ft.dropdown.Option("si", "🇱🇰 Sinhala"),
            ft.dropdown.Option("km", "🇰🇭 Khmer"),
            ft.dropdown.Option("ky", "🇰🇬 Kyrgyz"),
            ft.dropdown.Option("ur", "🇵🇰 Urdu"),
        ],
        hint_text=t["target_lang_hint"],
        width=field_width
    )
    purpose_dd = ft.Dropdown(
        label=t["purpose_label"],
        options=[ft.dropdown.Option(opt) for opt in t["purpose_options"]],
        hint_text=t["purpose_label"],
        width=field_width
    )
    
    # 영속적 채팅방 체크박스 추가
    persistent_room_checkbox = ft.Checkbox(
        label=t["persistent_room_label"],
        value=False,
        scale=1.0
    )
    
    # 영속적 채팅방 설명 텍스트
    persistent_room_desc = ft.Text(
        t["persistent_room_desc"],
        size=12,
                        color=ft.Colors.GREY_600,
        text_align=ft.TextAlign.START,
        max_lines=3
    )
    
    # on_create 콜백 수정: 방 제목, 상대방 언어, 영속적 채팅방 옵션을 전달
    create_button = ft.ElevatedButton(
        t["create_btn"],
        on_click=lambda e: on_create(room_title_field.value, target_lang_dd.value, persistent_room_checkbox.value) if on_create else None,
        width=field_width,
        bgcolor="#4ADE80",
        color=ft.Colors.WHITE
    )

    return ft.View(
        "/create_room",
        controls=[
            # 헤더 (아이콘 + 타이틀)
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(name=ft.Icons.PEOPLE, color="#22C55E", size=header_icon_size),
                            bgcolor="#22C55E22", border_radius=10 if is_mobile else 12, padding=6 if is_mobile else 8, margin=ft.margin.only(right=6 if is_mobile else 8)
                        ),
                        ft.Text(t["title"].replace("📌 ", ""), size=title_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ),
            ], alignment=ft.MainAxisAlignment.START, spacing=6 if is_mobile else 8, vertical_alignment=ft.CrossAxisAlignment.CENTER),

            # 중앙 카드 (설정 폼)
            ft.Container(
                content=ft.Column([
                    ft.Text(t["subtitle"], size=subtitle_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87, text_align="center"),
                    ft.Container(
                        content=ft.Text(t["room_title_label"], size=label_size, weight=ft.FontWeight.W_500),
                        margin=ft.margin.only(top=16 if is_mobile else 20)
                    ),
                    room_title_field,
                    ft.Row([
                        ft.Icon(name=ft.Icons.LANGUAGE, color="#2563EB", size=14 if is_mobile else 16),
                        ft.Text(t["your_lang"], size=hint_size, color="#2563EB"),
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(
                        content=ft.Text(t["target_lang_label"], size=label_size, weight=ft.FontWeight.W_500),
                        margin=ft.margin.only(top=12)
                    ),
                    target_lang_dd,
                    ft.Container(
                        content=ft.Text(t["purpose_label"], size=label_size, weight=ft.FontWeight.W_500),
                        margin=ft.margin.only(top=12)
                    ),
                    purpose_dd,
                    ft.Container(
                        content=persistent_room_checkbox,
                        margin=ft.margin.only(top=12)
                    ),
                    ft.Container(
                        content=persistent_room_desc,
                        margin=ft.margin.only(top=4)
                    ),
                    ft.Container(
                        content=create_button,
                        margin=ft.margin.only(top=16 if is_mobile else 20)
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(name=ft.Icons.LIGHTBULB_OUTLINE, color="#F59E42", size=16 if is_mobile else 18),
                            ft.Text(t["tip"], size=11 if is_mobile else 12, color="#64748B"),
                        ], spacing=4 if is_mobile else 6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#F1F5FF",
                        border_radius=6 if is_mobile else 8,
                        padding=10 if is_mobile else 12,
                        margin=ft.margin.only(top=16)
                    ),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30 if is_mobile else 40,
                bgcolor=ft.Colors.WHITE,
                border_radius=16 if is_mobile else 20,
                shadow=ft.BoxShadow(blur_radius=24, color="#B0BEC544"),
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=24 if is_mobile else 32),
                width=container_width
            ),
        ],
        bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
