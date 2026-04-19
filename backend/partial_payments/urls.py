from django.urls import path
from partial_payments.views import *

app_name = "partial_payments"

urlpatterns = [
    path("empenhos/", EmpenhoView.as_view(), name="empenhos"),
    path(
        "empenhos/montante-total/<int:pk>/",
        EmpenhoMontante.as_view(),
        name="total_empenho",
    ),
    path(
        "empenhos/transacoes-empenho/<int:pk>/",
        TransacoesByEmpenho.as_view(),
        name="transacoes_by_empenho",
    ),
    
    path("empenhos/<int:pk>/", SingleEmpenhoView.as_view(), name="single_empenho"),
    path(
        "tipos-documento/",
        TipoDocumentoPagamentoParcialView.as_view(),
        name="tipos_documento",
    ),
    path(
        "tipos-documento/<int:pk>/",
        SingleTipoDocumentoPagamentoParcialView.as_view(),
        name="single_tipo_documento",
    ),
    path("transacoes/", TransacaoPagamentoParcialView.as_view(), name="transacoes"),
    path(
        "transacoes/<int:pk>/",
        SingleTransacaoPagamentoParcialView.as_view(),
        name="single_transacao",
    ),
]
