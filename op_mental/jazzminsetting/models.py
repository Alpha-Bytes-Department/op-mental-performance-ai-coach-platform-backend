from django.db import models

class AdminPreferences(models.Model):
    theme = models.CharField(
        max_length=50,
        choices=[
            ('darkly', 'Darkly'),
            ('flatly', 'Flatly'),
            ('cerulean', 'Cerulean'),
            ('slate', 'Slate'),
            ('journal', 'Journal'),
        ],
        default='darkly'
    )

    def __str__(self):
        return f"Admin Theme: {self.theme}"
