from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone

from .models import ChallengeSession
from .challenge_logic import InternalChallengeTherapySystem, TherapyPhase
from .serializers import ChallengeRequestSerializer, ChallengeResponseSerializer
from subscriptions.models import UserSubscription
from chatbot.models import UserChatCounter

class ChallengeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChallengeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        user = request.user
        session_id = validated_data.get('session_id')
        user_message = validated_data.get('message')

        if not session_id:
            # New session: return welcome message and create session
            session = ChallengeSession.objects.create(user=user, current_phase=TherapyPhase.IDENTIFICATION.name)
            
            welcome_message = {
                "session_id": session.id,
                "is_session_complete": False,
                "response_type": "welcome",
                "message": [
                    "Welcome to Internal Challenge Therapy - 5-Phase Framework",
                    "I'm here to guide you through a therapeutic journey to understand and overcome your internal challenges.",
                    "We'll work through 5 phases together:",
                    "   Phase 1: Identification",
                    "   Phase 2: Exploration",
                    "   Phase 3: Reframing & Strengths",
                    "   Phase 4: Action Planning",
                    "   Phase 5: Reflection & Adaptation",
                    "Remember: This is a safe space. All experiences are welcomed and explored.",
                    "Let's start by understanding what you're facing..."
                ],
                "question": "What internal challenge would you like to work through today? Please share what's on your mind:"
            }
            return Response(welcome_message, status=status.HTTP_200_OK)

        # Existing session
        session = ChallengeSession.objects.filter(id=session_id, user=user).first()
        if not session:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.is_complete:
            return Response({"detail": "This session is complete."}, status=status.HTTP_400_BAD_REQUEST)

        therapy_system = self._load_system_from_session(session)

        # First message after welcome
        if not therapy_system.conversation_history:
            therapy_system.challenge_type = therapy_system.identify_challenge_type(user_message)
            # Manually add first user message to history
            therapy_system.conversation_history.append({
                "timestamp": timezone.now().isoformat(),
                "phase": "Initial",
                "question": "What internal challenge would you like to work through today? Please share what's on your mind:",
                "response": user_message,
                "question_key": "initial_challenge"
            })
            
            current_question = therapy_system.get_current_question()
            session = self._update_session_from_system(session, therapy_system)
            response_data = {
                "session_id": session.id,
                "is_session_complete": False,
                "phase": therapy_system.current_phase.value,
                "phase_goal": therapy_system.phase_goals[therapy_system.current_phase],
                "question": current_question['question'],
                "response_type": "continue"
            }
            return Response(ChallengeResponseSerializer(response_data).data, status=status.HTTP_200_OK)

        # Process subsequent messages
        result = therapy_system.process_response(user_message)
        session = self._update_session_from_system(session, therapy_system)
        response_data = self._prepare_response(session, therapy_system, result)
        
        return Response(ChallengeResponseSerializer(response_data).data, status=status.HTTP_200_OK)

    def _load_system_from_session(self, session: ChallengeSession) -> InternalChallengeTherapySystem:
        system = InternalChallengeTherapySystem()
        system.session_data = session.session_data
        system.conversation_history = session.conversation_history
        system.current_phase = TherapyPhase[session.current_phase]
        system.challenge_type = system.identify_challenge_type(session.challenge_type) # Use enum member
        system.current_question_index = session.current_question_index
        return system

    def _update_session_from_system(self, session: ChallengeSession, system: InternalChallengeTherapySystem) -> ChallengeSession:
        session.session_data = system.session_data
        session.conversation_history = system.conversation_history
        session.current_phase = system.current_phase.name
        session.challenge_type = system.challenge_type.value
        session.current_question_index = system.current_question_index
        session.save()
        return session

    def _prepare_response(self, session: ChallengeSession, system: InternalChallengeTherapySystem, result: dict) -> dict:
        response = {
            "session_id": session.id,
            "is_session_complete": session.is_complete,
            "phase": system.current_phase.value,
            "phase_goal": system.phase_goals[system.current_phase],
            "question": None,
            "error_message": None,
            "summary": None,
            "response_type": result.get('status')
        }

        if result['status'] == 'invalid_response':
            response['error_message'] = result['error']
            response['question'] = result['question']
        elif result['status'] == 'phase_complete':
            response['summary'] = system.get_phase_summary()
            if not system.advance_to_next_phase():
                session.is_complete = True
                response['is_session_complete'] = True
                response['summary'] = system.generate_final_therapeutic_summary()
                response['response_type'] = 'final_summary'
            session.save()
        else: # continue
            current_question = system.get_current_question()
            if current_question:
                response['question'] = current_question['question']
        
        return response


class ChallengeHistoryView(APIView):
    """API view to fetch the conversation history of a specific challenge session."""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, *args, **kwargs):
        try:
            session = ChallengeSession.objects.get(id=session_id, user=request.user)
            return Response(session.conversation_history, status=status.HTTP_200_OK)
        except ChallengeSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
    
   