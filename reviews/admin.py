from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(status='approved')
    approve_reviews.short_description = "Approve selected reviews"