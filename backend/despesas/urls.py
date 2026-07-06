from django.urls import path, include
from rest_framework.routers import DefaultRouter

from despesas.views.finalidades import *

from despesas.views.empenhos import EmpenhoListView, EmpenhoDetailsView
from despesas.views.documentos import DocumentoViewSet, TipoDocumentoViewSet
from despesas.views.transacoes import TransacoesViewSet

app_name = "despesas"

router = DefaultRouter()
router.register("documentos/", DocumentoViewSet, basename="documentos")
router.register("documentos/tipos/", TipoDocumentoViewSet, basename="tipos_documentos")
router.register("transacoes/", TransacoesViewSet, basename="transacoes")

urlpatterns = [
    path("", include(router.urls)),
    path("finalidades/naturezas", view=NaturezaFinalidadeListView.as_view(), name="naturezas_finalidades"),
    # acho que não precisa
    # path("finalidades/naturezas/<int:pk>/", view=NaturezaFinalidadeDetailsView.as_view(), name="naturezas_finalidades_detalhes"),
    path("finalidades/grupos/", view=GrupoFinalidadeListView.as_view(), name="grupos_finalidades"),
    # acho que não precisa
    # path("finalidades/grupos/<int:pk>/", view=SingleTipoFinalidadeView.as_view(), name="grupos_finalidades_detalhes"),
    path("finalidades/", view=FinalidadesListView.as_view(), name="finalidades"),
    path("finalidades/<int:pk>/", view=FinalidadeDetailsView.as_view(), name="finalidades_detalhes"),
    path("empenhos/", EmpenhoListView.as_view(), name="empenhos"),
    path("empenhos/<int:pk>/", EmpenhoDetailsView.as_view(), name="empenhos_detalhes"),
]
