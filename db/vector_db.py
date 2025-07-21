import chromadb
from chromadb.config import Settings

class VectorDB:
    def __init__(self, persist_directory="./db/chroma_store"):
        self.client = chromadb.Client(Settings(persist_directory=persist_directory))
        self.collection = self.client.get_or_create_collection("insurance_docs")

    def add_document(self, doc_id, content, metadata=None):
        self.collection.add(documents=[content], ids=[doc_id], metadatas=[metadata or {}])

    def query(self, query_text, n_results=3):
        return self.collection.query(query_texts=[query_text], n_results=n_results) 