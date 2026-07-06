from decimal import Decimal

from django.db import models
from django.db.models import Sum, Case, When, F, DecimalField

from entidades.models import Unidade, Pessoa
from usuarios.models import Usuario


class NaturezaFinalidade(models.Model):
    """
    Pode ser IDR (distribuição orçamentária inicial), custeio, capital, transferência, ou outras categorias com reserva
    de recursos (e.g. Bolsas PRAE, para as quais os fundos não podem ser usados para outras finalidades)
    """
    id_natureza_finalidade = models.AutoField(primary_key=True, db_column='id_natureza_finalidade')
    natureza_finalidade = models.CharField(max_length=128, unique=True, db_column='natureza_finalidade')
    ativo = models.BooleanField(default=True, blank=True, db_column='ativo')

    class Meta:
        managed = False
        db_table = "naturezas_finalidades"

    def __str__(self) -> str:
        return self.natureza_finalidade


class GrupoFinalidade(models.Model):
    """
    Um grupo é um conjunto de finalidades similares, por exemplo Bolsas 2A, Bolsas PRAE, Bolsas de Monitoria são todas
    pertencentes ao grupo Bolsas.
    """
    id_grupo_finalidade = models.AutoField(primary_key=True, db_column='id_grupo_finalidade')
    grupo_finalidade = models.CharField(max_length=256, unique=True, db_column='grupo_finalidade')
    ativo = models.BooleanField(default=True, blank=True, db_column='ativo')

    class Meta:
        managed = False
        db_table = "grupos_finalidades"

    def __str__(self) -> str:
        return self.grupo_finalidade


class Finalidade(models.Model):
    """
    Uma finalidade é um destino para uma transação. Por exemplo, dentro do GrupoFinalidade Bolsas, existem
    as finalidades de bolsa 2A, bolsa Monitoria, bolsa Descubra...
    """
    id_finalidade = models.AutoField(primary_key=True, db_column='id_finalidade')
    natureza_finalidade = models.ForeignKey(NaturezaFinalidade, models.DO_NOTHING, db_column="id_natureza_finalidade")
    grupo_finalidade = models.ForeignKey(GrupoFinalidade, models.DO_NOTHING, db_column="id_grupo_finalidade", null=True, blank=True)

    finalidade = models.CharField(max_length=512, unique=True, null=False, blank=False)
    ativo = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = False
        db_table = "finalidades"


class TipoDocumento(models.Model):
    """
    Um tipo de documento é uma informação necessária a alguns tipos de finalidade. Por exemplo,
    uma bolsa precisa de uma Lista SIAFI.
    """
    id_tipo_documento = models.AutoField(primary_key=True, db_column='id_tipo_documento')
    tipo_documento = models.CharField(max_length=128, unique=True, db_column='tipo_documento')
    ativo = models.BooleanField(default=True, blank=True, db_column='ativo')

    class Meta:
        managed = False
        db_table = "tipos_documentos"

    def __str__(self) -> str:
        return self.tipo_documento


class TiposDocumentosParaFinalidades(models.Model):
    """
    Tabela que liga os tipos de documentos às finalidades.
    """
    pk = models.CompositePrimaryKey("tipo_documento_id", "finalidade_id")
    tipo_documento = models.ForeignKey(TipoDocumento, models.DO_NOTHING, db_column="id_tipo_documento")
    finalidade = models.ForeignKey(Finalidade, models.DO_NOTHING, db_column="id_finalidade")
    obrigatorio = models.BooleanField(
        default=True, blank=True, db_column='obrigatorio',
        db_comment='Se este tipo de documento é obrigatório para esta finalidade'
    )

    class Meta:
        managed = False
        db_table = "tipos_documentos_para_finalidades"


class ValorDocumento(models.Model):
    """
    Valor de um documento. Por exemplo, o valor da Lista SIAFI.
    """
    id_valor_documento = models.AutoField(primary_key=True, db_column='id_valor_documento')
    tipo_documento = models.ForeignKey(TipoDocumento, models.DO_NOTHING, db_column="id_tipo_documento")
    transacao = models.ForeignKey("Transacao", models.DO_NOTHING, related_name="documentos", db_column="id_transacao")

    valor_documento = models.CharField(max_length=256, db_column='valor_documento')

    class Meta:
        managed = False
        db_table = "valores_documentos"


class Empenho(models.Model):
    id_empenho = models.AutoField(primary_key=True, db_column='id_empenho')
    numero_empenho = models.CharField(max_length=32, unique=True, db_column='numero_empenho')
    numero_pen = models.CharField(max_length=32, unique=True, null=True, blank=True, db_column='numero_pen')
    finalidade = models.ForeignKey(Finalidade, models.DO_NOTHING, db_column="id_finalidade")
    data_lancamento = models.DateTimeField(blank=True, auto_now_add=True)

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

    class Meta:
        managed = False
        db_table = "empenhos"


# pago, pendente, alocado
class StatusTransacao(models.Model):
    id_status_transacao = models.AutoField(primary_key=True, db_column='id_status_transacao')
    status_transacao = models.TextField(max_length=64, db_column='status_transacao')

    class Meta:
        managed = False
        db_table = "status_transacoes"


class Transacao(models.Model):
    """
    Transações imutáveis. As múltiplas versões de uma transação são armazenadas em VersaoTransacao.

    Cada nova versão é criada quando por exemplo o montante é atualizado, ou o status de pagamento trocado.
    """

    id_transacao = models.AutoField(primary_key=True, db_column="id_transacao")

    versao_transacao = models.OneToOneField(
        "VersaoTransacao",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
        db_column="id_versao_transacao",
    )

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "transacoes"


class VersaoTransacao(models.Model):
    """
    Versão de uma transação.

    Ao editar uma transação, uma nova versão de transação é criada.
    As versões existentes nunca são modificadas.
    """

    id_versao_transacao = models.AutoField(primary_key=True, db_column="id_versao_transacao")

    transacao = models.ForeignKey(Transacao, on_delete=models.PROTECT, related_name="versoes", db_column="id_transacao")

    numero_versao = models.PositiveIntegerField(default=1)

    empenho = models.ForeignKey(
        Empenho,
        models.DO_NOTHING,
        null=True,
        blank=True,
        db_column="id_empenho",
    )

    finalidade = models.ForeignKey(
        Finalidade,
        models.DO_NOTHING,
        null=True,
        blank=True,
        db_column="id_finalidade",
    )

    unidade_credora = models.ForeignKey(
        Unidade,
        models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="+",
        db_column="id_unidade_credora",
    )

    unidade_executora = models.ForeignKey(
        Unidade,
        models.DO_NOTHING,
        related_name="+",
        db_column="id_unidade_executora",
    )

    usuario = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column="id_usuario",
    )

    status_pagamento = models.ForeignKey(
        StatusTransacao,
        models.DO_NOTHING,
        db_column="id_status_pagamento",
    )

    beneficiario = models.ForeignKey(
        Pessoa,
        models.DO_NOTHING,
        null=True,
        blank=True,
        db_column="id_beneficiario",
    )

    credito = models.BooleanField(default=False)

    montante = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00")
    )

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "versoes_transacoes"

        constraints = [
            models.UniqueConstraint(
                fields=["transacao", "numero_versao"],
                name="uk_transacao_numero_versao",
            )
        ]

        ordering = ["numero_versao"]
