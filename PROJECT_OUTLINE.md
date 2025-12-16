# UVA AI Course Assistant - Project Outline

## CS 4774 Final Project
**Team:** Amelia Chen, Tyler Qiu, Thomas Kennedy

---

## 🎯 Project Overview

A Retrieval-Augmented Generation (RAG) application that consolidates UVA course information from multiple sources into a single, intelligent AI assistant. The assistant provides personalized course planning advice, schedule building, and academic guidance.

---

## 🚀 Getting Started

### 1. Setup

```bash
# Clone the repository
git clone <repo-url>
cd CS4774-Final-Project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your API key
cp env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Environment Variables

Create a `.env` file with:

```env
GEMINI_API_KEY=your-gemini-api-key-here
DEBUG=true
APP_TITLE=UVA AI Course Assistant
CHROMA_PERSIST_DIR=./data/chroma
```

Get a Gemini API key from: https://aistudio.google.com/apikey

### 3. Index Courses

Before using the chat, you need to populate the vector database with course data:

**Option A: Via Admin UI**
```bash
# Start the server first
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Then visit http://localhost:8000/admin/index and click "Run Indexing"
```

**Option B: Via Python Script**
```python
from app.data.indexer import CourseIndexer

indexer = CourseIndexer()

# Index default subjects (CS, DS, STAT, MATH, STS)
indexer.index_courses(term="1262")

# Or specify subjects
indexer.index_courses(term="1262", subjects=["CS", "ECE"])

# Force refresh from APIs (ignore cache)
indexer.index_courses(term="1262", force_refresh=True)
```

**Option C: One-liner**
```bash
.\venv\Scripts\python.exe -c "from app.data.indexer import CourseIndexer; CourseIndexer().index_courses()"
```

The indexing process:
1. Fetches courses from SIS API (or cache)
2. Fetches descriptions/prerequisites from Hooslist
3. Fetches instructor reviews from TheCourseForum
4. Builds weighted documents for each section
5. Embeds and stores in ChromaDB vector database

**Expected output:**
```
==================================================
FETCHING COURSES FROM SIS API
==================================================
[1/5] Fetching CS... 245 sections (2.1s)
[2/5] Fetching DS... 12 sections (0.5s)
...

==================================================
INDEXING INTO VECTOR DATABASE
==================================================
Indexing 500 documents (10 batches):
  Batch 1/10 [ 10.0%] - 50/500 docs... Done (2.3s) | ETA: 21s
...

==================================================
INDEXING COMPLETE!
  - Indexed: 500 documents
  - Time: 45.2 seconds
==================================================
```

### 4. Run the Server

```bash
# Development mode with auto-reload
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Production mode
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000 to use the AI Course Assistant.

### 5. Data Storage

| Location | Contents |
|----------|----------|
| `data/chroma/` | ChromaDB vector database (embeddings) |
| `data/courses/` | Cached SIS API responses (JSON) |
| `data/cache/` | Cached Hooslist/TCF data (JSONL) |

To re-index, either:
- Use `force_refresh=True` to re-fetch from APIs
- Delete `data/` folder and re-run indexing

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (HTML/CSS/JS)                    │
│                    Jinja2 Templates + FastAPI                    │
│              Markdown rendering + async fetch API                │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Routes    │  │   RAG       │  │   Data Connectors       │  │
│  │   /chat     │  │   Engine    │  │   - SIS API ✅          │  │
│  │   /courses  │  │   + Gemini  │  │   - HoosList ✅         │  │
│  │   /schedule │  │   + Mistune │  │   - RMP (TODO)          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Vector Database (ChromaDB)                  │
│     Embedded course data with descriptions & prerequisites       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
CS4774-Final-Project/
├── PROJECT_OUTLINE.md
├── PROGRESS.md
├── README.md
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration settings
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py             # Chat endpoint + markdown rendering
│   │   ├── courses.py          # Course browsing
│   │   └── schedule.py         # Schedule builder
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rag_engine.py       # RAG implementation
│   │   ├── gemini_service.py   # Google Gemini API wrapper
│   │   └── sis_service.py      # SIS + HoosList API integration
│   ├── data/
│   │   ├── __init__.py
│   │   ├── vector_store.py     # ChromaDB operations
│   │   └── course_loader.py    # Data ingestion
│   └── models/
│       ├── __init__.py
│       └── schemas.py          # Pydantic models
├── templates/
│   ├── base.html               # Base template
│   ├── index.html              # Landing page
│   ├── chat.html               # Chat interface (async + markdown)
│   ├── courses.html            # Course browser
│   └── schedule.html           # Schedule builder
├── static/
│   └── css/
│       └── styles.css          # Main stylesheet
├── data/
│   ├── courses/                # Cached course data
│   └── chroma/                 # Vector database
└── tests/
    └── *.py                    # Test scripts
