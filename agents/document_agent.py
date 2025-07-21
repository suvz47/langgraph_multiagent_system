from typing import Dict
from db.vector_db import VectorDB
from memory.agentic_memory import AgenticMemory
from llm.groq_llm import GroqLLM

def document_node(state: Dict, vector_db: VectorDB, memory: AgenticMemory, llm: GroqLLM) -> Dict:
    documents = state.get('documents', [])
    rag_results = []
    llm_summaries = []
    for doc in documents:
        doc_id = doc.get('id', str(hash(str(doc))))
        content = doc.get('content', '')
        vector_db.add_document(doc_id, content, metadata=doc)
        memory.save('document_agent', doc)
        rag_results.append(f"Indexed doc {doc_id}")
        # Use LLM to summarize/extract info from document
        summary = llm.chat([
            {"role": "system", "content": "You are an expert insurance document analyst."},
            {"role": "user", "content": f"Summarize this document for claim processing: {content}"}
        ])
        llm_summaries.append({"doc_id": doc_id, "summary": summary})
    # RAG: retrieve relevant docs for claim
    claim_query = state.get('claim', {}).get('details', '')
    if claim_query:
        retrieval = vector_db.query(claim_query, n_results=2)
        state['rag_retrieval'] = retrieval
    state.setdefault('agent_messages', []).append('DocumentAgent: Processed documents with LLM and RAG.')
    state['rag_results'] = rag_results
    state['llm_summaries'] = llm_summaries
    return state 