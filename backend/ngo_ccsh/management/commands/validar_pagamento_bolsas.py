"""
Executa cenários de provisionamento e pagamento de bolsas para validar o serviço.

Cada bolsa tem vínculo mensal com valor fixo de R$ 700,00. O comando testa três casos:

1. bolsa de 12 meses paga inteiramente com recursos de um único ano fiscal;
2. bolsa de 12 meses que atravessa dois anos fiscais: as parcelas do ano seguinte
   não podem ser reservadas enquanto o orçamento desse ano não existir e ficam
   "previstas" (compromisso futuro);
3. bolsa paga, em cada mês, com dinheiro de dois empenhos de finalidades diferentes
   e mesma natureza.

Todos os dados são criados em uma única transação e revertidos ao final.

Uso, a partir da pasta "backend":

    conda run -n ngo python manage.py validar_pagamento_bolsas --settings=ngo_ccsh.dev_settings

O fluxograma está em "backend/diagramas/validar_pagamento_bolsas.md".
"""

import datetime as dt
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from despesas import saldos, services
from despesas.models import Empenho, Finalidade, ParcelaBolsa, VinculoBolsa
from despesas.services import SaldoInsuficiente
from entidades.models import Cargo, Pessoa, PessoaSIE, Servidor
from ngo_ccsh.management.commands.validar_exercicio_financeiro import Command as ComandoExercicio

MENSALIDADE = Decimal("700.00")


