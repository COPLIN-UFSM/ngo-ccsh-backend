from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Usuario

class UserListSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "username", "email", "full_name", "is_superuser", "is_active", "password", "password2"]

        read_only_fields = ["is_active"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({
                "password": "As senhas não são iguais.",
                "password2": "As senhas não são iguais.",
            })
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = Usuario.objects.create_user(**validated_data)
        return user


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "username", "email", "full_name", "is_superuser", "is_active"]


class ChangePasswordSerializer(serializers.Serializer):
    password1 = serializers.CharField(
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
        new_password = attrs['password1']
        new_password_confirm = attrs['password2']

        if new_password != new_password_confirm:
            raise ValidationError({"detail": 'As senhas não são iguais!'})

        return attrs