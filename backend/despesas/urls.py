from django.urls import path, include
from rest_framework.routers import DefaultRouter

from despesas.views.finalidades import FinalidadeViewSet, NaturezaFinalidadeViewSet, GrupoFinalidadeViewSet
from despesas.views.documentos import TipoDocumentoViewSet, ValorDocumentoViewSet
from despesas.views.transacoes import TransacoesViewSet, StatusTransacaoViewSet, VersoesTransacaoViewSet
from rest_framework_nested import routers

app_name = "despesas"

router = DefaultRouter()

router.register("finalidades/naturezas", NaturezaFinalidadeViewSet, basename="naturezas_finalidades")
router.register("finalidades/grupos", GrupoFinalidadeViewSet, basename="grupos_finalidades")
router.register("finalidades", FinalidadeViewSet, basename="finalidades")
router.register("documentos/tipos", TipoDocumentoViewSet, basename="tipos_documentos")
router.register("transacoes/status", StatusTransacaoViewSet, basename="status_transacao")
router.register("transacoes", TransacoesViewSet, basename="transacoes")

transacao_router = routers.NestedSimpleRouter(router, r'transacoes', lookup='transacao')
transacao_router.register(r'documentos', ValorDocumentoViewSet, basename='transacao-documentos')
transacao_router.register(r'versoes', VersoesTransacaoViewSet, basename='transacao-versoes')

#transacoes/:id/versoes
#empenhos
urlpatterns = [
    path('', include(router.urls)),
    path('', include(transacao_router.urls))
    #path("empenhos/", EmpenhoListView.as_view(), name="empenhos"),
    #path("empenhos/<int:pk>/", EmpenhoDetailsView.as_view(), name="empenhos_detalhes"),
]
