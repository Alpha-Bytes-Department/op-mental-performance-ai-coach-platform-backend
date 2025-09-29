from django.db import models

# Create your models here.
class KnowledgeDocument(models.Model):
    title = models.CharField(max_length=255)
    document_file = models.FileField(upload_to="knowledge_docs/")
    domain = models.CharField(
        max_length=50,
        choices=[
            ("journal", "Journal Coach"),
            ("mindset", "Mindset Coach"),
            ("general", "General Chatbot"),
            ("therapy", "Challenge Therapy"),
            ("all", "All Chatbots"), 
        ],
        default="all"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
