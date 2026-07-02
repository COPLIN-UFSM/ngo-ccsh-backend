from django.db import models


class Centro(models.Model):
    id_centro = models.AutoField(primary_key=True, db_column='id_centro')
    nome_centro = models.CharField(max_length=256, db_column='nome_centro')
    sigla_centro = models.CharField(max_length=16, unique=True, db_column='sigla_centro')
    cod_estruturado = models.CharField(max_length=15, unique=True, db_column='cod_estruturado')

    class Meta:
        managed = False
        db_table = "v_centros"


class SituacaoUnidade(models.Model):
    id_situacao_unidade = models.AutoField(primary_key=True, db_column='id_situacao_unidade')
    situacao_unidade = models.CharField(max_length=16, db_column='situacao_unidade')

    class Meta:
        managed = False
        db_table = "v_situacoes_unidades"


class TipoUnidade(models.Model):
    id_tipo_unidade = models.AutoField(primary_key=True, db_column='id_tipo_unidade')
    tipo_unidade = models.CharField(max_length=128, db_column='tipo_unidade')

    class Meta:
        managed = False
        db_table = "v_tipos_unidades"


class Unidade(models.Model):
    id_unidade = models.AutoField(primary_key=True, db_column='id_unidade')
    nome_unidade = models.CharField(max_length=256, unique=False, db_column='nome_unidade')
    cod_estruturado = models.CharField(max_length=15, unique=True, db_column='cod_estruturado')

    centro = models.ForeignKey(Centro, models.DO_NOTHING, db_column="id_centro")
    tipo_unidade = models.ForeignKey(TipoUnidade, models.DO_NOTHING, db_column="id_tipo_unidade")
    situacao_unidade = models.ForeignKey(SituacaoUnidade, models.DO_NOTHING, db_column="id_situacao")

    class Meta:
        managed = False
        db_table = "v_unidades"

    def __str__(self) -> str:
        return self.nome_unidade


class UnidadeExterna(models.Model):
    """
    Uma entidade externa é uma unidade que não pertence a estrutura da UFSM.
    """
    id_unidade_externa = models.AutoField(primary_key=True, db_column='id_unidade_externa')
    nome_unidade_externa = models.CharField(max_length=256, unique=False, db_column='nome_unidade_externa')
    situacao_entidade_externa = models.ForeignKey(SituacaoUnidade, models.DO_NOTHING, db_column="id_situacao")

    class Meta:
        managed = False
        db_table = "unidades_externas"


class Curso(models.Model):
    id_curso = models.AutoField(primary_key=True, db_column="id_curso")
    centro = models.ForeignKey(Centro, on_delete=models.DO_NOTHING, db_column="centro")
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


class Pessoa(models.Model):
    id_pessoa = models.AutoField(primary_key=True, db_column="id_pessoa")
    nome_pessoa = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nome_pessoa")
    cpf = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="cpf")
    rg = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="rg")

    class Meta:
        managed = False
        db_table = "v_pessoas"


class Discente(models.Model):
    id_curso_aluno = models.AutoField(primary_key=True, db_column="id_curso_aluno")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa")
    matricula = models.TextField(max_length=32, unique=True, null=False, blank=False, db_column="matricula")
    curso = models.ForeignKey(Curso, on_delete=models.DO_NOTHING, db_column="id_curso")
    ativo = models.BooleanField(unique=False, null=False, blank=False, db_column="ativo")

    class Meta:
        managed = False
        db_table = "v_discentes"


class Servidor(models.Model):
    id_contrato_rh = models.AutoField(primary_key=True, db_column="id_contrato_rh")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa")
    matricula = models.TextField(max_length=32, unique=True, null=False, blank=False, db_column="matricula")
    cargo = models.ForeignKey(Cargo, on_delete=models.DO_NOTHING, db_column="id_cargo")
    ativo = models.BooleanField(unique=False, null=False, blank=False, db_column="ativo")

    class Meta:
        managed = False
        db_table = "v_servidores"


class PessoaExterna(models.Model):
    id_pessoa_externa = models.AutoField(primary_key=True, db_column="id_pessoa_externa")
    nome_pessoa = models.TextField(max_length=256, unique=False, null=False, blank=False, db_column="nome_pessoa")
    cpf = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="cpf")
    rg = models.TextField(max_length=11, unique=False, null=False, blank=False, db_column="rg")
    email = models.EmailField(unique=False, db_column="email")
    telefone = models.TextField(max_length=16, unique=False, null=True, blank=True, db_column="telefone")

    class Meta:
        managed = False
        db_table = "pessoas_externas"


class Email(models.Model):
    id_conta = models.AutoField(primary_key=True, db_column="id_conta")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa")
    email = models.EmailField(unique=False, db_column="email")
    ativo = models.BooleanField(unique=False, null=False, blank=False, db_column="ativo")

    class Meta:
        managed = False
        db_table = "v_emails"


class Telefone(models.Model):
    id_telefone = models.AutoField(primary_key=True, db_column="id_telefone")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa")
    telefone = models.TextField(max_length=16, unique=False, null=False, blank=False, db_column="telefone")
    ativo = models.BooleanField(unique=False, null=False, blank=False, db_column="ativo")

    class Meta:
        managed = False
        db_table = "telefones"
