[▶️ Demo Video Walkthrough](https://youtu.be/smPBF8ccoFw)

# 🚀 LangGraph Multi-Agent Insurance System

Welcome to a next-generation insurance claim processing system, powered by [LangGraph](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/) and [Groq LLM](https://console.groq.com/docs/overview)!

---

## 🏗️ Architecture Overview

### System Workflow

```
+--------+      +-------------+      +---------------+      +--------------+      +-------------------+
| Start  | ---> | Intake 📝    | ---> | Document 📄    | ---> | Policy 📑     | ---> | Coordinator 🤖     |
+--------+      +-------------+      +---------------+      +--------------+      +-------------------+
                                                                                          |
                                                                                          v
                                                                                 +-------------------+
                                                                                 | Scenario Agent    |
                                                                                 |  🚗  🏥  🏠         |
                                                                                 +-------------------+
                                                                                          |
                                                                                          v
                                                                                      +-------+
                                                                                      | End 🏁 |
                                                                                      +-------+
```
- **Intake Agent 📝**: Receives and triages new claims.
- **Document Agent 📄**: Handles document extraction, storage, RAG (vector DB), and memory. **Auto-detects and uses all uploaded documents, including policy PDFs.**
- **Policy Agent 📑**: Looks up and reasons over policy data.
- **Coordinator 🤖**: Routes claims to the correct scenario agent.
- **Scenario Agents 🚗🏥🏠**: Specialized for auto, health, and property claims.

---

### 📦 Data & Agent Relationships

```
CLAIM -- has --> DOCUMENT
CLAIM -- references --> POLICY
CLAIM -- handled_by --> SCENARIO
DOCUMENT -- indexed_in --> VECTOR_DB
AGENTIC_MEMORY -- stores --> DOCUMENT
COORDINATOR -- routes_to --> SCENARIO
SCENARIO -- is --> AGENT
AGENT -- logs --> MESSAGE

Entities:
- CLAIM: claim_id, type, details, policy_id
- DOCUMENT: id, content
- POLICY: policy_id, coverage, status
- SCENARIO: name
- AGENTIC_MEMORY: agent_name, info
- VECTOR_DB: doc_id, content
- AGENT: name
- MESSAGE: content
```

---

## 📄 Document Storage & Usage

- **Storage:**
  - Documents are stored in two places:
    - **Relational DB (SQLite):** For claim/document metadata and persistence.
    - **Chroma Vector DB:** For semantic search and retrieval-augmented generation (RAG).
- **Usage in Workflow:**
  - When a claim is submitted, documents are saved to both the SQL DB and indexed in Chroma.
  - The Document Agent uses the LLM to analyze and summarize each document.
  - The Document Agent also performs RAG: it retrieves relevant documents from Chroma based on the claim details and provides them to downstream agents.
  - Scenario and Policy Agents use these summaries and retrievals for decision-making.
  - **Policy PDFs uploaded via `/upload_policy_pdf` are automatically detected and used in all workflow runs for the claim.**
- **API:**
  - You can upload additional documents to a claim using the `/upload_document` endpoint.
  - All documents for a claim are used in every workflow run (e.g., when checking claim status).

---

## ⚙️ API Usage: Step-by-Step

### 1. **Submit a New Claim**
```bash
curl -X POST http://localhost:8000/submit_claim \
  -H "Content-Type: application/json" \
  -d '{"claim": {"type": "auto", "details": "Accident on 5th Ave.", "policy_id": "P456"}, "documents": []}'
```
- **Response:**
  ```json
  { "claim_id": "YOUR_CLAIM_ID", "result": { ... } }
  ```
  Save the `claim_id` for the next steps.

### 2. **Upload the Policy PDF as a Document**
```bash
curl -X POST "http://localhost:8000/upload_policy_pdf?claim_id=YOUR_CLAIM_ID"
```
- This will extract text from `./data/policy.pdf` and attach it to your claim as a document.
- **Response:**
  ```json
  { "status": "Policy PDF uploaded as document", "doc_id": "policy_pdf_YOUR_CLAIM_ID" }
  ```

### 3. **(Optional) Upload Additional Documents**
```bash
curl -X POST http://localhost:8000/upload_document \
  -H "Content-Type: application/json" \
  -d '{"claim_id": "YOUR_CLAIM_ID", "document": {"id": "D2", "content": "Police report."}}'
```

### 4. **Get Claim Status (and See Results)**
```bash
curl "http://localhost:8000/get_claim_status?claim_id=YOUR_CLAIM_ID"
```
- **Response:**
  Contains the final state, agent messages, and workflow result, using all documents (including the policy PDF).

---

## 🧠 Extending the System

- Add more scenario agents for new insurance types.
- Integrate human-in-the-loop or moderation steps.
- Expand RAG with more advanced retrieval or summarization.
- Add streaming or real-time features with LangGraph’s advanced capabilities.

---

## 📚 References & Inspiration

- [LangGraph Concepts](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/)
- [Step-by-Step Multi-Agent LangGraph Guide](https://medium.com/@sushmita2310/building-multi-agent-systems-with-langgraph-a-step-by-step-guide-d14088e90f72)
- [LangGraph Agents Tutorial](https://www.datacamp.com/tutorial/langgraph-agents)
- [LangChain Agents Tutorial](https://python.langchain.com/docs/tutorials/agents/)

---

## 💡 Contributing & Ideas

Pull requests and suggestions are welcome! 🚀

---

## 🧠 Agent Memory & State Management

- **Agentic Memory:**
  - Each agent can store information in a persistent memory store (SQLite) and in the workflow state.
  - For example, the Document Agent saves every processed document to both the database and the in-memory state (`state['llm_summaries']`, `state['rag_results']`).
  - The `AgenticMemory` class (see `memory/agentic_memory.py`) is used for in-memory storage, while the `AgenticMemory` table in the database is for persistent storage.
  - This allows agents to "remember" documents, summaries, and decisions across workflow runs and API calls.

---

## 🔄 Agent-to-Agent Communication in LangGraph

- **How it works:**
  - In LangGraph, agents are implemented as node functions. Each node receives the shared `state` (a Python dict or TypedDict), processes it, and returns the updated state.
  - **Agent-to-agent communication** is achieved by passing information through the shared state. For example:
    - The Document Agent adds document summaries to `state['llm_summaries']`.
    - The Policy Agent reads from `state['llm_summaries']` and adds its own analysis to `state['policy_llm_summary']`.
    - Scenario Agents use all of this information to make decisions, and can set flags (like `needs_more_docs`) in the state to influence the workflow.
  - **No direct function calls between agents:** All communication is via the shared state, which is passed from node to node according to the workflow graph.

---

## 🏗️ State and Node Definitions in LangGraph

- **State:**
  - The workflow state is defined as a `TypedDict` (see `main.py`):
    ```python
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
    ```
  - This state is passed to every agent (node) in the workflow and is updated at each step.

- **Nodes:**
  - Each agent is a function (node) that takes the state as input and returns the updated state.
    ```python
    def document_node(state: Dict, vector_db, memory, llm):
        # ... process documents, update state ...
        return state
    ```
  - Nodes are added to the workflow using `workflow.add_node("node_name", node_function)`.
  - The workflow graph defines the order and logic for node execution, including conditional and looping edges for agent-to-agent communication and decision loops.

- **Example Node Communication:**
    - Document Agent writes to `state['llm_summaries']`.
    - Policy Agent reads from `state['llm_summaries']` and writes to `state['policy_llm_summary']`.
    - Scenario Agent reads both and sets `state['needs_more_docs']` to control the workflow.

---

## 🏁 Enjoy building with LangGraph and Groq! 🏁