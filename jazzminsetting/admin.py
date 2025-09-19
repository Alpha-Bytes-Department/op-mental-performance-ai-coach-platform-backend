from django.contrib import admin
from .models import AdminPreferences

@admin.register(AdminPreferences)
class AdminPreferencesAdmin(admin.ModelAdmin):
    list_display = ('theme',)