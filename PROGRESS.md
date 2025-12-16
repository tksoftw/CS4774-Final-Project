# UVA AI Course Assistant - Development Progress

## Current Status: MVP Complete ✅

The core RAG application is functional with async chat, markdown rendering, course data ingestion, and HoosList integration.

---

## Completed Features

### ✅ Backend Infrastructure
- **FastAPI application** with modular router structure
- **Configuration management** via pydantic-settings
- **Environment variables** for secure API key handling

### ✅ AI Integration (Google Gemini)
- **Text generation** using gemini-2.5-flash lite
- **Embeddings** using gemini-embedding-001
- Task-type aware embeddings (document vs query)

### ✅ Data Pipeline
- **SIS API integration** - fetch course catalog, sections, instructors
- **HoosList integration** - fetch course descriptions and prerequisites
- **Batch indexing** with progress indicators and ETA
- **JSON caching** to avoid repeated API calls
- **Readable time formatting** - converts "09.00.00.000000" to "9am"

### ✅ Vector Database (ChromaDB)
- Persistent storage of course embeddings
- **Hybrid search**: exact course number matching + semantic search
- Metadata filtering for precise retrieval
- ~800+ course sections indexed

### ✅ RAG Engine
- Context-aware response generation
- Retrieves top 10 relevant documents per query
- System prompt tuned for academic advising
- Sources tracking (though not displayed to user)

### ✅ Chat Interface
- **Async fetch API** with loading animation
- **Markdown rendering** via mistune (server-side)
- Formatted responses with lists, code blocks, tables
- Conversation memory within session
- Suggestion chips for common queries
- Dark theme with UVA colors

### ✅ Course Browser
- Search by keyword, subject, instructor
- Display course details
- Section information (times, locations, enrollment)

---

## In Progress

### 🔄 Schedule Builder
- Basic page structure exists
- Need to implement course selection and calendar view

---

## TODO

### 📋 RateMyProfessor Integration
- Web scraping for professor ratings
- Match instructors to ratings
- Include in RAG context
- Display in course search results

### 📋 Enhanced Schedule Features
- Visual weekly calendar
- Conflict detection
- Multiple schedule comparison
- Export to calendar apps

### 📋 UI/UX Improvements
- Mobile responsiveness
- Accessibility (ARIA labels, keyboard nav)

### 📋 Performance
- Batch embedding requests
- Caching for repeated queries
- Database connection pooling

### 📋 Testing
- Unit tests for services
- Integration tests for API endpoints
- End-to-end tests for chat flow

---

## Known Issues

1. **Session storage is in-memory** - chat history lost on server restart
2. **No user authentication** - sessions are anonymous
3. **Rate limiting not implemented** - could hit API quotas
4. **HoosList fetching is slow** - fetches one course at a time during indexing

---

## Recent Changes

### December 2024

#### Markdown Rendering
- Added **mistune** library for server-side markdown rendering
- Supports lists, code blocks, tables, bold/italic
- Registered as Jinja2 filter for templates
- Consistent text colors in chat bubbles

#### Readable Time Formatting
- Added `_format_time()` helper to SISService
- Converts "09.00.00.000000" → "9am"
- Converts "14.30.00.000000" → "2:30pm"
- Times now human-readable in RAG context

#### Simplified Chat Interface
- Replaced SSE streaming with simple fetch + loading animation
- "Thinking..." indicator with spinner
- Faster perceived load (no streaming complexity)
- Minimal JavaScript (~35 lines)

#### HoosList Integration
- Added `get_course_description()` to SISService
- Fetches descriptions and prerequisites during indexing
- Enriched course documents with full descriptions
- Prerequisites now included in RAG context

#### Hybrid Search
- Implemented exact course number matching
- Falls back to semantic search for remaining results
- Improved accuracy for specific course queries (e.g., "CS 4774")

#### Indexing Improvements
- Added progress indicators for SIS fetching
- Added progress indicators for HoosList fetching
- Added batch progress with ETA for embedding generation
- Clear console output during indexing

#### Model Migration
- Switched from OpenAI to Google Gemini
- Updated embeddings to gemini-embedding-001
- Updated generation to gemini-2.5-flash lite

---

## Metrics

| Metric | Value |
|--------|-------|
| Indexed Courses | ~200 unique courses |
| Indexed Sections | ~800 sections |
| Subjects Covered | CS, DSA, STAT, MATH, STS |
| Avg Query Time | 2-4 seconds |
| Vector Dimensions | 3072 |

---

## Team Contributions

| Member | Focus Areas |
|--------|-------------|
| Amelia Chen | TBD |
| Tyler Qiu | TBD |
| Thomas Kennedy | TBD |

---

## Next Steps

1. **Re-index** with readable time formats
2. **Implement schedule builder** - basic functionality
3. **Add RMP scraping** - professor ratings
4. **Polish UI** - mobile responsiveness
