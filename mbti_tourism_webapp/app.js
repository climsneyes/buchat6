// 메인 애플리케이션 로직

// DOM 요소들
let mbtiCards; // 초기화 함수에서 설정
const resultsSection = document.getElementById('results-section');
const backBtn = document.getElementById('back-btn');
const attractionsGrid = document.getElementById('attractions-grid');
const modalOverlay = document.getElementById('modal-overlay');
const modalClose = document.getElementById('modal-close');
const modalTitle = document.getElementById('modal-title');
const attractionInfo = document.getElementById('attraction-info');

// MBTI 아이콘 매핑
const mbtiIcons = {
    'INTJ': 'fas fa-chess',
    'INTP': 'fas fa-flask',
    'ENTJ': 'fas fa-crown',
    'ENTP': 'fas fa-lightbulb',
    'INFJ': 'fas fa-dove',
    'INFP': 'fas fa-palette',
    'ENFJ': 'fas fa-heart',
    'ENFP': 'fas fa-star',
    'ISTJ': 'fas fa-shield-alt',
    'ISFJ': 'fas fa-hand-holding-heart',
    'ESTJ': 'fas fa-clipboard-check',
    'ESFJ': 'fas fa-users',
    'ISTP': 'fas fa-tools',
    'ISFP': 'fas fa-camera',
    'ESTP': 'fas fa-rocket',
    'ESFP': 'fas fa-music'
};

