from django.db import models

from entidades.managers import PessoaManager, CentroManager, UnidadeManager

class CentroSIE(models.Model):
    id_centro_sie = models.AutoField(primary_key=True, db_column="id_centro_sie")
    cod_estruturado = models.CharField(max_length=15, unique=True, db_column='cod_estruturado')
    sigla_centro = models.CharField(max_length=16, unique=True, db_column='sigla_centro')
    nome_centro = models.CharField(max_length=256, db_column='nome_centro')

    class Meta:
        managed = False
        db_table = "v_centros_sie"

    def __str__(self) -> str:
        return self.nome_centro


class Centro(models.Model):
    objects = CentroManager()

    id_centro_interno = models.AutoField(primary_key=True, db_column='id_centro_interno')
    # Pode ser null pelo fato de que existem tabelas que não estão cadastradas no sie
    centro_sie = models.OneToOneField(CentroSIE, null=True, blank=True, on_delete=models.DO_NOTHING, db_column='id_centro_sie')
    nome_centro = models.CharField(max_length=256, db_column='nome_centro')
    sigla_centro = models.CharField(max_length=16, unique=True, db_column='sigla_centro')
    cod_estruturado = models.CharField(max_length=15, unique=True, db_column='cod_estruturado')

    class Meta:
        managed = False
        db_table = "centros"

    def __str__(self) -> str:
        return self.nome_centro

class SituacaoUnidade(models.Model):
    id_situacao_unidade = models.AutoField(primary_key=True, db_column='id_situacao_unidade')
    situacao_unidade = models.CharField(max_length=16, db_column='situacao_unidade')

    class Meta:
        managed = False
        db_table = "v_situacoes_unidades"
        
    def __str__(self):
        return self.situacao_unidade

class TipoUnidade(models.Model):
    id_tipo_unidade = models.AutoField(primary_key=True, db_column='id_tipo_unidade')
    tipo_unidade = models.CharField(max_length=128, db_column='tipo_unidade')

    class Meta:
        managed = False
        db_table = "v_tipos_unidades"

    def __str__(self):
        return self.tipo_unidade



class UnidadeSIE(models.Model):
    id_unidade_sie = models.AutoField(primary_key=True, db_column='id_unidade_sie')
    nome_unidade = models.CharField(max_length=256, unique=False, db_column='nome_unidade')
    cod_estruturado = models.CharField(max_length=15, unique=True, db_column='cod_estruturado')

    centro = models.ForeignKey(Centro, models.DO_NOTHING, db_column="id_centro_sie", db_constraint=False)
    tipo_unidade = models.ForeignKey(TipoUnidade, models.DO_NOTHING, db_column="id_tipo_unidade")
    situacao_unidade = models.ForeignKey(SituacaoUnidade, models.DO_NOTHING, db_column="id_situacao_unidade")

    class Meta:
        managed = False
        db_table = "v_unidades_sie"


class Unidade(models.Model):
    objects = UnidadeManager()

    id_unidade_interna = models.AutoField(primary_key=True, db_column='id_unidade_interna')
    unidade_sie = models.OneToOneField(UnidadeSIE, null=True, blank=False, on_delete=models.DO_NOTHING, db_column="id_unidade_sie")

    nome_unidade = models.CharField(max_length=256, blank=False, null=False, db_column='nome_unidade')
    cod_estruturado = models.CharField(max_length=15, unique=True, blank=True, null=True, db_column='cod_estruturado')

    centro = models.ForeignKey(Centro, models.DO_NOTHING, blank=False, null=False,  db_column="id_centro_interno")
    tipo_unidade = models.ForeignKey(TipoUnidade, models.DO_NOTHING, blank=False, null=False, db_column="id_tipo_unidade")
    situacao_unidade = models.ForeignKey(SituacaoUnidade, models.DO_NOTHING, blank=False, null=False, db_column="id_situacao_unidade")

    class Meta:
        managed = False
        db_table = "unidades"

    def __str__(self) -> str:
        return self.nome_unidade


class Curso(models.Model):
    id_curso = models.AutoField(primary_key=True, db_column="id_curso")
    centro = models.ForeignKey(Centro, on_delete=models.DO_NOTHING, db_column="id_centro_interno", db_constraint=False)
    nome_curso = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nome_curso")
    nivel_curso = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nivel_curso")
    modalidade_curso = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="modalidade_curso")
    classificacao_curso = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="classificacao_curso")

    class Meta:
        managed = False
        db_table = "v_cursos"


class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True, db_column="id_cargo")
    cargo = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="cargo")

    class Meta:
        managed = False
        db_table = "v_cargos"

    def __str__(self):
        return self.cargo
class PessoaSIE(models.Model):
    id_pessoa_sie = models.AutoField(primary_key=True, db_column="id_pessoa_sie")
    nome_pessoa = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nome_pessoa")
    cpf = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="cpf")
    rg = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="rg")

    class Meta:
        managed = False
        db_table = "v_pessoas_sie"


class Pessoa(models.Model):
    objects = PessoaManager()

    id_pessoa_interna = models.AutoField(primary_key=True, db_column="id_pessoa_interna")
    pessoa_sie = models.OneToOneField(PessoaSIE, on_delete=models.DO_NOTHING, null=True, blank=True, db_column="id_pessoa_sie")
    nome_pessoa = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nome_pessoa")
    cpf = models.TextField(max_length=11, unique=True, null=False, blank=False, db_column="cpf")
    rg = models.TextField(max_length=11, unique=True, null=False, blank=False, db_column="rg")

    class Meta:
        managed = False
        db_table = 'pessoas'


class Discente(models.Model):
    id_curso_aluno = models.AutoField(primary_key=True, db_column="id_curso_aluno")
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.DO_NOTHING,
        db_column="id_pessoa_interna",
    )
    matricula = models.TextField(max_length=32, unique=True, null=False, blank=False, db_column="matricula")
    curso = models.ForeignKey(Curso, on_delete=models.DO_NOTHING, db_column="id_curso")
    ativo = models.BooleanField(unique=False, default=True, blank=True, db_column="ativo")

    class Meta:
        managed = False
        db_table = "v_discentes"


class Servidor(models.Model):
    id_contrato_rh = models.AutoField(primary_key=True, db_column="id_contrato_rh")
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.DO_NOTHING,
        db_column="id_pessoa_interna",
        db_constraint=False
    )
    matricula = models.TextField(max_length=32, unique=True, null=False, blank=False, db_column="matricula")
    cargo = models.ForeignKey(Cargo, on_delete=models.DO_NOTHING, db_column="id_cargo")
    ativo = models.BooleanField(unique=False, default=True, blank=True, db_column="ativo")

    class Meta:
        managed = False
        db_table = "v_servidores"


class Email(models.Model):
    id_email = models.AutoField(primary_key=True, db_column="id_conta")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa_interna", related_name='emails')
    email = models.EmailField(unique=True, db_column="email")
    ativo = models.BooleanField(unique=False, default=True, blank=True, db_column="ativo")

    class Meta:
        managed = False
        db_table = "emails"


class Telefone(models.Model):
    id_telefone = models.AutoField(primary_key=True, db_column="id_telefone")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa_interna", related_name="telefones",)
    telefone = models.TextField(max_length=16, unique=False, null=False, blank=False, db_column="telefone")
    ativo = models.BooleanField(unique=False, default=True, blank=True, db_column="ativo")

    class Meta:
        managed = False
        db_table = "telefones"
