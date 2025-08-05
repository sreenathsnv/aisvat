import os
from pathlib import Path
import hashlib
import re
from typing import List, Dict, Any
from chromadb import HttpClient
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document as LangChainDocument
from django.conf import settings
from .vulnerability_extraction import parse_vulnerability_from_pdf, extract_text_from_image, extract_structured_vulnerabilities, convert_vulnerabilities_to_documents, get_qa_chain
from langchain_community.llms import Ollama
import tempfile

import logging
logger = logging.getLogger(__name__)

CHROMA_HOST = getattr(settings, 'CHROMA_HOST', 'localhost')
CHROMA_PORT = int(getattr(settings, 'CHROMA_PORT', 6003))



def check_chromadb_connection(host: str = CHROMA_HOST, port: int = CHROMA_PORT) -> bool:
    """
    Check if the ChromaDB server is running and accessible.
    
    Args:
        host (str): ChromaDB host
        port (int): ChromaDB port
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        client = HttpClient(host=host, port=port)
        client.heartbeat()  # Check server availability
        print("ChromaDB is accessible!")
        return True
    except Exception as e:
        print(f"ChromaDB is not accessible: {e}")
        return False

def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in settings.ALLOWED_EXTENSIONS

def compute_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_collection_name(filepath: str, unique_id: str = None) -> str:
    """
    Generate a unique collection name from the file path, appending a unique identifier if provided.
    
    Args:
        filepath (str): The path or name of the file.
        unique_id (str, optional): A unique identifier to append to the collection name.
    
    Returns:
        str: The generated collection name, max 50 characters, alphanumeric start/end.
    """
   
    collection_name = Path(filepath).stem
    collection_name = collection_name.replace(" ", "-")
    collection_name = re.sub("[^A-Za-z0-9]+", "-", collection_name)
    max_base_length = 30 if unique_id else 50
    collection_name = collection_name[:max_base_length]
    if len(collection_name) < 3:
        collection_name = collection_name + "xyz"
    if not collection_name[0].isalnum():
        collection_name = "A" + collection_name[1:]
    if not collection_name[-1].isalnum():
        collection_name = collection_name[:-1] + "Z"
    # Append unique_id if provided
    if unique_id:
        # Truncate further to ensure total length <= 50 after adding unique_id
        max_base_length = 50 - len(unique_id) - 1  # -1 for hyphen
        collection_name = collection_name[:max_base_length]
        collection_name = f"{collection_name}-{unique_id}"
    return collection_name

def store_in_chromadb(
    docs: List[LangChainDocument],
    collection_name: str
):
    if not check_chromadb_connection():
        raise ValueError("Could not connect to ChromaDB server. Please ensure it is running.")

    # Filter out empty docs
    docs = [doc for doc in docs if doc.page_content.strip()]
    if not docs:
        raise ValueError("No valid content found in documents for embedding.")

    # Extract file_hash from the first doc (assuming all docs share same hash)
    file_hash = docs[0].metadata.get("file_hash") if docs[0].metadata else None
    if not file_hash:
        raise ValueError("file_hash missing in document metadata.")

    client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    vectorstore = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )

    # Get all metadata (may return empty if this is the first document)
    try:
        all_docs = vectorstore._collection.get(include=["metadatas"])
    except Exception as e:
        all_docs = {"metadatas": []}

    metadatas = all_docs.get("metadatas", [])

    # Check for existing file_hash
    for metadata in metadatas:
        if metadata.get("file_hash") == file_hash:
            print(f"Documents with file_hash {file_hash} already exist in ChromaDB.")
            return vectorstore

    # If no match, add the documents
    vectorstore.add_documents(docs)
    print(f"New documents added to ChromaDB under collection: {collection_name}")
    return vectorstore


def process_files(
    files: List[Any],
    llm: Ollama,
    model_name: str,
    chunk_size: int = 600,
    chunk_overlap: int = 40,
    llm_temperature: float = 0.7,
    max_tokens: int = 1024,
    top_k: int = 3
) -> tuple[List[str], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process uploaded files to extract vulnerabilities and store them in ChromaDB.

    Args:
        files (List[Any]): List of uploaded file objects
        llm (Ollama): Initialized LLM instance
        model_name (str): Name of the LLM model
        chunk_size (int): Size of text chunks for processing
        chunk_overlap (int): Overlap between text chunks
        llm_temperature (float): Temperature for LLM
        max_tokens (int): Maximum tokens for LLM response
        top_k (int): Number of top results to retrieve from vectorstore

    Returns:
        tuple: (collection_names, qa_chains, vulnerabilities)
    """
    if not check_chromadb_connection():
        raise ValueError("Could not connect to ChromaDB server. Please ensure it is running.")

    collection_names = []
    qa_chains = {}
    vulnerabilities = []

    for file in files:
        file_ext = Path(file.name).suffix.lower()
        if not allowed_file(file.name):
            raise ValueError(f"Unsupported file type: {file.name}")

        # Handle both InMemoryUploadedFile and TemporaryUploadedFile
        if hasattr(file, 'temporary_file_path'):
            file_path = file.temporary_file_path()
            temp_file = None
        else:
            # Save InMemoryUploadedFile to a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file.close()
            file_path = temp_file.name

        collection_name = create_collection_name(file.name)
        collection_names.append(collection_name)

        try:
            file_hash = compute_file_hash(file_path)

            if file_ext == '.pdf':
                vuln_data = parse_vulnerability_from_pdf(file_path, llm, model_name)
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                text = extract_text_from_image(file_path)
                vuln_data = extract_structured_vulnerabilities(text, llm, model_name)
            else:
                continue

            vulnerabilities.extend(vuln_data)
            vectorstore = store_in_chromadb(convert_vulnerabilities_to_documents(vuln_data,file_hash), collection_name)

            qa_chain, qa_status = get_qa_chain(vectorstore, llm_temperature, max_tokens, top_k, model_name)
            if not qa_chain:
                raise ValueError(qa_status)
            qa_chains[collection_name] = qa_chain
        finally:
            # Clean up temporary file if created
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    print(f"Error removing temp file {temp_file.name}: {e}")

    return collection_names, qa_chains, vulnerabilities