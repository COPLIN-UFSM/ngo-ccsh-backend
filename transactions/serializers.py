from rest_framework import serializers
from .models import Transacoes
class transacoesSerializer(serializers.ModelSerializer):
	# tipo_transacao = Transacoes.objects.aggregate()


    class meta:
        fields = ['id_transacao',]
