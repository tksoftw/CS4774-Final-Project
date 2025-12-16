"""RAG (Retrieval-Augmented Generation) engine."""

from typing import Optional
from app.services.gemini_service import GeminiService
from app.data.vector_store import VectorStore


class RAGEngine:
    """RAG engine for course-aware AI responses."""
    
    SYSTEM_PROMPT = """You are an AI academic advisor for University of Virginia (UVA) students. 
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

When discussing specific course(s), format the following details like so:
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

- Do NOT list **Lab/Discussion Sections:** if there are none
- If an instructor is missing data from reviews, state this clearly
- Do NOT include course information about prerequisites unless explicitly prompted to

When discussing general course information (e.g. "What are some good courses to take?"), limit relevant details to:
- Course title ONLY
"""

    QUERY_PROMPT_TEMPLATE = """Use the following course information to answer the student's question.

RELEVANT COURSE INFORMATION:
{context}

STUDENT QUESTION:
{question}

Provide a helpful, accurate response based on the course information above. If the information provided doesn't fully answer the question, acknowledge what you know and what you don't.
"""

    def __init__(self):
        self.gemini_service = GeminiService()
        self.vector_store = VectorStore()
        self.conversation_history: dict[str, list[dict]] = {}
    
    def query(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        n_results: int = 10,  # Increased from 5 to 10 for better recall
    ) -> dict:
        """Process a user query with RAG.
        
        Args:
            question: User's question
            conversation_id: Optional ID for conversation context
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
        # Build the prompt
        user_prompt = self.QUERY_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )
        
        # Get response from Gemini
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

