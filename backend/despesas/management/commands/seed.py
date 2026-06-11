from django.core.management.base import BaseCommand
from despesas.models import Beneficiario, Subunidade,Finalidade, TipoFinalidade, NaturezaFinalidade,TipoDocumento, Empenho, Transacao
from usuarios.models import Usuario

subunidades_insert = [
    Subunidade(subunidade="Proplan", grupo="Unidades"),
    Subunidade(subunidade="Depto. de C. Administrativas", grupo="DEPTO"),
    Subunidade(subunidade="Depto. de Direito", grupo="DEPTO"),
]

beneficiarios = [
    Beneficiario(beneficiario="Leandro", cpf="05186605085",matricula="202311173"),
    Beneficiario(beneficiario="Raíssa", cpf="00000000012",matricula="202411173")
]

tipos_documentos = [
    TipoDocumento(tipo_documento="Fatura"),
    TipoDocumento(tipo_documento="Lista SIAFE")
]

class Command(BaseCommand):
    help = 'Cria dados iniciais para o projeto'
    def handle(self, *args, **kwargs):
        bolsas, _ = TipoFinalidade.objects.get_or_create(tipo_finalidade="Bolsas")
        viagens, _ = TipoFinalidade.objects.get_or_create(tipo_finalidade="Viagens")
        
        custeio, _ = NaturezaFinalidade.objects.get_or_create(natureza_finalidade="Custeio")
        NaturezaFinalidade.objects.get_or_create(natureza_finalidade="Capital")

        finalidade,_ = Finalidade.objects.get_or_create(finalidade="Bolsa 2A", natureza_finalidade=custeio, tipo_finalidade=bolsas)
        Finalidade.objects.get_or_create(finalidade="Bolsa Formação", natureza_finalidade=custeio, tipo_finalidade=bolsas)
        Finalidade.objects.get_or_create(finalidade="Viagem Área", natureza_finalidade=custeio, tipo_finalidade=viagens)
        Finalidade.objects.get_or_create(finalidade="Bolsa PRAE", natureza_finalidade=custeio, tipo_finalidade=bolsas)
        
        subunidades = Subunidade.objects.bulk_create(subunidades_insert,ignore_conflicts=True)
        subunidade_1 = Subunidade.objects.filter(subunidade="Proplan").first()
        
        usuario = Usuario.objects.create_user(username="leandrogalbarino", email="leandrogalbarino@gmail.com", password="leandrogalbarino")

        Beneficiario.objects.bulk_create(beneficiarios,ignore_conflicts=True)
        empenho,_ = Empenho.objects.get_or_create(empenho="fsfdsf45", descricao="Empenho de bolsas 2A", finalidade=finalidade)
        transacao = Transacao.objects.get_or_create(
                finalidade=finalidade,
                empenho=empenho,
                subunidade_executora=subunidade_1,
                usuario=usuario,
                status="PAGO",
                descricao="Blá blá blá.........",
                montante=1.1,
                eh_credito=False
        )

