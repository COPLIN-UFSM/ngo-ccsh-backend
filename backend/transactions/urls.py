from django.urls import path
from .views import FinalidadesView, SubtipoFinalidadeView, home

app_name = "transactions"

urlpatterns = [
    path("", view=home, name="homepage"),
    path("finalidades/", view=FinalidadesView.as_view(), name="finalidades"),
    path(
        "subtipo-finalidade/", view=SubtipoFinalidadeView.as_view(), name="subtipo_finalidade"
    ),
]
