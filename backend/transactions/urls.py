from django.urls import path
from .views import (
    CategoriaFinalidadeView,
    FinalidadesView,
    SingleCategoriaFinalidadeView,
    SingleFinalidadeView,
    SingleSubunidadeView,
    SubunidadeView,
    TipoDespesaView,
)

app_name = "transactions"

urlpatterns = [
    path("finalidades/", view=FinalidadesView.as_view(), name="finalidades"),
    path(
        "finalidades/<int:pk>/",
        view=SingleFinalidadeView.as_view(),
        name="single_finalidades",
    ),
    path(
        "categoria-finalidade/",
        view=CategoriaFinalidadeView.as_view(),
        name="subtipo_finalidade",
    ),
    # Testar
    path(
        "categoria-finalidade/<int:pk>",
        view=SingleCategoriaFinalidadeView.as_view(),
        name="subtipo_finalidade",
    ),
    path("tipo-despesas/", view=TipoDespesaView.as_view(), name="despesas"),
    path("subunidades/", view=SubunidadeView.as_view(), name="subunidades"),
    path(
        "subunidades/<int:pk>/",
        view=SingleSubunidadeView.as_view(),
        name="single_subunidade",
    ),
]