// 카테고리별 아이콘 매핑
const categoryIcons = {
    // 한국어 카테고리
    '사찰': 'fas fa-torii-gate',
    '박물관': 'fas fa-university',
    '역사': 'fas fa-landmark',
    '공원': 'fas fa-tree',
    '산책로': 'fas fa-walking',
    '문화시설': 'fas fa-theater-masks',
    '도서관': 'fas fa-book',
    '등대': 'fas fa-lightbulb',
    '온천': 'fas fa-hot-tub',
    '역사관': 'fas fa-scroll',
    '영화관': 'fas fa-film',
    '과학관': 'fas fa-atom',
    '미술관': 'fas fa-palette',
    '자연': 'fas fa-mountain',
    '생태공원': 'fas fa-leaf',
    '전통시장': 'fas fa-store',
    '랜드마크': 'fas fa-building',
    '비즈니스 구역': 'fas fa-briefcase',
    '전시컨벤션': 'fas fa-calendar-alt',
    '고급 주거지': 'fas fa-home',
    '쇼핑몰': 'fas fa-shopping-cart',
    '고급 레스토랑': 'fas fa-utensils',
    '전망대': 'fas fa-binoculars',
    '복합문화공간': 'fas fa-building',
    '문화공간': 'fas fa-theater-masks',
    '갤러리': 'fas fa-image',
    'K-pop 성지': 'fas fa-music',
    'K-pop 관련': 'fas fa-microphone',
    '드라마 촬영지': 'fas fa-video',
    '문화마을': 'fas fa-home',
    '해수욕장': 'fas fa-umbrella-beach',
    '문학관': 'fas fa-feather-alt',
    '책방거리': 'fas fa-book-open',
    '역사거리': 'fas fa-road',
    '테마파크': 'fas fa-ferris-wheel',
    '관광열차': 'fas fa-train',
    '케이블카': 'fas fa-mountain',
    '아쿠아리움': 'fas fa-fish',
    '문화거리': 'fas fa-street-view',
    '이벤트': 'fas fa-calendar-star',
    '수산시장': 'fas fa-fish',
    '쇼핑거리': 'fas fa-shopping-bag',
    '상업지구': 'fas fa-city',
    '백화점': 'fas fa-store-alt',
    '호텔': 'fas fa-bed',
    '관공서': 'fas fa-building-columns',
    '방송국': 'fas fa-broadcast-tower',
    '야시장': 'fas fa-moon',
    '카페거리': 'fas fa-coffee',
    '항구': 'fas fa-anchor',
    '예술관': 'fas fa-paint-brush',
    '영화거리': 'fas fa-film',
    'VR체험': 'fas fa-vr-cardboard',
    
    // 영어 카테고리
    'Temple': 'fas fa-torii-gate',
    'Museum': 'fas fa-university',
    'History': 'fas fa-landmark',
    'Park': 'fas fa-tree',
    'Walking Trail': 'fas fa-walking',
    'Cultural Facility': 'fas fa-theater-masks',
    'Library': 'fas fa-book',
    'Lighthouse': 'fas fa-lightbulb',
    'Hot Springs': 'fas fa-hot-tub',
    'History Museum': 'fas fa-scroll',
    'Cinema': 'fas fa-film',
    'Science Center': 'fas fa-atom',
    'Art Museum': 'fas fa-palette',
    'Nature': 'fas fa-mountain',
    'Ecological Park': 'fas fa-leaf',
    'Traditional Market': 'fas fa-store',
    'Landmark': 'fas fa-building',
    'Business District': 'fas fa-briefcase',
    'Exhibition Convention': 'fas fa-calendar-alt',
    'Luxury Residential': 'fas fa-home',
    'Shopping Mall': 'fas fa-shopping-cart',
    'Fine Dining': 'fas fa-utensils',
    'Observatory': 'fas fa-binoculars',
    'Complex Cultural Space': 'fas fa-building',
    'Cultural Space': 'fas fa-theater-masks',
    'Gallery': 'fas fa-image',
    'K-pop Holy Site': 'fas fa-music',
    'K-pop Related': 'fas fa-microphone',
    'Drama Location': 'fas fa-video',
    'Culture Village': 'fas fa-home',
    'Beach': 'fas fa-umbrella-beach',
    'Literature Museum': 'fas fa-feather-alt',
    'Book Street': 'fas fa-book-open',
    'Historic Street': 'fas fa-road',
    'Theme Park': 'fas fa-ferris-wheel',
    'Tourist Train': 'fas fa-train',
    'Cable Car': 'fas fa-mountain',
    'Aquarium': 'fas fa-fish',
    'Cultural Street': 'fas fa-street-view',
    'Event': 'fas fa-calendar-star',
    'Fish Market': 'fas fa-fish',
    'Shopping Street': 'fas fa-shopping-bag',
    'Department Store': 'fas fa-store-alt',
    'Hotel': 'fas fa-bed',
    'Government Office': 'fas fa-building-columns',
    'Broadcasting Station': 'fas fa-broadcast-tower',
    'Night Market': 'fas fa-moon',
    'Cafe Street': 'fas fa-coffee',
    'Port': 'fas fa-anchor',
    'Art Center': 'fas fa-paint-brush',
    'Movie Street': 'fas fa-film'
};

// 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // MBTI 카드 요소들 선택 (DOM이 로드된 후)
    mbtiCards = document.querySelectorAll('.mbti-card');
    
    // URL 파라미터에서 언어 설정 확인
    const urlParams = new URLSearchParams(window.location.search);
    const langParam = urlParams.get('lang');
    if (langParam && translations[langParam]) {
        changeLanguage(langParam);
    }
    // 언어 버튼 이벤트 리스너
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            changeLanguage(lang);
        });
    });
    
    // MBTI 카드 이벤트 리스너
    mbtiCards.forEach(card => {
        card.addEventListener('click', function() {
            const mbtiType = this.getAttribute('data-mbti');
            selectMBTI(mbtiType);
        });
        
        // 키보드 접근성
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const mbtiType = this.getAttribute('data-mbti');
                selectMBTI(mbtiType);
            }
        });
    });
    
    // 뒤로 가기 버튼
    backBtn.addEventListener('click', function() {
        showMBTISelection();
    });
    
    // 모달 닫기 이벤트
    modalClose.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', function(e) {
        if (e.target === modalOverlay) {
            closeModal();
        }
    });
    
    // ESC 키로 모달 닫기
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
    
    // 초기 텍스트 업데이트
    updateTexts();
    
    // 애니메이션 효과
    addScrollAnimations();
}

