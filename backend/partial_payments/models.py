from django.db import models


# Empenho inicial para cada despesa. Valor a qual o crédito e débito serão realizado.
class EmpenhoPagamentoParcial(models.Model):
    id_empenho = models.AutoField(primary_key=True)
    empenho = models.CharField(unique=True, max_length=50)
    descricao = models.CharField(max_length=50)
    montante = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, default=0.00
    )
    ativo = models.BooleanField(default=True, blank=True)


# # Crédito, Débito
# class TipoTransacaoPagamentoParcial(models.Model):
#     id_tipo_transacao = models.AutoField(primary_key=True)
#     ativo = models.BooleanField(default=True, blank=True)
#     tipo_transacao = models.CharField(unique=True, max_length=20)
#     ativo = models.BooleanField(default=True, blank=True)


# Fatura/Nota Fiscal / Empenho
class TipoDocumentoPagamentoParcial(models.Model):
    id_tipo_documento = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(unique=True, max_length=20)
    ativo = models.BooleanField(default=True, blank=True)


# Adicionar a fatura
class TransacaoPagamentoParcial(models.Model):
    id_transacao = models.AutoField(primary_key=True)
    empenho_pai = models.ForeignKey(
        EmpenhoPagamentoParcial, models.DO_NOTHING, db_column="id_empenho"
    )
    tipo_documento = models.ForeignKey(
        TipoDocumentoPagamentoParcial, models.DO_NOTHING, db_column="id_tipo_documento"
    )
    credito = models.BooleanField(default=False)

    documento = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(max_length=50)
    data_lancamento = models.DateField(auto_now=True)
    montante = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True, blank=True)
