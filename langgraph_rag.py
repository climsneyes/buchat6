import os
import json
import pickle
import numpy as np
from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import google.generativeai as genai

class LangGraphRAG:
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        
        # LLM 설정
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            temperature=0.1,
            max_output_tokens=2000
        )
        
        # 임베딩 모델 설정
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=gemini_api_key
        )
        
        # 벡터스토어 초기화
        self.vector_store = None
        self.conversation_memory = []
        
    def load_vector_store(self, vector_db_path: str):
        """기존 벡터DB를 LangChain 벡터스토어로 변환"""
        try:
            with open(vector_db_path, 'rb') as f:
                vector_db = pickle.load(f)
            
            # 문서와 임베딩 추출
            documents = []
            embeddings_list = []
            
            for doc in vector_db.documents:
                if isinstance(doc, dict) and 'page_content' in doc:
                    documents.append(doc['page_content'])
                    if hasattr(vector_db, 'doc_embeddings') and vector_db.doc_embeddings:
                        # 기존 임베딩이 있으면 사용
                        doc_idx = vector_db.documents.index(doc)
                        if doc_idx < len(vector_db.doc_embeddings):
                            embeddings_list.append(vector_db.doc_embeddings[doc_idx])
            
            # FAISS 벡터스토어 생성
            if embeddings_list:
                self.vector_store = FAISS.from_embeddings(
                    embeddings_list, 
                    documents, 
                    self.embeddings
                )
            else:
                # 임베딩이 없으면 새로 생성
                self.vector_store = FAISS.from_texts(
                    documents, 
                    self.embeddings
                )
            
            print(f"벡터스토어 로드 완료: {len(documents)}개 문서")
            return True
            
        except Exception as e:
            print(f"벡터스토어 로드 실패: {e}")
            return False
    
    def create_rag_graph(self, target_lang: str = "ko"):
        """LangGraph 기반 RAG 파이프라인 생성"""
        
        # 1. 검색 노드
        def search_documents(state: Dict[str, Any]) -> Dict[str, Any]:
            """관련 문서 검색"""
            query = state["query"]
            k = state.get("k", 5)
            
            if self.vector_store:
                docs = self.vector_store.similarity_search(query, k=k)
                context = "\n\n".join([doc.page_content for doc in docs])
                return {"context": context, "documents": docs}
            else:
                return {"context": "", "documents": []}
        
        # 2. 질문 분석 노드
        def analyze_query(state: Dict[str, Any]) -> Dict[str, Any]:
            """질문 유형 분석 및 검색 전략 결정"""
            query = state["query"]
            
            # 질문 유형 분석
            query_type = "general"
            if any(keyword in query.lower() for keyword in ["쓰레기", "폐기물", "배출"]):
                query_type = "waste_management"
            elif any(keyword in query.lower() for keyword in ["맛집", "음식", "식당"]):
                query_type = "restaurant"
            elif any(keyword in query.lower() for keyword in ["권리", "법률", "근로자"]):
                query_type = "worker_rights"
            
            # 검색 파라미터 조정
            k = 3 if query_type == "waste_management" else 5
            
            return {
                "query_type": query_type,
                "k": k,
                "search_strategy": f"enhanced_search_{query_type}"
            }
        
        # 3. 컨텍스트 강화 노드
        def enhance_context(state: Dict[str, Any]) -> Dict[str, Any]:
            """컨텍스트를 강화하고 관련성 높은 정보만 필터링"""
            context = state.get("context", "")
            query = state["query"]
            query_type = state.get("query_type", "general")
            
            # 컨텍스트가 너무 길면 요약
            if len(context) > 3000:
                # 간단한 요약 로직
                sentences = context.split('.')
                relevant_sentences = []
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in query.lower().split()):
                        relevant_sentences.append(sentence)
                
                if relevant_sentences:
                    context = '. '.join(relevant_sentences[:10])  # 최대 10문장
                else:
                    context = '. '.join(sentences[:5])  # 처음 5문장
            
            return {"enhanced_context": context}
        
        # 4. 답변 생성 노드
        def generate_answer(state: Dict[str, Any]) -> Dict[str, Any]:
            """최종 답변 생성"""
            query = state["query"]
            context = state.get("enhanced_context", "")
            query_type = state.get("query_type", "general")
            
            # 언어별 프롬프트 템플릿
            templates = {
                "ko": """다음은 참고 정보입니다. 정확하고 도움이 되는 답변을 한국어로 해주세요.

[참고 정보]
{context}

질문: {query}

답변: 참고 정보를 바탕으로 한국어로 답변해주세요. 구체적이고 실용적인 정보를 제공해주세요.""",
                "en": """Here is reference information. Please provide accurate and helpful answers in English.

[Reference Information]
{context}

Question: {query}

Answer: Please provide a detailed answer in English based on the reference information. Include specific and practical information.""",
                "ja": """以下は参考情報です。正確で役立つ回答を日本語でお願いします。

[参考情報]
{context}

質問: {query}

回答: 参考情報に基づいて日本語で回答してください。具体的で実用的な情報を提供してください。""",
                "zh": """以下是参考信息。请用中文提供准确有用的答案。

[参考信息]
{context}

问题: {query}

答案: 请基于参考信息用中文提供详细答案。包含具体实用的信息。""",
                "vi": """Đây là thông tin tham khảo. Vui lòng cung cấp câu trả lời chính xác và hữu ích bằng tiếng Việt.

[Thông tin tham khảo]
{context}

Câu hỏi: {query}

Trả lời: Vui lòng cung cấp câu trả lời chi tiết bằng tiếng Việt dựa trên thông tin tham khảo. Bao gồm thông tin cụ thể và thực tế."""
            }
            
            template = templates.get(target_lang, templates["ko"])
            prompt = ChatPromptTemplate.from_template(template)
            
            # 체인 구성
            chain = prompt | self.llm | StrOutputParser()
            
            # 답변 생성
            try:
                answer = chain.invoke({
                    "context": context,
                    "query": query
                })
                
                # 답변 후처리
                answer = self.post_process_answer(answer, query_type)
                
                return {"answer": answer}
            except Exception as e:
                print(f"답변 생성 오류: {e}")
                return {"answer": "죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다."}
        
        # 5. 답변 후처리
        def post_process_answer(self, answer: str, query_type: str) -> str:
            """답변 품질 개선 및 후처리"""
            # 마크다운 정리
            answer = answer.replace("**", "").replace("*", "")
            
            # 불필요한 문구 제거
            answer = answer.replace("참고 정보를 바탕으로", "").replace("Based on the reference information", "")
            
            # 답변이 너무 짧으면 보완
            if len(answer) < 50:
                answer += "\n\n더 자세한 정보가 필요하시면 추가 질문해 주세요."
            
            return answer.strip()
        
        # 6. 대화 메모리 업데이트
        def update_memory(state: Dict[str, Any]) -> Dict[str, Any]:
            """대화 히스토리 업데이트"""
            query = state["query"]
            answer = state.get("answer", "")
            
            # 대화 히스토리에 추가
            self.conversation_memory.append({
                "query": query,
                "answer": answer,
                "timestamp": len(self.conversation_memory)
            })
            
            # 메모리 크기 제한 (최근 10개 대화만 유지)
            if len(self.conversation_memory) > 10:
                self.conversation_memory = self.conversation_memory[-10:]
            
            return {"memory_updated": True}
        
        # 그래프 구성
        workflow = StateGraph(Dict[str, Any])
        
        # 노드 추가
        workflow.add_node("analyze_query", analyze_query)
        workflow.add_node("search_documents", search_documents)
        workflow.add_node("enhance_context", enhance_context)
        workflow.add_node("generate_answer", generate_answer)
        workflow.add_node("update_memory", update_memory)
        
        # 엣지 연결
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "search_documents")
        workflow.add_edge("search_documents", "enhance_context")
        workflow.add_edge("enhance_context", "generate_answer")
        workflow.add_edge("generate_answer", "update_memory")
        workflow.add_edge("update_memory", END)
        
        # 그래프 컴파일
        self.rag_graph = workflow.compile()
        
        return self.rag_graph
    
    def answer_query(self, query: str, target_lang: str = "ko") -> str:
        """질문에 대한 답변 생성"""
        try:
            # 그래프가 없으면 생성
            if not hasattr(self, 'rag_graph'):
                self.create_rag_graph(target_lang)
            
            # 초기 상태 설정
            initial_state = {
                "query": query,
                "target_lang": target_lang
            }
            
            # 그래프 실행
            result = self.rag_graph.invoke(initial_state)
            
            return result.get("answer", "답변을 생성할 수 없습니다.")
            
        except Exception as e:
            print(f"LangGraph RAG 오류: {e}")
            return f"죄송합니다. 오류가 발생했습니다: {str(e)}"
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """대화 히스토리 반환"""
        return self.conversation_memory.copy()

