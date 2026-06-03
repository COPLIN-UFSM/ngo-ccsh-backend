from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from despesas.models import Transacao
from despesas.serializers import TransacaoSerializer


#Continuar daqui.
class TransacoesViewSet(viewsets.ModelViewSet):
    queryset = Transacao.objects.all()
    serializer_class = TransacaoSerializer

    def get_permissions(self):
        return [IsAuthenticated()]
    
    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save()
