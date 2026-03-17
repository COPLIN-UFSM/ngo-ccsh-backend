from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from typing import ClassVar

from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, username, email, password, **extra_fields):
        fields = {"username": username, "email": email}
        for key, value in fields.items():
            if not value:
                raise ValueError(f"O usuário deve ter um {key}.")

        email = self.normalize_email(email=email)
        user = self.model(username=username, email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True, editable=False, db_column="id_usuario")
    username = models.CharField(unique=True, max_length=32)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(blank=True, default=True)
    is_staff = models.BooleanField(blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "usuarios"
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    objects: UserManager = UserManager()
    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"

    REQUIRED_FIELDS = ["email", "full_name"]

    def set_password(self, raw_password: str | None) -> None:
        return super().set_password(raw_password)

    def __str__(self):
        return self.username
