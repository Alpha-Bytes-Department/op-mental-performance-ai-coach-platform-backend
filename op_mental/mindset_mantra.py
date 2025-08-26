import openai
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MindsetCoach:
    def __init__(self, api_key: str = None):
        if api_key:
            openai.api_key = api_key
        self.conversation_history = []
        self.current_step = 1
        self.user_responses = {
            'acceptance_reflection': '',
            'positivity_reflection': '',
            'past_mindsets': [],
            'final_mantra': ''
        }
        self.has_api_key = bool(api_key)
        
    def add_to_memory(self, message: str, response: str):
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "coach_response": response,
            "step": self.current_step
        })

    def get_step_prompt(self, step: int, user_message: str = "") -> str:
        
        if step == 1:  # Accept the Circumstances
            return f"""You are a mindset coach following the Building Effective Mindsets Framework. 

You are currently on Step 1: Accept the Circumstances.

IMPORTANT: You must evaluate if the user's response is relevant to Step 1. Step 1 is about identifying challenging circumstances they need to accept.

Your role is to help the user identify what is within their control vs. outside their control. Focus on:
- Helping them let go of "what ifs" and fantasy thinking
- Encouraging them to focus energy on managing reality in front of them
- Guiding them to accept their current circumstances

User's message: {user_message}

RESPONSE GUIDELINES:
- If the user shares challenging circumstances or situations they're facing: Acknowledge their situation and guide them toward acceptance, then ask the reflection question.
- If the user gives an irrelevant answer (off-topic, vague, or doesn't address circumstances): Gently redirect them with: "I understand, but let's focus on Step 1 of our framework. To build an effective mindset, we need to start by identifying what you're currently facing. What challenging circumstances or difficult situation are you currently dealing with that you need to accept?"
- If the user says they have no challenges: Guide them to think deeper: "Everyone faces some form of challenge or difficulty. It could be work stress, relationship issues, health concerns, financial worries, or personal goals. What area of your life feels challenging right now?"

The key reflection question for Step 1 is: "What challenging circumstances are you currently facing that you need to accept?"

Stay focused on Step 1 and don't move forward until they properly address this step."""

        elif step == 2:  # Find Positivity
            return f"""You are a mindset coach following the Building Effective Mindsets Framework.

You are currently on Step 2: Work to Find Positivity in the Situation.

IMPORTANT: Evaluate if the user's response addresses finding positivity in their circumstances from Step 1.

Help the user:
- Reframe challenges into opportunities for emotional growth
- Seek out silver linings, no matter how small
- Find ways to look at the glass half full
- Notice what is going well despite challenges

User's message: {user_message}

RESPONSE GUIDELINES:
- If the user shares positive perspectives or reframes their challenges: Acknowledge and build on their insights, then deepen the reflection.
- If the user gives an irrelevant answer or stays negative: Redirect them: "I understand this is difficult, but Step 2 requires us to find positivity in your situation. Even in challenging circumstances, there are often silver linings or growth opportunities. Let me ask you again: What is the most positive way you can view your current circumstances? What might you be learning or gaining from this experience?"
- If the user says there's nothing positive: Guide them gently: "I understand it's hard to see positivity right now. Let's start small - is there anything, even tiny, that you've learned about yourself? Any strength you've discovered? Any support you've received? Sometimes the growth itself is the positive aspect."

The key reflection question for Step 2 is: "What is the most positive way you can view your current circumstances?"

Stay focused on helping them find positivity before moving to Step 3."""

        elif step == 3:  # Evaluate Past Mindsets
            return f"""You are a mindset coach following the Building Effective Mindsets Framework.

You are currently on Step 3: Evaluate Your Past Ineffective Mindsets.

IMPORTANT: Evaluate if the user's response addresses past mindset patterns and past experiences.

Help the user reflect on past patterns by asking these key questions:
1. "What thoughts and attitudes have created challenges for you in the past?"
2. "What mental patterns from the past should you avoid?"
3. "Describe a challenging situation from your past that you overcame."

User's message: {user_message}

RESPONSE GUIDELINES:
- If the user shares past experiences, patterns, or mindsets: Acknowledge and explore deeper, helping them identify specific patterns to avoid.
- If the user gives an irrelevant answer or focuses on current situation instead of past: Redirect them: "Let's focus on Step 3 - learning from your past mindset patterns. To build a better mindset, we need to understand what hasn't worked before. Can you think of a time when your thinking or attitude made a situation harder for you? What thoughts or mental patterns have created challenges for you in the past?"
- If the user says they can't remember or have no past issues: Guide them: "Everyone has had moments where their mindset could have been better. Think about times you worried excessively, were overly negative, or got stuck in unhelpful thinking. Even small examples help us learn."

Work through these reflection questions systematically. Don't move to Step 4 until they've adequately reflected on past patterns."""

        elif step == 4:  # Create Mantra
            return f"""You are a mindset coach following the Building Effective Mindsets Framework.

You are currently on Step 4: Locking In Your Mindset Mantra.

IMPORTANT: Evaluate if the user's response shows effort to create a personal mantra or addresses mantra development.

Help the user:
- Develop a personal mantra to stay focused during difficult times
- Create something clear, actionable, and resonant
- Examples: "I am resilient." "I will find joy in every day." "I control my response, not my circumstances."

Based on their previous reflections about acceptance, positivity, and past patterns, help them craft their personal mantra.

User's message: {user_message}

RESPONSE GUIDELINES:
- If the user proposes a mantra or engages with mantra creation: Help refine and strengthen their mantra, make it more personal and powerful.
- If the user gives an irrelevant answer or avoids creating a mantra: Redirect them: "Step 4 is about creating your personal mantra - a powerful statement to guide you through difficult times. Based on our conversation about accepting your circumstances, finding positivity, and learning from past patterns, what powerful statement could you tell yourself daily? For example: 'I am resilient and can handle anything' or 'I control my response, not my situation.' What resonates with you?"
- If the user says they don't know: Provide guidance: "Let's build this together. Think about the strength you want to feel. Do you want to focus on resilience, control, positivity, or growth? A good mantra is personal, positive, and actionable. What quality do you most want to develop?"

The key question is: "What is a powerful mantra that resonates with you based on our conversation?"

Help them create a final integrated statement and then move to implementation guidance."""

    def get_response(self, message: str) -> str:
        if self.has_api_key:
            return self._get_ai_response(message)
        else:
            return self._get_fallback_response(message)
    
    def _get_ai_response(self, message: str) -> str:
        prompt = self.get_step_prompt(self.current_step, message)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            coach_response = response.choices[0].message.content
            self.add_to_memory(message, coach_response)
            
            # Check if we should advance to next step based on response
            if self._should_advance_step(coach_response):
                self.current_step += 1
                
            return coach_response
            
        except Exception as e:
            return self._get_fallback_response(message)
    
    def _get_fallback_response(self, message: str) -> str:
        """Fallback responses when AI is not available"""
        
        if self.current_step == 1:
            if self._is_relevant_to_circumstances(message):
                self.current_step = 2
                return f"""Thank you for sharing your circumstances. I can see you're dealing with challenging situations that require acceptance.

Remember: You can control your response even if you can't control the situation. Focus your energy on what you can influence rather than what's outside your control.

Now let's move to Step 2: Finding Positivity in the Situation.

What is the most positive way you can view your current circumstances? Even in challenges, there are often growth opportunities or silver linings. What might you be learning or gaining from this experience?"""
            else:
                return """I understand, but let's focus on Step 1 of our framework. To build an effective mindset, we need to start by identifying what you're currently facing. 

What challenging circumstances or difficult situation are you currently dealing with that you need to accept? This could be work stress, relationship issues, health concerns, financial worries, or personal goals."""

        elif self.current_step == 2:
            if self._is_relevant_to_positivity(message):
                self.current_step = 3
                return f"""Great work finding positivity in your situation! That mindset shift is crucial for building resilience.

Now let's move to Step 3: Evaluating Past Ineffective Mindsets.

To build a better mindset, we need to understand what hasn't worked before. Can you think of a time when your thinking or attitude made a situation harder for you? 

What thoughts or mental patterns have created challenges for you in the past?"""
            else:
                return """I understand this is difficult, but Step 2 requires us to find positivity in your situation. Even in challenging circumstances, there are often silver linings or growth opportunities.

Let me ask you again: What is the most positive way you can view your current circumstances? What might you be learning or gaining from this experience?"""

        elif self.current_step == 3:
            if self._is_relevant_to_past_patterns(message):
                self.current_step = 4
                return f"""Thank you for reflecting on your past mindset patterns. Learning from what hasn't worked is essential for growth.

Now let's move to Step 4: Creating Your Mindset Mantra.

Based on our conversation about accepting your circumstances, finding positivity, and learning from past patterns, what powerful statement could you tell yourself daily?

For example: 'I am resilient and can handle anything' or 'I control my response, not my situation.' What resonates with you?"""
            else:
                return """Let's focus on Step 3 - learning from your past mindset patterns. To build a better mindset, we need to understand what hasn't worked before.

Can you think of a time when your thinking or attitude made a situation harder for you? What thoughts or mental patterns have created challenges for you in the past?"""

        elif self.current_step == 4:
            if self._is_relevant_to_mantra(message):
                # Generate final mantra and save it
                final_mantra = self._generate_final_mantra(message)
                self.user_responses['final_mantra'] = final_mantra
                return f"""Perfect! Your personalized mindset mantra is:

**"{final_mantra}"**

This mantra combines your insights about acceptance, positivity, and learning from the past. 

Here's how to implement it daily:
- Say it every morning when you wake up
- Repeat it during stressful moments
- Write it somewhere you'll see it regularly
- Use it as your phone wallpaper or screensaver
- Share it with someone who can help keep you accountable

Remember: Mindset is greater than circumstances. You have the power to shape your perspective and response, no matter what you're facing.

Congratulations on completing the Building Effective Mindsets Framework! 🎉"""
            else:
                return """Step 4 is about creating your personal mantra - a powerful statement to guide you through difficult times.

Based on our conversation about accepting your circumstances, finding positivity, and learning from past patterns, what powerful statement could you tell yourself daily?

For example: 'I am resilient and can handle anything' or 'I control my response, not my situation.' What resonates with you?"""

        return "Continue reflecting on building your effective mindset. Remember: Mindset is greater than circumstances!"
    
    def _should_advance_step(self, response: str) -> bool:
        """Determine if we should advance to next step based on AI response"""
        advance_indicators = [
            "move to step",
            "let's move to",
            "now for step",
            "step 2:",
            "step 3:",
            "step 4:",
            "congratulations"
        ]
        return any(indicator in response.lower() for indicator in advance_indicators)
    
    def _is_relevant_to_circumstances(self, message: str) -> bool:
        """Check if message addresses circumstances/challenges"""
        keywords = ['stress', 'problem', 'challenge', 'difficult', 'issue', 'worry', 'struggle', 'hard', 'tough', 'facing']
        return any(keyword in message.lower() for keyword in keywords) and len(message.split()) > 3
    
    def _is_relevant_to_positivity(self, message: str) -> bool:
        """Check if message addresses positivity/silver linings"""
        keywords = ['positive', 'good', 'learn', 'grow', 'opportunity', 'better', 'grateful', 'silver lining', 'bright side']
        return any(keyword in message.lower() for keyword in keywords) and len(message.split()) > 3
    
    def _is_relevant_to_past_patterns(self, message: str) -> bool:
        """Check if message addresses past mindset patterns"""
        keywords = ['past', 'before', 'used to', 'would', 'always', 'pattern', 'habit', 'thinking', 'attitude', 'mindset']
        return any(keyword in message.lower() for keyword in keywords) and len(message.split()) > 3
    
    def _is_relevant_to_mantra(self, message: str) -> bool:
        """Check if message proposes a mantra or engages with mantra creation"""
        keywords = ['i am', 'i will', 'i can', 'i control', 'mantra', 'statement', 'tell myself', 'resilient', 'strong']
        return any(keyword in message.lower() for keyword in keywords) or len(message.split()) > 2
    
    def _generate_final_mantra(self, user_input: str) -> str:
        """Generate or refine the final mantra based on user input"""
        # If user provided a clear mantra, use it
        if any(phrase in user_input.lower() for phrase in ['i am', 'i will', 'i can', 'i control']):
            return user_input.strip().strip('"').strip("'")
        
        # Otherwise, create one based on common themes
        default_mantras = [
            "I am resilient and can handle any challenge",
            "I control my response, not my circumstances", 
            "I find strength and growth in every situation",
            "I am greater than any obstacle I face",
            "I choose positivity and forward movement"
        ]
        
        # Simple selection based on user input keywords
        if 'control' in user_input.lower():
            return "I control my response, not my circumstances"
        elif 'strong' in user_input.lower() or 'resilient' in user_input.lower():
            return "I am resilient and can handle any challenge"
        elif 'positive' in user_input.lower():
            return "I choose positivity and forward movement"
        elif 'grow' in user_input.lower():
            return "I find strength and growth in every situation"
        else:
            return "I am greater than any obstacle I face"

    def get_initial_question(self) -> str:
        return """Hello! I'm your AI mindset coach, and I'm excited to help you build an effective mindset using a proven framework.

Core Principle: *Mindset is greater than circumstances.* 

No matter what you're facing, your mindset will determine how successfully you navigate challenges and opportunities. You have the ability to shape your perspective and behavioral response, no matter your situation.

Let's begin with Step 1: Accept the Circumstances

What challenging circumstances or difficult situation are you dealing with right now that you'd like to develop a better mindset around?

This could be anything - work stress, relationship issues, health concerns, financial worries, personal goals, or any other challenge. Share what's on your mind, and we'll tackle this step by step!"""

