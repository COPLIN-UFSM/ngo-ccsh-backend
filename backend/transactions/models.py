from operator import truediv
from django.db import models
from users.models import CustomUser


class TiposDocumentos(models.Model):
    id_tipo_documento = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "tipos_documentos"

    def __str__(self) -> str:
        return self.tipo_documento


class Documentos(models.Model):
    id_documento = models.AutoField(primary_key=True)
    tipo_documento = models.ForeignKey(
        TiposDocumentos, models.DO_NOTHING, db_column="id_tipo_documento"
    )

    transacao = models.ForeignKey(
        "Transacoes", models.DO_NOTHING, db_column="id_transacao"
    )

    descricao = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "documentos"


class Finalidades(models.Model):
    id_finalidade = models.AutoField(primary_key=True)
    tipo_despesa = models.ForeignKey(
        "TipoDespesa",
        models.DO_NOTHING,
        db_column="id_tipo_despesa",
    )

    subtipo_finalidade = models.ForeignKey(
        "SubtipoFinalidades", models.DO_NOTHING, db_column="id_subtipo_finalidade"
    )
    finalidade = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "finalidades"


class NaturezaTransacao(models.Model):
    id_tipo_transacao = models.AutoField(primary_key=True)
    tipo_transacao = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "natureza_transacao"

    def __str__(self) -> str:
        return self.tipo_transacao


class Status(models.Model):
    id_status = models.AutoField(primary_key=True)
    status = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "status"

    def __str__(self) -> str:
        return self.status


class SubtipoFinalidades(models.Model):
    id_subtipo_finalidade = models.AutoField(
        primary_key=True,
    )
    subtipo_finalidade = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "subtipo_finalidades"

    def __str__(self) -> str:
        return self.subtipo_finalidade


class Subunidades(models.Model):
    id_subunidade = models.AutoField(primary_key=True)
    subunidade = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "subunidades"

    def __str__(self) -> str:
        return self.subunidade


class TipoDespesa(models.Model):
    id_tipo_despesa = models.AutoField(primary_key=True)
    tipo_despesa = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tipo_despesa"

    def __str__(self) -> str:
        return self.tipo_despesa


class Beneficiarios(models.Model):
    id_beneficiario = models.AutoField(primary_key=True)
    nome_beneficiario = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    matricula = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "beneficiarios"

    def __str__(self) -> str:
        return self.nome_beneficiario


class Transacoes(models.Model):
    id_transacao = models.AutoField(primary_key=True)
    tipo_transacao = models.ForeignKey(
        NaturezaTransacao, models.DO_NOTHING, db_column="id_tipo_transacao"
    )
    transacao_pai = models.ForeignKey(
        "self", models.DO_NOTHING, db_column="id_transacao_pai", blank=True, null=True
    )
    finalidade = models.ForeignKey(
        Finalidades, models.DO_NOTHING, db_column="id_finalidade", blank=True, null=True
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
    usuario = models.IntegerField()
    status = models.ForeignKey(Status, models.DO_NOTHING, db_column="id_status")
    beneficiario = models.ForeignKey(
        Beneficiarios,
        models.DO_NOTHING,
        db_column="id_beneficiario",
        blank=True,
        null=True,
    )
    descricao = models.CharField(max_length=500, blank=True, null=True)
    montante = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    motivo_modificacao = models.CharField(max_length=500, blank=True, null=True)
    quantidade = models.FloatField(blank=True, null=True)
    local_techo = models.CharField(max_length=255, blank=True, null=True)
    data_lancamento = models.DateTimeField(blank=True, null=True)
    data_modificacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "transacoes"