function selectMBTI(mbtiType) {
    // 선택된 카드 표시
    mbtiCards.forEach(card => card.classList.remove('selected'));
    const selectedCard = document.querySelector(`[data-mbti="${mbtiType}"]`);
    
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    // 결과 화면으로 전환
    showResults(mbtiType);
}

function showResults(mbtiType) {
    const data = mbtiData[mbtiType];
    if (!data) {
        console.error('MBTI 데이터를 찾을 수 없습니다:', mbtiType);
        return;
    }
    
    const langData = data[currentLanguage] || data['ko'];
    
    // 선택된 MBTI 정보 업데이트
    updateSelectedMBTIInfo(mbtiType, langData);
    
    // 관광지 카드들 생성
    generateAttractionCards(langData.attractions);
    
    // 화면 전환
    document.querySelector('.mbti-selection-section').style.display = 'none';
    resultsSection.style.display = 'block';
    
    // 스크롤을 최상단으로
    window.scrollTo(0, 0);
}

function updateSelectedMBTIInfo(mbtiType, data) {
    document.getElementById('selected-mbti-type').textContent = mbtiType;
    document.getElementById('selected-mbti-title').textContent = data.title;
    document.getElementById('selected-mbti-description').textContent = data.description;
    
    // 아이콘 업데이트
    const iconElement = document.getElementById('selected-mbti-icon').querySelector('i');
    iconElement.className = mbtiIcons[mbtiType] || 'fas fa-user';
}

async function generateAttractionCards(attractions) {
    attractionsGrid.innerHTML = '';
    
    // 이미지 로딩 통계 초기화
    imageLoadingStats.reset();
    
    // 모든 카드를 비동기로 생성
    const cardPromises = attractions.map(async (attraction, index) => {
        const card = await createAttractionCard(attraction, index);
        return { card, index };
    });
    
    // 카드들이 생성되는 대로 DOM에 추가
    for (const cardPromise of cardPromises) {
        try {
            const { card } = await cardPromise;
            attractionsGrid.appendChild(card);
            imageLoadingStats.incrementTotal();
        } catch (error) {
            console.error('카드 생성 중 오류:', error);
        }
    }
}

async function createAttractionCard(attraction, index) {
    const card = document.createElement('div');
    card.className = 'attraction-card fade-in-up';
    card.style.animationDelay = `${index * 0.1}s`;
    card.setAttribute('role', 'listitem');
    
    const categoryIcon = categoryIcons[attraction.category] || 'fas fa-map-marker-alt';
    const cardColors = [
        'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
        'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
    ];
    
    const bgColor = cardColors[index % cardColors.length];
    
    // 관광지 이미지 URL 생성 (비동기)
    const imageUrl = await getAttractionImageUrl(attraction.name, attraction.category);
    
    card.innerHTML = `
        <div class="attraction-image-container">
            <div class="image-loading-placeholder" style="background: ${bgColor};" aria-hidden="true">
                <div class="loading-spinner"></div>
            </div>
            <img class="attraction-photo" 
                 src="${imageUrl}" 
                 alt="${attraction.name} 관광지 이미지"
                 onerror="handleImageError(this, '${categoryIcon}', '${bgColor}')"
                 onload="handleImageLoad(this)">
            <div class="attraction-image-fallback" style="background: ${bgColor}; display: none;" aria-hidden="true">
                <i class="${categoryIcon}"></i>
            </div>
            <div class="attraction-image-overlay" aria-hidden="true">
                <span class="attraction-category-tag">${attraction.category}</span>
            </div>
        </div>
        <div class="attraction-content">
            <h3 class="attraction-name">${attraction.name}</h3>
            <p class="attraction-reason">${attraction.reason}</p>
            <div class="attraction-actions">
                <button class="btn btn-primary" onclick="showAttractionDetails('${attraction.name}', '${attraction.category}', '${attraction.reason}')" aria-label="${attraction.name} 상세 정보 보기">
                    <i class="fas fa-info-circle" aria-hidden="true"></i>
                    <span data-text="view_details">${getText('view_details')}</span>
                </button>
                <button class="btn btn-secondary" onclick="showLocation('${attraction.name}')" aria-label="${attraction.name} 위치 지도에서 보기">
                    <i class="fas fa-map-marker-alt" aria-hidden="true"></i>
                    <span data-text="show_location">${getText('show_location')}</span>
                </button>
            </div>
        </div>
    `;
    
    // 이미지 로딩 타임아웃 설정 (8초)
    const img = card.querySelector('.attraction-photo');
    img.timeoutId = setTimeout(() => {
        if (img && img.style.display === 'none') {
            handleImageError(img, categoryIcon, bgColor);
        }
    }, 8000);
    
    // 이미지 로딩 이벤트 리스너 추가
    img.addEventListener('imageLoadComplete', function(event) {
        if (event.detail.success) {
            imageLoadingStats.incrementLoaded();
        } else {
            imageLoadingStats.incrementFailed();
        }
    });
    
    return card;
}