class Command(BaseCommand):
    help = (
        "Valida o provisionamento e o pagamento de bolsas em três cenários: "
        "(1) uma bolsa totalmente dentro de um ano fiscal; "
        "(2) uma bolsa que dura dois anos fiscais; "
        "(3) uma Lista SIAFI que é paga por dois empenhos distintos. "
        "Não faz persistência de dados."
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    "Validação do pagamento de bolsas (os dados serão revertidos)"
                )
            )
            base = ComandoExercicio._criar_referencias_de_teste()
            self._preparar_orcamento(base)
            self._caso_1_um_ano_fiscal(base)
            self._caso_2_dois_anos_fiscais(base)
            self._caso_3_dois_empenhos(base)
            self._conferir_saldos_finais(base)

            transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                "Bolsas validadas: os três casos foram pagos e os saldos conferidos. "
                "Os dados de teste foram revertidos."
            )
        )

    def _preparar_orcamento(self, base):
        """
        Cria as finalidades e os empenhos e distribui o orçamento do ano corrente.

        Total necessário no ano:

        caso 1 (12 x 700) + caso 2 (6 x 700) + caso 3 (3 x 700) = 14.700,00
        distribuídos integralmente para uma unidade.
        """
        ano = base["ano_fiscal"]
        natureza = base["natureza"]
        centro = base["centro"]
        usuario = base["usuario"]
        sufixo = base["sufixo"]

        base["finalidade_bolsa_2a"] = Finalidade.objects.create(nome=f"Bolsa 2A {sufixo}", natureza=natureza)
        base["finalidade_monitoria"] = Finalidade.objects.create(nome=f"Bolsa Monitoria {sufixo}", natureza=natureza)
        base["finalidade_extensao"] = Finalidade.objects.create(nome=f"Bolsa Extensão {sufixo}", natureza=natureza)

        orcamento_ano = Decimal("14700.00")

        services.creditar(centro, ano, natureza, orcamento_ano, usuario)

        base["empenho_1"] = self._empenho(base, "1", base["finalidade_bolsa_2a"], ano, 8400)
        base["empenho_2"] = self._empenho(base, "2", base["finalidade_bolsa_2a"], ano, 4200)
        base["empenho_3"] = self._empenho(base, "3", base["finalidade_monitoria"], ano, 1260)
        base["empenho_4"] = self._empenho(base, "4", base["finalidade_extensao"], ano, 840)

        services.distribuir(centro, ano, natureza, base["unidade"], orcamento_ano, usuario)

        self.stdout.write(f"[preparo] {ano}: R$ {orcamento_ano} creditados, empenhados e distribuídos.")

    @staticmethod
    def _empenho(base, numero, finalidade, ano, valor):
        empenho = Empenho.objects.create(
            numero_empenho=f"{base['sufixo']}{numero}",
            centro=base["centro"],
            ano_fiscal=ano,
            natureza=base["natureza"],
            finalidade=finalidade,
        )
        services.reforcar_empenho(empenho, Decimal(valor), base["usuario"])
        return empenho

    @staticmethod
    def _criar_bolsista(sufixo, indice):
        """Bolsistas precisam existir no SIE e ser servidores ou discentes."""
        cpf = f"{sufixo}{indice:03d}"
        pessoa_sie = PessoaSIE.objects.create(
            nome_pessoa=f"Bolsista {indice} {sufixo}", cpf=cpf, rg=cpf
        )
        pessoa = Pessoa.objects.create(
            pessoa_sie=pessoa_sie, nome_pessoa=pessoa_sie.nome_pessoa, cpf=cpf, rg=cpf
        )
        cargo, _ = Cargo.objects.get_or_create(cargo="Professor")
        Servidor.objects.create(pessoa=pessoa, matricula=f"m{cpf}", cargo=cargo)
        return pessoa

    def _criar_vinculo(self, base, indice, finalidade, inicio, fim):
        vinculo = VinculoBolsa.objects.create(
            bolsista=self._criar_bolsista(base["sufixo"], indice),
            unidade=base["unidade"],
            finalidade=finalidade,
            valor_mensal=MENSALIDADE,
            inicio=inicio,
            fim=fim,
        )
        parcelas = services.gerar_parcelas(vinculo)
        return vinculo, parcelas

    # --- casos -------------------------------------------------------------------

    def _caso_1_um_ano_fiscal(self, base):
        """
        Bolsa de janeiro a dezembro: todas as 12 parcelas saem do mesmo ano.
        """

        ano = base["ano_fiscal"]
        vinculo, parcelas = self._criar_vinculo(
            base,
            1,
            finalidade=base["finalidade_bolsa_2a"],
            inicio=dt.date(ano, 1, 1),
            fim=dt.date(ano, 12, 31)
        )
        self._conferir("parcelas do caso 1", len(parcelas), 12)
        self._conferir(
            "parcelas do caso 1 no ano fiscal", {p.ano_fiscal for p in parcelas}, {ano}
        )
        for parcela in parcelas:
            services.alocar_parcela(parcela, base["empenho_1"])
        self._conferir(
            "valor previsto no empenho 1",
            saldos.previsto_empenho(base["empenho_1"]),
            Decimal("8400.00"),
        )
        self._pagar_mensalmente(base, parcelas)
        self._conferir("saldo do empenho 1", base["empenho_1"].saldo, Decimal("0.00"))
        self.stdout.write(
            f"[caso 1] 12 parcelas alocadas e pagas com o empenho 1 em {ano}."
        )

    def _caso_2_dois_anos_fiscais(self, base):
        """Bolsa de julho a junho: seis parcelas no ano corrente e seis no próximo."""
        ano = base["ano_fiscal"]
        proximo = ano + 1
        vinculo, parcelas = self._criar_vinculo(
            base, 2, base["finalidade_bolsa_2a"], dt.date(ano, 7, 1), dt.date(proximo, 6, 30)
        )
        deste_ano = [p for p in parcelas if p.ano_fiscal == ano]
        do_proximo = [p for p in parcelas if p.ano_fiscal == proximo]
        self._conferir("parcelas do caso 2 no ano corrente", len(deste_ano), 6)
        self._conferir("parcelas do caso 2 no ano seguinte", len(do_proximo), 6)

        for parcela in deste_ano:
            services.alocar_parcela(parcela, base["empenho_2"])

        # O ano seguinte ainda não tem orçamento: a reserva é recusada e a parcela
        # continua prevista, aparecendo como compromisso futuro.
        try:
            services.alocar_parcela(do_proximo[0])
        except SaldoInsuficiente as erro:
            self.stdout.write(f"[caso 2] {proximo} sem orçamento, como esperado: {erro}")
        else:
            raise CommandError(
                f"A parcela de {proximo} foi alocada, mas não havia orçamento."
            )
        do_proximo[0].refresh_from_db()
        self._conferir(
            "status da parcela sem orçamento",
            do_proximo[0].status,
            ParcelaBolsa.Status.PREVISTA,
        )
        self._conferir(
            "compromisso futuro",
            saldos.compromisso_futuro(base["centro"]),
            {proximo: Decimal("4200.00")},
        )

        self._pagar_mensalmente(base, deste_ano)
        self._conferir("saldo do empenho 2", base["empenho_2"].saldo, Decimal("0.00"))
        self.stdout.write(f"[caso 2] 6 parcelas de {ano} pagas; 6 seguem previstas.")

        # Chega o orçamento do ano seguinte e as parcelas previstas podem ser pagas.
        services.creditar(
            base["centro"], proximo, base["natureza"], Decimal("4200.00"), base["usuario"]
        )
        empenho_proximo = self._empenho(base, "5", base["finalidade_bolsa_2a"], proximo, 4200)
        services.distribuir(
            base["centro"],
            proximo,
            base["natureza"],
            base["unidade"],
            Decimal("4200.00"),
            base["usuario"],
        )
        for parcela in do_proximo:
            services.alocar_parcela(parcela, empenho_proximo)
        self._conferir(
            "compromisso futuro após o orçamento", saldos.compromisso_futuro(base["centro"]), {}
        )
        self._pagar_mensalmente(base, do_proximo)
        self._conferir("saldo do empenho de " + str(proximo), empenho_proximo.saldo, Decimal("0.00"))
        self.stdout.write(
            f"[caso 2] orçamento de {proximo} recebido: 6 parcelas alocadas e pagas."
        )

    def _caso_3_dois_empenhos(self, base):
        """
        Bolsa de três meses em que cada parcela sai de dois empenhos (420 + 280).

        Os empenhos têm finalidades diferentes da bolsa e entre si, mas a mesma
        natureza, que é o que a regra exige.
        """
        ano = base["ano_fiscal"]
        vinculo, parcelas = self._criar_vinculo(
            base, 3, base["finalidade_monitoria"], dt.date(ano, 10, 1), dt.date(ano, 12, 31)
        )
        self._conferir("parcelas do caso 3", len(parcelas), 3)
        for parcela in parcelas:
            services.alocar_parcela(parcela, base["empenho_3"])

        def divisao(item):
            return [
                (base["empenho_3"], Decimal("420.00")),
                (base["empenho_4"], Decimal("280.00")),
            ]

        self._pagar_mensalmente(base, parcelas, divisao)
        self._conferir("saldo do empenho 3", base["empenho_3"].saldo, Decimal("0.00"))
        self._conferir("saldo do empenho 4", base["empenho_4"].saldo, Decimal("0.00"))
        self.stdout.write(
            "[caso 3] 3 parcelas pagas: R$ 420.00 do empenho 3 (monitoria) e "
            "R$ 280.00 do empenho 4 (extensão) em cada uma."
        )

    # --- apoio -------------------------------------------------------------------

    def _pagar_mensalmente(self, base, parcelas, divisao=None):
        """Cria e paga uma Lista SIAFI por competência."""
        for parcela in parcelas:
            lista = services.criar_lista(base["centro"], parcela.competencia)
            (item,) = services.incluir_parcelas(lista, [parcela])
            divisoes = {item.pk: divisao(item)} if divisao else None
            services.pagar_lista(
                lista,
                base["usuario"],
                f"{parcela.competencia:%Y%m}-{base['sufixo']}-{parcela.pk}",
                divisoes=divisoes,
            )
            parcela.refresh_from_db()
            self._conferir(
                f"status da parcela {parcela.competencia}",
                parcela.status,
                ParcelaBolsa.Status.PAGA,
            )

    def _conferir_saldos_finais(self, base):
        ano = base["ano_fiscal"]
        natureza = base["natureza"]
        self._conferir(
            "saldo final da unidade",
            saldos.saldo_unidade(base["unidade"], ano, natureza),
            Decimal("0.00"),
        )
        self._conferir(
            "saldo final do centro",
            saldos.total_centro(base["centro"], ano, natureza),
            Decimal("0.00"),
        )
        self.stdout.write(f"[final] {ano}: unidade e centro sem saldo remanescente.")

    @staticmethod
    def _conferir(descricao, valor_obtido, valor_esperado):
        if valor_obtido != valor_esperado:
            raise CommandError(
                f"Falha ao conferir {descricao}: esperado {valor_esperado!r}, "
                f"obtido {valor_obtido!r}."
            )
