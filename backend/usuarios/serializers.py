from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from django.contrib.auth.password_validation import validate_password
from .models import Usuario

class UserListSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "cpf", "email", "full_name", "is_superuser", "is_active", "password", "password2"]

        read_only_fields = ["is_active"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({
                "password": "As senhas não são iguais.",
                "password2": "As senhas não são iguais.",
            })

        try:
            validate_password(data['password1'])
        except DjangoValidationError as passwordWeek:
            raise serializers.ValidationError({
                "password": passwordWeek.messages
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
    class Meta:
        model = Usuario
        fields = ["id", "cpf", "email", "full_name", "is_superuser", "is_active"]

    def update(self, instance, validated_data):
        try:
            user = Usuario.objects.update_user(**validated_data,instance=instance)
        except ValueError as e:
            raise serializers.ValidationError({
                "detail": str(e)
            })
        return user


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        required=True,
        error_messages={
            "required": "Por favor informe a nova senha.",
            "blank": "A nova senha não pode estar vazia.",
        }
    )
    password2 = serializers.CharField(
        required=True,
        error_messages={
            "required": "Por favor informe a nova senha.",
            "blank": "A nova senha não pode estar vazia.",
        }
    )

    def validate(self, attrs):
        new_password = attrs['password']
        new_password_confirm = attrs['password2']

        if new_password != new_password_confirm:
            raise serializers.ValidationError({"password": 'As senhas não são iguais!'})

        try:
            validate_password(attrs['password'])
        except DjangoValidationError as passwordWeek:
            raise serializers.ValidationError({"password": passwordWeek.messages})

        return attrs