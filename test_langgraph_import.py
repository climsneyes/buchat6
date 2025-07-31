#!/usr/bin/env python3
"""
LangGraph import 문제 디버깅 스크립트
"""

def test_langgraph_imports():
    """LangGraph 관련 라이브러리 import 테스트"""
    
    print("=== LangGraph Import 테스트 ===")
    
    # 1. langgraph.graph 테스트
    try:
        from langgraph.graph import StateGraph, END
        print("✅ langgraph.graph import 성공")
    except ImportError as e:
        print(f"❌ langgraph.graph import 실패: {e}")
    
    # 2. langchain_google_genai 테스트
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        print("✅ langchain_google_genai import 성공")
    except ImportError as e:
        print(f"❌ langchain_google_genai import 실패: {e}")
    
    # 3. langchain_core 테스트
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.runnables import RunnablePassthrough
        from langchain_core.output_parsers import StrOutputParser
        print("✅ langchain_core import 성공")
    except ImportError as e:
        print(f"❌ langchain_core import 실패: {e}")
    
    # 4. langchain.text_splitter 테스트
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        print("✅ langchain.text_splitter import 성공")
    except ImportError as e:
        print(f"❌ langchain.text_splitter import 실패: {e}")
    
    # 5. langchain_community.vectorstores 테스트
    try:
        from langchain_community.vectorstores import FAISS
        print("✅ langchain_community.vectorstores import 성공")
    except ImportError as e:
        print(f"❌ langchain_community.vectorstores import 실패: {e}")
    
    # 6. 전체 import 테스트
    try:
        from langgraph.graph import StateGraph, END
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        from langchain_core.prompts import ChatPromptTemplate
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain_core.runnables import RunnablePassthrough
        from langchain_core.output_parsers import StrOutputParser
        
        print("✅ 모든 LangGraph 관련 라이브러리 import 성공!")
        return True
        
    except ImportError as e:
        print(f"❌ 전체 import 실패: {e}")
        return False

def test_langgraph_availability():
    """rag_utils.py의 LANGGRAPH_AVAILABLE 플래그 테스트"""
    
    print("\n=== rag_utils.py LANGGRAPH_AVAILABLE 테스트 ===")
    
    try:
        # rag_utils 모듈 import
        import rag_utils
        
        # LANGGRAPH_AVAILABLE 변수 확인
        if hasattr(rag_utils, 'LANGGRAPH_AVAILABLE'):
            print(f"LANGGRAPH_AVAILABLE: {rag_utils.LANGGRAPH_AVAILABLE}")
            
            if rag_utils.LANGGRAPH_AVAILABLE:
                print("✅ LangGraph 사용 가능")
            else:
                print("❌ LangGraph 사용 불가능")
        else:
            print("❌ LANGGRAPH_AVAILABLE 변수가 없습니다")
            
    except Exception as e:
        print(f"❌ rag_utils import 실패: {e}")

def test_simple_langgraph_workflow():
    """간단한 LangGraph 워크플로우 테스트"""
    
    print("\n=== 간단한 LangGraph 워크플로우 테스트 ===")
    
    try:
        from langgraph.graph import StateGraph, END
        
        # 간단한 워크플로우 생성
        def simple_node(state):
            return {"result": f"처리된 결과: {state.get('input', '')}"}
        
        # 그래프 생성
        workflow = StateGraph(dict)
        workflow.add_node("simple_node", simple_node)
        workflow.set_entry_point("simple_node")
        workflow.add_edge("simple_node", END)
        
        # 컴파일
        compiled_workflow = workflow.compile()
        
        # 실행
        result = compiled_workflow.invoke({"input": "테스트 입력"})
        
        print(f"✅ LangGraph 워크플로우 실행 성공: {result}")
        return True
        
    except Exception as e:
        print(f"❌ LangGraph 워크플로우 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 1. Import 테스트
    import_success = test_langgraph_imports()
    
    # 2. rag_utils 테스트
    test_langgraph_availability()
    
    # 3. 워크플로우 테스트
    if import_success:
        test_simple_langgraph_workflow()
    
    print("\n=== 테스트 완료 ===") 