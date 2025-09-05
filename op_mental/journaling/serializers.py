from rest_framework import serializers
from .models import JournalSession, JournalEntry

class JournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = ('author', 'message', 'timestamp')

class JournalSessionSerializer(serializers.ModelSerializer):
    Entries = JournalEntrySerializer(many=True, read_only=True)

    class Meta:
        model = JournalSession
        fields = ('id', 'user', 'category', 'summary', 'created_at', 'Entries')
        read_only_fields = ('user',)

class JournalSessionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalSession
        fields = ('id', 'category', 'created_at')

class JournalingStatisticsSerializer(serializers.Serializer):
    category_counts = serializers.DictField(child=serializers.IntegerField())
    total_entries = serializers.IntegerField()
    this_month_entries = serializers.IntegerField()
    last_week_entries = serializers.IntegerField()