from django.urls import path
from despesas.views.finalidades import (
    FinalidadesView,
    SingleFinalidadeView,
    CategoriaFinalidadeView,
    SingleCategoriaFinalidadeView,
    TipoDespesaView,
    SingleTipoDespesaView,
)
from despesas.views.subunidades import (
    SubunidadeView,
    SingleSubunidadeView,
)
from despesas.views.beneficiario import BeneficiarioViewSet
from despesas.views.documentos import *
from rest_framework.routers import DefaultRouter
from django.urls import path, include

app_name = "despesas"

router = DefaultRouter()
router.register(r"beneficiarios", BeneficiarioViewSet, basename="beneficiario")
router.register(r"documentos", DocumentoViewSet, basename="documentos")
router.register(r"tipos-documentos", TipoDocumentoViewSet, basename="tipos_documentos")

urlpatterns = [
    path("", include(router.urls)),
    path("finalidades/", view=FinalidadesView.as_view(), name="finalidades"),
    path(
        "finalidades/<int:pk>/",
        view=SingleFinalidadeView.as_view(),
        name="single_finalidades",
    ),
    path(
        "categorias-finalidade/",
        view=CategoriaFinalidadeView.as_view(),
        name="subtipo_finalidade",
    ),
    path(
        "categorias-finalidade/<int:pk>/",
        view=SingleCategoriaFinalidadeView.as_view(),
        name="subtipo_finalidade",
    ),
    path("tipos-despesa/", view=TipoDespesaView.as_view(), name="tipos_despesas"),
    path(
        "tipos-despesa/<int:pk>/",
        view=SingleTipoDespesaView.as_view(),
        name="single_tipo_despesa",
    ),
    path("subunidades/", view=SubunidadeView.as_view(), name="subunidades"),
    path(
        "subunidades/<int:pk>/",
        view=SingleSubunidadeView.as_view(),
        name="single_subunidade",
    ),
]
