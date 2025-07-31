#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from urllib.parse import quote

# TourAPI 설정
TOUR_API_KEY = "rO5VJPog5TScnjUgCqneFaXfoep3fCsyR7VgL7dlQ1Ae99E/n3+ch8zmym+a1SIwylUd6Gj9L4E7B8txymXqMQ=="
TOUR_API_BASE_URL = "http://apis.data.go.kr/B551011/KorService1"

def test_tour_api_search(keyword):
    """TourAPI 키워드 검색 테스트"""
    try:
        search_url = f"{TOUR_API_BASE_URL}/searchKeyword1"
        params = {
            'serviceKey': TOUR_API_KEY,
            'numOfRows': 5,
            'pageNo': 1,
            'MobileOS': 'ETC',
            'MobileApp': 'BusanTourChat',
            'keyword': keyword,
            '_type': 'json',
            'listYN': 'Y',
            'arrange': 'A'
        }
        
        print(f"[검색] '{keyword}' 검색 중...")
        print(f"요청 URL: {search_url}")
        print(f"파라미터: {params}")
        
        response = requests.get(search_url, params=params, timeout=10)
        print(f"응답 상태코드: {response.status_code}")
        
        if response.status_code == 200:
            print(f"응답 내용 (처음 500자): {response.text[:500]}")
            try:
                data = response.json()
                print(f"응답 데이터 구조:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception as json_error:
                print(f"JSON 파싱 오류: {json_error}")
                print(f"전체 응답 내용: {response.text}")
                return
            
            if 'response' in data and 'body' in data['response']:
                body = data['response']['body']
                if 'items' in body and body['items']:
                    items = body['items']['item']
                    if not isinstance(items, list):
                        items = [items]
                    
                    print(f"\n[성공] 검색 결과 {len(items)}개:")
                    for i, item in enumerate(items, 1):
                        print(f"{i}. {item.get('title', 'N/A')} (ID: {item.get('contentid', 'N/A')})")
                        print(f"   주소: {item.get('addr1', 'N/A')}")
                        if item.get('firstimage'):
                            print(f"   대표이미지: {item.get('firstimage')}")
                        print()
                    
                    # 첫 번째 항목의 상세 이미지 조회
                    if items:
                        first_contentid = items[0].get('contentid')
                        if first_contentid:
                            test_detail_images(first_contentid)
                else:
                    print("[실패] 검색 결과가 없습니다.")
            else:
                print("[실패] 응답 구조가 예상과 다릅니다.")
        else:
            print(f"[실패] API 요청 실패: {response.status_code}")
            print(f"응답 내용: {response.text}")
            
    except Exception as e:
        print(f"[오류] 오류 발생: {e}")

def test_detail_images(contentid):
    """상세 이미지 조회 테스트"""
    try:
        detail_url = f"{TOUR_API_BASE_URL}/detailImage1"
        params = {
            'serviceKey': TOUR_API_KEY,
            'contentId': contentid,
            'MobileOS': 'ETC',
            'MobileApp': 'BusanTourChat',
            '_type': 'json',
            'imageYN': 'Y',
            'subImageYN': 'Y',
            'numOfRows': 10
        }
        
        print(f"[이미지] 상세 이미지 조회 중... (ContentID: {contentid})")
        
        response = requests.get(detail_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'response' in data and 'body' in data['response'] and 'items' in data['response']['body']:
                body = data['response']['body']
                if body['items']:
                    items = body['items']['item']
                    if not isinstance(items, list):
                        items = [items]
                    
                    print(f"[성공] 상세 이미지 {len(items)}개:")
                    for i, item in enumerate(items, 1):
                        print(f"{i}. {item.get('originimgurl', 'N/A')}")
                        print(f"   설명: {item.get('imgname', 'N/A')}")
                        print()
                else:
                    print("[실패] 상세 이미지가 없습니다.")
            else:
                print("[실패] 상세 이미지 응답 구조가 예상과 다릅니다.")
        else:
            print(f"[실패] 상세 이미지 API 요청 실패: {response.status_code}")
            
    except Exception as e:
        print(f"[오류] 상세 이미지 조회 오류: {e}")

if __name__ == "__main__":
    print("=== TourAPI 테스트 시작 ===")
    
    # 부산 관광지들 테스트
    test_keywords = ["해운대", "범어사", "감천문화마을", "광안리"]
    
    for keyword in test_keywords:
        print(f"\n{'='*50}")
        test_tour_api_search(keyword)
        print(f"{'='*50}")
    
    print("\n=== TourAPI 테스트 완료 ===")