def main():
    """Simple command line interface for the mindset coach"""
    print("=" * 60)
    print("🧠 AI MINDSET COACH")
    print("Building Effective Mindsets Through Guided Conversation")
    print("=" * 60)
    
    # Get API key
    api_key = input("Enter OpenAI API Key (optional, press Enter to skip): ").strip()
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY', '')
    
    # Initialize coach
    coach = MindsetCoach(api_key)
    
    # Start conversation
    print("\n" + coach.get_initial_question())
    
    # Main conversation loop
    while True:
        try:
            print(f"\n[Step {coach.current_step}/4]")
            user_input = input("\nYour response: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nThank you for using the AI Mindset Coach. Remember: Mindset is greater than circumstances! 🌟")
                break
            
            if not user_input:
                print("Please provide a response to continue...")
                continue
            
            print("\n" + "="*50)
            response = coach.get_response(user_input)
            print(response)
            print("="*50)
            
            # Check if we've completed all steps
            if coach.current_step > 4 or 'congratulations' in response.lower():
                print(f"\n🎉 Congratulations! You've completed the mindset framework!")
                if coach.user_responses['final_mantra']:
                    print(f"\nYour Final Mantra: \"{coach.user_responses['final_mantra']}\"")
                print("\nRemember to implement this mantra daily for lasting change!")
                break
                
        except KeyboardInterrupt:
            print("\n\nSession ended. Take care and remember: Mindset is greater than circumstances! 🌟")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again...")

if __name__ == "__main__":
    main()