// 관광지 이미지 캐시
const imageCache = new Map();

// 관광지 이미지 URL 생성 함수 (원래 Unsplash 방식)
async function getAttractionImageUrl(name, category) {
    // 캐시에서 먼저 확인
    if (imageCache.has(name)) {
        return imageCache.get(name);
    }
    
    // Unsplash API를 사용한 이미지 생성 (원래 방식)
    const keyword = generateImageKeyword(name, category);
    const imageUrl = `https://source.unsplash.com/800x600/?${encodeURIComponent(keyword)}`;
    
    // 캐시에 저장
    imageCache.set(name, imageUrl);
    return imageUrl;
}


// 폴백 이미지 (카테고리별)
function getFallbackImage(category) {
    const fallbackImages = {
        '사찰': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop',
        '박물관': 'https://images.unsplash.com/photo-1566127992631-137a642a90f4?w=800&h=600&fit=crop',
        '미술관': 'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=800&h=600&fit=crop',
        '공원': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&h=600&fit=crop',
        '해수욕장': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
        '전망대': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
        '시장': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&h=600&fit=crop',
        '문화마을': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop',
        '온천': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop',
        '케이블카': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
        'Temple': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop',
        'Museum': 'https://images.unsplash.com/photo-1566127992631-137a642a90f4?w=800&h=600&fit=crop',
        'Beach': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
        'Park': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&h=600&fit=crop'
    };
    
    return fallbackImages[category] || 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop';
}

// 문자열을 해시코드로 변환 (캐싱용)
function hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // 32비트 정수로 변환
    }
    return Math.abs(hash);
}

