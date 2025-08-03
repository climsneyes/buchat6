// MBTI별 부산 관광지 추천 데이터
const mbtiData = {
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
        {"name": "F1963 Complex Cultural Space", "category": "Complex Cultural Space", "reason": "Creative cultural space renovated from old Koryo Steel factory"},
        {"name": "Busan Museum of Contemporary Art", "category": "Art Museum", "reason": "Experimental and creative works of contemporary art"},
        {"name": "Eulsukdo Cultural Center", "category": "Cultural Space", "reason": "Various experimental performances and exhibitions"},
        {"name": "Arpina", "category": "Gallery", "reason": "Creative works exhibition by young artists"},
        {"name": "BTS 'Spring Day' MV Location (Gamcheon Culture Village)", "category": "K-pop Holy Site", "reason": "Colorful village famous as BTS music video filming location"},
        {"name": "BIGBANG Seungri's Cafe 'MONKEY MUSEUM'", "category": "K-pop Related", "reason": "Unique cafe culture related to K-pop idol"},
        {"name": "Drama 'City Couple's Way of Love' Location (Haeridan-gil)", "category": "Drama Location", "reason": "Street where young and trendy culture lives and breathes"}
      ]
    }
  },
  "INFJ": {
    "ko": {
      "title": "선의의 옹호자형",
      "description": "의미있는 경험과 내적 성찰을 추구하는 당신에게 추천합니다.",
      "attractions": [
        {"name": "해동용궁사", "category": "사찰", "reason": "바다와 어우러진 신비로운 사찰에서의 명상"},
        {"name": "흰여울문화마을", "category": "문화마을", "reason": "영화 '변호인'의 배경이 된 서정적인 마을"},
        {"name": "민락수변공원", "category": "공원", "reason": "고요한 바다를 바라보며 내적 평화를 찾을 수 있는 곳"},
        {"name": "온천천 시민공원", "category": "공원", "reason": "자연 속에서 평온한 산책과 사색"},
        {"name": "부산문학관", "category": "문학관", "reason": "문학을 통한 깊이 있는 사유와 감상"},
        {"name": "용두산공원", "category": "공원", "reason": "도심 속 조용한 휴식처에서의 명상"},
        {"name": "드라마 '49일' 촬영지 (해동용궁사)", "category": "드라마 촬영지", "reason": "생명과 죽음을 다룬 드라마의 철학적 배경"}
      ]
    },
    "en": {
      "title": "Gentle Advocate",
      "description": "Recommended for those who pursue meaningful experiences and inner reflection.",
      "attractions": [
        {"name": "Haedong Yonggungsa Temple", "category": "Temple", "reason": "Meditation in mysterious temple harmonizing with the sea"},
        {"name": "Huinnyeoul Culture Village", "category": "Culture Village", "reason": "Lyrical village that became background of movie 'The Attorney'"},
        {"name": "Millak Waterside Park", "category": "Park", "reason": "Place to find inner peace while looking at quiet sea"},
        {"name": "Oncheoncheon Citizens Park", "category": "Park", "reason": "Peaceful walk and contemplation in nature"},
        {"name": "Busan Literature Museum", "category": "Literature Museum", "reason": "Deep thinking and appreciation through literature"},
        {"name": "Yongdusan Park", "category": "Park", "reason": "Meditation in quiet resting place in city center"},
        {"name": "Drama '49 Days' Location (Haedong Yonggungsa Temple)", "category": "Drama Location", "reason": "Philosophical background of drama dealing with life and death"}
      ]
    }
  },
  "INFP": {
    "ko": {
      "title": "열정적인 중재자형",
      "description": "개인적 가치와 창의적 영감을 추구하는 당신에게 추천합니다.",
      "attractions": [
        {"name": "감천문화마을", "category": "문화마을", "reason": "다채로운 벽화와 예술 작품으로 가득한 창의적 공간"},
        {"name": "다대포 해수욕장", "category": "해수욕장", "reason": "부산에서 가장 아름다운 일몰을 감상할 수 있는 곳"},
        {"name": "보수동 책방골목", "category": "책방거리", "reason": "오래된 책들 사이에서 찾는 지적 영감"},
        {"name": "부산현대미술관", "category": "미술관", "reason": "현대 예술의 다양한 표현과 창작 기법"},
        {"name": "이기대 해안산책로", "category": "산책로", "reason": "자연의 아름다움 속에서 영감을 얻을 수 있는 곳"},
        {"name": "드라마 '상속자들' 촬영지 (동백섬)", "category": "드라마 촬영지", "reason": "로맨틱한 드라마의 감성적 배경"},
        {"name": "2NE1 박봄 가족 운영 카페", "category": "K-pop 관련", "reason": "K-pop 아티스트의 개인적 공간에서 느끼는 친밀감"}
      ]
    },
    "en": {
      "title": "Passionate Mediator",
      "description": "Recommended for those who pursue personal values and creative inspiration.",
      "attractions": [
        {"name": "Gamcheon Culture Village", "category": "Culture Village", "reason": "Creative space full of colorful murals and art works"},
        {"name": "Dadaepo Beach", "category": "Beach", "reason": "Place to view the most beautiful sunset in Busan"},
        {"name": "Bosu-dong Book Street", "category": "Book Street", "reason": "Intellectual inspiration found among old books"},
        {"name": "Busan Museum of Contemporary Art", "category": "Art Museum", "reason": "Various expressions and creative techniques of contemporary art"},
        {"name": "Igidae Coastal Walking Trail", "category": "Walking Trail", "reason": "Place to gain inspiration in the beauty of nature"},
        {"name": "Drama 'The Heirs' Location (Dongbaek Island)", "category": "Drama Location", "reason": "Emotional background of romantic drama"},
        {"name": "2NE1 Park Bom's Family Cafe", "category": "K-pop Related", "reason": "Intimacy felt in K-pop artist's personal space"}
      ]
    }
  },
  "ENFJ": {
    "ko": {
      "title": "정의로운 사회운동가형",
      "description": "사람들과의 연결과 사회적 의미를 추구하는 당신에게 추천합니다.",
      "attractions": [
        {"name": "부산민주공원", "category": "공원", "reason": "민주화 운동의 역사를 기리는 의미있는 공간"},
        {"name": "40계단 문화관광테마거리", "category": "역사거리", "reason": "한국전쟁 피난민들의 삶의 터전이었던 역사적 장소"},
        {"name": "부산문화회관", "category": "문화시설", "reason": "시민들과 함께 문화를 향유하는 공공 공간"},
        {"name": "UN평화공원", "category": "공원", "reason": "평화와 화합의 메시지를 전하는 상징적 장소"},
        {"name": "부산시민공원", "category": "공원", "reason": "시민들의 휴식과 소통의 장"},
        {"name": "용두산공원", "category": "공원", "reason": "시민들이 모여 소통하는 도심 속 만남의 장소"},
        {"name": "드라마 '동백꽃 필 무렵' 촬영지 (온천천)", "category": "드라마 촬영지", "reason": "따뜻한 공동체 정신을 그린 드라마의 배경"}
      ]
    },
    "en": {
      "title": "Righteous Social Activist",
      "description": "Recommended for those who pursue connection with people and social meaning.",
      "attractions": [
        {"name": "Busan Democracy Park", "category": "Park", "reason": "Meaningful space commemorating history of democratization movement"},
        {"name": "40-Step Cultural Tourism Theme Street", "category": "Historic Street", "reason": "Historic place that was living ground for Korean War refugees"},
        {"name": "Busan Cultural Center", "category": "Cultural Facility", "reason": "Public space to enjoy culture together with citizens"},
        {"name": "UN Peace Park", "category": "Park", "reason": "Symbolic place delivering message of peace and harmony"},
        {"name": "Busan Citizens Park", "category": "Park", "reason": "Place for citizens' rest and communication"},
        {"name": "Yongdusan Park", "category": "Park", "reason": "Meeting place in city center where citizens gather and communicate"},
        {"name": "Drama 'When the Camellia Blooms' Location (Oncheoncheon)", "category": "Drama Location", "reason": "Background of drama depicting warm community spirit"}
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
        {"name": "Drama 'Goblin' Location (Gwangan Bridge)", "category": "Drama Location", "reason": "Romantic drama background famous for beautiful night view"}
      ]
    }
  },
  "ESTP": {
    "ko": {
      "title": "모험을 즐기는 사업가형",
      "description": "활동적이고 스릴 넘치는 경험을 즐기는 당신에게 추천합니다.",
      "attractions": [
        {"name": "송도해상케이블카", "category": "케이블카", "reason": "바다 위 스릴 넘치는 케이블카 체험"},
        {"name": "부산 X the SKY", "category": "전망대", "reason": "부산 최고층에서의 짜릿한 스카이라운지 체험"},
        {"name": "해운대 해수욕장", "category": "해수욕장", "reason": "다양한 수상 스포츠와 활동적인 해변 체험"},
        {"name": "광안리 해수욕장", "category": "해수욕장", "reason": "밤늦게까지 즐기는 활기찬 해변 문화"},
        {"name": "부산항대교", "category": "랜드마크", "reason": "드라이브와 스피드를 즐길 수 있는 현대적 다리"},
        {"name": "롯데월드 어드벤처 부산", "category": "테마파크", "reason": "스릴 넘치는 놀이기구와 액티비티"},
        {"name": "태종대", "category": "자연", "reason": "절벽 트레킹과 모험적인 자연 탐험"},
        {"name": "부평깡통야시장", "category": "야시장", "reason": "활기찬 밤 문화와 즉석 먹거리 체험"},
        {"name": "드라마 '피노키오' 촬영지 (KBS부산방송총국)", "category": "드라마 촬영지", "reason": "방송 드라마의 화려한 무대 배경"}
      ]
    },
    "en": {
      "title": "Adventurous Entrepreneur",
      "description": "Recommended for those who enjoy active and thrilling experiences.",
      "attractions": [
        {"name": "Songdo Marine Cable Car", "category": "Cable Car", "reason": "Thrilling cable car experience over the sea"},
        {"name": "Busan X the SKY", "category": "Observatory", "reason": "Exciting sky lounge experience at Busan's highest floor"},
        {"name": "Haeundae Beach", "category": "Beach", "reason": "Various water sports and active beach experiences"},
        {"name": "Gwangalli Beach", "category": "Beach", "reason": "Lively beach culture enjoyed until late night"},
        {"name": "Busan Harbor Bridge", "category": "Landmark", "reason": "Modern bridge where you can enjoy driving and speed"},
        {"name": "Lotte World Adventure Busan", "category": "Theme Park", "reason": "Thrilling rides and activities"},
        {"name": "Taejongdae", "category": "Nature", "reason": "Cliff trekking and adventurous nature exploration"},
        {"name": "Bupyeong Kkangtong Night Market", "category": "Night Market", "reason": "Lively night culture and instant food experience"},
        {"name": "Drama 'Pinocchio' Location (KBS Busan Broadcasting Station)", "category": "Drama Location", "reason": "Glamorous stage background of broadcasting drama"}
      ]
    }
  },
  "ESFP": {
    "ko": {
      "title": "자유로운 영혼의 연예인형",
      "description": "즐겁고 활기찬 분위기에서 사람들과 함께하는 경험을 선호하는 당신에게 추천합니다.",
      "attractions": [
        {"name": "부평깡통야시장", "category": "야시장", "reason": "다양한 먹거리와 즐거운 밤 문화"},
        {"name": "전포카페거리", "category": "카페거리", "reason": "트렌디하고 활기찬 카페 문화"},
        {"name": "해리단길", "category": "문화거리", "reason": "젊고 활기찬 문화 공간"},
        {"name": "남포동 BIFF광장", "category": "영화거리", "reason": "영화제의 열기가 살아있는 활기찬 거리"},
        {"name": "드라마 '피노키오' 촬영지 (KBS부산방송총국)", "category": "드라마 촬영지", "reason": "방송 드라마의 화려한 무대 배경"}
      ]
    },
    "en": {
      "title": "Free-spirited Entertainer",
      "description": "Recommended for those who prefer experiences with people in fun and lively atmosphere.",
      "attractions": [
        {"name": "Bupyeong Kkangtong Night Market", "category": "Night Market", "reason": "Various food and fun night culture"},
        {"name": "Jeonpo Cafe Street", "category": "Cafe Street", "reason": "Trendy and lively cafe culture"},
        {"name": "Haeridan-gil", "category": "Cultural Street", "reason": "Young and lively cultural space"},
        {"name": "Nampo-dong BIFF Square", "category": "Movie Street", "reason": "Lively street where the heat of film festival lives on"},
        {"name": "Drama 'Pinocchio' Location (KBS Busan Broadcasting Station)", "category": "Drama Location", "reason": "Glamorous stage background of broadcasting drama"}
      ]
    }
  }
};