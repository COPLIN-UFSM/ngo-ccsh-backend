from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

from entidades.models import Pessoa, Servidor


class UserManager(BaseUserManager):
    def update_user(self, instance, **validated_data):
        pessoa = instance.pessoa
        if 'cpf' in validated_data:
            try:
                pessoa = Pessoa.objects.get(cpf=validated_data['cpf'])
            except Pessoa.DoesNotExist:
                raise ValueError("Não existe uma pessoa com este CPF no banco de dados institucional.")
        if 'email' in validated_data:
            email = self.normalize_email(validated_data['email'])

        if pessoa != instance.pessoa:
            if Usuario.objects.filter(pessoa=pessoa).exists():
                raise ValueError(
                    "Já existe um usuário com esse CPF cadastrado."
                )

            servidor = Servidor.objects.filter(
                pessoa=pessoa,
                ativo=True,
            ).exists()

            if not servidor:  # -> Leandro não é servidor.
                raise ValueError('Somente servidores ativos podem ser usuários.')

        validated_data.pop('email')
        instance = self.model(**validated_data, email=email)

        instance.save()
        return instance

    def create_user(self, cpf, email, password=None, **extra_fields):
        if not cpf:
            raise ValueError("O usuário deve estar associado a uma CPF.")

        cpf = "".join(filter(str.isdigit, cpf))

        if not email:
            raise ValueError("O usuário deve possuir um e-mail.")

        try:
            pessoa = Pessoa.objects.get(cpf=cpf)
        except Pessoa.DoesNotExist:
            raise ValueError("Não existe uma pessoa com este CPF no banco de dados institucional.")

        if Usuario.objects.filter(pessoa=pessoa).exists():
            raise ValueError(
                "Já existe um usuário com esse CPF cadastrado."
            )

        servidor = Servidor.objects.filter(
            pessoa=pessoa,
            ativo=True,
        ).exists()

        if not servidor: # -> Leandro não é servidor.
           raise ValueError('Somente servidores ativos podem ser usuários.')

        email = self.normalize_email(email)

        user = self.model(
            cpf=cpf,
            pessoa=pessoa,
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, cpf, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields["is_superuser"]:
            raise ValueError("Um superusuário deve possuir is_superuser=True.")

        return self.create_user(
            cpf=cpf,
            email=email,
            password=password,
            **extra_fields,
        )


class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True, editable=False, db_column="id")
    cpf = models.CharField(max_length=11, unique=True, null=False, blank=False, db_column="cpf")
    email = models.EmailField(unique=True, max_length=64, db_column='email')
    is_active = models.BooleanField(blank=True, default=True, db_column='is_active')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    pessoa = models.OneToOneField(
        Pessoa,
        on_delete=models.PROTECT,
        db_column="id_pessoa",
    )

    class Meta:
        managed = False
        db_table = "usuarios"

        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    objects = UserManager()

    USERNAME_FIELD = "cpf"
    EMAIL_FIELD = "email"

    REQUIRED_FIELDS = ["email"]

    @property
    def full_name(self):
        return self.pessoa.nome_pessoa

    def __str__(self):
        return f"{self.full_name} ({self.cpf})"
