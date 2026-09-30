from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from django.contrib.auth.password_validation import validate_password
from .models import Usuario

class UserListSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(source="password", write_only=True)
    senha2 = serializers.CharField(write_only=True, source="password2")
    administrador = serializers.BooleanField(source='is_superuser', required=False, default=False)

    class Meta:
        model = Usuario
        fields = ["id", "cpf", "email", "nome_pessoa", "administrador", "ativo", "senha", "senha2"]
        read_only_fields = ["id", "ativo"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({
                "senha": "As senhas não são iguais.",
                "senha2": "As senhas não são iguais.",
            })

        try:
            validate_password(data['password'])
        except DjangoValidationError as passwordWeak:
            raise serializers.ValidationError({
                "senha": passwordWeak.messages
            })

        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        try:
            user = Usuario.objects.create_user(**validated_data)
        except ValueError as createError:
            raise serializers.ValidationError({
                "detail": str(createError)
            })
        return user


class UserDetailsSerializer(serializers.ModelSerializer):

    administrador = serializers.BooleanField(source='is_superuser', required=False, default=False)

    class Meta:
        model = Usuario
        fields = ["id", "cpf", "email", "nome_pessoa", "administrador", "ativo"]

    def update(self, instance, validated_data):
        try:
            user = Usuario.objects.update_user(**validated_data,instance=instance)
        except ValueError as e:
            raise serializers.ValidationError({
                "detail": str(e)
            })
        return user


class ChangePasswordSerializer(serializers.Serializer):
    senha = serializers.CharField(
        required=True,
        error_messages={
            "required": "Por favor informe a nova senha.",
            "blank": "A nova senha não pode estar vazia.",
        }
    )
    senha2 = serializers.CharField(
        required=True,
        error_messages={
            "required": "Por favor informe a nova senha.",
            "blank": "A nova senha não pode estar vazia.",
        }
    )

    def validate(self, attrs):
        new_password = attrs['senha']
        new_password_confirm = attrs['senha2']

        if new_password != new_password_confirm:
            raise serializers.ValidationError({"senha2": 'As senhas não são iguais!'})

        try:
            validate_password(attrs['senha'])
        except DjangoValidationError as passwordWeak:
            raise serializers.ValidationError({"senha": passwordWeak.messages})

        return attrs