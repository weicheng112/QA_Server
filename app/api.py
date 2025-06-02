#!/usr/bin/env python3
"""
FastAPI backend for the Knowledge Base Q&A system.
This API provides an endpoint to query the knowledge base.
"""

import os
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the scripts directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import our query module
from query import query_knowledge_base

# Constants
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'chroma_store')
DEFAULT_MODEL = "gpt-3.5-turbo"

# Create FastAPI app
app = FastAPI(
    title="Knowledge Base Q&A API",
    description="API for querying the knowledge base",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class QueryRequest(BaseModel):
    query: str
    model: str = DEFAULT_MODEL
    top_k: int = 5

# Response models
class QueryResponse(BaseModel):
    query: str
    answer: str
    model_used: str

# Helper functions
def check_api_key() -> bool:
    """Check if OpenAI API key is set"""
    return os.environ.get("OPENAI_API_KEY") is not None

# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Knowledge Base Q&A API"}

@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the knowledge base"""
    if not check_api_key():
        raise HTTPException(status_code=500, detail="OpenAI API key not found")
    
    result = query_knowledge_base(
        query=request.query,
        db_path=DEFAULT_DB_PATH,
        model=request.model,
        top_k=request.top_k
    )
    
    # Return only the query, answer, and model used
    return {
        "query": result["query"],
        "answer": result["answer"],
        "model_used": result["model_used"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)