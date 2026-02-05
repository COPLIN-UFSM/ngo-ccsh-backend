from calendar import c
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "password",
            "password_confirm",
        ]

        read_only_fields = ["is_active"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "As senhas não são iguais."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = CustomUser.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:

        model = CustomUser
        fields = ["id", "username", "email", "full_name"]

