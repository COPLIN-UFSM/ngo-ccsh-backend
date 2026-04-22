from django.db import models
from users.models import CustomUser


class TipoDocumento(models.Model):
    id_tipo_documento = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "tipos_documentos"

    def __str__(self) -> str:
        return self.tipo_documento


class Documento(models.Model):
    id_documento = models.AutoField(primary_key=True)
    tipo_documento = models.ForeignKey(
        TipoDocumento, models.DO_NOTHING, db_column="id_tipo_documento"
    )

    transacao = models.ForeignKey(
        "Transacao", models.DO_NOTHING, db_column="id_transacao"
    )

    descricao = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "documentos"


class Finalidade(models.Model):
    id_finalidade = models.AutoField(primary_key=True)
    tipo_despesa = models.ForeignKey(
        "TipoDespesa",
        models.DO_NOTHING,
        db_column="id_tipo_despesa",
    )

    categoria_finalidade = models.ForeignKey(
        "CategoriaFinalidade", models.DO_NOTHING, db_column="id_categoria_finalidade"
    )
    finalidade = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "finalidades"


class TipoTransacao(models.Model):
    id_tipo_transacao = models.AutoField(primary_key=True)
    tipo_transacao = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "tipos_transacoes"

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


class CategoriaFinalidade(models.Model):
    id_categoria_finalidade = models.AutoField(
        primary_key=True,
    )
    categoria_finalidade = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "categorias_finalidades"

    def __str__(self) -> str:
        return self.categoria_finalidade


class Subunidade(models.Model):
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
        db_table = "tipos_despesa"

    def __str__(self) -> str:
        return self.tipo_despesa


class Beneficiario(models.Model):
    id_beneficiario = models.AutoField(primary_key=True)
    nome_beneficiario = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    matricula = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "beneficiarios"

    def __str__(self) -> str:
        return self.nome_beneficiario


class Transacao(models.Model):
    id_transacao = models.AutoField(primary_key=True)
    tipo_transacao = models.ForeignKey(
        TipoTransacao, models.DO_NOTHING, db_column="id_tipo_transacao"
    )
    transacao_pai = models.ForeignKey(
        "self", models.DO_NOTHING, db_column="id_transacao_pai", blank=True, null=True
    )
    finalidade = models.ForeignKey(
        Finalidade, models.DO_NOTHING, db_column="id_finalidade", blank=True, null=True
    )
    subunidade_credora = models.ForeignKey(
        Subunidade,
        models.DO_NOTHING,
        db_column="id_subunidade_credora",
        blank=True,
        null=True,
    )
    subunidade_executora = models.ForeignKey(
        Subunidade,
        models.DO_NOTHING,
        db_column="id_subunidade_executora",
        related_name="transacoes_id_subunidade_executora_set",
        blank=True,
        null=True,
    )
    usuario = models.IntegerField()
    status = models.ForeignKey(Status, models.DO_NOTHING, db_column="id_status")
    beneficiario = models.ForeignKey(
        Beneficiario,
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
