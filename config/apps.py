from django.apps import AppConfig
import os
from django.db.utils import ProgrammingError


class ConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config'

    def ready(self):
        """
        Load configuration variables from the database into environment variables.
        This method is called when the app is ready.
        """
        try:
            # Import the ConfigVariable model here to avoid circular imports
            from .models import ConfigVariable
            if ConfigVariable.objects.exists():
                for config in ConfigVariable.objects.all():
                    os.environ[config.key] = config.value
        except ProgrammingError:
            # This can happen if the database is not yet created (e.g., during migrations)
            pass
        except Exception as e:
            # Log other potential exceptions
            print(f"Could not load config from DB in ready(): {e}")
