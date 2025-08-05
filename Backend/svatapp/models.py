
from svatapp.managers import CustomUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
class Vulnerability(models.Model):
    vulnerability_name = models.CharField(max_length=255)
    cve_id = models.CharField(max_length=50, blank=True, null=True)
    cwe_id = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    severity = models.CharField(max_length=50, blank=True, null=True)
    risk = models.CharField(max_length=150, blank=True, null=True)
    recommended_fix = models.TextField(blank=True, null=True)
    cve_url = models.URLField(blank=True, null=True)
    cwe_url = models.URLField(blank=True, null=True)
    collection_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('vulnerability_name', 'cve_id', 'cwe_id', 'collection_name')

class ProcessingResult(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    collection_name = models.CharField(max_length=255)
    response_data = models.JSONField()  
    created_at = models.DateTimeField(auto_now_add=True)
    result_url = models.URLField()  

    class Meta:
        indexes = [
            models.Index(fields=['user', 'collection_name']),
        ]