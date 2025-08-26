
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import MindsetSession, MindsetMessage
from .serializers import MindsetRequestSerializer, MindsetResponseSerializer
from .mindset_logic import MindsetCoach

class MindsetCoachApiView(APIView):
    """API view to interact with the Mindset Coach chatbot."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = MindsetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        user_message = validated_data['message']
        session_id = validated_data.get('session_id')
        user = request.user

        coach = MindsetCoach()
        is_new_session = False

        if session_id:
            try:
                session = MindsetSession.objects.get(id=session_id, user=user)
            except MindsetSession.DoesNotExist:
                return Response({"error": "Mindset session not found or you do not have permission to access it."}, status=status.HTTP_404_NOT_FOUND)
        else:
            session = MindsetSession.objects.create(user=user)
            is_new_session = True

        # If it's a brand new session, get the initial question
        if is_new_session:
            coach_response = coach.get_initial_question()
            # Save the initial (empty) user message and the first question
            MindsetMessage.objects.create(
                session=session,
                user_message="<initial>",
                coach_response=coach_response
            )
        else:
            # Load state from the database for an existing session
            db_messages = MindsetMessage.objects.filter(session=session).order_by('timestamp')
            history = [{
                "user_message": msg.user_message,
                "coach_response": msg.coach_response
            } for msg in db_messages]

            session_data = {
                'current_step': session.current_step,
                'user_responses': session.user_responses,
                'history': history
            }
            coach.load_state(session_data)

            # Get the next response from the coach
            coach_response = coach.get_response(user_message)

            # Save the new exchange
            MindsetMessage.objects.create(
                session=session,
                user_message=user_message,
                coach_response=coach_response
            )

        # Update the session state in the database
        updated_state = coach.get_state()
        session.current_step = updated_state['current_step']
        session.user_responses = updated_state['user_responses']
        session.save()

        # Prepare and return the response
        response_serializer = MindsetResponseSerializer({
            'reply': coach_response,
            'session_id': session.id,
            'current_step': session.current_step,
            'is_complete': session.current_step > 4
        })

        return Response(response_serializer.data, status=status.HTTP_200_OK)
