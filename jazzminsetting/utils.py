from django.apps import apps

def get_admin_theme():
    try:
        if apps.ready:
            from .models import AdminPreferences  
            pref = AdminPreferences.objects.first()
            return pref.theme if pref else 'darkly'
        else:
            return 'darkly'
    except Exception as e:
        return 'darkly'