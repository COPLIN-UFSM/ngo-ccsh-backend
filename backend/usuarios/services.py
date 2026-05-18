from .models import Usuario
from rest_framework_simplejwt.tokens import AccessToken
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os
from rest_framework_simplejwt.exceptions import TokenError


def _find_user_by_Id(id):
    """Return user or None"""
    try:
        user = Usuario.objects.get(pk=id)
    except Usuario.DoesNotExist:
        return None
    return user


def trigger_password_reset_flow(user):
    token = create_token_with_allow_password_change(user=user)
    send_email_reset_password(user=user, token=token)


def create_token_with_allow_password_change(user):
    token = AccessToken.for_user(user=user)
    token["allow_password_change"] = True
    return token


def is_token_valid(token):
    try:
        AccessToken(str(token))
        return True
    except TokenError as e:
        return False


def send_email_reset_password(user, token):
    link = f"http://localhost:5173/mudar-senha/?token={token}"

    context = {
        "username": user.username,
        "full_name": user.full_name,
        "link": link,
    }
    html_content = render_to_string("email/my_email.html", context)
    text_content = strip_tags(html_content)
    text_content += f"\n\nLink para recuperação: {link}"

    msg = EmailMultiAlternatives(
        subject="Portal Transparência CCSH - Recuperação de Senha.",
        body=text_content,
        from_email=os.getenv("EMAIL_USER"),
        to=[user.email],
        headers={"List-Unsubscribe": "<mailto:suporte@cssh.com>"},
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
