#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
쓰레기 처리 기능 테스트 스크립트
"""
import os
import sys
import json

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_utils import is_waste_related_query, extract_district_from_query, get_district_selection_prompt

def test_waste_detection():
    """쓰레기 관련 질문 감지 테스트"""
    print("=== 쓰레기 관련 질문 감지 테스트 ===")
    
    test_queries = [
        "쓰레기 버리는 방법이 뭐야?",
        "중구에서 폐기물 처리하는 방법",
        "재활용품 배출 시간",
        "음식물쓰레기 어떻게 버려?",
        "대형폐기물 신고 방법",
        "일반적인 질문입니다",
        "한국 문화에 대해 알려주세요"
    ]
    
    for query in test_queries:
        is_waste = is_waste_related_query(query)
        district = extract_district_from_query(query)
        print(f"질문: '{query}'")
        print(f"  -> 쓰레기 관련: {is_waste}")
        print(f"  -> 구군명: {district}")
        print()

def test_json_loading():
    """JSON 파일 로딩 테스트"""
    print("=== JSON 파일 로딩 테스트 ===")
    
    json_path = "부산광역시_쓰레기처리정보.json"
    if os.path.exists(json_path):
        print(f"✅ JSON 파일 존재: {json_path}")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            waste_info = data.get("부산광역시_쓰레기처리정보", {})
            districts_info = waste_info.get("구군별_정보", {})
            
            print(f"✅ 총 구군 수: {len(districts_info)}")
            print(f"✅ 구군 목록: {list(districts_info.keys())[:3]}...")
            
            # 중구 정보 테스트
            jung_gu_info = districts_info.get("중구")
            if jung_gu_info:
                print(f"✅ 중구 정보 존재")
                print(f"  - 담당부서: {jung_gu_info.get('담당부서', 'N/A')}")
                print(f"  - 연락처: {jung_gu_info.get('연락처', 'N/A')}")
                print(f"  - 배출시간: {jung_gu_info.get('배출시간', 'N/A')}")
            else:
                print("❌ 중구 정보 없음")
                
        except Exception as e:
            print(f"❌ JSON 파일 로딩 오류: {e}")
    else:
        print(f"❌ JSON 파일 없음: {json_path}")

def test_district_selection_prompt():
    """구군 선택 프롬프트 테스트"""
    print("=== 구군 선택 프롬프트 테스트 ===")
    
    languages = ["ko", "en", "vi", "ja"]
    for lang in languages:
        prompt = get_district_selection_prompt(lang)
        print(f"{lang}: {prompt[:50]}...")
        print()

if __name__ == "__main__":
    test_waste_detection()
    test_json_loading()
    test_district_selection_prompt()