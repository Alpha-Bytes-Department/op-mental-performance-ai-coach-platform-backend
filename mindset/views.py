
import os
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
        user_message = validated_data.get('message', '')
        session_id = validated_data.get('session_id')
        user = request.user

        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return Response({"error": "OpenAI API key not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            coach = MindsetCoach(api_key=api_key)

            if not session_id:
                # New session
                session = MindsetSession.objects.create(user=user)
                welcome_message = coach.get_welcome_message()
                initial_question = coach.get_initial_question()
                full_welcome_message = f"{welcome_message}\n\n{initial_question}"
                
                MindsetMessage.objects.create(
                    session=session,
                    user_message="<start>",
                    coach_response=full_welcome_message
                )
                
                response_data = {
                    'reply': full_welcome_message,
                    'session_id': session.id,
                    'current_step': session.current_step,
                    'is_complete': False
                }
            else:
                # Existing session
                session = MindsetSession.objects.get(id=session_id, user=user)
                
                # Simple validation from mindset_mantra.py
                message_lower = user_message.lower().strip()
                word_count = len(message_lower.split())
                minimal_responses = ['start', 'next', 'go', 'ok', 'okay', 'yes', 'no', 'y', 'n']

                if message_lower in minimal_responses or word_count < 2:
                    # Get the last question to repeat it
                    last_message = MindsetMessage.objects.filter(session=session).order_by('-timestamp').first()
                    if last_message:
                        question_to_repeat = last_message.coach_response
                        # A more specific prompt for the user
                        if "Welcome to Your Mindset Transformation!" in question_to_repeat:
                            question_to_repeat = "Let's start by understanding what you're facing. What challenging circumstances are you currently facing that you need to accept?"

                    else:
                        question_to_repeat = "Please provide a more detailed response."

                    return Response({
                        'reply': f"Please provide a more detailed response. Even a few words will help. {question_to_repeat}",
                        'session_id': session.id,
                        'current_step': session.current_step,
                        'is_complete': False
                    }, status=status.HTTP_200_OK)

                messages_count = MindsetMessage.objects.filter(session=session).count()

                # Ongoing conversation
                db_messages = MindsetMessage.objects.filter(session=session).order_by('timestamp')
                history = [{
                    "user_message": msg.user_message,
                    "coach_response": msg.coach_response,
                    'step': msg.session.current_step
                } for msg in db_messages]

                session_data = {
                    'current_step': session.current_step,
                    'user_responses': session.user_responses,
                    'history': history
                }

                response = coach.get_response(user_message, session_data)
                coach_response = response['reply']
                updated_state = response['updated_state']

                MindsetMessage.objects.create(
                    session=session,
                    user_message=user_message,
                    coach_response=coach_response
                )

                session.current_step = updated_state['current_step']
                session.user_responses = updated_state['user_responses']
                session.save()

                is_complete = session.current_step > 4
                
                if is_complete:
                    session.delete()  # This cascades and deletes all related MindsetMessage objects.
                    session_id_to_return = None  # The session is gone.
                else:
                    session_id_to_return = session.id
                
                response_data = {
                    'reply': coach_response,
                    'session_id': session_id_to_return,
                    'current_step': updated_state['current_step'],
                    'is_complete': is_complete
                }

            return Response(MindsetResponseSerializer(response_data).data, status=status.HTTP_200_OK)

        except MindsetSession.DoesNotExist:
            return Response({"error": "Mindset session not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MindsetHistoryView(APIView):
    """API view to fetch the conversation history of a specific mindset session."""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, *args, **kwargs):
        try:
            session = MindsetSession.objects.get(id=session_id, user=request.user)
            messages = MindsetMessage.objects.filter(session=session).order_by('timestamp')
            
            history = []
            for msg in messages:
                if msg.user_message != "<start>" and msg.user_message != "<initial>":
                    history.append({'author': 'user', 'message': msg.user_message, 'timestamp': msg.timestamp})
                history.append({'author': 'bot', 'message': msg.coach_response, 'timestamp': msg.timestamp})

            return Response(history, status=status.HTTP_200_OK)
        except MindsetSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
