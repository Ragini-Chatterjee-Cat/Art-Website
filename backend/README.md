# Inside the Paintbox - RAG Chatbot Backend

A RAG (Retrieval-Augmented Generation) chatbot that answers questions about your artworks.

---

## ARCHITECTURE DIAGRAM

```
                            YOUR ART WEBSITE
    ┌────────────────────────────────────────────────────────────┐
    │                                                            │
    │   ┌──────────────────────────────────────────────────┐    │
    │   │              NETLIFY (Free Hosting)               │    │
    │   │                                                   │    │
    │   │   Index.html ─── css/ ─── js/chat.js ─── images/ │    │
    │   │         │                     │                   │    │
    │   │         │                     │                   │    │
    │   │         ▼                     ▼                   │    │
    │   │   [Your Art]          [Chat Widget]               │    │
    │   │                             │                     │    │
    │   └─────────────────────────────┼─────────────────────┘    │
    │                                 │                          │
    └─────────────────────────────────┼──────────────────────────┘
                                      │
                                      │ HTTPS Request
                                      │ POST /chat
                                      │ {"message": "Tell me about Voices"}
                                      │
                                      ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                 RENDER.COM (Free Hosting)                   │
    │                                                             │
    │   ┌─────────────────────────────────────────────────────┐  │
    │   │               FASTAPI BACKEND (app.py)               │  │
    │   │                                                      │  │
    │   │   /chat endpoint receives question                   │  │
    │   │         │                                            │  │
    │   │         ▼                                            │  │
    │   │   ┌─────────────────────────────────────────────┐   │  │
    │   │   │            RAG PIPELINE (rag.py)             │   │  │
    │   │   │                                              │   │  │
    │   │   │  STEP 1: Embed the question                  │   │  │
    │   │   │          │                                   │   │  │
    │   │   │          ▼                                   │   │  │
    │   │   │  ┌─────────────────────────────────────┐    │   │  │
    │   │   │  │  HuggingFace Embeddings (FREE)      │    │   │  │
    │   │   │  │  Model: all-MiniLM-L6-v2            │    │   │  │
    │   │   │  │  Converts text → 384-dim vector     │    │   │  │
    │   │   │  └─────────────────────────────────────┘    │   │  │
    │   │   │          │                                   │   │  │
    │   │   │          ▼                                   │   │  │
    │   │   │  STEP 2: Search for similar artworks         │   │  │
    │   │   │          │                                   │   │  │
    │   │   │          ▼                                   │   │  │
    │   │   │  ┌─────────────────────────────────────┐    │   │  │
    │   │   │  │  ChromaDB (FREE Vector Database)    │    │   │  │
    │   │   │  │                                     │    │   │  │
    │   │   │  │  Stores artwork descriptions as     │    │   │  │
    │   │   │  │  vectors for similarity search      │    │   │  │
    │   │   │  │                                     │    │   │  │
    │   │   │  │  Returns top 3 matching artworks    │    │   │  │
    │   │   │  └─────────────────────────────────────┘    │   │  │
    │   │   │          │                                   │   │  │
    │   │   │          ▼                                   │   │  │
    │   │   │  STEP 3: Generate response with context      │   │  │
    │   │   │          │                                   │   │  │
    │   │   └──────────┼───────────────────────────────────┘   │  │
    │   │              │                                        │  │
    │   └──────────────┼────────────────────────────────────────┘  │
    │                  │                                           │
    └──────────────────┼───────────────────────────────────────────┘
                       │
                       │ API Call
                       ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    GROQ API (FREE LLM)                      │
    │                                                             │
    │   Model: Llama 3.3 70B                                      │
    │                                                             │
    │   Input:                                                    │
    │   ┌─────────────────────────────────────────────────────┐  │
    │   │ System: You are an art assistant for Inside the      │  │
    │   │         Paintbox by Ragini Chatterjee...             │  │
    │   │                                                      │  │
    │   │ Context: [Relevant artwork descriptions from DB]     │  │
    │   │                                                      │  │
    │   │ Question: Tell me about Voices                       │  │
    │   └─────────────────────────────────────────────────────┘  │
    │                                                             │
    │   Output: "Voices is a mixed media piece that explores      │
    │           the darker side of unbridled ambition..."         │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
                       │
                       │ Response
                       ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    BACK TO USER                             │
    │                                                             │
    │   Chat Widget displays: "Voices is a mixed media piece      │
    │   that explores the darker side of unbridled ambition..."   │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

---

## WHAT EACH FILE DOES

```
backend/
│
├── app.py                 # FastAPI server - handles HTTP requests
│   │                        - /chat: receives questions, returns AI answers
│   │                        - /health: checks if server is running
│   │                        - /reindex: refreshes artwork database
│   │
├── rag.py                 # RAG (Retrieval-Augmented Generation) logic
│   │                        - Embeds questions into vectors
│   │                        - Searches ChromaDB for similar artworks
│   │                        - Calls Groq API to generate responses
│   │
├── document_loader.py     # Extracts artwork info from HTML files
│   │                        - Reads your artwork pages
│   │                        - Extracts titles, descriptions, inspiration
│   │                        - Prepares data for indexing
│   │
├── requirements.txt       # Python dependencies
│   │
├── .env.example           # Example environment variables
│   │
└── chroma_db/             # Vector database storage (auto-created)
```

---

## HOW RAG WORKS (SIMPLE EXPLANATION)

```
Traditional Chatbot:
    Question ──────────────────────────────► LLM ──► Generic Answer
                     (LLM doesn't know your art)


RAG Chatbot:
    Question ──► Find Relevant ──► Add Context ──► LLM ──► Specific Answer
                 Artworks           to Question         (about YOUR art!)


Example:

    User: "What inspired the Voices painting?"
           │
           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  STEP 1: SEARCH (Vector Similarity)                          │
    │                                                              │
    │  Question converted to numbers: [0.23, -0.45, 0.12, ...]    │
    │                                                              │
    │  Compare with stored artworks:                               │
    │    - Voices:    [0.25, -0.43, 0.11, ...] ← 95% similar!     │
    │    - Trapped:   [0.18, -0.30, 0.08, ...] ← 78% similar      │
    │    - Flowers:   [-0.10, 0.20, -0.15, ...] ← 30% similar     │
    │                                                              │
    │  Result: Return "Voices" and "Trapped" descriptions          │
    └──────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  STEP 2: AUGMENT (Add Context)                               │
    │                                                              │
    │  Create prompt for LLM:                                      │
    │                                                              │
    │  "Here's info about relevant artworks:                       │
    │                                                              │
    │   Voices - Mixed Media on Paper. 11.7x16.5 inches.          │
    │   This painting depicts a darker side to unbridled           │
    │   ambition. The warm colours merge into black...             │
    │                                                              │
    │   Now answer: What inspired the Voices painting?"            │
    └──────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  STEP 3: GENERATE (LLM Response)                             │
    │                                                              │
    │  Groq/Llama 3 generates:                                     │
    │                                                              │
    │  "Voices was inspired by the darker side of unbridled        │
    │   ambition. Ragini uses warm tones to represent passion      │
    │   for life, which gradually merges into black, symbolizing   │
    │   the despair that comes with constantly sacrificing today   │
    │   for a better tomorrow. The caged face represents the       │
    │   numbness of leading an unhappy life..."                    │
    └──────────────────────────────────────────────────────────────┘
```

---

## QUICK START (LOCAL TESTING)

```bash
# 1. Navigate to backend folder
cd /Users/raginichatterjee/Desktop/Website/backend

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file with your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# 5. Run the server
python app.py

# Server runs at http://localhost:8000
# Open your website and test the chat!
```

---

## DEPLOYMENT TO RENDER (FREE)

See the main instructions in the project root.

---

## API ENDPOINTS

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Health check with stats |
| `/chat` | POST | Send message, get AI response |
| `/reindex` | POST | Re-index artwork documents |
| `/stats` | GET | Get database statistics |

---

## TROUBLESHOOTING

**"GROQ_API_KEY not set"**
- Make sure you created a `.env` file with your Groq API key

**"No documents indexed"**
- Check that your artwork HTML files are in the correct location
- Call `/reindex` endpoint to manually refresh

**"Connection refused"**
- Make sure the backend server is running
- Check the API_URL in chat.js matches your server address
