from rest_framework import generics
from .models import Review
from .serializers import ReviewListSerializer, ReviewCreateSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Review.objects.filter(status='approved')

class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
