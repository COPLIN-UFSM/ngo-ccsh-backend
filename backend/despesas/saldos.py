"""
Consultas de saldo (somente leitura).

Todo saldo é uma soma simples sobre o razão (``Lancamento``); como o razão só recebe
linhas novas (correções entram como estornos), nunca é preciso "achar a versão
vigente". As consultas de bolsas somam ``ParcelaBolsa`` (plano, fora do razão).

Termos
------
* **saldo** de empenho/unidade: soma das linhas do razão naquela dimensão;
* **alocado** de uma unidade: parcelas de bolsa ALOCADAS e ainda não pagas;
* **disponível** de uma unidade: saldo - alocado;
* **total** do centro: soma das linhas que alteram o total (créditos, pagamentos...);
* **livre** (não empenhado): total - soma das linhas com empenho;
* **do centro** (não distribuído): total - soma das linhas com unidade.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from django.db.models import Q, Sum

from .models import (
    ZERO,
    Empenho,
    Lancamento,
    ParcelaBolsa,
    TipoMovimento,
    Transacao,
)


def _soma(queryset, campo="montante") -> Decimal:
    return queryset.aggregate(t=Sum(campo))["t"] or ZERO


# --- razão -----------------------------------------------------------------


def saldo_empenho(empenho) -> Decimal:
    return _soma(Lancamento.objects.filter(empenho=empenho))


def gasto_empenho(empenho) -> Decimal:
    return -_soma(
        Lancamento.objects.filter(
            empenho=empenho, tipo_movimento__conta_como_gasto=True
        )
    )


def saldo_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return _soma(
        Lancamento.objects.filter(
            unidade=unidade, ano_fiscal=ano_fiscal, natureza=natureza
        )
    )


def distribuido_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return _soma(
        Lancamento.objects.filter(
            unidade=unidade,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
        ).filter(
            Q(transacao__operacao=Transacao.Operacao.DISTRIBUICAO)
            | Q(estorna__transacao__operacao=Transacao.Operacao.DISTRIBUICAO)
        )
    )


def recebido_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return _soma(
        Lancamento.objects.filter(
            unidade=unidade,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            montante__gt=0,
        ).filter(
            Q(transacao__operacao=Transacao.Operacao.TRANSFERENCIA)
            | Q(estorna__transacao__operacao=Transacao.Operacao.TRANSFERENCIA)
        )
    )


def transferido_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return -_soma(
        Lancamento.objects.filter(
            unidade=unidade,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            montante__lt=0,
        ).filter(
            Q(transacao__operacao=Transacao.Operacao.TRANSFERENCIA)
            | Q(estorna__transacao__operacao=Transacao.Operacao.TRANSFERENCIA)
        )
    )


def gasto_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return -_soma(
        Lancamento.objects.filter(
            unidade=unidade,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            tipo_movimento__conta_como_gasto=True,
        )
    )


def total_centro(centro, ano_fiscal, natureza) -> Decimal:
    return _soma(
        Lancamento.objects.filter(
            centro=centro,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            tipo_movimento__altera_total=True,
        )
    )


def orcamento_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Total recebido pelo centro na natureza, incluindo conversões e transportes."""
    entradas = Lancamento.objects.filter(
        centro=centro,
        ano_fiscal=ano_fiscal,
        natureza=natureza,
        tipo_movimento__codigo__in=[
            TipoMovimento.Codigo.CREDITO_ORDINARIO,
            TipoMovimento.Codigo.CREDITO_EXTRAORDINARIO,
            TipoMovimento.Codigo.TRANSPORTE_ENTRADA,
            TipoMovimento.Codigo.CONVERSAO_NATUREZA,
        ],
        montante__gt=0,
        estorna__isnull=True,
        estornado_por__isnull=True,
    )
    return _soma(entradas)


def recebido_centro(centro, ano_fiscal, natureza) -> Decimal:
    return _soma(
        Lancamento.objects.filter(
            centro=centro,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            tipo_movimento__codigo__in=[
                "credito_ordinario",
                "credito_extraordinario",
            ],
        )
    )


def gasto_centro(centro, ano_fiscal, natureza) -> Decimal:
    lancamentos = Lancamento.objects.filter(
        centro=centro,
        ano_fiscal=ano_fiscal,
        natureza=natureza,
        estorna__isnull=True,
        estornado_por__isnull=True,
    )
    gastos_contabilizados = -_soma(
        lancamentos.filter(tipo_movimento__conta_como_gasto=True)
    )
    distribuido = _soma(
        lancamentos.filter(
            tipo_movimento__codigo=TipoMovimento.Codigo.DISTRIBUICAO,
            unidade__isnull=False,
        )
    )
    conversao_saida = -_soma(
        lancamentos.filter(
            tipo_movimento__codigo=TipoMovimento.Codigo.CONVERSAO_NATUREZA,
            montante__lt=0,
        )
    )
    transporte_saida = -_soma(
        lancamentos.filter(
            tipo_movimento__codigo=TipoMovimento.Codigo.TRANSPORTE_SAIDA,
            montante__lt=0,
        )
    )

    return gastos_contabilizados + distribuido + conversao_saida + transporte_saida


