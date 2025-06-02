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
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks of approximately chunk_size tokens with specified overlap.
    """
    tokens = tokenizer.encode(text)
    chunks = []
    
    if len(tokens) <= chunk_size:
        return [text]
    
    i = 0
    while i < len(tokens):
        # Get chunk_size tokens
        chunk_end = min(i + chunk_size, len(tokens))
        chunk = tokenizer.decode(tokens[i:chunk_end])
        
        # If not the last chunk, try to break at a paragraph or sentence
        if chunk_end < len(tokens):
            # Prefer breaking at paragraphs
            paragraphs = chunk.split('\n\n')
            if len(paragraphs) > 1:
                # Keep all but the last paragraph
                chunk = '\n\n'.join(paragraphs[:-1])
                # Adjust token position based on actual chunk used
                i += len(tokenizer.encode(chunk))
            else:
                # If no paragraph breaks, try sentence breaks
                sentences = re.split(r'(?<=[.!?])\s+', chunk)
                if len(sentences) > 1:
                    # Keep all but the last sentence
                    chunk = ' '.join(sentences[:-1])
                    i += len(tokenizer.encode(chunk))
                else:
                    # If no good breaks, just use the chunk as is
                    i += chunk_size - chunk_overlap
        else:
            # Last chunk, move to end
            i = len(tokens)
        
        chunks.append(chunk)
    
    return chunks

def extract_metadata(file_path: str, text: str) -> Dict[str, Any]:
    """
    Extract metadata from markdown file and content.
    """
    filename = os.path.basename(file_path)
    
    # Extract title from first heading if available
    title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    title = title_match.group(1) if title_match else filename
    
    # Extract section headings
    headings = re.findall(r'^(#{2,4})\s+(.+)$', text, re.MULTILINE)
    section = headings[0][1] if headings else ""
    
    return {
        "source": filename,
        "title": title,
        "section": section,
        "path": file_path
    }

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
        
        # Extract base metadata
        base_metadata = extract_metadata(file_path, processed_content)
        
        # Chunk the document
        chunks = chunk_text(processed_content)
        
        # Store chunks with metadata
        for i, chunk in enumerate(chunks):
            doc_chunks.append(chunk)
            
            # Add chunk-specific metadata
            chunk_metadata = base_metadata.copy()
            chunk_metadata["chunk_id"] = i
            chunk_metadata["chunk_total"] = len(chunks)
            
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
    parser.add_argument("--docs_dir", type=str, default="../docs", 
                        help="Directory containing markdown files")
    parser.add_argument("--db_path", type=str, default="../chroma_store",
                        help="Directory to store ChromaDB")
    
    args = parser.parse_args()
    
    ingest_docs(args.docs_dir, args.db_path)