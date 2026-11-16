from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from despesas.views.bolsas import (
    ListaSIAFIViewSet,
    ParcelaBolsaViewSet,
    VinculoBolsaViewSet,
)
from despesas.views.documentos import (
    LancamentoViewSet,
    TipoDadoDocumentoViewSet,
    TipoDocumentoViewSet,
    ValorDocumentoViewSet,
)
from despesas.views.empenhos import EmpenhoViewSet
from despesas.views.exercicios import ExercicioCentroViewSet
from despesas.views.finalidades import (
    FinalidadeViewSet,
    GrupoFinalidadeViewSet,
    NaturezaViewSet,
)
from despesas.views.transacoes import (
    TipoMovimentoViewSet,
    TransacaoOperationViewSet,
    TransacoesViewSet,
)

app_name = "despesas"

router = DefaultRouter()

router.register("finalidades/naturezas", NaturezaViewSet, basename="naturezas")  # OK
router.register(
    "finalidades/grupos", GrupoFinalidadeViewSet, basename="grupos_finalidades"
)  # OK
router.register("finalidades", FinalidadeViewSet, basename="finalidades")  # OK
router.register(
    "tipos-documentos", TipoDocumentoViewSet, basename="tipos_documentos"
)  # OK

router.register(
    "transacoes/tipos-movimento", TipoMovimentoViewSet, basename="tipos_movimento"
)  # OK

router.register("transacoes", TransacoesViewSet, basename="transacoes")
router.register("empenhos", EmpenhoViewSet, basename="empenhos")
router.register("vinculos-bolsa", VinculoBolsaViewSet, basename="vinculos-bolsa")  # OK
router.register("parcelas-bolsa", ParcelaBolsaViewSet, basename="parcelas-bolsa")  # OK
router.register("listas-siafi", ListaSIAFIViewSet, basename="listas-siafi")
router.register("exercicios", ExercicioCentroViewSet, basename="exercicios")

transacao_router = routers.NestedSimpleRouter(router, r"transacoes", lookup="transacao")
transacao_router.register(
    r"documentos", ValorDocumentoViewSet, basename="transacao-documentos"
)
transacao_router.register(
    r"lancamentos", LancamentoViewSet, basename="transacao-lancamentos"
)
urlpatterns = [
    path(
        "tipos-documentos/tipos-dados/",
        TipoDadoDocumentoViewSet.as_view(),
        name="tipos_dados",
    ),  # OK
    path(
        "transacoes/operacoes/",
        TransacaoOperationViewSet.as_view(),
        name="tipos_dado",
    ),  # OK
    path("", include(router.urls)),
    path("", include(transacao_router.urls)),
]
