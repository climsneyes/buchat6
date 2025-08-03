// 다국어 지원 데이터
const translations = {
    ko: {
        // Header & Navigation
        title: "MBTI별 부산 관광지 추천",
        subtitle: "당신의 성격 유형에 맞는 완벽한 부산 여행지를 찾아보세요!",
        
        // Stats
        mbti_types: "MBTI 유형",
        attractions: "관광지",
        languages: "언어 지원",
        
        // MBTI Selection
        select_mbti: "MBTI를 선택해주세요",
        
        // MBTI Categories
        analysts: "분석가형 (NT)",
        diplomats: "외교관형 (NF)", 
        sentinels: "관리자형 (SJ)",
        explorers: "탐험가형 (SP)",
        
        // MBTI Type Names
        intj_name: "전략적 사고의 건축가",
        intp_name: "논리적 분석의 논리술사",
        entj_name: "대담한 통솔력의 사령관",
        entp_name: "똑똑한 호기심의 변론가",
        infj_name: "선의의 옹호자",
        infp_name: "열정적인 중재자",
        enfj_name: "정의로운 사회운동가",
        enfp_name: "재기발랄한 활동가",
        istj_name: "실용적인 현실주의자",
        isfj_name: "온화한 수호자",
        estj_name: "엄격한 관리자",
        esfj_name: "사교적인 집정관",
        istp_name: "만능 재주꾼",
        isfp_name: "호기심 많은 예술가",
        estp_name: "모험을 즐기는 사업가",
        esfp_name: "자유로운 영혼의 연예인",
        
        // Actions & Buttons
        back: "돌아가기",
        view_details: "상세보기",
        show_location: "위치보기",
        loading: "로딩 중...",
        
        // Footer
        footer_desc: "당신의 성격에 맞는 완벽한 부산 여행을 계획하세요",
        quick_links: "빠른 링크",
        about: "소개",
        contact: "연락처", 
        privacy: "개인정보처리방침",
        follow_us: "팔로우",
        
        // Modal
        attraction_details: "관광지 상세정보",
        close: "닫기",
        why_recommend: "추천 이유",
        
        // Error Messages
        no_attractions: "추천 관광지를 찾을 수 없습니다.",
        loading_error: "데이터를 불러오는 중 오류가 발생했습니다."
    },
    
    en: {
        // Header & Navigation
        title: "Busan Tourist Spots by MBTI",
        subtitle: "Discover the perfect Busan destinations for your personality type!",
        
        // Stats
        mbti_types: "MBTI Types",
        attractions: "Attractions",
        languages: "Languages",
        
        // MBTI Selection
        select_mbti: "Select Your MBTI Type",
        
        // MBTI Categories
        analysts: "Analysts (NT)",
        diplomats: "Diplomats (NF)",
        sentinels: "Sentinels (SJ)", 
        explorers: "Explorers (SP)",
        
        // MBTI Type Names
        intj_name: "Strategic Architect",
        intp_name: "Logical Analyst",
        entj_name: "Bold Commander",
        entp_name: "Smart Debater",
        infj_name: "Gentle Advocate",
        infp_name: "Passionate Mediator",
        enfj_name: "Righteous Social Activist",
        enfp_name: "Energetic Campaigner",
        istj_name: "Practical Realist",
        isfj_name: "Gentle Protector",
        estj_name: "Strict Manager",
        esfj_name: "Sociable Executive",
        istp_name: "Versatile Virtuoso",
        isfp_name: "Curious Artist",
        estp_name: "Adventurous Entrepreneur",
        esfp_name: "Free-spirited Entertainer",
        
        // Actions & Buttons
        back: "Back",
        view_details: "View Details",
        show_location: "Show Location",
        loading: "Loading...",
        
        // Footer
        footer_desc: "Plan your perfect Busan trip tailored to your personality",
        quick_links: "Quick Links",
        about: "About",
        contact: "Contact",
        privacy: "Privacy Policy",
        follow_us: "Follow Us",
        
        // Modal
        attraction_details: "Attraction Details",
        close: "Close",
        why_recommend: "Why Recommended",
        
        // Error Messages
        no_attractions: "No recommended attractions found.",
        loading_error: "An error occurred while loading data."
    },
    
    ja: {
        // Header & Navigation
        title: "MBTI別釜山観光地おすすめ",
        subtitle: "あなたの性格タイプに合った完璧な釜山旅行地を見つけましょう！",
        
        // Stats
        mbti_types: "MBTIタイプ",
        attractions: "観光地",
        languages: "言語サポート",
        
        // MBTI Selection
        select_mbti: "MBTIタイプを選択してください",
        
        // MBTI Categories
        analysts: "分析家型 (NT)",
        diplomats: "外交官型 (NF)",
        sentinels: "管理者型 (SJ)",
        explorers: "探検家型 (SP)",
        
        // MBTI Type Names
        intj_name: "戦略的思考の建築家",
        intp_name: "論理的分析を好む論理学者",
        entj_name: "大胆な統率力の司令官",
        entp_name: "賢い好奇心の討論家",
        infj_name: "想像力豊かな調停者",
        infp_name: "理想主義的霊感の調停者",
        enfj_name: "カリスマ溢れる指導者",
        enfp_name: "機知に富む活動家",
        istj_name: "実用的現実主義者",
        isfj_name: "温和な守護者",
        estj_name: "厳格な管理者",
        esfj_name: "社交的な執政官",
        istp_name: "万能職人",
        isfp_name: "冒険を楽しむ冒険家",
        estp_name: "大胆な起業家",
        esfp_name: "自由な魂の芸術家",
        
        // Actions & Buttons
        back: "戻る",
        view_details: "詳細を見る",
        show_location: "場所を表示",
        loading: "読み込み中...",
        
        // Footer
        footer_desc: "あなたの性格に合った完璧な釜山旅行を計画しましょう",
        quick_links: "クイックリンク",
        about: "概要",
        contact: "お問い合わせ",
        privacy: "プライバシーポリシー",
        follow_us: "フォロー",
        
        // Modal
        attraction_details: "観光地詳細情報",
        close: "閉じる",
        why_recommend: "おすすめの理由",
        
        // Error Messages
        no_attractions: "おすすめの観光地が見つかりませんでした。",
        loading_error: "データの読み込み中にエラーが発生しました。"
    },
    
    zh: {
        // Header & Navigation
        title: "MBTI别釜山观光地推荐",
        subtitle: "找到适合您性格类型的完美釜山旅行地！",
        
        // Stats
        mbti_types: "MBTI类型",
        attractions: "景点",
        languages: "语言支持",
        
        // MBTI Selection
        select_mbti: "请选择您的MBTI类型",
        
        // MBTI Categories
        analysts: "分析家型 (NT)",
        diplomats: "外交家型 (NF)", 
        sentinels: "管理者型 (SJ)",
        explorers: "探险家型 (SP)",
        
        // MBTI Type Names
        intj_name: "战略思维的建筑师",
        intp_name: "逻辑分析的思想家",
        entj_name: "大胆统率的指挥官",
        entp_name: "聪明好奇的辩论家",
        infj_name: "善意的倡导者",
        infp_name: "热情的调解者",
        enfj_name: "正义的社会活动家",
        enfp_name: "活泼的活动家",
        istj_name: "实用的现实主义者",
        isfj_name: "温和的守护者",
        estj_name: "严格的管理者",
        esfj_name: "社交的执政官",
        istp_name: "多才多艺的巧匠",
        isfp_name: "好奇的艺术家",
        estp_name: "冒险的企业家",
        esfp_name: "自由灵魂的艺人",
        
        // Actions & Buttons
        back: "返回",
        view_details: "查看详情",
        show_location: "显示位置",
        loading: "加载中...",
        
        // Footer
        footer_desc: "规划适合您性格的完美釜山之旅",
        quick_links: "快速链接",
        about: "关于",
        contact: "联系",
        privacy: "隐私政策",
        follow_us: "关注我们",
        
        // Modal
        attraction_details: "景点详细信息",
        close: "关闭",
        why_recommend: "推荐理由",
        
        // Error Messages
        no_attractions: "未找到推荐景点。",
        loading_error: "加载数据时发生错误。"
    }
};

// 현재 언어 설정
let currentLanguage = 'ko';

// 텍스트 업데이트 함수
function updateTexts() {
    const texts = translations[currentLanguage];
    
    document.querySelectorAll('[data-text]').forEach(element => {
        const key = element.getAttribute('data-text');
        if (texts[key]) {
            element.textContent = texts[key];
        }
    });
}

// 언어 변경 함수
function changeLanguage(lang) {
    if (translations[lang]) {
        currentLanguage = lang;
        updateTexts();
        
        // 언어 버튼 업데이트
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-lang') === lang) {
                btn.classList.add('active');
            }
        });
        
        // 현재 MBTI가 선택되어 있다면 결과 업데이트
        const selectedMbti = document.querySelector('.mbti-card.selected');
        if (selectedMbti) {
            const mbtiType = selectedMbti.getAttribute('data-mbti');
            showResults(mbtiType);
        }
    }
}

// 번역 가져오기 함수
function getText(key) {
    return translations[currentLanguage][key] || key;
}