from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import uuid
import json

from .models import RedisChatSession, UserChatCounter
from .serializers import ChatRequestSerializer, ChatResponseSerializer
from .chatbot_logic import GeneralChatSystem
from subscriptions.models import UserSubscription


# Define the 24-hour timeout in seconds
SESSION_TIMEOUT = 24 * 60 * 60

class ChatbotApiView(APIView):
    """API view to interact with the chatbot using a hybrid Redis/DB approach."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        user = request.user
        session_id = validated_data.get('session_id')

        # Check for an active subscription
        has_active_subscription = UserSubscription.objects.filter(
            user=user,
            status='active',
            end_date__gte=timezone.now()
        ).exists()

        # If user is not subscribed, check their message count
        counter = None
        if not has_active_subscription:
            counter, created = UserChatCounter.objects.get_or_create(user=user)
            if counter.message_count >= 5:
                # Ensure a session_id exists for the response
                if not session_id:
                    new_session_id = uuid.uuid4()
                    RedisChatSession.objects.create(id=new_session_id, user=request.user)
                    session_id = str(new_session_id)
                
                return Response(
                    {
                        "reply": "You have reached your free message limit. Please subscribe for unlimited access.",
                        "session_id": session_id
                    },
                    status=status.HTTP_208_ALREADY_REPORTED
                )

        user_message = validated_data['message']
        age_group = validated_data.get('age_group')

        # If no session_id is provided, create a new one
        if not session_id:
            new_session_id = uuid.uuid4()
            # Create a DB record to map user to session ID
            RedisChatSession.objects.create(id=new_session_id, user=request.user)
            session_id = str(new_session_id)

        redis_key = f"chat:{session_id}"

        # Retrieve history from Redis
        history_json = cache.get(redis_key)
        history = json.loads(history_json) if history_json else []

        # Format history for the chatbot logic
        formatted_history = []
        for item in history:
            formatted_history.append({
                "user_message": item.get('message') if item.get('role') == 'user' else None,
                "bot_response": item.get('message') if item.get('role') == 'assistant' else None,
                "full_conversation": f"User: {item.get('message') if item.get('role') == 'user' else ''}\nBot: {item.get('message') if item.get('role') == 'assistant' else ''}"
            })

        # Initialize and run the chatbot logic
        chat_system = GeneralChatSystem()
        chat_system.load_history(formatted_history)
        bot_response = chat_system.get_response(user_message, age_group)

        # Append the new exchange to the history
        history.append({
            "role": "user",
            "message": user_message
        })
        history.append({
            "role": "assistant",
            "message": bot_response
        })

        # Save updated history back to Redis with a 24-hour TTL
        cache.set(redis_key, json.dumps(history), timeout=SESSION_TIMEOUT)

        # If user is not subscribed, increment their message count after a successful response
        if not has_active_subscription and counter:
            counter.message_count += 1
            counter.save()

        # Prepare and return the response
        response_serializer = ChatResponseSerializer({
            'reply': bot_response,
            'session_id': session_id
        })

        return Response(response_serializer.data, status=status.HTTP_200_OK)



class AllUserChatHistoryView(APIView):
    """API view to fetch all chat histories for a user from the last 24 hours."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        
        # 1. Find all recent session IDs for the user from the database
        recent_sessions = RedisChatSession.objects.filter(
            user=request.user,
            created_at__gte=twenty_four_hours_ago
        ).values_list('id', flat=True)

        all_messages = []
        # 2. For each session ID, fetch the history from Redis
        for session_id in recent_sessions:
            redis_key = f"chat:{str(session_id)}"
            history_json = cache.get(redis_key)
            if history_json:
                history = json.loads(history_json)
                # Add session_id to each message for context on the frontend
                for message in history:
                    message['session_id'] = str(session_id)
                all_messages.extend(history)
        
        # Optional: Sort all messages by a timestamp if messages had one.
        # For now, they are grouped by session.
        return Response(all_messages, status=status.HTTP_200_OK)