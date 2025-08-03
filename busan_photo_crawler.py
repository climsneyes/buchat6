import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
import os

class BusanPhotoCrawler:
    def __init__(self):
        self.base_url = "https://www.visitbusan.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.photos_data = {}
        
    def get_page_data(self, page_no=1):
        """특정 페이지의 관광지 사진 데이터를 크롤링"""
        url = f"{self.base_url}/index.do?menuCd=DOM_000000204009000000&title=&cate1s=&cate2s=&take_year=&rgt_type_code=1&searchwd=&list_type=TYPE_SMALL_CARD&order_type=VIEW&listCntPerPage2=15&page_no={page_no}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            photos = []
            
            # 페이지 내용 확인을 위한 디버그
            print(f"페이지 {page_no} HTML 길이: {len(response.content)}")
            
            # 부산 관광사진 카드 추출
            cards = soup.find_all('div', class_='cardlist')
            print(f"cardlist 클래스로 찾은 카드 수: {len(cards)}")
            
            if not cards:
                # 다른 선택자들 시도
                cards = soup.find_all('li', class_='cardlist')
                print(f"li.cardlist로 찾은 카드 수: {len(cards)}")
                
                if not cards:
                    cards = soup.find_all('div', class_='li')
                    print(f"div.li로 찾은 카드 수: {len(cards)}")
                    
                    if not cards:
                        # 모든 div와 li 태그 확인
                        all_divs = soup.find_all('div')
                        all_lis = soup.find_all('li')
                        print(f"전체 div 수: {len(all_divs)}, 전체 li 수: {len(all_lis)}")
                        
                        # 이미지가 있는 요소들 찾기
                        img_containers = soup.find_all(lambda tag: tag.find('img'))
                        print(f"이미지를 포함한 요소 수: {len(img_containers)}")
                        
                        # 실제 HTML 구조 확인
                        if img_containers:
                            print("첫 번째 이미지 컨테이너 HTML:")
                            print(str(img_containers[0])[:500])
                        
                        cards = img_containers[:15]  # 최대 15개만
            
            for card in cards:
                try:
                    photo_data = self.extract_photo_info(card)
                    if photo_data:
                        photos.append(photo_data)
                except Exception as e:
                    print(f"개별 사진 정보 추출 오류: {e}")
                    continue
            
            return photos
            
        except Exception as e:
            print(f"페이지 {page_no} 크롤링 오류: {e}")
            return []
    
    def extract_photo_info(self, card_element):
        """카드 요소에서 사진 정보 추출"""
        photo_info = {}
        
        # 이미지 URL 추출
        img_tag = card_element.find('img')
        if img_tag:
            img_src = img_tag.get('src') or img_tag.get('data-src')
            if img_src:
                # 썸네일을 원본 이미지로 변경 (가능한 경우)
                if '_thumbL' in img_src:
                    original_src = img_src.replace('_thumbL', '')
                    photo_info['image_url'] = urljoin(self.base_url, original_src)
                    photo_info['thumbnail_url'] = urljoin(self.base_url, img_src)
                else:
                    photo_info['image_url'] = urljoin(self.base_url, img_src)
        
        # 관광지 이름 추출 (.subject 클래스 사용)
        title_element = card_element.find('div', class_='subject')
        if title_element:
            title = title_element.get_text(strip=True)
            photo_info['title'] = title
        
        # 촬영 정보 추출
        dl_elements = card_element.find_all('dl')
        for dl in dl_elements:
            dt_elements = dl.find_all('dt')
            dd_elements = dl.find_all('dd')
            
            for dt, dd in zip(dt_elements, dd_elements):
                dt_text = dt.get_text(strip=True)
                dd_text = dd.get_text(strip=True)
                
                if '촬영연도' in dt_text:
                    photo_info['year'] = dd_text
                elif '촬영기관' in dt_text:
                    photo_info['agency'] = dd_text
                elif '보유기관' in dt_text:
                    photo_info['institution'] = dd_text
        
        # 해시태그 추출
        hashtag_element = card_element.find('div', class_='hash-tag')
        if hashtag_element:
            hashtag_text = hashtag_element.get_text()
            hashtags = re.findall(r'#\w+', hashtag_text)
            photo_info['hashtags'] = hashtags
        
        # 다운로드 정보 추출
        download_element = card_element.find('div', class_='download-info')
        if download_element:
            download_link = download_element.find('a', class_='download-link')
            if download_link:
                download_text = download_link.get_text(strip=True)
                download_count = re.search(r'\d+', download_text)
                if download_count:
                    photo_info['download_count'] = int(download_count.group())
        
        # 최소 정보가 있는 경우만 반환
        if photo_info.get('image_url') and photo_info.get('title'):
            photo_info['source'] = "부산광역시 관광사진 (visitbusan.net)"
            photo_info['copyright'] = "부산광역시청 / 공공누리"
            return photo_info
        
        return None
    
    def crawl_multiple_pages(self, start_page=1, end_page=10):
        """여러 페이지를 크롤링"""
        all_photos = []
        
        for page_no in range(start_page, end_page + 1):
            print(f"페이지 {page_no} 크롤링 중...")
            page_photos = self.get_page_data(page_no)
            all_photos.extend(page_photos)
            
            # 서버 부하 방지를 위한 딜레이
            time.sleep(1)
            
            if not page_photos:
                print(f"페이지 {page_no}에서 데이터를 찾을 수 없습니다. 크롤링을 중단합니다.")
                break
        
        return all_photos
    
    def organize_by_attraction(self, photos):
        """관광지별로 사진 데이터 정리"""
        organized = {}
        
        # MBTI 관광지 이름과 매칭
        mbti_attractions = {
            "해운대": ["해운대", "해운대해수욕장", "해운대비치"],
            "광안리": ["광안리", "광안대교", "광안리해수욕장"],
            "범어사": ["범어사", "범어사계곡"],
            "부산타워": ["부산타워", "용두산공원"],
            "감천문화마을": ["감천", "감천문화마을", "감천동"],
            "태종대": ["태종대", "태종대유원지"],
            "자갈치시장": ["자갈치", "자갈치시장"],
            "국제시장": ["국제시장", "부평시장"],
            "동백섬": ["동백섬", "동백공원"],
            "오륙도": ["오륙도", "오륙도스카이워크"],
            "송도": ["송도", "송도해수욕장", "송도케이블카"],
            "흰여울문화마을": ["흰여울", "흰여울문화마을"],
            "다대포": ["다대포", "다대포해수욕장"],
            "기장": ["기장", "기장해수욕장"],
            "부산현대미술관": ["현대미술관", "부산현대미술관"],
            "UN기념공원": ["UN기념공원", "유엔기념공원"],
            "부산박물관": ["부산박물관", "시립박물관"],
            "부산국제영화제": ["BIFF", "영화제", "부산국제영화제"],
            "센텀시티": ["센텀", "센텀시티"],
            "서면": ["서면", "서면거리"],
            "남포동": ["남포동", "남포"],
            "용두산공원": ["용두산", "용두산공원"],
            "부산역": ["부산역", "부산스테이션"],
            "해동용궁사": ["해동용궁사", "용궁사"],
            "부산항": ["부산항", "부산포트"],
            "영도": ["영도", "영도대교"],
            "중구": ["중구", "부산중구"],
            "동래": ["동래", "동래온천"],
            "기장군": ["기장군", "기장읍"],
            "부산대학교": ["부산대", "부산대학교"]
        }
        
        for photo in photos:
            title = photo.get('title', '').lower()
            matched = False
            
            for attraction, keywords in mbti_attractions.items():
                for keyword in keywords:
                    if keyword.lower() in title:
                        if attraction not in organized:
                            organized[attraction] = []
                        organized[attraction].append(photo)
                        matched = True
                        break
                if matched:
                    break
        
        return organized
    
    def save_to_json(self, data, filename="busan_photos.json"):
        """데이터를 JSON 파일로 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"데이터가 {filename}에 저장되었습니다.")

def main():
    crawler = BusanPhotoCrawler()
    
    # 6페이지까지 크롤링 (사용자가 제공한 URL 기준)
    print("부산 관광사진 크롤링 시작...")
    photos = crawler.crawl_multiple_pages(1, 6)
    
    print(f"총 {len(photos)}개의 사진 정보를 수집했습니다.")
    
    # 관광지별로 정리
    organized_photos = crawler.organize_by_attraction(photos)
    
    print("관광지별 사진 수:")
    for attraction, photos_list in organized_photos.items():
        print(f"  {attraction}: {len(photos_list)}개")
    
    # JSON 파일로 저장
    crawler.save_to_json(organized_photos, "C:/buchat(7.25.)/buchat2/busan_photos_visitbusan.json")
    
    return organized_photos

if __name__ == "__main__":
    main()