"""RAG (Retrieval-Augmented Generation) engine."""

from typing import Optional
from app.services.gemini_service import GeminiService
from app.data.vector_store import VectorStore
from app.config import get_cluster_summary


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
- Try to limit your responses to a length of around 1-2 paragraphs.

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
    
    def __init__(self):
        self.gemini_service = GeminiService()
        self.vector_store = VectorStore()
        self.conversation_history: dict[str, list[dict]] = {}
        # Build the full system prompt with cluster info
        self.SYSTEM_PROMPT = self.SYSTEM_PROMPT_BASE.format(
            cluster_info=get_cluster_summary()
        )

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
        # Retrieve relevant documents
        search_results = self.vector_store.search(query=question, n_results=n_results)
        
        # Format context from retrieved documents
        context_parts = []
        sources = []
        
        for i, doc in enumerate(search_results["documents"]):
            if doc:
                context_parts.append(f"[Source {i+1}]\n{doc}")
                
                # Extract source info from metadata
                metadata = search_results["metadatas"][i] if search_results["metadatas"] else {}
                if metadata:
                    source_str = f"{metadata.get('subject', '')} {metadata.get('catalog_number', '')} - {metadata.get('title', '')}"
                    sources.append(source_str)
        
        context = "\n\n".join(context_parts) if context_parts else "No specific course information found."
        # Build the prompt with context + degree requirements
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

