# Fatura/Nota Fiscal / Empenho
# class TipoDocumentoPagamentoParcial(models.Model):
#     id_tipo_documento = models.AutoField(primary_key=True)
#     tipo_documento = models.CharField(unique=True, max_length=50)
#     ativo = models.BooleanField(default=True, blank=True)
#
#     class Meta:
#         managed = False
#         db_table = "pagamento_parcial_tipo_documento"
#         verbose_name = "Tipo de documento"


# Adicionar a fatura
# class TransacaoPagamentoParcial(models.Model):
#     id_transacao = models.AutoField(primary_key=True)
#     empenho_pai = models.ForeignKey(
#         Empenho, models.DO_NOTHING, db_column="id_empenho"
#     )
#     tipo_documento = models.ForeignKey(
#         # Henry: troquei mas não sei se funciona!
#         TipoDocumento, models.DO_NOTHING, db_column="id_tipo_documento"
#     )
#     eh_credito = models.BooleanField(default=False, db_column="credito")
#
#     documento = models.CharField(max_length=50, unique=True)
#     descricao = models.TextField(max_length=50)
#     data_lancamento = models.DateField(auto_now=True)
#     montante = models.DecimalField(max_digits=10, decimal_places=2)
#
#     class Meta:
#         managed = False
#         db_table = "pagamento_parcial_transacao"
#         verbose_name = "Transação"
#         # Mudar para DataTime o Date...
#         ordering = ["id_transacao"]
