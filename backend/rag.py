"""
RAG (Retrieval-Augmented Generation) Module
Handles document indexing, embedding, and retrieval
"""

import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
import os
from typing import List, Dict

# Initialize the embedding model (runs locally, free)
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding model loaded!")

# Initialize ChromaDB (local vector database)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="artworks",
    metadata={"description": "Inside the Paintbox artwork collection"}
)


def get_groq_client():
    """Get Groq client with API key"""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set!")
    return Groq(api_key=api_key)


def index_documents(documents: List[Dict]):
    """Index documents into the vector database"""
    if not documents:
        print("No documents to index!")
        return 0

    # Clear existing documents
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    # Add new documents
    for i, doc in enumerate(documents):
        try:
            # Create embedding
            embedding = embedding_model.encode(doc["content"]).tolist()

            # Add to collection
            collection.add(
                documents=[doc["content"]],
                embeddings=[embedding],
                metadatas=[{
                    "title": doc.get("title", ""),
                    "source": doc.get("source", ""),
                    "subtitle": doc.get("subtitle", "")
                }],
                ids=[f"doc_{i}"]
            )
        except Exception as e:
            print(f"Error indexing document {i}: {e}")

    print(f"Indexed {len(documents)} documents")
    return len(documents)


def search_similar(query: str, n_results: int = 3) -> List[Dict]:
    """Search for similar documents"""
    # Embed the query
    query_embedding = embedding_model.encode(query).tolist()

    # Search in ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    # Format results
    similar_docs = []
    for i in range(len(results["documents"][0])):
        similar_docs.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return similar_docs


def generate_response(question: str, context_docs: List[Dict]) -> str:
    """Generate a response using Groq (Llama 3)"""
    # Build context from retrieved documents
    context = "\n\n---\n\n".join([doc["content"] for doc in context_docs])

    # System prompt
    system_prompt = """You are a friendly and knowledgeable art assistant for "Inside the Paintbox",
the portfolio website of Ragini Chatterjee.

Your role is to:
- Explain the inspiration, techniques, and meaning behind paintings
- Be conversational and welcoming, as if you're giving a gallery tour
- If asked about a centain artwork on the site, provide details about that specific piece and the link to view it.

If you don't have specific information about something, say so politely and offer to help with what you do know.
Keep responses concise but informative (1-2 sentences unless more detail is requested)."""

    # User prompt with context
    user_prompt = f"""Based on the following information about the artworks:

{context}

---

Visitor's question: {question}

Please provide a helpful and engaging response:"""

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble responding right now. Please try again in a moment!"


def query_rag(question: str) -> str:
    """Main RAG query function"""
    # 1. Search for relevant documents
    similar_docs = search_similar(question, n_results=3)

    # 2. Generate response with context
    response = generate_response(question, similar_docs)

    return response


def get_collection_stats():
    """Get statistics about the indexed collection"""
    return {
        "document_count": collection.count(),
        "collection_name": collection.name
    }
