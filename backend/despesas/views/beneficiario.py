from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from despesas.models import Beneficiario
from despesas.serializers import BeneficiarioSerializer


class BeneficiarioViewSet(viewsets.ModelViewSet):
    queryset = Beneficiario.objects.all()
    serializer_class = BeneficiarioSerializer

    def get_queryset(self):
        return Beneficiario.objects.filter(ativo=True)
    
    def get_permissions(self):
        return [IsAuthenticated()]
    
    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save()
