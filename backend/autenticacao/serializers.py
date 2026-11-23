from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):
    """Campos aceitos pelo endpoint de login."""

    cpf = serializers.CharField(
        help_text="CPF cadastrado para o usuário.",
        trim_whitespace=False,
    )
    senha = serializers.CharField(
        help_text="Senha do usuário.",
        trim_whitespace=False,
        write_only=True,
    )


class LoginResponseSerializer(serializers.Serializer):
    """Tokens retornados após uma autenticação bem-sucedida."""

    refresh = serializers.CharField()
    token = serializers.CharField(help_text="Token JWT de acesso.")


class EmailRequestSerializer(serializers.Serializer):
    """Endereço de email usado para iniciar a recuperação de senha."""

    email = serializers.CharField(
        help_text="Email cadastrado para o usuário.",
        trim_whitespace=False,
    )


class DetailResponseSerializer(serializers.Serializer):
    """Mensagem textual retornada pelas respostas de autenticação."""

    detail = serializers.CharField()
