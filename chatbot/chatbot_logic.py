import openai
from datetime import datetime
import json
import os
from typing import Dict, List, Any
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from knowledge_base.services import query_knowledge

from django.conf import settings

# It's better to handle configuration in Django's settings.py
# For now, we load it here for simplicity.
class ChatSystem:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.conversation_history = []
        self.embeddings = []
        self.index = None
        
    def add_to_memory(self, message: str, response: str):
        """Add conversation to memory with embeddings"""
        conversation = f"User: {message}\nBot: {response}"
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "bot_response": response,
            "full_conversation": conversation
        })
        
        # Create embedding
        embedding = self.model.encode([conversation])
        self.embeddings.append(embedding[0])
        
        # Update FAISS index
        self._update_faiss_index()
    
    def _update_faiss_index(self):
        """Update FAISS index with new embeddings"""
        if len(self.embeddings) > 0:
            embeddings_array = np.array(self.embeddings).astype('float32')
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(embeddings_array)
    
    def get_relevant_context(self, query: str, top_k: int = 3) -> List[Dict]:
        if self.index is None or len(self.conversation_history) == 0:
            return []
        
        query_embedding = self.model.encode([query]).astype('float32')
        scores, indices = self.index.search(query_embedding, min(top_k, len(self.conversation_history)))
        
        relevant_context = []
        for i, idx in enumerate(indices[0]):
            if scores[0][i] > 0.3:  # Threshold for relevance
                relevant_context.append(self.conversation_history[idx])
        
        return relevant_context
    
    def generate_summary(self) -> str:
        if not self.conversation_history:
            return "No conversations to summarize yet."
        
        conversations_text = "\n\n".join([
            f"Conversation {i+1}:\n{conv['full_conversation']}" 
            for i, conv in enumerate(self.conversation_history[-10:])  # Last 10 conversations
        ])
        
        summary_prompt = f"""
        Please provide a comprehensive summary of these mental health conversations:

        {conversations_text}

        Include:
        1. Main topics discussed
        2. Key emotional themes
        3. Progress or patterns observed
        4. Areas of focus or concern

        Keep it concise but informative.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def load_history(self, history: List[Dict]):
        """Load conversation history from a list of dicts (e.g., from a database)."""
        self.conversation_history = history
        self.embeddings = []
        if self.conversation_history:
            for conv in self.conversation_history:
                embedding = self.model.encode([conv['full_conversation']])
                self.embeddings.append(embedding[0])
            self._update_faiss_index()


class GeneralChatSystem(ChatSystem):
    def __init__(self):
        super().__init__()
        self.system_prompt = """
        You are a compassionate mental health support chatbot following the OP AI Coaching Style Refinement approach. Core principles: 
        
        FUNDAMENTAL APPROACH:
        - Serve all ages with age-appropriate guidance
        - Use evidence-based information from WHO, CDC, AAP, APA guidelines
        - Maintain a warm, empathetic, and supportive tone
        - Always prioritize safety - refer to professionals for serious concerns
        
        OP AI COACHING STYLE REFINEMENTS:
        
        1. NO QUESTION STACKING:
        - Ask ONLY ONE question at a time to maintain conversational flow
        - Avoid multiple questions in a single response
        - Create organic, human-like dialogue
        
        2. INCREASED CONVERSATIONAL FLOW:
        - Foster warmth and presence in responses
        - Sound organic and rooted in lived emotional experience
        - Avoid clinical or scripted language
        
        3. EMOTIONAL DEPTH FIRST, NOT SOLUTIONS:
        - Explore emotional and relational experiences FULLY before offering strategies
        - Validate and understand feelings before moving to reframing or solutions
        - Sit with the person's emotional experience
        
        4. COLLABORATIVE REFRAMING:
        - Use collaborative inquiry to help users shape their own reframes
        - Example: "What would it sound like to remind yourself of your worth?"
        - Avoid supplying prewritten interventions
        
        5. PERSONAL LANGUAGE AND OWNERSHIP:
        - All tools and statements must reflect the user's own words, values, and tone
        - Make reframes believable and emotionally resonant to the individual
        - Help them find their own voice and solutions
        
        6. ENCOURAGE EMOTION WORDS:
        - When users describe situations without emotion words, gently encourage them to identify feelings
        - Help expand emotional vocabulary and literacy
        - Example: "What emotions are coming up for you as you share this?"
        
        7. OBJECTIVITY IN INTERPERSONAL CONFLICT:
        - Be thoughtful and supportive but remain objective
        - Avoid being overly one-sided in relational conflicts
        - Help users reflect on their own actions and contributions
        - Balance validation with gentle accountability
        
        8. DUAL LANGUAGE RECOGNITION:
        
        MENTAL WELLNESS LANGUAGE (emotional distress, identity pain, overwhelm):
        - Signals: "I feel stuck," "I can't handle this," "I don't feel like myself"
        - Focus: Validate pain, expand emotional literacy, reduce shame, promote regulation
        
        MENTAL PERFORMANCE LANGUAGE (growth focus, motivation challenges, ambition blocks):
        - Signals: "I want to be more consistent," "I keep getting in my own way"
        - Focus: Build structure, develop systems, clarify goals, strengthen self-belief
        
        APPROACH: Always explore emotional foundations before introducing performance techniques when both are present.
        
        CRISIS PROTOCOL:
        If someone mentions self-harm, suicide, or urgent crisis, immediately provide crisis resources:
        - National Suicide Prevention Lifeline: 988 (US)
        - Crisis Text Line: Text HOME to 741741
        - Emergency Services: 911
        """
    
    def get_response(self, message: str, age_group: str = "adult") -> str:
        # Get relevant context from existing history
        context = self.get_relevant_context(message)
        context_text = "\n".join([conv['full_conversation'] for conv in context])
        
        age_guidance = {
            "youth": "This user is 17 or younger. Use age-appropriate language and consider guardian involvement for serious concerns.",
            "adult": "This user is 18-39. Use standard adult guidance and resources.",
            "masters": "This user is 40+. Consider comorbidities, life experience, and age-specific challenges."
        }

        ##############################################################
        # Retrieve relevant context from the knowledge base using the RAG pipeline
        evidence_context = ""
        retrieved = query_knowledge(message, domain="general")
        if retrieved:
            evidence_context = "\nRetrieved Insights:\n" + "\n".join(
                [f"- {doc['title']}: {doc['text'][:120]}..." for doc in retrieved]
            )
        ###############################################################

        # ✅ ADDED evidence_context into full_prompt
        full_prompt = f"""
        {self.system_prompt}
        
        Age Group Guidance: {age_guidance.get(age_group, age_guidance['adult'])}
        
        Previous conversation context (if any):
        {context_text}
        
        Retrieved knowledge (from your knowledge base):
        {evidence_context}
        
        Current message: {message}
        
        Remember the OP AI Coaching Style:
        - Ask only ONE question maximum. don't ask lots of questions, give solution as early as possible. 
        - Explore emotions before solutions
        - Use collaborative language
        - Encourage emotion words if the user isn't using them
        - Remain objective in interpersonal conflicts
        - Distinguish between wellness vs performance language
        - Make responses sound warm and conversational, not clinical
        
        Respond with empathy and appropriate guidance. If you detect any crisis indicators, prioritize safety resources.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            bot_response = response.choices[0].message.content
            # The view will be responsible for saving the conversation now
            # self.add_to_memory(message, bot_response) 
            return bot_response
            
        except Exception as e:
            return f"I'm sorry, I'm having trouble connecting right now. Please try again or contact a mental health professional if this is urgent. Error: {str(e)}"
