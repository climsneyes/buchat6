#!/usr/bin/env python3
"""
개선된 LangGraph RAG 시스템 테스트 스크립트
"""

import os
import sys
from rag_utils import answer_with_langgraph_rag, answer_with_rag
from config import GEMINI_API_KEY

def test_improved_langgraph_rag():
    """개선된 LangGraph RAG 시스템 테스트"""
    
    # API 키 확인
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        return
    
    print("=== 개선된 LangGraph RAG 시스템 테스트 ===")
    
    # 테스트 질문들 (다양한 유형)
    test_queries = [
        # 쓰레기 처리 관련 질문
        "해운대구에서 대형폐기물을 어떻게 버려야 하나요?",
        "부산진구 쓰레기 배출 방법 알려주세요",
        
        # 권리구제 관련 질문
        "외국인 근로자의 임금 체불 문제는 어떻게 해결하나요?",
        "근로계약서 작성 시 주의사항은?",
        
        # 맛집 관련 질문
        "부산에서 맛있는 해산물 맛집 추천해주세요",
        "서면 근처 맛집 알려주세요",
        
        # 일반 질문
        "한국의 의료보험 가입 방법은?",
        "다문화가족을 위한 교육 지원은 어떻게 받을 수 있나요?"
    ]
    
    # 벡터DB 로드
    try:
        import pickle
        vector_db_path = "다문화.pkl"
        
        if os.path.exists(vector_db_path):
            with open(vector_db_path, 'rb') as f:
                vector_db = pickle.load(f)
            print(f"✅ 벡터DB 로드 완료: {len(vector_db.documents)}개 문서")
        else:
            print(f"❌ 벡터DB 파일이 없습니다: {vector_db_path}")
            return
            
    except Exception as e:
        print(f"❌ 벡터DB 로드 실패: {e}")
        return
    
    # 각 질문에 대해 테스트
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"--- 테스트 {i}: {query} ---")
        print(f"{'='*50}")
        
        try:
            # LangGraph RAG 테스트
            print("🔄 개선된 LangGraph RAG 답변 생성 중...")
            langgraph_answer = answer_with_langgraph_rag(query, vector_db, GEMINI_API_KEY, "ko")
            print(f"✅ LangGraph RAG 답변:\n{langgraph_answer}")
            
            # 기본 RAG와 비교
            print("\n🔄 기본 RAG 답변 생성 중...")
            basic_answer = answer_with_rag(query, vector_db, GEMINI_API_KEY, "ko")
            print(f"✅ 기본 RAG 답변:\n{basic_answer}")
            
            # 답변 품질 비교
            print(f"\n📊 답변 품질 비교:")
            print(f"LangGraph RAG: {len(langgraph_answer)}자")
            print(f"기본 RAG: {len(basic_answer)}자")
            
            # 품질 점수 계산
            langgraph_score = calculate_answer_quality(langgraph_answer, query)
            basic_score = calculate_answer_quality(basic_answer, query)
            
            print(f"LangGraph RAG 품질 점수: {langgraph_score:.2f}")
            print(f"기본 RAG 품질 점수: {basic_score:.2f}")
            
            if langgraph_score > basic_score:
                print("🎉 LangGraph RAG가 더 좋은 답변을 생성했습니다!")
            elif basic_score > langgraph_score:
                print("⚠️ 기본 RAG가 더 좋은 답변을 생성했습니다.")
            else:
                print("🤝 두 시스템의 답변 품질이 비슷합니다.")
            
        except Exception as e:
            print(f"❌ 테스트 {i} 실패: {e}")
            import traceback
            traceback.print_exc()

def calculate_answer_quality(answer: str, query: str) -> float:
    """답변 품질을 계산하는 함수"""
    if not answer or len(answer) < 20:
        return 0.0
    
    # 품질 지표들
    quality_score = 0.0
    
    # 길이 점수 (적절한 길이)
    length_score = min(len(answer) / 300, 1.0)  # 300자 기준
    quality_score += length_score * 0.2
    
    # 키워드 매칭 점수
    query_keywords = set(query.lower().split())
    answer_keywords = set(answer.lower().split())
    keyword_overlap = len(query_keywords.intersection(answer_keywords)) / max(len(query_keywords), 1)
    quality_score += keyword_overlap * 0.4
    
    # 구체성 점수 (숫자, 구체적 정보 포함)
    specificity_score = 0.0
    if any(char.isdigit() for char in answer):
        specificity_score += 0.2
    if any(word in answer.lower() for word in ["전화", "연락처", "주소", "시간", "금액", "비용"]):
        specificity_score += 0.2
    if any(word in answer.lower() for word in ["방법", "절차", "단계", "순서"]):
        specificity_score += 0.2
    quality_score += specificity_score
    
    # 명확성 점수 (불명확한 표현이 적을수록 높음)
    clarity_score = 1.0
    unclear_phrases = ["모르겠습니다", "찾을 수 없습니다", "알 수 없습니다", "확인해보세요"]
    for phrase in unclear_phrases:
        if phrase in answer:
            clarity_score -= 0.3
    quality_score += max(clarity_score, 0) * 0.2
    
    return min(quality_score, 1.0)

def test_langgraph_features():
    """LangGraph 특별 기능 테스트"""
    print("\n=== LangGraph 특별 기능 테스트 ===")
    
    # 재검색 기능 테스트
    print("🔄 재검색 기능 테스트...")
    test_query = "부산에서 특별히 맛있는 음식점을 알려주세요"
    
    try:
        # 벡터DB 로드
        import pickle
        vector_db_path = "다문화.pkl"
        
        if os.path.exists(vector_db_path):
            with open(vector_db_path, 'rb') as f:
                vector_db = pickle.load(f)
            
            # LangGraph RAG 테스트
            answer = answer_with_langgraph_rag(test_query, vector_db, GEMINI_API_KEY, "ko")
            print(f"✅ 재검색 포함 답변:\n{answer}")
            
        else:
            print("❌ 벡터DB 파일이 없어 테스트를 건너뜁니다.")
            
    except Exception as e:
        print(f"❌ 재검색 기능 테스트 실패: {e}")

def test_langgraph_availability():
    """LangGraph 사용 가능 여부 테스트"""
    print("=== LangGraph 사용 가능 여부 테스트 ===")
    
    try:
        from langgraph.graph import StateGraph, END
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        from langchain_core.prompts import ChatPromptTemplate
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain_core.runnables import RunnablePassthrough
        from langchain_core.output_parsers import StrOutputParser
        
        print("✅ LangGraph 관련 라이브러리 모두 사용 가능")
        return True
        
    except ImportError as e:
        print(f"❌ LangGraph 라이브러리 누락: {e}")
        print("다음 명령어로 설치하세요:")
        print("pip install langgraph langchain-google-genai langchain-community")
        return False

if __name__ == "__main__":
    # LangGraph 사용 가능 여부 확인
    if test_langgraph_availability():
        # 개선된 LangGraph RAG 테스트 실행
        test_improved_langgraph_rag()
        
        # 특별 기능 테스트
        test_langgraph_features()
    else:
        print("LangGraph를 사용할 수 없어 테스트를 건너뜁니다.") 