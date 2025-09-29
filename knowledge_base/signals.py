from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import KnowledgeDocument
from .services import load_documents

@receiver(post_save, sender=KnowledgeDocument)
def knowledge_document_post_save(sender, instance, created, **kwargs):
    """
    A signal handler that reloads the knowledge base documents whenever a KnowledgeDocument is saved.
    """
    print("Signal received: Reloading knowledge base documents.")
    load_documents()
