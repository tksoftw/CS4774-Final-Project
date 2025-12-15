# UVA AI Course Assistant - Project Outline

## CS 4774 Final Project
**Team:** Amelia Chen, Tyler Qiu, Thomas Kennedy

---

## 🎯 Project Overview

A Retrieval-Augmented Generation (RAG) application that consolidates UVA course information from multiple sources into a single, intelligent AI assistant. The assistant provides personalized course planning advice, schedule building, and academic guidance.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (HTML/CSS)                       │
│                    Jinja2 Templates + FastAPI                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Routes    │  │   RAG       │  │   Data Connectors       │  │
│  │   /chat     │  │   Engine    │  │   - SIS API             │  │
│  │   /courses  │  │   + OpenAI  │  │   - RMP (TODO)          │  │
│  │   /schedule │  │             │  │   - HoosList (TODO)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Vector Database (ChromaDB)                  │
│              Embedded course data for semantic search            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
CS4774-Final-Project/
├── PROJECT_OUTLINE.md
├── README.md
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration settings
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py             # Chat endpoint
│   │   ├── courses.py          # Course browsing
│   │   └── schedule.py         # Schedule builder
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rag_engine.py       # RAG implementation
│   │   ├── openai_service.py   # OpenAI API wrapper
│   │   └── sis_service.py      # SIS API integration
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
│   ├── chat.html               # Chat interface
│   ├── courses.html            # Course browser
│   └── schedule.html           # Schedule builder
├── static/
│   └── css/
│       └── styles.css          # Main stylesheet
└── data/
    └── courses/                # Cached course data
```

---

## 🔧 Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | High-performance Python web framework |
| AI/LLM | OpenAI GPT-4o | Natural language understanding & generation |
| Vector DB | ChromaDB | Semantic search over course data |
| Embeddings | OpenAI text-embedding-3-small | Document vectorization |
| Templating | Jinja2 | Server-side HTML rendering |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Markup | HTML5 | Page structure |
| Styling | CSS3 | Visual design (no JavaScript) |
| Forms | HTML Forms | User input handling |

### Data Sources
| Source | Status | Data Provided |
|--------|--------|---------------|
| SIS API | ✅ Implemented | Course catalog, sections, schedules |
| RateMyProfessor | 📋 TODO | Instructor reviews, ratings |
| HoosList (Lou's List) | 📋 TODO | Historical enrollment, grade distributions |
| CourseForum | 📋 TODO | Student course reviews |

---

## 🚀 Core Features

### 1. AI Chat Assistant
- Natural language queries about courses
- Context-aware responses using RAG
- Conversation memory within session
- Course recommendations based on interests

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
2. **Transform** into structured documents
3. **Chunk** documents for embedding
4. **Embed** using OpenAI embeddings
5. **Store** in ChromaDB vector database

### Query Pipeline
1. **Receive** user query
2. **Embed** query using same embedding model
3. **Retrieve** top-k relevant documents
4. **Augment** prompt with retrieved context
5. **Generate** response using GPT-4o
6. **Return** formatted response to user

### Prompt Template
```
You are an AI academic advisor for UVA students. Use the following course 
information to answer the student's question. Be helpful, accurate, and 
concise. If you don't have enough information, say so.

RELEVANT COURSE INFORMATION:
{retrieved_documents}

STUDENT QUESTION:
{user_query}

RESPONSE:
```

---

## 🔌 API Integrations

### SIS API (Project SIS)
- **Base URL:** `https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch`
- **Documentation:** https://s23.cs3240.org/sis-api.html
- **Data:** Course catalog, sections, meeting times, instructors

### OpenAI API
- **Model:** gpt-4o
- **Embeddings:** text-embedding-3-small
- **Usage:** Response generation, semantic search

### RateMyProfessor (TODO)
- Web scraping required
- Professor ratings and reviews
- Teaching quality metrics

### HoosList (TODO)
- Successor to Lou's List
- Grade distributions
- Historical enrollment data

---

## 🎨 UI/UX Design

### Color Palette
- **Primary:** #232D4B (UVA Navy)
- **Secondary:** #E57200 (UVA Orange)
- **Background:** #F8F9FA
- **Text:** #2C3E50
- **Accent:** #3498DB

### Design Principles
- Clean, minimal interface
- High contrast for readability
- Mobile-responsive layout
- Fast server-side rendering
- No JavaScript dependencies

---

## 📋 Development Phases

### Phase 1: Foundation ✅
- [x] Project setup
- [x] Basic FastAPI structure
- [x] SIS API integration
- [x] OpenAI integration
- [x] Basic chat interface

### Phase 2: RAG Implementation
- [ ] ChromaDB setup
- [ ] Document processing pipeline
- [ ] Query pipeline
- [ ] Context-aware responses

### Phase 3: Features
- [ ] Course search/browse
- [ ] Schedule builder
- [ ] Conversation memory

### Phase 4: Data Expansion (TODO)
- [ ] RateMyProfessor scraping
- [ ] HoosList integration
- [ ] CourseForum data

### Phase 5: Polish
- [ ] UI refinement
- [ ] Error handling
- [ ] Performance optimization
- [ ] Documentation

---

## 🔐 Environment Variables

```env
OPENAI_API_KEY=sk-...
SIS_API_BASE_URL=https://sisuva.admin.virginia.edu/...
CHROMA_PERSIST_DIR=./data/chroma
DEBUG=true
```

---

## 📝 Notes

- All frontend interactions use HTML forms (POST/GET) - no JavaScript
- FastAPI handles form submissions and redirects appropriately
- Session state managed server-side
- RAG provides accurate, grounded responses from real course data

---

## 📚 References

- [Project SIS API Documentation](https://s23.cs3240.org/sis-api.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