// 관광지 이름과 카테고리에 맞는 검색 키워드 생성
function generateImageKeyword(name, category) {
    // 특정 관광지에 대한 맞춤 키워드
    const specificKeywords = {
        '범어사': 'korean temple traditional buddhist architecture',
        '부산박물관': 'museum korea busan cultural heritage',
        '국립해양박물관': 'maritime museum ocean ship',
        '해운대 해수욕장': 'busan haeundae beach korea ocean',
        '광안리 해수욕장': 'gwangalli beach busan night view bridge',
        '태종대': 'taejongdae cliff ocean korea busan',
        '감천문화마을': 'gamcheon culture village colorful houses busan',
        '자갈치시장': 'jagalchi fish market busan korea',
        '부산타워': 'busan tower city view korea',
        '센텀시티': 'centum city busan modern architecture',
        '해동용궁사': 'haedong yonggungsa temple ocean korea',
        '송도해상케이블카': 'cable car ocean busan korea',
        '부평깡통야시장': 'night market korea food street',
        '국제시장': 'international market korea traditional shopping',
        '을숙도 생태공원': 'eulsukdo ecological park birds nature korea',
        '광안대교': 'gwangan bridge busan night view',
        '다대포 해수욕장': 'dadaepo beach sunset korea busan',
        '민락수변공원': 'millak waterside park busan ocean',
        '용두산공원': 'yongdusan park busan tower korea',
        '온천천 시민공원': 'oncheoncheon park stream korea busan',
        'F1963 복합문화공간': 'f1963 cultural space industrial architecture',
        '부산현대미술관': 'contemporary art museum modern korea',
        '부산문화회관': 'cultural center performance hall korea',
        '부산국제금융센터': 'bifc busan international finance center',
        '벡스코': 'bexco convention center busan modern',
        '롯데월드 어드벤처 부산': 'lotte world adventure theme park busan',
        '해운대 블루라인 파크': 'blueline park train coastal busan',
        '부산 아쿠아리움': 'aquarium underwater marine life',
        '송도구름산책로': 'songdo cloud walk coastal path korea',
        '이기대 해안산책로': 'igidae coastal trail rocks ocean korea',
        '흰여울문화마을': 'huinnyeoul culture village white houses ocean',
        'UN평화공원': 'un peace park memorial korea busan',
        '보수동 책방골목': 'book street old bookstore korea traditional',
        '40계단 문화관광테마거리': '40 steps cultural street korea history',
        '부산민주공원': 'democracy park memorial korea busan',
        '전포카페거리': 'jeonpo cafe street trendy korea busan',
        '해리단길': 'haeridan gil street food cafe busan',
        '남포동': 'nampo dong shopping district busan korea',
    };
    
    // 특정 키워드가 있으면 사용, 없으면 카테고리 기반 키워드 생성
    if (specificKeywords[name]) {
        return specificKeywords[name];
    }
    
    // 카테고리별 기본 키워드
    const categoryKeywords = {
        // 한국어 카테고리
        '사찰': 'korean temple buddhist traditional architecture',
        '박물관': 'museum cultural heritage korea',
        '미술관': 'art museum gallery korea',
        '공원': 'park nature korea landscape',
        '해수욕장': 'beach ocean korea coastal',
        '전망대': 'observatory city view korea',
        '시장': 'traditional market korea food',
        '문화마을': 'cultural village korea traditional houses',
        '온천': 'hot spring spa korea traditional',
        '케이블카': 'cable car mountain ocean view',
        '테마파크': 'theme park amusement rides',
        '아쿠아리움': 'aquarium marine life underwater',
        '문화거리': 'cultural street korea urban',
        '카페거리': 'cafe street trendy korea urban',
        '야시장': 'night market food street korea',
        '쇼핑몰': 'shopping mall modern korea',
        '랜드마크': 'landmark architecture korea modern',
        '항구': 'harbor port ships korea',
        '등대': 'lighthouse ocean coast korea',
        '산책로': 'walking trail nature korea coastal',
        
        // 영어 카테고리
        'Temple': 'korean temple buddhist traditional architecture',
        'Museum': 'museum cultural heritage korea',
        'Art Museum': 'art museum gallery korea',
        'Park': 'park nature korea landscape',
        'Beach': 'beach ocean korea coastal',
        'Observatory': 'observatory city view korea',
        'Market': 'traditional market korea food',
        'Culture Village': 'cultural village korea traditional houses',
        'Hot Springs': 'hot spring spa korea traditional',
        'Cable Car': 'cable car mountain ocean view korea',
        'Theme Park': 'theme park amusement rides',
        'Aquarium': 'aquarium marine life underwater',
        'Cultural Street': 'cultural street korea urban',
        'Cafe Street': 'cafe street trendy korea urban',
        'Night Market': 'night market food street korea',
        'Shopping Mall': 'shopping mall modern korea',
        'Landmark': 'landmark architecture korea modern',
        'Port': 'harbor port ships korea',
        'Lighthouse': 'lighthouse ocean coast korea',
        'Walking Trail': 'walking trail nature korea coastal'
    };
    
    const baseKeyword = categoryKeywords[category] || 'korea busan tourism attraction';
    return `${baseKeyword} travel destination`;
}

