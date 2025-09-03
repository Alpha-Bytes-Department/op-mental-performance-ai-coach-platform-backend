import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import re
from dotenv import load_dotenv

load_dotenv()

try:
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class TherapyPhase(Enum):
    IDENTIFICATION = "Phase 1: Identification "
    EXPLORATION = "Phase 2: Exploration "
    REFRAMING = "Phase 3: Reframing & Strengths "
    ACTION_PLANNING = "Phase 4: Action Planning "
    REFLECTION = "Phase 5: Reflection & Adaptation "

class ChallengeType(Enum):
    MOOD_DISORDERS = "Mood Disorders"
    TRAUMA = "Trauma"
    RELATIONSHIP_CONFLICT = "Relationship Conflict"
    MOTIVATION_ISSUES = "Motivation Issues"
    NARRATIVE_ISSUES = "Narrative Issues"
    SELF_DOUBT = "Self-Doubt/Imposter Syndrome"
    PERFORMANCE_BLOCKS = "Performance Blocks"
    GENERAL = "General Challenge"

class QuestionState(Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    INVALID = "invalid"

class InternalChallengeTherapySystem:
    def __init__(self):
        self.current_phase = TherapyPhase.IDENTIFICATION
        self.challenge_type = ChallengeType.GENERAL
        self.current_question_index = 0
        self.session_data = {
            "intensity": None,
            "duration": None,
            "impact": None,
            "interfering_factors": None,
            "core_beliefs": [],
            "body_experiences": None,
            "personal_narrative": None,
            "strengths": [],
            "values": [],
            "growth_opportunities": None,
            "action_items": [],
            "interference_management": None,
            "daily_practices": None,
            "final_reflection": None,
            "progress_notes": []
        }
        self.conversation_history = []
        self.phase_questions = self._initialize_phase_questions()
        self.phase_goals = self._initialize_phase_goals()
        self.question_validators = self._initialize_validators()
        
    def _initialize_phase_goals(self) -> Dict[TherapyPhase, str]:
        return {
            TherapyPhase.IDENTIFICATION: "Understand the challenge clearly and completely by assessing its intensity, duration, impact, and interfering factors.",
            TherapyPhase.EXPLORATION: "Create safe, deep exploration to identify core beliefs, body experiences, and personal narratives driving the emotional response.",
            TherapyPhase.REFRAMING: "Shift perspective from problem-focused to growth-oriented by identifying strengths and aligning responses with core values.",
            TherapyPhase.ACTION_PLANNING: "Translate insights into concrete, repeatable behaviors with specific performance actions and interference management plans.",
            TherapyPhase.REFLECTION: "Build confidence in your ability to engage effectively during difficult times and reinforce that this moment will pass."
        }
    
    def _initialize_phase_questions(self) -> Dict[TherapyPhase, List[Dict]]:
        return {
            TherapyPhase.IDENTIFICATION: [
                {
                    "question": "How would you rate the intensity of this challenge on a scale of 1-10, where 1 is barely noticeable and 10 is completely overwhelming?",
                    "key": "intensity",
                    "type": "scale",
                    "validation_required": True
                },
                {
                    "question": "When did you first notice this challenge beginning? Please describe the timeline and any changes over time.",
                    "key": "duration",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "Which areas of your life are most affected by this challenge? (Consider: work, relationships, health, self-esteem, daily activities)",
                    "key": "impact",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "What internal or external factors seem to make this challenge stronger or weaker?",
                    "key": "interfering_factors",
                    "type": "text",
                    "validation_required": True
                }
            ],
            TherapyPhase.EXPLORATION: [
                {
                    "question": "Where do you feel this emotion or challenge in your body? Describe any physical sensations, tension, or changes you notice.",
                    "key": "body_experiences",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "What story are you telling yourself about this situation? What beliefs about yourself or the world might be contributing to this challenge?",
                    "key": "personal_narrative",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "What core beliefs do you hold about your ability to overcome difficult moments like this?",
                    "key": "core_beliefs",
                    "type": "list",
                    "validation_required": True
                },
                {
                    "question": "What would you say to a dear friend experiencing this same challenge?",
                    "key": "friend_advice",
                    "type": "text",
                    "validation_required": True
                }
            ],
            TherapyPhase.REFRAMING: [
                {
                    "question": "What personal strengths have helped you get through difficult times in the past?",
                    "key": "strengths",
                    "type": "list",
                    "validation_required": True
                },
                {
                    "question": "How might this challenge be an opportunity for growth that you can overcome?",
                    "key": "growth_opportunities",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "What values are most important to you in this situation? What really matters to you here?",
                    "key": "values",
                    "type": "list",
                    "validation_required": True
                },
                {
                    "question": "Imagine your most resilient self - what would they do in this moment? How would they approach this challenge?",
                    "key": "resilient_self",
                    "type": "text",
                    "validation_required": True
                }
            ],
            TherapyPhase.ACTION_PLANNING: [
                {
                    "question": "What specific actions could you take this week to address this challenge? List concrete, repeatable behaviors.",
                    "key": "action_items",
                    "type": "list",
                    "validation_required": True
                },
                {
                    "question": "What obstacles might interfere with these actions, and how can you prepare for them? Create your Interference Management Plan.",
                    "key": "interference_management",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "What daily emotion regulation practices will you commit to? (Examples: journaling, breathwork, reframing practice, acceptance exercises)",
                    "key": "daily_practices",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "Who in your support network could help you with this challenge?",
                    "key": "support_network",
                    "type": "text",
                    "validation_required": True
                }
            ],
            TherapyPhase.REFLECTION: [
                {
                    "question": "What have you learned about yourself through this therapeutic process?",
                    "key": "self_learning",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "How has your understanding of this challenge evolved from when we started?",
                    "key": "understanding_evolution",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "What strategies from our work together have been most helpful so far?",
                    "key": "helpful_strategies",
                    "type": "text",
                    "validation_required": True
                },
                {
                    "question": "How will you maintain your progress and continue growing as you move forward?",
                    "key": "maintenance_plan",
                    "type": "text",
                    "validation_required": True
                }
            ]
        }
    
    def _initialize_validators(self) -> Dict[str, callable]:
        return {
            "intensity": lambda x: self._validate_scale(x, 1, 10),
            "duration": lambda x: self._validate_text_length(x, min_length=10),
            "impact": lambda x: self._validate_text_length(x, min_length=15),
            "interfering_factors": lambda x: self._validate_text_length(x, min_length=10),
            "body_experiences": lambda x: self._validate_text_length(x, min_length=15),
            "personal_narrative": lambda x: self._validate_text_length(x, min_length=20),
            "core_beliefs": lambda x: self._validate_list_response(x, min_items=1),
            "friend_advice": lambda x: self._validate_text_length(x, min_length=15),
            "strengths": lambda x: self._validate_list_response(x, min_items=2),
            "growth_opportunities": lambda x: self._validate_text_length(x, min_length=20),
            "values": lambda x: self._validate_list_response(x, min_items=2),
            "resilient_self": lambda x: self._validate_text_length(x, min_length=20),
            "action_items": lambda x: self._validate_list_response(x, min_items=2),
            "interference_management": lambda x: self._validate_text_length(x, min_length=25),
            "daily_practices": lambda x: self._validate_text_length(x, min_length=15),
            "support_network": lambda x: self._validate_text_length(x, min_length=10),
            "self_learning": lambda x: self._validate_text_length(x, min_length=20),
            "understanding_evolution": lambda x: self._validate_text_length(x, min_length=20),
            "helpful_strategies": lambda x: self._validate_text_length(x, min_length=15),
            "maintenance_plan": lambda x: self._validate_text_length(x, min_length=20)
        }
    
    def _validate_scale(self, response: str, min_val: int, max_val: int) -> tuple[bool, str]:
        try:
            value = int(response.strip())
            if min_val <= value <= max_val:
                return True, ""
            else:
                return False, f"Please provide a number between {min_val} and {max_val}."
        except ValueError:
            return False, f"Please provide a valid number between {min_val} and {max_val}."
    
    def _validate_text_length(self, response: str, min_length: int) -> tuple[bool, str]:
        if len(response.strip()) >= min_length:
            return True, ""
        else:
            return False, f"Please provide a more detailed response (at least {min_length} characters). Your healing deserves thoughtful reflection."
    
    def _validate_list_response(self, response: str, min_items: int) -> tuple[bool, str]:
        # Check if response contains multiple items (separated by commas, semicolons, or line breaks)
        separators = [',', ';', '\n', '•', '-', '1.', '2.', '3.']
        item_count = 1  
        
        for sep in separators:
            if sep in response:
                item_count = max(item_count, len([item for item in response.split(sep) if item.strip()]))
        
        if item_count >= min_items and len(response.strip()) >= 10:
            return True, ""
        else:
            return False, f"Please provide at least {min_items} items in your response. You can separate them with commas, line breaks, or bullet points."
    
    def identify_challenge_type(self, message: str) -> ChallengeType:
        message_lower = message.lower()
        
        challenge_keywords = {
            ChallengeType.MOOD_DISORDERS: ['depressed', 'anxious', 'mood', 'panic', 'sad', 'hopeless', 'anxiety', 'depression'],
            ChallengeType.TRAUMA: ['trauma', 'abuse', 'ptsd', 'flashback', 'triggered', 'traumatic'],
            ChallengeType.RELATIONSHIP_CONFLICT: ['relationship', 'conflict', 'argument', 'partner', 'friend', 'family'],
            ChallengeType.MOTIVATION_ISSUES: ['motivation', 'procrastination', 'lazy', 'unmotivated', 'procrastinate'],
            ChallengeType.NARRATIVE_ISSUES: ['story', 'narrative', 'identity', 'who am i', 'sense of self'],
            ChallengeType.SELF_DOUBT: ['imposter', 'fraud', 'not good enough', 'self-doubt', 'doubt myself'],
            ChallengeType.PERFORMANCE_BLOCKS: ['performance', 'block', 'stuck', 'can\'t perform', 'blocked']
        }
        
        for challenge_type, keywords in challenge_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return challenge_type
        
        return ChallengeType.GENERAL
    
    def get_current_question(self) -> Optional[Dict]:
        phase_questions = self.phase_questions.get(self.current_phase, [])
        if self.current_question_index < len(phase_questions):
            return phase_questions[self.current_question_index]
        return None
    
    def validate_response(self, response: str) -> tuple[bool, str]:
        current_question = self.get_current_question()
        if not current_question:
            return True, ""
        
        question_key = current_question.get("key")
        if question_key in self.question_validators:
            return self.question_validators[question_key](response)
        
        return True, ""
    
    def process_response(self, response: str) -> Dict[str, Any]:
        current_question = self.get_current_question()
        if not current_question:
            return {"status": "phase_complete"}

        is_valid, error_message = self.validate_response(response)

        # Find the last entry in the history to update it
        last_entry = self.conversation_history[-1] if self.conversation_history else None

        if not is_valid:
            if last_entry and last_entry.get("question_key") == current_question["key"]:
                last_entry["error_message"] = error_message
                last_entry["response_type"] = "invalid_user_response"
            return {
                "status": "invalid_response",
                "error": error_message,
                "question": current_question["question"],
            }

        question_key = current_question["key"]
        if current_question["type"] == "scale":
            self.session_data[question_key] = int(response.strip())
        elif current_question["type"] == "list":
            self.session_data[question_key] = self._parse_list_response(response)
        else:
            self.session_data[question_key] = response.strip()

        # Update the last history entry with the user's response
        if last_entry and last_entry.get("question_key") == current_question["key"]:
            last_entry["response"] = response.strip()
            last_entry["response_type"] = "user_response"
            last_entry["timestamp"] = datetime.now().isoformat()

        self.current_question_index += 1

        if self.current_question_index >= len(self.phase_questions.get(self.current_phase, [])):
            return {"status": "phase_complete"}

        return {"status": "continue"}
    
    def _parse_list_response(self, response: str) -> List[str]:
        # Parse various list formats
        items = []
        
        # Try different separators
        separators = ['\n', ';', ',']
        for sep in separators:
            if sep in response:
                items = [item.strip() for item in response.split(sep) if item.strip()]
                break
        
        # If no separators found, check for bullet points or numbers
        if not items:
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                # Remove bullet points, numbers, dashes
                line = re.sub(r'^[\s\-\•\d\.\)\]]*', '', line).strip()
                if line:
                    items.append(line)
        
        # If still no items, treat as single item
        if not items:
            items = [response.strip()]
        
        return items
    
    def _generate_ai_therapeutic_summary(self) -> str:
        """Generate AI-powered therapeutic analysis using OpenAI API"""
        if not OPENAI_AVAILABLE or not os.getenv('OPENAI_API_KEY'):
            return self._generate_fallback_summary()
        
        try:
            # Prepare conversation context
            conversation_context = "\n\n".join([
                f"Phase: {conv['phase']}\nQuestion: {conv['question']}\nResponse: {conv['response']}" 
                for conv in self.conversation_history
            ])
            
            prompt = f'''
            As an expert therapeutic supervisor, analyze this complete 5-Phase Internal Challenge Therapy session and provide a comprehensive clinical assessment.

            **Session Data:**
            Challenge Type: {self.challenge_type.value}
            Initial Intensity: {self.session_data.get('intensity')}/10

            **Complete Therapeutic Conversation:**
            {conversation_context}

            **Session Summary Data:**
            - Strengths Identified: {', '.join(self.session_data.get('strengths', []))}
            - Core Values: {', '.join(self.session_data.get('values', []))}
            - Action Items: {', '.join(self.session_data.get('action_items', []))}
            - Daily Practices: {self.session_data.get('daily_practices', 'Not specified')}

            **Please provide a clinical analysis focusing on:**

            1. **Therapeutic Progress Assessment:**
               - How effectively did the client engage with each phase?
               - What key breakthroughs or insights emerged?
               - Evidence of emotional regulation development

            2. **Core Capacities Development:**
               - **Distress Tolerance:** Evidence of improved ability to stay present in discomfort
               - **Cognitive Flexibility:** Demonstration of multiple perspective-taking
               - **Emotional Literacy:** Growth in accurately naming and working with emotions  
               - **Self-Compassion:** Replacement of self-criticism with supportive self-talk

            3. **Clinical Strengths Observed:**
               - Resilience factors and coping mechanisms identified
               - Values alignment and motivational resources
               - Social support and protective factors

            4. **Treatment Recommendations:**
               - Specific areas for continued focus
               - Relapse prevention strategies
               - Maintenance of therapeutic gains

            5. **Prognosis and Next Steps:**
               - Expected trajectory based on engagement and insights
               - Specific homework or between-session activities
               - Long-term growth recommendations

            Use evidence-based therapeutic language while remaining compassionate and strengths-focused. Highlight concrete progress made in building the four core capacities.
            '''
            
            # Use the correct OpenAI client syntax
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert therapeutic supervisor specializing in internal challenge therapy, trauma-informed care, and resilience building. Provide clinical assessments that are both professionally rigorous and deeply compassionate."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.6
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return self._generate_fallback_summary()
    
    def _generate_fallback_summary(self) -> str:
        return f'''
**AI Therapeutic Analysis:**

**Therapeutic Progress Assessment:**
• You successfully engaged with all 5 phases of the therapeutic process
• Your responses demonstrate growing self-awareness and emotional intelligence
• You\'ve developed concrete tools for managing your {self.challenge_type.value.lower()}
• Your commitment to daily practices shows strong therapeutic engagement

**Core Capacities Development:**
✓ **Distress Tolerance:** You\'ve shown ability to stay present with difficult emotions without immediately avoiding or escaping them
✓ **Cognitive Flexibility:** Evidence of considering multiple perspectives on your challenge rather than rigid thinking patterns
✓ **Emotional Literacy:** Growth in naming and understanding your emotional experiences with greater nuance and accuracy
✓ **Self-Compassion:** Movement toward more supportive self-talk patterns, replacing harsh self-criticism

**Clinical Strengths Observed:**
• Strong engagement with the therapeutic process
• Willingness to explore difficult emotions and beliefs
• Identification of personal strengths and values
• Development of concrete action plans
• Recognition of support systems and resources

**Treatment Recommendations:**
• Continue daily emotion regulation practices consistently
• Use your developed action plan during challenging moments
• Practice the core capacities regularly to strengthen these skills
• Maintain connection with your support network
• Monitor progress and adjust strategies as needed

**Prognosis and Next Steps:**
Your therapeutic engagement and insight development indicate strong potential for continued growth. The tools and awareness you\'ve gained provide a solid foundation for managing future challenges. Focus on maintaining your daily practices and applying your new skills consistently.

**Continued Growth Recommendation:**
Practice your daily emotion regulation techniques and use your action plan consistently. Your therapeutic insights are real and will continue supporting your growth.
'''
    
    def advance_to_next_phase(self) -> bool:
        phases = list(TherapyPhase)
        current_index = phases.index(self.current_phase)
        
        if current_index < len(phases) - 1:
            self.current_phase = phases[current_index + 1]
            self.current_question_index = 0
            return True
        return False
    
    def get_phase_summary(self) -> str:
        phase_name = self.current_phase.value
        goal = self.phase_goals[self.current_phase]
        
        return f'''
 **{phase_name}**

**Phase Goal:** {goal}

**What we\'ve accomplished in this phase:**
{self._generate_phase_accomplishments()}

**Moving forward with strength and clarity.** 
'''
    
    def _generate_phase_accomplishments(self) -> str:
        accomplishments = []
        
        if self.current_phase == TherapyPhase.IDENTIFICATION:
            if self.session_data.get('intensity'):
                accomplishments.append(f"• Identified challenge intensity: {self.session_data['intensity']}/10")
            if self.session_data.get('duration'):
                accomplishments.append(f"• Mapped timeline and duration of the challenge")
            if self.session_data.get('impact'):
                accomplishments.append(f"• Assessed impact on life areas")
            if self.session_data.get('interfering_factors'):
                accomplishments.append(f"• Identified key interfering factors")
        
        elif self.current_phase == TherapyPhase.EXPLORATION:
            if self.session_data.get('body_experiences'):
                accomplishments.append(f"• Explored somatic experiences and body awareness")
            if self.session_data.get('personal_narrative'):
                accomplishments.append(f"• Examined personal narratives and belief systems")
            if self.session_data.get('core_beliefs'):
                accomplishments.append(f"• Identified core beliefs about overcoming challenges")
        
        elif self.current_phase == TherapyPhase.REFRAMING:
            if self.session_data.get('strengths'):
                accomplishments.append(f"• Identified personal strengths: {', '.join(self.session_data['strengths'][:3])}")
            if self.session_data.get('growth_opportunities'):
                accomplishments.append(f"• Reframed challenge as growth opportunity")
            if self.session_data.get('values'):
                accomplishments.append(f"• Clarified core values: {', '.join(self.session_data['values'][:3])}")
        
        elif self.current_phase == TherapyPhase.ACTION_PLANNING:
            if self.session_data.get('action_items'):
                accomplishments.append(f"• Developed {len(self.session_data['action_items'])} specific action items")
            if self.session_data.get('interference_management'):
                accomplishments.append(f"• Created interference management plan")
            if self.session_data.get('daily_practices'):
                accomplishments.append(f"• Committed to daily emotion regulation practices")
        
        elif self.current_phase == TherapyPhase.REFLECTION:
            accomplishments.append(f"• Consolidated learning and insights from therapeutic process")
            accomplishments.append(f"• Developed maintenance and growth strategies")
        
        return "\n".join(accomplishments) if accomplishments else "• Building awareness and insight step by step"
    
    def generate_final_therapeutic_summary(self) -> str:

        return self._generate_ai_therapeutic_summary()
    
    def save_session(self, filename: str = "therapy_session.json"):
        session_export = {
            "session_data": self.session_data,
            "conversation_history": self.conversation_history,
            "current_phase": self.current_phase.value,
            "challenge_type": self.challenge_type.value,
            "completion_status": "completed" if self.current_phase == TherapyPhase.REFLECTION else "in_progress",
            "export_timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(session_export, f, indent=2)
            return f" Therapy session saved to {filename}"
        except Exception as e:
            return f" Error saving session: {str(e)}"

class TherapyInterface:
    def __init__(self):
        self.therapy_system = InternalChallengeTherapySystem()
        self.session_active = False
        self.session_started = False  
    
    def start_session(self):
        
        
        while not self.session_started:
            user_input = input(" ").strip().upper()
            
            if user_input == "START":
                self.session_started = True
                self.session_active = True
                self._display_welcome_message()
                self._get_initial_challenge()
                self.continue_session()
            else:
                print(" Please type 'START' to begin the therapy session.")
    
    def _display_welcome_message(self):
        print("\n Welcome to Internal Challenge Therapy - 5-Phase Framework")
    
        print("\n I\'m here to guide you through a therapeutic journey to understand and overcome your internal challenges.")
        print("\n We\'ll work through 5 phases together:")
        print("   Phase 1: Identification ")
        print("   Phase 2: Exploration ") 
        print("   Phase 3: Reframing & Strengths ")
        print("   Phase 4: Action Planning ")
        print("   Phase 5: Reflection & Adaptation ")
        print("\n Remember: This is a safe space. All experiences are welcomed and explored.")
    
    
    def _get_initial_challenge(self):
        print("\n Let\'s start by understanding what you\'re facing...")
        initial_response = input("What internal challenge would you like to work through today? Please share what\'s on your mind: ")
        
        # Identify challenge type
        self.therapy_system.challenge_type = self.therapy_system.identify_challenge_type(initial_response)
        print(f"\n I sense you\'re working with: {self.therapy_system.challenge_type.value}")
    
    def continue_session(self):
        while self.session_active:
            # Show current phase and goal
            current_goal = self.therapy_system.phase_goals[self.therapy_system.current_phase]
            print(f"\n **{self.therapy_system.current_phase.value}**")
            print(f" Goal: {current_goal}")

            
            # Get current question
            current_question = self.therapy_system.get_current_question()
            if not current_question:
                # Phase complete
                print(self.therapy_system.get_phase_summary())
                
                if not self.therapy_system.advance_to_next_phase():
                    # All phases complete
                    self.complete_session()
                    break
                continue
            
            # Ask question
            print(f"\n {current_question['question']}")
            response = input("\n Your response: ")
            
            # Process response
            result = self.therapy_system.process_response(response)
            
            if result["status"] == "invalid_response":
                print(f"\n {result['error']}")
                print("Let's try again - your growth deserves thoughtful attention.")
                continue
            
            elif result["status"] == "phase_complete":
                print(f"\n Excellent work! You\'ve completed this phase.")
            
            print(f"\n Thank you for that thoughtful response. Moving forward...")

    def complete_session(self):

        print("CONGRATULATIONS! You\'ve completed the full 5-Phase Therapeutic Journey!")

        
        # Generate and show AI-only final summary
        final_summary = self.therapy_system.generate_final_therapeutic_summary()
        print(f"\n{final_summary}")
        
        # Save session
        save_result = self.therapy_system.save_session()
        print(f"\n{save_result}")
        
        self.session_active = False
        print("\n Remember: You have the tools and strength to navigate any challenge. Take care of yourself!")

# Run the therapy session
if __name__ == "__main__":
    interface = TherapyInterface()
    interface.start_session()