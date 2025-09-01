import openai
from datetime import datetime
import os
from dotenv import load_dotenv
import faiss
import numpy as np
import json
import pickle
from typing import List, Dict, Any
import time

load_dotenv()

class MindsetCoachWithMemory:
    def __init__(self, api_key: str = None):
        if not api_key:
            raise ValueError("OpenAI API key is required. Please add OPENAI_API_KEY to your .env file.")
        
        openai.api_key = api_key
        
        # Core session variables
        self.conversation_history = []
        self.current_step = 1
        self.current_question = 1
        self.session_started = False
        self.session_id = f"session_{int(time.time())}"
        
        # User responses storage
        self.user_responses = {
            'circumstances': [],
            'control_analysis': '',
            'letting_go': '',
            'positivity_insights': [],
            'past_ineffective_patterns': [],
            'challenge_overcome': '',
            'personal_mantra': '',
            'final_statement': ''
        }
        
        # FAISS memory system for current session
        self.memory_index = None
        self.memory_texts = []
        self.memory_metadata = []
        self.embedding_dim = 1536  
        
        # Initialize memory system
        self.setup_memory_system()
        
        # Simplified step configurations with easier validation
        self.step_configs = {
            1: {
                'title': 'Accept the Circumstances',
                'questions': [
                    "What challenging circumstances are you currently facing that you need to accept?",
                    "What aspects of this situation are within your control vs. outside your control?",
                    "What worst-case scenarios do you replay in your mind that prevent you from taking action?"
                ],
                'validation_keywords': ['work', 'job', 'money', 'health', 'family', 'stress', 'hard', 'tough', 'bad', 'control', 'cant', 'worry', 'think', 'feel', 'problem']
            },
            2: {
                'title': 'Work to Find Positivity in the Situation', 
                'questions': [
                    "What is the most positive way you can view your current circumstances?",
                    "What opportunities for emotional growth can you find in this challenge?",
                    "What silver linings or things that are going well can you identify, no matter how small?"
                ],
                'validation_keywords': ['good', 'better', 'learn', 'grow', 'help', 'try', 'can', 'maybe', 'hope', 'work', 'ok', 'fine', 'well']
            },
            3: {
                'title': 'Evaluate Your Past Ineffective Mindsets',
                'questions': [
                    "What thoughts and attitudes have created challenges for you in the past?",
                    "What mental patterns from the past should you avoid?",
                    "Describe a challenging situation from your past that you successfully overcame."
                ],
                'validation_keywords': ['past', 'before', 'used', 'always', 'habit', 'think', 'way', 'did', 'had', 'got', 'made', 'time', 'ago']
            },
            4: {
                'title': 'Locking In Your Mindset Mantra',
                'questions': [
                    "What is a powerful personal mantra that resonates with you? (Examples: 'I am resilient', 'I control my response, not my circumstances', 'I will find joy in every day')",
                    "Write out a final statement that integrates your mantra and your mindset commitment based on all our work together."
                ],
                'validation_keywords': ['i', 'am', 'will', 'can', 'try', 'strong', 'good', 'ok', 'work', 'do', 'make', 'get', 'go']
            }
        }

    def setup_memory_system(self):
        try:
            self.memory_index = faiss.IndexFlatL2(self.embedding_dim)
        except Exception as e:
            print(f"Warning: Could not initialize memory system: {e}")
            self.memory_index = None

    def get_embedding(self, text: str) -> np.ndarray:
        try:
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return np.array(response['data'][0]['embedding'], dtype=np.float32)
        except Exception as e:
            print(f"Warning: Could not get embedding: {e}")
            return np.random.rand(self.embedding_dim).astype(np.float32)

    def validate_response_simple(self, user_message: str, step: int, question_num: int) -> Dict[str, Any]:
        """Much more lenient validation that accepts shorter responses"""
        step_config = self.step_configs[step]
        validation_keywords = step_config['validation_keywords']
        current_question = step_config['questions'][question_num - 1]
        
        # Clean and analyze the message
        message_lower = user_message.lower().strip()
        word_count = len(message_lower.split())
        
        # Only reject extremely minimal responses
        minimal_responses = [
            'no', 'nope', 'nothing', 'idk', 'dunno', 'what', 'huh', '?'
        ]
        
        # Accept responses with just 2+ words (much more lenient)
        if message_lower in minimal_responses or word_count < 2:
            return {
                "score": 2,
                "is_valid": False,
                "feedback": "Please give me at least a few words to work with.",
                "suggestions": "Even a simple answer helps - just tell me what comes to mind.",
                "question": current_question
            }
        
        # Much more lenient keyword matching - any relevant word counts
        keyword_matches = sum(1 for keyword in validation_keywords if keyword in message_lower)
        
        # Accept almost everything with 2+ words or any keyword match
        if word_count >= 2 or keyword_matches >= 1:
            return {
                "score": 8,
                "is_valid": True,
                "feedback": "Thank you for sharing that with me.",
                "suggestions": "",
                "question": current_question
            }
        
        # Very rare case - only for truly problematic responses
        return {
            "score": 3,
            "is_valid": False,
            "feedback": "I need just a bit more information to help you.",
            "suggestions": "Any thoughts or feelings about this question are helpful.",
            "question": current_question
        }

    def validate_step_specific_content(self, message_lower: str, step: int, question_num: int) -> bool:
        """Simplified step validation - much more accepting"""
        
        # Accept almost any response that shows the user is trying to engage
        basic_engagement = len(message_lower.split()) >= 2
        
        if step == 1:  # Accept circumstances
            # Any mention of life areas or feelings
            life_areas = ['work', 'job', 'money', 'health', 'family', 'friend', 'school', 'home']
            feelings = ['stress', 'hard', 'tough', 'difficult', 'bad', 'worry', 'sad', 'mad']
            has_content = any(area in message_lower for area in life_areas + feelings)
            return basic_engagement or has_content
        
        elif step == 2:  # Find positivity
            # Any positive word or attempt at reframing
            positive_words = ['good', 'ok', 'fine', 'better', 'learn', 'try', 'can', 'maybe', 'help']
            has_positive = any(word in message_lower for word in positive_words)
            return basic_engagement or has_positive
        
        elif step == 3:  # Past patterns
            # Any reference to past or time
            time_words = ['past', 'before', 'used', 'always', 'ago', 'then', 'was', 'did', 'had']
            has_past = any(word in message_lower for word in time_words)
            return basic_engagement or has_past
        
        elif step == 4:  # Mantra
            # Any "I" statement or commitment word
            commitment_words = ['i', 'will', 'can', 'am', 'try', 'want', 'need', 'do']
            has_commitment = any(word in message_lower for word in commitment_words)
            return basic_engagement or has_commitment
        
        return basic_engagement

    def get_step_specific_guidance(self, step: int, question_num: int) -> str:
        """Simplified guidance that doesn't overwhelm users"""
        guidance = {
            1: {
                1: "Just tell me what's bothering you or causing stress right now.",
                2: "What can you change vs. what you can't change about this situation?",
                3: "What negative thoughts keep running through your mind?"
            },
            2: {
                1: "How might this challenge actually help you or teach you something?",
                2: "What could you learn or gain from going through this?",
                3: "What's going well in your life right now, even if it's small?"
            },
            3: {
                1: "What negative thinking patterns have hurt you before?",
                2: "What should you stop doing or thinking that hasn't worked?",
                3: "Tell me about a hard time you got through successfully."
            },
            4: {
                1: "What positive statement about yourself feels right? Start with 'I am' or 'I will'.",
                2: "Sum up your commitment to this new way of thinking."
            }
        }
        return guidance.get(step, {}).get(question_num, "Just share what comes to mind.")

    def add_to_memory(self, user_message: str, coach_response: str):
        """Add current conversation to FAISS memory for this session"""
        timestamp = datetime.now().isoformat()
        
        memory_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "user_message": user_message,
            "coach_response": coach_response,
            "step": self.current_step,
            "question": self.current_question,
            "user_responses": dict(self.user_responses)
        }
        
        self.conversation_history.append(memory_entry)
        
        if self.memory_index is not None:
            try:
                # Store the full conversation context
                search_text = f"Step {self.current_step} Q{self.current_question}: User: {user_message} | Coach: {coach_response}"
                embedding = self.get_embedding(search_text)
                embedding = embedding.reshape(1, -1)
                
                self.memory_index.add(embedding)
                self.memory_texts.append(search_text)
                self.memory_metadata.append(memory_entry)
                
            except Exception as e:
                print(f"Warning: Could not add to memory index: {e}")
        
        self.save_session()

    def search_memory(self, query: str, k: int = 3) -> List[Dict]:
        """Search current session memory for relevant conversations"""
        if self.memory_index is None or self.memory_index.ntotal == 0:
            return []
        
        try:
            query_embedding = self.get_embedding(query)
            query_embedding = query_embedding.reshape(1, -1)
            
            k = min(k, self.memory_index.ntotal)
            distances, indices = self.memory_index.search(query_embedding, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.memory_metadata):
                    memory = self.memory_metadata[idx].copy()
                    memory['similarity_score'] = float(distances[0][i])
                    results.append(memory)
            
            return results
            
        except Exception as e:
            print(f"Warning: Memory search failed: {e}")
            return []

    def get_memory_context(self, current_message: str) -> str:
        """Get relevant context from current session memory"""
        if not self.memory_texts:
            return ""
        
        relevant_memories = self.search_memory(current_message, k=2)
        
        if not relevant_memories:
            return ""
        
        context_parts = []
        for memory in relevant_memories:
            context_parts.append(
                f"Earlier this session at Step {memory['step']}: User said '{memory['user_message'][:100]}...'"
            )
        
        if context_parts:
            return f"\n\nSession Context: {' | '.join(context_parts)}"
        return ""

    def save_session(self):
        """Save current session to disk"""
        try:
            os.makedirs("sessions", exist_ok=True)
            
            session_data = {
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'conversation_history': self.conversation_history,
                'user_responses': self.user_responses,
                'current_step': self.current_step,
                'current_question': self.current_question
            }
            
            with open(f"sessions/{self.session_id}.json", 'w') as f:
                json.dump(session_data, f, indent=2)
            
            if self.memory_index is not None and self.memory_index.ntotal > 0:
                faiss.write_index(self.memory_index, f"sessions/{self.session_id}_index.faiss")
                
                with open(f"sessions/{self.session_id}_metadata.pkl", 'wb') as f:
                    pickle.dump({
                        'texts': self.memory_texts,
                        'metadata': self.memory_metadata
                    }, f)
                    
        except Exception as e:
            print(f"Warning: Could not save session: {e}")

    def get_step_response(self, message: str) -> str:
        step_config = self.step_configs[self.current_step]
        current_question = step_config['questions'][self.current_question - 1]
        
        # Much more lenient validation
        validation = self.validate_response_simple(message, self.current_step, self.current_question)
        
        # Only reject truly minimal responses
        if not validation['is_valid']:
            redirect_message = f"""{validation['feedback']}

{validation['suggestions']}

{current_question}"""
            
            return redirect_message

        # Valid response - store and continue
        self.store_user_response(message, self.current_step, self.current_question)
        
        # Generate coaching response
        memory_context = self.get_memory_context(message)
        
        coaching_prompt = f"""
        You are a supportive mindset coach. The user just shared: "{message}"

        Current: Step {self.current_step} - {step_config['title']} - Question {self.current_question}
        {memory_context}
        
        Provide a brief, encouraging acknowledgment (1-2 sentences), then:
        
        {"Move to the next question in this step." if self.current_question < len(step_config['questions']) else "Move to the next step with a brief summary."}
        
        Keep responses warm, supportive, and concise. No excessive praise. No emojis.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": coaching_prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            coach_response = response['choices'][0]['message']['content']
            
            # Handle progression
            if self.current_question < len(step_config['questions']):
                self.current_question += 1
                next_question = step_config['questions'][self.current_question - 1]
                coach_response += f"\n\n{next_question}"
            else:
                # Move to next step or complete
                if self.current_step < 4:
                    self.current_step += 1
                    self.current_question = 1
                    next_step = self.step_configs[self.current_step]
                    coach_response += f"\n\nStep {self.current_step}: {next_step['title']} \n\n{next_step['questions'][0]}"
                else:
                    # Generate implementation guide
                    return self.generate_implementation_guide()
            
            self.add_to_memory(message, coach_response)
            return coach_response
            
        except Exception as e:
            return f"I'm having trouble connecting right now. Error: {str(e)}. Please try again."

    def store_user_response(self, message: str, step: int, question: int):
        if step == 1:
            if question == 1:
                self.user_responses['circumstances'].append(message)
            elif question == 2:
                self.user_responses['control_analysis'] = message
            else:
                self.user_responses['letting_go'] = message
        elif step == 2:
            self.user_responses['positivity_insights'].append(message)
        elif step == 3:
            if question == 1:
                self.user_responses['past_ineffective_patterns'].append(message)
            elif question == 2:
                self.user_responses['past_ineffective_patterns'].append(f"Patterns to avoid: {message}")
            else:
                self.user_responses['challenge_overcome'] = message
        elif step == 4:
            if question == 1:
                self.user_responses['personal_mantra'] = message
            else:
                self.user_responses['final_statement'] = message

    def generate_implementation_guide(self) -> str:
        # Use current session memory to understand the user's journey
        all_insights = self.search_memory("growth transformation mindset mantra", k=5)
        
        implementation_prompt = f"""
        Create a brief implementation guide based on this user's mindset journey:
        
        User's Journey:
        - Circumstances: {self.user_responses['circumstances']}
        - Control analysis: {self.user_responses['control_analysis']}
        - Letting go: {self.user_responses['letting_go']}
        - Positive reframes: {self.user_responses['positivity_insights']}
        - Past patterns: {self.user_responses['past_ineffective_patterns']}
        - Challenge overcome: {self.user_responses['challenge_overcome']}
        - Personal mantra: {self.user_responses['personal_mantra']}
        - Final commitment: {self.user_responses['final_statement']}
        
        Create a simple daily plan that includes:
        1. How to use their mantra daily
        2. Where to put reminders
        3. Simple daily practices
        4. How to track progress
        
        Keep it practical and encouraging. No emojis.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": implementation_prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            implementation_guide = response['choices'][0]['message']['content']
            
            completion_message = f"""CONGRATULATIONS! Framework Complete!

Your Personal Mantra: "{self.user_responses['personal_mantra']}"

Your Commitment: "{self.user_responses['final_statement']}"

{implementation_guide}

Remember: Mindset is Greater Than Circumstances!

Session Complete - {len(self.conversation_history)} conversations saved

Your transformation journey is complete. Use your mantra daily and remember what you've learned!
"""
            
            self.add_to_memory("Framework completed", completion_message)
            return completion_message
            
        except Exception as e:
            return f"Congratulations on completing the framework! Your mantra '{self.user_responses['personal_mantra']}' is powerful. Error in generation: {e}"

    def get_response(self, message: str) -> str:
        if not self.session_started:
            if message.upper().strip() == "START":
                self.session_started = True
                return self.get_initial_question()
            else:
                return """Type 'START' to begin your mindset transformation session"""
        
        return self.get_step_response(message)

    def get_initial_question(self) -> str:
        return """Welcome to Your Mindset Transformation!

We'll work through 4 simple steps:

Step 1: Accept the Circumstances
Step 2: Find Positivity in the Situation 
Step 3: Learn from Past Patterns 
Step 4: Create Your Personal Mantra 

Then you'll get your personalized daily plan.

Step 1: Accept the Circumstances

What challenging circumstances are you currently facing that you need to accept?

Just tell me what's going on - even a few words helps."""

def main():
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    
    if not api_key:
        print("ERROR: No OpenAI API key found!")
        print("Please create a .env file with: OPENAI_API_KEY=your_key_here")
        return
    
    try:
        coach = MindsetCoachWithMemory(api_key)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return
    
    while True:
        try:
            if coach.session_started:
                print(f"")
            
            user_input = input("\n ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'stop']:
                print("\nThank you for using the AI Mindset Coach!")
                print("Remember: Mindset is greater than circumstances!")
                break
            
            if not user_input:
                print("Please share your thoughts to continue...")
                continue
            
            print("\n")
            response = coach.get_response(user_input)
            print(response)
            
            if coach.session_started and coach.current_step > 4:
                print("\nYour mindset transformation is complete!")
                print("Start using your mantra today!")
                break
                
        except KeyboardInterrupt:
            print("\n\nSession ended.")
            print("Remember: Mindset is greater than circumstances!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again...")

if __name__ == "__main__":
    main()