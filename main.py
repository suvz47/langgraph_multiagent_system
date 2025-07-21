from typing import TypedDict, Optional, List, Dict, Any
import langgraph
from langgraph.graph import StateGraph, END, START
from agents.intake_agent import intake_node
from agents.document_agent import document_node
from agents.policy_agent import policy_node
from agents.scenario_agents import auto_scenario_node, health_scenario_node, property_scenario_node
from agents.coordinator_agent import coordinator_router_node, coordinator_router_edge
from db.vector_db import VectorDB
from memory.agentic_memory import AgenticMemory
from llm.groq_llm import GroqLLM
from db.session import init_db, SessionLocal
from db.models import Claim, Document
from dotenv import load_dotenv
import uuid
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
from PyPDF2 import PdfReader
import os
load_dotenv()

class ClaimState(TypedDict, total=False):
    claim: dict
    documents: List[dict]
    policy: dict
    scenario: str
    agent_messages: List[str]
    memory: Dict[str, Any]
    rag_results: List[str]
    llm_summaries: List[dict]
    rag_retrieval: Any
    policy_llm_summary: str
    result: Any
    needs_more_docs: bool
    loop_count: int

# --- Workflow runner ---
def run_claim_workflow(claim, documents):
    vector_db = VectorDB()
    memory = AgenticMemory()
    groq_llm = GroqLLM()

    def document_node_wrapped(state):
        return document_node(state, vector_db, memory, groq_llm)
    def policy_node_wrapped(state):
        return policy_node(state, groq_llm)
    def auto_node_wrapped(state):
        return auto_scenario_node(state, groq_llm)
    def health_node_wrapped(state):
        return health_scenario_node(state, groq_llm)
    def property_node_wrapped(state):
        return property_scenario_node(state, groq_llm)

    workflow = StateGraph(ClaimState)
    workflow.add_node("intake_node", intake_node)
    workflow.add_node("document_node", document_node_wrapped)
    workflow.add_node("policy_node", policy_node_wrapped)
    workflow.add_node("coordinator_router_node", coordinator_router_node)
    workflow.add_node("auto_scenario_node", auto_node_wrapped)
    workflow.add_node("health_scenario_node", health_node_wrapped)
    workflow.add_node("property_scenario_node", property_node_wrapped)

    workflow.add_edge(START, "intake_node")
    workflow.add_edge("intake_node", "document_node")
    workflow.add_edge("document_node", "policy_node")
    workflow.add_edge("policy_node", "coordinator_router_node")
    workflow.add_conditional_edges(
        "coordinator_router_node",
        coordinator_router_edge,
        {
            "auto_scenario_node": "auto_scenario_node",
            "health_scenario_node": "health_scenario_node",
            "property_scenario_node": "property_scenario_node",
            "end": END
        }
    )
    workflow.add_edge("auto_scenario_node", END)
    workflow.add_edge("health_scenario_node", END)
    workflow.add_edge("property_scenario_node", END)

    def loop_edge(state):
        state['loop_count'] = state.get('loop_count', 0) + 1
        if state['loop_count'] > 2:
            state['needs_more_docs'] = False
        if state.get('needs_more_docs'):
            return "document_node"
        return END
    workflow.add_conditional_edges("auto_scenario_node", loop_edge, {"document_node": "document_node", END: END})
    workflow.add_conditional_edges("health_scenario_node", loop_edge, {"document_node": "document_node", END: END})
    workflow.add_conditional_edges("property_scenario_node", loop_edge, {"document_node": "document_node", END: END})

    app = workflow.compile()
    state = ClaimState(claim=claim, documents=documents, loop_count=0)
    result = app.invoke(state)
    return result

# --- FastAPI server ---
app = FastAPI()

class ClaimRequest(BaseModel):
    claim: dict
    documents: list

class UploadDocumentRequest(BaseModel):
    claim_id: str
    document: dict

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/submit_claim")
def submit_claim(req: ClaimRequest):
    session = SessionLocal()
    claim_id = str(uuid.uuid4())
    claim_data = req.claim
    claim_data["claim_id"] = claim_id
    documents = req.documents
    db_claim = Claim(claim_id=claim_id, type=claim_data.get("type"), details=claim_data.get("details"), policy_id=None)
    session.add(db_claim)
    session.commit()
    for doc in documents:
        db_doc = Document(doc_id=doc.get("id", str(uuid.uuid4())), content=doc.get("content", ""), claim_id=db_claim.id)
        session.add(db_doc)
    session.commit()
    result = run_claim_workflow(claim_data, documents)
    session.close()
    return {"claim_id": claim_id, "result": result}

@app.post("/upload_document")
def upload_document(req: UploadDocumentRequest):
    session = SessionLocal()
    claim_id = req.claim_id
    doc = req.document
    db_claim = session.query(Claim).filter_by(claim_id=claim_id).first()
    if not db_claim:
        session.close()
        return {"error": "Claim not found"}
    db_doc = Document(doc_id=doc.get("id", str(uuid.uuid4())), content=doc.get("content", ""), claim_id=db_claim.id)
    session.add(db_doc)
    session.commit()
    session.close()
    return {"status": "Document uploaded"}

@app.post("/upload_policy_pdf")
def upload_policy_pdf(claim_id: str):
    session = SessionLocal()
    db_claim = session.query(Claim).filter_by(claim_id=claim_id).first()
    if not db_claim:
        session.close()
        return {"error": "Claim not found"}
    pdf_path = os.path.join("data", "policy.pdf")
    if not os.path.exists(pdf_path):
        session.close()
        return {"error": "policy.pdf not found in ./data"}
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    doc_id = f"policy_pdf_{claim_id}"
    db_doc = Document(doc_id=doc_id, content=text, claim_id=db_claim.id)
    session.add(db_doc)
    session.commit()
    session.close()
    return {"status": "Policy PDF uploaded as document", "doc_id": doc_id}

@app.get("/get_claim_status")
def get_claim_status(claim_id: str):
    session = SessionLocal()
    db_claim = session.query(Claim).filter_by(claim_id=claim_id).first()
    if not db_claim:
        session.close()
        return {"error": "Claim not found"}
    docs = session.query(Document).filter_by(claim_id=db_claim.id).all()
    doc_list = [{"id": d.doc_id, "content": d.content} for d in docs]
    result = run_claim_workflow({"claim_id": claim_id, "type": db_claim.type, "details": db_claim.details, "policy_id": db_claim.policy_id}, doc_list)
    session.close()
    return {"claim_id": claim_id, "result": result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 