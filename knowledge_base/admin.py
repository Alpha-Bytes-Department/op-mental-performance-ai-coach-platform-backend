from django.contrib import admin
from .models import KnowledgeDocument


# Register your models here.
@admin.register(KnowledgeDocument)
class KnowlegeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title","domain","uploaded_at")
    