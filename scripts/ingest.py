#!/usr/bin/env python3
"""
Ingest markdown files into ChromaDB with OpenAI embeddings.
This script:
1. Loads markdown files from the docs directory
2. Preprocesses the content
3. Splits into chunks
4. Generates embeddings using OpenAI
5. Stores in ChromaDB
"""

import os
import glob
import re
from typing import List, Dict, Any
import argparse
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import tiktoken
from tqdm import tqdm
from langchain_text_splitters import MarkdownHeaderTextSplitter

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Initialize OpenAI embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small"
)

# Initialize tokenizer for token counting
tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer

def preprocess_markdown(text: str) -> str:
    """
    Clean and preprocess markdown text.
    """
    # Remove unnecessary markdown formatting that doesn't add semantic value
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Remove image links
    text = re.sub(r'<[^>]*>', '', text)  # Remove HTML tags
    
    return text

def chunk_markdown_with_headers(text: str) -> List[Dict[str, Any]]:
    """
    Split markdown text into chunks based on headers using LangChain's MarkdownHeaderTextSplitter.
    Returns a list of dictionaries with text and metadata.
    
    Manually processes the chunks to ensure proper metadata inheritance from parent headers.
    """
    # Define the headers to split on
    headers_to_split_on = [
        ("#", "title"),
        ("##", "section"),
        ("###", "subsection"),
    ]
    
    # Create the splitter
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
        return_each_line=False
    )
    
    # Split the text
    chunks = markdown_splitter.split_text(text)
    
    # Process chunks to ensure metadata inheritance
    processed_chunks = []
    current_title = ""
    current_section = ""
    
    for chunk in chunks:
        # Extract metadata
        metadata = chunk.metadata
        
        # Ensure title inheritance
        if "title" in metadata:
            current_title = metadata["title"]
        else:
            metadata["title"] = current_title
            
        # Ensure section inheritance
        if "section" in metadata:
            current_section = metadata["section"]
        else:
            metadata["section"] = current_section
            
        # Add to processed chunks
        processed_chunks.append(chunk)
    
    return processed_chunks

def extract_metadata(file_path: str, chunk_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format metadata from file path and chunk metadata.
    """
    filename = os.path.basename(file_path)
    
    # Start with basic metadata
    metadata = {
        "source": filename,
        "path": file_path
    }
    
    # Add metadata from chunk
    if "title" in chunk_metadata:
        metadata["title"] = chunk_metadata["title"]
    else:
        metadata["title"] = filename
        
    if "section" in chunk_metadata:
        metadata["section"] = chunk_metadata["section"]
    else:
        metadata["section"] = ""
        
    if "subsection" in chunk_metadata:
        metadata["subsection"] = chunk_metadata["subsection"]
    
    return metadata

def ingest_docs(docs_dir: str, db_path: str) -> None:
    """
    Main ingestion function to process docs and store in ChromaDB.
    """
    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_or_create_collection(
        name="kb_documents",
        embedding_function=openai_ef
    )
    
    # Get all markdown files
    md_files = glob.glob(os.path.join(docs_dir, "**/*.md"), recursive=True)
    print(f"Found {len(md_files)} markdown files to process")
    
    # Process each file
    doc_chunks = []
    metadatas = []
    ids = []
    chunk_id = 0
    
    for file_path in tqdm(md_files, desc="Processing files"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Preprocess content
        processed_content = preprocess_markdown(content)
        
        # Chunk the document using header-based splitting
        chunks_with_metadata = chunk_markdown_with_headers(processed_content)
        
        # Store chunks with metadata
        for i, chunk_with_metadata in enumerate(chunks_with_metadata):
            # Extract text and metadata
            chunk_text = chunk_with_metadata.page_content
            chunk_header_metadata = chunk_with_metadata.metadata
            
            # Skip empty chunks
            if not chunk_text.strip():
                continue
                
            # Create full metadata
            chunk_metadata = extract_metadata(file_path, chunk_header_metadata)
            chunk_metadata["chunk_id"] = i
            chunk_metadata["chunk_total"] = len(chunks_with_metadata)
            
            # Add to collections
            doc_chunks.append(chunk_text)
            metadatas.append(chunk_metadata)
            ids.append(f"chunk_{chunk_id}")
            chunk_id += 1
    
    # Add documents to ChromaDB
    if doc_chunks:
        print(f"Adding {len(doc_chunks)} chunks to ChromaDB")
        collection.add(
            documents=doc_chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully added {len(doc_chunks)} chunks to ChromaDB")
    else:
        print("No document chunks to add")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest markdown files into ChromaDB")
    parser.add_argument("--docs_dir", type=str, default="docs",
                        help="Directory containing markdown files")
    parser.add_argument("--db_path", type=str, default="chroma_store",
                        help="Directory to store ChromaDB")
    
    args = parser.parse_args()
    
    ingest_docs(args.docs_dir, args.db_path)