# 다문화가족 전용 RAG 클래스
class MulticulturalFamilyRAG(LangGraphRAG):
    def __init__(self, gemini_api_key: str):
        super().__init__(gemini_api_key)
        self.category = "multicultural_family"
    
    def create_rag_graph(self, target_lang: str = "ko"):
        """다문화가족 전용 RAG 그래프"""
        super().create_rag_graph(target_lang)
        
        # 다문화가족 전용 프롬프트 템플릿
        multicultural_templates = {
            "ko": """다문화가족을 위한 한국생활 안내 정보입니다. 따뜻하고 이해하기 쉬운 답변을 한국어로 해주세요.

[참고 정보]
{context}

질문: {query}

답변: 다문화가족의 입장에서 이해하기 쉽게 설명해주세요. 실용적인 정보와 함께 문화적 차이점도 고려해서 답변해주세요.""",
            "en": """This is Korean life guidance information for multicultural families. Please provide warm and easy-to-understand answers in English.

[Reference Information]
{context}

Question: {query}

Answer: Please explain in a way that's easy for multicultural families to understand. Provide practical information while considering cultural differences.""",
            "vi": """Đây là thông tin hướng dẫn cuộc sống Hàn Quốc cho gia đình đa văn hóa. Vui lòng cung cấp câu trả lời ấm áp và dễ hiểu bằng tiếng Việt.

[Thông tin tham khảo]
{context}

Câu hỏi: {query}

Trả lời: Vui lòng giải thích theo cách dễ hiểu cho gia đình đa văn hóa. Cung cấp thông tin thực tế đồng thời xem xét sự khác biệt văn hóa."""
        }
        
        # 템플릿 업데이트
        self.multicultural_templates = multicultural_templates
        return self.rag_graph

