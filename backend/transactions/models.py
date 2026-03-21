from operator import truediv
from django.db import models
from users.models import CustomUser


class Finalidades(models.Model):
    id_finalidade = models.AutoField(primary_key=True)
    id_tabela_finalidade = models.ForeignKey(
        "TabelasFinalidades",
        models.DO_NOTHING,
        db_column="id_tabela_finalidade",
        blank=True,
        null=True,
    )
    id_tipo_despesa = models.ForeignKey(
        "TipoDespesa",
        models.DO_NOTHING,
        db_column="id_tipo_despesa",
        blank=True,
        null=True,
    )
    finalidade = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "finalidades"

    def __str__(self):
        return self.finalidade


class Status(models.Model):
    id_status = models.AutoField(primary_key=True)
    status = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = "status"

    def __str__(self):
        return self.status


class Subunidades(models.Model):
    id_subunidade = models.AutoField(primary_key=True)
    subunidade = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = "subunidades"

    def __str__(self):
        return self.subunidade


class TabelasFinalidades(models.Model):
    id_tabela_finalidade = models.AutoField(primary_key=True)
    tabela_finalidade = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "tabelas_finalidades"

    def __str__(self):
        return self.tabela_finalidade


class TipoDespesa(models.Model):
    id_tipo_despesa = models.IntegerField(primary_key=True)
    tipo_despesa = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tipo_despesa"

    def __str__(self):
        return self.tipo_despesa


class TiposDocumento(models.Model):
    id_tipo_documento = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "tipos_documento"

    def __str__(self):
        return self.tipo_documento


class TiposTransacoes(models.Model):
    id_tipo_transacao = models.AutoField(
        primary_key=True,
    )
    tipo_transacao = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "tipos_transacoes"

    def __str__(self):
        return self.tipo_transacao


class Transacoes(models.Model):
    id_transacao = models.IntegerField(primary_key=True)
    tipo_transacao = models.ForeignKey(
        TiposTransacoes, models.DO_NOTHING, db_column="id_tipo_transacao"
    )

    id_transacao_pai = models.ForeignKey(
        "self", models.DO_NOTHING, db_column="id_transacao_pai", blank=True, null=True
    )

    finalidade = models.ForeignKey(
        Finalidades,
        models.DO_NOTHING,
        db_column="id_finalidade",
        blank=True,
        null=True,
    )
    subunidade_credora = models.ForeignKey(
        Subunidades,
        models.DO_NOTHING,
        db_column="id_subunidade_credora",
        blank=True,
        null=True,
    )
    subunidade_executora = models.ForeignKey(
        Subunidades,
        models.DO_NOTHING,
        db_column="id_subunidade_executora",
        related_name="transacoes_id_subunidade_executora_set",
        blank=True,
        null=True,
    )
    usuario = models.ForeignKey(CustomUser, models.DO_NOTHING, db_column="id_usuario")
    status = models.ForeignKey(
        Status, models.DO_NOTHING, db_column="id_status", null=True
    )
    tipo_documento = models.ForeignKey(
        TiposDocumento,
        models.DO_NOTHING,
        db_column="id_tipo_documento",
        blank=True,
        null=True,
    )
    descricao = models.CharField(max_length=50, blank=True, null=True)
    montante = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    documento = models.CharField(max_length=50, blank=True, null=True)
    data_referencia = models.DateField(blank=True, null=True)
    data_lancamento = models.DateTimeField(blank=True, null=True)
    data_atualizacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "transacoes"

    def __str__(self):
        str = f"Transação {self.id_transacao} {self.finalidade.finalidade} | {self.subunidade_executora.subunidade} - {self.montante}"
        return str


class Beneficiarios(models.Model):
    id_beneficiario = models.IntegerField(primary_key=True)
    nome_beneficiario = models.CharField(max_length=100, blank=True, null=True)
    matricula = models.CharField(max_length=11, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "beneficiarios"


class Bolsas(models.Model):
    id_transacao = models.OneToOneField(
        Transacoes, models.DO_NOTHING, db_column="id_transacao", primary_key=True
    )
    id_beneficiario = models.ForeignKey(
        Beneficiarios,
        models.DO_NOTHING,
        db_column="id_beneficiario",
        blank=True,
        null=True,
    )
    op_sf = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "bolsas"


class Diarias(models.Model):
    id_transacao = models.OneToOneField(
        Transacoes, models.DO_NOTHING, db_column="id_transacao", primary_key=True
    )
    id_beneficiario = models.ForeignKey(
        Beneficiarios,
        models.DO_NOTHING,
        db_column="id_beneficiario",
        blank=True,
        null=True,
    )
    local = models.CharField(max_length=50, blank=True, null=True)
    quantidade_diarias = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "diarias"


class Empenho(models.Model):
    id_transacao = models.OneToOneField(
        Transacoes, models.DO_NOTHING, db_column="id_transacao", primary_key=True
    )
    empenho_sie = models.CharField(max_length=50, blank=True, null=True)
    empenho_siafe = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "empenho"


class Grafica(models.Model):
    id_transacao = models.OneToOneField(
        Transacoes, models.DO_NOTHING, db_column="id_transacao", primary_key=True
    )
    cnpj_empresa = models.CharField(max_length=14, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "grafica"


class Hospedagem(models.Model):
    id_transacao = models.OneToOneField(
        Transacoes, models.DO_NOTHING, db_column="id_transacao", primary_key=True
    )
    id_beneficiario = models.ForeignKey(
        Beneficiarios,
        models.DO_NOTHING,
        db_column="id_beneficiario",
        blank=True,
        null=True,
    )
    quantidade_diarias = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "hospedagem"


class Manutencao(models.Model):
    id_transacao = models.OneToOneField(
        Transacoes, models.DO_NOTHING, db_column="id_transacao", primary_key=True
    )
    setor = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "manutencao"


class Passagens(models.Model):
    id_transacao = models.OneToOneField(
        Transacoes, models.DO_NOTHING, db_column="id_transacao", primary_key=True
    )
    id_beneficiario = models.ForeignKey(
        Beneficiarios,
        models.DO_NOTHING,
        db_column="id_beneficiario",
        blank=True,
        null=True,
    )
    trecho = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "passagens"


class Refeicoes(models.Model):
    id_transacao = models.OneToOneField(
        Transacoes, models.DO_NOTHING, db_column="id_transacao", primary_key=True
    )
    id_beneficiario = models.ForeignKey(
        Beneficiarios,
        models.DO_NOTHING,
        db_column="id_beneficiario",
        blank=True,
        null=True,
    )
    quantidade = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "refeicoes"
