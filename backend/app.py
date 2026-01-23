"""
Inside the Paintbox - RAG Chatbot API
FastAPI backend for the art website chatbot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from rag import query_rag, index_documents, get_collection_stats
from document_loader import load_all_artworks, load_about_page


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Index documents automatically
    print("Starting up... Indexing artwork documents...")
    try:
        # Load documents from the website
        docs = load_all_artworks("../")

        # Also load about page
        about = load_about_page("../")
        if about:
            docs.append(about)

        # Index them
        if docs:
            index_documents(docs)
            print(f"Successfully indexed {len(docs)} documents!")
        else:
            print("Warning: No documents found to index!")
    except Exception as e:
        print(f"Error during startup indexing: {e}")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Inside the Paintbox API",
    description="RAG Chatbot API for Ragini Chatterjee's Art Portfolio",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS (allow your Netlify site to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",      # Local development
        "http://127.0.0.1:5500",      # Local development
        "http://localhost:3000",       # Local development
        "https://*.netlify.app",       # Netlify preview URLs
        "*"                            # Allow all (update in production!)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class IndexResponse(BaseModel):
    status: str
    documents_indexed: int

class HealthResponse(BaseModel):
    status: str
    documents_count: int


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    stats = get_collection_stats()
    return HealthResponse(
        status="ok",
        documents_count=stats["document_count"]
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    stats = get_collection_stats()
    return HealthResponse(
        status="healthy",
        documents_count=stats["document_count"]
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    Receives a question and returns an AI-generated response
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        response = query_rag(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Sorry, I encountered an error. Please try again."
        )


@app.post("/reindex", response_model=IndexResponse)
async def reindex_documents():
    """
    Manually reindex all documents
    Call this if you've updated your artwork pages
    """
    try:
        docs = load_all_artworks("../")
        about = load_about_page("../")
        if about:
            docs.append(about)

        count = index_documents(docs)
        return IndexResponse(status="success", documents_indexed=count)
    except Exception as e:
        print(f"Error reindexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get statistics about the indexed documents"""
    return get_collection_stats()


# Run with: uvicorn app:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