// 이미지 로딩 성공 핸들러
function handleImageLoad(img) {
    const container = img.parentElement;
    const placeholder = container.querySelector('.image-loading-placeholder');
    const fallback = container.querySelector('.attraction-image-fallback');
    
    // 타임아웃 클리어
    if (img.timeoutId) {
        clearTimeout(img.timeoutId);
    }
    
    if (placeholder) {
        placeholder.style.display = 'none';
    }
    if (fallback) {
        fallback.style.display = 'none';
    }
    img.style.display = 'block';
    img.style.opacity = '0';
    
    // 페이드인 효과
    setTimeout(() => {
        img.style.transition = 'opacity 0.3s ease-in-out';
        img.style.opacity = '1';
    }, 50);
    
    // 로딩 완료 이벤트 발생
    img.dispatchEvent(new CustomEvent('imageLoadComplete', { 
        detail: { success: true, element: img }
    }));
}

// 이미지 로딩 실패 핸들러  
function handleImageError(img, iconClass, bgColor) {
    const container = img.parentElement;
    const placeholder = container.querySelector('.image-loading-placeholder');
    const fallback = container.querySelector('.attraction-image-fallback');
    
    // 타임아웃 클리어
    if (img.timeoutId) {
        clearTimeout(img.timeoutId);
    }
    
    img.style.display = 'none';
    if (placeholder) {
        placeholder.style.display = 'none';
    }
    if (fallback) {
        fallback.innerHTML = `<i class="${iconClass}"></i>`;
        fallback.style.background = bgColor;
        fallback.style.display = 'flex';
        
        // 페이드인 효과
        fallback.style.opacity = '0';
        setTimeout(() => {
            fallback.style.transition = 'opacity 0.3s ease-in-out';
            fallback.style.opacity = '1';
        }, 50);
    }
    
    // 로딩 실패 이벤트 발생
    img.dispatchEvent(new CustomEvent('imageLoadComplete', { 
        detail: { success: false, element: img, fallback: true }
    }));
}

// 이미지 로딩 상태 추적
const imageLoadingStats = {
    total: 0,
    loaded: 0,
    failed: 0,
    
    incrementTotal() {
        this.total++;
    },
    
    incrementLoaded() {
        this.loaded++;
        this.logProgress();
    },
    
    incrementFailed() {
        this.failed++;
        this.logProgress();
    },
    
    logProgress() {
        const completed = this.loaded + this.failed;
        if (completed === this.total && this.total > 0) {
            console.log(`이미지 로딩 완료: ${this.loaded}/${this.total} 성공, ${this.failed}/${this.total} 실패`);
        }
    },
    
    reset() {
        this.total = 0;
        this.loaded = 0;
        this.failed = 0;
    }
};

