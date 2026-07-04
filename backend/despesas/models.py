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
    grupo_finalidade = models.ForeignKey(GrupoFinalidade, models.DO_NOTHING, db_column="id_grupo_finalidade")

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
    id_tipo_documento_finalidade = models.AutoField(primary_key=True, db_column='id_tipo_documento_finalidade')
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


# pago, pendente, alocado
class StatusPagamento(models.Model):
    id_status_pagamento = models.AutoField(primary_key=True, db_column='id_status_pagamento')
    status_pagamento = models.TextField(max_length=64, db_column='status_pagamento')

    class Meta:
        managed = False
        db_table = "status_pagamento"


class Transacao(models.Model):
    id_transacao = models.AutoField(primary_key=True, db_column='id_transacao')
    id_transacao_anterior = models.OneToOneField("Transacao", models.DO_NOTHING, db_column="id_transacao_anterior")

    empenho = models.ForeignKey(
        Empenho, models.DO_NOTHING,
        blank=True, null=True,
        db_column="id_empenho"
    )

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
        blank=False,
        null=False,
    )

    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column="id_usuario")

    status_pagamento = models.ForeignKey(
        StatusPagamento,
        on_delete=models.DO_NOTHING,
        db_column="id_status_pagamento"
    )

    beneficiario = models.ForeignKey(
        Pessoa,
        models.DO_NOTHING,
        db_column="id_beneficiario",
        blank=True,
        null=True,
    )

    credito = models.BooleanField(default=False, blank=True)
    montante = models.DecimalField(decimal_places=2, blank=True, null=True, default=Decimal(0.00))
    data_lancamento = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        managed = False
        db_table = "transacoes"
