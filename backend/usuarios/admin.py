from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from usuarios.models import Usuario

class MyUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=256, required=False)

    class Meta:
        model = Usuario
        fields = ("matricula", "email", "full_name")


@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    add_form = MyUserCreationForm
    model = Usuario

    list_display = ["matricula", "email", "full_name"]

    add_fieldsets = (
        (
            "Autenticação",
            {
                "classes": ("wide",),
                "fields": (
                    "matricula",
                    "email",
                    "full_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    ordering = ("matricula",)

    search_fields = (
        "matricula",
        "full_name",
        "email",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )

    fieldsets = (
        ("Auth", {"fields": ("matricula", "password")}),
        ("Infos", {"fields": ("full_name", "email")}),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Metadata", {"fields": ("created_at",)})
    )

    readonly_fields = ("created_at",)
