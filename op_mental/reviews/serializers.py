from rest_framework import serializers
from .models import Review
from users.models import User

class ReviewerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'profile_image')

class ReviewListSerializer(serializers.ModelSerializer):
    user = ReviewerSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'role', 'rating', 'description', 'created_at')

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('role','rating', 'description')