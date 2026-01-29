from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm", "is_student"]

        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("As senhas não são iguais.")
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "is_student"]


# class Register2Serializer(serializers.Serializer):
#     id  = serializers.IntegerField(read_only=True)
#     id  = serializers.IntegerField(read_only=True)
#     id  = serializers.IntegerField(read_only=True)


# class RegisterSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User
#         fields = ["id","username", "email"]