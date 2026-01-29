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


def generate_response(question: str, context_docs: List[Dict], conversation_history: List[Dict] = None) -> str:
    """Generate a response using Groq (Llama 3)"""
    # Filter out low-confidence documents (distance > 1.5 means low relevance)
    CONFIDENCE_THRESHOLD = 1.5
    confident_docs = [doc for doc in context_docs if doc.get("distance", 0) < CONFIDENCE_THRESHOLD]

    # Build context from retrieved documents
    if confident_docs:
        context = "\n\n---\n\n".join([doc["content"] for doc in confident_docs])
        context_note = ""
    else:
        # No confident matches - let the model know
        context = "\n\n---\n\n".join([doc["content"] for doc in context_docs[:1]])  # Use top result anyway
        context_note = "\n\nNote: The retrieved information may not be directly relevant to this question. If unsure, acknowledge that you don't have specific information about this topic."

    # System prompt
    system_prompt = """You are a friendly and knowledgeable art assistant for "Inside the Paintbox",
the portfolio website of Ragini Chatterjee.

Your role is to:
- Explain the inspiration, techniques, and meaning behind paintings
- Be conversational and welcoming, as if you're giving a gallery tour
- If asked about a certain artwork on the site, provide details about that specific piece

If you don't have specific information about something, say so honestly and offer to help with what you do know.
Keep responses concise but informative (1-2 sentences unless more detail is requested).
Always base your answers on the provided context. Do not make up information that isn't in the context."""

    # User prompt with context
    user_prompt = f"""Based on the following information about the artworks:

{context}{context_note}

---

Visitor's question: {question}

Please provide a helpful and engaging response:"""

    try:
        client = get_groq_client()

        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided (last 6 exchanges max to stay within context limits)
        if conversation_history:
            for msg in conversation_history[-12:]:  # Last 6 exchanges (12 messages)
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current question with context
        messages.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=200,
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble responding right now. Please try again in a moment!"


def build_search_query(question: str, conversation_history: List[Dict] = None) -> str:
    """
    Build an enhanced search query that includes conversation context.
    This helps with follow-up questions like "What colors does it have?"
    by including context about what "it" refers to.
    """
    if not conversation_history:
        return question

    # Get the last few exchanges to understand context
    recent_history = conversation_history[-4:]  # Last 2 exchanges

    # Extract key context from recent messages
    context_parts = []
    for msg in recent_history:
        if msg["role"] == "user":
            context_parts.append(msg["content"])

    # Combine current question with recent context for better search
    # Put current question first (most important), then add context
    enhanced_query = question + " " + " ".join(context_parts)

    return enhanced_query


def query_rag(question: str, conversation_history: List[Dict] = None) -> str:
    """Main RAG query function"""
    # 1. Build enhanced search query with conversation context
    search_query = build_search_query(question, conversation_history)

    # 2. Search for relevant documents using enhanced query
    similar_docs = search_similar(search_query, n_results=3)

    # 3. Generate response with context and conversation history
    response = generate_response(question, similar_docs, conversation_history)

    return response


def get_collection_stats():
    """Get statistics about the indexed collection"""
    return {
        "document_count": collection.count(),
        "collection_name": collection.name
    }