```

---

## 🔧 Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | High-performance Python web framework |
| AI/LLM | Google Gemini 2.0 Flash | Natural language understanding & generation |
| Vector DB | ChromaDB | Semantic search over course data |
| Embeddings | Gemini gemini-embedding-001 | Document vectorization |
| Templating | Jinja2 | Server-side HTML rendering |
| Markdown | Mistune | Server-side markdown to HTML |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Markup | HTML5 | Page structure |
| Styling | CSS3 | Visual design (dark theme) |
| Interactivity | Vanilla JavaScript | Async fetch + loading states |

### Data Sources
| Source | Status | Data Provided |
|--------|--------|---------------|
| SIS API | ✅ Implemented | Course catalog, sections, schedules |
| HoosList | ✅ Implemented | Course descriptions, prerequisites |
| RateMyProfessor | 📋 TODO | Instructor reviews, ratings |

---

## 🚀 Core Features

### 1. AI Chat Assistant
- Natural language queries about courses
- Context-aware responses using RAG
- **Markdown rendering** - lists, code, tables, bold/italic
- Conversation memory within session
- Course recommendations based on interests
- Loading animation while processing

### 2. Course Search & Browse
- Search by subject, number, instructor
- Filter by requirements, availability
- View detailed course information
- Prerequisites visualization

### 3. Schedule Builder
- Add/remove courses to schedule
- Visual weekly calendar view
- Conflict detection
- Multiple schedule comparison

### 4. Degree Planning (Future)
- Track degree progress
- Suggest courses for requirements
- Multi-semester planning
- What-if scenarios

---

## 📊 RAG Implementation

### Document Processing Pipeline
1. **Fetch** course data from SIS API
2. **Enrich** with descriptions/prerequisites from HoosList
3. **Transform** into structured documents with readable times
4. **Embed** using Gemini embeddings
5. **Store** in ChromaDB vector database

### Query Pipeline
1. **Receive** user query via async fetch
2. **Embed** query using same embedding model
3. **Retrieve** top-k relevant documents (hybrid search)
4. **Augment** prompt with retrieved context
5. **Generate** response from Gemini
6. **Render** markdown to HTML
7. **Return** formatted response

### Hybrid Search
- **Exact matching**: First checks for specific course numbers (e.g., "CS 4774")
- **Semantic search**: Then fills remaining slots with embedding similarity

### Data Formatting
- **Times**: "09.00.00.000000" → "9am", "14.30.00.000000" → "2:30pm"
- **Days**: "MoWeFr", "TuTh" (as provided by SIS)
- **Descriptions**: Full course descriptions from HoosList
- **Prerequisites**: Parsed from HoosList response

---

## 🔌 API Integrations

### SIS API (Project SIS)
- **Base URL:** `https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch`
- **Documentation:** https://s23.cs3240.org/sis-api.html
- **Data:** Course catalog, sections, meeting times, instructors

### HoosList API
- **URL:** `https://hooslist.virginia.edu/ClassSchedule/_GetCourseDescription`
- **Data:** Course descriptions, prerequisites

### Google Gemini API
- **Model:** gemini-2.0-flash
- **Embeddings:** gemini-embedding-001
- **Features:** Fast generation, document/query task types

### RateMyProfessor (TODO)
- Web scraping required
- Professor ratings and reviews
- Teaching quality metrics

---

## 🎨 UI/UX Design

### Color Palette
- **Primary:** #232D4B (UVA Navy)
- **Secondary:** #E57200 (UVA Orange)
- **Background:** #0D1117 (Dark)
- **Surface:** #1C2128
- **Text:** #E6EDF3
- **Muted:** #8B949E

### Design Principles
- Clean, minimal dark interface
- High contrast for readability
- Consistent text colors across elements
- Loading animations for feedback
- Markdown-formatted responses

---

## 📋 Development Phases

### Phase 1: Foundation ✅
- [x] Project setup
- [x] Basic FastAPI structure
- [x] SIS API integration
- [x] Gemini API integration
- [x] Basic chat interface

### Phase 2: RAG Implementation ✅
- [x] ChromaDB setup
- [x] Document processing pipeline
- [x] Query pipeline with hybrid search
- [x] Context-aware responses

### Phase 3: Enhancements ✅
- [x] HoosList integration (descriptions + prerequisites)
- [x] Markdown rendering (mistune)
- [x] Readable time formatting
- [x] Indexing progress indicators
- [x] Loading animations

### Phase 4: Features (In Progress)
- [x] Course search/browse
- [ ] Schedule builder
- [x] Conversation memory

### Phase 5: Data Expansion (TODO)
- [ ] RateMyProfessor scraping
- [ ] Grade distribution data
- [ ] Historical enrollment trends

### Phase 6: Polish
- [ ] Mobile responsiveness
- [ ] Error handling
- [ ] Performance optimization
- [ ] Documentation

---

## 🔐 Environment Variables

```env
GEMINI_API_KEY=your-gemini-api-key
CHROMA_PERSIST_DIR=./data/chroma
DATA_DIR=./data
DEBUG=true
```

---

## 📝 Notes

- **Indexing**: Run once before using chat; data is cached locally
- **Caching**: SIS responses cached in `data/courses/`, Hooslist/TCF in `data/cache/`
- **Re-indexing**: Use `force_refresh=True` or delete cache files
- Chat uses async fetch with loading animation (simpler than SSE)
- Markdown rendered server-side via mistune library
- Hybrid search combines exact course matching with semantic search
- HoosList provides richer course data (descriptions, prerequisites)
- Times formatted for readability (9am instead of 09.00.00.000000)
- Session state managed server-side with in-memory storage
- RAG provides accurate, grounded responses from real course data

---

## 📚 References

- [Project SIS API Documentation](https://s23.cs3240.org/sis-api.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Google Gemini API Reference](https://ai.google.dev/gemini-api/docs)
- [Mistune Markdown Parser](https://mistune.lepture.com/)
