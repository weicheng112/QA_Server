#!/usr/bin/env python3
"""
Query the knowledge base and generate answers using RAG.
This script:
1. Takes a user query
2. Retrieves relevant chunks from ChromaDB
3. Formats context and query into a prompt
4. Sends to OpenAI API
5. Returns the generated answer
"""

import os
import argparse
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import openai

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize OpenAI embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small"
)

def get_chroma_client(db_path: str):
    """
    Initialize and return ChromaDB client.
    """
    return chromadb.PersistentClient(path=db_path)

def retrieve_context(query: str, db_path: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve relevant document chunks from ChromaDB.
    """
    # Initialize ChromaDB
    chroma_client = get_chroma_client(db_path)
    collection = chroma_client.get_collection(
        name="kb_documents",
        embedding_function=openai_ef
    )
    
    # Query the collection
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    # Format results
    context_chunks = []
    for i in range(len(results["documents"][0])):
        context_chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if "distances" in results else None
        })
    
    return context_chunks

def format_context(context_chunks: List[Dict[str, Any]]) -> str:
    """
    Format retrieved context chunks into a single context string.
    """
    formatted_context = ""
    
    for i, chunk in enumerate(context_chunks):
        metadata = chunk["metadata"]
        
        # Format the section information
        section_info = metadata['section']
        
        # Include additional sections if available
        if 'additional_sections' in metadata and metadata['additional_sections']:
            additional = ", ".join(metadata['additional_sections'])
            section_info += f" (Also covers: {additional})"
            
        formatted_context += f"\n--- Document: {metadata['source']} | Section: {section_info} ---\n"
        formatted_context += chunk["text"]
        formatted_context += "\n"
    
    return formatted_context

def create_prompt(query: str, context: str) -> str:
    """
    Create a prompt for the LLM using the query and context.
    """
    return f"""You are a helpful assistant for a company. Answer the question based ONLY on the provided context. 
If you don't know the answer or the information is not in the context, say "I don't have enough information to answer this question."
Do not make up or infer information that is not explicitly stated in the context.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""

def generate_answer(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    Generate an answer using OpenAI's API.
    """
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers questions based only on the provided context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def query_knowledge_base(query: str, db_path: str, model: str = "gpt-4o-mini", top_k: int = 5) -> Dict[str, Any]:
    """
    Main function to query the knowledge base and generate an answer.
    """
    # Retrieve relevant context
    context_chunks = retrieve_context(query, db_path, top_k)
    
    # Format context
    formatted_context = format_context(context_chunks)
    
    # Create prompt
    prompt = create_prompt(query, formatted_context)
    
    # Generate answer
    answer = generate_answer(prompt, model)
    
    # Return result
    return {
        "query": query,
        "answer": answer,
        "context_chunks": context_chunks,
        "model_used": model
    }

def print_result(result: Dict[str, Any], show_context: bool = False) -> None:
    """
    Print the query result in a readable format.
    """
    print("\n" + "="*50)
    print(f"QUERY: {result['query']}")
    print("="*50)
    print(f"\nANSWER:\n{result['answer']}")
    
    if show_context:
        print("\n" + "-"*50)
        print("CONTEXT USED:")
        for i, chunk in enumerate(result["context_chunks"]):
            metadata = chunk["metadata"]
            print(f"\n[{i+1}] From: {metadata['source']} | Section: {metadata['section']}")
            if 'additional_sections' in metadata and metadata['additional_sections']:
                print(f"   Also covers: {', '.join(metadata['additional_sections'])}")
            print(f"Relevance: {1 - chunk['distance']:.4f} (higher is better)")
            print("-"*30)
            print(chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"])
    
    print("\n" + "="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the knowledge base")
    parser.add_argument("query", type=str, help="The query to answer")
    parser.add_argument("--db_path", type=str, default="chroma_store",
                        help="Directory where ChromaDB is stored")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo",
                        help="OpenAI model to use (gpt-3.5-turbo or gpt-4)")
    parser.add_argument("--top_k", type=int, default=5,
                        help="Number of context chunks to retrieve")
    parser.add_argument("--show_context", action="store_true",
                        help="Show the context used for the answer")
    parser.add_argument("--output", type=str,
                        help="Output file to save the result (JSON format)")
    
    args = parser.parse_args()
    
    result = query_knowledge_base(args.query, args.db_path, args.model, args.top_k)
    
    # Print result
    print_result(result, args.show_context)
    
    # Save to file if specified
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)