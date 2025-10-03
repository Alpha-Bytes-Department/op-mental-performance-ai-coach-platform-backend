from django.contrib import admin
from .models import ChatbotSettings


@admin.register(ChatbotSettings)
class ChatbotSettingsAdmin(admin.ModelAdmin):
    """Admin interface for global chatbot settings."""
    list_display = ('allow_chat_history', 'updated_at')

    def has_add_permission(self, request):
        # Allow only one instance
        return not ChatbotSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False
