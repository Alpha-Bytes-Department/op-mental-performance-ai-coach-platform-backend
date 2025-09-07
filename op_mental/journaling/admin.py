from django.contrib import admin
from .models import JournalSession, JournalEntry
# Register your models here.
@admin.register(JournalSession)
class JournalSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'summary', 'created_at','session_data', 'get_entries')
    search_fields = ('user__username', 'category')
    list_filter = ('category', 'created_at')

    def get_entries(self, obj):
        return "\n".join([f"{entry.author}: {entry.message[:50]}..." for entry in obj.entries.all()])
    
    get_entries.short_description = 'Entries'  # Column header in admin

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'author', 'message', 'timestamp')
    search_fields = ('session__id', 'author', 'message')
    list_filter = ('author', 'timestamp')