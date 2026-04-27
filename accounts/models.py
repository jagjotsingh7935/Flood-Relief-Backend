from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    is_admin=models.BooleanField(default=False)
    is_person = models.BooleanField(default=False)

    def __str__(self) :
        return self.username
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"




class Admin(models.Model):
    user=models.OneToOneField(User, related_name="admin", on_delete=models.CASCADE)
    username = None
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    first_name = models.CharField(max_length=100,null=True, blank=True)
    last_name = models.CharField(max_length=100,null=True, blank=True)
    full_name = models.CharField(max_length=200)
    avatar_image = models.ImageField(upload_to='files/accounts/admin_users_images', null=True, blank=True)
    phone_number = models.CharField(max_length=15,null=True, blank=True)
    created_at = models.DateTimeField( auto_now_add=True)
    last_updated = models.DateTimeField( auto_now=True)

    def __str__(self):
        return self.email
    

    class Meta:
        verbose_name = "Admin"
        verbose_name_plural = "Admins"
        



class UserLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
    )

    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='user_logs', null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} - {self.action} - {self.created_at}"

    class Meta:
        verbose_name = "User Log"
        verbose_name_plural = "User Logs"
