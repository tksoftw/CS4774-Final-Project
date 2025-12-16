"""RAG (Retrieval-Augmented Generation) engine."""

from typing import Optional
from app.services.gemini_service import GeminiService
from app.data.vector_store import VectorStore
from app.config import get_cluster_summary

# Module-level storage for RAG context (persists across RAGEngine instances)
_last_context: dict[str, str] = {}
_last_query: dict[str, str] = {}


class RAGEngine:
    """RAG engine for course-aware AI responses."""
    
    SYSTEM_PROMPT_BASE = """You are an AI academic advisor for University of Virginia (UVA) students. 
Your role is to help students with course planning, scheduling, and academic advice.

Guidelines:
- Be helpful, accurate, and friendly
- Use the provided course information to give specific, grounded answers
- If you don't have enough information to answer a question, simply state clearly that the information is not available
- Focus on UVA-specific information when available
- Inform students on prerequisites, course content, and scheduling
- Suggest courses based on student interests and requirements
- Try to use markdown formatting to make the response more readable and visually appealing.
- Courses may include lab/discussion sections which will be listed as 0 credits

IMPORTANT - Handling follow-up requests:
- When user says "keep going", "more info", "tell me more", "continue", "yes", "elaborate", etc., provide ADDITIONAL details you haven't mentioned yet
- Do NOT repeat information you already gave - provide NEW information like:
  * Prerequisites and what they cover
  * Related/similar courses they might also like
  * Tips for success in the course
  * How this course fits into degree requirements
  * Comparison with similar courses
  * What topics/projects students typically work on
- Do NOT ask "what would you like to know?" - just provide more useful information
- Remember the conversation context and what course/topic was being discussed

When discussing a VERY specific question about a specific course, answer the question briefly and to the point.
 - For example, if the question is "Who teaches Discrete Math 1?", an appropriate response would be "Discrete Math 1 (CS 2120) is taught by [Name(s)]. <END RESPONSE>"

When asking a general question about courses, answer the question with all known information.

When discussing specific course(s) in all other scenarios, format the following details like so:
### Course Number: Course Title
- **Credits:**
- **Course Description:**
- **Prerequisites:**
### Course Sections and Instructors
**Main Course Sections:**
- **Section 1**
	- **Days:**
	- **Time:**
	- **Instructor:**
- …
**Lab/Discussion Sections:**
- …
### Instructor Reviews
- [Instructor Name]:
	- Rating:
	- Difficulty:
	- Avg GPA:
### Course Statistics
- **Overall Rating:**
- **Difficulty:**
- **Average GPA:**
- **Workload:**
- Hours per week:
- Homework:
- Reading:
- Writing:
- Group work:
- **Course Quality:**
- Instructor quality:
- Enjoyability:
- Recommendability:
- **Grade Distribution:**
- A+: [percentage] | A: [percentage] | A-: [percentage]
- B+: [percentage] | B: [percentage] | B-: [percentage]
- C+: [percentage] | C: [percentage] | C-: [percentage]
- D/F/W: [percentage]

- Do NOT list **Lab/Discussion Sections:** if there are none (lab sections are 0 credits)
- If an instructor is missing data from reviews, state this clearly
- Do NOT include course information about prerequisites unless explicitly prompted to
- Do NOT say "Based on the information provided" at the beginning of the response.
- DO NOT mention "Clusters" in the response.

When discussing general course information (e.g. "What are some good courses to take?"), limit relevant details to:
- Course title ONLY

{cluster_info}
"""
    
    # Follow-up phrases that should reuse previous context
    FOLLOWUP_PHRASES = [
        "keep going", "continue", "more info", "tell me more", "more", "elaborate",
        "go on", "yes", "yes please", "sure", "ok", "okay", "yeah", "yep",
        "what else", "anything else", "more details", "explain more",
        "and?", "so?", "then?", "more about", "keep talking",
    ]
    
    def __init__(self):
        self.gemini_service = GeminiService()
        self.vector_store = VectorStore()
        self.conversation_history: dict[str, list[dict]] = {}
        # Build the full system prompt with cluster info
        self.SYSTEM_PROMPT = self.SYSTEM_PROMPT_BASE.format(
            cluster_info=get_cluster_summary()
        )
    
    def _is_followup(self, question: str) -> bool:
        """Check if a question is a follow-up request."""
        q_lower = question.lower().strip()
        # Check exact matches
        if q_lower in self.FOLLOWUP_PHRASES:
            return True
        # Check if starts with follow-up phrase
        for phrase in self.FOLLOWUP_PHRASES:
            if q_lower.startswith(phrase):
                return True
        # Very short questions are likely follow-ups
        if len(q_lower.split()) <= 3 and "?" not in q_lower:
            return True
        return False

    QUERY_PROMPT_TEMPLATE = """Use the following information to answer the student's question.

RELEVANT COURSE INFORMATION (from catalog):
{context}

STUDENT QUESTION:
{question}

Provide a helpful, accurate response. For specific course details (instructors, times, descriptions), use the RELEVANT COURSE INFORMATION.
"""
    
    def query(
        self,
        question: str,
        session_id: Optional[str] = None,
        n_results: int = 15,  # Increased from 5 to 10 for better recall
    ) -> dict:
        """Process a user query with RAG.
        
        Args:
            question: User's question
            session_id: Optional session ID for conversation memory
            n_results: Number of documents to retrieve
            
        Returns:
            Dictionary with response and sources
        """
        sources = []
        
        # Check if this is a follow-up - reuse previous context if so
        is_followup = session_id and self._is_followup(question) and session_id in _last_context
        
        if is_followup:
            # Reuse previous context for follow-up questions
            context = _last_context[session_id]
            # Enhance the question to make it clearer
            original_q = _last_query.get(session_id, "")
            question = f"(Follow-up to previous question about '{original_q}'): {question}"
        else:
            # New question - do fresh RAG retrieval
            search_results = self.vector_store.search(query=question, n_results=n_results)
            
            # Format context from retrieved documents
            context_parts = []
            
            for i, doc in enumerate(search_results["documents"]):
                if doc:
                    context_parts.append(f"[Source {i+1}]\n{doc}")
                    
                    # Extract source info from metadata
                    metadata = search_results["metadatas"][i] if search_results["metadatas"] else {}
                    if metadata:
                        source_str = f"{metadata.get('subject', '')} {metadata.get('catalog_number', '')} - {metadata.get('title', '')}"
                        sources.append(source_str)
            
            context = "\n\n".join(context_parts) if context_parts else "No specific course information found."
            
            # Store context for potential follow-ups
            if session_id:
                _last_context[session_id] = context
                _last_query[session_id] = question
        
        # Build the prompt with context
        user_prompt = self.QUERY_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )
        
        # Get response from Gemini (with or without memory)
        if session_id:
            # Use chat with memory
            response = self.gemini_service.get_chat_completion(
                prompt=user_prompt,
                session_id=session_id,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=1000,
            )
        else:
            # Stateless query
            response = self.gemini_service.get_completion(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=1000,
            )
        
        return {
            "response": response,
            "sources": sources,
            "context_used": len(context_parts),
        }
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session's memory.
        
        Args:
            session_id: Session ID to clear
            
        Returns:
            True if cleared, False if didn't exist
        """
        # Clear context cache
        if session_id in _last_context:
            del _last_context[session_id]
        if session_id in _last_query:
            del _last_query[session_id]
        return self.gemini_service.clear_chat_session(session_id)
    
    def query_stream(
        self,
        question: str,
        n_results: int = 10,
    ):
        """Process a user query with RAG and stream the response.
        
        Args:
            question: User's question
            n_results: Number of documents to retrieve
            
        Yields:
            Text chunks as they are generated
        """
        # Retrieve relevant documents
        search_results = self.vector_store.search(query=question, n_results=n_results)
        
        # Format context from retrieved documents
        context_parts = []
        
        for i, doc in enumerate(search_results["documents"]):
            if doc:
                context_parts.append(f"[Source {i+1}]\n{doc}")
        
        context = "\n\n".join(context_parts) if context_parts else "No specific course information found."
        
        # Build the prompt
        user_prompt = self.QUERY_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )
        
        # Stream response from Gemini
        for chunk in self.gemini_service.get_completion_stream(
            prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=1000,
        ):
            yield chunk
    
    def simple_query(self, question: str) -> str:
        """Simple query without RAG (for general questions).
        
        Args:
            question: User's question
            
        Returns:
            Response string
        """
        return self.gemini_service.get_completion(
            prompt=question,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=1000,
        )
    
    def is_course_related(self, question: str) -> bool:
        """Determine if a question is course-related.
        
        Args:
            question: User's question
            
        Returns:
            True if question is about courses
        """
        course_keywords = [
            "course", "class", "credit", "prerequisite", "prereq",
            "schedule", "instructor", "professor", "section",
            "enroll", "registration", "major", "minor", "degree",
            "cs ", "math ", "stat ", "dsa ", "sts ",
            "semester", "spring", "fall", "summer",
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in course_keywords)

