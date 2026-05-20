from rest_framework import serializers

from .models import Usuario

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "password",
            "password2",
        ]

        read_only_fields = ["is_active"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError(
                {
                    "password": "As senhas não são iguais.",
                    "password2": "As senhas não são iguais.",
                }
            )
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = Usuario.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:

        model = Usuario
        fields = ["id", "username", "email", "full_name"]
