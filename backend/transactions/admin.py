from django.contrib import admin
from . import models

# Register your models here.


class FinalidadeAdmin(admin.ModelAdmin):
    pass


class SubunidadesAdmin(admin.ModelAdmin):
    pass


class StatusAdmin(admin.ModelAdmin):
    pass


class TabelasFinalidadesAdmin(admin.ModelAdmin):
    pass


class TipoDespesaAdmin(admin.ModelAdmin):
    pass


class TiposDocumentoAdmin(admin.ModelAdmin):
    pass


class TiposTransacoesAdmin(admin.ModelAdmin):
    pass


class BeneficiariosAdmin(admin.ModelAdmin):
    pass


class BolsasAdmin(admin.ModelAdmin):
    pass


class DiariasAdmin(admin.ModelAdmin):
    pass


class EmpenhoAdmin(admin.ModelAdmin):
    pass


class GraficaAdmin(admin.ModelAdmin):
    pass


class HospedagemAdmin(admin.ModelAdmin):
    pass


class ManutencaoAdmin(admin.ModelAdmin):
    pass


class PassagensAdmin(admin.ModelAdmin):
    pass


class RefeicoesAdmin(admin.ModelAdmin):
    pass


class TransacoesAdmin(admin.ModelAdmin):
    fields = [
        "id_transacao",
        "id_transacao_pai",
        "tipo_transacao",
        "montante",
        "finalidade",
        "subunidade_credora",
        "subunidade_executora",
        "usuario",
        "status",
        "tipo_documento",
        "documento",
        "descricao",
        "data_referencia",
    ]
    ordering = ["id_transacao"]


admin.site.register(models.Transacoes, TransacoesAdmin)


# admin.site.register(models.Transacoes, FinalidadeAdmin)
# admin.site.register(models.Transacoes, StatusAdmin)
# admin.site.register(models.Transacoes, SubunidadesAdmin)
# admin.site.register(models.Transacoes, )
# admin.site.register(models.Transacoes, TransacoesAdmin)
# admin.site.register(models.Transacoes, TransacoesAdmin)
# admin.site.register(models.Transacoes, TransacoesAdmin)
# admin.site.register(models.Transacoes, TransacoesAdmin)
# admin.site.register(models.Transacoes, TransacoesAdmin)
# admin.site.register(models.Transacoes, TransacoesAdmin)
# admin.site.register(models.Transacoes, TransacoesAdmin)
