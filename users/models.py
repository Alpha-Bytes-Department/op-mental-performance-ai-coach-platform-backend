# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager  # Corrected import

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        username = email.split('@')[0]
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        extra_fields.setdefault('username', username)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(_('name'), max_length=255, blank=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    profile_image = models.ImageField(
        _('profile image'),
        upload_to='profile_images/',
        blank=True,
        null=True
    )
    gender = models.CharField(
        _('gender'),
        max_length=10,
        choices=[('Men', 'Men'), ('Women', 'Women'), ('Other', 'Other')],
        blank=True
    )
    description = models.TextField(_('description'), blank=True)
    current_refresh_token = models.TextField(null=True, blank=True)
    force_logout_required = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        
    def __str__(self):
        return self.email
        
    def get_full_name(self):
        return self.name.strip()
        
    def get_short_name(self):
        return self.name.split(' ')[0] if self.name else ''

class SocialAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts')
    provider = models.CharField(max_length=30)
    uid = models.CharField(max_length=255)
    extra_data = models.JSONField(default=dict)

    class Meta:
        unique_together = ('provider', 'uid')
        verbose_name = _('Social Account')
        verbose_name_plural = _('Social Accounts')

    def __str__(self):
        return f'{self.user.email} - {self.provider.capitalize()}'