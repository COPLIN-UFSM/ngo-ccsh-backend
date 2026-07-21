from django.urls import path, include
from rest_framework.routers import DefaultRouter

from entidades.views import (
    CentroViewSet, UnidadeViewSet, CursoViewSet,
    PessoaViewSet, DiscenteViewSet, ServidorViewSet, TipoUnidadeViewSet, SituacaoUnidadeViewSet
)

app_name = "entidades"

router = DefaultRouter()

router.register("centros", CentroViewSet, basename="centros")

router.register("unidades/situacoes", SituacaoUnidadeViewSet, basename="situacoes_unidades")
router.register("unidades/tipos", TipoUnidadeViewSet, basename="tipos_unidades")
router.register("unidades", UnidadeViewSet, basename="unidades")

router.register("cursos", CursoViewSet, basename="cursos") # OK
#router.register("pessoas/telefones", TelefoneViewSet, basename="telefones")
#router.register("pessoas/emails", EmailViewSet, basename="emails")
router.register("pessoas/discentes", DiscenteViewSet, basename="discentes")
router.register("pessoas/servidores", ServidorViewSet, basename="servidores")
router.register("pessoas", PessoaViewSet, basename="pessoas")


urlpatterns = [
    path("", include(router.urls)),
]