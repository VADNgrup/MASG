import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from src.utils.config import config, Config

class VectorStoreManager:
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.vector_store_path = Config.OUTPUT_DIR / document_id / 'vector_store'
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def build_and_save(self, markdown_text: str):
        print("  - Splitting Markdown by Headers...")
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
        md_header_splits = markdown_splitter.split_text(markdown_text)

        print("  - Chunking large sections...")
        chunk_size = 1000
        chunk_overlap = 200
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        splits = text_splitter.split_documents(md_header_splits)
        
        print(f"  - Creating FAISS index from {len(splits)} chunks...")
        vectorstore = FAISS.from_documents(documents=splits, embedding=self.embeddings)
        
        print(f"  - Saving Vector Store to {self.vector_store_path}")
        vectorstore.save_local(str(self.vector_store_path))
        return self.vector_store_path

    def load_vector_store(self):
        if not os.path.exists(str(self.vector_store_path)):
            raise FileNotFoundError(f"Vector store not found at {self.vector_store_path}")
        return FAISS.load_local(str(self.vector_store_path), self.embeddings, allow_dangerous_deserialization=True)
