from django.db import models
from django.core.validators import MinLengthValidator
from usuarios.models import Usuario

from decimal import Decimal
from django.db.models import Sum, Case, When, F, DecimalField

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
    tipo_unidade = models.CharField(max_length=64, db_column='tipo_unidade')

    class Meta:
        managed = False
        db_table = "v_tipos_unidades"

class Unidade(models.Model):
    id_unidade = models.AutoField(primary_key=True, db_column='id_unidade')
    nome_unidade = models.CharField(max_length=256, unique=True, db_column='nome_unidade')
    cod_estruturado = models.CharField(max_length=15, unique=True, db_column='cod_estruturado')

    centro = models.ForeignKey(Centro, models.DO_NOTHING, db_column="id_centro")
    tipo_unidade = models.ForeignKey(TipoUnidade, models.DO_NOTHING, db_column="id_tipo_unidade")
    situacao_unidade = models.ForeignKey(SituacaoUnidade, models.DO_NOTHING, db_column="id_situacao")

    class Meta:
        managed = False
        db_table = "v_unidades"

    def __str__(self) -> str:
        return self.nome_unidade

# TODO daqui pra baixo nada tá ok

class NaturezaFinalidade(models.Model):
    id_natureza_finalidade = models.AutoField(primary_key=True)
    natureza_finalidade = models.CharField(max_length=100, unique=True)
    ativo = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = False
        db_table = "naturezas_finalidades"

    def __str__(self) -> str:
        return self.natureza_finalidade


class TipoFinalidade(models.Model):
    id_tipo_finalidade = models.AutoField(
        primary_key=True,
    )
    tipo_finalidade = models.CharField(max_length=255, unique=True)
    ativo = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = False
        db_table = "tipos_finalidades"

    def __str__(self) -> str:
        return self.tipo_finalidade


class Finalidade(models.Model):

    class Modalidade(models.TextChoices):
        IDR = "IDR", "IDR"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferência"
        DESPESA = "DESPESA", "Despesa"

    id_finalidade = models.AutoField(primary_key=True)
    natureza_finalidade = models.ForeignKey(
        NaturezaFinalidade,
        models.DO_NOTHING,
        db_column="id_tipo_despesa",
    )
    tipo_finalidade = models.ForeignKey(
        TipoFinalidade, models.DO_NOTHING, db_column="id_tipo_finalidade"
    )  # Isso aqui é para Bolsa-Bolsa 2A terem os mesmo campos.
    modalidade = models.CharField(choices=Modalidade.choices, default=Modalidade.DESPESA)
    finalidade = models.CharField(max_length=255, unique=True)
    ativo = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = False
        db_table = "finalidades"


class Beneficiario(models.Model):
    id_beneficiario = models.AutoField(primary_key=True)
    beneficiario = models.CharField(max_length=100)
    cpf = models.CharField(
        max_length=11,
        validators=[MinLengthValidator(11, message="O CPF deve conter pelo menos 11 caracteres.")],
        help_text="Digite o CPF apenas com números.",
        unique=True,
    )
    matricula = models.CharField(max_length=50, blank=True, null=True, unique=True)
    ativo = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = False
        db_table = "beneficiarios"

    def __str__(self) -> str:
        return self.beneficiario


class Empenho(models.Model):
    id_empenho = models.AutoField(primary_key=True)
    empenho = models.CharField(max_length=50, unique=True)
    pen = models.CharField(max_length=100, unique=True, null=True, blank=True)
    descricao = models.TextField(max_length=200)
    finalidade = models.ForeignKey(Finalidade, models.DO_NOTHING, db_column="id_finalidade")
    data = models.DateField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "empenhos"

    @property
    def montante(self):
        related_transaction = Transacao.objects.filter(empenho=self).aggregate(
            montante=Sum(
                Case(
                    When(eh_credito=True, then=F("montante")),
                    When(eh_credito=False, then=-F("montante")),
                    default=Decimal(0.00),
                ),
                output_field=DecimalField(),
            )
        )
        return related_transaction["montante"] or Decimal(0.00)


class TipoDocumento(models.Model):
    id_tipo_documento = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(max_length=100, unique=True)
    ativo = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = False
        db_table = "tipos_documentos"

    def __str__(self) -> str:
        return self.tipo_documento


class Documento(models.Model):
    id_documento = models.AutoField(primary_key=True)
    tipo_documento = models.ForeignKey(TipoDocumento, models.DO_NOTHING, db_column="id_tipo_documento")
    documento = models.CharField(max_length=100)

    transacao = models.ForeignKey("Transacao", models.DO_NOTHING, db_column="id_transacao", related_name="documentos")

    descricao = models.CharField(max_length=255, blank=True, null=True)
    ativo = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = False
        db_table = "documentos"


class Transacao(models.Model):
    class Status(models.TextChoices):
        PAGO = "PAGO"
        PENDENTE = "PENDENTE"
        ALOCADO = "ALOCADO"

    id_transacao = models.AutoField(primary_key=True)
    transacao_pai = models.ForeignKey("self", models.DO_NOTHING, db_column="id_transacao_pai", blank=True, null=True)
    empenho = models.ForeignKey(Empenho, models.DO_NOTHING, db_column="id_empenho", blank=True, null=True, related_name="transacoes")

    finalidade = models.ForeignKey(Finalidade, models.DO_NOTHING, db_column="id_finalidade", blank=True, null=True)

    subunidade_credora = models.ForeignKey(
        Unidade,
        models.DO_NOTHING,
        db_column="id_subunidade_credora",
        blank=True,
        null=True,
    )
    subunidade_executora = models.ForeignKey(
        Unidade,
        models.DO_NOTHING,
        db_column="id_subunidade_executora",
        related_name="transacoes_id_subunidade_executora_set",
    )

    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column="id_usuario")
    status = models.CharField(choices=Status.choices, default=Status.PENDENTE, max_length=255)

    beneficiario = models.ForeignKey(
        Beneficiario,
        models.DO_NOTHING,
        db_column="id_beneficiario",
        blank=True,
        null=True,
    )
    eh_credito = models.BooleanField(default=False, blank=True)
    motivo_modificacao = models.CharField(max_length=500, blank=True, null=True)

    descricao = models.CharField(max_length=500, blank=True, null=True)
    montante = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    quantidade = models.FloatField(blank=True, null=True)
    local_trecho = models.CharField(max_length=255, blank=True, null=True)
    data_lancamento = models.DateTimeField(blank=True, auto_now_add=True)
    data_modificacao = models.DateTimeField(blank=True, auto_now=True)

    class Meta:
        managed = False
        db_table = "transacoes"
