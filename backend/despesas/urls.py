from django.urls import path, include
from rest_framework.routers import DefaultRouter

from despesas.views.finalidades import (
    FinalidadesView,
    SingleFinalidadeView,
    TipoFinalidadeView,
    SingleTipoFinalidadeView,
    NaturezaFinalidadeView,
    SingleNaturezaFinalidadeView,
)

from despesas.views.subunidades import SubunidadeView, SingleSubunidadeView
from despesas.views.empenhos import EmpenhoView, SingleEmpenhoView, TransacoesByEmpenho
from despesas.views.beneficiario import BeneficiarioViewSet
from despesas.views.documentos import DocumentoViewSet, TipoDocumentoViewSet
from despesas.views.transacoes import TransacoesViewSet

app_name = "despesas"

router = DefaultRouter()
router.register(r"beneficiarios", BeneficiarioViewSet, basename="beneficiario")
router.register(r"documentos", DocumentoViewSet, basename="documentos")
router.register(r"tipos-documentos", TipoDocumentoViewSet, basename="tipos_documentos")
router.register(r"transacoes", TransacoesViewSet, basename="transacoes")

urlpatterns = [
    path("", include(router.urls)),
    path("finalidades/", view=FinalidadesView.as_view(), name="finalidades"),
    path("finalidades/<int:pk>/", view=SingleFinalidadeView.as_view(), name="single_finalidades"),
    path("tipos-finalidade/", view=TipoFinalidadeView.as_view(), name="subtipo_finalidade"),
    path("tipos-finalidade/<int:pk>/", view=SingleTipoFinalidadeView.as_view(), name="single_subtipo_finalidade"),
    path("naturezas-finalidade/", view=NaturezaFinalidadeView.as_view(), name="tipos_despesas"),
    path("naturezas-finalidade/<int:pk>/", view=SingleNaturezaFinalidadeView.as_view(), name="single_natureza_finalidade"),
    path("subunidades/", view=SubunidadeView.as_view(), name="subunidades"),
    path("subunidades/<int:pk>/", view=SingleSubunidadeView.as_view(), name="single_subunidade"),
    path("empenhos/", EmpenhoView.as_view(), name="empenhos"),
    path("empenhos/<int:pk>/", SingleEmpenhoView.as_view(), name="single_empenho"),
]