async function showAttractionDetails(name, category, reason) {
    // 현재 포커스된 요소 저장
    lastFocusedElement = document.activeElement;
    
    modalTitle.textContent = name;
    
    const categoryIcon = categoryIcons[category] || 'fas fa-map-marker-alt';
    
    // 간단한 상세 정보 표시 (원래 방식)
    const detailInfo = getFallbackDetailInfo(name);
    
    attractionInfo.innerHTML = `
        <div class="attraction-detail-header">
            <div class="attraction-detail-icon" aria-hidden="true">
                <i class="${categoryIcon}"></i>
            </div>
            <div class="attraction-detail-info">
                <h3>${name}</h3>
                <span class="attraction-detail-category">${category}</span>
            </div>
        </div>
        <div class="attraction-detail-content">
            <h4>${getText('why_recommend') || '추천 이유'}</h4>
            <p>${reason}</p>
            
            ${detailInfo ? `
                <div class="attraction-detail-description">
                    <h4>상세 정보</h4>
                    <p>${detailInfo.description}</p>
                    ${detailInfo.address ? `<p class="attraction-address"><i class="fas fa-map-marker-alt"></i> ${detailInfo.address}</p>` : ''}
                    ${detailInfo.hours ? `<p class="attraction-hours"><i class="fas fa-clock"></i> ${detailInfo.hours}</p>` : ''}
                    ${detailInfo.phone ? `<p class="attraction-phone"><i class="fas fa-phone"></i> ${detailInfo.phone}</p>` : ''}
                    ${detailInfo.homepage ? `<p class="attraction-homepage"><i class="fas fa-globe"></i> <a href="${detailInfo.homepage}" target="_blank">홈페이지</a></p>` : ''}
                </div>
            ` : `
                <div class="attraction-detail-description">
                    <h4>관광지 정보</h4>
                    <p>이 관광지에 대한 자세한 정보는 위치보기 버튼을 통해 확인하실 수 있습니다.</p>
                </div>
            `}
        </div>
    `;
    
    openModal();
}


// 폴백 상세 정보
function getFallbackDetailInfo(name) {
    const fallbackDetails = {
        '범어사': {
            description: '한국 불교 조계종의 사찰로, 678년에 의상대사가 창건했습니다. 금정산 중턱에 위치해 있으며, 대웅전과 삼층석탑이 보물로 지정되어 있습니다.',
            address: '부산광역시 금정구 범어사로 250',
            hours: '일출~일몰 (입장료 무료)',
            phone: '051-508-3122'
        },
        '부산박물관': {
            description: '부산의 역사와 문화를 한눈에 볼 수 있는 종합박물관입니다. 선사시대부터 현대까지의 부산 지역 문화유산을 체계적으로 전시하고 있습니다.',
            address: '부산광역시 남구 유엔평화로 63',
            hours: '09:00~18:00 (월요일 휴관)',
            phone: '051-610-7111'
        },
        '국립해양박물관': {
            description: '우리나라 유일의 종합 해양박물관으로, 해양문화, 해양역사, 해양과학 등을 체험할 수 있습니다. 4D 영상관과 아쿠아리움도 운영됩니다.',
            address: '부산광역시 영도구 해양로 301번길 45',
            hours: '09:00~18:00 (월요일 휴관)',
            phone: '051-309-1900'
        },
        '해운대 해수욕장': {
            description: '한국 최대의 해수욕장으로, 1.5km의 백사장과 다양한 해양 레저 활동을 즐길 수 있습니다. 매년 부산 국제영화제가 열리는 곳이기도 합니다.',
            address: '부산광역시 해운대구 해운대해변로 264',
            hours: '24시간 개방 (해수욕 시설은 계절별 운영)',
            phone: '051-749-4061'
        },
        '광안리 해수욕장': {
            description: '광안대교의 야경으로 유명한 해수욕장입니다. 밤에는 광안대교가 아름답게 조명되어 부산의 대표적인 야경 명소로 사랑받고 있습니다.',
            address: '부산광역시 수영구 광안해변로 219',
            hours: '24시간 개방',
            phone: '051-610-4421'
        },
        '태종대': {
            description: '절영도 남쪽 끝에 위치한 자연공원으로, 기암절벽과 울창한 숲이 어우러진 명승지입니다. 다누비열차를 타고 공원을 둘러볼 수 있습니다.',
            address: '부산광역시 영도구 전망로 24',
            hours: '05:00~24:00',
            phone: '051-860-7301'
        },
        '감천문화마을': {
            description: '산비탈에 계단식으로 들어선 집들이 마치 레고 블록 같다고 해서 한국의 마추픽추라고 불립니다. 골목길 곳곳에 예술 작품들이 전시되어 있습니다.',
            address: '부산광역시 사하구 감내2로 203',
            hours: '09:00~18:00',
            phone: '051-204-1444'
        },
        '자갈치시장': {
            description: '한국 최대의 수산물 시장으로, 싱싱한 해산물을 직접 구매하거나 횟집에서 바로 회를 떠서 드실 수 있습니다. 부산의 대표적인 전통시장입니다.',
            address: '부산광역시 중구 자갈치해안로 52',
            hours: '05:00~22:00 (일요일 휴무)',
            phone: '051-245-2594'
        },
        '해동용궁사': {
            description: '바다와 용왕님이 함께하는 기도도량으로 유명한 사찰입니다. 바다를 배경으로 한 아름다운 경관과 새해 해돋이 명소로도 인기가 높습니다.',
            address: '부산광역시 기장군 기장읍 용궁길 86',
            hours: '04:30~19:30',
            phone: '051-722-7744'
        },
        '송도해상케이블카': {
            description: '한국 최초의 해상케이블카로, 송도해수욕장과 암남공원을 연결합니다. 케이블카에서 내려다보는 부산 바다의 전경이 장관입니다.',
            address: '부산광역시 서구 송도해변로 171',
            hours: '09:00~22:00 (기상상황에 따라 변동)',
            phone: '051-247-9200'
        }
    };
    
    return fallbackDetails[name] || null;
}