def empenhado_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Soma dos saldos de todos os empenhos do centro naquele ano e natureza."""
    return _soma(
        Lancamento.objects.filter(
            centro=centro,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            empenho__isnull=False,
        )
    )


def distribuido_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Soma dos saldos de todas as unidades do centro naquele ano e natureza."""
    return _soma(
        Lancamento.objects.filter(
            centro=centro,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            unidade__isnull=False,
        )
    )


def distribuido_unidades_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Total líquido transferido do centro para as unidades naquela natureza."""
    return _soma(
        Lancamento.objects.filter(
            centro=centro,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            unidade__isnull=False,
            tipo_movimento__codigo=TipoMovimento.Codigo.DISTRIBUICAO,
            estorna__isnull=True,
            estornado_por__isnull=True,
        )
    )


def livre_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Recurso do centro que ainda não foi empenhado."""
    return total_centro(centro, ano_fiscal, natureza) - empenhado_centro(
        centro, ano_fiscal, natureza
    )


def nao_distribuido_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Recurso do centro que ainda não foi distribuído às subunidades."""
    return total_centro(centro, ano_fiscal, natureza) - distribuido_centro(
        centro, ano_fiscal, natureza
    )


# --- bolsas (plano) ---------------------------------------------------------


def alocado_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return _soma(
        ParcelaBolsa.objects.filter(
            vinculo__unidade=unidade,
            vinculo__finalidade__natureza=natureza,
            ano_fiscal=ano_fiscal,
            status=ParcelaBolsa.Status.ALOCADA,
        ),
        campo="valor",
    )


def disponivel_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return saldo_unidade(unidade, ano_fiscal, natureza) - alocado_unidade(
        unidade, ano_fiscal, natureza
    )


def previsto_empenho(empenho) -> Decimal:
    """Parcelas alocadas que devem sair deste empenho e ainda não foram pagas."""
    return _soma(
        ParcelaBolsa.objects.filter(
            empenho_previsto=empenho, status=ParcelaBolsa.Status.ALOCADA
        ),
        campo="valor",
    )


def a_complementar(empenho) -> Decimal:
    """
    Quanto falta empenhar (reforçar) para cobrir o que já está alocado para sair deste
    empenho. Zero quando o empenho já cobre tudo.
    """
    falta = previsto_empenho(empenho) - saldo_empenho(empenho)
    return falta if falta > 0 else ZERO


def compromisso_futuro(centro=None) -> dict:
    """
    Parcelas ainda PREVISTAS (sem reserva), somadas por ano fiscal. É o relatório de
    "compromisso futuro": o que já se sabe que será preciso pagar, mas ainda não tem
    orçamento distribuído para reservar.
    """
    parcelas = ParcelaBolsa.objects.filter(status=ParcelaBolsa.Status.PREVISTA)
    if centro is not None:
        parcelas = parcelas.filter(vinculo__unidade__centro=centro)
    linhas = parcelas.values("ano_fiscal").annotate(total=Sum("valor"))
    return {
        linha["ano_fiscal"]: linha["total"] for linha in linhas.order_by("ano_fiscal")
    }


# --- fechamento ---------------------------------------------------------------


def pendencias_fechamento(centro, ano_fiscal) -> dict:
    """
    O que ainda impede o fechamento do exercício: tudo precisa estar zerado.

    Retorna ``{"ok": bool, "empenhos": [(Empenho, saldo)], "unidades":
    [(unidade_id, natureza_id, saldo)], "totais": [(natureza_id, total)],
    "parcelas_alocadas": int}``.
    """
    base = Lancamento.objects.filter(centro=centro, ano_fiscal=ano_fiscal)

    por_empenho = (
        base.filter(empenho__isnull=False).values("empenho").annotate(s=Sum("montante"))
    )
    saldos_empenho = {
        item["empenho"]: item["s"] for item in por_empenho if item["s"] != 0
    }
    empenhos = Empenho.objects.in_bulk(list(saldos_empenho))

    por_unidade = (
        base.filter(unidade__isnull=False)
        .values("unidade", "natureza")
        .annotate(s=Sum("montante"))
    )
    unidades = [
        (item["unidade"], item["natureza"], item["s"])
        for item in por_unidade
        if item["s"] != 0
    ]

    totais = defaultdict(lambda: ZERO)
    for item in (
        base.filter(tipo_movimento__altera_total=True)
        .values("natureza")
        .annotate(s=Sum("montante"))
    ):
        totais[item["natureza"]] += item["s"]
    totais = [(n, t) for n, t in totais.items() if t != 0]

    parcelas = ParcelaBolsa.objects.filter(
        status=ParcelaBolsa.Status.ALOCADA,
        ano_fiscal=ano_fiscal,
        vinculo__unidade__centro=centro,
    ).count()

    resultado = {
        "empenhos": [(empenhos[pk], s) for pk, s in saldos_empenho.items()],
        "unidades": unidades,
        "totais": totais,
        "parcelas_alocadas": parcelas,
    }
    resultado["ok"] = not (resultado["empenhos"] or unidades or totais or parcelas)
    return resultado
