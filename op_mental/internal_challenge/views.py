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

        # Print the request message to the terminal for testing
        print("\n--- Internal Challenge Request ---")
        print(f"User: {request.user.email}")
        print(f"Request Body: {validated_data}")
        print("------------------------------------\n")

        user = request.user
        session_id = validated_data.get('session_id')
        user_message = validated_data['message']

        # Subscription check (Temporarily disabled for testing)
        # The rule is that only subscribed users can use this feature.
        # has_active_subscription = UserSubscription.objects.filter(
        #     user=user, status='active', end_date__gte=timezone.now()
        # ).exists()
        #
        # if not has_active_subscription:
        #     return Response(
        #         {"detail": "You must have an active subscription to use this feature."},
        #         status=status.HTTP_402_PAYMENT_REQUIRED
        #     )

        # Get or create session
        if session_id:
            session = ChallengeSession.objects.filter(id=session_id, user=user).first()
        else:
            session = None

        if not session:
            session = ChallengeSession.objects.create(user=user, current_phase=TherapyPhase.IDENTIFICATION.name)

        # Load therapy system from session state
        therapy_system = self._load_system_from_session(session)

        # Process message
        if session.is_complete:
            return Response({"detail": "This session is complete."}, status=status.HTTP_400_BAD_REQUEST)

        # First message of a new session identifies the challenge type
        if not therapy_system.conversation_history:
             therapy_system.challenge_type = therapy_system.identify_challenge_type(user_message)

        result = therapy_system.process_response(user_message)

        # Update and save session state
        session = self._update_session_from_system(session, therapy_system)

        # Construct response
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
    
   