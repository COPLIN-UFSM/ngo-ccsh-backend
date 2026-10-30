from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from despesas.views.documentos import TipoDocumentoViewSet, ValorDocumentoViewSet
from despesas.views.documentos import LancamentoViewSet
from despesas.views.empenhos import EmpenhoViewSet
from despesas.views.finalidades import (
    FinalidadeViewSet,
    GrupoFinalidadeViewSet,
    NaturezaViewSet,
)
from despesas.views.transacoes import (
    TipoMovimentoViewSet,
    TransacoesViewSet,
)

app_name = "despesas"

router = DefaultRouter()

router.register(
    "finalidades/naturezas", NaturezaViewSet, basename="naturezas"
)
router.register(
    "finalidades/grupos", GrupoFinalidadeViewSet, basename="grupos_finalidades"
)
router.register("finalidades", FinalidadeViewSet, basename="finalidades")
router.register("documentos/tipos", TipoDocumentoViewSet, basename="tipos_documentos")
router.register("transacoes/tipos-movimento", TipoMovimentoViewSet, basename="tipos_movimento")
router.register("transacoes", TransacoesViewSet, basename="transacoes")
router.register("empenhos", EmpenhoViewSet, basename="empenhos")

transacao_router = routers.NestedSimpleRouter(router, r"transacoes", lookup="transacao")
transacao_router.register(
    r"documentos", ValorDocumentoViewSet, basename="transacao-documentos"
)
transacao_router.register(
    r"lancamentos", LancamentoViewSet, basename="transacao-lancamentos"
)
urlpatterns = [path("", include(router.urls)), path("", include(transacao_router.urls))]
