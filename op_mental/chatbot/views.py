from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import ChatSession, ChatMessage
from .serializers import ChatRequestSerializer, ChatResponseSerializer
from .chatbot_logic import GeneralChatSystem

class ChatbotApiView(APIView):
    """API view to interact with the chatbot."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        user_message = validated_data['message']
        session_id = validated_data.get('session_id')
        age_group = validated_data.get('age_group')
        user = request.user

        # Get or create a chat session
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=user)
            except ChatSession.DoesNotExist:
                return Response({"error": "Chat session not found or you do not have permission to access it."}, status=status.HTTP_404_NOT_FOUND)
        else:
            session = ChatSession.objects.create(user=user)

        # Load history from the database
        db_messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
        
        # Format history for the chatbot logic
        conversation_history = []
        for db_message in db_messages:
            conversation_history.append({
                "user_message": db_message.user_message,
                "bot_response": db_message.bot_response,
                "full_conversation": f"User: {db_message.user_message}\nBot: {db_message.bot_response}"
            })

        # Initialize and run the chatbot logic
        chat_system = GeneralChatSystem()
        chat_system.load_history(conversation_history)
        bot_response = chat_system.get_response(user_message, age_group)

        # Save the new exchange to the database
        ChatMessage.objects.create(
            session=session,
            user_message=user_message,
            bot_response=bot_response
        )

        # Prepare and return the response
        response_serializer = ChatResponseSerializer({
            'reply': bot_response,
            'session_id': session.id
        })

        return Response(response_serializer.data, status=status.HTTP_200_OK)
