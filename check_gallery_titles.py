#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# TourAPI 관광사진 설정
TOUR_API_KEY = "rO5VJPog5TScnjUgCqneFaXfoep3fCsyR7VgL7dlQ1Ae99E/n3+ch8zmym+a1SIwylUd6Gj9L4E7B8txymXqMQ=="
TOUR_API_BASE_URL = "http://apis.data.go.kr/B551011/PhotoGalleryService1"

def check_gallery_titles():
    """갤러리에 있는 실제 제목들 확인"""
    try:
        gallery_url = f"{TOUR_API_BASE_URL}/galleryList1"
        params = {
            'serviceKey': TOUR_API_KEY,
            'numOfRows': 20,
            'pageNo': 1,
            'MobileOS': 'ETC',
            'MobileApp': 'BusanTourChat',
            '_type': 'json',
            'arrange': 'A'
        }
        
        print("=== TourAPI 갤러리 제목 확인 ===")
        
        response = requests.get(gallery_url, params=params, timeout=10)
        print(f"응답 상태코드: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if 'response' in data and 'body' in data['response']:
                    body = data['response']['body']
                    if 'items' in body and body['items']:
                        items = body['items']['item']
                        if not isinstance(items, list):
                            items = [items]
                        
                        print(f"갤러리 항목 수: {len(items)}")
                        print()
                        
                        for i, item in enumerate(items, 1):
                            title = item.get('galTitle', 'N/A')
                            location = item.get('galPhotographyLocation', 'N/A')
                            image_url = item.get('galWebImageUrl', 'N/A')
                            
                            print(f"{i}. 제목: {title}")
                            print(f"   촬영지: {location}")
                            print(f"   이미지 URL: {image_url[:50]}..." if len(image_url) > 50 else f"   이미지 URL: {image_url}")
                            print()
                        
                        return True
                    else:
                        print("갤러리에 사진이 없습니다.")
                        return False
                else:
                    print("응답 구조가 예상과 다릅니다.")
                    return False
            except Exception as json_error:
                print(f"JSON 파싱 오류: {json_error}")
                print(f"응답 내용 (처음 1000자): {response.text[:1000]}")
                return False
        else:
            print(f"API 요청 실패: {response.status_code}")
            print(f"응답 내용: {response.text}")
            return False
            
    except Exception as e:
        print(f"갤러리 확인 오류: {e}")
        return False

if __name__ == "__main__":
    check_gallery_titles()