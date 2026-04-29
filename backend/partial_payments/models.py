from django.db import models
from django.db.models import Sum, Case, When, F, DecimalField
from decimal import Decimal


# Empenho inicial para cada despesa. Valor a qual o crédito e débito serão realizado.
class EmpenhoPagamentoParcial(models.Model):
    id_empenho = models.AutoField(primary_key=True)
    empenho = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(max_length=200)
    ativo = models.BooleanField(default=True, blank=True)

    @property
    def montante(self):
        related_transaciton = TransacaoPagamentoParcial.objects.filter(
            empenho_pai=self
        ).aggregate(
            montante=Sum(
                Case(
                    When(eh_credito=True, then=F("montante")),
                    When(eh_credito=False, then=-F("montante")),
                    default=Decimal(0.00),
                ),
                output_field=DecimalField(),
            )
        )
        return related_transaciton["montante"] or Decimal(0.00)

    class Meta:
        managed = False
        db_table = "pagamento_parcial_empenho"


# Fatura/Nota Fiscal / Empenho
class TipoDocumentoPagamentoParcial(models.Model):
    id_tipo_documento = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(unique=True, max_length=20)
    ativo = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = False
        db_table = "pagamento_parcial_tipo_documento"
        verbose_name = "Tipo de documento"


# Adicionar a fatura
class TransacaoPagamentoParcial(models.Model):
    id_transacao = models.AutoField(primary_key=True)
    empenho_pai = models.ForeignKey(
        EmpenhoPagamentoParcial, models.DO_NOTHING, db_column="id_empenho"
    )
    tipo_documento = models.ForeignKey(
        TipoDocumentoPagamentoParcial, models.DO_NOTHING, db_column="id_tipo_documento"
    )
    eh_credito = models.BooleanField(default=False, db_column="credito")

    documento = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(max_length=50)
    data_lancamento = models.DateField(auto_now=True)
    montante = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = "pagamento_parcial_transacao"
        verbose_name = "Transação"
        # Mudar para DataTime o Date...
        ordering = ["id_transacao"]
