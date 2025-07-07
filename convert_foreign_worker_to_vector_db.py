import chromadb
import pickle
import os
from create_foreign_worker_db import OpenAIEmbeddingFunction
from rag_utils import OpenAIEmbeddings, SimpleVectorDB

def convert_foreign_worker_chromadb_to_vector_db():
    """외국인 근로자 ChromaDB를 기존 vector_db 형식으로 변환"""
    
    try:
        # ChromaDB에서 데이터 가져오기
        db_name = "foreign_worker_rights_guide_openai"
        persist_directory = "./chroma_db"
        chroma_client = chromadb.PersistentClient(path=persist_directory)
        collection = chroma_client.get_collection(name=db_name)
        
        # 모든 문서 가져오기
        results = collection.get()
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        
        print(f"ChromaDB에서 {len(documents)}개의 문서를 가져왔습니다.")
        
        # vector_db 형식으로 변환
        vector_db_documents = []
        for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
            vector_db_documents.append({
                'page_content': doc,
                'metadata': metadata or {},
                'source': f"foreign_worker_{i}"
            })
        
        # OpenAI 임베딩 생성
        from config import OPENAI_API_KEY
        embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
        
        # 문서 임베딩 생성
        doc_texts = [doc['page_content'] for doc in vector_db_documents]
        doc_embeddings = embeddings.embed_documents(doc_texts)
        
        # SimpleVectorDB 생성
        vector_db = SimpleVectorDB(vector_db_documents, embeddings, doc_embeddings)
        
        # 파일로 저장
        with open("vector_db_foreign_worker.pkl", "wb") as f:
            pickle.dump(vector_db, f)
        
        print(f"외국인 근로자 vector_db 저장 완료: vector_db_foreign_worker.pkl")
        print(f"총 문서 수: {len(vector_db_documents)}")
        
        return vector_db
        
    except Exception as e:
        print(f"변환 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    vector_db = convert_foreign_worker_chromadb_to_vector_db()
    if vector_db:
        print("✅ 변환 완료!")
    else:
        print("❌ 변환 실패!") 