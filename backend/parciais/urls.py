from django.urls import path
from parciais.views import *

app_name = "parciais"

urlpatterns = [
    path("empenhos/", EmpenhoView.as_view(), name="empenhos"),
    path("empenhos/<int:pk>/", SingleEmpenhoView.as_view(), name="single_empenho"),
    path("empenhos/transacoes-empenho/<int:pk>/", TransacoesByEmpenho.as_view(), name="transacoes_by_empenho"),
]
