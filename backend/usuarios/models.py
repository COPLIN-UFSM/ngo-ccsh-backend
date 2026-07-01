from django.db import models

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

class Pessoa(models.Model):
    id_pessoa = models.AutoField(primary_key=True, db_column="id_pessoa")
    matricula = models.TextField(max_length=32, unique=True, null=False, blank=False, db_column="matricula")
    nome_pessoa = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nome_pessoa")
    # TODO vinculo e cargo precisam ser normalizados!
    vinculo = models.TextField(max_length=64, unique=False, null=False, blank=False, db_column="vinculo")
    cargo = models.TextField(max_length=128, unique=False, null=True, blank=True, db_column="cargo")
    # TODO vinculo e cargo precisam ser normalizados!
    cpf = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="cpf")
    rg = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="rg")
    ativo = models.BooleanField(unique=False, null=False, blank=False, db_column="ativo")

    class Meta:
        managed = False
        db_table = "v_pessoas"


class UserManager(BaseUserManager):
    def create_user(self, matricula, email, password=None, **extra_fields):
        fields = {"matricula": matricula, "email": email}
        for key, value in fields.items():
            if not value:
                raise ValueError(f"O usuário deve ter um {key}.")

        email = self.normalize_email(email=email)
        user = self.model(matricula=matricula, email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, matricula, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Um super-usuário deve ter is_staff=True.")

        if not extra_fields.get("is_superuser"):
            raise ValueError("Um super-usuário deve ter is_superuser=True.")

        return self.create_user(
            matricula,
            email,
            password,
            **extra_fields,
        )


class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True, editable=False, db_column="id")

    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.DO_NOTHING,
        db_column="id_pessoa",
    )

    email = models.EmailField(unique=True, db_column='email')

    is_active = models.BooleanField(blank=True, default=True, db_column='is_active')
    is_staff = models.BooleanField(blank=True, default=False, db_column='is_staff')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    @property
    def matricula(self):
        return self.pessoa.matricula

    @property
    def full_name(self):
        return self.pessoa.nome_pessoa

    class Meta:
        managed = False
        db_table = "usuarios"

        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    objects: UserManager = UserManager()

    USERNAME_FIELD = "matricula"
    EMAIL_FIELD = "email"

    REQUIRED_FIELDS = ["email", "full_name"]

    def __str__(self):
        return f'{self.full_name} ({self.matricula})'