function showLocation(name) {
    // Google Maps에서 같은 창에서 열기
    const query = encodeURIComponent(`${name} 부산`);
    const googleMapsUrl = `https://www.google.com/maps/search/${query}`;
    window.location.href = googleMapsUrl;
}

function openModal() {
    modalOverlay.classList.add('active');
    modalOverlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    
    // 포커스를 모달의 첫 번째 포커스 가능한 요소로 이동
    const focusableElements = modalOverlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusableElements.length > 0) {
        focusableElements[0].focus();
    }
    
    // 모달 내에서 포커스 트랩 설정
    trapFocus(modalOverlay);
}

function closeModal() {
    modalOverlay.classList.remove('active');
    modalOverlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    
    // 포커스를 마지막으로 활성화된 요소로 되돌리기
    if (lastFocusedElement) {
        lastFocusedElement.focus();
    }
}

// 포커스 트랩 기능
function trapFocus(element) {
    const focusableElements = element.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const firstFocusableElement = focusableElements[0];
    const lastFocusableElement = focusableElements[focusableElements.length - 1];
    
    element.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstFocusableElement) {
                    lastFocusableElement.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastFocusableElement) {
                    firstFocusableElement.focus();
                    e.preventDefault();
                }
            }
        }
    });
}

// 마지막으로 포커스된 요소 추적
let lastFocusedElement = null;

function showMBTISelection() {
    resultsSection.style.display = 'none';
    document.querySelector('.mbti-selection-section').style.display = 'block';
    
    // 선택 해제
    mbtiCards.forEach(card => card.classList.remove('selected'));
    
    // 스크롤을 MBTI 선택 섹션으로
    document.querySelector('.mbti-selection-section').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

function addScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    }, observerOptions);
    
    // 관찰할 요소들
    document.querySelectorAll('.mbti-category, .mbti-card').forEach(el => {
        observer.observe(el);
    });
}

// 반응형 네비게이션
function handleResponsiveNav() {
    const header = document.querySelector('.header');
    let lastScrollY = window.scrollY;
    
    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        if (currentScrollY < lastScrollY) {
            header.classList.remove('header-hidden');
        } else if (currentScrollY > 100) {
            header.classList.add('header-hidden');
        }
        
        lastScrollY = currentScrollY;
    });
}

// 성능 최적화를 위한 디바운스 함수
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 윈도우 리사이즈 핸들러
window.addEventListener('resize', debounce(() => {
    // 필요한경우 레이아웃 재조정
}, 250));

// 페이지 로드 완료 후 추가 초기화
window.addEventListener('load', () => {
    handleResponsiveNav();
    
    // 페이지 로딩 애니메이션 완료
    document.body.classList.add('loaded');
});