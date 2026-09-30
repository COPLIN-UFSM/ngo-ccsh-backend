from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from usuarios.models import Usuario


class MyUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = Usuario
        fields = ("cpf", "email")


@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    add_form = MyUserCreationForm
    model = Usuario

    list_display = ["cpf", "email", "nome_pessoa"]

    add_fieldsets = (
        (
            "Autenticação",
            {
                "classes":["wide",],
                "fields": (
                    "cpf",
                    "email",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    ordering = ("cpf",)

    search_fields = (
        "cpf",
        "email",
    )

    list_filter = (
        "ativo",
        "is_superuser",
    )

    fieldsets = (
        ("Auth", {"fields": ("cpf", "password")}),
        ("Infos", {"fields": ["email"]}),
        ("Permissions", {
            "fields": (
                "ativo",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Metadata", {"fields": ("data_criacao",)})
    )

    readonly_fields = ("data_criacao",)
