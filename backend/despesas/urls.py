from django.urls import path, include
from rest_framework.routers import DefaultRouter

from despesas.views import finalidades
from despesas.views.finalidades import *

from despesas.views.empenhos import EmpenhoListView, EmpenhoDetailsView
from despesas.views.documentos import TipoDocumentoViewSet
from despesas.views.transacoes import TransacoesViewSet, StatusTransacaoViewSet

app_name = "despesas"

router = DefaultRouter()
# TODO o valor de um documento é atrelado a uma transação. a informação não deve ser vista
# individualmente
# router.register("documentos/", DocumentoViewSet, basename="documentos")
#router.register("documentos/tipos/", TipoDocumentoViewSet, basename="tipos_documentos")
#router.register("transacoes/", TransacoesViewSet, basename="transacoes")
#router.register("transacoes/status/", StatusTransacaoViewSet, basename="status_transacoes")

router.register("finalidades/naturezas", NaturezaFinalidadeViewSet, basename="naturezas_finalidades")
router.register("finalidades/grupos", GrupoFinalidadeViewSet, basename="grupos_finalidades")
router.register("finalidades", FinalidadeViewSet, basename="finalidades")

urlpatterns = [
    path('', include(router.urls)),
    #path("empenhos/", EmpenhoListView.as_view(), name="empenhos"),
    #path("empenhos/<int:pk>/", EmpenhoDetailsView.as_view(), name="empenhos_detalhes"),
]