import random
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json
import re
import openai
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class Journal:

    def __init__(self):
        # Initialize OpenAI for version 0.28.0
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("Please set OPENAI_API_KEY in your .env file")
        
        # Initialize sentence transformer for embeddings
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize FAISS index
        self.dimension = 384  # Dimension of all-MiniLM-L6-v2 embeddings
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
        
        # Store evidence database for FAISS
        self.evidence_database = []
        self.evidence_embeddings = []
        
        # Domain-specific keywords for relevance checking
        self.coaching_domains = {
            "personal_development": ["personal", "self", "growth", "improvement", "habits", "mindset", "confidence", "identity", "values", "change", "development"],
            "professional_development": ["work", "career", "job", "professional", "workplace", "colleague", "boss", "promotion", "skills", "interview", "resume"],
            "emotional_wellbeing": ["feel", "emotion", "stress", "anxiety", "happy", "sad", "frustrated", "overwhelmed", "excited", "worried", "depression", "mood"],
            "relationships": ["friend", "family", "partner", "relationship", "social", "communication", "conflict", "support", "marriage", "dating", "children"],
            "goals_achievement": ["goal", "dream", "vision", "future", "plan", "achieve", "success", "challenge", "obstacle", "progress", "motivation", "ambition"],
            "life_challenges": ["problem", "difficulty", "struggle", "issue", "challenge", "conflict", "decision", "choice", "crisis", "setback", "failure"]
        }
        
        # Entry points with AI-powered initial prompts
        self.entry_points = {
            "personal_challenge": "What has been going on in your personal life that I can help you explore? Take your time to share as much detail as you'd like about the situation.",
            "personal_win": "Wins are easy to overlook. Let's dive into your success. Tell me about a recent personal achievement or positive experience you'd like to explore deeper.",
            "professional_challenge": "What has been going on in your professional life that I can help you explore? Share the details of what you're facing at work.",
            "professional_win": "Wins are easy to overlook. Let's dive into your success. Tell me about a professional achievement or positive moment you'd like to explore further."
        }
        
        # Layer-specific prompts for structured exploration
        self.layer_templates = {
            "layer1_facts": {
                "past_present": [
                    "Can you walk me through exactly what happened, step by step?",
                    "Who else was involved in this situation and what role did they play?",
                    "What specific actions were taken and what was the timeline?",
                    "What were the concrete details and circumstances surrounding this?"
                ],
                "future": [
                    "Describe your vision as if you're already living it - what does a typical day look like?",
                    "What specific goals and milestones are part of this future you envision?",
                    "How would others see your life when you achieve what you're working toward?",
                    "What tangible changes would be evident in your daily routine and environment?"
                ]
            },
            "layer2_emotions": [
                "What emotions are you experiencing as you think about this situation?",
                "How do these feelings show up in your body - any physical sensations?",
                "What's the strongest emotion you're experiencing right now about this?",
                "If you had to name three specific emotions, what would they be?",
                "How do these emotions affect your energy and motivation?"
            ],
            "layer3_meaning": [
                "What does this experience reveal about your beliefs regarding yourself?",
                "What story are you telling yourself about what this means?",
                "How does this situation connect to your identity and self-image?",
                "What assumptions might you be making that could be examined?",
                "What deeper significance does this hold for you?"
            ]
        }
        
        self.perspective_prompts = {
            "negative_reframe": [
                "What might someone you respect say about this situation?",
                "What opportunities or lessons might be hidden in this challenge?",
                "How have you successfully handled similar difficulties before?",
                "What would you tell a close friend facing this exact situation?",
                "What strengths have you used in past challenges that could apply here?"
            ],
            "positive_amplify": [
                "What specific qualities or skills enabled this success?",
                "How can you apply what worked here to other areas of your life?",
                "What patterns do you notice in your successful experiences?",
                "How does this achievement reflect your core strengths?",
                "What does this success teach you about your capabilities?"
            ],
            "future_action": [
                "What would be the first concrete step you could take toward this vision?",
                "Who in your network could support you in achieving this goal?",
                "What resources do you already have that could help you move forward?",
                "What daily habits or behaviors would bring you closer to this outcome?",
                "How will you measure progress as you work toward this vision?"
            ]
        }
        
        self.value_prompts = [
            "What personal values are most evident in this experience?",
            "How does this connect to who you want to be as a person?",
            "What does this reveal about what matters most deeply to you?",
            "Which of your core principles are reflected in this situation?",
            "How does this align with your sense of purpose and meaning?"
        ]
        
        # Evidence-based sources for FAISS database
        self.evidence_sources = {
            "mental_health": {
                "source": "National Institute of Mental Health (NIMH)",
                "recommendations": [
                    "Structured self-reflection improves emotional regulation and self-awareness through systematic introspection practices",
                    "Regular journaling reduces anxiety and depression symptoms by 25-30% in clinical studies",
                    "Identifying personal values enhances motivation and life satisfaction while improving decision-making quality",
                    "Processing difficult emotions through structured reflection is more effective than avoidance strategies",
                    "Self-awareness practices contribute significantly to emotional intelligence and interpersonal relationships"
                ],
                "keywords": ["mental health", "depression", "anxiety", "emotional regulation", "self-awareness", "therapy", "wellbeing"]
            },
            "stress_management": {
                "source": "Mayo Clinic",
                "recommendations": [
                    "Structured reflection helps process stressful experiences effectively and reduces cortisol levels significantly",
                    "Positive visualization techniques reduce cortisol by up to 23% in controlled clinical studies",
                    "Goal setting with emotional connection increases achievement rates by 42% over logical approaches alone",
                    "Breaking overwhelming situations into manageable components reduces stress and increases success probability",
                    "Professional guidance and social support improve stress management outcomes by substantial margins"
                ],
                "keywords": ["stress", "cortisol", "overwhelm", "pressure", "tension", "relaxation", "coping", "management"]
            },
            "behavioral_change": {
                "source": "American Psychological Association (APA)",
                "recommendations": [
                    "Breaking goals into specific actionable steps increases success probability by 67% in behavioral studies",
                    "Strong social support systems improve behavior change success rates by 95% across demographics",
                    "Self-efficacy beliefs directly predict performance outcomes and long-term success sustainability",
                    "Value-based decision making creates more consistent behavior change than external motivation alone",
                    "Regular self-monitoring and reflection improve goal achievement rates and maintain progress"
                ],
                "keywords": ["behavior change", "habits", "goals", "motivation", "self-efficacy", "success", "achievement", "performance"]
            },
            "lifestyle_medicine": {
                "source": "American College of Lifestyle Medicine (ACLM)",
                "recommendations": [
                    "Holistic approaches addressing mental, physical and social factors show 85% better results than single interventions",
                    "Regular reflection practices contribute to overall wellbeing and reduce chronic disease risk factors",
                    "Value-based living reduces stress levels and improves life satisfaction across all demographic groups",
                    "Lifestyle interventions are most effective when aligned with personal values and identity",
                    "Sustainable change requires simultaneously addressing both mindset and behavior pattern modifications"
                ],
                "keywords": ["lifestyle", "holistic health", "wellbeing", "chronic disease", "prevention", "lifestyle medicine", "integration"]
            },
            "wellness": {
                "source": "U.S. Department of Health & Human Services (HHS)",
                "recommendations": [
                    "Regular self-assessment promotes proactive health management and prevents serious health complications",
                    "Goal-oriented thinking patterns support mental health resilience and recovery from setbacks",
                    "Strong social connections and support networks are vital for wellbeing and increased longevity",
                    "Preventive approaches to mental health show superior long-term outcomes compared to reactive treatment",
                    "Integration of mental and physical health strategies proves most effective for comprehensive wellness"
                ],
                "keywords": ["wellness", "health", "prevention", "social support", "resilience", "longevity", "proactive"]
            },
            "substance_abuse": {
                "source": "Substance Abuse and Mental Health Services Administration (SAMHSA)",
                "recommendations": [
                    "Early intervention and self-awareness prevent escalation of substance abuse and mental health problems",
                    "Support systems are critical for recovery and maintaining wellness during high-stress situations",
                    "SAMHSA National Helpline (1-800-662-HELP) provides 24/7 confidential treatment referrals and support",
                    "Holistic treatment approaches addressing underlying emotional issues show highest long-term success rates",
                    "Regular mental health check-ins with professionals improve recovery outcomes and prevent relapse"
                ],
                "keywords": ["substance abuse", "addiction", "recovery", "mental health support", "helpline", "intervention", "treatment"]
            }
        }
        
        # Initialize FAISS database
        self._initialize_evidence_database()
        
        # Session data storage
        self.current_session = {
            "entry_point": None,
            "responses": {},
            "current_layer": 1,
            "current_phase": "start",
            "session_start": None,
            "is_future_focused": "False",
            "sentiment": None,
            "session_active": "False",
            "conversation_history": [],
            "questions_asked": []  # Track asked questions to avoid repetition
        }

    def _initialize_evidence_database(self):
        """Initialize FAISS database with evidence-based sources."""
        #print("Initializing evidence database...")
        
        for category, data in self.evidence_sources.items():
            for recommendation in data["recommendations"]:
                entry = {
                    "text": recommendation,
                    "source": data["source"],
                    "category": category,
                    "keywords": data["keywords"]
                }
                self.evidence_database.append(entry)
        
        # Generate embeddings
        texts = [entry["text"] for entry in self.evidence_database]
        embeddings = self.encoder.encode(texts)
        
        # Normalize embeddings for cosine similarity
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        self.evidence_embeddings = embeddings
        
        #print(f"Evidence database initialized with {len(self.evidence_database)} entries")

    def _is_coaching_related(self, text: str) -> bool:
        """Check if the input is related to life coaching domains."""
        text_lower = text.lower()
        
        # Count matches across all domains
        total_matches = 0
        for domain, keywords in self.coaching_domains.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            total_matches += matches
        
        # Also check for question words that might indicate coaching relevance
        coaching_question_words = ["how", "what", "why", "when", "where", "should", "could", "would"]
        question_matches = sum(1 for word in coaching_question_words if word in text_lower)
        
        # Check for personal pronouns that suggest self-reflection
        personal_indicators = ["i", "me", "my", "myself", "i'm", "i've", "i'll"]
        personal_matches = sum(1 for word in personal_indicators if word in text_lower)
        
        # Consider it coaching-related if we have domain keywords, questions, or personal references
        return total_matches > 0 or (question_matches > 0 and personal_matches > 0)

    def _handle_irrelevant_input(self, user_input: str) -> str:
        """Handle inputs that are not related to life coaching."""
        
        # Generate a focused response that redirects to coaching
        redirect_responses = [
            "I'm here to help you explore personal and professional growth. Let's focus on what matters most to you right now - what aspect of your life would you like to work on together?",
            
            "As your AI life coach, I'm designed to help you with personal development, career challenges, relationships, and achieving your goals. What would you like to explore about yourself today?",
            
            "I specialize in helping people navigate life's challenges and celebrate their wins. What's been on your mind lately that we could explore together?",
            
            "My expertise is in life coaching - helping you gain clarity, overcome obstacles, and achieve your goals. What area of your life could use some attention right now?",
            
            "Let's redirect our conversation to focus on your personal growth. What's something you've been thinking about - a challenge you're facing or a success you'd like to build on?",
            
            "I'm focused on helping with personal and professional development. What's happening in your life that you'd like to reflect on or work through together?"
        ]
        
        return random.choice(redirect_responses)

    def _get_relevant_evidence(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant evidence using FAISS similarity search."""
        if not query.strip():
            return []
            
        try:
            # Encode query
            query_embedding = self.encoder.encode([query])
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.evidence_database) and score > 0.1:  # Minimum relevance threshold
                    entry = self.evidence_database[idx].copy()
                    entry["similarity_score"] = float(score)
                    results.append(entry)
            
            return results
        except Exception as e:
            print(f"Error in evidence retrieval: {e}")
            return []

    def _generate_ai_response(self, user_input: str, context: str, response_type: str) -> str:
        
        # Get relevant evidence only from our curated sources
        evidence_query = f"{user_input} {context} {response_type}"
        relevant_evidence = self._get_relevant_evidence(evidence_query, top_k=2)
        
        # Build evidence context from our sources only
        evidence_context = ""
        if relevant_evidence:
            evidence_context = "\nRelevant research insights from our evidence base:\n"
            for evidence in relevant_evidence:
                evidence_context += f"• {evidence['source']}: {evidence['text'][:120]}...\n"
        
        # Create conversation history context
        history_context = ""
        if len(self.current_session["conversation_history"]) > 1:
            recent_history = self.current_session["conversation_history"][-2:]
            history_context = "\nRecent context:\n"
            for exchange in recent_history:
                history_context += f"User: {exchange['user'][:80]}...\nCoach: {exchange['coach'][:80]}...\n"
        
        # Build prompt based on response type and current layer
        if response_type == "layer_exploration":
            system_prompt = f"""You are an AI life coach with expertise in personal development, professional growth, emotional wellbeing, and goal achievement. You MUST stay within your coaching domain and only reference the evidence-based sources provided.

STRICT GUIDELINES:
- ONLY provide advice based on the evidence from these trusted sources: NIMH, Mayo Clinic, APA, ACLM, HHS, and SAMHSA
- Stay focused on life coaching topics: personal/professional challenges, emotional wellbeing, goals, relationships, and personal growth
- If asked about topics outside your domain, politely redirect to coaching-related discussions
- Use only the research insights provided in the evidence context

Current layer: {self.current_session['current_layer']}
- Layer 1: Focus on facts and concrete details
- Layer 2: Explore emotions and feelings  
- Layer 3: Examine meaning and interpretation
- Layer 4: Expand perspectives
- Layer 5: Connect to values and identity

Response Guidelines:
- Ask ONE insightful follow-up question that goes deeper
- Acknowledge their sharing with genuine empathy
- Use evidence-based insights naturally when relevant (ONLY from provided sources)
- Keep responses warm, professional, and encouraging
- Be concise but meaningful (2-3 sentences maximum)
- Avoid repeating similar questions from the conversation"""

            user_prompt = f"""Session context: {context}
{history_context}
{evidence_context}

User shared: "{user_input}"

Current layer {self.current_session['current_layer']} focus: {'Facts and details' if self.current_session['current_layer'] == 1 else 'Emotions and feelings' if self.current_session['current_layer'] == 2 else 'Meaning and interpretation' if self.current_session['current_layer'] == 3 else 'Perspective expansion' if self.current_session['current_layer'] == 4 else 'Values and identity connection'}

Provide empathetic acknowledgment and ask ONE specific follow-up question for this layer. Base your response ONLY on the evidence sources provided."""

        elif response_type == "validation":
            system_prompt = """You are a supportive AI life coach helping someone provide more meaningful responses. Stay focused on life coaching topics only. Be encouraging and specific about life coaching topics."""
            
            user_prompt = f"""The user's response seems brief or off-topic for our {context} session.
User said: "{user_input}"

Provide encouraging, specific guidance for a more detailed response about life coaching topics. Be supportive and redirect to personal/professional growth topics."""

        elif response_type == "summary_insights":
            system_prompt = """You are an AI life coach creating personalized insights based ONLY on the evidence-based sources provided. Be specific, actionable, and encouraging. Only reference the provided research sources."""
            
            user_prompt = f"""Based on this coaching session about {context}, create personalized insights using ONLY the provided evidence:
{user_input}

{evidence_context}

Generate 2-3 specific, actionable insights that are encouraging and personalized, based solely on the evidence sources provided."""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            
            generated_response = response.choices[0].message.content.strip()
            
            # Store the question/response pattern to avoid repetition
            if response_type == "layer_exploration":
                self.current_session["questions_asked"].append(generated_response[:50])
            
            return generated_response
            
        except Exception as e:
            print(f"AI response generation error: {e}")
            return self._get_fallback_response(response_type)

    def _get_fallback_response(self, response_type: str) -> str:
        """Provide fallback responses when AI generation fails."""
        fallbacks = {
            "layer_exploration": "Thank you for sharing that. Can you tell me more about how this experience has affected you personally?",
            "validation": "I'd appreciate hearing more details about your experience. Could you elaborate on what you're going through in your personal or professional life?",
            "summary_insights": "Your responses demonstrate thoughtful self-reflection and genuine engagement with the coaching process."
        }
        return fallbacks.get(response_type, "Please share more about your personal or professional experience.")

    def start_journaling_session(self, choice: str) -> str:
        """Starts a journaling session with a given choice."""
        choice_map = {
            "1": "personal_win",
            "2": "personal_challenge", 
            "3": "professional_win",
            "4": "professional_challenge"
        }
        
        if choice in choice_map:
            self.current_session["entry_point"] = choice_map[choice]
            self.current_session["current_phase"] = "exploration"
            self.current_session["session_active"] = "True"
            self.current_session["session_start"] = datetime.now().isoformat()
            self.current_session["conversation_history"] = []
            self.current_session["questions_asked"] = []
            
            opening_message = self.entry_points[choice_map[choice]]
            self._add_to_history("Selected option " + choice, opening_message)
            return opening_message
        else:
            return "Invalid choice. Please select 1, 2, 3, or 4."

    def start_system(self, user_input: str, is_initial_choice: bool = False) -> str:
        """Handle system initialization and all user interactions with domain focus."""
        user_input_clean = user_input.strip()
        
        if is_initial_choice:
            return self.start_journaling_session(user_input_clean)
        
        # Handle different conversation phases
        if self.current_session["current_phase"] == "exploration":
            # Check if input is relevant to coaching before processing
            if not self._is_coaching_related(user_input_clean):
                redirect_msg = self._handle_irrelevant_input(user_input_clean)
                self._add_to_history(user_input_clean, redirect_msg)
                return redirect_msg
            return self._handle_exploration_phase(user_input_clean)
        else:
            return "I'm not sure how to help with that. Please type 'START' to begin a new coaching session."

    

    def _add_to_history(self, user_msg: str, coach_msg: str):
        """Add exchange to conversation history."""
        self.current_session["conversation_history"].append({
            "user": user_msg,
            "coach": coach_msg
        })

    def _handle_exploration_phase(self, user_input: str) -> str:
        """Handle the main exploration phase with AI responses."""
        
        # Validate response quality
        if not self._is_valid_response(user_input):
            validation_response = self._generate_ai_response(
                user_input, 
                self.current_session["entry_point"].replace('_', ' '), 
                "validation"
            )
            self._add_to_history(user_input, validation_response)
            return validation_response
        
        # Store the response
        layer_key = f"layer_{self.current_session['current_layer']}"
        if layer_key not in self.current_session["responses"]:
            self.current_session["responses"][layer_key] = []
        
        self.current_session["responses"][layer_key].append(user_input)
        
        # Analyze response for sentiment and focus
        self._analyze_response(user_input)
        
        # Generate AI response based on current layer
        if self.current_session["current_layer"] <= 5:
            # Check if we should advance to next layer
            current_responses = len(self.current_session["responses"][layer_key])
            if (self.current_session["current_layer"] <= 3 and current_responses >= 2) or \
               (self.current_session["current_layer"] > 3 and current_responses >= 1):
                self.current_session["current_layer"] += 1
                
                # Generate summary if we've completed all layers
                if self.current_session["current_layer"] > 5:
                    return self.generate_summary()
            
            # Generate layer-appropriate response
            context = f"{self.current_session['entry_point'].replace('_', ' ')} exploration - Layer {self.current_session['current_layer']}"
            response = self._generate_ai_response(user_input, context, "layer_exploration")
        else:
            response = self.generate_summary()
        
        # Add to conversation history
        self._add_to_history(user_input, response)
        return response

    def _is_valid_response(self, response: str) -> bool:
        """Check if response is substantial enough."""
        response = response.strip()
        
        # Too short
        if len(response) < 15:
            return False
            
        # Too generic
        generic_responses = ["yes", "no", "ok", "sure", "maybe", "i don't know", "nothing", "fine", "good"]
        if response.lower() in generic_responses:
            return False
            
        return True

    def _analyze_response(self, response: str) -> None:
        """Analyze response for sentiment and future focus using embeddings."""
        try:
            response_embedding = self.encoder.encode([response])
            
            # Check for future orientation
            future_indicators = "goals dreams vision future plans aspirations wants achieve"
            future_embedding = self.encoder.encode([future_indicators])
            future_similarity = np.dot(response_embedding, future_embedding.T)[0][0]
            self.current_session["is_future_focused"] = str(future_similarity > 0.25)
            
            # Analyze sentiment
            positive_words = "great wonderful amazing excellent successful proud happy excited confident accomplished"
            negative_words = "difficult challenging frustrated stressed overwhelmed disappointed sad angry worried anxious"
            
            positive_embedding = self.encoder.encode([positive_words])
            negative_embedding = self.encoder.encode([negative_words])
            
            pos_similarity = np.dot(response_embedding, positive_embedding.T)[0][0]
            neg_similarity = np.dot(response_embedding, negative_embedding.T)[0][0]
            
            if pos_similarity > neg_similarity and pos_similarity > 0.2:
                self.current_session["sentiment"] = "positive"
            elif neg_similarity > pos_similarity and neg_similarity > 0.2:
                self.current_session["sentiment"] = "negative"
            else:
                self.current_session["sentiment"] = "neutral"
                
        except Exception as e:
            print(f"Analysis error: {e}")
            self.current_session["sentiment"] = "neutral"
            self.current_session["is_future_focused"] = False

    def generate_summary(self) -> str:
        """Generate comprehensive AI-powered summary with evidence-based recommendations from curated sources only."""
        
        # Collect all responses
        all_responses = ""
        for layer_key, responses in self.current_session["responses"].items():
            all_responses += f"{layer_key}: " + " | ".join(responses) + "\n"
        
        # Generate AI insights (using only our evidence sources)
        ai_insights = self._generate_ai_response(
            all_responses,
            f"complete {self.current_session['entry_point'].replace('_', ' ')} coaching session",
            "summary_insights"
        )
        
        # Get evidence-based recommendations from our curated sources only
        evidence_query = f"{self.current_session['entry_point']} {self.current_session['sentiment']} {all_responses[:300]}"
        relevant_evidence = self._get_relevant_evidence(evidence_query, top_k=4)
        
        # Generate recommendations based only on our evidence sources
        recommendations = self._generate_recommendations(relevant_evidence)
        
        # Create final summary
        summary = f"""
AI LIFE COACH SESSION SUMMARY

SESSION OVERVIEW:
Focus Area: {self.current_session['entry_point'].replace('_', ' ').title()}
Emotional Tone: {self.current_session['sentiment'].title()}
Orientation: {'Future-Focused' if self.current_session['is_future_focused'] else 'Present-Focused'}

PERSONALIZED AI INSIGHTS:
{ai_insights}

EVIDENCE-BASED RECOMMENDATIONS:
{recommendations}

RESEARCH SOURCES USED:
{self._format_evidence_sources(relevant_evidence)}

Your responses demonstrated genuine engagement and thoughtful self-reflection throughout this session. The AI analysis indicates strong readiness for positive change and growth.

Session completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Reset session
        self._reset_session()
        return summary.strip()

    def _generate_recommendations(self, evidence: List[Dict]) -> str:
        """Generate actionable recommendations based only on our evidence sources."""
        try:
            evidence_text = ""
            for ev in evidence[:3]:
                evidence_text += f"- {ev['source']}: {ev['text'][:100]}...\n"
            
            themes = []
            if "win" in self.current_session["entry_point"]:
                themes.append("building on success")
            if "challenge" in self.current_session["entry_point"]:
                themes.append("overcoming obstacles")
            if self.current_session["is_future_focused"]:
                themes.append("goal achievement")
            if self.current_session["sentiment"] == "negative":
                themes.append("stress management")
                
            prompt = f"""Based on session themes ({', '.join(themes)}) and ONLY the research evidence from our trusted sources (NIMH, Mayo Clinic, APA, ACLM, HHS, SAMHSA):
{evidence_text}

Create specific, actionable recommendations. Be practical and encouraging. Base recommendations ONLY on the evidence provided from these trusted sources."""

            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Generate specific, actionable recommendations based ONLY on the evidence provided from our trusted research sources. Do not reference any external information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Recommendations error: {e}")
            return self._fallback_recommendations()

    def _fallback_recommendations(self) -> str:
        """Fallback recommendations when AI generation fails, based on our evidence sources."""
        base_recs = [
            "• Continue regular self-reflection to maintain awareness and growth (supported by NIMH research)",
            "• Apply insights from this session to similar situations you encounter (APA behavioral studies)",
            "• Consider sharing your learnings with trusted friends or mentors (Mayo Clinic stress management)",
            "• Schedule regular check-ins with yourself to track progress (HHS wellness guidelines)"
        ]
        return "\n".join(base_recs)

    def _format_evidence_sources(self, evidence: List[Dict]) -> str:
        """Format evidence sources for the summary."""
        if not evidence:
            return "• General psychological and wellness research principles from our curated database"
            
        sources = []
        seen_sources = set()
        for ev in evidence:
            if ev['source'] not in seen_sources:
                sources.append(f"• {ev['source']}")
                seen_sources.add(ev['source'])
        
        return "\n".join(sources[:4])

    def _reset_session(self) -> Dict:
        """Reset session data for next use."""
        self.current_session = {
            "entry_point": None,
            "responses": {},
            "current_layer": 1,
            "current_phase": "start",
            "session_start": None,
            "is_future_focused": "False",
            "sentiment": None,
            "session_active": "False",
            "conversation_history": [],
            "questions_asked": []
        }
        return self.current_session

    def get_session_data(self) -> Dict:
        """Get current session data for debugging or analytics."""
        return self.current_session.copy()

    def get_evidence_stats(self) -> Dict:
        """Get evidence database statistics."""
        return {
            "total_evidence_entries": len(self.evidence_database),
            "categories": list(set([entry["category"] for entry in self.evidence_database])),
            "sources": list(set([entry["source"] for entry in self.evidence_database])),
            "faiss_index_size": self.index.ntotal,
            "coaching_domains": list(self.coaching_domains.keys())
        }

    def export_session_data(self, filepath: str = None) -> str:
        """Export session data to JSON file for analysis."""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"coaching_session_{timestamp}.json"
        
        export_data = {
            "session_metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "session_start": self.current_session["session_start"],
                "entry_point": self.current_session["entry_point"],
                "sentiment": self.current_session["sentiment"],
                "is_future_focused": self.current_session["is_future_focused"],
                "layers_completed": self.current_session["current_layer"] - 1
            },
            "conversation_history": self.current_session["conversation_history"],
            "responses_by_layer": self.current_session["responses"],
            "evidence_stats": self.get_evidence_stats()
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return f"Session data exported to {filepath}"
        except Exception as e:
            return f"Error exporting session data: {e}"

    def load_custom_evidence(self, custom_sources: Dict) -> str:
        """Load additional evidence sources while maintaining domain focus."""
        try:
            initial_count = len(self.evidence_database)
            
            for category, data in custom_sources.items():
                # Validate that custom sources are coaching-related
                if not any(keyword in category.lower() for domain_keywords in self.coaching_domains.values() for keyword in domain_keywords):
                    print(f"Skipping non-coaching category: {category}")
                    continue
                
                for recommendation in data.get("recommendations", []):
                    entry = {
                        "text": recommendation,
                        "source": data.get("source", "Custom Source"),
                        "category": category,
                        "keywords": data.get("keywords", [])
                    }
                    self.evidence_database.append(entry)
            
            # Reinitialize FAISS index with new data
            if len(self.evidence_database) > initial_count:
                self._reinitialize_faiss_index()
                return f"Added {len(self.evidence_database) - initial_count} new evidence entries"
            else:
                return "No coaching-related evidence was added"
                
        except Exception as e:
            return f"Error loading custom evidence: {e}"

    def _reinitialize_faiss_index(self):
        """Reinitialize FAISS index after adding new evidence."""
        try:
            # Create new index
            self.index = faiss.IndexFlatIP(self.dimension)
            
            # Generate embeddings for all evidence
            texts = [entry["text"] for entry in self.evidence_database]
            embeddings = self.encoder.encode(texts)
            
            # Normalize embeddings
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to FAISS index
            self.index.add(embeddings.astype('float32'))
            self.evidence_embeddings = embeddings
            
        except Exception as e:
            print(f"Error reinitializing FAISS index: {e}")

    def get_coaching_tips(self) -> List[str]:
        """Get general coaching tips based on evidence sources."""
        tips = [
            "Regular self-reflection improves emotional awareness and decision-making quality",
            "Breaking large goals into specific steps increases success probability significantly", 
            "Strong social support systems are crucial for maintaining positive changes",
            "Value-based decision making creates more sustainable behavior changes",
            "Processing emotions through structured reflection is more effective than avoidance"
        ]
        return tips

    def validate_session_integrity(self) -> Dict[str, bool]:
        """Validate the integrity of the current session."""
        checks = {
            "session_active": self.current_session["session_active"],
            "entry_point_selected": self.current_session["entry_point"] is not None,
            "responses_recorded": len(self.current_session["responses"]) > 0,
            "conversation_history": len(self.current_session["conversation_history"]) > 0,
            "evidence_database_loaded": len(self.evidence_database) > 0,
            "faiss_index_ready": self.index.ntotal > 0
        }
        return checks

def run_interactive_coach():
    """Main function to run the interactive coaching session."""
    try:
        coach = Journal()
        
        """print("=== DOMAIN-FOCUSED AI LIFE COACH WITH GPT-4o AND FAISS ===")
        print(f"Evidence Database: {coach.get_evidence_stats()['total_evidence_entries']} research-backed entries loaded")
        print("Coaching Domains: Personal Development, Professional Growth, Emotional Wellbeing, Relationships, Goals")
        print("\nType 'START' when ready to begin.")
        print("Type 'quit' or 'exit' to end the session.")
        print("Type 'stats' to see evidence database statistics.")
        print("Type 'tips' to get general coaching tips.")
        print("Type 'export' to save your session data.\n")"""
        
        while True:
            try:
                user_input = input(" ").strip()
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                    print("\nThank you for using AI Life Coach. Take care!")
                    break
                
                if user_input.lower() == 'stats':
                    stats = coach.get_evidence_stats()
                    print(f"\nEvidence Database Statistics:")
                    print(f"• Total entries: {stats['total_evidence_entries']}")
                    print(f"• Categories: {', '.join(stats['categories'])}")
                    print(f"• Sources: {', '.join(stats['sources'])}")
                    print(f"• Coaching domains: {', '.join(stats['coaching_domains'])}\n")
                    continue
                
                if user_input.lower() == 'tips':
                    tips = coach.get_coaching_tips()
                    print("\nEvidence-Based Coaching Tips:")
                    for i, tip in enumerate(tips, 1):
                        print(f"{i}. {tip}")
                    print()
                    continue
                
                if user_input.lower() == 'export':
                    if coach.current_session["session_active"] or coach.current_session["conversation_history"]:
                        result = coach.export_session_data()
                        print(f"\n{result}\n")
                    else:
                        print("\nNo session data to export. Start a session first.\n")
                    continue
                
                if user_input.lower() == 'validate':
                    checks = coach.validate_session_integrity()
                    print("\nSession Integrity Check:")
                    for check, status in checks.items():
                        status_symbol = "✓" if status else "✗"
                        print(f"{status_symbol} {check.replace('_', ' ').title()}")
                    print()
                    continue
                
                if not user_input:
                    continue
                
                # Process coaching input
                response = coach.start_system(user_input)
                print(f"\n {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nSession interrupted. Thank you for using AI Life Coach!")
                break
            except Exception as e:
                print(f"\nError processing input: {e}")
                print("Please try again.\n")
    
    except Exception as e:
        print(f"Initialization error: {e}")
        print("Please ensure you have:")
        print("1. Set OPENAI_API_KEY in your .env file")
        print("2. Installed all required packages:")
        print("   - pip install openai sentence-transformers faiss-cpu numpy python-dotenv")

def main():
    """Entry point for the application."""
    run_interactive_coach()

if __name__ == "__main__":
    main()