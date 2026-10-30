"""
Entidades: centros, unidades, pessoas e vínculos.

Convenção deste módulo
----------------------
* Modelos com prefixo/tabela ``v_*`` (``CentroSIE``, ``UnidadeSIE``, ``PessoaSIE``,
  ``Curso``, ``Cargo``, ``Discente``, ``Servidor``, ...) são *views* do SIE:
  continuam ``managed = False`` e são somente leitura.
* Os modelos internos (``Centro``, ``Unidade``, ``Pessoa``, ``Email``, ``Telefone``)
  também são ``managed = False``: o schema é criado por DDL Db2 versionado, nunca
  por migrations do Django.

O que mudou em relação à versão anterior
----------------------------------------
* ``Unidade`` ganhou ``unidade_pai`` (hierarquia real, via FK) e perdeu
  ``pode_empenhar`` (quem empenha é sempre o ``Centro``).
* ``Unidade.__montante_calc__`` / ``montante_custeio`` / ``montante_capital`` saíram:
  os saldos agora são calculados a partir do razão, em ``despesas.saldos``.
* Não há mais import de ``despesas`` aqui (evita dependência circular).
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from entidades.managers import CentroManager, PessoaManager, UnidadeManager


class CentroSIE(models.Model):
    id_centro_sie = models.AutoField(primary_key=True, db_column="id_centro_sie")
    cod_estruturado = models.CharField(
        max_length=15, unique=True, db_column="cod_estruturado"
    )
    sigla_centro = models.CharField(
        max_length=16, unique=True, db_column="sigla_centro"
    )
    nome_centro = models.CharField(max_length=256, db_column="nome_centro")

    class Meta:
        managed = False
        db_table = "v_centros_sie"

    def __str__(self) -> str:
        return self.nome_centro


class Centro(models.Model):
    """
    Um centro (CCSH, CT, CCS...) recebe os recursos da PROPLAN e os mantém sob sua
    tutela. É o centro quem empenha e quem paga de fato.
    """

    objects = CentroManager()

    id_centro_interno = models.AutoField(
        primary_key=True, db_column="id_centro_interno"
    )
    # Pode ser null pelo fato de que existem centros que não estão cadastrados no SIE
    centro_sie = models.OneToOneField(
        CentroSIE,
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        db_column="id_centro_sie",
    )
    nome_centro = models.CharField(max_length=256, db_column="nome_centro")
    sigla_centro = models.CharField(
        max_length=16, unique=True, db_column="sigla_centro"
    )
    cod_estruturado = models.CharField(
        max_length=15, unique=True, db_column="cod_estruturado"
    )

    class Meta:
        managed = False
        db_table = "centros"

    def __str__(self) -> str:
        return self.nome_centro


class SituacaoUnidade(models.Model):
    id_situacao_unidade = models.AutoField(
        primary_key=True, db_column="id_situacao_unidade"
    )
    situacao_unidade = models.CharField(max_length=16, db_column="situacao_unidade")

    class Meta:
        managed = False
        db_table = "v_situacoes_unidades"

    def __str__(self):
        return self.situacao_unidade


class TipoUnidade(models.Model):
    id_tipo_unidade = models.AutoField(primary_key=True, db_column="id_tipo_unidade")
    tipo_unidade = models.CharField(max_length=128, db_column="tipo_unidade")

    class Meta:
        managed = False
        db_table = "v_tipos_unidades"

    def __str__(self):
        return self.tipo_unidade


class UnidadeSIE(models.Model):
    id_unidade_sie = models.AutoField(primary_key=True, db_column="id_unidade_sie")
    nome_unidade = models.CharField(
        max_length=256, unique=False, db_column="nome_unidade"
    )
    cod_estruturado = models.CharField(
        max_length=15, unique=True, db_column="cod_estruturado"
    )

    centro = models.ForeignKey(
        Centro, models.DO_NOTHING, db_column="id_centro_sie", db_constraint=False
    )
    tipo_unidade = models.ForeignKey(
        TipoUnidade,
        models.DO_NOTHING,
        db_column="id_tipo_unidade",
        db_constraint=False,
    )
    situacao_unidade = models.ForeignKey(
        SituacaoUnidade,
        models.DO_NOTHING,
        db_column="id_situacao_unidade",
        db_constraint=False,
    )

    class Meta:
        managed = False
        db_table = "v_unidades_sie"


class Unidade(models.Model):
    """
    Uma unidade pertence a um centro. A hierarquia (centro -> subunidades -> ...) é
    dada por ``unidade_pai``. O ``cod_estruturado`` continua existindo como dado de
    origem (vem do SIE), mas a árvore é consultada pela FK, não pela string.

    As subunidades não recebem dinheiro de fato: recebem um "cheque" (saldo no razão,
    ver ``despesas.models.Lancamento``) e pedem ao centro que pague suas despesas.
    """

    objects = UnidadeManager()

    id_unidade_interna = models.AutoField(
        primary_key=True, db_column="id_unidade_interna"
    )
    unidade_sie = models.OneToOneField(
        UnidadeSIE,
        null=True,
        blank=False,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        db_column="id_unidade_sie",
    )

    nome_unidade = models.CharField(
        max_length=256, blank=False, null=False, db_column="nome_unidade"
    )
    cod_estruturado = models.CharField(
        max_length=15, unique=True, blank=False, null=False, db_column="cod_estruturado"
    )

    centro = models.ForeignKey(
        Centro,
        models.DO_NOTHING,
        blank=False,
        null=False,
        db_column="id_centro_interno",
    )
    unidade_pai = models.ForeignKey(
        "self",
        models.PROTECT,
        null=True,
        blank=True,
        related_name="subunidades",
        db_column="id_unidade_pai",
        db_comment="Unidade imediatamente acima na hierarquia; nulo para unidades de topo do centro",
    )
    tipo_unidade = models.ForeignKey(
        TipoUnidade,
        models.DO_NOTHING,
        blank=False,
        null=False,
        db_column="id_tipo_unidade",
        db_constraint=False,
    )
    situacao_unidade = models.ForeignKey(
        SituacaoUnidade,
        models.DO_NOTHING,
        blank=False,
        null=False,
        db_column="id_situacao_unidade",
        db_constraint=False,
    )

    class Meta:
        managed = False
        db_table = "unidades"
        constraints = [
            models.CheckConstraint(
                condition=~Q(unidade_pai=F("id_unidade_interna")),
                name="ck_unidade_nao_e_pai_de_si_mesma",
            )
        ]

    def __str__(self) -> str:
        return self.nome_unidade

    def clean(self):
        if self.unidade_pai_id:
            if self.unidade_pai_id == self.pk:
                raise ValidationError("Uma unidade não pode ser pai de si mesma.")
            if self.unidade_pai.centro_id != self.centro_id:
                raise ValidationError(
                    "A unidade pai precisa pertencer ao mesmo centro da unidade."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def ancestrais(self):
        """Do pai imediato até o topo da árvore."""
        resultado = []
        atual = self.unidade_pai
        while atual is not None:
            resultado.append(atual)
            atual = atual.unidade_pai
        return resultado


class Curso(models.Model):
    id_curso = models.AutoField(primary_key=True, db_column="id_curso")
    centro = models.ForeignKey(
        Centro,
        on_delete=models.DO_NOTHING,
        db_column="id_centro_interno",
        db_constraint=False,
    )
    nome_curso = models.TextField(
        max_length=256, unique=False, null=False, blank=False, db_column="nome_curso"
    )
    nivel_curso = models.TextField(
        max_length=256, unique=False, null=False, blank=False, db_column="nivel_curso"
    )
    modalidade_curso = models.TextField(
        max_length=256,
        unique=False,
        null=False,
        blank=False,
        db_column="modalidade_curso",
    )
    classificacao_curso = models.TextField(
        max_length=256,
        unique=False,
        null=False,
        blank=False,
        db_column="classificacao_curso",
    )

    class Meta:
        managed = False
        db_table = "v_cursos"


class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True, db_column="id_cargo")
    cargo = models.TextField(
        max_length=256, unique=False, null=False, blank=False, db_column="cargo"
    )

    class Meta:
        managed = False
        db_table = "v_cargos"

    def __str__(self):
        return self.cargo


class PessoaSIE(models.Model):
    id_pessoa_sie = models.AutoField(primary_key=True, db_column="id_pessoa_sie")
    nome_pessoa = models.TextField(
        max_length=256, unique=False, null=False, blank=False, db_column="nome_pessoa"
    )
    cpf = models.TextField(
        max_length=11, unique=False, null=False, blank=False, db_column="cpf"
    )
    rg = models.TextField(
        max_length=11, unique=False, null=False, blank=False, db_column="rg"
    )

    class Meta:
        managed = False
        db_table = "v_pessoas_sie"


class Pessoa(models.Model):
    """
    Pessoa interna. Quando existe no SIE, ``pessoa_sie`` aponta para o registro de
    origem; pessoas externas (que podem ser beneficiárias de um pagamento) não têm
    correspondente no SIE e ficam com ``pessoa_sie`` nulo.
    """

    objects = PessoaManager()

    id_pessoa_interna = models.AutoField(
        primary_key=True, db_column="id_pessoa_interna"
    )
    pessoa_sie = models.OneToOneField(
        PessoaSIE,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        db_constraint=False,
        db_column="id_pessoa_sie",
    )
    nome_pessoa = models.TextField(
        max_length=256, unique=False, null=False, blank=False, db_column="nome_pessoa"
    )
    cpf = models.TextField(
        max_length=11, unique=True, null=False, blank=False, db_column="cpf"
    )
    rg = models.TextField(
        max_length=11, unique=True, null=False, blank=False, db_column="rg"
    )

    class Meta:
        managed = False
        db_table = "pessoas"

    def __str__(self):
        return self.nome_pessoa

    @property
    def externa(self) -> bool:
        """Pessoa sem correspondente no SIE (não pode ser bolsista)."""
        return self.pessoa_sie_id is None


class Discente(models.Model):
    id_curso_aluno = models.AutoField(primary_key=True, db_column="id_curso_aluno")
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.DO_NOTHING,
        db_column="id_pessoa_interna",
        db_constraint=False,
    )
    matricula = models.TextField(
        max_length=32, unique=True, null=False, blank=False, db_column="matricula"
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.DO_NOTHING,
        db_column="id_curso",
        db_constraint=False,
    )
    ativo = models.BooleanField(
        unique=False, default=True, blank=True, db_column="ativo"
    )

    class Meta:
        managed = False
        db_table = "v_discentes"


class Servidor(models.Model):
    id_contrato_rh = models.AutoField(primary_key=True, db_column="id_contrato_rh")
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.DO_NOTHING,
        db_column="id_pessoa_interna",
        db_constraint=False,
    )
    matricula = models.TextField(
        max_length=32, unique=True, null=False, blank=False, db_column="matricula"
    )
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.DO_NOTHING,
        db_column="id_cargo",
        db_constraint=False,
    )
    ativo = models.BooleanField(
        unique=False, default=True, blank=True, db_column="ativo"
    )

    class Meta:
        managed = False
        db_table = "v_servidores"


class Email(models.Model):
    id_email = models.AutoField(primary_key=True, db_column="id_email")
    pessoa = models.ForeignKey(
        Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa_interna"
    )
    email = models.EmailField(unique=True, db_column="email")
    ativo = models.BooleanField(
        unique=False, default=True, blank=True, db_column="ativo"
    )

    class Meta:
        managed = False
        db_table = "emails"


class Telefone(models.Model):
    id_telefone = models.AutoField(primary_key=True, db_column="id_telefone")
    pessoa = models.ForeignKey(
        Pessoa, on_delete=models.DO_NOTHING, db_column="id_pessoa_interna"
    )
    telefone = models.TextField(
        max_length=16, unique=False, null=False, blank=False, db_column="telefone"
    )
    ativo = models.BooleanField(
        unique=False, default=True, blank=True, db_column="ativo"
    )

    class Meta:
        managed = False
        db_table = "telefones"