# 외국인 근로자 전용 RAG 클래스
class ForeignWorkerRAG(LangGraphRAG):
    def __init__(self, gemini_api_key: str):
        super().__init__(gemini_api_key)
        self.category = "foreign_worker"
    
    def create_rag_graph(self, target_lang: str = "ko"):
        """외국인 근로자 전용 RAG 그래프"""
        super().create_rag_graph(target_lang)
        
        # 외국인 근로자 전용 프롬프트 템플릿
        worker_templates = {
            "ko": """외국인 근로자의 권리구제 정보입니다. 명확하고 실용적인 답변을 한국어로 해주세요.

[참고 정보]
{context}

질문: {query}

답변: 외국인 근로자의 권리와 법적 보호에 대해 구체적으로 설명해주세요. 실제 도움이 되는 정보를 제공해주세요.""",
            "en": """This is information about rights protection for foreign workers. Please provide clear and practical answers in English.

[Reference Information]
{context}

Question: {query}

Answer: Please explain specifically about foreign workers' rights and legal protection. Provide information that is actually helpful.""",
            "vi": """Đây là thông tin về bảo vệ quyền lợi cho lao động nước ngoài. Vui lòng cung cấp câu trả lời rõ ràng và thực tế bằng tiếng Việt.

[Thông tin tham khảo]
{context}

Câu hỏi: {query}

Trả lời: Vui lòng giải thích cụ thể về quyền lợi và bảo vệ pháp lý của lao động nước ngoài. Cung cấp thông tin thực sự hữu ích."""
        }
        
        # 템플릿 업데이트
        self.worker_templates = worker_templates
        return self.rag_graph 