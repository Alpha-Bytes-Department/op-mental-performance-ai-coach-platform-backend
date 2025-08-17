from rest_framework import generics
from .models import Journal
from .serializers import JournalSerializer
from rest_framework.permissions import IsAuthenticated

class JournalListCreateView(generics.ListCreateAPIView):
    serializer_class = JournalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Journal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class JournalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JournalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Journal.objects.filter(user=self.request.user)
