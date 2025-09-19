from django.apps import AppConfig
from django.conf import settings

class JazzminsettingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jazzminsetting'

    def ready(self):
        from .models import AdminPreferences
        try:
            pref = AdminPreferences.objects.first()
            if pref:
                settings.JAZZMIN_UI_TWEAKS["dark_mode_theme"] = pref.theme
        except:
            pass
