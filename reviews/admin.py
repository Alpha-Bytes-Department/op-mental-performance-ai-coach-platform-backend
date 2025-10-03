from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer_name', 'role', 'rating', 'status', 'created_at')
    list_filter = ('status', 'rating', 'role')
    search_fields = ('reviewer_name', 'description')
    readonly_fields = ('created_at',)
    list_editable = ('status',)
    
    fieldsets = (
        ('Review Information', {
            'fields': ('reviewer_name', 'role', 'rating', 'description')
        }),
        ('Status', {
            'fields': ('status', 'created_at')
        }),
    )