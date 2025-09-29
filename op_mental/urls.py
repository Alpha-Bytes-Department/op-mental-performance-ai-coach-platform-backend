
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),  # Include user management URLs
    path('api/', include('reviews.urls')), # Include review app URLs
    path('api/', include('journaling.urls')), # Include journaling app URLs
    path('api/subscriptions/', include('subscriptions.urls')),  # Include subscription management URLs
    path('api/chatbot/', include('chatbot.urls')),  # Include chatbot app URLs
    path('api/mindset/', include('mindset.urls')),  # Include mindset coach app URLs
    path('api/internal-challenge/', include('internal_challenge.urls')),
    path('api/knowledge-base/', include('knowledge_base.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
