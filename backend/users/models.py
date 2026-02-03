from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, max_length=100)
    administrador = models.BooleanField(blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = "usuarios"

    def __str__(self):
        return self.username

    def get_email(self):
        return self.email
