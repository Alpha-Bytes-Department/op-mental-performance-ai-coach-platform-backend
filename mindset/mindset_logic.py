import openai
import os
from typing import Dict, Any
from knowledge_base.services import query_knowledge

load_dotenv()

class MindsetCoach:
    """Handles the logic for the Mindset Coach chatbot."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        openai.api_key = api_key
        self.step_configs = self._initialize_step_configs()

    def _initialize_step_configs(self) -> Dict[int, Dict]:
        return {
            1: {
                'title': 'Accept the Circumstances',
                'questions': [
                    "What challenging circumstances are you currently facing that you need to accept?",
                    "What aspects of this situation are within your control vs. outside your control?",
                    "What worst-case scenarios do you replay in your mind that prevent you from taking action?"
                ]
            },
            2: {
                'title': 'Work to Find Positivity in the Situation',
                'questions': [
                    "What is the most positive way you can view your current circumstances?",
                    "What opportunities for emotional growth can you find in this challenge?",
                    "What silver linings or things that are going well can you identify, no matter how small?"
                ]
            },
            3: {
                'title': 'Evaluate Your Past Ineffective Mindsets',
                'questions': [
                    "What thoughts and attitudes have created challenges for you in the past?",
                    "What mental patterns from the past should you avoid?",
                    "Describe a challenging situation from your past that you successfully overcame."
                ]
            },
            4: {
                'title': 'Locking In Your Mindset Mantra',
                'questions': [
                    "What is a powerful personal mantra that resonates with you? (Examples: 'I am resilient', 'I control my response, not my circumstances', 'I will find joy in every day')",
                    "Write out a final statement that integrates your mantra and your mindset commitment based on all our work together."
                ]
            }
        }

    def get_welcome_message(self) -> str:
        #return "Welcome to Your Mindset Transformation!\n\nWe'll work through 4 simple steps:\n\nStep 1: Accept the Circumstances\nStep 2: Find Positivity in the Situation \nStep 3: Learn from Past Patterns \nStep 4: Create Your Personal Mantra \n\nThen you'll get your personalized daily plan."
        return "Welcome to Your Mindset Transformation!\n"

    def get_initial_question(self) -> str:
        return "Let's start by understanding what you're facing. What challenging circumstances are you currently facing that you need to accept?"

    def get_response(self, user_message: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        current_step = session_data.get('current_step', 1)
        user_responses = session_data.get('user_responses', {})
        history = session_data.get('history', [])

        # Determine the current question index based on history for the current step
        current_question_index = sum(1 for msg in history if msg.get('step') == current_step)

        step_config = self.step_configs[current_step]
        
        # Store the user's response
        if f"step_{current_step}" not in user_responses:
            user_responses[f"step_{current_step}"] = []
        user_responses[f"step_{current_step}"].append(user_message)

##############################################################
        # Retrieve relevant context from the knowledge base using the RAG pipeline
        evidence_context = ""
        retrieved = query_knowledge(user_message,domain="mindset")
        if retrieved:
            evidence_context = "n\Retrived Insights:\n" + "\n".join(
                [f"- {doc['title']}: {doc['text'][:120]}..." for doc in retrieved]
            )
###############################################################

        # Check if the current step is complete
        if current_question_index >= len(step_config['questions']) - 1:
            # Move to the next step or complete the session
            if current_step < 4:
                current_step += 1
                next_step_config = self.step_configs[current_step]
                reply = f"Thank you for sharing. Let's move to the next step.\n\nStep {current_step}: {next_step_config['title']}\n\n{next_step_config['questions'][0]}"
            else:
                # Session is complete, generate final summary
                reply = self._generate_final_summary(user_responses)
                current_step = 5 # Mark as complete
        else:
            # Ask the next question in the current step
            next_question_index = current_question_index + 1
            reply = step_config['questions'][next_question_index]

        return {
            'reply': reply,
            'updated_state': {
                'current_step': current_step,
                'user_responses': user_responses
            }
        }

    def _generate_final_summary(self, user_responses: Dict[str, Any]) -> str:
        # This is a simplified summary generation. 
        # In a real application, you would use a more sophisticated method, possibly involving an LLM.
        
        mantra = user_responses.get('step_4', ['I am resilient'])[0]
        
        summary = f"CONGRATULATIONS! You have completed your mindset transformation.\n\n"
        summary += f"Your personal mantra is: \"{mantra}\"\n\n"
        summary += "Remember to use this mantra daily to reinforce your new mindset.\n\n"
        summary += "Here are some of the insights you gathered during your session:\n"
        
        for step in range(1, 4):
            if f"step_{step}" in user_responses:
                summary += f"\nIn Step {step}, you reflected on:\n"
                for response in user_responses[f"step_{step}"]:
                    summary += f"- {response}\n"
                    
        return summary
