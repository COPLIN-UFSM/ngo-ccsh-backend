from django.urls import path

from entidades.models import SituacaoUnidade

app_name = "entidades"

urlpatterns = [
    path("centros/", CentroListView.as_view(), name="centros"),
    path("centros/<int:id>/", CentroDetailsView.as_view(), name="centros_detalhes"),
    path("unidades", UnidadeListView.as_view(), name="unidades"),
    path("unidades/<int:id>/", UnidadeDetailsView.as_view(), name="unidades_detalhes"),
    path("unidades/situacoes/", SituacaoUnidadeListView.as_view(), name="situacoes_unidades"),
    path("unidades/tipos/", TipoUnidadeListView.as_view(), name="tipos_unidades"),
    path("cursos/", CursosListView.as_view(), name="cursos"),
    path("cursos/<int:id>/", CursoDetailsView.as_view(), name="cursos_detalhes"),
    path("cargos/", CargoDetailsView.as_view(), name="cargos_detalhes"),
    path("pessoas/", PessoasListView.as_view(), name="pessoas"),
    path("pessoas/<int:id>/", PessoaDetailsView.as_view(), name="pessoas_detalhes"),
    path("pessoas/discentes/", DiscentesListView.as_view(), name="discentes"),
    path("pessoas/discentes/<int:id>/", DiscenteDetailsView.as_view(), name="discentes_detalhes"),
    path("pessoas/servidores/", ServidoresListView.as_view(), name="servidores"),
    path("pessoas/servidores/<int:id>/", ServidorDetailsView.as_view(), name="servidores_detalhes"),
]