#!/usr/bin/env python3
"""
개선된 RAG 시스템 테스트 스크립트
"""

import os
import pickle
from config import GEMINI_API_KEY
from rag_utils import answer_with_langgraph_rag, answer_with_rag

def test_improved_rag():
    """개선된 RAG 시스템 테스트"""
    
    print("=== 개선된 RAG 시스템 테스트 ===")
    
    # API 키 확인
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        return
    
    print(f"✅ API Key 확인됨: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}")
    
    # 벡터DB 로드
    vector_db_path = "다문화.pkl"
    
    if not os.path.exists(vector_db_path):
        print(f"❌ 벡터DB 파일이 없습니다: {vector_db_path}")
        return
    
    try:
        print(f"📖 벡터DB 로드 중: {vector_db_path}")
        with open(vector_db_path, 'rb') as f:
            vector_db = pickle.load(f)
        print(f"✅ 벡터DB 로드 완료: {len(vector_db.documents)}개 문서")
        
    except Exception as e:
        print(f"❌ 벡터DB 로드 실패: {e}")
        return
    
    # 테스트 시나리오들
    test_scenarios = [
        {
            "name": "쓰레기 처리 질문 후 구군명 입력",
            "queries": [
                "쓰레기 버리는 방법은요?",
                "동구입니다"
            ]
        },
        {
            "name": "의료 정보 질문 후 구군명 입력",
            "queries": [
                "병원 정보 알려주세요",
                "해운대구입니다"
            ]
        },
        {
            "name": "교육 정보 질문 후 구군명 입력",
            "queries": [
                "학교 정보 알려주세요",
                "부산진구입니다"
            ]
        },
        {
            "name": "일반 생활 정보 질문",
            "queries": [
                "부산에서 맛있는 음식점 추천해주세요"
            ]
        },
        {
            "name": "직접 구군명 입력",
            "queries": [
                "동구"
            ]
        }
    ]
    
    # 각 시나리오 테스트
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"📋 시나리오 {i}: {scenario['name']}")
        print(f"{'='*60}")
        
        for j, query in enumerate(scenario['queries'], 1):
            print(f"\n--- 질문 {j}: {query} ---")
            
            # LangGraph RAG 테스트
            print("\n🔄 LangGraph RAG 답변:")
            try:
                langgraph_answer = answer_with_langgraph_rag(query, vector_db, GEMINI_API_KEY, "ko")
                print(f"✅ 답변: {langgraph_answer}")
            except Exception as e:
                print(f"❌ 오류: {e}")
            
            # 기본 RAG 테스트
            print("\n🔄 기본 RAG 답변:")
            try:
                basic_answer = answer_with_rag(query, vector_db, GEMINI_API_KEY, "ko")
                print(f"✅ 답변: {basic_answer}")
            except Exception as e:
                print(f"❌ 오류: {e}")
            
            print("\n" + "-"*40)

def test_context_awareness():
    """문맥 인식 기능 테스트"""
    
    print("\n=== 문맥 인식 기능 테스트 ===")
    
    # API 키 확인
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        return
    
    # 벡터DB 로드
    vector_db_path = "다문화.pkl"
    
    if not os.path.exists(vector_db_path):
        print(f"❌ 벡터DB 파일이 없습니다: {vector_db_path}")
        return
    
    try:
        with open(vector_db_path, 'rb') as f:
            vector_db = pickle.load(f)
        print(f"✅ 벡터DB 로드 완료: {len(vector_db.documents)}개 문서")
        
    except Exception as e:
        print(f"❌ 벡터DB 로드 실패: {e}")
        return
    
    # 문맥 인식 테스트
    context_tests = [
        {
            "context": "쓰레기 처리",
            "district": "동구",
            "expected": "쓰레기 배출"
        },
        {
            "context": "의료 정보",
            "district": "해운대구",
            "expected": "의료"
        },
        {
            "context": "교육 정보",
            "district": "부산진구",
            "expected": "교육"
        }
    ]
    
    for test in context_tests:
        print(f"\n🧪 테스트: {test['context']} + {test['district']}")
        
        # 시뮬레이션된 대화
        print("🔄 시뮬레이션된 대화:")
        print(f"사용자: {test['context']} 알려주세요")
        print(f"시스템: 부산광역시 어느 구에서 {test['context']}를 알고 싶으신가요?")
        print(f"사용자: {test['district']}입니다")
        
        # LangGraph RAG 테스트
        try:
            answer = answer_with_langgraph_rag(f"{test['district']}입니다", vector_db, GEMINI_API_KEY, "ko")
            print(f"✅ LangGraph 답변: {answer[:100]}...")
            
            # 예상 키워드 포함 여부 확인
            if test['expected'] in answer:
                print(f"✅ 예상 키워드 '{test['expected']}' 포함됨")
            else:
                print(f"⚠️ 예상 키워드 '{test['expected']}' 포함되지 않음")
                
        except Exception as e:
            print(f"❌ 오류: {e}")

if __name__ == "__main__":
    # 기본 테스트
    test_improved_rag()
    
    # 문맥 인식 테스트
    test_context_awareness()
    
    print("\n=== 테스트 완료 ===") 