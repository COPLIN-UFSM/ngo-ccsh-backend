from django.db import models

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

from despesas.models import Centro


class Curso(models.Model):
    id_curso = models.AutoField(primary_key=True, db_column="id_curso")
    centro = models.ForeignKey(Centro, on_delete=models.DO_NOTHING, db_column="centro")
    nome_curso = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nome_curso")
    nivel_curso = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nivel_curso")
    modalidade_curso = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="modalidade_curso")
    classificacao_curso = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="classificacao_curso")

    class Meta:
        managed = False
        db_table = "v_cursos"


class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True, db_column="id_cargo")
    cargo = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="cargo")

    class Meta:
        managed = False
        db_table = "v_cargos"


class Pessoa(models.Model):
    id_pessoa = models.AutoField(primary_key=True, db_column="id_pessoa")
    nome_pessoa = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nome_pessoa")
    cpf = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="cpf")
    rg = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="rg")

    class Meta:
        managed = False
        db_table = "v_pessoas"


class Discente(models.Model):
    id_curso_aluno = models.AutoField(primary_key=True, db_column="id_curso_aluno")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa")
    matricula = models.TextField(max_length=32, unique=True, null=False, blank=False, db_column="matricula")
    curso = models.ForeignKey(Curso, on_delete=models.DO_NOTHING, db_column="id_curso")
    ativo = models.BooleanField(unique=False, null=False, blank=False, db_column="ativo")

    class Meta:
        managed = False
        db_table = "v_discentes"

class Servidor(models.Model):
    id_contrato_rh = models.AutoField(primary_key=True, db_column="id_contrato_rh")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa")
    matricula = models.TextField(max_length=32, unique=True, null=False, blank=False, db_column="matricula")
    cargo = models.ForeignKey(Cargo, on_delete=models.DO_NOTHING, db_column="id_cargo")
    ativo = models.BooleanField(unique=False, null=False, blank=False, db_column="ativo")

    class Meta:
        managed = False
        db_table = "v_servidores"


class UserManager(BaseUserManager):
    def create_user(self, pessoa, email, password=None, **extra_fields):
        if pessoa is None:
            raise ValueError("O usuário deve estar associado a uma pessoa.")

        if not email:
            raise ValueError("O usuário deve possuir um e-mail.")

        email = self.normalize_email(email)

        user = self.model(
            pessoa=pessoa,
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, pessoa, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields["is_staff"] is not True:
            raise ValueError("Um superusuário deve possuir is_staff=True.")

        if extra_fields["is_superuser"] is not True:
            raise ValueError("Um superusuário deve possuir is_superuser=True.")

        return self.create_user(
            pessoa=pessoa,
            email=email,
            password=password,
            **extra_fields,
        )


class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True, editable=False, db_column="id")

    pessoa = models.OneToOneField(
        Pessoa,
        on_delete=models.PROTECT,
        db_column="id_pessoa",
    )

    email = models.EmailField(unique=True, db_column='email')

    is_active = models.BooleanField(blank=True, default=True, db_column='is_active')
    is_staff = models.BooleanField(blank=True, default=False, db_column='is_staff')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        managed = False
        db_table = "usuarios"

        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    objects = UserManager()

    USERNAME_FIELD = "pessoa"
    EMAIL_FIELD = "email"

    REQUIRED_FIELDS = ["email"]

    @property
    def cpf(self):
        return self.pessoa.cpf

    @property
    def full_name(self):
        return self.pessoa.nome_pessoa

    def __str__(self):
        return f"{self.full_name} ({self.cpf})"
