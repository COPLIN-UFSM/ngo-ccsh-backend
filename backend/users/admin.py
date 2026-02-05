from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class MyUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=255, required=False)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "full_name")


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = MyUserCreationForm
    model = CustomUser

    list_display = ["username", "email", "full_name"]

    add_fieldsets = (
        (
            "Autenticação",
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "full_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    fieldsets = (
        ("Auth", {"fields": ("username", "password")}),
        ("Infos", {"fields": ("full_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
