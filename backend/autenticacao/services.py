from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from datetime import datetime as dt
from ngo_ccsh import settings


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
    except TokenError:
        return False


def send_email_reset_password(user, token):
    link = f"{settings.FRONTEND_URL}/trocar-senha/?token={token}"

    context = {
        "app_full_name": settings.APP_FULL_NAME,
        "app_short_name": settings.APP_SHORT_NAME,
        "matricula": user.matricula,
        "user_full_name": user.full_name,
        "link": link,
        "year": dt.now().year
    }
    html_content = render_to_string("email/recuperar_email.html", context)
    text_content = strip_tags(html_content)
    text_content += f"\n\nLink para recuperação: {link}"

    msg = EmailMultiAlternatives(
        subject=f"{settings.APP_FULL_NAME} - Recuperação de Senha",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
        headers={"List-Unsubscribe": "<mailto:suporte@cssh.com>"},
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
