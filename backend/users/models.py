from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# Precisa ? Porque existe apenas usuário logado, usuário não logado e super_user
# class Permissoes(models.Model):
#     id_permissao = models.IntegerField(primary_key=True)
#     permissao = models.CharField(max_length=15)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, max_length=100)
    # permissao = models.ForeignKey(
    #     Permissoes, models.DO_NOTHING, db_column="usuario_permissoes"
    # )

    class Meta:
        managed = True
        db_table = "usuarios"

    def __str__(self):
        return self.username

    def get_email(self):
        return self.email
