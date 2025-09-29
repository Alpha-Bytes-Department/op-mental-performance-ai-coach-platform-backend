import streamlit as st
import openai
from datetime import datetime
import json
import os
from typing import Dict, List, Any
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


load_dotenv()

# Configure page
st.set_page_config(
    page_title="General Mental Health Chatbot",
    page_icon="🧠",
    layout="wide"
)

class ChatSystem:
    def __init__(self, api_key: str):
        openai.api_key = api_key
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
            if self.index is None:
                dimension = embeddings_array.shape[1]
                self.index = faiss.IndexFlatIP(dimension)
            else:
                # Reset index and add all embeddings
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
                model="gpt-4o",
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def save_session_data(self, filename: str = "general_chat_session.json"):
        """Save conversation history to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
            return f"Session saved to {filename}"
        except Exception as e:
            return f"Error saving session: {str(e)}"
    
    def load_session_data(self, filename: str = "general_chat_session.json"):
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    self.conversation_history = json.load(f)
                
                # Rebuild embeddings and FAISS index
                self.embeddings = []
                for conv in self.conversation_history:
                    embedding = self.model.encode([conv['full_conversation']])
                    self.embeddings.append(embedding[0])
                
                self._update_faiss_index()
                return f"Session loaded from {filename} ({len(self.conversation_history)} conversations)"
            else:
                return "No previous session found."
        except Exception as e:
            return f"Error loading session: {str(e)}"

class GeneralChatSystem(ChatSystem):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.system_prompt = """
        You are a mental health support chatbot following the OP AI Coaching Style Refinement approach. Core principles:
        
        FUNDAMENTAL APPROACH:
        - provide all types of help related to mental health, emotional wellness, depression, anxiety, stress, relationships, self-esteem, motivation, productivity, life transitions, identity, trauma, grief, and more.
        - understand problem clearly and provide solution as early as possible.
        - Use evidence-based techniques from CBT, DBT, ACT,WHO, CDC, AAP, APA guidelines, mindfulness, positive psychology,
        - Serve all ages with age-appropriate guidance
        - Maintain a warm, empathetic, and supportive tone
        - Always prioritize safety - refer to professionals for serious concerns

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
        # Get relevant context
        context = self.get_relevant_context(message)
        context_text = "\n".join([conv['full_conversation'] for conv in context])
        
        age_guidance = {
            "youth": "This user is 17 or younger. Use age-appropriate language and consider guardian involvement for serious concerns.",
            "adult": "This user is 18-39. Use standard adult guidance and resources.",
            "masters": "This user is 40+. Consider comorbidities, life experience, and age-specific challenges."
        }
        
        full_prompt = f"""
        {self.system_prompt}
        
        Age Group Guidance: {age_guidance.get(age_group, age_guidance['adult'])}
        
        Previous conversation context (if any):
        {context_text}
        
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
                model="gpt-4",
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            bot_response = response.choices[0].message.content
            self.add_to_memory(message, bot_response)
            return bot_response
            
        except Exception as e:
            return f"I'm sorry, I'm having trouble connecting right now. Please try again or contact a mental health professional if this is urgent. Error: {str(e)}"

# Initialize session state
def init_session_state():
    if 'api_key' not in st.session_state:
        st.session_state.api_key = os.getenv('OPENAI_API_KEY', '')
    if 'chat_system' not in st.session_state:
        st.session_state.chat_system = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'age_group' not in st.session_state:
        st.session_state.age_group = "adult"

def main():
    init_session_state()
    
    st.title("🧠 General Mental Health Chatbot")
    st.markdown("*Compassionate AI-powered mental health support with OP AI Coaching Style*")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.api_key,
            help="Enter your OpenAI API key or set OPENAI_API_KEY in .env file"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            st.session_state.chat_system = None  # Reset chat system
        
        if not api_key:
            st.warning("⚠️ Please enter your OpenAI API key to start chatting.")
            st.info("💡 You can also set OPENAI_API_KEY in your .env file")
            st.stop()
        
        # Initialize chat system
        if st.session_state.chat_system is None:
            try:
                with st.spinner("Initializing chat system..."):
                    st.session_state.chat_system = GeneralChatSystem(api_key)
                    
                    # Try to load previous session
                    load_msg = st.session_state.chat_system.load_session_data()
                    st.success("✅ Chat system initialized!")
                    if "conversations" in load_msg:
                        st.info(f"📂 {load_msg}")
                    
            except Exception as e:
                st.error(f"❌ Error initializing chat system: {str(e)}")
                st.stop()
        
        st.markdown("---")
        
        # Age group selection
        st.header("👤 User Profile")
        age_group = st.selectbox(
            "Select age group:",
            ["youth", "adult", "masters"],
            index=["youth", "adult", "masters"].index(st.session_state.age_group),
            help="Youth: ≤17 years, Adult: 18-39 years, Masters: 40+ years"
        )
        st.session_state.age_group = age_group
        
        age_descriptions = {
            "youth": "🧒 Age-appropriate guidance with guardian consideration",
            "adult": "🧑 Standard adult mental health support",
            "masters": "🧓 Age-specific support considering life experience"
        }
        st.info(age_descriptions[age_group])
        
        st.markdown("---")
        
        # OP AI Coaching Style Info
        st.header("🎯 OP AI Coaching Style")
        with st.expander("View Coaching Principles"):
            st.markdown("""
            **Key Principles:**
            - One question at a time for natural flow
            - Emotional depth before solutions
            - Collaborative reframing approach
            - Encourage emotion words
            - Objective in interpersonal conflicts
            - Distinguish wellness vs performance language
            - Warm, conversational tone
            """)
        
        st.markdown("---")
        
        # Session management
        st.header("💾 Session Management")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Session", use_container_width=True):
                if st.session_state.chat_system:
                    save_msg = st.session_state.chat_system.save_session_data()
                    st.success(save_msg)
        
        with col2:
            if st.button("📂 Load Session", use_container_width=True):
                if st.session_state.chat_system:
                    load_msg = st.session_state.chat_system.load_session_data()
                    st.info(load_msg)
                    st.rerun()
        
        # Generate summary
        if st.button("📊 Generate Summary", use_container_width=True):
            if st.session_state.chat_system:
                with st.spinner("Generating summary..."):
                    summary = st.session_state.chat_system.generate_summary()
                    st.markdown("### 📋 Chat Summary")
                    st.markdown(summary)
        
        # Clear chat
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.chat_system:
                st.session_state.chat_system.conversation_history = []
                st.session_state.chat_system.embeddings = []
                st.session_state.chat_system.index = None
            st.success("✅ Chat history cleared!")
            st.rerun()
        
        st.markdown("---")
        
        # Crisis resources
        st.header("🆘 Crisis Resources")
        st.markdown("""
        **Emergency:** 911
        
        **Suicide Prevention:** 988
        
        **Crisis Text:** Text HOME to 741741
        
        **SAMHSA Helpline:** 1-800-662-4357
        """)
    
    # Main chat interface
    st.markdown("### 💬 Chat Interface")
    
    # Display conversation statistics
    if st.session_state.chat_system and st.session_state.chat_system.conversation_history:
        total_conversations = len(st.session_state.chat_system.conversation_history)
        st.info(f"📈 Total conversations in memory: {total_conversations}")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Share what's on your mind... I'm here to listen and support you."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking with care..."):
                try:
                    response = st.session_state.chat_system.get_response(prompt, st.session_state.age_group)
                    st.markdown(response)
                    
                    # Add bot response to chat
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"I'm sorry, I encountered an error: {str(e)}. If this is urgent, please contact a mental health professional immediately."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    <small>⚠️ This chatbot provides supportive guidance using OP AI Coaching Style principles but is not a replacement for professional mental health care. 
    In case of emergency, please contact your local emergency services or crisis hotline.</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()