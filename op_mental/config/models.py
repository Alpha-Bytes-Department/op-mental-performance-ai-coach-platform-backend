from django.db import models

class ConfigVariable(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.key