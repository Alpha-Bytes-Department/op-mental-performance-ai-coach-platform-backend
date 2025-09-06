from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import JournalSession, JournalEntry
from .serializers import JournalSessionSerializer, JournalSessionListSerializer, JournalingStatisticsSerializer
from .journal_chat import Journal as JournalChat
from django.utils import timezone
from datetime import timedelta, datetime

class JournalingChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_message = request.data.get('message', '') or ''
        session_id = request.data.get('session_id')
        user = request.user

        if not session_id:
            # Start a new session
            journal_chat = JournalChat()
            response_message = journal_chat.start_system(user_message, is_initial_choice=True)
            
            session = JournalSession.objects.create(
                user=user,
                category=journal_chat.current_session['entry_point']
            )
            session_id = session.id
            JournalEntry.objects.create(session=session, author='user', message=user_message)
            JournalEntry.objects.create(session=session, author='bot', message=response_message)
            
            if journal_chat.current_session.get('session_start') and isinstance(journal_chat.current_session.get('session_start'), datetime):
                journal_chat.current_session['session_start'] = journal_chat.current_session['session_start'].isoformat()
            request.session['journal_chat_session'] = journal_chat.current_session
            return Response({'reply': response_message, 'session_id': session_id})

        else:
            journal_chat_session = request.session.get('journal_chat_session')
            journal_chat = JournalChat()
            if journal_chat_session:
                if journal_chat_session.get('session_start') and isinstance(journal_chat_session.get('session_start'), str):
                    journal_chat_session['session_start'] = datetime.fromisoformat(journal_chat_session['session_start'])
                if journal_chat_session.get('session_active') == 'True':
                    journal_chat_session['session_active'] = True
                else:
                    journal_chat_session['session_active'] = False
                if journal_chat_session.get('is_future_focused') == 'True':
                    journal_chat_session['is_future_focused'] = True
                else:
                    journal_chat_session['is_future_focused'] = False
                journal_chat.current_session = journal_chat_session

            try:
                session = JournalSession.objects.get(id=session_id, user=user)
            except JournalSession.DoesNotExist:
                return Response({"error": "Journal session not found."}, status=status.HTTP_404_NOT_FOUND)

            # Continue existing session
            response_message = journal_chat.start_system(user_message, is_initial_choice=False)

            JournalEntry.objects.create(session=session, author='user', message=user_message)
            JournalEntry.objects.create(session=session, author='bot', message=response_message)

            if "AI LIFE COACH SESSION SUMMARY" in response_message:
                session.summary = response_message
                session.save()
                # Clear the session
                request.session['journal_chat_session'] = journal_chat._reset_session()
            else:
                if journal_chat.current_session.get('session_start') and isinstance(journal_chat.current_session.get('session_start'), datetime):
                    journal_chat.current_session['session_start'] = journal_chat.current_session['session_start'].isoformat()
                request.session['journal_chat_session'] = journal_chat.current_session

            return Response({'reply': response_message, 'session_id': session_id})

            return Response({'reply': response_message, 'session_id': session_id})

class JournalSessionListView(generics.ListAPIView):
    serializer_class = JournalSessionListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JournalSession.objects.filter(user=self.request.user).order_by('-created_at')

class JournalSessionDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = JournalSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JournalSession.objects.filter(user=self.request.user)

class JournalingStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Category counts
        category_counts = {
            'personal_win': JournalSession.objects.filter(user=user, category='personal_win').count(),
            'personal_challenge': JournalSession.objects.filter(user=user, category='personal_challenge').count(),
            'professional_win': JournalSession.objects.filter(user=user, category='professional_win').count(),
            'professional_challenge': JournalSession.objects.filter(user=user, category='professional_challenge').count(),
        }

        # Entry counts
        total_entries = JournalSession.objects.filter(user=user).count()
        this_month_entries = JournalSession.objects.filter(user=user, created_at__gte=timezone.now() - timedelta(days=30)).count()
        last_week_entries = JournalSession.objects.filter(user=user, created_at__gte=timezone.now() - timedelta(days=7)).count()

        data = {
            'category_counts': category_counts,
            'total_entries': total_entries,
            'this_month_entries': this_month_entries,
            'last_week_entries': last_week_entries,
        }

        serializer = JournalingStatisticsSerializer(data)
        return Response(serializer.data)