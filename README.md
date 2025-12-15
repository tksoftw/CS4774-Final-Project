# UVA AI Course Assistant

> An AI-powered course planning assistant for University of Virginia students, built with RAG (Retrieval-Augmented Generation).

**CS 4774 Final Project** — Amelia Chen, Tyler Qiu, Thomas Kennedy

---

## 🎯 Overview

Course information at UVA is scattered across multiple platforms: SIS, CourseForum, RateMyProfessor, Lou's List, and more. This application consolidates all that information into a single, intelligent AI assistant that can help students with:

- 💬 **Natural Language Q&A** — Ask questions about courses, prerequisites, professors
- 📚 **Course Search** — Browse and search the course catalog
- 📅 **Schedule Building** — Build and visualize your class schedule
- ✨ **Smart Recommendations** — Get personalized course suggestions

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + FastAPI |
| AI/LLM | OpenAI GPT-4o |
| Vector DB | ChromaDB |
| Embeddings | OpenAI text-embedding-3-small |
| Frontend | HTML/CSS + Jinja2 (no JavaScript) |
| Data Source | UVA SIS API |

## 📁 Project Structure

```
CS4774-Final-Project/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings & configuration
│   ├── routers/             # API endpoints
│   │   ├── chat.py          # Chat interface
│   │   ├── courses.py       # Course browser
│   │   └── schedule.py      # Schedule builder
│   ├── services/            # Business logic
│   │   ├── openai_service.py    # OpenAI API wrapper
│   │   ├── sis_service.py       # SIS API integration
│   │   └── rag_engine.py        # RAG implementation
│   ├── data/                # Data management
│   │   ├── vector_store.py  # ChromaDB operations
│   │   └── course_loader.py # Data ingestion
│   └── models/
│       └── schemas.py       # Pydantic models
├── templates/               # Jinja2 HTML templates
├── static/css/             # Stylesheets
├── data/                   # Cached data & vector store
├── requirements.txt
├── PROJECT_OUTLINE.md
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/CS4774-Final-Project.git
   cd CS4774-Final-Project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy the example env file
   copy env.example .env   # Windows
   cp env.example .env     # macOS/Linux
   
   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=sk-your-key-here
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Open in browser**
   ```
   http://localhost:8000
   ```

### First-Time Setup: Index Courses

Before using the chat feature, you need to index course data:

1. Navigate to `http://localhost:8000/admin/index`
2. Click "Start Indexing" to fetch and index courses from the SIS API
3. Wait for the process to complete (may take a few minutes)

## 📖 Usage

### Chat Assistant
Navigate to `/chat` to ask questions about courses:
- "What CS courses should I take for machine learning?"
- "Tell me about CS 4774"
- "What are the prerequisites for Data Structures?"
- "Who teaches Operating Systems?"

### Course Browser
Navigate to `/courses` to:
- Search by subject (CS, MATH, STAT, etc.)
- Search by keyword
- View course details and enrollment status
- Add courses to your schedule

### Schedule Builder
Navigate to `/schedule` to:
- View your added courses
- See a weekly calendar view
- Remove courses from your schedule

## 🔌 API Integrations

### Currently Implemented

| Source | Status | Description |
|--------|--------|-------------|
| SIS API | ✅ Active | Course catalog, sections, enrollment |
| OpenAI | ✅ Active | Chat completions, embeddings |

### Planned (TODO)

| Source | Status | Description |
|--------|--------|-------------|
| RateMyProfessor | 📋 TODO | Professor ratings and reviews |
| HoosList | 📋 TODO | Grade distributions, historical data |
| CourseForum | 📋 TODO | Student course reviews |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User (Browser)                         │
│                  HTML Forms (POST/GET)                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Routers    │  │  RAG Engine  │  │   Services   │  │
│  │  /chat       │  │  Query →     │  │  SIS API     │  │
│  │  /courses    │  │  Retrieve →  │  │  OpenAI      │  │
│  │  /schedule   │  │  Generate    │  │  (RMP TODO)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    ChromaDB                              │
│            Vector embeddings of course data              │
└─────────────────────────────────────────────────────────┘
```

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `DEBUG` | Enable debug mode | No |
| `CHROMA_PERSIST_DIR` | Vector DB storage path | No |

## 🧪 Development

### Running in Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Project Guidelines
- Frontend: HTML/CSS only (no JavaScript)
- Backend: Python with FastAPI
- All forms use traditional POST/GET requests
- Server-side rendering with Jinja2 templates

## 📜 License

This project was created for educational purposes as part of CS 4774 at the University of Virginia.

## 🙏 Acknowledgments

- [UVA SIS API](https://s23.cs3240.org/sis-api.html) for course data
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [OpenAI](https://openai.com/) for AI capabilities

