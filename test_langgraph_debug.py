#!/usr/bin/env python3
"""
LangGraph RAG 시스템 실제 동작 테스트
"""

import os
import pickle
from config import GEMINI_API_KEY
from rag_utils import answer_with_langgraph_rag, answer_with_rag

def test_langgraph_rag_actual():
    """실제 LangGraph RAG 시스템 테스트"""
    
    print("=== LangGraph RAG 실제 동작 테스트 ===")
    
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
    
    # 테스트 질문
    test_query = "쓰레기 버리는 방법은요?"
    print(f"\n🧪 테스트 질문: {test_query}")
    
    # LangGraph RAG 테스트
    print("\n" + "="*50)
    print("🔄 LangGraph RAG 테스트")
    print("="*50)
    
    try:
        langgraph_answer = answer_with_langgraph_rag(test_query, vector_db, GEMINI_API_KEY, "ko")
        print(f"\n✅ LangGraph RAG 답변:\n{langgraph_answer}")
        
    except Exception as e:
        print(f"❌ LangGraph RAG 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 기본 RAG와 비교
    print("\n" + "="*50)
    print("🔄 기본 RAG 테스트")
    print("="*50)
    
    try:
        basic_answer = answer_with_rag(test_query, vector_db, GEMINI_API_KEY, "ko")
        print(f"\n✅ 기본 RAG 답변:\n{basic_answer}")
        
    except Exception as e:
        print(f"❌ 기본 RAG 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_langgraph_rag_actual() 