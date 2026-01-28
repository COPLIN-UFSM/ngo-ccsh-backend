from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class CustomUser(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    is_student = models.BooleanField(default=False)
    email = models.EmailField(unique=True, max_length=100)

    def __str__(self):
        return self.username

    def get_email(self):
        return self.email
