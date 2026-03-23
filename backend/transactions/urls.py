from django.urls import path
from .views import FinalidadesView, SingleFinalidadeView, SubtipoFinalidadeView, TipoDespesaView, home

app_name = "transactions"

urlpatterns = [
    path("", view=home, name="homepage"),
    path("finalidades/", view=FinalidadesView.as_view(), name="finalidades"),
    path("finalidades/<int:pk>/", view=SingleFinalidadeView.as_view(), name="single_finalidades"),
    path(
        "subtipo-finalidade/",
        view=SubtipoFinalidadeView.as_view(),
        name="subtipo_finalidade",
    ),
    path("tipo-despesas/", view=TipoDespesaView.as_view(), name="tipo_despesa"),
]
