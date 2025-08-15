from rest_framework import serializers
from .models import Review
from users.serializers import UserProfileSerializer

class ReviewListSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'rating', 'description', 'created_at')

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('rating', 'description')
