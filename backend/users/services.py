from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings


def enviar_email_recuperacao(usuario, uid, token):
    # A URL que o usuário clicará no e-mail (Frontend)
    url_frontend = f"http://localhost:3000/password-reset-confirm/{uid}/{token}"

    contexto = {"nome": usuario.username, "url_reset": url_frontend}

    html_body = render_to_string("emails/solicitacao_senha.html", contexto)
    text_body = strip_tags(html_body)  # Backup para dispositivos sem HTML

    email = EmailMultiAlternatives(
        subject="Recuperação de Senha - Quadrinópolis",
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[usuario.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send()
