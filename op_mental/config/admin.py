from django.contrib import admin
from .models import ConfigVariable

@admin.register(ConfigVariable)
class ConfigVariableAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ('key',)