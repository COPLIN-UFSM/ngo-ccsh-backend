from django.urls import path

from entidades.views.cargos import CargoListView
from entidades.views.centros import CentroDetailsView, CentroListView
from entidades.views.cursos import CursoDetailsView, CursoListView
from entidades.views.discentes import DiscenteListView, DiscenteDetailsView
from entidades.views.pessoas import PessoaListView, PessoaDetailsView
from entidades.views.servidores import ServidorListView, ServidorDetailsView
from entidades.views.unidades import TipoUnidadeListView, UnidadeDetailsView, SituacaoUnidadeListView, UnidadeListView

app_name = "entidades"

urlpatterns = [
    path("centros/", CentroListView.as_view(), name="centros"),
    path("centros/<int:id>/", CentroDetailsView.as_view(), name="centros_detalhes"),
    path("unidades", UnidadeListView.as_view(), name="unidades"),
    path("unidades/<int:id>/", UnidadeDetailsView.as_view(), name="unidades_detalhes"),
    path("unidades/situacoes/", SituacaoUnidadeListView.as_view(), name="situacoes_unidades"),
    path("unidades/tipos/", TipoUnidadeListView.as_view(), name="tipos_unidades"),
    path("cursos/", CursoListView.as_view(), name="cursos"),
    path("cursos/<int:id>/", CursoDetailsView.as_view(), name="cursos_detalhes"),
    path("cargos/", CargoListView.as_view(), name="cargos"),
    path("pessoas/", PessoaListView.as_view(), name="pessoas"),
    path("pessoas/<int:id>/", PessoaDetailsView.as_view(), name="pessoas_detalhes"),
    path("pessoas/discentes/", DiscenteListView.as_view(), name="discentes"),
    path("pessoas/discentes/<int:id>/", DiscenteDetailsView.as_view(), name="discentes_detalhes"),
    path("pessoas/servidores/", ServidorListView.as_view(), name="servidores"),
    path("pessoas/servidores/<int:id>/", ServidorDetailsView.as_view(), name="servidores_detalhes"),
]