from rest_framework import serializers
from .models import Review

class ReviewListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('id', 'reviewer_name', 'role', 'rating', 'description', 'created_at')

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('reviewer_name', 'role', 'rating', 'description')